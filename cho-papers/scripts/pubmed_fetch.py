#!/usr/bin/env python3
"""
CHO细胞表达文献自动下载器 - PubMed版本
带去重功能，避免重复抓取
"""

import os
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path

# ========== 配置 ==========
NCBI_EMAIL = os.environ.get("NCBI_EMAIL", "zhu199365@gmail.com")
NCBI_API_KEY = os.environ.get("NCBI_API_KEY", "")  # 从环境变量读取，不要硬编码

SEARCH_TERMS = [
    # 针对 CHO-S 和 CHO-K1 特定细胞系
    '"CHO-S" antibody production',
    '"CHO-K1" recombinant protein',
    '"CHO-S" cell culture optimization',
    '"CHO-K1" expression system',
    
    # 针对产量提升
    'CHO cells high titer production',
    'CHO cell productivity improvement',
    'CHO fed-batch optimization',
    'Chinese hamster ovary cell density',
    
    # 针对抗体/蛋白高产
    'CHO monoclonal antibody production',
    'CHO recombinant protein yield',
    'CHO cell bioreactor scale-up',
    'Chinese hamster ovary perfusion culture',
    
    # 针对工艺优化
    'CHO cell media optimization',
    'CHO cell culture process development',
    'CHO glycosylation engineering',
    'CHO cell line development high producer',
]

WORKSPACE = Path("/Users/mini4-2/.openclaw/workspace/cho-papers")
OUTPUT_DIR = WORKSPACE / "output"
HISTORY_FILE = WORKSPACE / "data" / "pmid_history.json"
DAYS_BACK = 10000  # 抓取从2000年至今（约26年）

# ========== API基础配置 ==========
BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def load_history():
    """加载已处理的PMID历史"""
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    return set()


def save_history(history):
    """保存PMID历史"""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(history), f, indent=2)


def search_papers(term, days_back=30):
    """搜索最近N天的文献"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    date_query = f"{start_date.strftime('%Y/%m/%d')}:{end_date.strftime('%Y/%m/%d')}[PDAT]"
    
    params = {
        "db": "pubmed",
        "term": f"{term} AND {date_query}",
        "retmax": 100,
        "retmode": "json",
        "email": NCBI_EMAIL,
    }
    
    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY
    
    try:
        response = requests.get(f"{BASE_URL}/esearch.fcgi", params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        print(f"❌ 搜索失败 [{term}]: {e}")
        return []


def fetch_paper_details(pmid_list):
    """获取文献详情"""
    if not pmid_list:
        return []
    
    params = {
        "db": "pubmed",
        "id": ",".join(pmid_list),
        "retmode": "json",
        "email": NCBI_EMAIL,
    }
    
    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY
    
    try:
        response = requests.get(f"{BASE_URL}/esummary.fcgi", params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        papers = []
        result = data.get("result", {})
        for pmid in pmid_list:
            if pmid in result and "error" not in result[pmid]:
                paper = result[pmid]
                papers.append({
                    "pmid": pmid,
                    "title": paper.get("title", "N/A"),
                    "authors": [a.get("name") for a in paper.get("authors", [])],
                    "journal": paper.get("fulljournalname", "N/A"),
                    "pubdate": paper.get("pubdate", "N/A"),
                    "doi": paper.get("elocationid", ""),
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    "fetch_date": datetime.now().isoformat(),
                })
        return papers
    except Exception as e:
        print(f"❌ 获取详情失败: {e}")
        return []


def save_results(papers, term, is_incremental=False):
    """保存结果到JSON（追加模式）"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d")
    safe_term = term.replace(" ", "_").lower()
    output_file = OUTPUT_DIR / f"pubmed_{safe_term}_latest.json"
    
    # 如果是增量更新，合并现有数据
    existing_papers = []
    if is_incremental and output_file.exists():
        with open(output_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
            existing_papers = existing_data.get("papers", [])
    
    # 合并新旧数据（新数据在前）
    all_papers = papers + existing_papers
    
    # 去重（基于PMID）
    seen_pmids = set()
    unique_papers = []
    for paper in all_papers:
        pmid = paper.get("pmid")
        if pmid and pmid not in seen_pmids:
            seen_pmids.add(pmid)
            unique_papers.append(paper)
    
    # 保存
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "search_term": term,
            "last_update": datetime.now().isoformat(),
            "total_count": len(unique_papers),
            "new_count": len(papers),
            "papers": unique_papers,
        }, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 保存 {len(papers)} 篇新文献 → {output_file}")
    print(f"  总计 {len(unique_papers)} 篇（已去重）")
    
    return output_file


def main():
    print(f"🔬 CHO细胞文献抓取（去重模式） - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    # 加载历史记录
    history = load_history()
    print(f"📚 历史记录: {len(history)} 篇已处理\n")
    
    total_new = 0
    all_new_pmids = []
    
    for term in SEARCH_TERMS:
        print(f"🔍 搜索: {term}")
        
        # 搜索
        pmids = search_papers(term, DAYS_BACK)
        print(f"   找到 {len(pmids)} 篇")
        
        # 过滤已处理的
        new_pmids = [p for p in pmids if p not in history]
        print(f"   新文献 {len(new_pmids)} 篇")
        
        if new_pmids:
            # 获取详情
            papers = fetch_paper_details(new_pmids)
            
            # 保存（增量模式）
            save_results(papers, term, is_incremental=True)
            
            # 记录到历史
            all_new_pmids.extend(new_pmids)
            total_new += len(new_pmids)
        else:
            print(f"   ✓ 无新文献")
        
        print()
    
    # 更新历史记录
    if all_new_pmids:
        history.update(all_new_pmids)
        save_history(history)
        print(f"💾 已记录 {len(all_new_pmids)} 个新PMID")
    
    print(f"\n{'='*60}")
    print(f"✅ 本次新增: {total_new} 篇")
    print(f"📚 累计处理: {len(history)} 篇")
    print(f"{'='*60}")
    
    return total_new


if __name__ == "__main__":
    main()
