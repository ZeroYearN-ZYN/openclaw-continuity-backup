#!/usr/bin/env python3
"""
生成文献下载链接页面
手动下载无法自动获取的文献
"""

import json
from pathlib import Path
from datetime import datetime

WORKSPACE = Path("/Users/mini4-2/.openclaw/workspace/cho-papers")
OUTPUT_DIR = WORKSPACE / "output"
PDF_DIR = Path.home() / "Desktop" / "CHO-Literature-All"
DOWNLOAD_HISTORY = WORKSPACE / "data" / "download_history.json"


def load_download_history():
    """加载已下载的PMID"""
    if DOWNLOAD_HISTORY.exists():
        with open(DOWNLOAD_HISTORY, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    return set()


def get_existing_pdfs():
    """获取已下载的PDF文件名"""
    pdf_files = set()
    if PDF_DIR.exists():
        for pdf in PDF_DIR.glob("*.pdf"):
            pdf_files.add(pdf.stem)
    return pdf_files


def generate_html():
    """生成HTML下载页面"""
    
    # 加载历史
    download_history = load_download_history()
    existing_pdfs = get_existing_pdfs()
    
    # 收集所有文献
    all_papers = []
    json_files = list(OUTPUT_DIR.glob("pubmed_*_latest.json"))
    if not json_files:
        json_files = list(OUTPUT_DIR.glob("pubmed_*.json"))
    
    for json_file in json_files:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            all_papers.extend(data.get("papers", []))
    
    # 去重
    seen_pmids = set()
    unique_papers = []
    for paper in all_papers:
        pmid = paper.get("pmid")
        if pmid and pmid not in seen_pmids:
            seen_pmids.add(pmid)
            unique_papers.append(paper)
    
    # 分类：已下载 vs 未下载
    downloaded = []
    not_downloaded = []
    
    for paper in unique_papers:
        pmid = paper.get("pmid", "")
        title = paper.get("title", "")
        doi = paper.get("doi", "").replace("doi: ", "").strip()
        
        # 检查是否已下载
        if pmid in download_history or any(title[:50] in pdf for pdf in existing_pdfs):
            downloaded.append(paper)
        else:
            not_downloaded.append(paper)
    
    # 生成HTML
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CHO细胞文献下载</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        .stats {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .paper {{
            background: white;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid #2196F3;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .paper.downloaded {{
            border-left-color: #4CAF50;
            opacity: 0.7;
        }}
        .title {{
            font-weight: bold;
            color: #333;
            margin-bottom: 8px;
        }}
        .meta {{
            color: #666;
            font-size: 0.9em;
            margin-bottom: 8px;
        }}
        .links {{
            margin-top: 10px;
        }}
        .links a {{
            display: inline-block;
            margin-right: 10px;
            margin-bottom: 5px;
            padding: 5px 12px;
            background: #2196F3;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-size: 0.85em;
        }}
        .links a:hover {{
            background: #1976D2;
        }}
        .links a.scihub {{
            background: #FF9800;
        }}
        .links a.scihub:hover {{
            background: #F57C00;
        }}
        .status {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 0.8em;
            margin-left: 10px;
        }}
        .status.downloaded {{
            background: #4CAF50;
            color: white;
        }}
        .status.not-downloaded {{
            background: #FF5722;
            color: white;
        }}
        .section {{
            margin-top: 30px;
        }}
        .section h2 {{
            color: #555;
            margin-bottom: 15px;
        }}
    </style>
</head>
<body>
    <h1>📚 CHO细胞文献下载中心</h1>
    
    <div class="stats">
        <h3>📊 统计信息</h3>
        <p>✅ 已下载: <strong>{len(downloaded)}</strong> 篇</p>
        <p>📥 待下载: <strong>{len(not_downloaded)}</strong> 篇</p>
        <p>📄 总计: <strong>{len(unique_papers)}</strong> 篇</p>
        <p>🕐 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="section">
        <h2>📥 待下载文献 ({len(not_downloaded)}篇)</h2>
"""
    
    # 未下载的文献
    for paper in not_downloaded:
        pmid = paper.get("pmid", "")
        title = paper.get("title", "N/A")
        authors = paper.get("authors", [])
        journal = paper.get("journal", "N/A")
        pubdate = paper.get("pubdate", "N/A")
        doi = paper.get("doi", "").replace("doi: ", "").strip()
        
        author_str = ", ".join(authors[:3])
        if len(authors) > 3:
            author_str += " et al."
        
        html += f"""
        <div class="paper">
            <div class="title">{title} <span class="status not-downloaded">待下载</span></div>
            <div class="meta">
                <strong>作者:</strong> {author_str} | 
                <strong>期刊:</strong> {journal} | 
                <strong>日期:</strong> {pubdate} |
                <strong>PMID:</strong> {pmid}
            </div>
            <div class="links">
                <a href="https://pubmed.ncbi.nlm.nih.gov/{pmid}/" target="_blank">PubMed</a>
"""
        
        if doi:
            html += f"""
                <a href="https://doi.org/{doi}" target="_blank">DOI</a>
                <a href="https://sci-hub.se/{doi}" target="_blank" class="scihub">SCI-hub</a>
                <a href="https://sci-hub.sg/{doi}" target="_blank" class="scihub">SCI-hub (备用)</a>
"""
        
        html += """
            </div>
        </div>
"""
    
    html += """
    </div>
    
    <div class="section">
        <h2>✅ 已下载文献 ({len(downloaded)}篇)</h2>
"""
    
    # 已下载的文献
    for paper in downloaded:
        pmid = paper.get("pmid", "")
        title = paper.get("title", "N/A")
        authors = paper.get("authors", [])
        journal = paper.get("journal", "N/A")
        
        author_str = ", ".join(authors[:3])
        if len(authors) > 3:
            author_str += " et al."
        
        html += f"""
        <div class="paper downloaded">
            <div class="title">{title} <span class="status downloaded">已下载</span></div>
            <div class="meta">
                <strong>作者:</strong> {author_str} | 
                <strong>期刊:</strong> {journal} |
                <strong>PMID:</strong> {pmid}
            </div>
        </div>
"""
    
    html += """
    </div>
    
    <div class="stats" style="margin-top: 40px;">
        <h3>💡 使用提示</h3>
        <p><strong>自动下载：</strong>运行 <code>bash /Users/mini4-2/.openclaw/workspace/cho-papers/scripts/run_daily.sh</code></p>
        <p><strong>手动下载：</strong>点击上方链接，优先尝试DOI，如无法访问再使用SCI-hub</p>
        <p><strong>PDF位置：</strong><code>~/Desktop/CHO-Literature-All/</code></p>
    </div>
</body>
</html>
"""
    
    # 保存HTML
    output_file = PDF_DIR / "文献下载中心.html"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ 已生成下载页面: {output_file}")
    print(f"\n📊 统计:")
    print(f"  ✅ 已下载: {len(downloaded)} 篇")
    print(f"  📥 待下载: {len(not_downloaded)} 篇")
    print(f"  📄 总计: {len(unique_papers)} 篇")
    print(f"\n💡 在浏览器中打开:")
    print(f"  file://{output_file}")
    
    return output_file


if __name__ == "__main__":
    generate_html()
