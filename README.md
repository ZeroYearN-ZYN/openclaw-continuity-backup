# CHO细胞文献自动抓取系统 - 使用指南

## ✅ 系统特点

### 🎯 核心功能
- ✅ **自动去重** - 不会重复抓取相同文献
- ✅ **统一目录** - 所有PDF保存在一个文件夹
- ✅ **历史记录** - 记录已处理的PMID和已下载的PDF
- ✅ **增量更新** - 每次只处理新文献

### 📂 文件结构

```
~/Desktop/CHO-Literature-All/          ← 🔥 统一PDF目录
├── 文献1.pdf
├── 文献2.pdf
├── 文献3.pdf
├── ...
└── _最新下载报告.txt

~/.openclaw/workspace/cho-papers/
├── data/                              ← 历史记录
│   ├── pmid_history.json             ← 已抓取的PMID
│   └── download_history.json         ← 已下载的PDF
├── output/                            ← 文献数据
│   ├── pubmed_cho_cells_latest.json  ← 最新数据（累积）
│   └── pubmed_cho_cells_20260310.json ← 历史备份
└── logs/                              ← 运行日志
    └── fetch_20260310.log
```

---

## 🚀 快速开始

### 手动运行
```bash
# 一键运行（抓取 + 下载）
bash /Users/mini4-2/.openclaw/workspace/cho-papers/scripts/run_daily.sh

# 或者分步运行
cd /Users/mini4-2/.openclaw/workspace/cho-papers
python3 scripts/pubmed_fetch.py              # 抓取文献
python3 scripts/download_pdfs_enhanced.py    # 下载PDF
```

### 自动运行
- ⏰ **时间**: 每天早上 8:00
- 📍 **位置**: `~/Desktop/CHO-Literature-All/`
- 🔁 **去重**: 自动跳过已处理的文献

---

## 📊 查看结果

### 查看PDF
```bash
# 打开文件夹
open ~/Desktop/CHO-Literature-All/

# 统计数量
ls -1 ~/Desktop/CHO-Literature-All/*.pdf | wc -l

# 查看最新报告
cat ~/Desktop/CHO-Literature-All/_最新下载报告.txt
```

### 查看数据
```bash
# 查看累积的文献数据
cat ~/.openclaw/workspace/cho-papers/output/pubmed_cho_cells_latest.json | jq '.total_count'

# 查看历史记录
cat ~/.openclaw/workspace/cho-papers/data/pmid_history.json | jq 'length'
```

### 查看日志
```bash
# 最新日志
tail -20 ~/.openclaw/workspace/cho-papers/logs/fetch_$(date +%Y%m%d).log

# 所有日志
ls -lht ~/.openclaw/workspace/cho-papers/logs/
```

---

## 🔧 配置修改

### 修改搜索关键词
编辑 `scripts/pubmed_fetch.py`:
```python
SEARCH_TERMS = [
    "CHO cells protein expression",
    "Chinese hamster ovary recombinant",
    # 添加新关键词...
]
```

### 修改抓取时间范围
```python
DAYS_BACK = 30  # 默认30天
```

### 重置历史记录
```bash
# ⚠️ 谨慎使用！会重新抓取所有文献
rm ~/.openclaw/workspace/cho-papers/data/pmid_history.json
rm ~/.openclaw/workspace/cho-papers/data/download_history.json
```

---

## 📈 数据流程

```
PubMed API
    ↓
搜索关键词 (最近30天)
    ↓
获取PMID列表
    ↓
🔍 去重检查（pmid_history.json）
    ↓
只保留新PMID
    ↓
获取文献详情
    ↓
保存到 JSON（累积）
    ↓
更新历史记录
    ↓
尝试下载PDF
    ↓
🔍 去重检查（download_history.json）
    ↓
只下载新PDF
    ↓
保存到统一目录
```

---

## 💡 使用技巧

