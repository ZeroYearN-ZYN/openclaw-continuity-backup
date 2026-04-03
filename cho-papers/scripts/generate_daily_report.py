#!/usr/bin/env python3
"""
CHO细胞文献翻译和摘要生成器
自动翻译PDF，提取关键信息，生成每日报告
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime
import re

# ========== 配置 ==========
WORKSPACE = Path("/Users/mini4-2/.openclaw/workspace/cho-papers")
PDF_DIR = Path.home() / "Desktop" / "CHO-Literature-All"
REPORT_DIR = Path.home() / "Desktop" / "CHO-Literature-Reports"

# 翻译配置（使用免费的翻译方案）
TRANSLATION_METHOD = "summarize"  # summarize（摘要）或 full（全文翻译）


def extract_text_from_pdf(pdf_path):
    """从PDF提取文本"""
    
    # 方法1: 优先使用 PyPDF2（更可靠）
    try:
        import PyPDF2
        
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
            if text.strip():
                return text.strip()
    except Exception as e:
        print(f"  ⚠️  PyPDF2提取失败: {str(e)[:50]}")
    
    # 方法2: 尝试 pdftotext
    try:
        result = subprocess.run(
            ['pdftotext', '-layout', str(pdf_path), '-'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception as e:
        print(f"  ⚠️  pdftotext提取失败: {str(e)[:50]}")
    
    return None


def extract_key_info(text, title):
    """提取关键信息"""
    # 限制文本长度（避免太长）
    max_chars = 3000
    if len(text) > max_chars:
        text = text[:max_chars] + "..."
    
    # 提取关键信息
    info = {
        "title": title,
        "word_count": len(text.split()),
        "has_keywords": any(kw in text.lower() for kw in ['cho', 'chinese hamster', 'recombinant', 'expression']),
        "sections": []
    }
    
    # 检测常见部分
    sections_keywords = {
        "摘要": ["abstract", "summary"],
        "方法": ["methods", "methodology", "experimental"],
        "结果": ["results", "findings"],
        "结论": ["conclusion", "discussion"],
    }
    
    text_lower = text.lower()
    for section_cn, keywords in sections_keywords.items():
        if any(kw in text_lower for kw in keywords):
            info["sections"].append(section_cn)
    
    # 提取前200个字符作为预览
    info["preview"] = text[:200].replace('\n', ' ').strip()
    
    return info


def generate_summary_with_ai(title, text):
    """使用AI生成摘要（这里使用简化的关键词提取）"""
    
    # 由于没有直接的翻译API，我们生成结构化摘要
    summary = {
        "原始标题": title,
        "主要关键词": [],
        "研究类型": "未分类",
        "相关度": "未知"
    }
    
    # 提取关键词
    keywords_map = {
        "CHO细胞": ["cho cell", "chinese hamster ovary"],
        "重组蛋白": ["recombinant protein", "recombinant expression"],
        "抗体生产": ["antibody", "mab", "monoclonal"],
        "细胞培养": ["cell culture", "bioreactor", "fed-batch"],
        "基因表达": ["gene expression", "transfection"],
        "糖基化": ["glycosylation", "glycan"],
        "过程优化": ["optimization", "process development"],
    }
    
    text_lower = text.lower()
    for keyword_cn, keywords_en in keywords_map.items():
        if any(kw in text_lower for kw in keywords_en):
            summary["主要关键词"].append(keyword_cn)
    
    # 判断研究类型
    if "review" in text_lower or "overview" in text_lower:
        summary["研究类型"] = "综述"
    elif "methods" in text_lower and "results" in text_lower:
        summary["研究类型"] = "原创研究"
    elif "case study" in text_lower:
        summary["研究类型"] = "案例研究"
    
    # 判断相关度
    cho_mentions = text_lower.count("cho")
    if cho_mentions > 10:
        summary["相关度"] = "高度相关 ⭐⭐⭐"
    elif cho_mentions > 5:
        summary["相关度"] = "相关 ⭐⭐"
    elif cho_mentions > 0:
        summary["相关度"] = "提及 ⭐"
    else:
        summary["相关度"] = "低相关"
    
    return summary


def process_pdf(pdf_path):
    """处理单个PDF"""
    title = pdf_path.stem
    
    print(f"  📄 处理: {title[:60]}...")
    
    # 提取文本
    text = extract_text_from_pdf(pdf_path)
    
    if not text:
        return {
            "title": title,
            "status": "❌ 无法提取文本",
            "file": pdf_path.name
        }
    
    # 提取关键信息
    key_info = extract_key_info(text, title)
    
    # 生成摘要
    summary = generate_summary_with_ai(title, text)
    
    return {
        "title": title,
        "status": "✅ 成功",
        "file": pdf_path.name,
        "word_count": key_info["word_count"],
        "preview": key_info["preview"],
        "summary": summary,
        "sections": key_info["sections"],
        "path": str(pdf_path)
    }


def generate_daily_report(papers_data, date_str):
    """生成每日报告"""
    
    # 创建报告目录
    date_dir = REPORT_DIR / date_str
    date_dir.mkdir(parents=True, exist_ok=True)
    
    # 统计
    total = len(papers_data)
    success = sum(1 for p in papers_data if "成功" in p.get("status", ""))
    failed = total - success
    
    # 按相关度排序
    high_relevance = [p for p in papers_data if "⭐⭐⭐" in p.get("summary", {}).get("相关度", "")]
    medium_relevance = [p for p in papers_data if "⭐⭐" in p.get("summary", {}).get("相关度", "")]
    
    # 生成Markdown报告
    report = f"""# 📚 CHO细胞文献每日报告

