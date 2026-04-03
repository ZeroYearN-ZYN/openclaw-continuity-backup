#!/usr/bin/env python3
"""
CHO细胞表达文献自动下载器 - Semantic Scholar版本
免费API，无需密钥
"""

import os
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
import time

# ========== 配置 ==========
SEARCH_TERMS = [
    # 针对 CHO-S 和 CHO-K1 特定细胞系
    "CHO-S antibody production",
    "CHO-K1 recombinant protein",
    "CHO-S cell culture",
    "CHO-K1 expression",
    
    # 针对产量提升
    "CHO high titer production",
    "CHO productivity improvement",
    "CHO fed-batch optimization",
    "Chinese hamster ovary cell density",
    
    # 针对抗体/蛋白高产
    "CHO monoclonal antibody production",
    "CHO recombinant protein yield",
    "CHO bioreactor scale-up",
    "Chinese hamster ovary perfusion",
    
    # 针对工艺优化
    "CHO cell media optimization",
    "CHO culture process development",
    "CHO glycosylation engineering",
    "CHO cell line development producer",
]

OUTPUT_DIR = Path(__file__).parent.parent / "output"
DAYS_BACK = 7
LIMIT_PER_SEARCH = 30

# ========== API配置 ==========
BASE_URL = "https://api.semanticscholar.org/graph/v1"


def search_papers(term, days_back=7, limit=30):
    """搜索Semantic Scholar"""
    year_start = (datetime.now() - timedelta(days=days_back)).year
    
    params = {
        "query": term,
        "limit": limit,
        "year": f"{year_start}-",
        "fields": "title,authors,year,journal,doi,url,publicationDate,abstract",
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}/paper/search",
            params=params,
            headers={"User-Agent": "CHO-Paper-Fetcher/1.0"},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        papers = []
        for p in data.get("data", []):
            papers.append({
                "paperId": p.get("paperId"),
                "title": p.get("title", "N/A"),
                "authors": [a.get("name") for a in p.get("authors", [])],
                "year": p.get("year"),
                "journal": p.get("journal", {}).get("name") if p.get("journal") else "N/A",
                "doi": p.get("doi", ""),
                "url": p.get("url", ""),
                "pub_date": p.get("publicationDate", ""),
                "abstract": p.get("abstract", "")[:500] if p.get("abstract") else "",
            })
        
        return papers
    except Exception as e:
        print(f"❌ 搜索失败 [{term}]: {e}")
        return []


def save_results(papers, term):
    """保存到JSON"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d")
    safe_term = term.replace(" ", "_").lower()
    output_file = OUTPUT_DIR / f"semantic_{safe_term}_{timestamp}.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "search_term": term,
            "fetch_date": datetime.now().isoformat(),
            "source": "Semantic Scholar",
            "count": len(papers),
            "papers": papers,
        }, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 保存 {len(papers)} 篇文献 → {output_file}")


def main():
    print(f"📚 Semantic Scholar文献抓取 - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    all_papers = []
    for i, term in enumerate(SEARCH_TERMS):
        print(f"🔍 搜索: {term}")
        papers = search_papers(term, DAYS_BACK, LIMIT_PER_SEARCH)
        print(f"   找到 {len(papers)} 篇")
        
        if papers:
            save_results(papers, term)
            all_papers.extend(papers)
        
        # 避免API限制
        if i < len(SEARCH_TERMS) - 1:
            time.sleep(1)
        print()
    
    print(f"✅ 总计: {len(all_papers)} 篇文献")
    return all_papers


if __name__ == "__main__":
    main()