### 1. 首次运行
```bash
# 第一次运行会抓取最近30天的所有文献
bash /Users/mini4-2/.openclaw/workspace/cho-papers/scripts/run_daily.sh

# 预期：
# - 抓取约 50-100 篇文献
# - 下载约 10-20 个PDF（开放获取）
```

### 2. 日常使用
- **每天8:00** 自动运行
- **增量更新** 只处理新发表的文献
- **桌面查看** `CHO-Literature-All/` 文件夹

### 3. 批量管理
```bash
# 查看所有PDF
find ~/Desktop/CHO-Literature-All/ -name "*.pdf" -exec ls -lh {} \;

# 按大小排序
ls -lhS ~/Desktop/CHO-Literature-All/*.pdf | head -10

# 搜索特定文献
grep -l "关键词" ~/Desktop/CHO-Literature-All/*.pdf
```

---

## 🎯 高级功能

### 导出到Excel
```bash
# 安装工具
pip3 install pandas openpyxl

# 创建导出脚本
cat > /tmp/export.py << 'EOF'
import json, pandas as pd
from pathlib import Path

data_dir = Path("~/.openclaw/workspace/cho-papers/output").expanduser()
all_papers = []

for f in data_dir.glob("pubmed_*_latest.json"):
    with open(f) as fp:
        data = json.load(fp)
        all_papers.extend(data.get("papers", []))

# 去重
df = pd.DataFrame(all_papers).drop_duplicates(subset=['pmid'])
df.to_excel("~/Desktop/CHO文献列表.xlsx", index=False)
print(f"✅ 导出 {len(df)} 篇文献")
EOF

python3 /tmp/export.py
```

### 云同步
```bash
# 使用iCloud同步
ln -s ~/Desktop/CHO-Literature-All ~/Library/Mobile\ Documents/com~apple~CloudDocs/

# 使用Dropbox同步
ln -s ~/Desktop/CHO-Literature-All ~/Dropbox/CHO-Literature
```

---

## ❓ 常见问题

### Q: 如何确认去重正常工作？
A: 查看历史记录：
```bash
cat ~/.openclaw/workspace/cho-papers/data/pmid_history.json | jq 'length'
```
数字应该逐渐增加，不会重复。

### Q: PDF下载比例为什么这么低？
A: 正常现象！
- PubMed文献约 15-25% 是开放获取
- 其余需要机构订阅或付费
- 可通过DOI链接手动下载

### Q: 如何重新下载失败的PDF？
A: 简单！重新运行即可：
```bash
python3 scripts/download_pdfs_enhanced.py
```
系统会自动跳过已下载的。

### Q: 可以抓取其他主题吗？
A: 可以！修改 `SEARCH_TERMS`:
```python
SEARCH_TERMS = [
    "CRISPR gene editing",
    "machine learning drug discovery",
    "任何PubMed关键词",
]
```

### Q: 如何暂停自动运行？
A: 编辑cron任务：
```bash
crontab -e
# 注释掉这一行（添加 #）：
# # 0 8 * * * /bin/bash ...
```

---

## 📞 技术细节

### 去重机制
1. **PMID去重**: `pmid_history.json` 记录所有已抓取的PMID
2. **PDF去重**: `download_history.json` 记录已下载的PMID
3. **文件去重**: 检查PDF文件是否存在

### API限制
- **PubMed**: 10次/秒（有API密钥）
- **Unpaywall**: 无限制
- **PMC**: 无明确限制

### 存储空间
- **JSON数据**: 约 1MB/100篇
- **PDF**: 平均 3-5MB/篇
- **建议**: 定期清理旧PDF（保留6个月）

---

## 🎉 享受自动化！

- ✅ **去重**: 永不重复抓取
- ✅ **统一**: 所有PDF在一处
- ✅ **自动**: 每天8:00准时运行
- ✅ **可靠**: 完整日志可追溯

**明天开始，你的桌面会自动积累最新的CHO细胞文献！** 📚🔬
