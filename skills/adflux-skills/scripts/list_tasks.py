#!/usr/bin/env python3
"""分页查询开放 API 生成记录（仅本 Key 绑定员工、source=open-api）。"""

import argparse
import urllib.parse

import _client as client

STATUSES = ["PENDING", "QUEUED", "RUNNING", "SUCCESS", "FAILED", "CANCELLED"]
BUSINESS_TYPES = ["image", "video", "video_enhance"]


def normalize_time(value, end=False):
    """纯日期补齐时分秒，避免 --end 2026-11-25 漏掉当天数据。"""
    if not value:
        return None
    text = value.strip()
    if len(text) == 10:
        return text + (" 23:59:59" if end else " 00:00:00")
    return text


def main():
    parser = argparse.ArgumentParser(description="分页查询 adflux 生成记录")
    parser.add_argument("--page-no", type=int, default=1, help="页码，默认 1")
    parser.add_argument("--page-size", type=int, default=10, help="每页条数，默认 10，最大 200")
    parser.add_argument("--status", choices=STATUSES, help="任务状态")
    parser.add_argument("--business-type", choices=BUSINESS_TYPES, help="业务类型")
    parser.add_argument("--task-no", help="按任务编号精确查询")
    parser.add_argument("--start", help="创建时间开始：yyyy-MM-dd 或 yyyy-MM-dd HH:mm:ss")
    parser.add_argument("--end", help="创建时间结束：yyyy-MM-dd 或 yyyy-MM-dd HH:mm:ss")
    parser.add_argument("--dry-run", action="store_true", help="只打印请求，不发网络请求")
    args = parser.parse_args()

    query = {"pageNo": args.page_no, "pageSize": args.page_size}
    if args.status:
        query["status"] = args.status
    if args.business_type:
        query["businessType"] = args.business_type
    if args.task_no:
        query["taskNo"] = args.task_no
    start = normalize_time(args.start)
    end = normalize_time(args.end, end=True)
    if start:
        query["createTimeStart"] = start
    if end:
        query["createTimeEnd"] = end

    data = client.request("GET", "/task/page?" + urllib.parse.urlencode(query), dry_run=args.dry_run)
    if data is None:
        return
    client.emit(data)


if __name__ == "__main__":
    client.run(main)
