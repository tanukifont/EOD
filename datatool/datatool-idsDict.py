# encoding: utf-8

################################################################################
#
# IDS dataset tool
#
################################################################################

import csv
import re
# import json
import gzip
import pickle


# TSVs of ids data
# CHISE ids project: https://gitlab.chise.org/CHISE/ids
idsTSVList = [
    './dataset/ids/IDS-UCS-Basic.txt',
    './dataset/ids/IDS-UCS-Ext-A.txt'
]

jisTSVFile = './dataset/ids/IDS-JIS-X0208-1990.txt'
orderingFile = './dataset/ids/Adobe-Japan1-7_ordering.txt'

# TSVs of your ids patch to override
# !!! Please follow the CHISE style format
idsPatchList = [
    './dataset/custom/IDS-UCS-Basic-Patch.txt',
    './dataset/custom/IDS-UCS-Ext-A-Patch.txt'
]

# TSVs of Unihan data
# Unihan project: http://www.unicode.org/reports/tr38
unihanTSVList = ['./dataset/Unihan/Unihan_IRGSources.txt']

RADICAL_MAP = {
    '\u2EBE': '\u8279',  # ⺾ -> 艹
    '\u2ECC': '\u8FB6',  # ⻌ -> 辶
    '\u2EDF': '\u98E0',  # ⻟ -> 飠
    '\u2EDE': '\u98E0',  # ⻞ -> 飠
    '\u2ED6': '\u961D',  # ⻖ -> 阝
    '\u2EBC': '\u6708',  # ⺼ -> 月
    '\u2EA1': '\u6C35',  # ⺡ -> 氵
    '\u2EA8': '\u72AD',  # ⺨ -> 犭
    '\u2EA3': '\u706C',  # ⺣ -> 灬
    '\u2EA4': '\u722B',  # ⺤ -> 爫
    '\u2E85': '\u4ebb',  # ⺅ -> 亻
    '\u2E88': '\u5202',  # ⺈ -> 刂
    '\u2E8A': '\u535c',  # ⺊ -> 卜
    '\u2E95': '\u5f51',  # ⺕ -> 彐
    '\u2E96': '\u5fc4',  # ⺖ -> 忄
    '\u2E97': '\u624c',  # ⺗ -> 扌
    '\u2E98': '\u6535',  # ⺘ -> 攵
    '\u2EAB': '\u7389',  # ⺫ -> 王
    '\u2EC0': '\u8864',  # ⻀ -> 衤
    '\u2EB9': '\u793b',  # ⺹ -> 礻
}


def readTSVs(tsvList):
    tsvData = []
    for tsvFile in tsvList:
        try:
            with open(tsvFile, 'r', encoding='utf-8') as tsv_in:
                tsvReader = csv.reader(tsv_in, delimiter='\t')
                for record in tsvReader:
                    if record and not record[0].startswith(';'):
                        tsvData.append(record)
        except FileNotFoundError:
            pass
    return tsvData