**日期**: {datetime.now().strftime('%Y年%m月%d日')}  
**生成时间**: {datetime.now().strftime('%H:%M:%S')}

---

## 📊 统计概览

- **总计处理**: {total} 篇文献
- **成功解析**: {success} 篇 ✅
- **解析失败**: {failed} 篇 ❌
- **高度相关**: {len(high_relevance)} 篇 ⭐⭐⭐
- **中等相关**: {len(medium_relevance)} 篇 ⭐⭐

---

## 🔥 高度相关文献 ({len(high_relevance)}篇)

"""
    
    for i, paper in enumerate(high_relevance, 1):
        summary = paper.get("summary", {})
        report += f"""### {i}. {summary.get('原始标题', paper['title'])}

**关键词**: {', '.join(summary.get('主要关键词', []))}  
**研究类型**: {summary.get('研究类型', '未知')}  
**相关度**: {summary.get('相关度', '未知')}  
**字数**: {paper.get('word_count', 0):,}

**内容预览**:
{paper.get('preview', '无预览')}

**文件**: `{paper.get('file', '')}`

---

"""
    
    report += f"""## 📌 中等相关文献 ({len(medium_relevance)}篇)

"""
    
    for i, paper in enumerate(medium_relevance, 1):
        summary = paper.get("summary", {})
        report += f"""### {i}. {summary.get('原始标题', paper['title'])}

**关键词**: {', '.join(summary.get('主要关键词', []))}  
**相关度**: {summary.get('相关度', '未知')}

**文件**: `{paper.get('file', '')}`

---

"""
    
    # 其他文献
    other_papers = [p for p in papers_data if p not in high_relevance and p not in medium_relevance]
    
    if other_papers:
        report += f"""## 📄 其他文献 ({len(other_papers)}篇)

"""
        for paper in other_papers:
            summary = paper.get("summary", {})
            report += f"""- **{summary.get('原始标题', paper['title'])}** - {summary.get('相关度', '未知')}
  文件: `{paper.get('file', '')}`

"""
    
    # 添加总结
    report += f"""---

## 💡 今日总结

1. **主要研究方向**: 
"""
    
    # 统计关键词
    all_keywords = []
    for paper in papers_data:
        all_keywords.extend(paper.get("summary", {}).get("主要关键词", []))
    
    keyword_counts = {}
    for kw in all_keywords:
        keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
    
    sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
    
    for kw, count in sorted_keywords[:5]:
        report += f"   - {kw}: {count}篇\n"
    
    report += f"""
2. **推荐阅读**: 优先查看标记为 ⭐⭐⭐ 的 {len(high_relevance)} 篇高度相关文献

3. **原文位置**: `~/Desktop/CHO-Literature-All/`

---

## 📧 联系方式

如有问题，请查看原始PDF文件或联系研究团队。

---

**报告生成器**: OpenClaw CHO-Literature System  
**版本**: 1.0  
**更新**: 每日自动生成
"""
    
    # 保存报告
    report_file = date_dir / f"每日报告_{date_str}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    # 生成JSON数据
    json_file = date_dir / f"文献数据_{date_str}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            "date": date_str,
            "generated_at": datetime.now().isoformat(),
            "statistics": {
                "total": total,
                "success": success,
                "failed": failed,
                "high_relevance": len(high_relevance),
                "medium_relevance": len(medium_relevance)
            },
            "papers": papers_data
        }, f, ensure_ascii=False, indent=2)
    
    return report_file, json_file


def main():
    print(f"\n{'='*60}")
    print(f"📚 CHO细胞文献翻译和摘要生成器")
    print(f"{'='*60}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 检查PDF目录
    if not PDF_DIR.exists():
        print(f"❌ PDF目录不存在: {PDF_DIR}")
        return
    
    # 获取所有PDF
    pdf_files = list(PDF_DIR.glob("*.pdf"))
    
    if not pdf_files:
        print(f"❌ 未找到PDF文件")
        return
    
    print(f"📁 找到 {len(pdf_files)} 个PDF文件\n")
    
    # 处理每个PDF
    papers_data = []
    
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"[{i}/{len(pdf_files)}] ", end="")
        result = process_pdf(pdf_file)
        papers_data.append(result)
    
    # 生成报告
    date_str = datetime.now().strftime("%Y-%m-%d")
    report_file, json_file = generate_daily_report(papers_data, date_str)
    
    print(f"\n{'='*60}")
    print(f"✅ 报告生成完成！")
    print(f"{'='*60}")
    print(f"📄 Markdown报告: {report_file}")
    print(f"📊 JSON数据: {json_file}")
    print(f"📁 报告目录: {REPORT_DIR / date_str}")
    print(f"{'='*60}\n")
    
    # 显示统计
    success = sum(1 for p in papers_data if "成功" in p.get("status", ""))
    high_rel = sum(1 for p in papers_data if "⭐⭐⭐" in p.get("summary", {}).get("相关度", ""))
    
    print(f"📊 处理统计:")
    print(f"  ✅ 成功: {success}/{len(pdf_files)}")
    print(f"  ⭐⭐⭐ 高度相关: {high_rel}")
    print(f"\n💡 查看报告:")
    print(f"  open {report_file}")


if __name__ == "__main__":
    main()
