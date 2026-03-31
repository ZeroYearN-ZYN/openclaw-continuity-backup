# MEMORY.md - 长期记忆

## 用户背景

- **姓名**: kk
- **时区**: Asia/Shanghai (UTC+8)
- **研究方向**: CHO 细胞、抗体生产、重组蛋白表达

## CHO 细胞文献整理系统

### 目录结构
- `~/Desktop/CHO-Literature-All/` — 下载的 PDF 文献
- `~/Desktop/CHO-Literature-Reports/` — 每日报告 + JSON 数据
- `~/Desktop/CHO-Literature/` — 工作目录

### 文献检索关键词
1. CHO cell culture production
2. Chinese hamster ovary recombinant
3. CHO cells protein expression

### 相关工具
- `~/Desktop/cho_codon_optimizer.py` — 基础版
- `~/Desktop/cho_codon_optimizer_advanced.py` — 高级版
- `~/Desktop/cho_codon_optimizer_gui.py` — GUI 版

### 研究关注点
- CHO 细胞培养
- 抗体生产
- 重组蛋白表达
- 糖基化
- 过程优化
- 基因表达

### 定时任务
- **CHO 文献每日整理**: 每天 08:00 (Asia/Shanghai)
  - 脚本：`~/.openclaw/workspace/cho-papers/scripts/run_daily.sh`
  - 流程：PubMed 抓取 → PDF 下载 → 生成下载页面 → 生成每日报告
  - Cron ID: `c06105e1-dda1-4794-aa5f-64c10d634239`
  - 输出：`~/Desktop/CHO-Literature-Reports/YYYY-MM-DD/`
  - 模型：`custom-v2-aicodee-com/MiniMax-M2.5-highspeed` (2026-03-24 切换，修复 qwen-portal token 过期问题)
  - 状态：✅ 已修复

- **CHO 文献每日摘要**: 每天 10:00 (Asia/Shanghai)
  - 流程：读取新 PDF → 提取文本 → AI 生成通俗易懂摘要 → 保存到桌面 → 通知用户
  - Cron ID: `24253446-4444-44a4-b407-5eda287b813b`
  - 脚本：`~/.openclaw/workspace/cho-papers/scripts/daily_summary.py`
  - 输出：`~/Desktop/CHO-Literature-Reports/YYYY-MM-DD/每日摘要_YYYY-MM-DD.md`
  - 模型：`custom-v2-aicodee-com/MiniMax-M2.5-highspeed` (2026-03-24 切换，修复 qwen-portal token 过期问题)
  - 状态：✅ 已修复

- **CHO 文献分批下载**: 每天 14:00 (Asia/Shanghai)
  - 脚本：`~/.openclaw/workspace/cho-papers/scripts/run_batch_download.sh`
  - Cron ID: `69eb36cf-86a0-4769-bc44-6a3960fde49e`
  - 模型：`custom-v2-aicodee-com/MiniMax-M2.5-highspeed` (2026-03-24 切换，修复 qwen-portal token 过期问题)
  - 状态：✅ 已修复

---

## 系统配置

### Channels
- **飞书**: 已配置，App ID: `cli_a9f6dabc26b85cc6`
- **Webchat**: 默认

### Skills 已安装
- 飞书系列：feishu-doc, feishu-drive, feishu-perm, feishu-wiki
- 工具：github, gh-issues, 1password, healthcheck, himalaya, weather
- 其他：skill-creator, skill-vetter, agent-browser, find-skills, obsidian, gemini, gifgrep, bear-notes, vercel-react-best-practices

---

## 连续性备份系统

**状态**: ✅ 已激活

**仓库**: https://github.com/ZeroYearN-ZYN/openclaw-continuity (私有)

**自动备份**: 每天 00:00 (Asia/Shanghai)

**已备份内容**:
- 核心身份：MEMORY.md, USER.md, SOUL.md, IDENTITY.md, TOOLS.md, AGENTS.md
- CHO 文献系统：cho-papers/
- 自定义工具：cho_codon_optimizer*.py

**恢复**: `git clone git@github.com:ZeroYearN-ZYN/openclaw-continuity.git ~/.openclaw/workspace/`

**Cron ID**: `b7fee1df-d8ec-4e53-801f-706c02ac98e1`

---

## API 配置变更 (2026-03-22) ✅ 已解决

**问题**: 原 API 提供商出现故障
- xiaomi/mimo-v2-flash: 💰 余额不足
- zai/glm-5: ⚠️ 速率限制
- minimax-portal/MiniMax-M2.1: 🔑 认证失败
- minimax/MiniMax-M2.1: 🔑 HTTP 401 无效密钥

**解决方案**: 所有 CHO 文献任务切换至 `qwen-portal/coder-model`

**飞书渠道修复**: 已配置 delivery.to = `ou_ffdf1ad958894f78b7d2c0e52b75a1ec`

**状态更新时间**: 2026-03-22 13:36:00 GMT+8

---

## 抗体分子量验证项目 (2026-03-14)

**任务**: 验证并补充 50 个 Top 抗体药的理化性质数据

**输出文件** (桌面):
- `Antibody_Top50_Biosimilar_Final.csv` - 最终整理数据
- `Antibody_Top50_Biosimilar_Verified.csv` - 验证后数据
- `Antibody_MW_Comparison.csv` - 分子量对比
- `antibody_mw_calculator.py` - 分子量计算工具

**数据覆盖**:
- 分子量 (MW): 47/50 有精确值
- 等电点 (pI): 23 个有文献值，其余为估算
- 消光系数 (ε280): 大部分有估算值
- 亚型：全部 50 个

**特殊发现**:
- Certolizumab: Fab'片段 (47.75 kDa)，非全长 IgG
- Blinatumomab: BiTE®双抗 (55 kDa)，非 IgG 结构
- Ranibizumab: Fab 片段 (48 kDa)，眼科用药

**数据来源**: DrugBank, FDA/EMA 审评报告，PubMed (Goyon et al. 2017 等)

---

*最后更新：2026-03-22*