def readJISTSV(jisFile, orderingPath):
    cid_map = {}
    try:
        with open(orderingPath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 4 and parts[1] == 'Kanji':
                    cid = int(parts[0])
                    try:
                        ku = int(parts[2][1:], 16) - 0x20
                        ten = int(parts[3][1:], 16) - 0x20
                        cid_map[cid] = bytes([ku + 0xa0, ten + 0xa0]).decode('euc-jp')
                    except Exception:
                        pass
    except FileNotFoundError:
        print('Ordering file not found, skipping CID mapping.')

    records = []
    try:
        with open(jisFile, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line.startswith('J90-'):
                    continue
                parts = line.split('\t')
                if len(parts) >= 3:
                    hex_str = parts[0].split('-')[1]
                    try:
                        ku = int(hex_str[:2], 16) - 0x20
                        ten = int(hex_str[2:], 16) - 0x20
                        kanji = bytes([ku + 0xa0, ten + 0xa0]).decode('euc-jp')
                    except Exception:
                        continue
                    formulaRAW = parts[2]
                    formulaRAW = re.sub(
                        r'&AJ1-(\d+);',
                        lambda m: cid_map.get(int(m.group(1)), m.group(0)),
                        formulaRAW
                    )
                    for k, v in RADICAL_MAP.items():
                        formulaRAW = formulaRAW.replace(k, v)
                    uni_code = f'U+{ord(kanji):04X}'
                    records.append([uni_code, kanji, formulaRAW])
    except FileNotFoundError:
        print('JIS file not found, skipping JIS dataset.')
    print(f'### JIS records loaded: {len(records)}')
    return records


idsTSVData = readTSVs(idsTSVList) + readJISTSV(jisTSVFile, orderingFile) + readTSVs(idsPatchList)

unihanTSVData = readTSVs(unihanTSVList)


# unihanTSVData = []
# for unihanTSV in unihanTSVList:
# 	with open(unihanTSV, 'r') as tsv_in:
# 		tsvReader = csv.reader(tsv_in, delimiter='\t')
# 		tsvLabels = tsvReader.__next__()
# 		for record in tsvReader:
# 			unihanTSVData.append(record)

unihanDict = {}
for lineList in unihanTSVData:
    if len(lineList) >= 3 and lineList[1] == 'kTotalStrokes':
        xUni = lineList[0][2:]
        xTotalStrokes = int(lineList[2].partition(' ')[0])
        unihanDict[xUni] = {'totalStrokes': xTotalStrokes}


# Package the idsDict
# 	idsDict[xUni] = {'zi': xZi, 'formula': formulaList, 'totalStrokes': totalStrokes}
idsDict = {}


def checkIt(listXY):
    if len(listXY) == 0:
        return 0
    if len(listXY) == 1:
        return 1

    if str(listXY[0]) in '⿲⿳':
        for x in listXY[1:4]:
            if str(x) in '⿰⿱⿴⿵⿶⿷⿸⿹⿺⿻⿲⿳':
                return 0
        return 4

    if str(listXY[0]) in '⿰⿱⿴⿵⿶⿷⿸⿹⿺⿻':
        for x in listXY[1:3]:
            if str(x) in '⿰⿱⿴⿵⿶⿷⿸⿹⿺⿻⿲⿳':
                return 0
        return 3

    return 0


'''
Cut fromula String into List

Input: '⿳⿰巳巳一&GT-K00059;'
Output: ['⿳','⿰','巳','巳','一','GT-K00059']

    [^\u0000-\u007f] >>> NOT Basic Latin Character
    (?<=&).+?(?=;) >>> String surrounded by '&' and ';'

'''
pParts = re.compile(r'[^\u0000-\u007f]|(?<=&).+?(?=;)')

for x in idsTSVData:
    xUni = x[0][2:]
    xZi = x[1]
    formulaRAW = x[2]

    formulaList = re.findall(pParts, formulaRAW)

    # IDS formula parser
    iX = 0
    steps = 0
    failed = False
    while checkIt(formulaList) == 0:
        steps += 1
        if steps > 50 or iX >= len(formulaList):
            failed = True
            break
        if checkIt(formulaList[iX:iX + 4]) == 0:
            iX += 1
        elif checkIt(formulaList[iX:iX + 4]) == 3:
            formulaList = formulaList[:iX] + [formulaList[iX:iX + 3]] + formulaList[iX + 3:]
            iX = 0
        elif checkIt(formulaList[iX:iX + 4]) == 4:
            formulaList = formulaList[:iX] + [formulaList[iX:iX + 4]] + formulaList[iX + 4:]
            iX = 0

    if failed or checkIt(formulaList) == 0:
        continue

    model_lengths = {
        '⿰': 2, '⿱': 2, '⿴': 2, '⿵': 2, '⿶': 2, '⿷': 2,
        '⿸': 2, '⿹': 2, '⿺': 2, '⿻': 2, '⿲': 3, '⿳': 3
    }
    if formulaList[0] in model_lengths and len(formulaList) - 1 != model_lengths[formulaList[0]]:
        continue

    if formulaList == [xZi]:
        formulaList = ['○', xZi, xZi]

    totalStrokes = unihanDict.get(xUni, {'totalStrokes': 0}).get('totalStrokes')
    if not totalStrokes and xUni in idsDict:
        totalStrokes = idsDict[xUni].get('totalStrokes', 0)

    idsDict[xUni] = {'zi': xZi, 'formula': formulaList, 'totalStrokes': totalStrokes}

print('### idsDict{} Ready')

# Checking point with buggy formulas
# ['⿳', '彑', ['⿰', '米', '糸'], '廾']
# ['⿳', '𰀉', ['⿱', '冖', 'GT-K00059'], ['⿱', '𠀎', 'CDP-8B67']]
# ['⿰', '止', '?']
print('Checking the Result:')
print('idsDict[''5F5D'']---->', idsDict['5F5D'])
print('idsDict[''56A2'']---->', idsDict['56A2'])
print('idsDict[''3C50'']---->', idsDict['3C50'])

# Export the data as file

# with open('./output/idsDict.json', 'w') as outfile:
#     json.dump(idsDict, outfile)
#     print('### idsDict{} json Done')

# with open('.output/idsDict.pickle', 'wb') as outfile:
#     pickle.dump(idsDict, outfile)
#     print('### pickle Done')

with gzip.open('./output/idsDict.pdata', 'w') as outfile:
    outfile.write(pickle.dumps(idsDict))
    print('### idsDict{} pickle+gzip Done')

print('##### All Done')
