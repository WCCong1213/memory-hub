# -*- coding: utf-8 -*-
"""扫描各AI会话源，对照状态文件输出新增会话清单
用法：python scan_ai_memories.py
"""
import json, os, sys, glob

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_FILE = os.path.join(SKILL_DIR, 'scripts', 'memory_hub_state.json')

def load_config():
    cfg_path = os.path.join(SKILL_DIR, 'config.json')
    if not os.path.exists(cfg_path):
        sys.exit('未找到 config.json，请先运行 install.py 或复制 config.json.example')
    return json.load(open(cfg_path, encoding='utf-8'))

def load_state():
    if os.path.exists(STATE_FILE):
        return json.load(open(STATE_FILE, encoding='utf-8'))
    return {}

def _sqlite_fingerprint(path):
    """sqlite 文件内容指纹：mtime + size（文件持续更新时用指纹判断是否变化）"""
    try:
        st = os.stat(path)
        return f"{int(st.st_mtime)}:{st.st_size}"
    except OSError:
        return None

def _sqlite_new_sessions(path, since_mtime):
    """列出 sqlite 会话库中在 since_mtime（秒）之后更新的未删除会话，用于指纹变化时的明细输出"""
    try:
        import sqlite3
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        cur.execute(
            "SELECT task_id, title, task_status, datetime(updated_at/1000,'unixepoch','localtime') "
            "FROM tasks WHERE deleted=0 AND archived=0 AND updated_at > ? ORDER BY updated_at",
            (int(since_mtime) * 1000,))
        rows = cur.fetchall()
        conn.close()
        return [{'id': r[0], 'title': r[1], 'status': r[2], 'updated': r[3]} for r in rows]
    except Exception:
        return []

def scan(cfg):
    """增量扫描：只列已处理清单（processed_files）之外的新项目；清单内文件指纹变化（跨天持续会话）报更新"""
    new_items = []
    state = load_state()
    processed = set(state.get('processed_files', []))
    # sqlite 指纹表：{路径: "mtime:size"}，用于检测单文件持续更新的数据源（如 ZCode tasks-index.sqlite）
    fingerprints = state.get('sqlite_fingerprints', {})
    # 普通会话文件指纹表：{文件完整路径: "mtime:size"}，用于检测已处理会话文件后续写入（跨天持续会话）
    # 首次引入该字段时自动建立基线（记录全部已处理文件的当前指纹，本轮不报更新），避免历史文件全量误报
    first_time = 'file_fingerprints' not in state
    file_fps = state.get('file_fingerprints', {})
    for ai, src in cfg['sources'].items():
        paths = src['path'] if isinstance(src['path'], list) else [src['path']]
        for base in paths:
            if not os.path.exists(base):
                continue
            if src['type'] == 'sqlite':
                fid = os.path.basename(base)
                if fid not in processed:
                    # 首次扫描：列出全部未删除会话供提炼判断
                    sessions = _sqlite_new_sessions(base, 0)
                    new_items.append({'ai': ai, 'source': base, 'type': 'sqlite', 'sessions': sessions})
                else:
                    # 已处理过，但文件内容可能更新了（mtime/size 变化）→ 仍视为新增，附上指纹后新增会话清单
                    fp = _sqlite_fingerprint(base)
                    if fp is not None and fingerprints.get(base) != fp:
                        old_fp = fingerprints.get(base, '')
                        since = int(old_fp.split(':')[0]) if old_fp else 0
                        sessions = _sqlite_new_sessions(base, since)
                        new_items.append({'ai': ai, 'source': base, 'type': 'sqlite', 'changed': True, 'fp': fp, 'sessions': sessions})
            elif src['type'] == 'jsonl_dir':
                for f in glob.glob(os.path.join(base, '*', '*.jsonl')):
                    fid = os.path.basename(f)
                    if fid not in processed:
                        new_items.append({'ai': ai, 'source': f, 'type': 'jsonl'})
                    else:
                        # 已处理过但文件又写入新内容（跨天持续会话）→ 报"更新"，AI 判断提炼增量
                        fp = _sqlite_fingerprint(f)
                        if fp is not None:
                            if first_time:
                                file_fps[f] = fp  # 基线校准，不报
                            elif file_fps.get(f) != fp:
                                new_items.append({'ai': ai, 'source': f, 'type': 'jsonl', 'changed': True, 'fp': fp})
            elif src['type'] == 'zstd_jsonl_dir':
                # DSH(DeepSeek Harness)会话：~/.dsh/sessions/<工作区>/<会话ID>/session.jsonl.zstd
                # zstd 压缩的 JSONL（文件头 28 B5 2F FD），解码用 Python zstandard 流式解压：
                #   import zstandard
                #   dctx = zstandard.ZstdDecompressor()
                #   text = dctx.stream_reader(open(p,'rb')).read().decode('utf-8','replace')
                # 环境依赖：pip install zstandard（无该包时扫描可跑，但提炼时需安装）
                # ⚠️ 会话文件都叫 session.jsonl.zstd，唯一标识用父目录名（会话UUID目录），
                #    不能用 basename（否则标记1条会误跳过所有会话）
                for f in glob.glob(os.path.join(base, '**', '*.jsonl.zstd'), recursive=True):
                    fid = os.path.basename(os.path.dirname(f))
                    if fid not in processed:
                        new_items.append({'ai': ai, 'source': f, 'fid': fid, 'type': 'zstd_jsonl'})
                    else:
                        # 已处理过但会话文件后续又写入（跨天持续会话）→ 报"更新"
                        fp = _sqlite_fingerprint(f)
                        if fp is not None:
                            if first_time:
                                file_fps[f] = fp  # 基线校准，不报
                            elif file_fps.get(f) != fp:
                                new_items.append({'ai': ai, 'source': f, 'fid': fid, 'type': 'zstd_jsonl', 'changed': True, 'fp': fp})
            elif src['type'] == 'files':
                for f in glob.glob(os.path.join(base, '*', '*')) + glob.glob(os.path.join(base, '*', '*', '*')):
                    if os.path.isfile(f):
                        fid = os.path.basename(f)
                        if fid not in processed:
                            new_items.append({'ai': ai, 'source': f, 'type': 'file'})
                        else:
                            fp = _sqlite_fingerprint(f)
                            if fp is not None:
                                if first_time:
                                    file_fps[f] = fp  # 基线校准，不报
                                elif file_fps.get(f) != fp:
                                    new_items.append({'ai': ai, 'source': f, 'type': 'file', 'changed': True, 'fp': fp})
    if first_time:
        # 首次引入文件指纹：基线落盘，下次扫描起才检测真实变化
        state['file_fingerprints'] = file_fps
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    return new_items, state


