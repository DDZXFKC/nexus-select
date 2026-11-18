# GPT実装：共通カラーマスター外部辞書照合
オーナー指示：魔王による画像目視不要、外部既存データを再利用、全ブランド共通。作業実施済み：meodai/color-namesの固定コミット4e9d724b03a4c8334933a312958f370d187317c4からCSV実物706680文字（正規化名32004種）とMITライセンスを取得し、既存新規マスターCSV1656行（正規化名1656種）を実データ照合。辞書完全一致のみ567件（既存値等を優先する前の件数）。候補生成結果：既存55、辞書完全一致529、基本色語626、UNKNOWN429、複数基本色11、特殊語6。HEXあり1210/1656、なし446。これは候補であり商品数・BUYMA確定数ではない。現行テーマから86語を抽出してパレットJSONに保存。既存13トークンを含む実シートの共通キー移行、全商品への再計算は未実施。既存CSVに元のID衝突修正前のIDが残る可能性があるため、候補CSVはtoken_normalizedで照合し、color_idだけで結合しない。
## 登録済み
collector/color_dictionary_resolver.py 35e79055
collector/test_color_dictionary_resolver.py 37166b0e
collector/color-dictionary-palette.json 9ced607a
collector/color-dictionary-LICENSE.txt 08536c9b
docs/color-dictionary-candidates-2026-11-19.csv 6bdf88be
全ファイルをGitHub読み戻し一致確認。実データ照合はGPTのJS実行で実施（Pythonと同じ優先順位）。Python自体の実行は未実施：GPTコンテナの外部DNS不可。Pythonは標準ライブラリのみ。Museは実行担当として以下を実行、個別色調査はしない。
## 実行
python3 -m unittest discover -s collector -p test_color_dictionary_resolver.py
python3 collector/color_dictionary_resolver.py --master <共通化済み実シートのCSV> --palette collector/color-dictionary-palette.json --cache <専用キャッシュディレクトリ> --output <新規候補CSV>
固定版辞書とLICENSEを一度取得・ハッシュ保存。既存HEX維持、特殊語は色コードなし、完全一致→基本色語、競合は保留。候補の出典と方法を保持。未解決446件は次に店タグの単一・一意対応や追加の外部辞書で自動処理（画像目視禁止）。今回のコードは店タグ照合やBUYMA分類を実装していない。全件の色コード一括確定、本番反映、実シート書き換えは未実施。実シート共通化の際、既存確定HEXの衝突は自動上書きせず記録。Claudeは既存丸窓連携を継続。