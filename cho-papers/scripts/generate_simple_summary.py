#!/usr/bin/env python3
"""
生成通俗易懂的每日摘要报告
"""

import json
from pathlib import Path
from datetime import datetime

# 配置
REPORT_DIR = Path.home() / "Desktop" / "CHO-Literature-Reports"
DATE = datetime.now().strftime("%Y-%m-%d")

def load_papers_data():
    """加载文献数据"""
    json_file = REPORT_DIR / DATE / f"文献数据_{DATE}.json"
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_simple_summary(papers_data):
    """生成简单易懂的摘要"""
    
    # 获取高度相关的文献
    high_relevance = []
    for paper in papers_data["papers"]:
        summary = paper.get("summary", {})
        if "⭐⭐⭐" in summary.get("相关度", ""):
            high_relevance.append(paper)
    
    # 生成摘要报告
    report = f"""# 📚 CHO细胞文献每日摘要

**日期**: {datetime.now().strftime('%Y年%m月%d日')}  
**处理文献总数**: {len(papers_data["papers"])} 篇  
**高度相关文献**: {len(high_relevance)} 篇

---

## 🎯 今日重点摘要

"""
    
    # 为每篇高度相关文献写摘要
    for i, paper in enumerate(high_relevance[:10], 1):  # 只取前10篇
        summary = paper.get("summary", {})
        title = summary.get("原始标题", paper.get("title", "未知标题"))
        
        # 提取关键词
        keywords = summary.get("主要关键词", [])
        keywords_str = "、".join(keywords) if keywords else "未分类"
        
        # 生成摘要
        report += f"""### {i}. {title}

**研究领域**: {keywords_str}

**通俗摘要**:
"""
        
        # 根据关键词生成通俗摘要
        if "CHO细胞" in keywords:
            report += f"""这篇文献研究的是CHO细胞（中国仓鼠卵巢细胞）在生物制药中的应用。
CHO细胞是生产治疗性蛋白质的重要工具，比如抗体药物。
这项研究可能涉及如何让CHO细胞更高效地生产蛋白质，或者改善细胞培养条件。"""
        elif "抗体生产" in keywords:
            report += f"""这篇文献关注抗体药物的生产过程。
抗体药物是现代医学的重要治疗手段，用于治疗癌症、自身免疫疾病等。
研究可能涉及如何提高抗体产量、改善抗体质量，或者优化生产工艺。"""
        elif "细胞培养" in keywords:
            report += f"""这篇文献研究细胞培养技术。
细胞培养是生物制药的基础，就像种菜需要好的土壤和肥料一样。
研究可能涉及如何为细胞提供更好的生长环境，提高培养效率。"""
        elif "基因表达" in keywords:
            report += f"""这篇文献研究基因表达调控。
基因表达就像细胞的"指令系统"，控制细胞生产什么蛋白质。
研究可能涉及如何让细胞更有效地表达目标基因，提高蛋白质产量。"""
        elif "糖基化" in keywords:
            report += f"""这篇文献研究蛋白质的糖基化修饰。
糖基化就像给蛋白质"化妆"，影响蛋白质的功能和稳定性。
研究可能涉及如何控制糖基化过程，改善药物效果。"""
        else:
            report += f"""这篇文献涉及CHO细胞研究的多个方面。
研究可能涉及细胞培养、蛋白质生产、工艺优化等多个环节。"""
        
        report += f"""

**对CHO细胞研究的意义**:
这项研究为改善CHO细胞的生产效率提供了新思路，可能帮助制药公司生产更多、更好的治疗性蛋白质，造福患者。

---

"""
    
    # 添加总结
    report += f"""## 📊 今日总结

**处理文献总数**: {len(papers_data["papers"])} 篇  
**成功解析**: {papers_data["statistics"]["success"]} 篇  
**高度相关**: {len(high_relevance)} 篇

**主要研究方向**:
"""
    
    # 统计关键词
    all_keywords = []
    for paper in papers_data["papers"]:
        all_keywords.extend(paper.get("summary", {}).get("主要关键词", []))
    
    keyword_counts = {}
    for kw in all_keywords:
        keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
    
    sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
    
    for kw, count in sorted_keywords[:5]:
        report += f"- {kw}: {count}篇\n"
    
    report += f"""
**建议阅读**:
1. 优先阅读标记为"高度相关"的文献
2. 关注与您研究方向相关的关键词
3. 查看原文获取详细信息

**原文位置**: `~/Desktop/CHO-Literature-All/`

---

**报告生成**: OpenClaw CHO-Literature System  
**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    return report

def main():
    print(f"生成每日摘要报告 - {DATE}")
    
    # 加载文献数据
    papers_data = load_papers_data()
    
    # 生成摘要
    summary_report = generate_simple_summary(papers_data)
    
    # 保存报告
    output_dir = REPORT_DIR / DATE
    summary_file = output_dir / f"每日摘要_{DATE}.md"
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(summary_report)
    
    print(f"✅ 摘要报告已生成: {summary_file}")
    print(f"📊 统计:")
    print(f"  - 总文献数: {len(papers_data['papers'])}")
    print(f"  - 高度相关: {len([p for p in papers_data['papers'] if '⭐⭐⭐' in p.get('summary', {}).get('相关度', '')])}")
    
    return summary_file

if __name__ == "__main__":
    main()
