#!/usr/bin/env python3
"""上传本地素材（multipart）。"""

import argparse
from pathlib import Path

import _client as client


def main():
    parser = argparse.ArgumentParser(description="上传本地图片 / 视频 / 音频素材")
    parser.add_argument("--file", required=True, help="本地文件路径")
    parser.add_argument("--tags", help="标签，逗号分隔")
    parser.add_argument("--remark", help="备注")
    parser.add_argument("--dry-run", action="store_true", help="只打印请求，不发网络请求")
    args = parser.parse_args()

    file_path = Path(args.file).expanduser()
    if not args.dry_run and not file_path.is_file():
        parser.error("文件不存在：%s" % file_path)

    fields = {"tags": args.tags, "remark": args.remark}
    data = client.request(
        "POST",
        "/material/upload",
        payload=fields,
        file_field={"name": "file", "path": file_path},
        dry_run=args.dry_run,
    )
    if data is None:
        return
    client.emit(data)


if __name__ == "__main__":
    client.run(main)
