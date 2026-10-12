# Explosive Ordnance Disposal (拆字小组)

EOD is a Glyphs 4 compatible plug-in designed to improve the efficiency of Chinese font designers. Provide easy-to-use glyph disassembly and analysis functions.

## Glyphs 4 local revision (2.4.7 / 261012)

The existing native loader is retained. This revision repairs component creation,
Reload, per-master stroke counting, stale results after font changes, and recursive
custom IDS data. Missing `aBombList.pdata` now uses a visible rectangular placeholder;
new part glyphs and the placeholder do not export. Source glyphs retain their names
and Unicode values. The upstream update feed is disabled for this local revision.

Install `EOD.glyphsPalette` in Glyphs 4 and restart the application. Custom IDS data
belongs at `~/Library/Application Support/Glyphs 4/Info/EDO/idsDict.pdata`.
The data filename is **idsDict.pdata**, not idsData.pdata.

Regression checks: `python3 -m unittest discover -s tests -v`.
Native verification details are recorded in `verification/Glyphs4-verification.md`.
Original bundle backups are in `verification/`.

## Features

### Disassemble the Glyph (召集/创建部件)

Automatically disassemble the CJK characters into radical or part glyphs.

Example:

    '鷹' =
        _part.u5E7F-SfAL  <--- '广' as a part
        + _part.u4EBB-LR  <--- '亻' as a part
        + _part.u96B9-LR  <--- '隹' as a part
        + _part.u9CE5-Si  <--- '鳥' as a part

Demo:

![Disassemble GIF](./img/EOD-Demo-Disassemble.gif)

### Siblings Glyphs (呼叫姐妹字)

*Siblings Glyphs* contain a group of CJK characters that share the same radical or part.

Example:

    䧹 in (應 譍 噟 鷹)  <--- Siblings
    鳥 in (鷹 鴵 蔦 鵎)  <--- Also Siblings, and '鷹' in both groups.

EOD give you an button to randomly call out the siblings for quick edit or compare the glyphs.

Demo:

![Siblings Glyphs GIF](./img/EOD-Demo-Siblings.gif)

## [ ...WIP ]

## License

Copyright © 2020–2021 3type

Made possible with the [GlyphsSDK](https://github.com/schriftgestalt/GlyphsSDK) by Georg Seifert ([@schriftgestalt](https://github.com/schriftgestalt)) and Rainer Erich Scheichelbauer ([@mekkablue](https://github.com/mekkablue)).

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

<http://www.apache.org/licenses/LICENSE-2.0>

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
