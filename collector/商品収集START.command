#!/bin/bash
# スクリプト自身のディレクトリに移動
cd "$(dirname "$0")"

# Pythonスクリプトを実行
python3 ahc_collect.py

# 終了後にウィンドウがすぐ閉じないように入力待ち
echo ""
echo "処理が完了しました。何かキーを押して終了してください..."
read -n 1
