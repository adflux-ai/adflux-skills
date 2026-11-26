#!/usr/bin/env python3
"""视频积分预估 / 提交生成任务。"""

import argparse

import _client as client

GENERATE_TYPES = ["text", "reference", "frame"]
VIDEO_TASK_TYPES = ["reference", "edit", "extend"]
EDIT_EXTEND_TYPES = ("edit", "extend")


def resolve_video_task_type(args):
    return args.video_task_type or "reference"


def resolve_generate_type(args):
    """编辑 / 延长固定 reference；其余沿用入参（省略时交给服务端按 text 处理）。"""
    if resolve_video_task_type(args) in EDIT_EXTEND_TYPES:
        return "reference"
    return args.generate_type


def build_payload(args):
    payload = {
        "modelCode": args.model,
        "prompt": args.prompt,
        "resolution": args.resolution,
        "duration": args.duration,
        "aspectRatio": args.aspect_ratio,
        "generateType": resolve_generate_type(args),
        "videoTaskType": args.video_task_type or None,
        "referenceImageUrls": args.reference or None,
        "referenceImageMaterialIds": args.reference_image_id or None,
        "referenceVideoUrls": args.reference_video or None,
        "referenceVideoMaterialIds": args.reference_video_id or None,
        "referenceAudioUrls": args.reference_audio or None,
        "referenceAudioMaterialIds": args.reference_audio_id or None,
        "firstFrameImageUrl": args.first_frame_url,
        "firstFrameMaterialId": args.first_frame_id,
        "lastFrameImageUrl": args.last_frame_url,
        "lastFrameMaterialId": args.last_frame_id,
        "generateAudio": False if args.no_audio else None,
    }
    return {key: value for key, value in payload.items() if value is not None}


def validate_edit_extend_args(parser, args, task_type):
    label = "视频编辑" if task_type == "edit" else "视频延长"
    if args.generate_type not in (None, "reference"):
        parser.error(f"{label}固定使用 --generate-type reference，不能传 {args.generate_type}")
    if (args.first_frame_url or args.first_frame_id
            or args.last_frame_url or args.last_frame_id):
        parser.error(f"{label}不支持首帧 / 尾帧素材")
    if args.reference_video and args.reference_video_id:
        # 服务端合并时 URL 列表排在素材 ID 之前，混用会让「第一个是原片」失效
        parser.error(f"{label}的参考视频请只用一种来源：全部 --reference-video 或全部 --reference-video-id"
                     "（服务端按 URL 在前合并，混用会导致原片顺序不符合预期）")
    videos = (args.reference_video or []) + (args.reference_video_id or [])
    if not videos:
        parser.error(f"{label}需要 --reference-video 或 --reference-video-id 指定原片（本地先 upload.py，站内已有素材先 list_materials.py）")
    if task_type == "edit" and len(videos) != 1:
        parser.error(f"视频编辑只能指定 1 个原片，当前 {len(videos)} 个")


def validate_args(parser, args):
    if not args.prompt.strip():
        parser.error("--prompt 不能为空")
    task_type = resolve_video_task_type(args)
    if task_type in EDIT_EXTEND_TYPES:
        validate_edit_extend_args(parser, args, task_type)
        return
    generate_type = args.generate_type or "text"
    if generate_type == "text":
        if (args.reference or args.reference_image_id or args.reference_video
                or args.reference_video_id or args.reference_audio or args.reference_audio_id
                or args.first_frame_url or args.first_frame_id
                or args.last_frame_url or args.last_frame_id):
            parser.error("generateType=text 为纯文生视频，不能同时传参考素材或首尾帧；"
                         "需要素材时请用 --generate-type reference / frame")
    if generate_type == "reference" and not (
            args.reference or args.reference_video
            or args.reference_image_id or args.reference_video_id
            or args.reference_audio or args.reference_audio_id):
        parser.error("generateType=reference 时至少需要一个 --reference / --reference-video / "
                     "--reference-audio（或对应素材 ID）")
    if generate_type == "frame":
        if args.first_frame_url and args.first_frame_id:
            parser.error("首帧只能传 --first-frame-url 或 --first-frame-id 之一")
        if args.last_frame_url and args.last_frame_id:
            parser.error("尾帧只能传 --last-frame-url 或 --last-frame-id 之一")
        if not (
                (args.first_frame_url or args.first_frame_id)
                and (args.last_frame_url or args.last_frame_id)):
            parser.error("generateType=frame 时需要同时提供首帧与尾帧（URL 或素材 ID）")


