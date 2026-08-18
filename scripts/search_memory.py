# -*- coding: utf-8 -*-
"""记忆搜索：关键词搜索记忆库（项目库+能力库+AI记忆+捕捉箱）
用法：python search_memory.py "关键词" [--ai AI名] [--limit N] [--record-use "经验卡标识"]
--record-use：记录一条经验卡被引用（应用闭环：引用计数+最近使用时间）
"""
import argparse, json, os, glob, sys, datetime

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'memory_hub_state.json')

def load_state():
    if os.path.exists(STATE_FILE):
        return json.load(open(STATE_FILE, encoding='utf-8'))
    return {}

def save_state(st):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(st, f, ensure_ascii=False, indent=2)

def record_use(card_id):
    """记录经验卡被引用：引用次数+1、最近使用日期。用法：AI执行任务引用经验卡后调用"""
    st = load_state()
    usage = st.setdefault('experience_usage', {})
    today = datetime.date.today().isoformat()
    u = usage.get(card_id, {'uses': 0})
    u['uses'] = u.get('uses', 0) + 1
    u['last_used'] = today
    usage[card_id] = u
    st['experience_usage'] = usage
    save_state(st)
    return u['uses']

def usage_summary():
    """返回使用统计（供搜索时展示经验卡验证状态）"""
    return load_state().get('experience_usage', {})

def load_cfg():
    d = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return json.load(open(os.path.join(d, 'config.json'), encoding='utf-8'))

def search(root, kw, limit):
    hits = []
    for base in ['项目经验库', '能力经验库', 'AI会话记忆']:
        bdir = os.path.join(root, base)
        if not os.path.exists(bdir):
            continue
        for f in glob.glob(os.path.join(bdir, '**', '*.md'), recursive=True):
            try:
                txt = open(f, encoding='utf-8', errors='ignore').read()
                if kw in txt:
                    # 提取命中行上下文
                    for line in txt.split('\n'):
                        if kw in line:
                            rel = os.path.relpath(f, root)
                            hits.append((rel, line.strip()[:90]))
            except:
                pass
    # 文件产出（xlsx/pdf等：文件名命中）
    for ext in ('*.xlsx', '*.xls', '*.pdf', '*.csv'):
        for f in glob.glob(os.path.join(root, '**', ext), recursive=True):
            if kw.lower() in os.path.basename(f).lower():
                hits.append((os.path.relpath(f, root), '[文件产出]'))
    # 捕捉箱
    inbox = os.path.join(root, '📥 捕捉箱.md')
    if os.path.exists(inbox):
        for line in open(inbox, encoding='utf-8', errors='ignore'):
            if kw in line:
                hits.append(('📥 捕捉箱.md', line.strip()[:90]))
    return hits[:limit]

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('kw', nargs='?', default='')
    p.add_argument('--limit', type=int, default=15)
    p.add_argument('--full', action='store_true', help='输出全部命中行')
    p.add_argument('--record-use', metavar='经验卡标识', help='记录经验卡被引用（如"审计实务方法/问题链1"）')
    a = p.parse_args()
    if a.record_use:
        n = record_use(a.record_use)
        print(f'✅ 已记录引用：{a.record_use}（累计引用 {n} 次）')
        sys.exit(0)
    cfg = load_cfg()
    hits = search(cfg['memory_root'], a.kw, a.limit)
    full = a.full
    print(f'搜索「{a.kw}」：')
    # 优先展示经验总索引命中（10秒定位，省token）
    idx_path = os.path.join(cfg['memory_root'], '能力经验库', '📋 经验总索引.md')
    shown = 0
    if os.path.exists(idx_path):
        idx_txt = open(idx_path, encoding='utf-8').read()
        for line in idx_txt.split('\n'):
            if a.kw in line and line.startswith('|'):
                print(f'  [🎯索引] {line.strip()[:110]}')
                shown += 1
    # 展示命中经验卡的验证状态（应用闭环：引用次数+最近使用）
    usage = usage_summary()
    if usage:
        shown_usage = {}
        for rel, line in hits:
            for card, u in usage.items():
                if card.split('/')[-1] in rel or card.split('/')[-1] in line:
                    shown_usage[card] = u
        for card, u in sorted(shown_usage.items(), key=lambda x: -x[1].get('uses', 0))[:5]:
            print(f'  [📊经验] {card}：引用{u.get("uses",0)}次·最近{u.get("last_used","?")}（用后记得 --record-use 回流）')
    if full:
        for rel, line in hits:
            print(f'  [{rel}] {line[:100]}')
    elif not shown:
        seen = set()
        for rel, line in hits:
            if rel not in seen:
                seen.add(rel)
                print(f'  [文件] {rel}')
        print('  [提示] 加 --full 查看详细命中行')
    if not hits and not shown:
        print('  （无命中——可检查捕捉箱或建议写入经验库）')
