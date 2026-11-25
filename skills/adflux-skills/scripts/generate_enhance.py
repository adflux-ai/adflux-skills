#!/usr/bin/env python3
"""视频画质提升积分预估 / 提交任务。"""

import argparse

import _client as client


def build_payload(args):
    payload = {
        "videoMaterialId": args.video_material_id,
        "videoUrl": args.video_url,
        "resolution": args.resolution,
        "variant": args.variant,
        "bitrateLevel": args.bitrate_level,
    }
    return {key: value for key, value in payload.items() if value is not None}


def validate_args(parser, args):
    if args.video_material_id and args.video_url:
        parser.error("--video-material-id 与 --video-url 只能传一个（优先用素材 ID）")
    if not args.video_material_id and not args.video_url:
        parser.error("需要 --video-material-id 或 --video-url 指定输入视频（URL 必须是当前员工 upload.py 上传的素材）")


def main():
    parser = argparse.ArgumentParser(description="adflux 视频画质提升预估 / 生成")
    parser.add_argument("--video-material-id", type=int, metavar="ID",
                        help="输入视频素材 ID（upload.py 返回的 id，优先使用）")
    parser.add_argument("--video-url", help="输入视频 URL（必须是当前员工 upload.py 上传的素材）")
    parser.add_argument("--resolution", required=True,
                        help="输出分辨率：720p / 1080p / 2k / 4k")
    parser.add_argument("--variant", default="LITE", help="画质提升版本，默认 LITE")
    parser.add_argument("--bitrate-level", default="medium", choices=["low", "medium", "high"],
                        help="码率档，默认 medium")
    parser.add_argument("--estimate", action="store_true", help="只做积分预估，不提交任务")
    parser.add_argument("--dry-run", action="store_true", help="只打印请求，不发网络请求")
    args = parser.parse_args()

    validate_args(parser, args)

    path = "/video/enhance/estimate" if args.estimate else "/video/enhance/generate"
    data = client.request("POST", path, build_payload(args), dry_run=args.dry_run)
    if data is None:
        return
    client.emit(data)


if __name__ == "__main__":
    client.run(main)
