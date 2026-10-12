# encoding: utf-8

################################################################################
#
#    Explosive Ordnance Disposal
#    The Glyphs 4 compatible Plugin from 3type
#
################################################################################

import gzip
import itertools
import os
import pickle
import random
import time

import objc
from GlyphsApp import UPDATEINTERFACE, Glyphs, GSComponent, \
    GSGlyph, GSNode, GSPath
from GlyphsApp.plugins import PalettePlugin


class EOD(PalettePlugin):
    '''
    ============================================================================
    objc IBOutlet Zone
    ============================================================================
    '''

    dialog = objc.IBOutlet()

    textFieldTargetZi = objc.IBOutlet()
    textFieldTargetZiFormulaType = objc.IBOutlet()
    textFieldPartAAmount = objc.IBOutlet()
    textFieldPartBAmount = objc.IBOutlet()
    textFieldProgress = objc.IBOutlet()
    textFieldNextHero = objc.IBOutlet()
    textFieldPartNameNote = objc.IBOutlet()

    checkBoxFormulaType = objc.IBOutlet()
    checkBoxDoneUniOnly = objc.IBOutlet()
    checkBoxFormulaDeepDown = objc.IBOutlet()

    progBarProgress = objc.IBOutlet()

    uniListPopupButton = objc.IBOutlet()
    heroAmountPopupButton = objc.IBOutlet()
    progPercentPopupButton = objc.IBOutlet()
    idsDataPopupButton = objc.IBOutlet()

    '''
    ============================================================================
    objc IBAction Zone
    ============================================================================
    '''

    @objc.IBAction
    def forgePartsButton_(self, sender):
        '''
        Find all the formula parts and call out. If _parts.xxx glyph is empty,
        copy form the done Zi.
        '''
        time_start = time.time()
        font = Glyphs.font
        if font is None:
            return
        thisUniList = [glyph.unicode for glyph in self.thisGlyphs() if glyph.unicode]

        if not thisUniList:
            return

        sumDict = {}
        partNameStr = ''

        for glyphUni in thisUniList:
            if glyphUni in self.idsDict.keys():
                formula = self.getFormula(glyphUni)
                partNameDict = self.getPartNameDict(formula)

                for partName, noteList in partNameDict.items():
                    sumDict[partName] = sumDict.get(partName, 0) + 1

                    # Example: '_part.u8F66-LR' ---> '8F66'
                    rootName = partName.removeprefix(
                        '_part.u').split('-', 1)[0]
                    partNameStr = partNameStr + '/' + partName + ' '

                    if not font.glyphs[partName]:
                        partGlyph = GSGlyph(partName)
                        partGlyph.export = False
                        font.glyphs.append(partGlyph)
                        sumShapes = 0
                        if (rootGlyph := font.glyphs[rootName]):
                            for layer in rootGlyph.layers:
                                sumShapes += len(layer.shapes)

                        if sumShapes:
                            for master in font.masters:
                                source = rootGlyph.layers[master.id]
                                target = partGlyph.layers[master.id]
                                target.shapes = [shape.copy() for shape in source.shapes]
                                target.width = source.width
                        else:
                            for master in font.masters:
                                layer = font.glyphs[partName].layers[master.id]
                                layer.shapes = list(layer.shapes) + [self.getBombComponent()]
                                layer.width = self.getHanWidth()

                        userData_partNameNote = '部件字符：%s \n生成于：【 %s 】 \n结构型：%s' % (noteList[0],
                                                                                   self.zi(glyphUni), noteList[1])
                        font.glyphs[partName].userData['EOD_partNameNote'] = userData_partNameNote

            else:
                continue
        tab = font.currentTab or font.newTab()
        if tab is not None:
            original = self.zi(thisUniList[0])
            tab.text = partNameStr + original
            originalLength = len(original.encode('utf-16-le')) // 2
            stringLength = len(tab.string.encode('utf-16-le')) // 2
            tab.selectedTextRange = (max(0, stringLength - originalLength), originalLength)

        print('=' * 40, '\n部件查找计算用时：', round(time.time() - time_start, 2), 's')
        # print(sumDict)

    @objc.IBAction
    def checkProgressButton_(self, sender):
        '''
        Check the done glyphs by totalStrokes.
        '''
        if Glyphs.font is None:
            return
        doneList = self.doneList(update=True)
        self.doneList(update=True, bypass=True)

        font = Glyphs.font
        for xUni in doneList:
            if 'EOD_Done' not in font.glyphs[xUni].tags:
                font.glyphs[xUni].tags.append('EOD_Done')
        textDone = Glyphs.localize({
            'en': 'Glyphs done: ',
            'zh': '已绘制：'})
        text = textDone + str(len(doneList)) + ' Unicode'
        self.textFieldProgress.setStringValue_(text)

    @objc.IBAction
    def siblingButton_(self, sender):
        '''
        Call out all the sibling glyphs to play.
        '''
        # time_start = time.time()

        font = Glyphs.font
        if (thisGlyphs := self.thisGlyphs()):
            thisGlyph = thisGlyphs[0]
        else:  # No selection
            return

        if not (thisGlyphUni := thisGlyph.unicode):  # No unicode glyphs
            return

        searchRange = []
        if self.checkBoxDoneUniOnly.intValue():
            searchRange = self.doneList()
        else:
            searchRange = self.doneList(bypass=True)

        if self.checkBoxFormulaType.intValue():
            formulaTypeList = []
            thisGlyphFormulaType = self.getFormula(thisGlyphUni)[0]
            for xUni in searchRange:
                if thisGlyphFormulaType == self.getFormula(xUni)[0]:
                    formulaTypeList.append(xUni)
            searchRange = formulaTypeList
        # print('='*40, '\nEOD searchRange Time: %fs' %
        #       round(time.time() - time_start, 2))
        glyphZi = self.zi(thisGlyphUni)

        partListA = []
        partListB = []
        for xUni in searchRange:
            if not (matchType := self.isSlibing(thisGlyphUni, xUni)[0]):
                continue
            if matchType in ['A', 'A-sub']:
                partListA.append(xUni)
            elif matchType in ['B', 'B-sub', 'C']:
                partListB.append(xUni)

        # print('='*20, '\n查询字:', glyphZi, '\n', '-'*20)

        def getRandomStr(xList, amount):
            rList = random.sample(xList, min(len(xList), max(0, amount)))
            return ''.join(self.zi(x) for x in rList)

        partStrA = getRandomStr(
            partListA, self.textFieldPartAAmount.intValue())
        partStrB = getRandomStr(
            partListB, self.textFieldPartBAmount.intValue())
        # print('A侧部件:', partStrA)
        # print('B侧部件:', partStrB)

        tabText = partStrA + glyphZi + partStrB
        tab = font.currentTab or font.newTab(tabText)
        tab.text = tabText
        tab.selectedTextRange = (len(partStrA.encode('utf-16-le')) // 2,
                                 len(glyphZi.encode('utf-16-le')) // 2)
        Glyphs.defaults['com.the3type.EOD.siblingAmounts'] = [self.textFieldPartAAmount.intValue(),
                                                              self.textFieldPartBAmount.intValue()]

        # print('='*40, '\nEOD sibling Time: %fs' %
        #       round(time.time() - time_start, 2))

    @objc.IBAction
    def nextHeroButton_(self, sender):
        '''
        Find your next Hero Glyph to help the most.
        '''
        font = Glyphs.font
        if font is None:
            return
        layerWidth = self.getHanWidth()

        uniListDict = {
            0: 'GB2312',
            1: 'Hanyi9169',
            2: 'Big5'
        }
        uniListName = uniListDict[self.uniListPopupButton.indexOfSelectedItem()]

        searchRange = self.charSetDict[uniListName]
        print('Character set size: ', len(searchRange))
        doneList = self.doneList()
        print('Characters done: ', len(doneList))

        heroAmount = self.heroAmountPopupButton.indexOfSelectedItem() + 1
        nextHeroList = self.nextHeroList(doneList, searchRange, heroAmount)

        nextHeroZiStr = ''
        for xUni in nextHeroList:
            nextHeroZiStr += self.zi(xUni)
            if not font.glyphs[xUni]:
                font.glyphs.append(GSGlyph(self.zi(xUni)))
            for layer in font.glyphs[xUni].layers:
                layer.width = layerWidth

        self.textFieldNextHero.setStringValue_(nextHeroZiStr)
        tab = font.newTab(nextHeroZiStr)
        if tab is not None:
            firstLength = len(nextHeroZiStr[:1].encode('utf-16-le')) // 2
            tab.selectedTextRange = (0, firstLength)

    @objc.IBAction
    def loadIDSButton_(self, sender):
        '''
        Choose your IDS data.
        '''
        self.readPdata()
        self.update(None)

    '''
    ============================================================================
    Glyphs-Plugin Zone
    ============================================================================
    '''

    @objc.python_method
    def settings(self):
        self.name = Glyphs.localize({
            'en': 'Explosive Ordnance Disposal',
            'zh': '拆字小组',
        })

        self.loadNib('IBdialog', __file__)

    @objc.python_method
    def start(self):
        # Get ready for startup
        self.idsDict = {}
        self.charSetDict = {}
        self.lastActiveGlyph = None
        self.lastActiveTab = None
        self.lastUIState = None
        self.runtimeDict = {}
        # Load data
        self.readPdata()
        # UI setup
        siblingAmounts = Glyphs.defaults.get(
            'com.the3type.EOD.siblingAmounts', [3, 3]
        )
        self.textFieldPartAAmount.setIntValue_(siblingAmounts[0])
        self.textFieldPartBAmount.setIntValue_(siblingAmounts[1])
        self.progPercentPopupButton.selectItemAtIndex_(
            Glyphs.defaults.get('com.the3type.EOD.progPercent', 0)
        )
        Glyphs.addCallback(self.update, UPDATEINTERFACE)

    @objc.python_method
    def __del__(self):
        Glyphs.removeCallback(self.update)

    @objc.python_method
    def update(self, sender):
        font = Glyphs.font
        thisGlyphs = self.thisGlyphs()
        if not thisGlyphs:
            return

        thisGlyph = thisGlyphs[0]
        uiState = (font, thisGlyph, font.currentTab,
                   self.checkBoxFormulaDeepDown.intValue(),
                   thisGlyph.userData['EOD_partNameNote'])
        if uiState == self.lastUIState:
            return
        self.lastUIState = uiState

        self.lastActiveGlyph = thisGlyph
        self.lastActiveTab = font.currentTab

        thisGlyphUni = thisGlyph.unicode
        if thisGlyphUni in self.idsDict.keys():
            targetZi = self.zi(thisGlyphUni)
            targetZiFormulaType = self.getFormula(thisGlyphUni)[0]
        else:
            targetZi = '⌀'
            targetZiFormulaType = '○'

        if thisGlyph.userData['EOD_partNameNote']:
            nameNote = thisGlyph.userData['EOD_partNameNote']
        elif thisGlyph.unicode:
            text = Glyphs.localize({
                "en": "Decomposition:",
                "zh": "拆解结构式：",
            })
            nameNote = text + "\n" + self.getFormulaNote(
                thisGlyph.unicode,
                deepDown=self.checkBoxFormulaDeepDown.intValue()
            )
        else:
            nameNote = Glyphs.localize({
                'en': 'Glyph without Unicode',
                'zh': '无 Unicode 字符',
            })

        self.textFieldTargetZi.setStringValue_(targetZi)
        self.textFieldTargetZiFormulaType.setStringValue_(targetZiFormulaType)
        self.textFieldPartNameNote.setStringValue_(nameNote)

    @objc.python_method
    def __file__(self):
        return __file__

    '''
    ============================================================================
    EOD self.function Zone
    ============================================================================
    '''

    @objc.python_method
    def thisGlyphs(self):
        font = Glyphs.font
        if font is None:
            return []
        if font.currentTab:
            thisLayers = font.currentTab.selectedLayers
            if len(thisLayers) >= 1:
                thisGlyphList = [layer.parent for layer in thisLayers]
            else:
                thisGlyphList = []

        else:
            try:
                thisGlyphList = font.selection
            except:
                thisGlyphList = []

        return thisGlyphList

    @objc.python_method
    def zi(self, xUni):
        return chr(int(xUni, 16))

    @objc.python_method
    def uni(self, zi):
        return hex(ord(zi)).swapcase()[2:]

    @objc.python_method
    def getHanWidth(self):
        font = Glyphs.font
        layerWidth = 1000.0
        if font is None:
            return layerWidth
        for parameter in font.customParameters:
            if parameter.name == 'Default Layer Width':
                value = str(parameter.value)
                if value.startswith('han:'):
                    try:
                        return float(value[4:])
                    except ValueError:
                        continue
                try:
                    layerWidth = float(value)
                except ValueError:
                    continue

        return layerWidth

    @objc.python_method
    def getFormula(self, xUni):
        if (xUniValue := self.idsDict.get(xUni)):
            return xUniValue.get('formula')
        else:
            zi = self.zi(xUni)
            return ['○', zi, zi]

    @objc.python_method
    def getFormulaNote(self, xUni, deepDown=False):
        if not self.idsDict:
            formulaNote = Glyphs.localize({
                'en': 'Please click the 「数据源」 tab to download or choose your data file',
                'zh': '首次使用，请点击「数据源」标签页，下载所需数据。',
            })
            return formulaNote

        def packList(xList, deep=False, seen=frozenset()):
            outStr = ''
            for x in xList:
                # print(x)
                if isinstance(x, list):
                    outStr += '「%s」' % packList(x, deep, seen)
                elif isinstance(x, str):
                    if len(x) > 1:  # For 'CDP-xxxxx'
                        outStr += '「%s」' % x
                    elif deep:  # Search the Zi again
                        formulaList = self.getFormula(self.uni(x))
                        if formulaList[0] == '○' or x in seen:
                            outStr += x
                        else:
                            outStr += '「%s」' % packList(formulaList, deep, seen | {x})
                    else:
                        outStr += x
            return outStr

        formulaList = self.getFormula(xUni)
        # print(formulaList)
        if formulaList[0] == '○':
            formulaNote = '「 %s 」' % formulaList[1]
        else:
            formulaNote = packList(formulaList, deepDown)
        return formulaNote

    @objc.python_method
    def getPartNameDict(self, formulaList, seen=frozenset()):
        def cleanName(strOld):
            strNew = ''
            for x in strOld:
                if x.isalnum() or x in '-_':
                    pass
                else:
                    x = '_'
                strNew += x
            return strNew

        modelStrDict = {
            '⿰': [['-LR', '⿰ 左侧部', '⿰左'], ['-LR', '⿰ 右侧部']],
            '⿱': [['-AB', '⿱ 上侧部'], ['-AB', '⿱ 下侧部']],
            '⿴': [['-FS', '⿴ 全包围部'], ['-Si', '⿴ 被包围部']],
            '⿵': [['-SfA', '⿵ 上包围部'], ['-Si', '⿴ 被包围部']],
            '⿶': [['-SfB', '⿶ 下包围部'], ['-Si', '⿴ 被包围部']],
            '⿷': [['-SfL', '⿷ 左包围部'], ['-Si', '⿴ 被包围部']],
            '⿸': [['-SfAL', '⿸ 左上包围部'], ['-Si', '⿴ 被包围部']],
            '⿹': [['-SfAR', '⿹ 右上包围部'], ['-Si', '⿴ 被包围部']],
            '⿺': [['-SfBL', '⿺ 左下包围部'], ['-Si', '⿴ 被包围部']],
            '⿻': [['-XiX', '⿻ 交叠件'], ['-XiX', '⿻ 交叠件']],
            '⿲': [['-LR', '⿲ 左侧部'], ['-LR', '⿲ 中央部'], ['-LR', '⿲ 右侧部']],
            '⿳': [['-AB', '⿳ 上侧部'], ['-AB', '⿳ 中央部'], ['-AB', '⿳ 下侧部']]
        }
        modelSymbol = formulaList[0]
        if modelSymbol == '○':
            return {}

        if modelSymbol not in modelStrDict or repr(formulaList) in seen:
            return {}
        seen = seen | {repr(formulaList)}
        modelList = modelStrDict[modelSymbol]
        partNameDict = {}
        for i, part in enumerate(formulaList[1:]):

            nameNote = modelList[i][1]
            if isinstance(part, str) and len(part) == 1:
                partFormulaList = self.getFormula(self.uni(part))
                if partFormulaList[0] == '○':
                    partNameStr = '_part.u' + self.uni(part) + modelList[i][0]
                    partNameDict[partNameStr] = [part, nameNote]
                else:
                    innerPartDict = self.getPartNameDict(partFormulaList, seen)
                    for xName, xNote in innerPartDict.items():
                        nameNote = modelList[i][1] + ' ➤ 子结构：' + xNote[1]
                        innerPartDict[xName][1] = nameNote
                    partNameDict = innerPartDict | partNameDict

            elif isinstance(part, list):
                innerPartDict = self.getPartNameDict(part, seen)
                for xName, xNote in innerPartDict.items():
                    nameNote = modelList[i][1] + ' ➤ 子结构：' + xNote[1]
                    innerPartDict[xName][1] = nameNote
                partNameDict = innerPartDict | partNameDict

            elif isinstance(part, str):
                partNameStr = '_part.' + cleanName(str(part)) + modelList[i][0]
                partNameDict[partNameStr] = [part, nameNote]

        return partNameDict

    @objc.python_method
    def nextHeroList(self, doneUniList, allUniList, amount=3):
        def cut2ModelDict(uniList):
            modelDict = {}
            for xUni in uniList:
                modelKey = self.getFormula(xUni)[0]
                if modelKey != '○':
                    modelDict.setdefault(modelKey, []).append(xUni)

            return modelDict

        time_start = time.time()
        self.progBarProgress.setDoubleValue_(0.0)

        idsSet = set(self.idsDict.keys())
        doneUniSet = set(doneUniList) & idsSet
        allUniSet = set(allUniList) & idsSet
        searhUniSet = allUniSet - doneUniSet

        nextUniSet = searhUniSet.copy()
        targetDict = cut2ModelDict(doneUniSet)

        for xUni in searhUniSet:
            modelKey = self.getFormula(xUni)[0]
            for yUni in targetDict.setdefault(modelKey, []):
                matchType, matchPart, matchNote = self.isSlibing(xUni, yUni)
                if matchType:
                    nextUniSet.discard(xUni)

        self.progBarProgress.setDoubleValue_(50.0)
        print('=' * 20, '\nPart1 Time：', round(time.time() - time_start, 2), 's')
        time_part1 = time.time()

        targetDict = cut2ModelDict(nextUniSet)
        xDict = {}
        for modelList in targetDict.values():
            for xUni, yUni in itertools.product(modelList, modelList):
                matchType, matchPart, matchNote = self.isSlibing(xUni, yUni)
                if matchType:
                    xDict[xUni] = xDict.get(xUni, 0) + 1

        allHeroLists = sorted(xDict.items(), key=lambda x: x[1], reverse=1)
        topHeroLists = allHeroLists[:amount]

        heroList = []
        for xUni, xCoverage in topHeroLists:
            heroList.append(xUni)

        self.progBarProgress.setDoubleValue_(100.0)
        print('=' * 20, '\nPart2 Time：', round(time.time() - time_part1, 2), 's')
        print('=' * 40, '\nTotal Time：', round(time.time() - time_start, 2), 's')

        return heroList

    @objc.python_method
    def doneList(self, update=False, bypass=False):
        def getCompStrokes(glyph, seen=frozenset()):
            if glyph is None or glyph.name in seen:
                return 0
            seen = seen | {glyph.name}
            layer = glyph.layers[Glyphs.font.selectedFontMaster.id]
            if layer is None:
                return 0
            return len(layer.paths) + sum(
                getCompStrokes(comp.component, seen) for comp in layer.components
            )

        if Glyphs.font is None:
            return []

        if bypass:
            dataName = 'runtime_AllList'
        else:
            dataName = 'runtime_DoneList'

        progList = [0.7, 0.5, 0.3, 0.0]
        progIndex = self.progPercentPopupButton.indexOfSelectedItem()
        progPercent = progList[progIndex]
        Glyphs.defaults['com.the3type.EOD.progPercent'] = progIndex

        # Recompute on explicit button actions: a font/master or outlines may
        # have changed since the previous action. Never scan here on redraw.
        listX = []

        for glyph in Glyphs.font.glyphs:
            if not (xUni := glyph.unicode):
                continue
            if bypass:
                listX.append(xUni)
                continue
            if (totalStrokes := self.idsDict.get(xUni, {'totalStrokes': 1}).get('totalStrokes')) < 3:
                totalStrokes = 1
            targetStrokes = progPercent * totalStrokes

            doneStrokes = getCompStrokes(glyph)
            if doneStrokes > targetStrokes:
                listX.append(xUni)
                if 'EOD_Done' not in glyph.tags:
                    glyph.tags.append('EOD_Done')
            else:
                if 'EOD_Done' in glyph.tags:
                    glyph.tags.remove('EOD_Done')
        self.runtimeDict[dataName] = listX

        return listX

    @objc.python_method
    def isSlibing(self, xUni, yUni):
        '''
        Check if the xUni/yUni formula match.
        '''
        slibingResult = [None, None, 'No Match']
        xGet, yGet = self.getFormula(xUni), self.getFormula(yUni)

        xA, xB = xGet[1], xGet[2]
        yA, yB = yGet[1], yGet[2]

        # A-Side match
        if xA == yA:
            slibingResult = ['A', xA, 'A-side match: %s' % str(xA)]
        # B-Side match
        elif xB == yB:
            slibingResult = ['B', xB, 'B-side match: %s' % str(xB)]
        # A-Side sub part match
        elif (isinstance(xA, list) and isinstance(yA, list)):
            if len(xA) == len(yA):
                if (xA[0:2] == yA[0:2] or xA[0:3:2] == yA[0:3:2]):
                    slibingResult = ['A-sub', xA, 'A-side match: %s' % str(xA)]
        # B-Side sub part match
        elif (isinstance(xB, list) and isinstance(yB, list)):
            if len(xB) == len(yB):
                if xB[0:2] == yB[0:2] or xB[0:3:2] == yB[0:3:2]:
                    slibingResult = ['B-sub', xB, 'B-side match: %s' % str(xB)]
        # C-Side match for 3in1
        elif len(xGet) > 3 and xGet[-1] == yGet[-1]:
            xC = xGet[-1]
            slibingResult = ['C', xC, 'C-side match: %s' % str(xC)]

        return slibingResult

    @objc.python_method
    def defaultDataFolder(self):
        workDir = os.path.dirname(__file__)
        workDir = os.path.join(workDir, "dataset")
        # print("__workDir", workDir)
        return workDir

    @objc.python_method
    def userDataFolder(self):
        from Foundation import NSApplicationSupportDirectory, NSUserDomainMask, NSSearchPathForDirectoriesInDomains
        workDir = os.path.join(
            NSSearchPathForDirectoriesInDomains(NSApplicationSupportDirectory, NSUserDomainMask, True)[0],
            'Glyphs 4',
        )
        workDir = os.path.join(workDir, "Info/EDO")
        # print("__workDir", workDir)
        return workDir

    @objc.python_method
    def readPdata(self):
        '''
        Load or download the pdata file.
        '''
        self.runtimeDict = {}
        self.lastUIState = None

        useLocal = self.idsDataPopupButton.state()

        defaultDataFolder = self.defaultDataFolder()
        with gzip.open(os.path.join(defaultDataFolder, 'charSetDict.pdata'), 'rb') as fin:
            self.charSetDict = pickle.load(fin)
            print('EOD charSetDict Ready')

        idsDataPath = None
        if useLocal:
            idsDataPath = os.path.join(self.userDataFolder(), 'idsDict.pdata')
            if not os.path.exists(idsDataPath):
                idsDataPath = None
        if idsDataPath is None:
            idsDataPath = os.path.join(defaultDataFolder, 'idsDict.pdata')

        try:
            with gzip.open(idsDataPath, 'rb') as fin:
                self.idsDict = pickle.load(fin)
                print('EOD idsDict Ready')
        except (OSError, EOFError, pickle.UnpicklingError) as error:
            self.idsDict = {}
            print(error)
            print('EOD idsDict data missing or broken.\nPlease Try Again.')
        # print("__readPdata b")

    @objc.python_method
    def getBombComponent(self):
        aBomb = '_EOD.aBomb'
        font = Glyphs.font
        aBombGlyph = font.glyphs[aBomb]
        if not aBombGlyph:
            # workDir = os.path.dirname(__file__)
            bombPath = os.path.join(self.defaultDataFolder(), 'aBombList.pdata')
            if os.path.exists(bombPath):
                with gzip.open(bombPath, 'rb') as fin:
                    aBombNodeList = pickle.load(fin)
            else:
                # The upstream bundle omits aBombList.pdata. A visible box is
                # a deterministic placeholder for a component awaiting drawing.
                from GlyphsApp import LINE
                aBombNodeList = [[(100, 100, LINE), (100, 700, LINE),
                                 (700, 700, LINE), (700, 100, LINE)]]

            shapeList = []
            for path in aBombNodeList:
                newPath = GSPath()
                for node in path:
                    newNode = GSNode()
                    newNode.position = (node[0], node[1])
                    newNode.type = node[2]
                    newPath.nodes.append(newNode)
                newPath.closed = True
                shapeList.append(newPath)
            aBombGlyph = GSGlyph(aBomb)
            aBombGlyph.export = False
            font.glyphs.append(aBombGlyph)
            for layer in aBombGlyph.layers:
                layer.width = self.getHanWidth()
                layer.shapes = [shape.copy() for shape in shapeList]

        return GSComponent(aBombGlyph)
