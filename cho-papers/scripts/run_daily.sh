#!/bin/bash
# 每日文献处理流程（包含报告生成）

set -e

PROJECT_DIR="/Users/mini4-2/.openclaw/workspace/cho-papers"
LOG_DIR="$PROJECT_DIR/logs"
DATE=$(date +%Y%m%d)
LOG_FILE="$LOG_DIR/fetch_$DATE.log"

mkdir -p "$LOG_DIR"

exec > >(tee -a "$LOG_FILE") 2>&1

echo "========================================"
echo "CHO细胞文献自动处理 - $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo

# 步骤1: 抓取文献
echo "📚 步骤1: PubMed文献抓取（去重模式）..."
echo "----------------------------------------"
cd "$PROJECT_DIR"
python3 scripts/pubmed_fetch.py
echo

# 步骤2: 下载PDF
echo "📥 步骤2: 下载开放获取PDF..."
echo "----------------------------------------"
python3 scripts/download_pdfs_enhanced.py
echo

# 步骤3: 生成下载页面
echo "🌐 步骤3: 生成下载页面..."
echo "----------------------------------------"
python3 scripts/generate_download_page.py
echo

# 步骤4: 生成每日报告
echo "📊 步骤4: 生成每日报告（翻译+摘要）..."
echo "----------------------------------------"
python3 scripts/generate_daily_report.py
echo

echo "========================================"
echo "✅ 全部完成 - $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo "📁 PDF位置: ~/Desktop/CHO-Literature-All/"
echo "📄 每日报告: ~/Desktop/CHO-Literature-Reports/$(date '+%Y-%m-%d')/"
echo "🌐 下载页面: ~/Desktop/CHO-Literature-All/文献下载中心.html"
echo "========================================"

find "$LOG_DIR" -name "*.log" -mtime +30 -delete
