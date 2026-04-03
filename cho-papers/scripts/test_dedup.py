#!/usr/bin/env python3
"""
测试去重功能
运行两次pubmed_fetch.py，验证不会重复抓取
"""

import sys
sys.path.insert(0, '/Users/mini4-2/.openclaw/workspace/cho-papers/scripts')

from pubmed_fetch import load_history, main
import json
from pathlib import Path

print("="*60)
print("测试1: 查看当前历史记录")
print("="*60)
history = load_history()
print(f"已处理PMID数量: {len(history)}")
print(f"前10个PMID: {list(history)[:10]}")

print("\n" + "="*60)
print("测试2: 再次运行抓取（应该无新文献）")
print("="*60)
new_count = main()

print("\n" + "="*60)
print("测试3: 验证结果")
print("="*60)
if new_count == 0:
    print("✅ 去重功能正常！没有重复抓取")
else:
    print(f"⚠️  发现 {new_count} 篇新文献（可能正常）")

print("\n" + "="*60)
print("测试4: 查看累积数据")
print("="*60)
workspace = Path("/Users/mini4-2/.openclaw/workspace/cho-papers")
output_dir = workspace / "output"

for json_file in output_dir.glob("pubmed_*_latest.json"):
    with open(json_file, 'r') as f:
        data = json.load(f)
    print(f"{json_file.name}:")
    print(f"  总计: {data.get('total_count', 0)} 篇")
    print(f"  新增: {data.get('new_count', 0)} 篇")
    print()

print("="*60)
print("✅ 测试完成")
print("="*60)
