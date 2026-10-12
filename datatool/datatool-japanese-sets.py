#!/usr/bin/env python3
"""Generate Japanese character sets and build unified charSetDict.pdata."""

import gzip
import json
import os
import pickle
import re
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)


def to_hex(ch):
    return hex(ord(ch)).swapcase()[2:]


# 1. Existing character sets
def load_json(filename):
    with open(os.path.join(BASE_DIR, filename), 'r', encoding='utf-8') as f:
        return json.load(f)


uniList_GB2312 = sorted(load_json('GB2312.json'))
uniList_Big5 = sorted(load_json('Big5.json'))
uniList_Hanyi9169 = sorted(load_json('Hanyi9619.json'))

# 2. JIS X 0208 Level 1 & Level 2
jis1_chars = []
for ku in range(16, 48):
    for ten in range(1, 95):
        if ku == 47 and ten > 51:
            break
        jis1_chars.append(bytes([ku + 0xa0, ten + 0xa0]).decode('euc_jp'))
assert len(jis1_chars) == 2965, f'JIS1 count mismatch: {len(jis1_chars)}'
uniList_JIS1 = sorted(to_hex(c) for c in jis1_chars)

jis2_chars = []
for ku in range(48, 85):
    for ten in range(1, 95):
        if ku == 84 and ten > 6:
            break
        jis2_chars.append(bytes([ku + 0xa0, ten + 0xa0]).decode('euc_jp'))
assert len(jis2_chars) == 3390, f'JIS2 count mismatch: {len(jis2_chars)}'

uniList_JIS1_2 = sorted(to_hex(c) for c in (jis1_chars + jis2_chars))
assert len(uniList_JIS1_2) == 6355, f'JIS1+2 count mismatch: {len(uniList_JIS1_2)}'

# 3. 常用漢字 (2,136字)
joyo_url = 'https://raw.githubusercontent.com/JuanitoFatas/common_kanjis/master/common_kanjis.json'
req = urllib.request.urlopen(joyo_url)
joyo_data = json.loads(req.read().decode('utf-8'))
joyo_chars = [x['word'] for x in joyo_data['results']]
assert len(joyo_chars) == 2136, f'Joyo count mismatch: {len(joyo_chars)}'
uniList_Joyo = sorted(to_hex(c) for c in joyo_chars)

# 4. 教育漢字 (1,026字)
# Fetch directly from Wikipedia 学年別漢字配当表
wiki_url = 'https://ja.wikipedia.org/wiki/%E5%AD%A6%E5%B9%B4%E5%88%A5%E6%BC%A2%E5%AD%97%E9%85%8D%E5%BD%93%E8%A1%A8'
req_wiki = urllib.request.Request(wiki_url, headers={'User-Agent': 'Mozilla/5.0'})
wiki_html = urllib.request.urlopen(req_wiki).read().decode('utf-8')

expected_grades = {1: 80, 2: 160, 3: 200, 4: 202, 5: 193, 6: 191}
kyoiku_chars = []
for g in range(1, 7):
    marker = f'<h2 id="第{g}学年（{expected_grades[g]}字）">'
    body = wiki_html.split(marker)[1]
    m = re.search(r'<p[^>]*><b[^>]*>(.*?)</b></p>', body, re.DOTALL)
    g_chars = re.findall(r'title=\"wikt:([^\"]+)\"', m.group(1))
    assert len(g_chars) == expected_grades[g], f'Grade {g} mismatch: {len(g_chars)} != {expected_grades[g]}'
    kyoiku_chars.extend(g_chars)

assert len(kyoiku_chars) == 1026, f'Kyoiku count mismatch: {len(kyoiku_chars)}'
uniList_Kyoiku = sorted(to_hex(c) for c in kyoiku_chars)

# Verify Kyoiku is subset of Joyo
assert set(uniList_Kyoiku).issubset(set(uniList_Joyo)), 'Kyoiku must be subset of Joyo'

# Save JSON datasets for transparency
datasets = {
    'Joyo.json': uniList_Joyo,
    'JIS1.json': uniList_JIS1,
    'Kyoiku.json': uniList_Kyoiku,
    'JIS1_2.json': uniList_JIS1_2,
}
for name, data in datasets.items():
    path = os.path.join(BASE_DIR, name)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    print(f'Saved {name} ({len(data)} items)')

# Package charSetDict.pdata
charSetDict = {
    'Joyo': uniList_Joyo,
    'JIS1': uniList_JIS1,
    'Kyoiku': uniList_Kyoiku,
    'JIS1_2': uniList_JIS1_2,
    'GB2312': uniList_GB2312,
    'Hanyi9169': uniList_Hanyi9169,
    'Big5': uniList_Big5,
}

output_pdata = os.path.join(OUTPUT_DIR, 'charSetDict.pdata')
with gzip.open(output_pdata, 'wb') as f:
    f.write(pickle.dumps(charSetDict))
print(f'Built {output_pdata}')

# Copy to plugin dataset directory
plugin_dataset = os.path.join(BASE_DIR, '..', 'EOD.glyphsPalette', 'Contents', 'Resources', 'dataset', 'charSetDict.pdata')
with gzip.open(plugin_dataset, 'wb') as f:
    f.write(pickle.dumps(charSetDict))
print(f'Updated {plugin_dataset}')

print('All Japanese character sets generated and packaged successfully!')
