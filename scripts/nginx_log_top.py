#!/usr/bin/env python3
import re
import sys
from collections import Counter

def parse_log(filepath):
    ip_pattern = re.compile(r'^(\d+\.\d+\.\d+\.\d+)')
    url_pattern = re.compile(r'"(?:GET|POST|PUT|DELETE) (\S+)')
    status_pattern = re.compile(r'" (\d{3}) ')

    ips = Counter()
    urls = Counter()
    statuses = Counter()

    with open(filepath, 'r') as f:
        for line in f:
            ip = ip_pattern.search(line)
            url = url_pattern.search(line)
            status = status_pattern.search(line)
            if ip: ips[ip.group(1)] += 1
            if url: urls[url.group(1)] += 1
            if status: statuses[status.group(1)] += 1

    print("=== TOP 10 IP ===")
    for ip, count in ips.most_common(10):
        print(f"{ip:20s} {count}")

    print("\n=== TOP 10 URL ===")
    for url, count in urls.most_common(10):
        print(f"{url:40s} {count}")

    print("\n=== 状态码统计 ===")
    for status, count in statuses.most_common():
        print(f"{status}: {count}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 nginx_log_top.py <日志文件>")
        sys.exit(1)
    parse_log(sys.argv[1])
