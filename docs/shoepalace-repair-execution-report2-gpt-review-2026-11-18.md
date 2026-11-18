# GPT検収2／次工程（Shoe Palaceのみ）
根拠：docs/shoepalace-repair-execution-report-maou-2026-11-18-2.md（1a9a75da）。Museの実測報告に基づく検収でありGPT自身のiMac実行ではない。
## 合格
既存3ブランド163商品・1796 variant・1959 CSV行すべてSKUと親子関係で照合成功、sheet_issues 0、元20列の変更0、原本ハッシュ不変、再実行一致。既存CSVとの接続合格。非靴cm対象外、定価復元・件数分離も報告範囲で合格。情報修正全体は色とcmの未解決があるので合格にしない。
## 色
修正コミット90750bd1、41653687。具体色と汎用Color_タグを独立保持。タグと一致しない末尾括弧をTITLE_CANDIDATEとして残す（確定色扱い・原題削除は禁止）。Sea Salt/Astro Dust等を保持し、色以外の括弧・複数候補は確認する。sp_color_name_status追加。Museは靴25件と163件の同一入力で再実行し、候補・確定・不明の件数、色以外の括弧の誤抽出を確認。70件の内訳を記録し、候補は商品原文/公式色欄などから確定できるものだけ確定する。候補の存在だけで合格にしない。
## cm：次の作業
先に163商品のUGG/HOKAの不足サイズを商品ID、型番、モデル、Department、サイズ原文で集計し、必要な行だけ補完する。既存サイズ表を再利用。公式のJP/CMを参照し、足長実測とJP表示を混同しない。
公式資料の調査結果（GPT、2026-11-18）：
- UGG公式USキッズ表：https://www.ugg.com/on/demandware.static/-/Sites-UGG-US-Library/default/dwf764bc52/documents/UGG-Inches-kids-shoe-measurement-guide-v1.pdf （INFANTSの0/1・02/03・04/05等、年齢区分あり。店舗の1C/2C/3Cがこれらと同義と推測しない。実商品の公式サイズ表を照合）
- HOKA公式チリの商品ページ：https://cl.hoka.com/p/hoka-clifton-11-hombre-frost-black/ （CM Japón。女性Clifton系とBondi系で同じUSサイズのCMが異なる。モデルごとの表で照合すること。米国商品の型番・世代・市場と公式表の一致が必要）
- HOKA公式豪州サポート：https://help.au.hoka.com/hc/en-us/sections/32484593546777-Size-Fit （商品別のサイズガイドがある）
- 現行のbrand,department,size_originalの3キーだけではモデル差、乳児・トドラー・キッズ差を識別できない場合がある。GPTが必要なキーの追加を担当するため、Museは実際の不足組み合わせと公式資料の対応を共有する。異なるモデルの表を混ぜてCSVを作らない。未確認は空欄、非靴はNOT_APPLICABLE。
## 順番
1. 上記の色修正を再実行、実物の色の確認とcm不足リストを作成。
2. 実際のモデル別公式表に基づくcm参照契約の修正と再実行。日本語説明は別レイヤーPENDINGのまま保持可。クーポンタグは適用確定ではない。画像加工なし。
3. 163件の修正層検収後、全店バッチ（最新48ページ）を読み取り専用でrepairへ流し、全件数とdistinct商品/variant数、欠落理由を記録。既存Woo prepは3ブランドのみなので全店原本と直接照合して未照合を問題扱いしない。全店の新規出力は別保存、シートの実態に応じて次レイヤーへ渡す。販売・価格・購入・本番書き込みなし。
オーナーへの追加質問不要。GPTは実装担当、Museは実行と証拠回収。