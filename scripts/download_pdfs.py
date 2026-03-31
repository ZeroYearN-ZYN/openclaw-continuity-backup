#!/usr/bin/env python3
"""
尝试下载开放获取的PDF全文
需要先运行 pubmed_fetch.py 或 semantic_scholar_fetch.py 生成JSON
"""

import json
import requests
from pathlib import Path
from datetime import datetime
import time

OUTPUT_DIR = Path(__file__).parent.parent / "output"
PDF_DIR = OUTPUT_DIR / "pdfs"


def download_from_unpaywall(doi, title):
    """通过Unpaywall API获取开放获取PDF"""
    if not doi:
        return None
    
    email = "your_email@example.com"  # 替换你的邮箱
    url = f"https://api.unpaywall.org/v2/{doi}?email={email}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("is_oa"):
                oa_location = data.get("best_oa_location", {})
                pdf_url = oa_location.get("url_for_pdf") or oa_location.get("url")
                
                if pdf_url:
                    print(f"  📥 下载: {title[:50]}...")
                    pdf_response = requests.get(pdf_url, timeout=30)
                    
                    if pdf_response.status_code == 200:
                        safe_title = "".join(c for c in title[:80] if c.isalnum() or c in " -_")
                        pdf_file = PDF_DIR / f"{safe_title}.pdf"
                        
                        with open(pdf_file, "wb") as f:
                            f.write(pdf_response.content)
                        
                        print(f"  ✅ 成功: {pdf_file.name}")
                        return pdf_file
    except Exception as e:
        print(f"  ❌ 失败: {e}")
    
    return None


def process_json_file(json_file):
    """处理JSON文件，尝试下载PDF"""
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    papers = data.get("papers", [])
    print(f"\n📄 处理 {json_file.name}: {len(papers)} 篇文献\n")
    
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    
    downloaded = 0
    for i, paper in enumerate(papers, 1):
        print(f"[{i}/{len(papers)}] {paper.get('title', 'N/A')[:60]}")
        
        doi = paper.get("doi", "")
        if doi:
            result = download_from_unpaywall(doi, paper.get("title", ""))
            if result:
                downloaded += 1
            time.sleep(1)  # 避免API限制
    
    return downloaded


def main():
    print(f"📥 PDF下载器 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    json_files = list(OUTPUT_DIR.glob("*.json"))
    
    if not json_files:
        print("❌ 未找到JSON文件，请先运行文献抓取脚本")
        return
    
    total_downloaded = 0
    for json_file in json_files:
        downloaded = process_json_file(json_file)
        total_downloaded += downloaded
    
    print(f"\n✅ 总计下载 {total_downloaded} 个PDF")


if __name__ == "__main__":
    main()
