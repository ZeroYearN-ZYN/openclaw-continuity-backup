#!/bin/bash
# CHO文献分批下载脚本
# 连续模式：完成10篇后等待1分钟继续

cd /Users/mini4-2/.openclaw/workspace/cho-papers/scripts
python3 batch_download.py --continuous 2>&1 | tee -a /tmp/cho-download.log
