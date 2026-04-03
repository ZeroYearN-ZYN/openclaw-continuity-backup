# 🚀 快速开始指南

## ✅ 已完成
1. ✓ 创建了项目目录结构
2. ✓ 安装了Python依赖（requests, biopython）
3. ✓ 设置了每日自动运行的Cron任务（每天8:00）
4. ✓ 创建了3个脚本：
   - `pubmed_fetch.py` - PubMed文献抓取
   - `semantic_scholar_fetch.py` - Semantic Scholar抓取
   - `download_pdfs.py` - PDF下载器（可选）

## ⚠️ 需要你完成的配置

### 1. 配置邮箱（必需）

编辑文件：
```bash
nano /Users/mini4-2/.openclaw/workspace/cho-papers/scripts/pubmed_fetch.py
```

找到第12行，改成你的邮箱：
```python
NCBI_EMAIL = "your_email@example.com"  # ← 改成你的真实邮箱
```

### 2. 获取NCBI API密钥（推荐，免费）

**为什么需要？**
- 无密钥：3次请求/秒
- 有密钥：10次请求/秒（更稳定快速）

**如何获取：**
1. 访问 https://www.ncbi.nlm.nih.gov/account/
2. 注册/登录账号
3. 点击右上角头像 → Settings
4. 找到 "API Key Management" → "Create an API Key"
5. 复制生成的密钥

**配置密钥：**
继续编辑 `pubmed_fetch.py`，在第13行填入：
```python
NCBI_API_KEY = "你的密钥粘贴在这里"
```

### 3. 测试运行

```bash
cd /Users/mini4-2/.openclaw/workspace/cho-papers
python3 scripts/pubmed_fetch.py
```

成功后会在 `output/` 目录看到JSON文件。

## 📂 项目结构

```
cho-papers/
├── output/              # 抓取结果保存位置
│   ├── pubmed_*.json   # PubMed数据
│   ├── semantic_*.json # Semantic Scholar数据
│   └── pdfs/           # 下载的PDF（可选）
├── scripts/
│   ├── pubmed_fetch.py
│   ├── semantic_scholar_fetch.py
│   ├── download_pdfs.py
│   └── run_daily.sh
├── logs/               # 自动生成的运行日志
└── README.md
```

## ⏰ 自动运行

Cron任务已设置：
- **时间**：每天早上8:00
- **任务**：运行PubMed + Semantic Scholar抓取

查看任务：
```bash
crontab -l
```

查看日志：
```bash
ls -lht /Users/mini4-2/.openclaw/workspace/cho-papers/logs/
```

## 🔧 自定义搜索关键词

编辑脚本中的 `SEARCH_TERMS`：

```python
SEARCH_TERMS = [
    "CHO cells protein expression",
    "Chinese hamster ovary recombinant",
    "CHO cell culture production",
    # 添加你感兴趣的关键词...
]
```

## 💡 使用建议

1. **首次运行**：配置好邮箱后，手动运行一次测试
2. **查看结果**：`output/` 目录下的JSON文件
3. **PDF下载**：取消 `run_daily.sh` 中的注释以启用
4. **调整频率**：修改cron表达式（现在是每天8:00）

## ❓ 常见问题

**Q: Semantic Scholar报错429？**
A: API临时限制，等几分钟后再试，或主要使用PubMed

**Q: 找不到文献？**
A: 确认邮箱已设置，尝试注册NCBI API密钥

**Q: PDF下载失败？**
A: 正常现象，多数文献需要订阅。可以用DOI链接手动下载

## 📞 下一步

1. 现在就去配置邮箱！
2. （可选）注册NCBI API密钥
3. 手动测试一次
4. 明天8:00会自动运行

---
需要帮助随时问我！
