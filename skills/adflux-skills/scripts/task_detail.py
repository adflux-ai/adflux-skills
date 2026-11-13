#!/usr/bin/env python3
"""查询任务详情，可选自动轮询与结果下载。"""

import argparse
import mimetypes
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import _client as client

TERMINAL_STATUSES = {"SUCCESS", "FAILED", "CANCELLED"}
DOWNLOAD_TIMEOUT = 300


def fetch(task_no, dry_run=False):
    query = urllib.parse.urlencode({"taskNo": task_no})
    return client.request("GET", "/task/detail?" + query, dry_run=dry_run)


def download_results(data, output_dir, dry_run=False):
    """把 SUCCESS 任务的结果下载到本地，并在每条结果上写入 localPath。"""
    if dry_run or data.get("status") != "SUCCESS":
        return
    directory = Path(output_dir).expanduser().resolve()
    directory.mkdir(parents=True, exist_ok=True)
    for index, item in enumerate(data.get("results") or [], 1):
        url = item.get("resultUrl")
        if not url:
            continue
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "adflux-skill/1"})
            with urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT) as response:
                content = response.read()
                content_type = response.headers.get_content_type()
            suffix = Path(urllib.parse.urlparse(url).path).suffix
            if not suffix and item.get("format"):
                suffix = "." + str(item["format"]).strip(".")
            if not suffix:
                suffix = mimetypes.guess_extension(content_type) or ".bin"
            destination = directory / ("%02d%s" % (index, suffix))
            destination.write_bytes(content)
            item["localPath"] = str(destination)
        except (urllib.error.URLError, OSError) as exc:
            item["downloadError"] = str(exc)


def main():
    parser = argparse.ArgumentParser(description="查询 adflux 任务详情")
    parser.add_argument("--task-no", required=True, help="提交生成后返回的 taskNo")
    parser.add_argument("--watch", action="store_true", help="轮询直到终态或超时")
    parser.add_argument("--max-wait", type=int, default=600, help="--watch 的最长等待秒数，默认 600")
    parser.add_argument("--download", metavar="DIR", help="任务成功后把结果下载到该目录，并在结果中返回 localPath")
    parser.add_argument("--dry-run", action="store_true", help="只打印请求，不发网络请求")
    args = parser.parse_args()

    if not args.watch:
        data = fetch(args.task_no, dry_run=args.dry_run)
        if data is None:
            return
        if args.download:
            download_results(data, args.download, dry_run=args.dry_run)
        client.emit(data)
        return

    started = time.time()
    while True:
        data = fetch(args.task_no, dry_run=args.dry_run)
        if data is None:
            return
        elapsed = time.time() - started
        if data.get("status") in TERMINAL_STATUSES:
            if args.download:
                download_results(data, args.download, dry_run=args.dry_run)
            client.emit(data)
            return
        if elapsed >= args.max_wait:
            client.emit(data)
            print('{"error": "等待超时，任务仍在执行，可稍后重新查询"}', file=sys.stderr)
            sys.exit(1)
        # 前 30 秒每 3 秒一次，之后每 10 秒一次
        time.sleep(3 if elapsed < 30 else 10)


if __name__ == "__main__":
    client.run(main)
