---
name: adflux-skills
description: 通过 adflux 开放 API 生成图片和视频（文生图、参考图生视频、首尾帧生视频、视频编辑、视频延长），查询可用模型、生成记录与素材、积分预估与任务结果。当用户要求生成图片、生成视频、编辑已有视频、延长已有视频、查看可用模型、查询生成任务状态，或列出历史生成记录 / 已有素材以便复用时使用本技能。
user-invocable: true
---

# adflux

通过 adflux 开放 API 调用平台的 AI 生图 / 生视频能力。所有调用都是异步任务：提交后拿 `taskNo`，再轮询任务详情拿结果 URL。

## 何时使用

- 用户要生成图片（文生图、参考图、多图、指定尺寸/画质）
- 用户要生成视频（文生视频、参考图生视频、首尾帧、视频编辑、视频延长）
- 用户要查看当前可用模型及其参数能力
- 用户要查询某次生成任务的进度或结果
- 用户要查看历史生成记录、列出已生成的图片 / 视频，或复用某个素材继续创作

不适用：素材删除 / 重命名、积分余额查询、批量任务编排、模型配置管理。

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
2. 检测 Python：依次尝试 `python`、`py -3`、`python3`，静默选第一个可用且版本 ≥ 3.8 的解释器，不要把命令或版本号抛给用户。
   - 都不可用时，只回一句：「这个技能需要先装一下 Python（免费），装完告诉我一声就能继续」，并给出 https://www.python.org/downloads/ ；Windows 提醒安装时勾选 "Add python.exe to PATH"。
   - 不要解释 Python 是什么，不要列 pip、环境变量或排查步骤；用户确认装好后重新检测一次再继续。
