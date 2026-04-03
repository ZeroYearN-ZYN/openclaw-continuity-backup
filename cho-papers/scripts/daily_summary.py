#!/usr/bin/env python3
"""
CHO 细胞文献每日摘要系统
每天早上读取新文献，提取文本，准备给 AI 生成摘要
"""

import os
import sys
import json
import glob
from datetime import datetime
from pathlib import Path

# 配置
PDF_DIR = Path.home() / "Desktop" / "CHO-Literature-All"
OUTPUT_DIR = Path.home() / "Desktop" / "CHO-Literature-Reports"
HISTORY_FILE = Path.home() / ".openclaw" / "workspace" / "cho-papers" / "data" / "summarized.json"

def load_history():
    """加载已处理的文件历史"""
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    return set()

def save_history(history):
    """保存处理历史"""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(history), f, ensure_ascii=False, indent=2)

def get_new_pdfs(history):
    """获取未处理的 PDF 文件"""
    pdf_files = list(PDF_DIR.glob("*.pdf"))
    new_pdfs = [f for f in pdf_files if f.name not in history]
    return sorted(new_pdfs, key=lambda x: x.stat().st_mtime, reverse=True)

def extract_text(pdf_path, max_chars=8000):
    """提取 PDF 文本"""
    try:
        import fitz
        doc = fitz.open(str(pdf_path))
        text_parts = []
        total_chars = 0
        
        for page in doc:
            text = page.get_text()
            if total_chars + len(text) > max_chars:
                text = text[:max_chars - total_chars]
            text_parts.append(text)
            total_chars += len(text)
            if total_chars >= max_chars:
                break
        
        doc.close()
        return "\n".join(text_parts)
    except Exception as e:
        return f"[提取失败: {e}]"

def get_paper_info(pdf_path):
    """获取论文基本信息"""
    try:
        import fitz
        doc = fitz.open(str(pdf_path))
        info = {
            "pages": len(doc),
            "title": doc.metadata.get("title", ""),
            "author": doc.metadata.get("author", ""),
        }
        doc.close()
        return info
    except:
        return {"pages": 0, "title": "", "author": ""}

def main():
    """主函数"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    print(f"📚 CHO 细胞文献每日摘要 - {today}")
    print("=" * 50)
    
    # 加载历史
    history = load_history()
    print(f"📖 已处理文献: {len(history)} 篇")
    
    # 获取新文献
    new_pdfs = get_new_pdfs(history)
    
    if not new_pdfs:
        print("ℹ️  没有新文献需要处理")
        return {
            "status": "no_new_papers",
            "message": "没有新文献",
            "count": 0
        }
    
    print(f"📄 发现新文献: {len(new_pdfs)} 篇")
    
    # 准备输出目录
    output_dir = OUTPUT_DIR / today
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 处理每篇文献
    papers_data = []
    text_file = output_dir / f"文献全文_{today}.txt"
    
    with open(text_file, 'w', encoding='utf-8') as tf:
        for i, pdf in enumerate(new_pdfs, 1):
            print(f"\n处理: {pdf.name[:50]}...")
            
            # 提取文本
            text = extract_text(pdf)
            info = get_paper_info(pdf)
            
            # 从文件名提取标题
            title = pdf.stem
            if len(title) > 100:
                title = title[:100] + "..."
            
            paper_data = {
                "filename": pdf.name,
                "title": title,
                "pages": info["pages"],
                "text_length": len(text)
            }
            papers_data.append(paper_data)
            
            # 写入文本文件
            tf.write(f"\n{'='*60}\n")
            tf.write(f"文献 {i}: {title}\n")
            tf.write(f"页数: {info['pages']}\n")
            tf.write(f"文件: {pdf.name}\n")
            tf.write(f"{'='*60}\n\n")
            tf.write(text)
            tf.write("\n\n")
            
            # 更新历史
            history.add(pdf.name)
    
    # 保存历史
    save_history(history)
    
    # 生成元数据文件
    summary_file = output_dir / f"待摘要文献_{today}.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            "date": today,
            "count": len(papers_data),
            "papers": papers_data,
            "text_file": str(text_file)
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 已生成待摘要文件:")
    print(f"   📄 文本: {text_file}")
    print(f"   📊 元数据: {summary_file}")
    print(f"   📚 文献数量: {len(papers_data)} 篇")
    
    return {
        "status": "success",
        "count": len(papers_data),
        "text_file": str(text_file),
        "papers": [{"title": p["title"][:50], "pages": p["pages"]} for p in papers_data]
    }

if __name__ == "__main__":
    result = main()
    print("\n" + "=" * 50)
    print(json.dumps(result, ensure_ascii=False, indent=2))
