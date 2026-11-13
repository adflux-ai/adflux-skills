---
name: adflux-skills
description: 通过 adflux 开放 API 生成图片和视频（文生图、参考图生视频、首尾帧生视频），查询可用模型、积分预估与任务结果。当用户要求生成图片、生成视频、查看可用模型或查询生成任务状态时使用。
user-invocable: true
---

# adflux

通过 adflux 开放 API 调用平台的 AI 生图 / 生视频能力。所有调用都是异步任务：提交后拿 `taskNo`，再轮询任务详情拿结果 URL。

## 何时使用

- 用户要生成图片（文生图、参考图、多图、指定尺寸/画质）
- 用户要生成视频（文生视频、参考图生视频、首尾帧）
- 用户要查看当前可用模型及其参数能力
- 用户要查询某次生成任务的进度或结果

不适用：素材库管理、积分余额查询、批量任务编排、模型配置管理。

## 前置条件

| 项 | 要求 |
|---|---|
| Python | 3.8+，只用标准库，不需要 `pip install` |
| `ADFLUX_API_KEY` | 必填，形如 `adfk_xxx`，由平台 Key 管理页创建，绑定员工计费 |
| `ADFLUX_BASE_URL` | 可选，普通用户无需配置；仅私有化部署时覆盖，可只填域名 |
| 安全 | Key 只从环境变量读取；禁止把 Key 写进文件、命令行参数或对话输出 |

## 首次使用

1. 若 skill 尚未安装到当前宿主，先征得用户同意再执行安装（不要擅自写入用户目录）：
   `npx skills add adflux-ai/adflux-skills --skill adflux-skills -g -y`
   没有 Node 的用户改为克隆仓库后，把 `skills/adflux-skills` 链接到宿主 skills 目录。
2. 确认 Python 可用（`python` 或 `py -3`）。
3. 若未配置 `ADFLUX_API_KEY`，引导用户到平台「开放 API / Key 管理」新建 Key 并绑定本租户员工；明文只展示一次。不要要求用户把 Key 贴到对话里，让用户自行写入环境变量。
4. 设置环境变量后需要重开终端，再运行 `python scripts/check.py` 自检。
5. 自检通过后，用一次最低规格生成验证链路，再处理正式需求。

## 执行约定

1. **保留用户提示词**：除非用户明确要求改写或翻译，不要重写 prompt。
2. **不要脑补参数**：用户没指定的比例、分辨率、画质、数量一律不传，交给服务端默认值；不要把示例里的值当成建议值。
3. **不支持的能力要停下**：站内素材库 ID（`referenceAssetImageIds` 等）、站内字段首期不支持，遇到时明确说明并给替代方案，禁止静默丢弃或映射到别的字段。参考视频/音频可以传，本地文件必须先 `upload.py` 上传，生成时用返回的 `id`（推荐）或 `url`。
4. **不要自动重试提交**：生成接口无幂等，重复调用会重复冻结积分；只有在没有拿到 `taskNo` 时才重新提交。
5. **失败不要伪造结果**：任务 `FAILED` / `CANCELLED` 时如实汇报 `errorMessage`，不要用旧结果或占位图代替。

## 端点

| 方法 | 路径 | 用途 |
|---|---|---|
| POST | `/image/estimate` | 图片积分预估，不冻结 |
| POST | `/image/generate` | 提交图片任务，返回 `taskNo` |
| POST | `/video/estimate` | 视频积分预估，不冻结 |
| POST | `/video/generate` | 提交视频任务，返回 `taskNo` |
| GET | `/task/detail?taskNo=` | 任务详情与结果 URL |
| GET | `/model/simple-list?type=` | 可用模型列表（`image` / `video`） |
| POST | `/material/upload` | 上传本地素材（multipart） |

## 推荐流程

### 模型选择

用户未指定模型时不要反问，先 `python scripts/list_models.py --type image`（或 `video`）取当前可用模型，按以下偏好选择：

- 图片：优先 `seedream` 系列，其次该类型第一个可用模型
- 视频：优先 `seedance` 系列，其次该类型第一个可用模型

