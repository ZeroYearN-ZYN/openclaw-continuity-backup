#!/usr/bin/env python3
"""
CHO细胞文献PDF下载器 - 包含SCI-hub备选方案
自动尝试：Unpaywall → PMC → SCI-hub
"""

import json
import requests
import time
import re
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.parse

# ========== 配置 ==========
WORKSPACE = Path("/Users/mini4-2/.openclaw/workspace/cho-papers")
OUTPUT_DIR = WORKSPACE / "output"
PDF_DIR = Path.home() / "Desktop" / "CHO-Literature-All"
DOWNLOAD_HISTORY = WORKSPACE / "data" / "download_history.json"

# API配置
UNPAYWALL_EMAIL = "zhu199365@gmail.com"
SCI_HUB_BASE = "https://sci-hub.sg"

# 下载配置
MAX_WORKERS = 2  # 降低并发，避免触发限制
TIMEOUT = 30
MAX_RETRIES = 2

# 使用SCI-hub的开关（默认开启）
USE_SCIHUB = True


def clean_filename(title):
    """清理文件名"""
    cleaned = re.sub(r'[<>:"/\\|?*]', '', title)
    return cleaned[:100].strip()


def load_download_history():
    """加载下载历史"""
    if DOWNLOAD_HISTORY.exists():
        with open(DOWNLOAD_HISTORY, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    return set()


def save_download_history(history):
    """保存下载历史"""
    DOWNLOAD_HISTORY.parent.mkdir(parents=True, exist_ok=True)
    with open(DOWNLOAD_HISTORY, 'w', encoding='utf-8') as f:
        json.dump(list(history), f, indent=2)


def get_pdf_from_unpaywall(doi, title):
    """通过Unpaywall获取PDF（方法1）"""
    if not doi:
        return None, "无DOI"
    
    doi = doi.replace("doi: ", "").strip()
    url = f"https://api.unpaywall.org/v2/{doi}?email={UNPAYWALL_EMAIL}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("is_oa"):
                oa_location = data.get("best_oa_location") or {}
                pdf_url = (
                    oa_location.get("url_for_pdf") or 
                    oa_location.get("url") or
                    None
                )
                if pdf_url:
                    return pdf_url, "Unpaywall"
            return None, "非开放获取"
    except Exception as e:
        return None, f"Unpaywall错误"
    
    return None, "Unpaywall未找到"


def get_pdf_from_pmc(pmid):
    """从PMC获取PDF（方法2）"""
    base_url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    
    try:
        params = {
            "query": f"PMID:{pmid}",
            "format": "json",
            "pageSize": 1
        }
        response = requests.get(base_url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("resultList", {}).get("result", [])
            
            if results:
                pmcid = results[0].get("pmcid")
                if pmcid:
                    pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/"
                    return pdf_url, "PMC"
    except:
        pass
    
    return None, "PMC未找到"


def get_pdf_from_scihub(doi):
    """通过SCI-hub获取PDF（方法3 - 备选）"""
    if not USE_SCIHUB or not doi:
        return None, "SCI-hub未启用"
    
    doi = doi.replace("doi: ", "").strip()
    
    # SCI-hub备用域名列表
    scihub_urls = [
        "https://sci-hub.sg",
        "https://sci-hub.se",
        "https://sci-hub.st",
        "https://sci-hub.ru",
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://google.com",
    }
    
    for base_url in scihub_urls:
        try:
            # 访问SCI-hub页面
            url = f"{base_url}/{doi}"
            response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            
            if response.status_code == 200:
                # 从HTML中提取PDF链接
                html = response.text
                
                # 查找PDF URL（常见的模式）
                pdf_patterns = [
                    r'<iframe[^>]+src=["\']([^"\']*\.pdf[^"\']*)["\']',
                    r'<embed[^>]+src=["\']([^"\']*\.pdf[^"\']*)["\']',
                    r'location\.href=["\']([^"\']*\.pdf[^"\']*)["\']',
                    r'<a[^>]+href=["\']([^"\']*\.pdf[^"\']*)["\']',
                ]
                
                for pattern in pdf_patterns:
                    matches = re.findall(pattern, html, re.IGNORECASE)
                    if matches:
                        pdf_url = matches[0]
                        
                        # 处理相对URL
                        if pdf_url.startswith('//'):
                            pdf_url = 'https:' + pdf_url
                        elif pdf_url.startswith('/'):
                            pdf_url = base_url + pdf_url
                        elif not pdf_url.startswith('http'):
                            pdf_url = base_url + '/' + pdf_url
                        
                        # URL解码
                        pdf_url = urllib.parse.unquote(pdf_url)
                        
                        return pdf_url, "SCI-hub"
            
        except Exception as e:
            continue
    
    return None, "SCI-hub未找到"


def download_pdf(url, output_path, source_name):
    """下载PDF文件"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=headers, timeout=TIMEOUT, stream=True)
            
            # 检查是否是PDF
            content_type = response.headers.get('content-type', '')
            if 'pdf' not in content_type.lower() and not url.endswith('.pdf'):
                # 可能是HTML页面，检查内容
                if 'text/html' in content_type.lower():
                    return False, "非PDF链接"
            
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # 验证文件大小
                if output_path.stat().st_size < 1000:
                    output_path.unlink()
                    return False, "文件过小"
                
                return True, f"✅ {source_name}"
            
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(2)
                continue
            return False, f"下载失败"
    
    return False, "下载失败"


def process_paper(paper, pdf_dir, download_history):
    """处理单篇文献 - 依次尝试3种方法"""
    pmid = paper.get("pmid", "")
    title = paper.get("title", "Unknown")
    doi = paper.get("doi", "")
    
    # 检查是否已下载
    if pmid in download_history:
        return "已下载", title, pmid
    
    print(f"  📄 [{pmid}] {title[:50]}...", flush=True)
    
    # 清理文件名
    safe_title = clean_filename(title)
    pdf_path = pdf_dir / f"{safe_title}.pdf"
    
    # 如果文件已存在
    if pdf_path.exists():
        return "已存在", title, pmid
    
    # 方法1: Unpaywall（开放获取）
    pdf_url, source = get_pdf_from_unpaywall(doi, title)
    
    # 方法2: PMC
    if not pdf_url:
        pdf_url, source = get_pdf_from_pmc(pmid)
    
    # 方法3: SCI-hub（备选）
    if not pdf_url and USE_SCIHUB:
        print(f"     ⏳ 尝试SCI-hub...", flush=True)
        pdf_url, source = get_pdf_from_scihub(doi)
        time.sleep(2)  # SCI-hub需要延迟
    
    # 下载PDF
    if pdf_url:
        success, message = download_pdf(pdf_url, pdf_path, source)
        if success:
            return f"新下载({source})", title, pmid
        return message, title, pmid
    
    return source, title, pmid


def process_json_file(json_file, pdf_dir, download_history):
    """处理JSON文件"""
    print(f"\n{'='*60}", flush=True)
    print(f"📚 处理: {json_file.name}", flush=True)
    print(f"{'='*60}", flush=True)
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    papers = data.get("papers", [])
    search_term = data.get("search_term", "unknown")
    new_count = data.get("new_count", len(papers))
    
    print(f"🔍 搜索词: {search_term}", flush=True)
    print(f"📊 总文献: {len(papers)} | 本次新增: {new_count}", flush=True)
    print(f"📁 保存到: {pdf_dir}\n", flush=True)
    
    # 统计
    stats = {
        "downloaded": 0,
        "unpaywall": 0,
        "pmc": 0,
        "scihub": 0,
        "existing": 0,
        "no_access": 0,
        "failed": 0
    }
    
    failed_papers = []
    new_downloads = []
    
    # 并发下载（降低并发数）
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(process_paper, paper, pdf_dir, download_history): paper 
            for paper in papers
        }
        
        for future in as_completed(futures):
            status, title, pmid = future.result()
            
            if "新下载" in status:
                stats["downloaded"] += 1
                new_downloads.append(pmid)
                
                # 统计来源
                if "Unpaywall" in status:
                    stats["unpaywall"] += 1
                elif "PMC" in status:
                    stats["pmc"] += 1
                elif "SCI-hub" in status:
                    stats["scihub"] += 1
                    
            elif "已下载" in status or "已存在" in status:
                stats["existing"] += 1
            elif "非开放获取" in status or "无DOI" in status:
                stats["no_access"] += 1
            else:
                stats["failed"] += 1
                failed_papers.append((title[:50], status))
            
            time.sleep(0.5)
    
    # 打印统计
    print(f"\n{'─'*60}", flush=True)
    print(f"📊 统计:", flush=True)
    print(f"  ✅ 新下载: {stats['downloaded']}", flush=True)
    if stats['downloaded'] > 0:
        print(f"     - Unpaywall: {stats['unpaywall']}", flush=True)
        print(f"     - PMC: {stats['pmc']}", flush=True)
        print(f"     - SCI-hub: {stats['scihub']}", flush=True)
    print(f"  📁 已有: {stats['existing']}", flush=True)
    print(f"  🔒 无访问: {stats['no_access']}", flush=True)
    print(f"  ❌ 失败: {stats['failed']}", flush=True)
    
    if failed_papers and stats["failed"] > 0:
        print(f"\n❌ 失败列表:", flush=True)
        for title, reason in failed_papers[:3]:
            print(f"  - {title}... ({reason})", flush=True)
    
    return stats, new_downloads


def create_summary_report(pdf_dir, all_stats, new_downloads):
    """创建摘要报告"""
    report_file = pdf_dir / "_下载报告.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"CHO细胞文献下载报告\n")
        f.write(f"{'='*60}\n")
        f.write(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'='*60}\n\n")
        
        total_downloaded = 0
        total_unpaywall = 0
        total_pmc = 0
        total_scihub = 0
        total_existing = 0
        total_no_access = 0
        total_failed = 0
        
        for term, stats in all_stats.items():
            f.write(f"📌 {term}\n")
            f.write(f"  ✅ 新下载: {stats['downloaded']}\n")
            if stats['downloaded'] > 0:
                f.write(f"     - Unpaywall: {stats['unpaywall']}\n")
                f.write(f"     - PMC: {stats['pmc']}\n")
                f.write(f"     - SCI-hub: {stats['scihub']}\n")
            f.write(f"  📁 已有: {stats['existing']}\n")
            f.write(f"  🔒 无访问: {stats['no_access']}\n")
            f.write(f"  ❌ 失败: {stats['failed']}\n\n")
            
            total_downloaded += stats['downloaded']
            total_unpaywall += stats['unpaywall']
            total_pmc += stats['pmc']
            total_scihub += stats['scihub']
            total_existing += stats['existing']
            total_no_access += stats['no_access']
            total_failed += stats['failed']
        
        f.write(f"{'='*60}\n")
        f.write(f"本次总计:\n")
        f.write(f"  ✅ 新下载: {total_downloaded}\n")
        if total_downloaded > 0:
            f.write(f"     - Unpaywall: {total_unpaywall}\n")
            f.write(f"     - PMC: {total_pmc}\n")
            f.write(f"     - SCI-hub: {total_scihub}\n")
        f.write(f"  📁 已有: {total_existing}\n")
        f.write(f"  🔒 无访问: {total_no_access}\n")
        f.write(f"  ❌ 失败: {total_failed}\n\n")
        
        f.write(f"{'='*60}\n")
        f.write(f"PDF目录: {pdf_dir}\n")
        f.write(f"累计文件: {len(list(pdf_dir.glob('*.pdf')))} 个PDF\n")
    
    print(f"\n✅ 报告已保存: {report_file}", flush=True)


def main():
    print(f"\n{'='*60}", flush=True)
    print(f"📥 CHO细胞文献PDF下载器（含SCI-hub备选）", flush=True)
    print(f"{'='*60}", flush=True)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print(f"模式: Unpaywall → PMC → SCI-hub", flush=True)
    
    # 创建目录
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 统一保存: {PDF_DIR}\n", flush=True)
    
    # 加载历史
    download_history = load_download_history()
    print(f"📚 已下载: {len(download_history)} 个PDF\n", flush=True)
    
    # 查找JSON
    json_files = list(OUTPUT_DIR.glob("pubmed_*_latest.json"))
    if not json_files:
        json_files = list(OUTPUT_DIR.glob("pubmed_*.json"))
    
    if not json_files:
        print("❌ 未找到JSON文件", flush=True)
        return
    
    print(f"找到 {len(json_files)} 个数据文件\n", flush=True)
    
    # 处理
    all_stats = {}
    all_new_downloads = []
    
    for json_file in json_files:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        search_term = data.get("search_term", json_file.stem)
        stats, new_downloads = process_json_file(json_file, PDF_DIR, download_history)
        all_stats[search_term] = stats
        all_new_downloads.extend(new_downloads)
    
    # 更新历史
    if all_new_downloads:
        download_history.update(all_new_downloads)
        save_download_history(download_history)
        print(f"\n💾 已记录 {len(all_new_downloads)} 个新下载", flush=True)
    
    # 报告
    create_summary_report(PDF_DIR, all_stats, all_new_downloads)
    
    # 统计
    total_pdfs = len(list(PDF_DIR.glob('*.pdf')))
    
    print(f"\n{'='*60}", flush=True)
    print(f"✅ 全部完成！", flush=True)
    print(f"📁 PDF目录: {PDF_DIR}", flush=True)
    print(f"📚 累计PDF: {total_pdfs} 个", flush=True)
    print(f"{'='*60}\n", flush=True)


if __name__ == "__main__":
    main()
