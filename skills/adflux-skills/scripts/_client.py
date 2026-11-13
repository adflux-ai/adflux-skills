#!/usr/bin/env python3
"""adflux skill 公共客户端：仅依赖 Python 标准库。"""

import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from urllib.parse import urlsplit

# 发布给终端用户的默认网关地址；dev / test 用 ADFLUX_BASE_URL 覆盖
DEFAULT_BASE_URL = "https://www.adflux.cn/open-api/ai"
DEFAULT_TIMEOUT = 120
MASKED_KEY = "adfk_****"


class ConfigError(Exception):
    """本地配置缺失或不合法。"""


class ApiError(Exception):
    """服务端返回 code != 0 或 HTTP 非 2xx。"""

    def __init__(self, message, code=None, http_status=None):
        super().__init__(message)
        self.code = code
        self.http_status = http_status


def base_url(dry_run=False):
    value = (os.environ.get("ADFLUX_BASE_URL") or DEFAULT_BASE_URL).strip().rstrip("/")
    if not value:
        if dry_run:
            return "<base-url>"
        raise ConfigError("未配置服务地址")
    if not urlsplit(value).path:
        value += "/open-api/ai"
    return value


def api_key():
    value = os.environ.get("ADFLUX_API_KEY", "").strip()
    if not value:
        raise ConfigError("未配置 ADFLUX_API_KEY")
    return value


def mask_key(value):
    if not value:
        return MASKED_KEY
    return value[:9] + "****" if len(value) > 12 else MASKED_KEY


def request(method, path, payload=None, file_field=None, dry_run=False, timeout=DEFAULT_TIMEOUT):
    """调用开放 API，返回 data 字段；失败抛 ConfigError / ApiError。"""
    url = base_url(dry_run=dry_run) + path
    headers = {}
    if file_field:
        body, content_type = _encode_multipart(payload or {}, file_field)
        headers["Content-Type"] = content_type
    elif payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    else:
        body = None

    if dry_run:
        headers["Authorization"] = "Bearer " + mask_key(os.environ.get("ADFLUX_API_KEY"))
        print(json.dumps({
            "dryRun": True,
            "method": method,
            "url": url,
            "headers": headers,
            "body": payload if payload is not None else ({"file": file_field.get("path")} if file_field else None),
        }, ensure_ascii=False, indent=2))
        return None

    headers["Authorization"] = "Bearer " + api_key()
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            status = resp.status
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        raise _to_api_error(raw, exc.code) from None
    except urllib.error.URLError as exc:
        raise ConfigError("请求失败：%s（检查 ADFLUX_BASE_URL 与网络）" % exc.reason) from None
    return _unwrap(raw, status)


def _to_api_error(raw, status):
    try:
        body = json.loads(raw)
    except ValueError:
        return ApiError("HTTP %s：%s" % (status, (raw or "无响应体")[:200]), http_status=status)
    return ApiError(body.get("msg") or ("HTTP %s" % status), code=body.get("code"), http_status=status)


def _unwrap(raw, status):
    try:
        body = json.loads(raw)
    except ValueError:
        raise ApiError("响应不是合法 JSON：%s" % (raw or "")[:200], http_status=status) from None
    code = body.get("code")
    if code != 0:
        raise ApiError(body.get("msg") or "接口返回失败", code=code, http_status=status)
    return body.get("data")


def _encode_multipart(fields, file_field):
    boundary = "----adflux" + uuid.uuid4().hex
    parts = []
    for name, value in (fields or {}).items():
        if value is None or value == "":
            continue
        parts.append((
            "--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n"
            % (boundary, name, value)
        ).encode("utf-8"))
    file_path = Path(file_field["path"])
    filename = file_field.get("filename") or file_path.name
    content_type = file_field.get("content_type") or mimetypes.guess_type(filename)[0] or "application/octet-stream"
    parts.append((
        "--%s\r\nContent-Disposition: form-data; name=\"%s\"; filename=\"%s\"\r\nContent-Type: %s\r\n\r\n"
        % (boundary, file_field.get("name", "file"), filename, content_type)
    ).encode("utf-8"))
    parts.append(file_path.read_bytes())
    parts.append(b"\r\n")
    parts.append(("--%s--\r\n" % boundary).encode("utf-8"))
    return b"".join(parts), "multipart/form-data; boundary=%s" % boundary


def emit(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


def run(main):
    """统一入口：异常转 stderr JSON 并返回非零退出码。"""
    try:
        main()
    except ApiError as exc:
        print(json.dumps({"error": str(exc), "code": exc.code}, ensure_ascii=False), file=sys.stderr)
        sys.exit(2)
    except ConfigError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as exc:  # noqa: BLE001 - 脚本层兜底，保证 stderr 是机器可读 JSON
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
