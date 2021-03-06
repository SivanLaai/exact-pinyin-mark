import os
import jieba
from PinyinConfig import pinyin_config
from opencc import OpenCC
import PinyinStyle

root_dir = pinyin_config["PROGRAM"]["ROOT"]

class PinyinDataBuild:
    homographWeightDict = dict()
    phrasePinyinDict = dict()

    def __init__(self, loadJieba=False):
        self.jieba_dict = None
        if loadJieba:
            self.jieba_dict = open(root_dir + '/data/jieba.dict', 'w', encoding='utf8')
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
            jieba.load_userdict(root_dir + '/data/jieba.dict')

    def loadSinglePinyinDict(self):
        for data in open(root_dir + '/data/pinyin.txt', 'r', encoding='utf8'):
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
        for data in open(root_dir + '/data/large_pinyin.txt', 'r', encoding="utf8"):
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
        for data in open(root_dir + '/data/single_character_info.txt', 'r', encoding="utf-8"):
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
        f = open(root_dir + "/data/luna_pinyin.dict.yaml", "r", encoding='utf8')
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
        for line in open(root_dir + "/data/clover.base.dict.yaml", "r", encoding='utf8'):
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


    def getPlainPinyin(self, pinyin):
        shengdiao = '''a ?? ?? ?? ??
o ?? ?? ?? ??
e ?? ?? ?? ??
i ?? ?? ?? ??
u ?? ?? ?? ??
?? ?? ?? ?? ??'''
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
        pinyin = plain_pinyin.replace('??', 'v')
        return pinyin

    def markPinyin(self, pinyin, plain=False):
        splits = ['a', 'o', 'e', 'i', 'u', '??']
        shengdiao = '''a ?? ?? ?? ??
o ?? ?? ?? ??
e ?? ?? ?? ??
i ?? ?? ?? ??
u ?? ?? ?? ??
?? ?? ?? ?? ??'''
        plainToShengdiao = dict()
        for line in shengdiao.split("\n"):
            datas = line.split(' ')
            plainToShengdiao[datas[0]] = datas[1:]
        shengdiaoToPlain = dict()
        for line in shengdiao.split("\n"):
            datas = line.split(' ')
            for curr in datas[1:]:
                shengdiaoToPlain[curr] = datas[0]
        yunmus = '''a???o???e???i???u????????ai???ei???ui???ao???ou???iu???ie?????e???er???an???en???in???ua???uo???un?????n???ang???eng???ing???ong'''.replace(' ', '').split('???')
        yunmus.extend('''iao iou uai uei ian uan ??an iang uang ueng iong'''.split(' '))
        yunmus.reverse()
        if '??' in pinyin:
            pinyin = pinyin.replace("??", " ")
        elif pinyin == '':
            pass
        elif 'r' == pinyin[-1]:
            pinyin = pinyin[:-1] + " ??r"
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
                    if ("??" == currYunmu[0] or "u" == currYunmu[0]) and "n" != currYunmu[-1]:
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
            pinyin = plain_pinyin.replace('??', 'v')
        return pinyin

    '''
        parameters:
        word - ??????????????????????????????
        pinyins - ??????????????????
        homograph=False - ?????????
        phraseHomograph - ???????????????
        plain - ??????????????????
    '''
    def matchPinyin1(self, word, pinyins, homograph=False, phraseHomograph=True, plain=True):
        pinyinType = "plainPinyins"
        if not plain:
            pinyinType = "pinyins"
        if word in self.phrasePinyinDict:
            pinyinDatas = self.phrasePinyinDict[word][pinyinType]
            if phraseHomograph:
                pinyins.append(pinyinDatas)
            else:
                pinyins.append([pinyinDatas[0]])
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
                        pinyins.append([self.homographWeightDict[curr][pinyinType][maxPinyinIndex]])

    '''
        parameters:
        word - ??????????????????????????????
        pinyins - ??????????????????
        pinyinStyle - ??????????????????
    '''
    def matchPinyin(self, word, pinyins, pinyinStyle=PinyinStyle.PLAIN_NOTPOLYPHONE_WITH_PHRASE):
        pinyinType = "plainPinyins"
        if pinyinStyle > 3:
            pinyinType = "pinyins"
        if word in self.phrasePinyinDict:
            pinyinDatas = list()
            if pinyinType in self.phrasePinyinDict[word]:
                pinyinDatas = self.phrasePinyinDict[word][pinyinType]
            if len(pinyinDatas) == 0:
                pinyins.append(pinyinDatas)
                return
            #print(self.phrasePinyinDict[word])
            #if phraseHomograph:
            if pinyinStyle in [0, 1, 4, 5, 8, 9]:
                pinyins.append(pinyinDatas)
            else:
                pinyins.append([pinyinDatas[0]])
        else:
            for curr in word:
                if curr in self.homographWeightDict:
                    #if homograph:
                    pinyinDatas = list()
                    if pinyinType in self.homographWeightDict[curr]:
                        pinyinDatas = self.homographWeightDict[curr][pinyinType]
                    if len(pinyinDatas) == 0:
                        pinyins.append(pinyinDatas)
                        continue
                    if pinyinStyle in [1, 3, 5, 7, 9, 11]:
                        pinyins.append(pinyinDatas)
                    else:
                        maxPinyinIndex = 0
                        maxWeight = 0
                        weights = self.homographWeightDict[curr]["weight"]
                        for i in range(len(weights)):
                            if maxWeight < float(weights[i]):
                                maxWeight = float(weights[i])
                                maxPinyinIndex = i
                        pinyins.append([pinyinDatas[maxPinyinIndex]])

    def getMark(self, pinyin, shengdiaoToPlain):
        plain_mark_pinyin = ''
        tailMark = '5'
        for curr in pinyin:
            if curr not in shengdiaoToPlain:
                plain_mark_pinyin += curr
            else:
                plain_mark_pinyin += shengdiaoToPlain[curr][0]
                tailMark = str(shengdiaoToPlain[curr][1])
        plain_mark_pinyin += tailMark
        return plain_mark_pinyin

    def formatMarkPinyin(self, pinyin):
        shengdiao = '''a ?? ?? ?? ??
o ?? ?? ?? ??
e ?? ?? ?? ??
i ?? ?? ?? ??
u ?? ?? ?? ??
?? ?? ?? ?? ??'''
        shengdiaoToPlain = dict()
        for line in shengdiao.split("\n"):
            datas = line.split(' ')
            for i in range(len(datas)):
                if i == 0:
                    continue
                shengdiaoToPlain[datas[i]] = [datas[0], i]
        markPinyins = list()
        for curr_pinyin in pinyin.split(" "):
            markPinyins.append(self.getMark(curr_pinyin, shengdiaoToPlain))
        return " ".join(markPinyins).replace('??', 'v').lower()



    def formatPinyins(self, pinyins, pinyinStyle):
        for i in range(len(pinyins)):
            for j in range(len(pinyins[i])):
                if pinyinStyle in [4, 5, 6, 7]:
                    pinyins[i][j] = self.formatMarkPinyin(pinyins[i][j])
                pinyins[i][j] = pinyins[i][j]



    '''
        parameters:
        word - ??????????????????????????????
        pinyins - ??????????????????
        pinyinStyle - ??????????????????
    '''
    def getPinyin(self, sentence, pinyinStyle=PinyinStyle.PLAINMARK_POLYPHONE_WITH_PHRASE):
        seg_list = jieba.cut(sentence) #?????????????????????
        lines = ",".join(seg_list)
        #print(lines)
        pinyins = list()
        for word in lines.split(","):
            self.matchPinyin(word, pinyins, pinyinStyle)
        self.formatPinyins(pinyins, pinyinStyle)
        return pinyins

if __name__ == "__main__":
    sentence = "?????????"
    pinyin = PinyinDataBuild(loadJieba=False).getPinyin(sentence=sentence)
    print(pinyin)
