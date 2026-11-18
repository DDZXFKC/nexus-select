# AHC VPN 状態取得PoC 実機結果（2026-11-18）

実行：オーナーの実ターミナル（監督下）。ダンパーは `ahc_vpn_ax_dumper`、対象はシステム設定のVPNペイン（オーナーが手動で開いた状態）。
注記：今回実行されたバイナリの出力形式はラウンド3版ダンパー相当（Subrole／Identifierを含む形式）だった。ラウンド4版（型付き値出力）での再実行は今後の課題とする。

## 結果1：AX許可

```
=== AX Trusted: true ===
```

ターミナルへのアクセシビリティ許可が有効で、ダンパーがVPNペインのAXツリーを取得できた。

## 結果2：VPNペインの構造（抜粋）

```
[D8] 0.0.0.2.0.0.0.0 Role: AXStaticText | Value: AHC DE
[D8] 0.0.0.2.0.0.0.2 Role: AXStaticText | Value: 接続解除済み
[D8] 0.0.0.2.0.0.0.4 Role: AXCheckBox | Sub: AXSwitch
[D8] 0.0.0.2.0.0.0.5 Role: AXStaticText | Value: AHC US
[D8] 0.0.0.2.0.0.0.7 Role: AXStaticText | Value: 接続解除済み
[D8] 0.0.0.2.0.0.0.9 Role: AXCheckBox | Sub: AXSwitch
```

Matched Keywords 抽出：

```
[D8] Role: AXStaticText | Value: AHC DE
[D8] Role: AXStaticText | Value: 接続解除済み
[D8] Role: AXStaticText | Value: AHC US
[D8] Role: AXStaticText | Value: 接続解除済み
```

プロファイル名の直後に、そのプロファイルの状態テキストとスイッチが並ぶ構造が確認できた。切断状態については、プロファイル別の状態をAXで構造的に取得できる。

## 結果3：scutil --nc list（実ターミナル）

```
Available network connection services in the current set (*=enabled):
```

見出し行のみで、サービスは0件。オーナーの実ターミナルでも scutil からはNE構成のプロファイルが見えないことが確定した（ラウンド2で「未確認」扱いだった点の確定証拠）。

## 未検証・残課題

- 「接続済み」状態の表記（接続した状態での再ダンプが必要）。
- AXSwitch 自体の値（今回の出力には含まれず、状態の根拠は状態テキスト）。
- ラウンド4版ダンパー（型付き値出力）での再実行と、Agent／Watchdog 文脈での読み取り可否。

## 実行担当の所見

状態取得方式としてAX読み取りは成立する見込みが立った。次はGPTの判定を受けた上で、接続状態での再ダンプを監督下で行い、3状態（接続済み／接続解除済み／遷移中）の識別可否を確定させたい。