模型编码以接口返回的 `model` 字段为准，不要硬编码或猜测版本号；列表为空时才告知用户当前没有可用模型。

### 素材引用

| 素材来源 | 做法 |
|---|---|
| 公网图片链接 | 直接 `--reference <URL>` / `--first-frame-url` / `--last-frame-url` |
| 本地图片 / 视频 / 音频 | 先 `upload.py --file`，后续一律用返回的 `id`：`--reference-image-id` / `--reference-video-id` / `--reference-audio-id` / `--first-frame-id` / `--last-frame-id` |

- 本地素材不要用 `upload.py` 返回的 `url` 去生成，它只是约 1 小时的预览地址；`id` 长期有效。
- 参考视频 / 参考音频必须先上传；参考图可以是任意公网 URL。
- 同一素材只传一种：URL 与对应 ID 不要同时传。

### 生成图片

1. `python scripts/list_models.py --type image` 确认模型编码与能力
2. 需要先看预估积分时：`python scripts/generate_image.py --model <modelCode> --prompt "..." --estimate`（只返回 `estimatedCredits`，没有人民币或单价字段）
3. 提交：`python scripts/generate_image.py --model <modelCode> --prompt "..." --count 1`
   - 本地参考图先 `upload.py` 上传，再传 `--reference-image-id <ID>`（也可直接传公网 URL `--reference`）
4. 轮询并落盘：`python scripts/task_detail.py --task-no <taskNo> --watch --download ./adflux_results/<taskNo>`
5. 把 `localPaths` 中的绝对路径给用户；未落盘时再给 `resultUrl`，并说明约 1 小时失效

### 生成视频

1. `python scripts/list_models.py --type video`
2. 按 `generateType` 与 `capabilities` 准备素材：
   - `reference`：参考图（`--reference <公网URL>` 或 `--reference-image-id <ID>`）与参考视频（`--reference-video <URL>` 或 `--reference-video-id <ID>`）至少一个；参考音频（`--reference-audio` / `--reference-audio-id`）不能单独使用，须搭配至少 1 个参考图或视频
   - `frame`：首帧（`--first-frame-url` 或 `--first-frame-id`）+ 尾帧（`--last-frame-url` 或 `--last-frame-id`）
   - 本地上传的素材用 `upload.py` 返回的 `id` 传 `--reference-*-id` / `--first-frame-id` / `--last-frame-id`；只有参考视频/音频必须来自上传，参考图可以是任意公网 URL
   - 单段/合计时长不要超过 `capabilities.min/maxReferenceVideoDurationSec`、`maxReferenceVideoTotalSec`、`min/maxReferenceAudioDurationSec`、`maxReferenceAudioTotalSec`
3. 提交：`python scripts/generate_video.py --model <modelCode> --prompt "..." --resolution 1080p --duration 5 --generate-type reference --reference-image-id 123`
   - `--resolution` / `--duration` 的合法值以 `list_models.py` 返回的 `capabilities.resolution`、`minDurationSec`/`maxDurationSec` 为准（分辨率大小写敏感）
4. 轮询并落盘：`python scripts/task_detail.py --task-no <taskNo> --watch --download ./adflux_results/<taskNo>`
5. 视频由平台定时任务结算，轮询到 `SUCCESS` 即完成，结果同样落盘后给本地路径

## 结果呈现

任务结束后用固定结构回复（用户语言，默认中文）；宿主支持时同时展示图片预览或视频文件：

```markdown
**<图片|视频>已生成 ✅**

**规格**：<宽×高> · `<modelCode>` · <文生图|图生图|文生视频|图生视频> · <时长>

**内容要点**
- <主体与场景>
- <构图 / 镜头 / 光线>
- <色调 / 风格>

**文件**
`<本地绝对路径>`

本次生成消耗 <actualCredits> 积分。

**说明**
- <仅在使用了默认值、调整过参数或能力受限时出现>

**可调整方向**
- <1~3 个具体、模型确实支持的调整>

告诉我要改哪一点即可。
```

规则：

