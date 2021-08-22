import os
import time
import random
import requests
import json
import execjs
from lxml import etree
from io import StringIO, BytesIO
from urllib.parse import unquote, quote
import pymysql
from Logger import logger
from Config import config
import jieba
from opencc import OpenCC
class PinyinDataBuild:
    homographWeightDict = dict()
    phrasePinyinDict = dict()

    def __init__(self, loadJieba=False):
        self.jieba_dict = None
        if loadJieba:
            self.jieba_dict = open('./data/jieba.dict', 'w', encoding='utf8')
            self.jiebaSet = set()
        self.loadSingleCharacterDict()
        self.loadLargePinyinDict()
        self.loadHomograph()
        self.loadSinglePinyinDict()
        if self.jieba_dict:
            for word in self.jiebaSet:
                self.jieba_dict.write(f"{word}\n")
                self.jieba_dict.flush()
            self.jieba_dict.close()
            jieba.load_userdict('./data/jieba.dict')

    def loadSinglePinyinDict(self):
        for data in open('data/pinyin.txt', 'r'):
            if '#' in data[0]:
                continue
            datas = data.strip().split(": ")[-1].split("  # ")
            pinyins = datas[0].split(",")
            word = datas[1]
            if word not in self.homographWeightDict:
                self.homographWeightDict[word] = dict()
            if "pinyins" not in self.homographWeightDict[word]:
                self.homographWeightDict[word]["pinyins"] = list()
            if "plainPinyins" not in self.homographWeightDict[word]:
                self.homographWeightDict[word]["plainPinyins"] = list()
            if "weight" not in self.homographWeightDict[word]:
                self.homographWeightDict[word]["weight"] = list()
            for pinyin in pinyins:
                plainPinyin = self.getPlainPinyin(pinyin)
                if plainPinyin not in self.homographWeightDict[word]["plainPinyins"]:
                    self.homographWeightDict[word]["plainPinyins"].append(plainPinyin)
                    self.homographWeightDict[word]["weight"].append("1")
                self.homographWeightDict[word]["pinyins"].append(pinyin)

    def loadLargePinyinDict(self):
        for data in open('data/large_pinyin.txt', 'r'):
            if '#' in data:
                continue
            datas = data.strip().split(": ")
            word = datas[0]
            pinyin = datas[1]
            plainPinyin = self.getPlainPinyin(pinyin)

            if word not in self.phrasePinyinDict:
                self.phrasePinyinDict[word] = dict()
            if "pinyins" not in self.phrasePinyinDict[word]:
                self.phrasePinyinDict[word]["pinyins"] = list()
            if "plainPinyins" not in self.phrasePinyinDict[word]:
                self.phrasePinyinDict[word]["plainPinyins"] = list()

            if pinyin not in self.phrasePinyinDict[word]["pinyins"]:
                self.phrasePinyinDict[word]["pinyins"].append(pinyin)
            if plainPinyin not in self.phrasePinyinDict[word]["plainPinyins"]:
                self.phrasePinyinDict[word]["plainPinyins"].append(plainPinyin)

            if self.jieba_dict:
                self.jiebaSet.add(word)

    def loadSingleCharacterDict(self):
        for data in open('data/single_character_info.txt', 'r'):
            datas = data.strip().replace('"', '').split("\t")
            if len(datas) >= 3:
                word = datas[1]
                pinyin = datas[0]
                plainPinyin = datas[2]

                if word not in self.phrasePinyinDict:
                    self.phrasePinyinDict[word] = dict()
                if "pinyins" not in self.phrasePinyinDict[word]:
                    self.phrasePinyinDict[word]["pinyins"] = list()
                if "plainPinyins" not in self.phrasePinyinDict[word]:
                    self.phrasePinyinDict[word]["plainPinyins"] = list()

                if pinyin not in self.phrasePinyinDict[word]["pinyins"]:
                    self.phrasePinyinDict[word]["pinyins"].append(pinyin)
                if plainPinyin not in self.phrasePinyinDict[word]["plainPinyins"]:
                    self.phrasePinyinDict[word]["plainPinyins"].append(plainPinyin)

                if self.jieba_dict:
                    self.jiebaSet.add(datas[1])

    def loadHomograph(self):
        f = open("./data/luna_pinyin.dict.yaml", "r", encoding='utf8')
        cc = OpenCC('t2s')
        for line in f.readlines():
            datas = line.strip().split('\t')
            if len(datas) == 1:
                continue
            word = datas[0]
            if len(word) > 1:
                word = cc.convert(word)
            pinyin = datas[1]
            if len(word) > 1:
                plainPinyin = self.getPlainPinyin(pinyin)

                if word not in self.phrasePinyinDict:
                    self.phrasePinyinDict[word] = dict()
                if "plainPinyins" not in self.phrasePinyinDict[word]:
                    self.phrasePinyinDict[word]["plainPinyins"] = list()

                if plainPinyin not in self.phrasePinyinDict[word]["plainPinyins"]:
                    self.phrasePinyinDict[word]["plainPinyins"].append(plainPinyin)

                if self.jieba_dict:
                    self.jiebaSet.add(word)
        for line in open("./data/clover.base.dict.yaml", "r", encoding='utf8'):
            if '\t' in line:
                datas = line.strip().split('\t')
                word = datas[0]
                pinyin = datas[1]
                weight = datas[2]
                if word not in self.homographWeightDict:
                    self.homographWeightDict[word] = dict()
                if "plainPinyins" not in self.homographWeightDict[word]:
                    self.homographWeightDict[word]["plainPinyins"] = list()
                self.homographWeightDict[word]["plainPinyins"].append(pinyin)
                if "weight" not in self.homographWeightDict[word]:
                    self.homographWeightDict[word]["weight"] = list()
                self.homographWeightDict[word]["weight"].append(weight)
        #word = "的"
        #print(self.homographWeightDict[word])

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

    def getConnection(self):
        host = config["MYSQL"]["HOST"]
        port = int(config["MYSQL"]["PORT"])
        db = config["MYSQL"]["DATA_BASE_NAME"]
        user = config["MYSQL"]["USERNAME"]
        password = config["MYSQL"]["PASSWORD"]
        conn = pymysql.connect(host=host, port=port, db=db, user=user, password=password)
        return conn

    def fixesPinyin(self):
        sql_str = "select * from single_character_info where pinyin not like '% %'"
        conn = self.getConnection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(sql_str)
        datas = cursor.fetchall()
        #logger.info(f'getCurrCharacterStoreIndex datas = {datas}')
        for data in datas:
            try:
                old_pinyin = data["pinyin"]
                word = data["word"]
                pinyin = self.markPinyin(data["pinyin"])
                plain_pinyin = self.markPinyin(data["pinyin"], plain=True)
                sql_str = f"update single_character_info set pinyin='{pinyin}', plainPinyin='{plain_pinyin}' where pinyin = '{old_pinyin}' and word = '{word}'"
                #print(sql_str)
                #cursor.execute(sql_str)
                #conn.commit()
            except Exception as e:
                print(e)

    def getPlainPinyin(self, pinyin):
        shengdiao = '''a ā á ǎ à
o ō ó ǒ ò
e ē é ě è
i ī í ǐ ì
u ū ú ǔ ù
ü ǖ ǘ ǚ ǜ'''
        shengdiaoToPlain = dict()
        for line in shengdiao.split("\n"):
            datas = line.split(' ')
            for curr in datas[1:]:
                shengdiaoToPlain[curr] = datas[0]
        plain_pinyin = ''
        for curr in pinyin:
            if curr not in shengdiaoToPlain:
                plain_pinyin += curr
            else:
                plain_pinyin += shengdiaoToPlain[curr]
        pinyin = plain_pinyin.replace('ü', 'v')
        return pinyin

    def markPinyin(self, pinyin, plain=False):
        splits = ['a', 'o', 'e', 'i', 'u', 'ü']
        shengdiao = '''a ā á ǎ à
o ō ó ǒ ò
e ē é ě è
i ī í ǐ ì
u ū ú ǔ ù
ü ǖ ǘ ǚ ǜ'''
        plainToShengdiao = dict()
        for line in shengdiao.split("\n"):
            datas = line.split(' ')
            plainToShengdiao[datas[0]] = datas[1:]
        shengdiaoToPlain = dict()
        for line in shengdiao.split("\n"):
            datas = line.split(' ')
            for curr in datas[1:]:
                shengdiaoToPlain[curr] = datas[0]
        yunmus = '''a、o、e、i、u、ü、ai、ei、ui、ao、ou、iu、ie、üe、er、an、en、in、ua、uo、un、ün、ang、eng、ing、ong'''.replace(' ', '').split('、')
        yunmus.extend('''iao iou uai uei ian uan üan iang uang ueng iong'''.split(' '))
        yunmus.reverse()
        if '·' in pinyin:
            pinyin = pinyin.replace("·", " ")
        elif pinyin == '':
            pass
        elif 'r' == pinyin[-1]:
            pinyin = pinyin[:-1] + " ér"
        else:
            shengdiaoYunmus = list()
            for currYunmu in yunmus:
                if len(currYunmu) >= 4:
                    letter = currYunmu[1]
                elif len(currYunmu) >= 3:
                    if "ng" in currYunmu:
                        letter = currYunmu[0]
                    else:
                        letter = currYunmu[1]
                elif len(currYunmu) >= 2:
                    if ("ü" == currYunmu[0] or "u" == currYunmu[0]) and "n" != currYunmu[-1]:
                        letter = currYunmu[1]
                    else:
                        letter = currYunmu[0]
                else:
                    letter = currYunmu[0]
                shengdiaoYunmus.append(currYunmu)
                for shengdiao in plainToShengdiao[letter]:
                    currShengdiaoYunmu = currYunmu.replace(letter, shengdiao)
                    shengdiaoYunmus.append(currShengdiaoYunmu)
            for shengdiaoYunmu in shengdiaoYunmus:
                pinyin = pinyin.replace(shengdiaoYunmu, " ")
            #print(pinyin)
        if plain:
            plain_pinyin = ''
            for curr in pinyin:
                if curr not in shengdiaoToPlain:
                    plain_pinyin += curr
                else:
                    plain_pinyin += shengdiaoToPlain[curr]
            pinyin = plain_pinyin.replace('ü', 'v')
        return pinyin

    def matchPinyin1(self, word, pinyins, homograph=False, plain=True):
        pinyinType = "plainPinyins"
        if not plain:
            pinyinType = "pinyins"
        if word in self.phrasePinyinDict:
            pinyinDatas = self.phrasePinyinDict[word][pinyinType]
            for i in range(len(pinyinDatas)):
                if word not in pinyins:
                    pinyins[word] = list()
                pinyins[word].append(pinyinDatas[i])
        else:
            for curr in word:
                if curr in self.homographWeightDict:
                    if curr not in pinyins:
                        pinyins[curr] = list()
                    if homograph:
                        pinyins[curr].append(self.homographWeightDict[curr][pinyinType])
                    else:
                        maxPinyinIndex = 0
                        maxWeight = 0
                        weights = self.homographWeightDict[curr]["weight"]
                        for i in range(len(weights)):
                            if maxWeight < float(weights[i]):
                                maxWeight = float(weights[i])
                                maxPinyinIndex = i
                        if curr not in pinyins:
                            pinyins[curr] = list()
                        pinyins[curr].append(self.homographWeightDict[curr][pinyinType][maxPinyinIndex])

    def matchPinyin(self, word, pinyins, homograph=False, plain=True):
        pinyinType = "plainPinyins"
        if not plain:
            pinyinType = "pinyins"
        if word in self.phrasePinyinDict:
            pinyinDatas = self.phrasePinyinDict[word][pinyinType]
            pinyins.append(pinyinDatas)
        else:
            for curr in word:
                if curr in self.homographWeightDict:
                    if homograph:
                        pinyins.append(self.homographWeightDict[curr][pinyinType])
                    else:
                        maxPinyinIndex = 0
                        maxWeight = 0
                        weights = self.homographWeightDict[curr]["weight"]
                        for i in range(len(weights)):
                            if maxWeight < float(weights[i]):
                                maxWeight = float(weights[i])
                                maxPinyinIndex = i
                        pinyins.append(self.homographWeightDict[curr][pinyinType][maxPinyinIndex])

    def getPinyin(self, sentence, homograph=False, plain=True):
        seg_list = jieba.cut(sentence) #默认是精确模式
        lines = ",".join(seg_list)
        #print(lines)
        pinyins = list()
        for word in lines.split(","):
            self.matchPinyin(word, pinyins, homograph, plain)
        return pinyins

if __name__ == "__main__":
    #PinyinDataBuild().fixesPinyin()
    sentence = "什么什么样的人就会做什么样的事"
    pinyin = PinyinDataBuild(loadJieba=False).getPinyin(sentence=sentence, homograph=True, plain=False)
    print(pinyin)
    lines = '''α射线
    α粒子
    β射线
    β粒子
    γ刀
    γ射线
    剞
    口音
    后生
    外面
    威廉退尔
    孩儿
    尾宿
    开山
    支派
    敷衍
    来往
    江湖
    泼洒
    的话
    苦头
    角宿
    觖望
    觜宿
    说法
    跰
    轸宿
    阿兰德隆
    隔断
    飘洒
    㑌儴
    䒷蒌
    䓮䕅
    䖮虫
    䰀鬌
    䵚黍
    '''
