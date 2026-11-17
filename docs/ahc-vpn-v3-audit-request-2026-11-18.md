# AHC VPN v3 第1弾コードの監査依頼（GPT宛・2026-11-18）

オーナー判断で、v3 の実装は GLM が担当することになった。設計は GPT の v3 案どおり。GPT には監査役としてレビューをお願いしたい。

## 対象
GitHub integration/grok-review、コミット 931ced8b で登録した3ファイル：
- tools/ahc-vpn/shortcuts_backend.py
- tools/ahc-vpn/status_probe.py
- tools/ahc-vpn/preflight.py

## 僕（Muse）が気づいた懸念3点（検証してほしい）
1. **status_probe の netstat 解析**：`get_default_gateway_interface()` が default 行の `parts[5]` をインターフェース名としている。macOS の `netstat -rn` の default 行は「default <gateway> <flags> <netif>」の並びで、インターフェースは parts[3]（または末尾）のはず。parts[5] は誤りではないか。len(parts) >= 6 の条件も、通常の default 行では満たさない可能性がある。
2. **DISCONNECTED 判定**：`ifconfig -l` は VPN 未接続でも utun インターフェースを列挙する（存在するが無効なものを含む）。そのため `probe_status()` は未接続でも utun が見つかり、curl 確認に失敗して UNKNOWN を返しがちではないか。デフォルトルートが utun でない場合は、その時点で DISCONNECTED と判定するのが正しいのではないか（GPT の検証ステップ5「DE・US・未接続を正確に区別」の合格条件に直結する）。
3. **connect 直後の probe のタイミング**：`shortcuts_backend.connect()` はショートカット実行直後に1回だけ probe する。IKEv2 の接続確立には数秒かかるため、確立前に probe して UNKNOWN → 失敗扱いになりやすい。GPT の設計にあった wait()（状態が一致するまで一定時間ポーリングする仕組み）をバックエンド側に持つべきではないか。

## その他に見てほしい点
- v2 の安全設計（リース・watchdog・arm・読み取り専用デフォルト）との統合時に問題になりそうな設計（例外の握りつぶし、戻り値の形式など）があれば指摘してほしい。
- preflight.py の `sys.path.insert(0, '.')` は実行文脈依存で壊れやすい。agent から呼ばれる形として適切か。

## 返し方
- 問題があれば、GLM への修正指示としてそのまま渡せる形（対象ファイル・対象箇所・修正内容・理由）で返してほしい。
- 問題がなければ、その旨と、次工程（controller.py のインターフェース変更＋統合テスト）へ進めてよいかを返してほしい。
