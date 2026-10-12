# EOD Glyphs 4 検証記録

- 修正版: 2.4.7 / 261012、2026-10-12
- 実機: Glyphs 4.2 (4201), `com.GeorgSeifert.Glyphs4`
- plugin.py SHA-256: `060b903e578aef26b46e12d2e46438e320c51eadeecfa0aab661f22e1a419733`
- 既存ローダー SHA-256: `165af5653635741bbf6698476aff5f868618a8040bc76d8abb7076f7115e91fa`
- ローダーは変更せず、x86_64 / arm64の両アーキテクチャを保持。

## 修正

1. Reloadがチェックボックスをポップアップとして呼び出し、readPdataへ余分な引数を渡す問題。
2. 欠落しているaBombList.pdataによる部品作成失敗。矩形の仮部品を生成するよう修正。
3. 元グリフを丸ごと置換するコピー処理。部品名・Unicodeのない状態を保ち、各マスターの図形を独立コピー。
4. 複数コンポーネントの画数集計が最後のコンポーネントだけになっていた問題。循環も検出。
5. フォントやマスター変更後も残る集計キャッシュと重複タグ。
6. フォント未選択、負の抽出件数、漢字以外のデフォルト幅指定、循環IDSへの対処。
7. Glyphs 4の図形プロキシを踏まえたshape追加と、元文字の選択位置維持。
8. 選択範囲をUTF-16単位に合わせ、補助平面の漢字にも対応。
9. カスタムデータ案内をGlyphs 4の`Info/EDO/idsDict.pdata`へ訂正。
10. ローカル修正版を旧版で上書きしないため、上流UpdateFeedURLを削除。

## 静的検証

`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`: 6テスト成功。
同梱27,570文字すべての深い分解表示と部品名生成が終了することを確認。
plist構文とgit diff --checkも成功。XIBからNIBを再コンパイル済み。

開発スキルのscaffold検証は、その配布テンプレートのローダーhash不一致と
旧バンドルにSDK provenanceファイルがないため成功扱いにしていない。
既存バンドルの構造確認と、実際のGlyphs 4による起動・読み込みを別に検証した。

## 実機検証

専用フォント: `/tmp/EOD-Glyphs4-Test-20261012.glyphs`。
作業フォントへのプラグイン操作は実行していない。

Glyphsのインストール画面で旧EODを置換し、Plugins/EOD.glyphsPaletteを
このワークスペースのEOD.glyphsPaletteへリンク。再起動後、読み込まれた
EODクラスのソースパスがこのplugin.pyであることをnative scriptで確認。

実際のパレットをクリックして以下を確認:

- data sourceのReloadが実行できる。
- progressに`Glyphs done: 0 Unicode`が表示される。
- 「体」から`_part.u4EBB-LR`と`_part.u672C-LR`が表示される。
- 最終修正版で生成後も「体」の選択が残る。
- 再実行しても部品が増殖しない。
- 姉妹字ボタンで「休体体」のタブ表示を確認。

再起動後のインストール済みEODクラスを使う追加テスト
`native_test.py`も全assertを通過した:

- 27,570件のIDSデータをReload。
- 「林」のテスト構造を上下に設定し、新規`_part.u6728-AB`へ木の輪郭を独立コピー。
- 部品はUnicodeなし・非出力、生成後も林を選択。
- 繰り返してもグリフ数は同じ。
- 姉妹字「休体体」、進捗の再集計でタグ重複なし。
- 推薦は5文字のテスト集合で「休体林」を確認。
- 出力末尾: `FINAL_NATIVE_TEST_COMPLETE`。

## 検証範囲

推薦機能の全GB2312/Big5集合での速度、全機能の1操作単位のUndo、
実機での複数マスター切り替えは今回の確認範囲に含めない。
複数コンポーネント集計と補助平面文字の選択範囲は独立回帰テストで確認。

作業中のSymbolProject_G4_AutoFitTest.glyphsは、再起動前に利用者の許可を受けて保存。
保存前後のSHA-256が同じであることを確認:
`0e5858a34668a467dfde169865039b98dc5b51fee3bc35f0acba7753c7acf83c`。

## 戻す場合

`EOD-before-Glyphs4.zip`は修正前のワークスペースバンドル、
`EOD-installed-before.zip`はインストール済み旧版のバックアップ。
元のPluginsリンク先は`~/Library/Application Support/Glyphs 4/Repositories/EOD/EOD.glyphsPalette`。
