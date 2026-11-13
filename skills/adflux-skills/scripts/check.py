#!/usr/bin/env python3
"""连通性自检：环境变量 + 模型列表。"""

import argparse
import os

import _client as client


def main():
    parser = argparse.ArgumentParser(description="adflux skill 自检")
    parser.add_argument("--dry-run", action="store_true", help="只打印请求，不发网络请求")
    args = parser.parse_args()

    models = client.request("GET", "/model/simple-list", dry_run=args.dry_run)
    if models is None:
        return

    image_count = sum(1 for model in models if model.get("type") == "image")
    video_count = sum(1 for model in models if model.get("type") == "video")

    client.emit({
        "ok": True,
        "baseUrl": client.base_url(dry_run=args.dry_run),
        "apiKey": client.mask_key(os.environ.get("ADFLUX_API_KEY", "")),
        "modelCount": {"image": image_count, "video": video_count},
    })


if __name__ == "__main__":
    client.run(main)
