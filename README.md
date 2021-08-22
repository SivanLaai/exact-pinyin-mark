精准拼音转换（Python 版）
=============================

将汉字转为拼音。

基于 `luna_pinyin\pypinyin\clover-pinyin` 数据。（共提供50W左右拼音数据）

基于 [百度汉语数据](https://hanyu.baidu.com/)(共抓取35W词组拼音数据) 。

基于 jieba分词工具。

特性
----

* 从百度汉语字典中抓取汉字的最新拼音数据。
* 根据词组智能匹配最正确的拼音。
* 简单使用。


安装
----

```python
$ git clone https://github.com/SivanLaai/exact-pinyin-mark.git
$ cd exact-pinyin-mark
$ pip install -r requirements.txt
```


使用示例
--------

Python 3(Python 2 下把 ``'中心'`` 替换为 ``u'中心'`` 即可):

```python
>>> from PinyinDataBuild import PinyinDataBuild
>>> pdb = PinyinDataBuild(loadJieba=False)
>>> pdb.getPinyin('从百度汉语字典中抓取汉字的最新拼音数据。')
['cong', 'bai', 'du', 'han', 'yu', 'zi', 'dian', 'zhong', 'zhua', 'qu', 'han', 'zi', 'de', 'zui', 'xin', 'pin', 'yin', 'shu', 'ju']
```

拼音数据
---------

* 单个汉字的拼音使用 `luna-pinyin`_ 的数据
* 词组的拼音使用 `phrase-pinyin-data`_ 的数据
* 词组的拼音使用 `baidu-hanyu-pinyin`_ 的数据

# 百度汉语字典爬虫

利用爬虫从百度抓取所有汉字的词组，然后整理有效的词组在mysql数据库中。

## 使用方法

安装

```bash
$ git clone https://github.com/SivanLaai/exact-pinyin-mark.git
$ cd exact-pinyin-mark
$ pip install -r requirements.txt
```

安装mysql

创建表格
```sql
CREATE TABLE `single_character` (
  `pinyin` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `word` varchar(255) NOT NULL,
  `plainPinyin` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `definition` varchar(4096) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `pronunciation` varchar(255) DEFAULT NULL,
  `wordID` int DEFAULT NULL,
  PRIMARY KEY (`word`,`pinyin`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```

配置setting

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
运行爬虫
```bash
# 会开始抓取百度下所有的词组和拼音以及常见的含义。
python PinyinDataCrawler.py
```

#### 注意事项

- 因为数据量过大，爬虫的抓取时间可能需要1到2天，需要保证程序的正常运行。
- 先配置好mysql。
# BaiduHanyuCrawler
