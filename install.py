# -*- coding: utf-8 -*-
"""记忆库管理插件 安装向导：首次运行生成 config.json
用法：python install.py   （按提示填写路径，回车用默认值）
"""
import json, os, sys

DEFAULT = {
    "memory_root": r"D:\第二大脑",
    "sources": {
        "ZCode": {"type": "sqlite", "path": os.path.expanduser(r"~\.zcode\v2\tasks-index.sqlite")},
        "ClaudeCode": {"type": "jsonl_dir", "path": os.path.expanduser(r"~\.claude\projects")},
        "Doubao": {"type": "files", "path": [os.path.expanduser(r"~\Doubao\chats"), os.path.expanduser(r"~\.doubao\chats")]}
    },
    "filters": {
        "ignore_keywords": ["鼠标", "网盘", "下载地址", "韩元", "剧场版", "大模型"],
        "privacy_mark": "🔒"
    }
}

def ask(label, default):
    v = input(f"{label} [默认: {default}]: ").strip()
    return v if v else default

def main():
    print("=== 记忆库管理插件 安装向导 ===")
    print("将生成 config.json（所有路径可自定义，本插件零硬编码）")
    cfg = {}
    cfg["memory_root"] = ask("记忆库根目录（第二大脑）", DEFAULT["memory_root"])
    cfg["sources"] = {}
    print("\n-- AI会话源路径（留空用默认）--")
    for name, src in DEFAULT["sources"].items():
        if isinstance(src["path"], list):
            p1 = ask(f"{name} 路径1", src["path"][0])
            p2 = ask(f"{name} 路径2", src["path"][1] if len(src["path"]) > 1 else "")
            cfg["sources"][name] = {"type": src["type"], "path": [p1, p2] if p2 else [p1]}
        else:
            p = ask(f"{name} 路径", src["path"])
            cfg["sources"][name] = {"type": src["type"], "path": p}
    cfg["filters"] = DEFAULT["filters"]
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    print(f"\n✅ config.json 已生成: {out}")

    # 自动创建记忆库骨架（不需要预先存在第二大脑）
    root = cfg["memory_root"]
    dirs = ["AI会话记忆", "项目经验库", "项目经验库/归档", "能力经验库"]
    created = []
    for d in dirs:
        p = os.path.join(root, d)
        os.makedirs(p, exist_ok=True)
        created.append(p)
    inbox = os.path.join(root, "📥 捕捉箱.md")
    if not os.path.exists(inbox):
        with open(inbox, "w", encoding="utf-8") as f:
            f.write("# 📥 捕捉箱\n\n> 临时想法随手记，整理记忆时自动提炼\n")
        created.append(inbox)
    guide = os.path.join(root, "📖 记忆库使用指南.md")
    tmpl = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge", "记忆库使用指南模板.md")
    if not os.path.exists(guide) and os.path.exists(tmpl):
        import shutil
        shutil.copy(tmpl, guide)
        created.append(guide)
    print("✅ 记忆库骨架已创建：")
    for c in created:
        print("   ", c)

    # Obsidian 询问：有则指引安装，无则纯本地
    obs = input("\n是否安装 Obsidian 来查看记忆库？(y/n，回车默认 n): ").strip().lower()
    if obs in ("y", "yes"):
        print("\n📖 Obsidian 安装指引：")
        print("  1. 访问 https://obsidian.md 下载并安装（免费）")
        print(f"  2. 打开 Obsidian → 选择「打开文件夹作为库」→ 选择: {root}")
        print("  3. 左侧文件树即可浏览全部记忆（AI会话记忆/项目经验库/能力经验库）")
    else:
        print("\n✅ 本地记忆库已就绪（纯文件，不依赖 Obsidian）：")
        print(f"  记忆库位置: {root}")
        print("  查看方式：任意文本编辑器（记事本/VS Code）打开 md 文件即可")
        print("  随时可改主意：安装 Obsidian 后选择「打开文件夹作为库」指向同一路径即可")

if __name__ == "__main__":
    main()