def main():
    parser = argparse.ArgumentParser(description="adflux 视频预估 / 生成")
    parser.add_argument("--model", required=True, help="模型编码，先用 list_models.py --type video 获取")
    parser.add_argument("--prompt", required=True, help="提示词，不能为空")
    parser.add_argument("--resolution", required=True,
                        help="分辨率：取值以 capabilities.resolution 为准（大小写敏感）；编辑 / 延长同样按该档位传入，输出比例由服务端按原片覆盖")
    parser.add_argument("--duration", required=True, type=int,
                        help="时长（秒）：普通生成 / 编辑传原片时长，延长传本次新增片段秒数")
    parser.add_argument("--aspect-ratio", help="画面比例，默认 9:16，取值见 capabilities.ratio；编辑 / 延长由服务端覆盖")
    parser.add_argument("--generate-type", choices=GENERATE_TYPES, default=None,
                        help="生成方式：text（纯文生视频）/ reference / frame；省略时普通生成按 text，编辑 / 延长按 reference")
    parser.add_argument("--video-task-type", choices=VIDEO_TASK_TYPES, default=None,
                        help="视频任务类型：reference（默认）/ edit（视频编辑）/ extend（视频延长）")
    parser.add_argument("--reference", action="append", metavar="URL", help="参考图公网 URL（外部临时图片），可重复；站内或本地素材请用 --reference-image-id")
    parser.add_argument("--reference-image-id", action="append", type=int, metavar="ID",
                        help="参考图素材 ID（upload.py 或 list_materials.py 返回的 id），可重复")
    parser.add_argument("--reference-video", action="append", metavar="URL",
                        help="参考视频 URL（必须是当前员工名下素材地址，可先 upload.py 上传），可重复")
    parser.add_argument("--reference-video-id", action="append", type=int, metavar="ID",
                        help="参考视频素材 ID（upload.py 或 list_materials.py 返回的 id），可重复；编辑 / 延长时第一个为原片")
    parser.add_argument("--reference-audio", action="append", metavar="URL",
                        help="参考音频 URL（必须是当前员工名下素材地址，可先 upload.py 上传），可重复")
    parser.add_argument("--reference-audio-id", action="append", type=int, metavar="ID",
                        help="参考音频素材 ID（upload.py 或 list_materials.py 返回的 id），可重复")
    parser.add_argument("--first-frame-url", help="首帧图片 URL")
    parser.add_argument("--first-frame-id", type=int, metavar="ID", help="首帧图片素材 ID（与 --first-frame-url 二选一）")
    parser.add_argument("--last-frame-url", help="尾帧图片 URL（generateType=frame 必填）")
    parser.add_argument("--last-frame-id", type=int, metavar="ID", help="尾帧图片素材 ID（与 --last-frame-url 二选一）")
    parser.add_argument("--no-audio", action="store_true", help="不生成音频（默认生成）")
    parser.add_argument("--estimate", action="store_true", help="只做积分预估，不提交任务")
    parser.add_argument("--dry-run", action="store_true", help="只打印请求，不发网络请求")
    args = parser.parse_args()

    validate_args(parser, args)

    path = "/video/estimate" if args.estimate else "/video/generate"
    data = client.request("POST", path, build_payload(args), dry_run=args.dry_run)
    if data is None:
        return
    client.emit(data)


if __name__ == "__main__":
    client.run(main)
