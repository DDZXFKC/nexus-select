# AHC VPN v3 監査依頼（ラウンド4）— 2026-11-18

宛先：GPT（設計・監査担当）
対象：`tools/ahc-vpn/` の GLM 修正版（ラウンド4）

## トラックA：AXダンパー修正版

`ahc_vpn_ax_dumper.swift` をラウンド3監査の A-1〜A-4 に沿って修正した。
- A-1：属性値を型付きで出力（Str/Num/Bool/NoValue/Unsupported）。AXEnabled も取得。
- A-2：探索の打切り理由（COMPLETED/MAX_DEPTH/MAX_ELEMENTS/TIMEOUT）と要素数を Summary に出力。
- A-3：AXUIElementSetMessagingTimeout 2秒＋全体30秒の deadline。
- A-4：既定ではシステム設定を開かず、オーナーが手動で開いたVPNペインを読む。open は --open 引数がある時だけ。
実機検証はオーナー帰宅後に監督下で実施予定（手順は iMac のメモに準備済み）。

## トラックB：3モジュール残修正＋モック統合

- status_probe.py：list_utun_interfaces へ改名し utun 名を正規表現で厳密検証、空 stdout を区別。route の interface 欠落・複数を明示エラー化。status 行を解析。共通 deadline と部分取得。出力に unmanaged_vpn=UNKNOWN、source、observed_at、completeness を追加。
- shortcuts_backend.py：結果分類を同一 schema で復活（result_code/command_completed/returncode/effect_unknown/sanitized_error、無効 name と無効 time_budget は REJECTED）。verify_shortcuts で名称の一意性を確認。生 stdout/stderr は返さない。
- preflight.py：profile_status_verified を常に false に固定。shortcuts_registered と診断状態（diagnostic_executable/completed/partial）を分離。
- mock_controller_interface.py：実操作無効のモック統合インターフェースを新規追加。

## 判定してほしいこと

1. トラックA修正版は、監督下の読み取り実証へ進める水準か。
2. トラックB残修正はラウンド3の要求を満たしたか。残る修正必須があれば列挙。
3. モック統合の範囲は妥当か。
4. 実VPNの切替テストは従来どおり承認対象外として扱う。
