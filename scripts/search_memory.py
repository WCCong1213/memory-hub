# -*- coding: utf-8 -*-
"""记忆搜索：关键词搜索记忆库（项目库+能力库+AI记忆+捕捉箱）
用法：python search_memory.py "关键词" [--ai AI名] [--limit N]
"""
import argparse, json, os, glob

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
    # 捕捉箱
    inbox = os.path.join(root, '📥 捕捉箱.md')
    if os.path.exists(inbox):
        for line in open(inbox, encoding='utf-8', errors='ignore'):
            if kw in line:
                hits.append(('📥 捕捉箱.md', line.strip()[:90]))
    return hits[:limit]

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('kw')
    p.add_argument('--limit', type=int, default=15)
    a = p.parse_args()
    cfg = load_cfg()
    hits = search(cfg['memory_root'], a.kw, a.limit)
    print(f'搜索「{a.kw}」命中 {len(hits)} 条：')
    for rel, line in hits:
        print(f'  [{rel}] {line}')
    if not hits:
        print('  （无命中——可检查捕捉箱或建议写入经验库）')
