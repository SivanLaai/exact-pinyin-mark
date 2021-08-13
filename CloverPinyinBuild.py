import os
import requests
import json
import execjs
from lxml import etree
from io import StringIO, BytesIO
from urllib.parse import unquote, quote
import pymysql
from Logger import logger

header_str = '''Host:hanyu.baidu.com
Connection:keep-alive
sec-ch-ua:"Chromium";v="92", " Not A;Brand";v="99", "Microsoft Edge";v="92"
Accept:application/json, text/javascript, */*; q=0.01
X-Requested-With:XMLHttpRequest
sec-ch-ua-mobile:?0
User-Agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36 Edg/92.0.902.67
Sec-Fetch-Site:same-origin
Sec-Fetch-Mode:cors
Sec-Fetch-Dest:empty
Referer:https://hanyu.baidu.com/s?wd=%E5%8F%B7%E8%AF%8D%E7%BB%84&from=poem
Accept-Encoding:gzip, deflate, br
Accept-Language:zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7
Cookie:BIDUPSID=C54EE66A9D960662A585B0E735EC5EF2; PSTM=1613205183; BAIDUID=F7EFA36CAC4D356A6DA065FAD318BBAE:FG=1; __yjs_duid=1_d1f6f1201d78b30171d64739b6120f431619257583974; BDSFRCVID_BFESS=e-0OJexroG0YyvRH3CTRKw3v2FweG7bTDYLEOwXPsp3LGJLVJeC6EG0Pts1-dEu-EHtdogKK0mOTHvCF_2uxOjjg8UtVJeC6EG0Ptf8g0M5; H_BDCLCKID_SF_BFESS=tR3aQ5rtKRTffjrnhPF3bDrQXP6-hnjy3bRkX4Q4WIOTSMoo5Tb-DxKWbttf5q3RymJ42-39LPO2hpRjyxv4y4Ldj4oxJpOJ-bCL0p5aHl51fbbvbURvD-ug3-7q3M5dtjTO2bc_5KnlfMQ_bf--QfbQ0hOhqP-jBRIE3-oJqC-WhU5; BDORZ=B490B5EBF6F3CD402E515D22BCDA1598; ab_sr=1.0.1_NzAzZjI0NzFmYjE4OTYxNGJmZWNjNzM0ZTIzYmNlNGJkODZkZjZmMjM1YjYzN2JmYTM0ZjhmZGI1YmI0ZjhmY2E2NTc2OGIyNGM1ZjQ2YmI1MTdkZjE1MWFkM2M3Y2FlNWZhZWVlMjgzN2NjMmU3YTY5NjQ0ZTNjNjBjMWE4M2MwNDkwMmRlYTQ4NzcxMjQzNDVlNGMxMjMzNjNmMDM0NA==; delPer=0; PSINO=3; BAIDUID_BFESS=F7EFA36CAC4D356A6DA065FAD318BBAE:FG=1; H_PS_PSSID=34369_31253_34403_33848_34073_34092_34111_26350_34419_34323_34390_34360; BA_HECTOR=8g0k200h8hak8h0l661ghbqbv0r; Hm_lvt_010e9ef9290225e88b64ebf20166c8c4=1628826303; Hm_lpvt_010e9ef9290225e88b64ebf20166c8c4=1628826586'''


params_str = '''wd=%E5%8F%B7%E8%AF%8D%E7%BB%84
from=poem
pn=1
_=1628826451938'''

