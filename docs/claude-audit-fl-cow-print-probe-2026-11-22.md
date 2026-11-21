# Claude 監査：FL Cow Print 画像確認ワークフローの判定ミス（2026-11-22 05:06 JST）

対象：87f59a5 `.github/workflows/fl-cow-print-source-probe.yml`

- 画像の種類を判定する箇所が `payload.startswith(b'\\x89PNG\\r\\n\\x1a\\n')` のように、バックスラッシュが 2 つになっている。
  - YAML のブロック（`|`）と、クォート付きのヒアドキュメント（`<<'PY'`）の中ではエスケープが外れない。
  - そのため Python は `b'\\x89PNG...'` をそのまま受け取り、「バックスラッシュ・x・8・9…」という文字の並びと比べてしまう。
  - JPEG（`b'\\xff\\xd8'`）も同じ。
- 結果：本物の PNG や JPEG でも一致せず、必ず `detected=OTHER` と出る（WEBP の判定は `b'RIFF'` なので正しく動く）。
- 直し方：`b'\x89PNG\r\n\x1a\n'`、`b'\xff\xd8'` のように、バックスラッシュを 1 つにする。
- Claude 側の確認：`b'\\x89PNG'` は 8 バイトの文字列になり、先頭は `b'\\x89'` で PNG の署名と一致しないことを、手元で確かめた。
