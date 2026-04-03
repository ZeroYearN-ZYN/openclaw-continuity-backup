# SCI-hub 使用说明

## 🔍 下载流程

系统现在会依次尝试3种方法下载PDF：

```
1️⃣ Unpaywall（合法开放获取）
    ↓ 失败
2️⃣ PMC（PubMed Central免费全文）
    ↓ 失败
3️⃣ SCI-hub（备选方案）
    ↓
✅ 下载成功
```

## ⚙️ 配置选项

编辑 `scripts/download_pdfs_enhanced.py`：

```python
# 开启/关闭SCI-hub（默认开启）
USE_SCIHUB = True  # 改为 False 可禁用

# SCI-hub备用域名（自动切换）
scihub_urls = [
    "https://sci-hub.sg",  # 新加坡
    "https://sci-hub.se",  # 瑞典
    "https://sci-hub.st",  # 圣多美和普林西比
    "https://sci-hub.ru",  # 俄罗斯
]
```

## 📊 下载统计

下载报告会显示来源：

```
✅ 新下载: 25
   - Unpaywall: 5   (开放获取)
   - PMC: 3         (PubMed Central)
   - SCI-hub: 17    (SCI-hub)
```

## ⚠️ 注意事项

### 1. 网络延迟
- SCI-hub下载较慢（需要解析页面）
- 并发数已降低为2，避免触发限制
- 每个SCI-hub请求间隔2秒

### 2. 成功率
- Unpaywall: 约15-25%（开放获取）
- PMC: 约5-10%（PubMed Central）
- **SCI-hub: 约60-80%**（大部分付费文献）

### 3. 合法性
- Unpaywall: ✅ 完全合法
- PMC: ✅ 完全合法
- SCI-hub: ⚠️ 灰色地带，注意版权

## 🚀 使用方法

### 运行下载器
```bash
cd /Users/mini4-2/.openclaw/workspace/cho-papers
python3 scripts/download_pdfs_enhanced.py
```

### 查看下载报告
```bash
cat ~/Desktop/CHO-Literature-All/_下载报告.txt
```

### 查看来源统计
```bash
# 查看SCI-hub下载的数量
grep "SCI-hub" ~/Desktop/CHO-Literature-All/_下载报告.txt
```

## 🔧 故障排查

### SCI-hub全部失败？
```bash
# 检查网络连接
curl -I https://sci-hub.se

# 尝试手动访问
open https://sci-hub.se
```

### 下载速度慢？
正常现象！SCI-hub需要：
1. 访问页面
2. 解析HTML
3. 提取PDF链接
4. 下载PDF

每篇文献约需5-10秒。

### 想禁用SCI-hub？
编辑脚本：
```python
USE_SCIHUB = False
```

## 📈 预期效果

**首次运行（85篇文献）：**
```
✅ 新下载: 约50-60篇
   - Unpaywall: 5-10篇
   - PMC: 3-5篇
   - SCI-hub: 40-50篇

🔒 无访问: 5-10篇（无DOI或无法获取）
❌ 失败: 5-10篇（网络问题）
```

**日常运行（新增5篇）：**
```
✅ 新下载: 3-4篇
   - 大部分通过SCI-hub
```

## 💡 优化建议

1. **网络环境好** → 保持默认设置
2. **网络不稳定** → 降低 MAX_WORKERS 为 1
3. **追求速度** → 关闭SCI-hub（USE_SCIHUB = False）
4. **追求完整** → 开启SCI-hub，耐心等待

## 📞 常见问题

**Q: SCI-hub下载的PDF质量如何？**
A: 与官方PDF完全相同，都是出版社原版。

**Q: 会被封IP吗？**
A: 已设置延迟和低并发，风险较低。如遇问题，等待几小时再试。

**Q: 某些文献一直失败？**
A: 可能是：
- 无DOI
- SCI-hub未收录
- 网络问题

建议手动下载：访问 https://sci-hub.se/{DOI}

---

**🎉 享受完整文献获取！**

现在你的系统可以获取：
- ✅ 15-25% 开放获取文献
- ✅ 60-80% 付费文献（SCI-hub）
- ✅ 总覆盖率：75-90%
