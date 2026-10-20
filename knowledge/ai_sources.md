# AI会话数据源知识库（自动发现对照表）

> 技能自动扫描时对照本表识别AI工具及数据格式。新AI出现时在此追加。
> 位置用相对用户主目录（~）和系统变量描述，不写死具体用户名。

## 已知AI数据源

| AI工具 | 本地数据位置 | 数据格式 | 内容说明 | 解析方式 |
|--------|-------------|---------|---------|---------|
| ZCode | `~\.zcode\v2\tasks-index.sqlite` | SQLite | 任务/会话元数据+searchable_text摘要 | sqlite查询 |
| Claude Code | `~\.claude\projects\*\*.jsonl` | JSONL | 完整会话（用户消息+助手回复）| 逐行解析message |
| 豆包（桌面/网页）| `~\Doubao\chats`、`~\.doubao\chats` | 文件产出 | 生成文件（xlsx/pdf/脚本），无对话正文 | 文件索引 |
| Codex（OpenAI CLI）| `~\.codex\sessions\**\rollout-*.jsonl` | JSONL | CLI会话记录 | 逐行解析 |
| 文心一言 | （未发现独立目录，Baidu目录为网盘）| — | 网页版对话在云端 | 需用户导出 |
| Copilot | `~\.copilot`（可能为空）| — | 配置为主 | — |

## 自动发现扫描范围

扫描以下位置，存在即识别为AI数据源：
1. 用户主目录（~）下的：`.zcode`、`.claude`、`.doubao`、`Doubao`、`.codex`、`.kimi`、`.tongyi`、`.deepseek`、`.gemini`、`.chatgpt`、`.copilot`、`.windsurf` 等
2. AppData\Local 和 AppData\Roaming 下的：`Doubao`、`Kimi`、`Tongyi`、`ChatGPT`、`Claude`、`Cursor`、`Codex`、`Zhipu`、`iFlytek`、`Yuanbao` 等
3. 识别方法：目录名匹配 + 存在特征文件（sqlite/jsonl/projects目录）

## 新AI接入流程
1. 安装新AI工具后，运行一次技能（自动发现会扫描到）
2. 若未识别：在 `config.json` sources 手动添加，或在本表追加一行

## 扩展AI清单（v2，自动发现全覆盖）

| AI工具 | 本地数据位置 | 数据格式 |
|--------|-------------|---------|
| Cursor | `~\AppData\Roaming\Cursor` | 会话jsonl/配置 |
| Windsurf | `~\AppData\Roaming\Windsurf` | 会话jsonl |
| Trae | `~\.trae`、`AppData\Roaming\Trae` | 会话/配置 |
| MarsCode | `~\.marscode` | 会话/配置 |
| Cline | `~\.cline` | 会话jsonl |
| RooCode | `~\.roo-code` | 会话jsonl |
| Continue | `~\.continue` | 会话/索引 |
| 通义灵码 | `~\.tongyilingma`、`AppData\Local\TongyiLingma` | 会话/配置 |
| 文心快码 | `~\.comate`、`AppData\Roaming\BaiduComate` | 会话/配置 |
| 讯飞星火 | `AppData\Local\iFlytek`、`Roaming\iFlytek` | 会话/配置 |
| 腾讯元宝 | `AppData\Local\Yuanbao`、`Roaming\Yuanbao` | 会话/配置 |
| WPSAI | `AppData\Roaming\Kingsoft`、`Local\Kingsoft` | 会话/配置 |
| GLMCLI | `~\.glm-cli` | CLI会话 |
| KimiCLI | `~\.kimi-cli` | CLI会话 |
| MiniMax | `AppData\Local\MiniMax`、`Roaming\MiniMax` | 会话/配置 |
| DeepSeekHarness | `~\.dsh\sessions\<工作区>\<会话ID>\session.jsonl.zstd` | **zstd压缩的JSONL**（文件头 28 B5 2F FD）|

> 说明：各AI数据格式不同（sqlite/jsonl/LevelDB/文件产出），技能按格式自动解析；纯云端AI（网页版）需用户导出对话放 import_dir。

## DeepSeek Harness（DSH）会话说明

- **位置**：`~\.dsh\sessions\<工作区编码目录>\<会话ID>\session.jsonl.zstd`，按工作区归档（目录名是工作区路径的编码，如 `--F-2~0020~5DE5~5177-12-DeepSeek-Harness-~63D2~4EF6--` = `F:\2 工具\12-DeepSeek-Harness-插件`）
- **格式**：Zstandard 多帧拼接的 JSONL（文件头魔数 `28 B5 2F FD`），每行一条事件（`user/message`、`assistant/message`、`tool/call`、`session/title` 等）
- **解码方式（提炼前必须）**：用 Node 内置 zstd 解码，脚本 `F:\2 工具\12-DeepSeek-Harness-插件\decode-session.mjs`（零依赖）：
  ```
  node F:\2 工具\12-DeepSeek-Harness-插件\decode-session.mjs <会话文件路径>
  ```
  输出含类型分布 + 会话概览；用 `pwsh` 工具调用，无需给 Python 装 zstandard 库
- **提炼要点**：DSH 会话里 `user/message` 是用户原话，`assistant/message` 是 AI 回复，`tool/call`+`tool/result` 是工具操作（可提炼出"怎么用 DSH 完成 X"的问题链）；按 `模板\会话笔记模板.md` 统一标准提炼
- **导入目录**：`AI会话记忆\DeepSeekHarness\<项目名>\`（第二大脑已有此目录结构）

## sqlite 单文件数据源说明（如 ZCode tasks-index.sqlite）

- ZCode 等 sqlite 数据源是**单文件持续更新**（新会话写在同一个 sqlite 里），旧逻辑只认文件名 → 内容更新永远不会被当作"新增"
- **修复**（2026-08-19）：扫描脚本用**指纹检测**（mtime+size）判断 sqlite 内容是否变化——指纹与上次记录不同 → 报新增；标记（--mark）时记录当前指纹，下次内容不变不再报
- 指纹存于 `scripts/memory_hub_state.json` 的 `sqlite_fingerprints` 字段，无需人工干预
