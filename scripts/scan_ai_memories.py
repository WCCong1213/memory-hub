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

def scan(cfg):
    new_items = []
    state = load_state()
    for ai, src in cfg['sources'].items():
        last = state.get(ai, 0)
        paths = src['path'] if isinstance(src['path'], list) else [src['path']]
        for base in paths:
            if not os.path.exists(base):
                continue
            if src['type'] == 'sqlite':
                mtime = os.path.getmtime(base)
                if mtime > last:
                    new_items.append({'ai': ai, 'source': base, 'type': 'sqlite', 'mtime': mtime})
            elif src['type'] == 'jsonl_dir':
                for f in glob.glob(os.path.join(base, '*', '*.jsonl')):
                    mtime = os.path.getmtime(f)
                    if mtime > last:
                        new_items.append({'ai': ai, 'source': f, 'type': 'jsonl', 'mtime': mtime})
            elif src['type'] == 'files':
                for f in glob.glob(os.path.join(base, '*', '*')) + glob.glob(os.path.join(base, '*', '*', '*')):
                    if os.path.isfile(f):
                        mtime = os.path.getmtime(f)
                        if mtime > last:
                            new_items.append({'ai': ai, 'source': f, 'type': 'file', 'mtime': mtime})
    return new_items, state

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
            manual.append({**d, 'type': 'jsonl_dir' if os.path.isdir(d['path']) else 'sqlite'})
    return manual


if __name__ == '__main__':
    cfg = load_config()
    sources = merge_sources(cfg)
    print('发现AI数据源:')
    for src in sources:
        print(f"  [{src['ai']}] {'(自动发现)' if src.get('auto') else '(手动配置)'} {src['path']}")
    items, state = scan({'sources': {src['ai']: {'type': src['type'], 'path': src['path']} for src in sources}})
    print(f'扫描完成：新增 {len(items)} 个未处理项目')
    for it in items[:20]:
        print(f"  [{it['ai']}] {it['source']}")
    if len(items) > 20:
        print(f'  ...等共 {len(items)} 项')

