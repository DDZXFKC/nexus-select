# AFTER HOURS CLUB 品質検査システム（第1段階）

開発指示書（改訂版 2026-11-15）の「第1段階：公開前に必須」を実装したものです。
作成：Claude ／ 実行：魔王ちゃん（iMac） ／ 監査：チャッピー

## できること

| 検査 | 内容 | 使うもの |
|---|---|---|
| `data` | 価格の欠落・不正、バリエーションの価格欠落、商品名・ブランド・説明・画像の欠落、画像ファイルの欠落、SKUの欠落・重複、カテゴリー未設定、性別カテゴリーの重複登録、カテゴリー件数の不一致、WordPress設定の旧ブランド名、PCヒーローの動画設定、カテゴリー構造の変更 | 書き出した商品データ（JSON） |
| `crawl` | サイト内の全ページ巡回：リンク切れ、HTTPエラー、リダイレクトの繰り返し・ループ、タイトルの欠落、旧ブランド名「NEXUS SELECT」の表示、画像の表示エラー・破損、確定事項（PCヒーロー静止画／ヘッダーのドロップダウン廃止／空カテゴリー非表示／承認済みロゴ／商品ページの縦スクロール） | Python標準ライブラリ＋Pillow |
| `purchase` | 選択肢の選択、ADD TO BAG、カート、数量変更、小計・合計、送料無料、チェックアウト画面、注文追跡画面、商品削除。WebKit（Safari相当）とChromium、PC幅とスマホ幅の4通り | Playwright |

### 安全のための決まり（コードで固定）

- **読み取りのみ。** データベースには書き込みません。巡回はGET通信だけで、フォームは送信しません。
- **購入の検査はLocal環境だけ。** ホスト名が `.local`／`localhost` 以外のときは実行しません。本番（after-hours-club.com）やLive Link（localsite.io）では、設定に書いても動きません。
- **注文は確定しません。** チェックアウト画面が表示されることまでを確認し、入力も「注文する」も押しません。テストで入れたカートの中身は最後に空にします。
- **許可したホスト以外には通信しません**（`allowed_hosts`）。
- **レポートはリポジトリの外にしか出せません。** 出力先がGitリポジトリの中だと、エラーで止まります（このリポジトリは公開のため）。
- 書き出すデータに、顧客・注文・住所・メールアドレスは含みません。

## 実行手順（iMac）

### 0. 最初の1回だけ

```bash
mkdir -p ~/ahc-qa-reports/export
cd ~/nexus-select/qa
cp config.example.json ~/ahc-qa-reports/config.json   # 必要なら base_url などを書き換える
python3 -m pip install --user Pillow playwright
python3 -m playwright install webkit chromium
```

`config.json` はリポジトリの外に置いてください。

### 1. 商品データを書き出す（WP-CLI、読み取りのみ）

実証済みの方法（Local同梱のWP-CLI pharを、LocalのCLI用PHPで起動し、MySQLソケットを指定）で実行します。

```bash
# 例：パスは環境に合わせて置き換える
PHP="<Local同梱のPHPのパス>"
WP="<Local同梱の wp-cli.phar のパス>"
SOCK="<Localのmysqld.sockのパス>"   # 例: ~/Library/Application Support/Local/run/<サイトID>/mysql/mysqld.sock
SITE="$HOME/Local Sites/kaitsuke-shop/app/public"

"$PHP" -d mysqli.default_socket="$SOCK" -d pdo_mysql.default_socket="$SOCK" \
  "$WP" eval-file ~/nexus-select/qa/export/ahc_export.php ~/ahc-qa-reports/export/latest.json --path="$SITE"
```

成功すると `Exported N products, ... to ...` と表示されます。ソケットを指定しないとDB接続エラーになります。

### 2. 検査を実行する

```bash
cd ~/nexus-select/qa
python3 -m ahc_qa --config ~/ahc-qa-reports/config.json
```

- 一部だけ実行：`--checks data` ／ `--checks data,crawl` ／ `--checks purchase`
- 巡回は途中で止まっても、もう一度同じコマンドを実行すれば続きから再開します。最初からやり直すときは `--fresh`
- 終了コード：CRITICALあり＝2、HIGHあり＝1、それ以外＝0

### 3. 結果を見る

`~/ahc-qa-reports/latest/report.html` をブラウザで開きます（Safariで可）。

```
~/ahc-qa-reports/
  config.json
  export/latest.json            商品データ
  state/baseline.json           基準（初回の結果を自動保存）
  state/category_structure.json カテゴリー構造の確定形（初回に自動保存）
  runs/<日時>/report.html       見やすいレポート（原因ごと・重大度ごと）
  runs/<日時>/findings.csv      表計算用（Excel・Numbersで開ける）
  runs/<日時>/findings.json     機械処理用
  runs/<日時>/screenshots/      購入検査の不具合画面
  runs/<日時>/run.log           実行ログ（処理時間つき）
  latest -> runs/<最新>
```

## 基準と差分

- 初回の結果は自動で `state/baseline.json` に保存されます。
- 2回目以降、各不具合は「既存」か「新規」かが表示され、前回からなくなったものは「解決したもの」に出ます。
- 修正が一段落して、今の状態を新しい基準にしたいときは `--set-baseline` を付けて実行します。

## カテゴリー構造の確定形

- 初回実行時のカテゴリー（ID・名前・スラッグ・親）を `state/category_structure.json` に保存し、以後の変更をHIGHで報告します。
- **初回の実行は、カテゴリーが確定形になっている状態で行ってください。** 確定形が変わったとオーナーが決めた場合は、このファイルを削除してから実行すると、その時点の構造が新しい確定形になります。
- このツールがカテゴリーを変更することはありません。

## 判定の担当と重大度

各不具合には「判定」（Python／AI／人）と重大度（CRITICAL／HIGH／MEDIUM／LOW／REVIEW）が付きます。
REVIEWは自動で確定できないものです（例：複数の性別カテゴリーへの登録はユニセックスなら正しい、送料表示の文言）。

## テスト

意図的に不具合を入れた模擬サイトで、すべての不具合が検出されること、不具合のないサイトでは何も検出されないこと（誤検出ゼロ）を確認します。

```bash
cd ~/nexus-select/qa
python3 -m unittest discover -s tests -v
```

## 第1段階に含まれていないもの

商品画像の品質（白背景・正方形・ぼかし・余白・輪郭・類似画像）、PC・スマホの細かな表示崩れ、表示速度は第2段階で追加します。
