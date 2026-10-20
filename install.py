# -*- coding: utf-8 -*-
"""记忆库管理插件 安装向导：首次运行生成 config.json 并创建记忆库骨架
用法：python install.py   （按提示填写路径，回车用默认值）
可重复运行：已存在的文件不会被覆盖。
"""
import json
import os
import shutil

DEFAULT = {
    "memory_root": os.environ.get("MEMORY_HUB_ROOT") or os.path.join(os.path.expanduser("~"), "第二大脑"),
    "sources": {
        "ZCode": {"type": "sqlite", "path": os.path.expanduser(r"~\.zcode\v2\tasks-index.sqlite")},
        "ClaudeCode": {"type": "jsonl_dir", "path": os.path.expanduser(r"~\.claude\projects")},
        "Doubao": {"type": "files", "path": [os.path.expanduser(r"~\Doubao\chats"), os.path.expanduser(r"~\.doubao\chats")]},
    },
    "filters": {
        "ignore_keywords": ["鼠标", "网盘", "下载地址"],
        "privacy_mark": "🔒",
    },
}

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATES = os.path.join(HERE, "knowledge", "模板")


def ask(label, default):
    v = input(f"{label} [默认: {default}]: ").strip()
    return v if v else default


def build_config():
    cfg = {"memory_root": ask("记忆库根目录（第二大脑）", DEFAULT["memory_root"])}
    cfg["sources"] = {}
    print("\n-- AI会话源路径（留空用默认）--")
    for name, src in DEFAULT["sources"].items():
        if isinstance(src["path"], list):
            p1 = ask(f"{name} 路径1", src["path"][0])
            p2 = ask(f"{name} 路径2", src["path"][1] if len(src["path"]) > 1 else "")
            cfg["sources"][name] = {"type": src["type"], "path": [p1, p2] if p2 else [p1]}
        else:
            cfg["sources"][name] = {"type": src["type"], "path": ask(f"{name} 路径", src["path"])}
    cfg["filters"] = DEFAULT["filters"]
    return cfg


def write_if_missing(path, content=None, src=None, created=None):
    """文件不存在才写入/复制，避免覆盖用户已编辑的内容。"""
    if os.path.exists(path):
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if src:
        shutil.copy(src, path)
        # 指南里的 <技能目录> 替换成实际路径，装完即可直接执行
        if path.endswith("📖 记忆库使用指南.md"):
            text = open(path, encoding="utf-8").read().replace("<技能目录>", HERE)
            open(path, "w", encoding="utf-8").write(text)
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    created.append(path)


def main():
    print("=== 记忆库管理插件 安装向导 ===")
    print("将生成 config.json（所有路径可自定义，本插件零硬编码）")

    out = os.path.join(HERE, "config.json")
    if os.path.exists(out):
        old = json.load(open(out, encoding="utf-8"))
        print(f"\n检测到已有配置: {out}")
        print(f"  记忆库根目录: {old.get('memory_root')}")
        again = input("是否重新生成 config.json？(y/n，回车默认 n——保留现有配置): ").strip().lower()
        if again in ("y", "yes"):
            cfg = build_config()
            with open(out, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            print(f"✅ config.json 已更新: {out}")
        else:
            cfg = old
            print("✅ 保留现有 config.json")
            print("   如需只补建缺失的骨架文件，本向导会继续执行且不覆盖已有文件")
    else:
        cfg = build_config()
        with open(out, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        print(f"\n✅ config.json 已生成: {out}")

    root = cfg["memory_root"]
    created = []
    for d in ["AI会话记忆", "项目经验库", os.path.join("项目经验库", "归档"),
              os.path.join("项目经验库", "_模板"),
              "能力经验库", os.path.join("能力经验库", "_模板")]:
        os.makedirs(os.path.join(root, d), exist_ok=True)

    # 骨架文件：指南 + 首页 + 两个总索引 + 两个聚合模板
    skeleton = [
        ("📖 记忆库使用指南.md", os.path.join(HERE, "knowledge", "记忆库使用指南模板.md")),
        ("🏠 记忆库首页.md", os.path.join(TEMPLATES, "🏠 记忆库首页模板.md")),
        (os.path.join("项目经验库", "📋 项目总索引.md"), os.path.join(TEMPLATES, "📋 项目总索引模板.md")),
        (os.path.join("能力经验库", "📋 经验总索引.md"), os.path.join(TEMPLATES, "📋 经验总索引模板.md")),
        (os.path.join("项目经验库", "_模板", "📊 项目经验聚合模板.md"),
         os.path.join(TEMPLATES, "📊 项目经验聚合模板.md")),
        (os.path.join("能力经验库", "_模板", "📊 经验聚合模板.md"),
         os.path.join(TEMPLATES, "📊 经验聚合模板.md")),
    ]
    for rel, src in skeleton:
        if os.path.exists(src):
            write_if_missing(os.path.join(root, rel), src=src, created=created)

    write_if_missing(os.path.join(root, "📥 捕捉箱.md"),
                     content="# 📥 捕捉箱\n\n> 临时想法随手记，整理记忆时自动提炼\n",
                     created=created)

    if created:
        print("✅ 已创建记忆库骨架：")
        for c in created:
            print("   ", c)
    else:
        print("✅ 记忆库骨架已存在，未覆盖任何文件")

    obs = input("\n是否安装 Obsidian 来查看记忆库？(y/n，回车默认 n): ").strip().lower()
    if obs in ("y", "yes"):
        print("\n📖 Obsidian 安装指引：")
        print("  1. 访问 https://obsidian.md 下载并安装（免费）")
        print(f"  2. 打开 Obsidian → 选择「打开文件夹作为库」→ 选择: {root}")
        print("  3. 左侧文件树即可浏览全部记忆")
    else:
        print("\n✅ 本地记忆库已就绪（纯文件，不依赖 Obsidian）")
        print(f"  记忆库位置: {root}")
        print("  查看方式：任意文本编辑器（记事本 / VS Code）打开 md 文件即可")
        print("  随时可改主意：装 Obsidian 后「打开文件夹作为库」指向同一路径即可")

    print("\n下一步：")
    print('  1. 对本机 AI 说「整理记忆」——扫描各 AI 工具会话并提炼入库')
    print('  2. 对 AI 说「读第二大脑指南，以后每次任务前先检索」')
    print("  3. 新建项目按 项目经验库\\📋 项目总索引.md 里的流程走")


if __name__ == "__main__":
    main()
