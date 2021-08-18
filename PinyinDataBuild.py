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
        self.loadHomograph()
        self.loadLargePinyinDict()
        self.loadSingleCharacterDict()
        if self.jieba_dict:
            for word in self.jiebaSet:
                self.jieba_dict.write(f"{word}\n")
                self.jieba_dict.flush()
            self.jieba_dict.close()
            jieba.load_userdict('./data/jieba.dict')

    def loadLargePinyinDict(self):
        for data in open('data/large_pinyin.txt', 'r'):
            if '#' in data:
                continue
            datas = data.strip().split(": ")
            if datas[0] not in self.phrasePinyinDict:
                self.phrasePinyinDict[datas[0]] = list()
            currDict = {"pinyin": datas[1], "plainPinyin": self.getPlainPinyin(datas[1])}
            self.phrasePinyinDict[datas[0]].append(currDict)
            if self.jieba_dict:
                self.jiebaSet.add(datas[0])

    def loadSingleCharacterDict(self):
        for data in open('data/single_character_info.txt', 'r'):
            datas = data.strip().replace('"', '').split("\t")
            if len(datas) >= 3:
                if datas[1] not in self.phrasePinyinDict:
                    self.phrasePinyinDict[datas[1]] = list()
                currDict = {"pinyin": datas[0], "plainPinyin": datas[2]}
                self.phrasePinyinDict[datas[1]].append(currDict)
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
                if word not in self.phrasePinyinDict:
                    self.phrasePinyinDict[word] = list()
                currDict = {"pinyin": "", "plainPinyin": pinyin}
                self.phrasePinyinDict[word].append(currDict)
                if self.jieba_dict:
                    self.jiebaSet.add(word)

            if word not in self.homographWeightDict:
                self.homographWeightDict[word] = dict()
            if len(datas) == 3:
                weight = datas[2]
                self.homographWeightDict[word][pinyin] = weight
            else:
                self.homographWeightDict[word][pinyin] = '100%'

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
        pinyin = plain_pinyin
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
            pinyin = plain_pinyin
        return pinyin

    def matchPinyin(self, word, pinyins):
        if word in self.phrasePinyinDict:
            pinyinDatas = self.phrasePinyinDict[word][0]["plainPinyin"].split(" ")
            #print(pinyinDatas)
            for i in range(len(pinyinDatas)):
                if word not in pinyins:
                    pinyins[word] = list()
                pinyins[word].append(pinyinDatas[i])
        else:
            for curr in word:
                if curr in self.homographWeightDict:
                    pinyinDatas = self.homographWeightDict[curr].items()
                    maxPinyinData = None
                    for pinyinData in pinyinDatas:
                        if maxPinyinData is None:
                            maxPinyinData = pinyinData
                        elif '%' in pinyinData[1] and float(maxPinyinData[1][:-1]) < float(pinyinData[1][:-1]):
                            maxPinyinData = pinyinData
                    if word not in pinyins:
                        pinyins[word] = list()
                    pinyins[word].append(maxPinyinData[0])

    def getPinyin(self, sentence, heterograph=False):
        seg_list = jieba.cut_for_search(sentence) #默认是精确模式
        lines = ",".join(seg_list)
        pinyins = dict()
        for word in lines.split(","):
            self.matchPinyin(word, pinyins)
        words = list()
        pinyinList = list()
        for word in pinyins:
            if len(word) != len(pinyins[word]):
                curr_pinyins = dict()
                for w in word:
                    self.matchPinyin(w, curr_pinyins)
                words.extend(curr_pinyins.keys())
                for wPinyin in curr_pinyins.values():
                    pinyinList.extend(wPinyin)
            else:
                words.extend(word)
                pinyinList.extend(pinyins[word])
        i = 0
        j = 0
        finalPinyins = list()
        while i < len(sentence) and j < len(words) and len(pinyinList) > 0:
            if sentence[i] == words[j]:
                i += 1
                finalPinyins.append(pinyinList[j])
            j += 1
        return finalPinyins

if __name__ == "__main__":
    #PinyinDataBuild().fixesPinyin()
    PinyinDataBuild().getPinyin(sentence="弹出")
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
