"""Run through Glyphs' Script Window on the dedicated EOD test font only."""
import objc, inspect, time, json, hashlib
from GlyphsApp import Glyphs, GSGlyph, GSLayer
font = Glyphs.font
assert font and font.familyName == 'EOD Glyphs4 Compatibility Test'
p = objc.lookUpClass('EOD').alloc().init()
Glyphs.removeCallback(p.update)
assert hasattr(p, 'siblingKeys'), 'Old plugin class is still loaded'
source = inspect.getsourcefile(p.siblingKeys)
results = {'build': Glyphs.buildNumber, 'source': source,
           'sha256': hashlib.sha256(open(source, 'rb').read()).hexdigest(), 'checks': []}
p.readPdata()
originalIDS = p.idsDict
try:
    p.idsDict = {
        'F0000': {'formula': ['⿰', ['⿱','木','火'], ['⿱','水','土']]},
        'F0001': {'formula': ['⿰', ['⿱','口','日'], ['⿱','水','金']]},
        'F0002': {'formula': ['⿲', ['⿱','木','火'], '水', '土']},
        'F0003': {'formula': ['⿲', ['⿱','口','日'], '金', '土']}}
    assert p.isSlibing('F0000','F0001')[0] == 'B-sub'
    assert p.isSlibing('F0002','F0003')[0] == 'C'
    results['checks'].append('nested B-sub and C matching')
finally:
    p.idsDict = originalIDS

p.uniListPopupButton.selectItemAtIndex_(0)
p.heroAmountPopupButton.selectItemAtIndex_(0)
candidate = p.nextHeroList(p.doneList(), p.charSetDict['GB2312'], 1)[0]
glyph = font.glyphs[candidate]
if glyph is None:
    glyph = GSGlyph(chr(int(candidate,16)))
    font.glyphs.append(glyph)
master = glyph.layers[font.masters[0].id]
master.width = 777
backup = GSLayer()
backup.name = 'EOD width preservation test'
backup.associatedMasterId = font.masters[0].id
backup.width = 555
glyph.layers.append(backup)
p.nextHeroButton_(None)
assert font.currentTab.text == chr(int(candidate,16)), (font.currentTab.text,candidate)
assert master.width == 777 and backup.width == 555, (master.width,backup.width)
p.nextHeroButton_(None)
assert master.width == 777 and backup.width == 555
results['checks'].append({'existing widths after repeated recommendation': [master.width,backup.width]})
for index,name in enumerate(['GB2312','Hanyi9169','Big5']):
    p.uniListPopupButton.selectItemAtIndex_(index)
    p.heroAmountPopupButton.selectItemAtIndex_(2)
    start = time.perf_counter()
    p.nextHeroButton_(None)
    elapsed = time.perf_counter()-start
    assert len(font.currentTab.text) == 3
    results['checks'].append({'dataset':name,'seconds':elapsed,'output':font.currentTab.text})

tab = font.newTab('体')
tab.selectedTextRange = (0,1)
p.checkBoxDoneUniOnly.setIntValue_(0)
p.checkBoxFormulaType.setIntValue_(1)
p.textFieldPartAAmount.setIntValue_(100)
p.textFieldPartBAmount.setIntValue_(100)
p.siblingButton_(None)
assert font.currentTab.text.count('体') == 1, font.currentTab.text
assert '休' in font.currentTab.text
p.siblingButton_(None)
assert font.currentTab.text.count('体') == 1
results['checks'].append({'siblings no duplicate after repeat':font.currentTab.text})
p.readPdata()
p.textFieldPartAAmount.setIntValue_(3)
p.textFieldPartBAmount.setIntValue_(3)
p.siblingButton_(None)
with open('/tmp/EOD-review-native-results.json','w') as handle:
    json.dump(results,handle,ensure_ascii=False,indent=2)
print(json.dumps(results,ensure_ascii=False,indent=2))
print('PASS ALL FOUR REVIEW FIXES IN GLYPHS')
