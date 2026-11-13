#!/usr/bin/env python3
"""视频积分预估 / 提交生成任务。"""

import argparse

import _client as client

GENERATE_TYPES = ["reference", "frame"]


def build_payload(args):
    payload = {
        "modelCode": args.model,
        "prompt": args.prompt,
        "resolution": args.resolution,
        "duration": args.duration,
        "aspectRatio": args.aspect_ratio,
        "generateType": args.generate_type,
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


def validate_args(parser, args):
    if not args.prompt.strip():
        parser.error("--prompt 不能为空")
    if args.generate_type == "reference" and not (
            args.reference or args.reference_video
            or args.reference_image_id or args.reference_video_id):
        parser.error("generateType=reference 时至少需要一个 --reference / --reference-video / "
                     "--reference-image-id / --reference-video-id")
    if args.generate_type == "frame":
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
    parser.add_argument("--resolution", required=True, help="分辨率，取值以 list_models.py 返回的 capabilities.resolution 为准（大小写敏感）")
    parser.add_argument("--duration", required=True, type=int, help="时长（秒），范围以 capabilities.minDurationSec / maxDurationSec 为准")
    parser.add_argument("--aspect-ratio", help="画面比例，默认 9:16，取值见 capabilities.ratio")
    parser.add_argument("--generate-type", required=True, choices=GENERATE_TYPES, help="生成方式")
    parser.add_argument("--reference", action="append", metavar="URL", help="参考图公网 URL，可重复")
    parser.add_argument("--reference-image-id", action="append", type=int, metavar="ID",
                        help="参考图素材 ID（upload.py 返回的 id），可重复")
    parser.add_argument("--reference-video", action="append", metavar="URL", help="参考视频 URL（需先 upload.py 上传），可重复")
    parser.add_argument("--reference-video-id", action="append", type=int, metavar="ID",
                        help="参考视频素材 ID（upload.py 返回的 id），可重复")
    parser.add_argument("--reference-audio", action="append", metavar="URL", help="参考音频 URL（需先 upload.py 上传），可重复")
    parser.add_argument("--reference-audio-id", action="append", type=int, metavar="ID",
                        help="参考音频素材 ID（upload.py 返回的 id），可重复")
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
