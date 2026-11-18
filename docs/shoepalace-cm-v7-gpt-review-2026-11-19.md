# GPT v7検収・次工程
対象 c58fb671 の報告、code7、汎用参照978行、CONVERSEスコープ2行を直接確認。報告値 v6→v7 MATCHED +226（UGG Kids +224、CONVERSE +2）、MISSING -226、総103834、整合。実行・全ID集合はMuse報告に依存。暫定合格：集計・限定CONVERSE適用。UGG KidsのコードはKids全体の汎用許可のみで年齢区分検査をしていないため、224件の原文年齢区分とC/Y体系の対応証拠を保存・検査し、不一致を隔離する。BIRKENSTOCK 332件は前回指示どおり暫定。MATCHED 68767は全件根拠確定値ではない。
## Women Chuck 70
公式 https://www.converse.com/uk/en/size-chart-guide?id=men にChuck 70のUS MEN/WOMEN対応あり。Men3.5/Women5.5=実箱JP22.5、Men4/Women6=23、Men4.5/Women6.5=23.5。公式LENGTH(CM)欄をラベルとして全サイズに転用しない。対象2商品は保存raw・HTMLの選択肢ラベル、サイズガイド、品番、商品別の明示的なUS Men/Women対応、既存実箱/注文記録を確認。商品名Womens、サイズ範囲だけでは確定不可。必要なら店へ商品URL/品番を添えて選択サイズの体系を問い合わせる（外部送信は承認後）。US Womenと確定した商品IDに限り5.5/6/6.5の実箱根拠を適用、US Menなら3.5/4/4.5の確認済み値のみ。曖昧なら保留。他モデル・Kidsは一般化禁止。輸入適法性とは別。
## 次着手順位
0. 誤適用防止を最優先：BIRKENSTOCK332のEU確認・UGG Kids224の年齢区分確認・CONVERSE2行の実箱根拠ID（画像/記録への参照）・汎用参照の出典URL/適用体系を出力に保存する。現行generic CSVは4列で出典なし、コードのcm_source_urlはscopedのみ。元ブックの5列の出典を維持、参照キーと根拠を紐付ける。汎用/商品単位を一緒に適用する実行手順と状態遷移を記録（現行loaderは2形式を別々に扱うため、合算の実装も検証）。既存成果を作り直さない。
1. HOKA Women 549件を優先。公式チリ https://cl.hoka.com/p/hoka-clifton-11-hombre-frost-black/ に女性表の対象モデル名が明記された。Clifton10/11・Rincon5・Arahi8/9・Challenger8 はUS5=21.5、Bondi9・Speedgoat7・Gaviota6・Transport・Torrent4・Rincon4・Mach7・Kaha3 はUS5=22。両表US4.5〜11、0.5刻み。該当する女性モデル/世代/市場/サイズ体系に限定して商品ID別参照を生成。旧モデルは名称が似ていても適用しない。前回のClifton11=22の保留値を使用しない。公式表の見出しを保存。
2. UGG大人Women482/Men203（v6時点、v7で不変報告）を公式表で確認。商品タイプ・男女・モデル差を先に集計。同一公式表適用が確認できればブランド区分共通で再利用、未照合84行の再投入は禁止。UGG Kids残16の複合サイズは個別根拠のみ。
3. CONVERSE Women Chuck70の2商品を上記手順で確認。残りCONVERSE Men/Kids等は実箱や公式JPラベル資料の確保ができるものだけ。オーナー表41行を一括適用しない。
4. REEBOK、VEJA、VANS、NEWBALANCE等は最新MISSINGをブランド/区分/モデル/サイズ体系/サイズ原文/在庫有無別に集計し、少数の根拠で多く解消できるものから。公式表未掲載サイズは外挿不可。ADIDAS Kids約2073は足長しかない現資料で埋めず、公式JPラベル資料が新たに確認できない限り調査保留。足長は別項目。未確認を理由に他の修正層・業務接続を停止しない。
## 次回受入
v7を保全しv8を別出力。103834件のvariant_id集合/重複、状態遷移、MATCHED根拠別（暫定を分離）、在庫ありMISSING、出典付き件数、再現性、原本不変。EU/UGG年齢/CONVERSE体系の不一致はMISSINGに戻す。確認済みデータの減少を不合格としない。全店PythonはGPT未実行。価格・本番変更なし。オーナー操作不要。
