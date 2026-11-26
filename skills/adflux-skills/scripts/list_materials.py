#!/usr/bin/env python3
"""分页查询当前员工素材；默认只返回开放任务产物（source=TASK_OUTPUT）。"""

import argparse
import urllib.parse

import _client as client

MEDIA_TYPES = ["IMAGE", "VIDEO", "AUDIO", "DOCUMENT"]


def normalize_time(value, end=False):
    """纯日期补齐时分秒，避免 --end 2026-11-25 漏掉当天数据。"""
    if not value:
        return None
    text = value.strip()
    if len(text) == 10:
        return text + (" 23:59:59" if end else " 00:00:00")
    return text


def main():
    parser = argparse.ArgumentParser(description="分页查询 adflux 素材")
    parser.add_argument("--page-no", type=int, default=1, help="页码，默认 1")
    parser.add_argument("--page-size", type=int, default=10, help="每页条数，默认 10，最大 200")
    parser.add_argument("--media-type", choices=MEDIA_TYPES, help="素材类型，不传返回全部")
    parser.add_argument("--source", choices=["TASK_OUTPUT", "UPLOAD"], default="TASK_OUTPUT",
                        help="来源，默认 TASK_OUTPUT（开放任务产物）")
    parser.add_argument("--task-no", help="来源任务编号，仅查该任务的产物")
    parser.add_argument("--start", help="创建时间开始：yyyy-MM-dd 或 yyyy-MM-dd HH:mm:ss")
    parser.add_argument("--end", help="创建时间结束：yyyy-MM-dd 或 yyyy-MM-dd HH:mm:ss")
    parser.add_argument("--dry-run", action="store_true", help="只打印请求，不发网络请求")
    args = parser.parse_args()

    query = {"pageNo": args.page_no, "pageSize": args.page_size, "source": args.source}
    if args.media_type:
        query["mediaType"] = args.media_type
    if args.task_no:
        query["taskNo"] = args.task_no
    start = normalize_time(args.start)
    end = normalize_time(args.end, end=True)
    if start:
        query["createTimeStart"] = start
    if end:
        query["createTimeEnd"] = end

    data = client.request("GET", "/material/page?" + urllib.parse.urlencode(query), dry_run=args.dry_run)
    if data is None:
        return
    client.emit(data)


if __name__ == "__main__":
    client.run(main)
