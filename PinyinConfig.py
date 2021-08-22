import configparser
import os
import sys
sys.path.append("./exact-pinyin-mark")

global pinyin_config

pinyin_config = configparser.ConfigParser()
pinyin_config.sections()
if os.path.exists("pinyin_setting.ini"):
    pinyin_config.read("pinyin_setting.ini")
else:
    pinyin_config.read("./exact-pinyin-mark/pinyin_setting.ini")
