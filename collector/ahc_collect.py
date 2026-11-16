#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import time
import sqlite3
import urllib.request
import urllib.error
from datetime import datetime

# ==========================================
# 設定・定数
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "ahc_data")
RAW_JSON_DIR = os.path.join(DATA_DIR, "raw_json")
DB_PATH = os.path.join(DATA_DIR, "ahc_products.db")
LOCK_FILE = os.path.join(BASE_DIR, "ahc_collect.lock")
REPORT_DIR = os.path.join(BASE_DIR, "reports")

# 収集対象ストア設定 (ストア名, ベースURL, コレクションスラッグ)
# 今回は最小実装として 'all' スラッグを対象とする
TARGET_STORES = [
    {"name": "Shoe Palace", "url": "https://www.shoepalace.com", "slug": "all"},
    {"name": "Kith", "url": "https://kith.com", "slug": "all"},
    {"name": "Patta", "url": "https://pattaclothing.us", "slug": "all"},
    {"name": "Notre", "url": "https://www.notre-shop.com", "slug": "all"}
]

# ==========================================
# ユーティリティ: ロックファイル・ディレクトリ準備
# ==========================================
def setup_directories():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(RAW_JSON_DIR, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)

def acquire_lock():
    if os.path.exists(LOCK_FILE):
        print("[エラー] 既に起動中です (ロックファイルが存在します)。")
        return False
    try:
        with open(LOCK_FILE, 'w') as f:
            f.write(str(os.getpid()))
        return True
    except Exception as e:
        print(f"[エラー] ロックファイルの作成に失敗: {e}")
        return False

def release_lock():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)

# ==========================================
# ユーティリティ: データベース操作
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        store_name TEXT NOT NULL,
        product_id TEXT NOT NULL,
        variant_id TEXT,
        payload TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(store_name, product_id, variant_id)
    )
    """)
    conn.commit()
    conn.close()

def save_to_db(store_name, product):
    product_id = str(product.get("id", ""))
    variants = product.get("variants", [])
    # バリアントIDは最初のものを代表値として使用（1商品1レコードとして保存）
    variant_id = str(variants[0].get("id", "")) if variants else ""

    payload = json.dumps(product, ensure_ascii=False)
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute("""
        INSERT OR IGNORE INTO products (store_name, product_id, variant_id, payload, created_at)
        VALUES (?, ?, ?, ?, ?)
        """, (store_name, product_id, variant_id, payload, created_at))
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        print(f"  [DBエラー] {e}")
        return False
    finally:
        conn.close()

def is_product_exists(store_name, product):
    product_id = str(product.get("id", ""))
    variants = product.get("variants", [])
    variant_id = str(variants[0].get("id", "")) if variants else ""

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    SELECT 1 FROM products WHERE store_name=? AND product_id=? AND variant_id=? LIMIT 1
    """, (store_name, product_id, variant_id))
    result = cur.fetchone() is not None
    conn.close()
    return result

def save_raw_json(store_name, page, data):
    store_dir = os.path.join(RAW_JSON_DIR, store_name.replace(" ", "_"))
    os.makedirs(store_dir, exist_ok=True)
    filepath = os.path.join(store_dir, f"page_{page}.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ==========================================
# 取得ロジック・進捗表示
# ==========================================
def fetch_page(store_url, slug, page):
    endpoint = f"{store_url}/collections/{slug}/products.json"
    params = f"?limit=250&page={page}"
    url = endpoint + params
    
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json'
    })
    
    with urllib.request.urlopen(req, timeout=30) as response:
        if response.status == 200:
            return json.loads(response.read().decode('utf-8'))
        else:
            raise Exception(f"HTTP {response.status}")

def collect_store(store_info):
    store_name = store_info["name"]
    store_url = store_info["url"]
    slug = store_info["slug"]
    
    print(f"\n[{store_name}] 収集を開始します...")
    page = 1
    total_saved = 0
    total_skipped = 0
    
    while True:
        try:
            print(f"  Page {page} を取得中...")
            data = fetch_page(store_url, slug, page)
            products = data.get("products", [])
            
            if not products:
                print(f"  Page {page} に商品がありません。収集を完了します。")
                break
            
            saved_this_page = 0
            skipped_this_page = 0
            
            for product in products:
                if is_product_exists(store_name, product):
                    skipped_this_page += 1
                else:
                    if save_to_db(store_name, product):
                        saved_this_page += 1
            
            save_raw_json(store_name, page, data)
            
            total_saved += saved_this_page
            total_skipped += skipped_this_page
            print(f"  Page {page} 完了: 保存 {saved_this_page}件, スキップ {skipped_this_page}件")
            
            # ページ送りの終了条件 (250件未満なら最終ページと判断)
            if len(products) < 250:
                print(f"  最終ページに到達しました。")
                break
            
            page += 1
            time.sleep(1) # サーバー負荷軽減
            
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"  [情報] Page {page} は404です。最終ページと判断し終了します。")
                break # 修正: 無限ループを防ぐため break を追加
            else:
                raise Exception(f"HTTPエラー: {e.code}")
        except Exception as e:
            raise Exception(f"取得エラー: {e}")
            
    return {"store": store_name, "saved": total_saved, "skipped": total_skipped, "status": "success"}

# レポート出力
# ==========================================
def generate_report(results):
    if not os.path.exists(REPORT_DIR):
        os.makedirs(REPORT_DIR)
        
    today = datetime.now().strftime("%Y%m%d")
    filepath = os.path.join(REPORT_DIR, f"report_{today}.txt")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("=====================================\n")
        f.write(" 商品収集レポート\n")
        f.write(f" 実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=====================================\n\n")
        
        for res in results:
            f.write(f"【{res['store']}】\n")
            f.write(f"  ステータス: {res['status']}\n")
            if res['status'] == 'success':
                f.write(f"  新規保存: {res['saved']}件\n")
                f.write(f"  スキップ: {res['skipped']}件\n")
            else:
                f.write(f"  エラー詳細: {res.get('error', '不明')}\n")
            f.write("\n")
            
    print(f"\n[完了] レポートを生成しました: {filepath}")

# ==========================================
# メイン処理
# ==========================================
def main():
    print("=== 商品収集ツール (最小実装) ===")
    
    # 1. 準備
    setup_directories()
    
    # 2. ロック取得
    if not acquire_lock():
        sys.exit(1)
        
    # 3. DB初期化
    init_db()
    
    results = []
    
    # 4. 各ストアの収集 (エラー隔離)
    for store_info in TARGET_STORES:
        try:
            res = collect_store(store_info)
            results.append(res)
        except Exception as e:
            print(f"\n[エラー隔離] {store_info['name']} の処理中にエラーが発生しました: {e}")
            print("次のストアの処理に進みます...")
            results.append({
                "store": store_info["name"],
                "status": "error",
                "error": str(e)
            })
            continue
            
    # 5. レポート出力
    generate_report(results)
    
    # 6. ロック解除
    release_lock()
    print("\n=== 全ての処理が完了しました ===")

if __name__ == "__main__":
    main()
