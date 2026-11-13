#!/usr/bin/env python3
"""图片积分预估 / 提交生成任务。"""

import argparse

import _client as client


def build_payload(args):
    payload = {
        "modelCode": args.model,
        "prompt": args.prompt,
        "quality": args.quality,
        "width": args.width,
        "height": args.height,
        "imageCount": args.count,
        "referenceImageUrls": args.reference or None,
        "referenceImageMaterialIds": args.reference_image_id or None,
        "outputFormat": args.output_format,
        "watermark": True if args.watermark else None,
    }
    return {key: value for key, value in payload.items() if value is not None}


def main():
    parser = argparse.ArgumentParser(description="adflux 图片预估 / 生成")
    parser.add_argument("--model", required=True, help="模型编码，先用 list_models.py --type image 获取")
    parser.add_argument("--prompt", required=True, help="提示词，不能为空")
    parser.add_argument("--quality", choices=["1k", "1.5k", "2k", "3k", "4k"], help="画质档位")
    parser.add_argument("--width", type=int, help="自定义宽度")
    parser.add_argument("--height", type=int, help="自定义高度")
    parser.add_argument("--count", type=int, default=1, help="生成数量 1~15，默认 1")
    parser.add_argument("--reference", action="append", metavar="URL", help="参考图公网 URL，可重复")
    parser.add_argument("--reference-image-id", action="append", type=int, metavar="ID",
                        help="参考图素材 ID（upload.py 返回的 id），可重复")
    parser.add_argument("--output-format", help="输出格式，默认由服务端决定（jpeg）")
    parser.add_argument("--watermark", action="store_true", help="添加水印")
    parser.add_argument("--estimate", action="store_true", help="只做积分预估，不提交任务")
    parser.add_argument("--dry-run", action="store_true", help="只打印请求，不发网络请求")
    args = parser.parse_args()

    if not args.prompt.strip():
        parser.error("--prompt 不能为空")
    if not 1 <= args.count <= 15:
        parser.error("--count 必须在 1~15 之间")

    path = "/image/estimate" if args.estimate else "/image/generate"
    data = client.request("POST", path, build_payload(args), dry_run=args.dry_run)
    if data is None:
        return
    client.emit(data)


if __name__ == "__main__":
    client.run(main)
