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