3. 若未配置 `ADFLUX_API_KEY`，引导用户到 [adflux](https://adflux.cn) 的「开放 API / Key 管理」新建 Key 并绑定本租户员工；明文只展示一次。不要要求用户把 Key 贴到对话里，让用户自行写入环境变量。
4. 设置环境变量后需要重开终端，再用检测到的解释器运行 `scripts/check.py` 自检。
5. 自检通过后，用一次最低规格生成验证链路，再处理正式需求。

## 执行约定

1. **保留用户提示词**：除非用户明确要求改写或翻译，不要重写 prompt。
2. **不要脑补参数**：用户没指定的比例、分辨率、画质、数量一律不传，交给服务端默认值；不要把示例里的值当成建议值。
3. **不支持的能力要停下**：内部字段（站内素材库 ID 等）首期不支持，遇到时明确说明并给替代方案，禁止静默丢弃或映射到别的字段。参考视频/音频可以传，本地文件先 `upload.py` 上传，站内已有素材先 `list_materials.py` 查 `id`，生成时统一用素材 `id` 引用。
4. **不要自动重试提交**：生成接口无幂等，重复调用会重复冻结积分；只有在没有拿到 `taskNo` 时才重新提交。轮询超时、任务 `FAILED` 或连接中断都算「已拿到 `taskNo`」，不得重新提交。
5. **失败不要伪造结果**：任务 `FAILED` / `CANCELLED` 时如实汇报 `errorMessage`，不要用旧结果或占位图代替。
6. **超时不等于失败**：`--watch` 超时只表示本次等待结束，任务仍在执行；用同一 `taskNo` 继续查询，必要时加大 `--max-wait`。不要结束任务，也不要让用户重述需求。

## 端点

| 方法 | 路径 | 用途 |
|---|---|---|
| POST | `/image/estimate` | 图片积分预估，不冻结 |
| POST | `/image/generate` | 提交图片任务，返回 `taskNo` |
| POST | `/video/estimate` | 视频积分预估，不冻结 |
| POST | `/video/generate` | 提交视频任务，返回 `taskNo` |
| GET | `/task/detail?taskNo=` | 任务详情与结果 URL |
| GET | `/task/page` | 按日期分页查询生成记录（仅本 Key 员工、`source=open-api`） |
| GET | `/model/simple-list?type=` | 可用模型列表（`image` / `video` / `video_enhance`） |
| POST | `/material/upload` | 上传本地素材（multipart） |
| GET | `/material/page` | 分页查询素材，默认只返回开放任务产物 |

## 推荐流程

### 模型选择

用户未指定模型时不要反问，先 `python scripts/list_models.py --type image`（或 `video`）取当前可用模型，按以下偏好选择：

- 图片：优先 `seedream` 系列，其次该类型第一个可用模型
- 视频：优先 `seedance` 系列，其次该类型第一个可用模型
- 视频编辑 / 延长：先按 `capabilities.videoTaskTypes` 过滤，只在该值包含 `edit` / `extend` 的模型里选；没有可用模型时直接告知用户，不要提交后吃 400

模型编码以接口返回的 `model` 字段为准，不要硬编码或猜测版本号；列表为空时才告知用户当前没有可用模型。

提交前的告知分三档：

| 场景 | 提交前动作 |
|---|---|
| 图片单张、用户未指定模型 | 自动选择后一句话说明将使用的模型名称与规格，然后直接提交 |
| 视频、多图（`--count > 1`）或用户要求高分辨率 / 长时长 | 先 `--estimate` 取 `estimatedCredits`，说明模型名称与预估积分并请用户确认，确认后再提交 |
| 用户已指定模型 | 直接提交，不再重复确认 |

- 对用户只写模型名称（`name`），不写 `modelCode`
- 提交前的说明用陈述句，例如「用 Seedream 5.0 生成一张 1024×1024，约需 120 积分」，不要问「你想用哪个模型」
- 预估积分只取 `--estimate` 的返回值，取不到就省略，不自行估算
- 用户不确认则不提交，可建议换模型或降低规格

### 素材引用

复用优先用素材 ID：站内已有素材（历史生成产物 / 已上传）先查 `id`，不要让用户重新上传或重新给 URL。

| 素材来源 | 做法 |
|---|---|
| 站内已有素材（历史产物 / 已上传） | 先 `list_materials.py` 取 `id`（如 `--media-type VIDEO --task-no <taskNo>`），再传 `--reference-image-id` / `--reference-video-id` / `--reference-audio-id` / `--first-frame-id` / `--last-frame-id` |
| 公网图片链接 | 直接 `--reference <URL>` / `--first-frame-url` / `--last-frame-url`（仅限外部临时图片） |
| 本地图片 / 视频 / 音频 | 先 `upload.py --file`，后续一律用返回的 `id`（参数同上） |

- 上传返回的 `url` 只是约 1 小时的预览地址，不要拿去生成；`id` 长期有效。
- 参考视频 / 参考音频必须来自当前员工名下素材（上传或历史产物），不能用外链；参考图可临时用公网 URL。
- 同一素材只传一种：URL 与对应 ID 不要同时传。

### 生成图片

1. `python scripts/list_models.py --type image` 确认模型编码与能力
2. 需要先看预估积分时：`python scripts/generate_image.py --model <modelCode> --prompt "..." --estimate`（只返回 `estimatedCredits`，没有人民币或单价字段）
3. 提交：`python scripts/generate_image.py --model <modelCode> --prompt "..." --count 1`
   - 本地参考图先 `upload.py` 上传，再传 `--reference-image-id <ID>`（外部临时图片也可直接传公网 URL `--reference`）
   - 用户要复用之前生成的图时，先 `python scripts/list_materials.py --media-type IMAGE --task-no <taskNo>` 取 `id` 直接传，不要要求重新上传
4. 轮询并落盘：`python scripts/task_detail.py --task-no <taskNo> --watch --download ./adflux_results/<taskNo>`
5. 把 `localPaths` 中的绝对路径给用户；未落盘时再给 `resultUrl`，并说明签名地址约 1 小时有效（文件长期保存在平台，过期重新查询即可）

### 生成视频

1. `python scripts/list_models.py --type video`
2. 按 `generateType` 与 `capabilities` 准备素材：
   - `text`（默认，隐式支持，不会出现在 `capabilities.generateType` 中）：纯文生视频，只传提示词，不要传任何参考素材或首尾帧
   - `reference`：参考图（`--reference <公网URL>` 或 `--reference-image-id <ID>`）、参考视频（`--reference-video <URL>` 或 `--reference-video-id <ID>`）、参考音频（`--reference-audio` / `--reference-audio-id`）至少一个；参考音频单独使用仅 Seedance 2.5 系列（含 flash）支持，2.0 系列仍须搭配至少 1 个参考图或视频，否则后端返回 400
   - `frame`：首帧（`--first-frame-url` 或 `--first-frame-id`）+ 尾帧（`--last-frame-url` 或 `--last-frame-id`）
   - 本地或站内已有素材（含历史产物）优先用素材 ID：本地先 `upload.py`，站内先 `list_materials.py` 取 `id`，再传 `--reference-*-id` / `--first-frame-id` / `--last-frame-id`；参考视频 / 音频必须是当前员工名下素材，参考图可临时用公网 URL
   - 单段/合计时长不要超过 `capabilities.min/maxReferenceVideoDurationSec`、`maxReferenceVideoTotalSec`、`min/maxReferenceAudioDurationSec`、`maxReferenceAudioTotalSec`
   - 参考素材上限按所选模型取，**2.5 与 2.5 flash 不同**：2.5 为图 30 / 视频 10 / 音频 10，2.5 flash 为图 10 / 视频 5 / 音频 5；统一看 `capabilities.maxReferenceImageCount` / `maxReferenceVideoCount` / `maxReferenceAudioCount`，不要按模型名硬套
   - 视频编辑 / 延长用 `--video-task-type` 显式声明（仅当 `capabilities.videoTaskTypes` 含该值）：
     - `edit`（视频编辑）：必须恰好 1 个原片，通过 `--reference-video-id <ID>`（或 `--reference-video <URL>`）传入，长度 4~30s；`--duration` 取 `upload.py` 返回的 `duration`（服务端仍会用原片元数据覆盖）；不能传首尾帧；可同时传参考图（`--reference`），提示词用 `@图片N` 引用；输出时长可能短于原片，以任务详情 `durationSeconds` 为准
     - `extend`（视频延长）：至少 1 个视频，第一个为原片，其余为额外参考视频；`--duration` 传本次**新增片段**秒数（4~30s，上限看模型能力），产物只含续接片段，不含原片；原片必须放第一位，参考视频只用一种来源（全部 `--reference-video` 或全部 `--reference-video-id`，混用会改变顺序）；可叠加参考图 / 参考音频
     - 两者固定 `generateType=reference`；`--resolution` 仍必填，取值以 `capabilities.resolution` 为准（如 480p / 720p），分辨率按传入档位生效；编辑 / 延长不支持设置比例，输出比例由服务端按原片覆盖
3. 提交：`python scripts/generate_video.py --model <modelCode> --prompt "..." --resolution 720p --duration 5`
   - 不传 `--generate-type` 即纯文生视频（`text`）；带素材时显式指定：
     - `--generate-type reference --reference https://example.com/a.jpg`
     - `--generate-type frame --first-frame-url https://example.com/a.jpg --last-frame-url https://example.com/b.jpg`
   - 编辑原片：`--video-task-type edit --resolution 720p --reference-video-id <原片ID> --reference https://example.com/product.jpg --duration <原片时长> --prompt "把 @图片1 中的商品替换到 @视频1 对应位置，保持镜头、节奏、时长和其他画面不变"`
   - 延长原片：`--video-task-type extend --resolution 720p --reference-video-id <原片ID> --duration 6 --prompt "向后延长 @视频1，镜头继续推进，补充第二个卖点"`
   - 普通生成的 `--resolution` 以 `capabilities.resolution` 为准（大小写敏感）；编辑 / 延长按 480p / 720p 传；`--duration` 合法值以 `capabilities.minDurationSec` / `maxDurationSec` 为准
4. 轮询并落盘：`python scripts/task_detail.py --task-no <taskNo> --watch --download ./adflux_results/<taskNo>`
   - `--watch` 默认最多等 600 秒；视频可能更久，可加 `--max-wait 1800`，超时后继续用同一 `taskNo` 查询，不要重新提交
5. 视频由平台定时任务结算，轮询到 `SUCCESS` 即完成，结果同样落盘后给本地路径

### 视频画质提升

输入现成视频，输出更高清的视频，内容不变；不需要提示词、时长、比例。

1. `python scripts/list_models.py --type video_enhance` 确认可用参数（分辨率 720p / 1080p / 2k / 4k，版本 LITE，码率 low / medium / high）
2. 输入视频必须是当前员工名下的视频素材：新文件用 `python scripts/upload.py --file ./input.mp4`；复用已有视频（含历史生成产物）用 `python scripts/list_materials.py --media-type VIDEO` 取 `id`
3. 预估：`python scripts/generate_enhance.py --video-material-id <ID> --resolution 1080p --estimate`
4. 提交：`python scripts/generate_enhance.py --video-material-id <ID> --resolution 1080p`（如需调码率加 `--bitrate-level high`）
5. 轮询并落盘：`python scripts/task_detail.py --task-no <taskNo> --watch --download ./adflux_results/<taskNo>`
   - 产物会转存到平台自有存储并写入员工素材库，`resultUrl` 为自有存储签名地址（约 1 小时有效）；落盘后给本地路径

### 查询记录与复用素材

用户要「看看之前生成了什么 / 找一条原片继续编辑 / 复用已有素材」时：

1. 查生成记录：`python scripts/list_tasks.py --page-size 10 --start 2026-11-01`
   - 支持 `--status`、`--business-type`、`--task-no`、`--start/--end`；创建时间跨度不能超过 31 天
   - 每条记录的 `date` 可直接用于按天分组，`results[].resultUrl` 为自有存储签名地址（约 1 小时有效）
2. 查素材：`python scripts/list_materials.py --media-type VIDEO --task-no <taskNo>`
   - 默认只返回开放任务产物（`source=TASK_OUTPUT`）；上传的素材用 `--source UPLOAD`
   - 返回的 `id` 长期有效，可直接作为 `--reference-image-id` / `--reference-video-id` / `--first-frame-id` 等入参复用；`url` 是自有存储签名地址（约 1 小时有效）
3. 结果地址过期时重新查一次即可，不要缓存 URL。

查询结果只包含当前 Key 绑定员工的记录与素材，跨员工 / 跨租户不可见。

## 结果呈现

任务结束后用固定结构回复（用户语言，默认中文）；宿主支持时同时展示图片预览或视频文件：

```markdown
**<图片|视频>已生成 ✅**

**规格**：<宽×高> · <模型名称> · <文生图|图生图|文生视频|参考生成|视频编辑|视频延长> · <时长>

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
2. 规格只写接口真实返回或提交参数里的值：宽高取 `results[].width/height`，时长取 `durationSeconds`；视频任务的类型取任务详情的 `videoTaskType`（`edit` → 视频编辑，`extend` → 视频延长，`reference` → 参考生成）；模型优先取任务详情返回的 `modelName`，没有则用本次提交时 `list_models.py` 返回的 `name`，再没有才用 `modelCode`，都没有就省略。未知项直接省略，不要猜。
3. 积分只在 `actualCredits` 有值时展示，禁止估算或编造。
4. 文件优先给 `--download` 落盘的绝对路径；未落盘时给 `resultUrl`，并提示签名地址约 1 小时有效（文件长期保存在平台，过期重新查询即可；已落盘的本地文件不受影响）。
5. 可调整方向只建议模型实际支持的能力，以 `capabilities` 为准：分辨率看 `resolution`、比例看 `ratio`、模式看 `generateType`（`text` 为隐式模式，不会出现在该字段中）、能否编辑 / 延长看 `videoTaskTypes`、输出时长看 `minDurationSec`/`maxDurationSec`，参考素材上限看 `maxReference*` / `*ReferenceDurationSec`。
6. 不要粘贴原始 JSON、`taskNo`、端点或脚本输出，除非用户主动要求。
7. 模型是自动选择时，在「说明」里加一句「本次自动使用 <模型名称>，如需换模型可直接指定」；用户自己指定模型时不加。

## 脚本

| 脚本 | 用途 |
|---|---|
| `scripts/check.py` | 自检环境变量与连通性 |
| `scripts/list_models.py` | 列出可用模型 |
| `scripts/generate_image.py` | 图片预估 / 提交（`--estimate` 只预估） |
| `scripts/generate_video.py` | 视频预估 / 提交（`--estimate` 只预估；`--video-task-type` 支持 reference / edit / extend） |
| `scripts/generate_enhance.py` | 视频画质提升预估 / 提交（`--estimate` 只预估；输入用 `--video-material-id` 或 `--video-url`） |
| `scripts/task_detail.py` | 任务详情，`--watch` 自动轮询，`--download DIR` 下载结果到本地 |
| `scripts/list_tasks.py` | 分页查询生成记录（按日期 / 状态 / 业务类型 / taskNo） |
| `scripts/list_materials.py` | 分页查询素材（默认 `TASK_OUTPUT`，可按类型 / taskNo / 时间） |
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
| 等待 | `--watch` 默认最多等 600 秒；超时只表示本次等待结束，任务仍在执行，继续用同一 `taskNo` 查询，不要重新提交 |
| 结果 URL | 开放 API 产物会异步转存到平台自有存储，`task_detail.py` / `list_tasks.py` / `list_materials.py` 返回的地址都是自有存储签名地址（约 1 小时有效）；**文件本身长期保存在平台**，过期重新查询即可，不要缓存。上传素材的 `url` 同样是 1 小时预览地址，素材 `id` 长期有效 |
| 并发 | 图片生成与其他业务共享并发额度，拿不到许可会以 `CONCURRENCY_TIMEOUT` 失败并退费 |
| 限流 | 没有 Key 级限流，也不提供开放配额承诺；不要依赖其他通道的限流值 |
| 素材 | 站内已有素材（历史产物 / 已上传）优先用 `list_materials.py` 查 `id` 复用，不要要求重新上传；参考视频 / 音频必须来自当前员工名下素材，参考图可临时传公网 URL；上传返回的 `id` 长期有效，`url` 只是 1 小时预览地址；内网、回环、链路本地地址会被拒绝 |
| 素材归属 | 素材 ID 按 Key 绑定员工隔离，只能引用该员工名下素材（上传或历史产物） |
| 内部字段 | 仅支持本文列出的开放字段；站内素材库 ID 等内部字段传了会 400；`reference*MaterialIds` / `firstFrameMaterialId` / `lastFrameMaterialId` 是上传素材 ID，支持 |
| 模型 | 不要硬编码模型清单，运行时用 `list_models.py` 获取 |

## 错误处理

错误码与处置建议见 `references/errors.md`。常见动作：

- HTTP 401：Key 无效 / 停用 / 过期 / 绑定员工不可用 → 让用户在 Key 管理页核对或重建
- `1040004002`：积分不足 → 提示充值或换绑定员工
- `400`：参数不合法（空提示词、`generateType` 与素材不匹配、内网 URL）→ 修正参数后重试
- `1040008000`：任务不存在 → 确认 `taskNo` 与 Key 属于同一员工

## 安装与更新

- 安装：`npx skills add adflux-ai/adflux-skills --skill adflux-skills -g -y`
- 更新：`npx skills update adflux-skills`
- 若提示“请更新 adflux”，执行上面的更新命令，不要手工改脚本