class CloverPinyinBuild:
    homographWeightDict = dict()
    def __init__(self):
        self.conn = self.getConnection()
        wordSet = set()
        f = open("./data/luna_pinyin.dict.yaml", "r", encoding='utf8')
        for line in f.readlines():
            datas = line.strip().split('\t')
            if len(datas) == 3:
                word = datas[0]
                pinyin = datas[1]
                weight = datas[2]
                if word not in self.homographWeightDict:
                    self.homographWeightDict[word] = dict()
                if pinyin  not in self.homographWeightDict[word]:
                    self.homographWeightDict[word][pinyin] = dict()
                self.homographWeightDict[word][pinyin] = weight
    def getHomograph(self, word="不"):
        return self.homographWeightDict.get(word, dict())

    # 把所有的多音字进行识别
    def splitHomograph(self, path='./Clover四叶草拼音', newPath='./Clover四叶草拼音new'):
        if not os.path.exists(newPath):
            os.mkdir(f'{newPath}')

        for file_now in os.listdir(path):
            new_file_path = os.path.join(newPath, file_now)
            curr_path = os.path.join(path, file_now)
            new_file = open(new_file_path, 'w', encoding="utf-8")
            if 'base' not in curr_path:
                continue
            for line in open(curr_path, encoding='utf-8'):
                if "\t" in line:
                    keyword = line.split('\t')[0]
                    pinyin_old = line.split('\t')[1].strip()
                    count_str = line.split('\t')[-1].strip().replace(" ", '')
                    pinyinDict = self.getHomograph(keyword)
                    if len(pinyinDict) == 0:
                        new_file.write(line)
                        new_file.flush()
                    else:
                        currPinyins = sorted(pinyinDict.items(), key=lambda x: x[1], reverse=True)
                        for currPinyin in currPinyins:
                            try:
                                newLine = line.replace(pinyin_old, currPinyin[0]).replace(count_str, currPinyin[1])
                                new_file.write(newLine)
                                new_file.flush()
                            except Exception as e:
                                print(e)
                else:
                    new_file.write(line)
                    new_file.flush()
            new_file.close()

    def format_header(self, header_str=header_str):
        header = dict()
        for line in header_str.split('\n'):
            header[line.split(':')[0]] = ":".join(line.split(':')[1:])
        return header

    def format_params(self, params_str=params_str):
        params = dict()
        for line in params_str.split('\n'):
            params[line.split('=')[0]] = line.split('=')[1]
        return params

    def getPlainPinyin(self, sug_py):
        splits = ['a', 'o', 'e', 'i', 'u', 'ü']
        shengdiao = '''a ā á ǎ à 
o ō ó ǒ ò
e ē é ě è
i ī í ǐ ì
u ū ú ǔ ù
ü ǖ ǘ ǚ ǜ'''
        shengdiaoToWord = dict()
        for line in shengdiao.split("\n"):
            datas = line.split(' ')
            for curr in datas[1:]:
                shengdiaoToWord[curr] = datas[0]
        plain_pinyin = ''
        for curr in sug_py:
            if curr not in shengdiaoToWord:
                plain_pinyin += curr
            else:
                plain_pinyin += shengdiaoToWord[curr]
        return plain_pinyin

    def parserDatas(self, word, datas):
        res_list = list()
        for currWordData in datas:
            currMeanList = currWordData["mean_list"]
            try:
                word = currWordData["name"][0]
                for currMean in currMeanList:
                    pinyin = currMean["pinyin"]
                    if len(pinyin) > 0:
                        pinyin = pinyin[0]
                    definition = currMean["definition"]
                    if len(definition) > 0:
                        definition = '\n'.join(definition)
                    plain_pinyin = currMean["sug_py"]
                    if len(plain_pinyin) > 0:
                        plain_pinyin = self.getPlainPinyin(pinyin)
                    pindu = currMean["pindu"]
                    if len(pindu) > 0:
                        pindu = pindu[0]
                    pronunciation = currMean["tone_py"]
                    if len(pronunciation) > 0:
                        pronunciation = pronunciation[0]
                    sql_str = f"insert into single_character_info values ('{pinyin}', '{word}', \
                    '{plain_pinyin}', '{definition}', '{pindu}', '{pronunciation}')"
                    cursor = self.conn.cursor(pymysql.cursors.DictCursor)
                    cursor.execute(sql_str)
                    self.conn.commit()
            except Exception as e:
                logger.error(f"word: {word}, pinyin: {pinyin}, error_info: {e}")

    def getConnection(self):
        host = '39.98.80.136'
        port = 3306
        db = 'character'
        user = 'job'
        password = 'laiyanhua'
        conn = pymysql.connect(host=host, port=port, db=db, user=user, password=password)
        return conn

    def crawlerExactPhrasePinyin(self, word="号"):
        headers = self.format_header()
        params = self.format_params()
        params["pn"] = 1
        url = "https://hanyu.baidu.com/hanyu/ajax/search_list"
        params['wd'] = word + "词组"
        response = requests.get(url, params=params, headers=headers)
        datas = json.loads(response.text).get('ret_array', list())
        while len(datas) > 1:
            self.parserDatas(word, datas)
            params["pn"] += 1
            response = requests.get(url, params=params, headers=headers)
            datas = json.loads(response.text).get('ret_array', list())
            #self.parserDatas(word, datas)

    def crawlerPhraseDict(self):
        file_path = './data/clover.base.dict.yaml'
        file = open(file_path, 'r', encoding="utf-8")
        for line in file.readlines():
            word = line.split('\t')[0]
            self.crawlerExactPhrasePinyin(word)
if __name__ == "__main__":
    CloverPinyinBuild().crawlerExactPhrasePinyin()
    #CloverPinyinBuild().getPlainPinyin("guà hào")
