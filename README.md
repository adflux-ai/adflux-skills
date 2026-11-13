<p align="center">
  <img src="assets/logo.webp" alt="adflux" width="280">
</p>

# adflux-skills

> AI Agent Skills for [adflux](https://adflux.cn/) — 让你的 AI Agent 直接调用 adflux 开放 API 的生图、生视频能力。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-green.svg)](https://python.org)

## ✨ 简介

**adflux-skills** 是一个面向 AI Agent 的技能包，通过 adflux 开放 API 提供 **AI 生图**、**AI 生视频** 能力。Agent 可以按用户的自然语言需求选择模型、上传本地参考素材、提交生成任务、轮询进度，并把最终的图片 / 视频下载到本地。

本技能遵循 `SKILL.md` 技能规范，可被 `npx skills` 以及支持该规范的 AI Agent 平台（Claude Code、Trae、CodeBuddy、Cursor、Codex 等）直接识别和调用。

## 📦 技能列表

| 技能 | 描述 | 主要脚本 |
|------|------|----------|
| **adflux-skills** | adflux 生图 / 生视频技能 — 查询模型、积分预估、提交任务、轮询进度并下载结果 | `generate_image.py` `generate_video.py` `task_detail.py` |

## 📥 快速安装

通过 `npx skills` 一键安装技能：

```bash
# 交互式选择要安装的技能
npx skills add adflux-ai/adflux-skills

# 直接安装指定技能
npx skills add adflux-ai/adflux-skills --skill adflux-skills

# 安装到用户级（所有项目共用），并指定宿主
npx skills add adflux-ai/adflux-skills --skill adflux-skills -g -a claude-code -y
```

- 默认安装到当前项目的 `.claude/skills` 等目录；`-g` 安装到用户级
- `-a` 指定宿主，`--copy` 改为复制而不是链接
- 在 Agent、CI 等非交互环境中安装时，加 `-y` 跳过确认：`npx -y skills add adflux-ai/adflux-skills --skill adflux-skills -g -y`
- 没有 Node 时：`git clone https://github.com/adflux-ai/adflux-skills.git`，把 `skills/adflux-skills` 链接或复制到宿主的 skills 目录

### 🔄 更新技能

```bash
# 更新用户级技能
npx skills update adflux-skills -g -y

# 查看已安装的技能
npx skills ls -g
```

如果 `update` 提示已是最新但仓库确实有新提交，重新执行一次 `npx skills add ...` 覆盖本地副本即可。更新只替换技能文件，不影响环境变量；更新后请重启 Agent 或新开会话。

### ⚙️ 配置 API Key

还没有 Key 时，先在 adflux 平台创建：

1. 打开 [adflux](https://adflux.cn/)。
2. 登录后进入「开放 API / Key 管理」。
3. 新建 Key，选择一个本租户员工作为计费对象。
4. 创建成功后立即复制（明文只展示一次，关闭后无法再次查看）。

创建完成后，把 Key 设置为环境变量：

```bash
# macOS / Linux
export ADFLUX_API_KEY="adfk_xxxxxxxx"
```

```powershell
# Windows PowerShell（当前会话）
$env:ADFLUX_API_KEY = "adfk_xxxxxxxx"
```

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `ADFLUX_API_KEY` | ✅ | — | 开放 API 鉴权密钥，`adfk_` 开头 |
| `ADFLUX_BASE_URL` | ❌ | 内置 | 仅私有化部署时覆盖，普通用户无需配置（可只填域名） |

> ⚠️ API Key 属于机密信息：请只通过环境变量配置，不要写入项目文件、提交到代码仓库，或粘贴到提示词 / 日志中。

> 🎉 **就这么简单！** 安装后直接在 Agent 里提需求即可，例如：
>
> - “用 adflux-skills 生成一张雨夜霓虹街道的电影感海报。”
> - “把这张图片作为参考，生成一段 5 秒的产品展示视频。”
> - “列出 adflux 当前可用的视频模型。”

## 🧠 支持的模型

模型清单不写死在技能里，运行时从接口读取：

```bash
python3 skills/adflux-skills/scripts/list_models.py --type image
python3 skills/adflux-skills/scripts/list_models.py --type video
```

各模型的分辨率、比例、数量等参数能力以返回的 `capabilities`（JSON Schema）为准；平台新增模型不需要升级技能。

## 🛠️ 手动使用 / 调试

<details>
<summary>点击展开：自检、预估、生成、上传与下载</summary>

### 前置要求

- **Python 3.8+**（仅使用标准库，无需安装依赖；Windows 如无 `python3`，请用 `python` 或 `py -3`）
- **`ADFLUX_API_KEY`** 环境变量已设置

### 自检

```bash
python3 skills/adflux-skills/scripts/check.py
```

### 预估积分（不冻结）

```bash
python3 skills/adflux-skills/scripts/generate_image.py --model <modelCode> --prompt "海边日落" --estimate
```

### 提交生图

```bash
python3 skills/adflux-skills/scripts/generate_image.py --model <modelCode> --prompt "海边日落，电影感" --count 1 --quality 2k
```

### 提交生视频

```bash
python3 skills/adflux-skills/scripts/generate_video.py --model <modelCode> --prompt "镜头缓慢推进" \
  --resolution 1080p --duration 5 --generate-type reference --reference https://example.com/a.jpg
```

### 轮询并下载

```bash
python3 skills/adflux-skills/scripts/task_detail.py --task-no <taskNo> --watch --download ./adflux_results/<taskNo>
```

`status` 变为 `SUCCESS` 后，各结果的 `localPath` 即本地绝对路径。

### 上传本地素材

```bash
python3 skills/adflux-skills/scripts/upload.py --file ./poster.png --tags "海报,产品"
```

上传响应里的 `id` 是长期稳定的素材句柄，生成时优先用素材 ID 引用；`url` 只是约 1 小时的预览地址。参考图也可直接传公网 URL；参考视频 / 参考音频必须先上传。

所有脚本都支持 `--help` 与 `--dry-run`；`--dry-run` 只打印请求（Key 脱敏），不发网络请求。

</details>

## 📁 项目结构

```text
adflux-skills/
├── README.md
├── LICENSE
├── .gitignore
├── assets/
│   └── logo.webp
└── skills/
    └── adflux-skills/
        ├── SKILL.md                # 技能描述文件
        ├── references/
        │   └── errors.md           # 错误码与处置
        └── scripts/
            ├── _client.py          # 公共请求、鉴权、错误映射
            ├── check.py            # 自检
            ├── list_models.py      # 模型列表
            ├── generate_image.py   # 图片预估 / 提交
            ├── generate_video.py   # 视频预估 / 提交
            ├── task_detail.py      # 查询 / 轮询 / 下载
            └── upload.py           # 上传本地素材
```

## 🔧 API 参考

### 鉴权

所有请求通过 HTTP Header 鉴权：

```
Authorization: Bearer <ADFLUX_API_KEY>
```

### 接口列表

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/image/estimate` | 图片积分预估（不冻结） |
| `POST` | `/image/generate` | 提交图片生成任务 |
| `POST` | `/video/estimate` | 视频积分预估（不冻结） |
| `POST` | `/video/generate` | 提交视频生成任务 |
| `GET` | `/task/detail?taskNo=` | 查询任务详情与结果 |
| `GET` | `/model/simple-list?type=` | 可用模型列表 |
| `POST` | `/material/upload` | 上传图片 / 视频 / 音频素材 |

完整字段、错误码与调用限制以平台开放 API 文档为准。

## 🤖 Agent 集成指南

典型工作流：

```text
用户指令 → list_models.py 选择模型
              ↓
   （有本地素材）upload.py → 素材 ID
              ↓
   generate_image.py / generate_video.py → taskNo
              ↓
   task_detail.py --watch --download → 本地文件
              ↓
        向用户展示生成结果
```

### 最佳实践

- **参数不脑补**：用户未指定比例、分辨率、画质、数量时省略对应参数，交给服务端默认值
- **先预估后提交**：需要展示预估积分时用 `--estimate`，不冻结积分
- **结果落盘**：签名 URL 约 1 小时失效，用 `--download` 保存本地
- **失败不伪造**：任务 `FAILED` / `CANCELLED` 时如实返回 `errorMessage`
- **不自动重试提交**：生成接口无幂等，重复调用会重复冻结积分
- **先 dry-run**：不确定的参数组合先加 `--dry-run` 检查请求

## ⚠️ 使用限制

- **无幂等**：重复提交会重复冻结积分，重试前先确认上次是否已返回 `taskNo`
- **结果 URL 1 小时失效**：用 `task_detail.py --download` 落盘，或过期后重新查询
- **并发共享**：图片生成与站内业务共用并发额度，高峰可能 `CONCURRENCY_TIMEOUT` 后自动退费
- **内部字段不开放**：站内素材库 ID（`referenceAssetImageIds` 等）、站内字段传了会被拒绝或覆盖；上传素材 ID（`reference*MaterialIds` / `firstFrameMaterialId` / `lastFrameMaterialId`）支持
- **素材要求**：参考视频 / 参考音频必须先 `upload.py` 上传；素材 ID 按 Key 绑定员工隔离；内网、回环地址会被拒绝

## 🤝 贡献

- 改动脚本后运行 `python -m unittest discover -s tests`
- 接口契约变化时同步 `docs/adflux-open-api.md` 与 `SKILL.md`
- 合并到 `master` 即发布；GitHub 仓为对外公开镜像

## 📄 License

本项目采用 [MIT License](LICENSE) 开源。
