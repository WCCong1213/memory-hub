# -*- coding: utf-8 -*-
"""记忆库写入脚本：向项目经验库追加执行史一行（格式统一、防交错）
用法：
python append_execution.py --project "CPA考试" --date 2026-08-18 --ai ZCode \
    --task "任务简述" --problem "执行问题" --solution "解决办法" --experience "沉淀经验"
"""
import argparse, os, sys

import json, os
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_cfg = json.load(open(os.path.join(SKILL_DIR, 'config.json'), encoding='utf-8'))
BASE = os.path.join(_cfg['memory_root'], '项目经验库')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--project', required=True, help='项目名（对应项目经验库目录名）')
    p.add_argument('--date', required=True)
    p.add_argument('--ai', required=True, help='AI工具名（ZCode/ClaudeCode/Doubao/其他）')
    p.add_argument('--task', required=True)
    p.add_argument('--problem', default='—')
    p.add_argument('--solution', default='—')
    p.add_argument('--experience', default='—')
    a = p.parse_args()

    fpath = os.path.join(BASE, a.project, '📊 项目经验聚合.md')
    if not os.path.exists(fpath):
        sys.exit(f'错误：未找到 {fpath}')

    line = f'| {a.date} | {a.ai} | {a.task} | {a.problem} | {a.solution} | {a.experience} |'
    with open(fpath, encoding='utf-8') as f:
        lines = f.read().split('\n')

    # 定位"| 日期 |"表头行
    header_idx = None
    for i, l in enumerate(lines):
        if l.strip().startswith('| 日期 |'):
            header_idx = i
            break
    if header_idx is None:
        sys.exit('错误：未找到执行史表（需有"| 日期 |"表头）')

    # 找表头后最后一个数据行
    insert_at = header_idx + 1
    for i in range(header_idx + 1, len(lines)):
        s = lines[i].strip()
        if s.startswith('|') and not s.startswith('| ---') and s != '|':
            insert_at = i + 1
        elif s == '' and insert_at > header_idx + 1:
            break

    lines.insert(insert_at, line)
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f'OK 已追加: {a.project} | {a.date} | {a.ai} | {a.task[:20]}')


if __name__ == '__main__':
    main()
