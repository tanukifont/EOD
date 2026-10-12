"""Focused regression checks independent of Glyphs' native UI."""
import ast
import gzip
import pickle
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'EOD.glyphsPalette/Contents/Resources/plugin.py'


def load_logic():
    tree = ast.parse(SOURCE.read_text())
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef))
    methods = [node for node in cls.body if isinstance(node, ast.FunctionDef)]
    for method in methods:
        method.decorator_list = []
    cls.bases = []
    cls.body = methods
    tree.body = [cls]
    namespace = {'Glyphs': SimpleNamespace(font=None, defaults={}, removeCallback=lambda callback: None, localize=lambda d: d['en']),
                 'os': __import__('os'), 'gzip': gzip, 'pickle': pickle,
                 'time': __import__('time'), 'itertools': __import__('itertools'),
                 'random': __import__('random'), '__file__': str(SOURCE)}
    exec(compile(ast.fix_missing_locations(tree), str(SOURCE), 'exec'), namespace)
    return namespace['EOD'](), namespace['Glyphs']


class Control:
    def __init__(self, value=0): self.value = value
    def indexOfSelectedItem(self): return self.value
    def state(self): return self.value
    def intValue(self): return self.value
    def setDoubleValue_(self, value): self.value = value
    def setStringValue_(self, value): self.value = value


