# adflux 错误码与处置

## 认证失败（HTTP 401）

| code | 含义 | 用户可执行的动作 |
|---|---|---|
| `1040024000` | Key 不存在（含非 `adfk_` 前缀的任意未知串） | 在 Key 管理页确认 Key 是否已被删除，重新创建 |
| `1040024001` | Key 无效（未携带 / 空值） | 检查 `ADFLUX_API_KEY` 是否为 `adfk_` 开头且完整 |
| `1040024002` | Key 已停用 | 在 Key 管理页重新启用，或新建 Key |
| `1040024003` | Key 已过期 | 新建 Key 并替换环境变量 |
| `1040024004` | 绑定员工不存在 / 已停用 / 不属于该租户 | 联系租户管理员把 Key 改绑到在职员工 |

401 一律先看认证，不要重试；重复调用不会成功。

## 业务失败（HTTP 200，`code != 0`）

| code | 含义 | 处置 |
|---|---|---|
| `400` | 参数不合法 | 按 `msg` 修正后重试，常见原因见下 |
| `1040004002` | 积分不足 | 充值，或把 Key 改绑到有积分的员工 |
| `1040001000` | 模型不存在 | 用 `list_models.py` 重新获取 `modelCode` |
| `1040001001` | 模型已禁用 | 换一个可用模型 |
| `1040001004` | 分辨率不支持 | 按模型 `capabilities.resolution` 选择 |
| `1040001005` | 画面比例不支持 | 按 `capabilities.ratio` 选择 |
| `1040008000` | 任务不存在 | 确认 `taskNo`，且任务属于当前 Key 绑定的员工 |
| `1040006000` ~ `1040006004` | 素材相关失败 | 检查文件格式、大小、素材归属 |

## `400` 的高频原因

| 原因 | 修正 |
|---|---|
| `prompt` 为空或只有空白 | 提供非空提示词 |
| 视频未传 `generateType` | 显式传 `reference` / `frame` |
| `reference` 既没传参考图也没传参考视频 | 至少一个 `--reference <公网URL>`、`--reference-image-id` 或 `--reference-video` / `--reference-video-id` |
| `frame` 缺首帧或尾帧 | 同时传首帧与尾帧（URL 或素材 ID） |
| 参考视频/音频用了外部直链 | 先用 `upload.py` 上传，再传返回的 `id`（推荐）或 `url`（服务端需解析时长计费） |
| 参考视频/音频时长超限 | 按 `capabilities.min/maxReferenceVideoDurationSec`、`maxReferenceVideoTotalSec`、`min/maxReferenceAudioDurationSec`、`maxReferenceAudioTotalSec` 调整 |
| 参考素材是内网地址 | 换成公网可访问的 http/https URL |
| 分辨率/比例的大小写与返回值不一致 | 按 `capabilities.resolution` / `capabilities.ratio` 原样传（如 `480P`、`768P`、`2K`） |
| 传了站内素材库 ID 字段（`referenceAssetImageIds` 等） | 不支持，改用 `/material/upload` 返回的 `reference*MaterialIds` 或公网 URL |
| 素材 ID 不存在 / 类型不符 / 跨员工 | 确认 `id` 来自当前 Key 绑定员工的 `upload.py` 上传结果，且媒体类型与字段匹配（图片 / 视频 / 音频） |
| 把素材 ID 传进了 `--reference` / `--first-frame-url` 等 URL 参数 | 会报「需要 http/https URL」；本地素材改用 `--reference-image-id` / `--reference-video-id` / `--reference-audio-id` / `--first-frame-id` / `--last-frame-id` |

## 运行期问题

| 现象 | 排查 |
|---|---|
| 任务一直 `PENDING` / `RUNNING` | 图片任务在服务端异步执行；超过预期时间用 `task_detail.py` 继续查，必要时联系管理员 |
| 轮询超时（退出码 1） | 任务仍在执行，用同一 `taskNo` 继续查询，必要时加大 `--max-wait`；禁止重新提交 |
| `resultUrl` 打不开（403 / 过期） | 签名地址约 1 小时失效，重新调 `task_detail.py` |
| `CONCURRENCY_TIMEOUT` | 图片并发额度被占满，稍后重试；失败会自动退费 |
| `check.py` 报未配置环境变量 | 设置 `ADFLUX_API_KEY` 后重开终端 |
| `check.py` 网络失败 | 先确认网络 / 代理能访问 adflux.cn；私有化部署时再核对自定义地址（可只填域名） |
| 提示“请更新 adflux” | 执行 `npx skills update adflux-skills` |

## 安全约定

- 不要把 Key 写进仓库、脚本、日志或对话
- 日志与问题反馈只提供 `adfk_` 前缀（前 9 位）+ `****`
- Key 丢失只能停用后重建，平台不会再次展示明文