1. 状态行按 `status` 写：`SUCCESS` → 已生成 ✅；`FAILED` → 生成失败 ❌；`CANCELLED` → 已取消 ⏹。失败或取消时给出 `errorMessage`，跳过其余小节。
2. 规格只写接口真实返回或提交参数里的值：宽高取 `results[].width/height`，模型取提交的 `modelCode`，时长取 `durationSeconds`；未知项直接省略，不要猜。
3. 积分只在 `actualCredits` 有值时展示，禁止估算或编造。
4. 文件优先给 `--download` 落盘的绝对路径；未落盘时给 `resultUrl`，并提示约 1 小时失效。
5. 可调整方向只建议模型实际支持的能力，以 `capabilities` 为准：分辨率看 `resolution`、比例看 `ratio`、模式看 `generateType`、输出时长看 `minDurationSec`/`maxDurationSec`，参考素材上限看 `maxReference*` / `*ReferenceDurationSec`。
6. 不要粘贴原始 JSON、`taskNo`、端点或脚本输出，除非用户主动要求。

## 脚本

| 脚本 | 用途 |
|---|---|
| `scripts/check.py` | 自检环境变量与连通性 |
| `scripts/list_models.py` | 列出可用模型 |
| `scripts/generate_image.py` | 图片预估 / 提交（`--estimate` 只预估） |
| `scripts/generate_video.py` | 视频预估 / 提交（`--estimate` 只预估） |
| `scripts/task_detail.py` | 任务详情，`--watch` 自动轮询，`--download DIR` 下载结果到本地 |
| `scripts/upload.py` | 上传本地图片 / 视频 / 音频 |

每个脚本都支持 `--help` 与 `--dry-run`。`--dry-run` 只打印将要发送的请求（Key 已脱敏），不发网络请求。

## 输出约定

- 成功：stdout 输出 JSON（`taskNo`、模型列表、任务详情等）
- 失败：stderr 输出 `{"error": "...", "code": ...}`，退出码非 0
- 参数错误由 argparse 直接返回非 0，不发起请求

## 限制与注意事项

| 项 | 说明 |
|---|---|
| 幂等 | 生成接口不做幂等，重复调用会重复冻结积分 |
| 结果 URL | 签名地址约 1 小时失效；建议用 `task_detail.py --download` 落盘，或过期后重新查询 |
| 并发 | 图片生成与站内共享并发额度，拿不到许可会以 `CONCURRENCY_TIMEOUT` 失败并退费 |
| 限流 | 没有 Key 级限流，也不提供开放配额承诺；不要依赖站内通道限流值 |
| 素材 | 参考图可直接传公网 URL；**参考视频/音频必须先 `upload.py` 上传**；上传返回的 `id` 长期有效，优先用素材 ID 引用，`url` 只是 1 小时预览地址；内网、回环、链路本地地址会被拒绝 |
| 素材归属 | 素材 ID 按 Key 绑定员工隔离，只能引用该员工自己上传的素材 |
| 内部字段 | 站内素材库 ID（`referenceAssetImageIds`、`firstFrameAssetId` 等）不支持，传了会 400；`reference*MaterialIds` / `firstFrameMaterialId` / `lastFrameMaterialId` 是上传素材 ID，支持 |
| 模型 | 不要硬编码模型清单，运行时用 `list_models.py` 获取 |

## 错误处理

错误码与处置建议见 `references/errors.md`。常见动作：

- HTTP 401：Key 无效 / 停用 / 过期 / 绑定员工不可用 → 让用户在 Key 管理页核对或重建
- `1040004002`：积分不足 → 提示充值或换绑定员工
- `400`：参数不合法（空提示词、`generateType` 与素材不匹配、内网 URL）→ 修正参数后重试
- `1040008000`：任务不存在 → 确认 `taskNo` 与 Key 属于同一员工

## 安装与更新

- 安装：`npx skills add adflux-ai/adflux-skills -g -y`
- 更新：`npx skills update adflux-skills`
- 若提示“请更新 adflux”，执行上面的更新命令，不要手工改脚本