class EODTests(unittest.TestCase):
    def setUp(self):
        self.eod, self.app = load_logic()
        self.eod.idsDataPopupButton = Control()
        self.eod.progPercentPopupButton = Control()
        self.eod.runtimeDict = {}
        self.eod.readPdata()

    def test_reload_button_uses_checkbox_and_clears_cache(self):
        self.eod.runtimeDict['runtime_DoneList'] = ['FFFF']
        self.eod.update = lambda sender: None
        self.eod.loadIDSButton_(None)
        self.assertEqual(self.eod.runtimeDict, {})
        self.assertEqual(len(self.eod.idsDict), 27570)

    def test_all_bundled_formulas_terminate(self):
        for uni in self.eod.idsDict:
            self.eod.getFormulaNote(uni, True)
            self.eod.getPartNameDict(self.eod.getFormula(uni))

    def test_recursive_custom_data_terminates(self):
        self.eod.idsDict = {'6728': {'formula': ['⿰', '木', '木']}}
        self.assertIn('木', self.eod.getFormulaNote('6728', True))
        self.assertEqual(self.eod.getPartNameDict(['⿰', '木', '木']), {})

    def test_component_strokes_sum_and_cache_refresh(self):
        def glyph(name, unicode, paths=0, components=()):
            return SimpleNamespace(name=name, unicode=unicode, tags=[], layers={
                'M': SimpleNamespace(paths=[None] * paths,
                                     components=[SimpleNamespace(component=c) for c in components])})
        root_a, root_b = glyph('a', None, 1), glyph('b', None, 2)
        combined = glyph('combined', '6728', components=[root_a, root_b])
        self.app.font = SimpleNamespace(glyphs=[root_a, root_b, combined], selectedFontMaster=SimpleNamespace(id='M'))
        self.eod.idsDict = {'6728': {'totalStrokes': 4}}
        self.assertEqual(self.eod.doneList(), ['6728'])  # 3 > 4 * .7
        combined.layers['M'].components = []
        self.assertEqual(self.eod.doneList(), [])
        self.assertEqual(combined.tags, [])

    def test_sibling_selection_uses_utf16_for_supplementary_cjk(self):
        tab = SimpleNamespace(text='', selectedTextRange=None)
        glyph = SimpleNamespace(unicode='20000')
        self.app.font = SimpleNamespace(currentTab=tab)
        self.eod.thisGlyphs = lambda: [glyph]
        self.eod.doneList = lambda **kwargs: []
        self.eod.checkBoxDoneUniOnly = Control()
        self.eod.checkBoxFormulaType = Control()
        self.eod.textFieldPartAAmount = Control(3)
        self.eod.textFieldPartBAmount = Control(3)
        self.eod.siblingButton_(None)
        self.assertEqual(tab.selectedTextRange, (0, 2))
        self.assertEqual(tab.text, chr(0x20000))

    def test_no_font_and_width_parameter(self):
        self.assertEqual(self.eod.thisGlyphs(), [])
        self.assertEqual(self.eod.doneList(), [])
        self.eod.forgePartsButton_(None)
        self.eod.checkProgressButton_(None)
        self.eod.nextHeroButton_(None)
        self.app.font = SimpleNamespace(customParameters=[
            SimpleNamespace(name='Default Layer Width', value='kana:900'),
            SimpleNamespace(name='Default Layer Width', value='han:1024')])
        self.assertEqual(self.eod.getHanWidth(), 1024)

    def test_existing_recommendation_widths_preserved(self):
        layers = [SimpleNamespace(width=777), SimpleNamespace(width=555)]
        self.app.font = SimpleNamespace(customParameters=[], glyphs={'6728': SimpleNamespace(layers=layers)},
                                        newTab=lambda text: SimpleNamespace())
        self.eod.uniListPopupButton = Control()
        self.eod.heroAmountPopupButton = Control()
        self.eod.textFieldNextHero = Control()
        self.eod.charSetDict = {'GB2312': ['6728']}
        self.eod.doneList = lambda: []
        self.eod.nextHeroList = lambda *args: ['6728']
        self.eod.nextHeroButton_(None)
        self.assertEqual([layer.width for layer in layers], [777, 555])

        class GlyphCollection(dict):
            def __getitem__(self, key): return self.get(key)
            def append(self, glyph): self['6728'] = glyph

        self.app.font.glyphs = GlyphCollection()
        factory = lambda name: SimpleNamespace(layers=[SimpleNamespace(width=0), SimpleNamespace(width=0)])
        self.eod.nextHeroButton_.__func__.__globals__['GSGlyph'] = factory
        self.eod.nextHeroButton_(None)
        self.assertEqual([layer.width for layer in self.app.font.glyphs['6728'].layers], [1000, 1000])

    def test_nested_a_does_not_block_b_or_c_match(self):
        formulas = [
            ['⿰', ['⿱', '木', '火'], ['⿱', '水', '土']],
            ['⿰', ['⿱', '口', '日'], ['⿱', '水', '金']],
            ['⿲', ['⿱', '木', '火'], '水', '土'],
            ['⿲', ['⿱', '口', '日'], '金', '土']]
        self.eod.idsDict = {str(i): {'formula': f} for i, f in enumerate(formulas)}
        self.assertEqual(self.eod.isSlibing('0', '1')[0], 'B-sub')
        self.assertEqual(self.eod.isSlibing('2', '3')[0], 'C')

    def test_siblings_exclude_selected_character(self):
        tab = SimpleNamespace(text='', selectedTextRange=None)
        self.app.font = SimpleNamespace(currentTab=tab)
        self.eod.thisGlyphs = lambda: [SimpleNamespace(unicode='6728')]
        self.eod.doneList = lambda **kwargs: ['6728']
        self.eod.checkBoxDoneUniOnly = Control()
        self.eod.checkBoxFormulaType = Control()
        self.eod.textFieldPartAAmount = Control(3)
        self.eod.textFieldPartBAmount = Control(3)
        self.eod.siblingButton_(None)
        self.assertEqual(tab.text, '木')

    def test_indexed_recommendation_matches_independent_brute_force(self):
        # Independently implement the corrected matching rules, including
        # overlapping matches that must count only once in coverage.
        def matches(x, y):
            if x[0] != y[0] or x[0] == '○':
                return False
            if x[1] == y[1] or x[2] == y[2]:
                return True
            for a, b in zip(x[1:3], y[1:3]):
                if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
                    if a[:2] == b[:2] or a[0:3:2] == b[0:3:2]:
                        return True
            return len(x) > 3 and len(y) > 3 and x[-1] == y[-1]

        unis = sorted(self.eod.idsDict)[:150]
        unis += ['F0000', 'F0001', 'F0002', 'F0003']
        for uni, formula in zip(unis[-4:], [
                ['⿲', ['⿱', '木', '火'], '水', '土'],
                ['⿲', ['⿱', '口', '日'], '金', '土'],
                ['⿰', ['⿱', '木', '火'], ['⿱', '水', '土']],
                ['⿰', ['⿱', '口', '日'], ['⿱', '水', '金']]]):
            self.eod.idsDict[uni] = {'formula': formula}
        self.eod.progBarProgress = Control()
        for done in ([], unis[:12], unis[-1:]):
            candidates = [u for u in unis if u not in done and
                          not any(matches(self.eod.getFormula(u), self.eod.getFormula(d)) for d in done)]
            coverage = {u: sum(matches(self.eod.getFormula(u), self.eod.getFormula(v))
                               for v in candidates) for u in candidates}
            expected = sorted((u for u in candidates if coverage[u]),
                              key=lambda u: (-coverage[u], int(u, 16)))
            self.assertEqual(self.eod.nextHeroList(done, unis, 200), expected)

    def test_part_name_dict_localization_japanese_and_english(self):
        # Test English localization (default mock app)
        parts_en = self.eod.getPartNameDict(self.eod.getFormula('62C5'))  # 担
        self.assertEqual(parts_en['_part.u624C-LR'], ['扌', '⿰ Left'])
        self.assertEqual(parts_en['_part.u65E5-AB'], ['日', '⿰ Right ➤ Substructure: ⿱ Top'])
        self.assertEqual(parts_en['_part.u4E00-AB'], ['一', '⿰ Right ➤ Substructure: ⿱ Bottom'])

        # Switch mock to Japanese
        orig_localize = self.app.localize
        try:
            self.app.localize = lambda d: d.get('ja', d.get('en'))
            parts_ja = self.eod.getPartNameDict(self.eod.getFormula('62C5'))
            self.assertEqual(parts_ja['_part.u624C-LR'], ['扌', '⿰ 左側部'])
            self.assertEqual(parts_ja['_part.u65E5-AB'], ['日', '⿰ 右側部 ➤ 子構造：⿱ 上側部'])
            self.assertEqual(parts_ja['_part.u4E00-AB'], ['一', '⿰ 右側部 ➤ 子構造：⿱ 下側部'])
        finally:
            self.app.localize = orig_localize

    def test_localize_part_note_legacy_conversion(self):
        legacy = '部件字符：扌 \n生成于：【 担 】 \n结构型：⿰ 左侧部'

        # Under English locale
        converted_en = self.eod.localizePartNote(legacy)
        self.assertEqual(converted_en, 'Component: 扌 \nFrom: 【 担 】 \nStructure: ⿰ Left')

        # Under Japanese locale
        orig_localize = self.app.localize
        try:
            self.app.localize = lambda d: d.get('ja', d.get('en'))
            converted_ja = self.eod.localizePartNote(legacy)
            self.assertEqual(converted_ja, 'パーツ文字：扌 \n元文字：【 担 】 \n構造型：⿰ 左側部')
        finally:
            self.app.localize = orig_localize


if __name__ == '__main__': unittest.main()

