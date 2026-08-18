# -*- coding: utf-8 -*-
"""把待处理清单切成N批（配合并行子代理使用）
用法：
  python split_batch.py --batch-size 5 --workers 3   # 从扫描结果切批
  python split_batch.py --files a.jsonl b.jsonl... --workers 3  # 指定文件切批
"""
import argparse, json, os, sys, subprocess

def get_unprocessed():
    """直接调用scan模块获取结构化未处理清单"""
    import importlib.util
    here = os.path.dirname(os.path.abspath(__file__))
    spec = importlib.util.spec_from_file_location('scanner', os.path.join(here, 'scan_ai_memories.py'))
    scanner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scanner)
    cfg = scanner.load_config()
    sources = scanner.merge_sources(cfg)
    items, _ = scanner.scan({'sources': {src['ai']: {'type': src['type'], 'path': src['path']} for src in sources}})
    return [it['source'] for it in items]

def split(items, workers):
    batches = [[] for _ in range(workers)]
    for i, it in enumerate(items):
        batches[i % workers].append(it)
    return batches

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--workers', type=int, default=3, help='并行子代理数')
    p.add_argument('--files', nargs='*', default=None, help='手动指定文件列表')
    a = p.parse_args()
    items = a.files if a.files else get_unprocessed()
    if not items:
        print('无待处理项目')
        sys.exit(0)
    batches = split(items, a.workers)
    print(f'共 {len(items)} 个，切成 {a.workers} 批：')
    for i, b in enumerate(batches):
        print(f'--- 批{i+1}（{len(b)}个）---')
        for x in b:
            print(f'    {x}')
        print(f'    子代理提示词开头：处理以上文件，按 knowledge/模板/会话笔记模板.md 提炼，写入 AI会话记忆\对应AI\，完成后返回结果')
