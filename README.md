# exact-pinyin-mark

汉字转拼音，拼音标注，支持多音字标注

实现：利用爬虫从百度抓取所有汉字的词组，然后整理有效的词组在mysql数据库中。

# 使用方法
### 0 python安装requests,lxml,pymongo,execjs,selenium
### 1 安装mysql
### 2 配置setting
```bash
[LOG]
LEVEL = INFO //日志等级
LOG_PATH = ./FundCrawler/logs //日志目录

[MYSQL]
host = 127.0.0.1 //MYSQL服务器ip
PORT = 20137 //MYSQL服务器端口
USERNAME = username
PASSWORD = password
DATA_BASE_NAME = Fund
```
### 3 运行爬虫
```bash
# 会开始抓取百度下所有的词组和拼音以及常见的含义。
python CloverPinyinBuild.py
```
