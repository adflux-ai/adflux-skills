#!/usr/bin/env python3
"""列出可用模型。"""

import argparse
import urllib.parse

import _client as client


def main():
    parser = argparse.ArgumentParser(description="列出 adflux 可用模型")
    parser.add_argument("--type", choices=["image", "video"], help="只列出指定类型，默认返回图片与视频")
    parser.add_argument("--dry-run", action="store_true", help="只打印请求，不发网络请求")
    args = parser.parse_args()

    path = "/model/simple-list"
    if args.type:
        path += "?" + urllib.parse.urlencode({"type": args.type})

    models = client.request("GET", path, dry_run=args.dry_run)
    if models is None:
        return
    client.emit(models)


if __name__ == "__main__":
    client.run(main)
