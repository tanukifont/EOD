import objc, inspect
from GlyphsApp import GSPath, GSNode, LINE
assert font.familyName == 'EOD Glyphs4 Compatibility Test'
p = objc.lookUpClass('EOD').alloc().init()
Glyphs.removeCallback(p.update)
print('LOADED_SOURCE', inspect.getsourcefile(p.getBombComponent))
p.loadIDSButton_(None)
assert len(p.idsDict) == 27570
print('PASS Reload')
wood = font.glyphs['uni6728'].layers[font.masters[0].id]
shape = GSPath()
for xy in [(100,100),(100,700),(700,700),(700,100)]:
    shape.nodes.append(GSNode(xy, LINE))
shape.closed = True
wood.shapes = [shape]
p.idsDict['6797']['formula'] = ['⿱', '木', '木']
tab = font.newTab('林')
tab.selectedTextRange = (0, 1)
assert p.thisGlyphs()[0].name == 'uni6797'
p.forgePartsButton_(None)
part = font.glyphs['_part.u6728-AB']
assert part and not part.export and part.unicode is None
assert len(part.layers[font.masters[0].id].paths) == 1
assert part.layers[font.masters[0].id].paths[0] is not wood.paths[0]
assert p.thisGlyphs()[0].name == 'uni6797'
count = len(font.glyphs)
p.forgePartsButton_(None)
assert len(font.glyphs) == count
print('PASS copied outlines and repeat; original 林 remains selected')
p.readPdata()
tab = font.newTab('体')
tab.selectedTextRange = (0, 1)
p.siblingButton_(None)
assert '休' in font.currentTab.text
assert p.thisGlyphs()[0].name == 'uni4F53'
print('PASS siblings', font.currentTab.text)
p.checkProgressButton_(None)
p.checkProgressButton_(None)
assert all(list(g.tags).count('EOD_Done') <= 1 for g in font.glyphs)
print('PASS repeated progress')
p.charSetDict = {'GB2312': ['6728','6797','68EE','4F11','4F53']}
p.nextHeroButton_(None)
assert font.currentTab.text
print('PASS recommendation bounded dataset', font.currentTab.text)
print('FINAL_NATIVE_TEST_COMPLETE')