def mark_processed(items):
    """把已提炼的项目加入已处理清单（增量定位的核心）"""
    state = load_state()
    processed = set(state.get('processed_files', []))
    fingerprints = state.get('sqlite_fingerprints', {})
    file_fps = state.get('file_fingerprints', {})
    for it in items:
        # 有 fid 用 fid（DSH 会话用会话目录名），否则用 basename（其他类型）
        processed.add(it.get('fid') or os.path.basename(it['source']))
        # sqlite 变化项：记录当前指纹，下次内容不变就不再报
        if it.get('type') == 'sqlite':
            if it.get('changed') and it.get('fp') and it.get('source'):
                fingerprints[it['source']] = it['fp']
            elif it.get('source'):
                # 首次标记：也记录当前指纹，避免下次误报"内容变化"
                fp = _sqlite_fingerprint(it['source'])
                if fp is not None:
                    fingerprints[it['source']] = fp
        elif it.get('source'):
            # 非 sqlite（jsonl/zstd/files）：记录文件指纹 mtime:size，
            # 跨天持续会话（会话文件后续又写入新内容）→ 指纹变化 → 下次扫描报"更新"
            fp = _sqlite_fingerprint(it['source'])
            if fp is not None:
                file_fps[it['source']] = fp
    state['processed_files'] = sorted(processed)
    state['processed_count'] = len(processed)
    state['sqlite_fingerprints'] = fingerprints
    state['file_fingerprints'] = file_fps
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    return state

