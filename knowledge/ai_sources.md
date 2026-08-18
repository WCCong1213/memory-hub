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

> 说明：各AI数据格式不同（sqlite/jsonl/LevelDB/文件产出），技能按格式自动解析；纯云端AI（网页版）需用户导出对话放 import_dir。
