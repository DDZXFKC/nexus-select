# カテゴリー自動分類・旧URL転送の修正 — 魔王ちゃんへの作業依頼（2026-11-15）

作成：Claude ／ 対象ブランチ：`integration/grok-review`
きっかけ：GitHub上のコード監査で見つかった①②⑤（自動分類のタイミング、ブランド名での分類、旧URL転送の不完全さ）。オーナー承認済み。

## 変更したファイル（2つ。テーマ・カテゴリー構造・既存商品は変更なし）

`local-snapshot-2026-11-15/mu-plugins/` の中：

1. `nexus-catnav-autoclassify.php`
   - **実行タイミング**：`save_post_product` をやめ、WooCommerceが商品のカテゴリーを保存し終えた後に動く `woocommerce_new_product`／`woocommerce_update_product` に変更。管理画面、REST API、WP-CLI、商品発掘システムからの登録のすべてで分類されるようになる
   - **Boots**：「Timberland」というブランド名では分類しない。商品名に Boot／6-Inch／Chukka／Goadome／Field Boot／Euro Hiker などのブーツを示す語があるときだけ
   - **AF1に加えてDunkも**、用途カテゴリー（Running・Basketball・Boots）に自動で入れない
   - **誤分類の訂正**：このプラグインが自動で付けた用途カテゴリーは、ルールに合わなくなったら自動で外す。**人が付けたカテゴリーは絶対に外さない**。最後の末端カテゴリーも外さない
   - **性別の判定**：`mens-sneakers` のような末端カテゴリーだけが付いていても、MEN'Sとして親カテゴリーを補完する
   - **分類できない商品**：`_nx_catnav_needs_review` に理由（`gender-missing`／`leaf-missing`）を記録する。公開は止めない（公開保留は未承認の改善案のため、今回は入れていない）
   - 第1〜第3階層すべてへの付与は維持（ヘッダーがMEN'Sなどの件数を使っているため）
2. `nexus-catnav-redirects.php`
   - 旧URLのページ送り（`/product-category/mens/mens-sneakers/page/2/`）も転送する
   - 並び替えなどの条件（`?orderby=price` など）を引き継ぐ

## 作業手順（Local環境のみ）

### 1. 退避
```bash
MU="$HOME/Local Sites/kaitsuke-shop/app/public/wp-content/mu-plugins"
mkdir -p ~/ahc-qa-reports/backup/mu-plugins-2026-11-15
cp "$MU/nexus-catnav-autoclassify.php" "$MU/nexus-catnav-redirects.php" ~/ahc-qa-reports/backup/mu-plugins-2026-11-15/
```

### 2. 単体テスト（WordPress不要）
```bash
cd ~/nexus-select && git pull
php qa/php-tests/test_catnav.php      # 「OK 28 tests」と出ること
```

### 3. 反映
```bash
cp local-snapshot-2026-11-15/mu-plugins/nexus-catnav-autoclassify.php "$MU/"
cp local-snapshot-2026-11-15/mu-plugins/nexus-catnav-redirects.php "$MU/"
```

### 4. 実環境での確認（WP-CLI、ソケット指定）
一時的な**下書き**商品を1点作り、WooCommerce経由（REST APIや発掘システムと同じ経路）で保存して分類を確かめ、最後に削除します。公開はされません。`.local` 以外では動かないようにしてあります。
```bash
"$PHP" -d mysqli.default_socket="$SOCK" -d pdo_mysql.default_socket="$SOCK" \
  "$WP" eval-file ~/nexus-select/qa/php-tests/local_autoclassify_check.php --path="$SITE"
```
4項目すべて PASS、最後に `Success` と出ること。

### 5. 品質検査
```bash
# 商品データを書き出し直す（qa/README.md 手順1）→
cd ~/nexus-select/qa && python3 -m ahc_qa --config ~/ahc-qa-reports/config.json
```
確認するところ：
- 旧URL転送（CAT_OLD_URL）が0件
- 「Bootsに分類されていますが、商品名にブーツを示す語がありません」（REVIEW）：**以前の「Timberland＝Boots」ルールで付いた可能性がある既存商品**。今回の修正は既存商品の分類を自動では変えないので、外すかどうかはオーナー判断
- 「自動分類できなかった商品」（REVIEW）：一覧をオーナーに報告

### 6. 戻し方
```bash
cp ~/ahc-qa-reports/backup/mu-plugins-2026-11-15/*.php "$MU/"
```

## 報告してほしいこと
手順2・4の結果（PASS／FAIL）、手順5のCRITICAL・HIGH件数と上の2種類のREVIEWの件数。
