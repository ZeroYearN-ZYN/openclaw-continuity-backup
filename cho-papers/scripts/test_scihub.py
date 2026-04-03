#!/usr/bin/env python3
"""
测试SCI-hub访问
"""

import requests
import re

# 测试DOI
test_doi = "10.1038/s41587-020-00749-9"

scihub_urls = [
    "https://sci-hub.se",
    "https://sci-hub.sg",
    "https://sci-hub.st",
]

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

print("="*60)
print("测试SCI-hub访问")
print("="*60)

for base_url in scihub_urls:
    print(f"\n测试: {base_url}")
    try:
        # 测试连接
        url = f"{base_url}/{test_doi}"
        print(f"  URL: {url}")
        
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        print(f"  状态码: {response.status_code}")
        print(f"  内容长度: {len(response.text)} 字符")
        
        # 提取PDF链接
        html = response.text
        
        # 方法1: iframe
        iframe_match = re.search(r'<iframe[^>]+src=["\']([^"\']*\.pdf[^"\']*)["\']', html, re.IGNORECASE)
        if iframe_match:
            print(f"  ✅ 找到PDF (iframe): {iframe_match.group(1)[:80]}")
        
        # 方法2: embed
        embed_match = re.search(r'<embed[^>]+src=["\']([^"\']*\.pdf[^"\']*)["\']', html, re.IGNORECASE)
        if embed_match:
            print(f"  ✅ 找到PDF (embed): {embed_match.group(1)[:80]}")
        
        # 方法3: 查找所有PDF链接
        pdf_links = re.findall(r'https?://[^\s"\']+\.pdf[^\s"\']*', html, re.IGNORECASE)
        if pdf_links:
            print(f"  ✅ 找到 {len(pdf_links)} 个PDF链接")
            for link in pdf_links[:2]:
                print(f"     - {link[:80]}")
        
        # 显示HTML片段
        if not (iframe_match or embed_match or pdf_links):
            print("  ❌ 未找到PDF链接")
            print(f"  HTML片段: {html[:300]}...")
        
    except Exception as e:
        print(f"  ❌ 错误: {e}")

print("\n" + "="*60)
print("测试完成")
print("="*60)