def auto_discover():
    """自动发现本机所有AI数据源（对照 knowledge/ai_sources.md 的已知位置）"""
    import json as _json
    home = os.path.expanduser('~')
    local = os.environ.get('LOCALAPPDATA', '')
    roaming = os.environ.get('APPDATA', '')
    known = {
        'ZCode': [os.path.join(home, '.zcode', 'v2', 'tasks-index.sqlite')],
        'ClaudeCode': [os.path.join(home, '.claude', 'projects')],
        'Doubao': [os.path.join(home, 'Doubao', 'chats'), os.path.join(home, '.doubao', 'chats')],
        'Codex': [os.path.join(home, '.codex', 'sessions')],
        'Kimi': [os.path.join(local, 'Kimi'), os.path.join(roaming, 'Kimi'), os.path.join(home, '.kimi')],
        'Tongyi': [os.path.join(local, 'Tongyi'), os.path.join(roaming, 'Tongyi'), os.path.join(home, '.tongyi')],
        'ChatGPT': [os.path.join(roaming, 'ChatGPT'), os.path.join(local, 'ChatGPT')],
        'Claude桌面': [os.path.join(roaming, 'Claude')],
        'DeepSeek': [os.path.join(home, '.deepseek'), os.path.join(local, 'DeepSeek')],
        'Gemini': [os.path.join(home, '.gemini')],
        'Zhipu': [os.path.join(local, 'Zhipu'), os.path.join(roaming, 'Zhipu')],
        'Cursor': [os.path.join(roaming, 'Cursor'), os.path.join(local, 'Cursor')],
        'Windsurf': [os.path.join(roaming, 'Windsurf')],
        'Trae': [os.path.join(home, '.trae'), os.path.join(roaming, 'Trae')],
        'MarsCode': [os.path.join(home, '.marscode')],
        'Cline': [os.path.join(home, '.cline')],
        'RooCode': [os.path.join(home, '.roo-code')],
        'Continue': [os.path.join(home, '.continue')],
        '通义灵码': [os.path.join(home, '.tongyilingma'), os.path.join(local, 'TongyiLingma')],
        '文心快码': [os.path.join(home, '.comate'), os.path.join(roaming, 'BaiduComate')],
        '讯飞星火': [os.path.join(local, 'iFlytek'), os.path.join(roaming, 'iFlytek')],
        '腾讯元宝': [os.path.join(local, 'Yuanbao'), os.path.join(roaming, 'Yuanbao')],
        'WPSAI': [os.path.join(roaming, 'Kingsoft'), os.path.join(local, 'Kingsoft')],
        'GLMCLI': [os.path.join(home, '.glm-cli'), os.path.join(home, '.glmcli')],
        'KimiCLI': [os.path.join(home, '.kimi-cli')],
        'MiniMax': [os.path.join(local, 'MiniMax'), os.path.join(roaming, 'MiniMax')],
        'DeepSeekHarness': [os.path.join(home, '.dsh', 'sessions')],
    }
    found = []
    for ai, paths in known.items():
        for p in paths:
            if os.path.exists(p):
                found.append({'ai': ai, 'path': p, 'auto': True})
    return found


def merge_sources(cfg):
    """合并：config手动配置 + 自动发现"""
    manual = []
    for ai, src in cfg.get('sources', {}).items():
        paths = src['path'] if isinstance(src['path'], list) else [src['path']]
        for p in paths:
            manual.append({'ai': ai, 'path': p, 'type': src['type'], 'auto': False})
    discovered = auto_discover() if cfg.get('auto_discover', True) else []
    # 去重（手动优先）
    seen = {(d['ai'], d['path']) for d in manual}
    for d in discovered:
        if (d['ai'], d['path']) not in seen:
            # DSH 会话是 zstd 压缩的 jsonl，单独类型；其余按目录/文件判断
            if d['ai'] == 'DeepSeekHarness':
                dtype = 'zstd_jsonl_dir'
            elif os.path.isdir(d['path']):
                dtype = 'jsonl_dir'
            else:
                dtype = 'sqlite'
            manual.append({**d, 'type': dtype})
    return manual


if __name__ == '__main__':
    import sys
    if '--mark' in sys.argv:
        # 标记指定文件为已处理（用于提炼完成后）
        # DSH 会话文件同名（session.jsonl.zstd），自动补 fid=父目录名，避免误跳过
        items = []
        for x in sys.argv[sys.argv.index('--mark') + 1:]:
            if x.endswith('.jsonl.zstd'):
                items.append({'source': x, 'fid': os.path.basename(os.path.dirname(x))})
            elif x.endswith('.sqlite'):
                # sqlite 单文件：标记时记录当前指纹，下次内容不变不再报
                fp = _sqlite_fingerprint(x)
                items.append({'source': x, 'type': 'sqlite', 'fp': fp} if fp is not None else {'source': x, 'type': 'sqlite'})
            else:
                items.append({'source': x})
        st = mark_processed(items)
        print(f'已标记 {len(items)} 个文件为已处理，累计 {st["processed_count"]} 个')
        sys.exit(0)
    cfg = load_config()
    sources = merge_sources(cfg)
    print('发现AI数据源:')
    for src in sources:
        print(f"  [{src['ai']}] {'(自动发现)' if src.get('auto') else '(手动配置)'} {src['path']}")
    items, state = scan({'sources': {src['ai']: {'type': src['type'], 'path': src['path']} for src in sources}})
    print(f'扫描完成：新增 {len(items)} 个未处理项目（已处理 {state.get("processed_count", 0)} 个）')
    for it in items[:20]:
        if it.get('type') == 'sqlite':
            print(f"  [{it['ai']}] {it['source']}" + ("（指纹变化）" if it.get('changed') else ""))
            for s in it.get('sessions', []):
                print(f"      ├─ {s['updated']} [{s['status']}] {s['id'][:22]}… {s['title']}")
        else:
            print(f"  [{it['ai']}] {it['source']}" + ("（更新）" if it.get('changed') else ""))
    if len(items) > 20:
        print(f'  ...等共 {len(items)} 项')
    if items:
        print('  [提示] 提炼完成后运行 scripts/scan_ai_memories.py --mark <文件路径...> 标记已处理，下次自动跳过')

