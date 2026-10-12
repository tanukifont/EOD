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


if __name__ == '__main__': unittest.main()
