#!/usr/bin/env python3
"""
CHO细胞文献分批下载器
每次只下载指定数量的文献，避免长时间运行被中断
"""

import os
import json
import requests
import time
from pathlib import Path
from datetime import datetime

# ========== 配置 ==========
BATCH_SIZE = 10  # 每次下载数量
OUTPUT_DIR = Path("/Users/mini4-2/Desktop/CHO-Literature-All")
DATA_DIR = Path("/Users/mini4-2/.openclaw/workspace/cho-papers/output")
PROGRESS_FILE = Path("/Users/mini4-2/.openclaw/workspace/cho-papers/data/download_progress.json")

# Unpaywall API
UNPAYWALL_EMAIL = "zhu199365@gmail.com"

# SCI-hub 镜像列表
SCIHUB_MIRRORS = [
    "https://sci-hub.se",
    "https://sci-hub.st",
    "https://sci-hub.ru",
]

def load_progress():
    """加载下载进度"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {"attempted": [], "downloaded": [], "failed": []}

def save_progress(progress):
    """保存下载进度"""
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def get_all_papers():
    """获取所有待下载的文献"""
    papers = []
    for json_file in DATA_DIR.glob("*.json"):
        with open(json_file, 'r') as f:
            data = json.load(f)
            for paper in data.get("papers", []):
                pmid = paper.get("pmid")
                if pmid and pmid not in [p["pmid"] for p in papers]:
                    # 清理 DOI 格式
                    doi = paper.get("doi", "")
                    if doi.startswith("doi: "):
                        doi = doi[5:]
                    papers.append({
                        "pmid": pmid,
                        "title": paper.get("title", ""),
                        "doi": doi,
                        "url": paper.get("url", ""),
                    })
    return papers

def try_unpaywall(doi, output_path):
    """尝试通过 Unpaywall 下载"""
    if not doi:
        return False
    try:
        url = f"https://api.unpaywall.org/v2/{doi}?email={UNPAYWALL_EMAIL}"
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            pdf_url = data.get("best_oa_location", {}).get("url_for_pdf")
            if pdf_url:
                pdf_resp = requests.get(pdf_url, timeout=60)
                if pdf_resp.status_code == 200 and pdf_resp.headers.get("content-type", "").startswith("application/pdf"):
                    with open(output_path, 'wb') as f:
                        f.write(pdf_resp.content)
                    return True
    except Exception:
        pass
    return False

def try_pmc(pmid, output_path):
    """尝试通过 PMC 下载"""
    try:
        # 查找 PMC ID
        search_url = f"https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?ids={pmid}&format=json"
        resp = requests.get(search_url, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            pmcid = data.get("records", [{}])[0].get("pmcid", "")
            if pmcid:
                pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/"
                pdf_resp = requests.get(pdf_url, timeout=60)
                if pdf_resp.status_code == 200:
                    with open(output_path, 'wb') as f:
                        f.write(pdf_resp.content)
                    return True
    except Exception:
        pass
    return False

def try_scihub(doi, output_path):
    """尝试通过 SCI-hub 下载"""
    if not doi:
        return False
    for mirror in SCIHUB_MIRRORS:
        try:
            url = f"{mirror}/{doi}"
            resp = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                # 查找 PDF 链接
                import re
                pdf_match = re.search(r'(https?://[^"\'>]+\.pdf)', resp.text)
                if pdf_match:
                    pdf_url = pdf_match.group(1)
                    pdf_resp = requests.get(pdf_url, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
                    if pdf_resp.status_code == 200 and b"%PDF" in pdf_resp.content[:100]:
                        with open(output_path, 'wb') as f:
                            f.write(pdf_resp.content)
                        return True
        except Exception:
            continue
    return False

def download_paper(paper, progress):
    """下载单篇文献"""
    pmid = paper["pmid"]
    doi = paper["doi"]
    title = paper["title"][:50] + "..." if len(paper["title"]) > 50 else paper["title"]
    
    # 检查是否已下载
    existing = list(OUTPUT_DIR.glob(f"*{pmid}*.pdf"))
    if existing:
        return "already_exists"
    
    # 检查是否已尝试失败
    if pmid in progress["failed"]:
        return "previously_failed"
    
    output_path = OUTPUT_DIR / f"{pmid}_{title.replace('/', '_')[:80]}.pdf"
    
    print(f"  📄 [{pmid}] {title}")
    
    # 尝试 Unpaywall
    if try_unpaywall(doi, output_path):
        print(f"     ✅ Unpaywall 成功")
        return "success"
    
    # 尝试 PMC
    if try_pmc(pmid, output_path):
        print(f"     ✅ PMC 成功")
        return "success"
    
    # 尝试 SCI-hub
    if try_scihub(doi, output_path):
        print(f"     ✅ SCI-hub 成功")
        return "success"
    
    print(f"     ❌ 下载失败")
    return "failed"

def download_batch(progress, all_papers, batch_num):
    """下载一批文献"""
    pending = [p for p in all_papers if p["pmid"] not in progress["attempted"]]
    
    if not pending:
        return False  # 没有待下载的了
    
    batch = pending[:BATCH_SIZE]
    print(f"🚀 批次 {batch_num}: 下载 {len(batch)} 篇...\n")
    
    stats = {"success": 0, "failed": 0, "skipped": 0}
    
    for paper in batch:
        result = download_paper(paper, progress)
        progress["attempted"].append(paper["pmid"])
        
        if result == "success":
            progress["downloaded"].append(paper["pmid"])
            stats["success"] += 1
        elif result in ["already_exists", "previously_failed"]:
            stats["skipped"] += 1
        else:
            progress["failed"].append(paper["pmid"])
            stats["failed"] += 1
        
        time.sleep(2)  # 避免请求过快
    
    # 保存进度
    save_progress(progress)
    
    # 汇总
    print(f"\n{'─'*60}")
    print(f"📊 批次 {batch_num} 统计:")
    print(f"  ✅ 成功: {stats['success']} | ❌ 失败: {stats['failed']} | ⏭️ 跳过: {stats['skipped']}")
    print(f"📈 总进度: 已下载 {len(progress['downloaded'])} / {len(all_papers)}")
    remaining = len([p for p in all_papers if p["pmid"] not in progress["attempted"]])
    print(f"⏳ 剩余: {remaining} 篇")
    
    return remaining > 0

def main():
    import sys
    continuous = "--continuous" in sys.argv or "-c" in sys.argv
    wait_seconds = 60  # 批次间等待时间
    
    print(f"\n{'='*60}")
    print(f"📥 CHO文献分批下载 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"📦 每批次: {BATCH_SIZE} 篇")
    print(f"🔄 模式: {'连续下载' if continuous else '单批次'}")
    if continuous:
        print(f"⏱️  批次间隔: {wait_seconds} 秒")
    print(f"{'='*60}\n")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 加载进度
    progress = load_progress()
    print(f"📊 已尝试: {len(progress['attempted'])} | 已下载: {len(progress['downloaded'])} | 失败: {len(progress['failed'])}")
    
    # 获取所有文献
    all_papers = get_all_papers()
    print(f"📚 总文献: {len(all_papers)} 篇")
    
    pending = [p for p in all_papers if p["pmid"] not in progress["attempted"]]
    print(f"⏳ 待下载: {len(pending)} 篇\n")
    
    if not pending:
        print("✅ 所有文献已处理完成！")
        return
    
    if continuous:
        # 连续模式：完成一批后等待1分钟继续
        batch_num = 1
        while download_batch(progress, all_papers, batch_num):
            batch_num += 1
            print(f"\n⏳ 等待 {wait_seconds} 秒后继续下一批...")
            print(f"{'='*60}\n")
            time.sleep(wait_seconds)
        
        print(f"\n{'='*60}")
        print(f"✅ 全部完成！")
        print(f"📊 最终统计: 已下载 {len(progress['downloaded'])} / {len(all_papers)} 篇")
        print(f"{'='*60}\n")
    else:
        # 单批次模式
        download_batch(progress, all_papers, 1)
        print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
