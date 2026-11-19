#!/usr/bin/env python3
"""Shoe Palace color decomposition full run (offline candidate generation).
Design: docs/color-components-sheet-design-gpt-2026-11-19.md (70ee0596)
Review conditions: docs/color-fixture-phase2-gpt-review-2026-11-19.md (c51beeec)
Outputs are candidates: DRAFT/UNKNOWN/CONFLICT preserved, nothing confirmed.
"""
import csv, json, glob, re, unicodedata, hashlib, sys
from collections import Counter, defaultdict

BASE = '/home/hatch/workspace'
OUT = f'{BASE}/color-fullrun-2026-11-19'
SID_PRODUCTS = f'{BASE}/sp-fullstore/out-v8-a/products.csv'

# ---------- load palette from theme main.js ----------
src = open(f'{BASE}/theme-fix6/main.js').read()
PALETTE = {}
BASIC = {}
EXACT = {}
for name, store in [('BASIC_COLORS', BASIC), ('EXACT_COLORS', EXACT)]:
    m = re.search(name + r'\s*=\s*\{(.*?)\n\}', src, re.S)
    for k, v in re.findall(r"'([^']+)'\s*:\s*'([^']+)'", m.group(1)):
        store[k] = v
        PALETTE.setdefault(k, v)

# ---------- load sheet master (source of truth for existing tokens) ----------
sheet_master = json.load(open(f'{BASE}/color-fullrun-2026-11-19-sheet-master.json'))
MCOLS = sheet_master[0]
existing_master = [dict(zip(MCOLS, r + [''] * (len(MCOLS) - len(r)))) for r in sheet_master[1:]]
sheet_products = json.load(open(f'{BASE}/color-fullrun-2026-11-19-sheet-products.json'))
PCOLS = sheet_products[0]
existing_keys = {r[2] for r in sheet_products[1:] if len(r) > 2 and r[2]}

# ---------- load products (v8) + raw tags ----------
with open(SID_PRODUCTS, newline='', encoding='utf-8-sig') as f:
    products = list(csv.DictReader(f))
raw_by_id = {}
for fn in sorted(glob.glob(f'{BASE}/sp-fullstore/raw/page_*.json')):
    d = json.load(open(fn))
    for p in d.get('products', []):
        raw_by_id[str(p['id'])] = p

def norm(tok):
    t = unicodedata.normalize('NFKC', tok).casefold()
    return re.sub(r'\s+', ' ', t).strip()

WORD_FAMILY = {
    'black': 'black', 'white': 'white', 'grey': 'grey', 'gray': 'grey',
    'red': 'red', 'blue': 'blue', 'navy': 'blue', 'green': 'green',
    'pink': 'pink', 'brown': 'brown', 'beige': 'beige', 'yellow': 'yellow',
    'orange': 'orange', 'purple': 'purple', 'gold': 'gold', 'silver': 'silver',
    'olive': 'olive', 'burgundy': 'burgundy', 'maroon': 'maroon', 'tan': 'tan',
    'khaki': 'khaki', 'cream': 'cream', 'anthracite': 'anthracite',
    'gum': 'gum', 'sail': 'sail', 'violet': 'purple', 'lilac': 'purple',
    'lavender': 'purple', 'mint': 'green',
}
BUYMA_NAME = {
    'black': 'ブラック', 'white': 'ホワイト', 'grey': 'グレー', 'red': 'レッド',
    'blue': 'ブルー', 'green': 'グリーン', 'pink': 'ピンク', 'brown': 'ブラウン',
    'beige': 'ベージュ', 'yellow': 'イエロー', 'orange': 'オレンジ',
    'purple': 'パープル', 'gold': 'ゴールド', 'silver': 'シルバー',
}
JA_WORD = {
    'black': 'ブラック', 'white': 'ホワイト', 'red': 'レッド', 'blue': 'ブルー',
    'navy': 'ネイビー', 'grey': 'グレー', 'gray': 'グレー', 'green': 'グリーン',
    'pink': 'ピンク', 'brown': 'ブラウン', 'beige': 'ベージュ', 'yellow': 'イエロー',
    'orange': 'オレンジ', 'purple': 'パープル', 'gold': 'ゴールド', 'silver': 'シルバー',
    'cream': 'クリーム', 'olive': 'オリーブ', 'burgundy': 'バーガンディ',
    'maroon': 'マルーン', 'tan': 'タン', 'khaki': 'カーキ', 'light': 'ライト',
    'dark': 'ダーク', 'midnight': 'ミッドナイト', 'metallic': 'メタリック',
    'university': 'ユニバーシティ', 'core': 'コア', 'cloud': 'クラウド',
    'hyper': 'ハイパー', 'armory': 'アーモリー', 'smoke': 'スモーク',
    'bright': 'ブライト', 'royal': 'ロイヤル', 'concord': 'コンコルド',
    'phantom': 'ファントム', 'gum': 'ガム', 'sail': 'セイル',
    'anthracite': 'アンスラサイト', 'summit': 'サミット', 'team': 'チーム',
    'triple': 'トリプル', 'vintage': 'ヴィンテージ', 'soft': 'ソフト',
    'pale': 'ペール', 'deep': 'ディープ', 'vivid': 'ヴィヴィッド',
    'neon': 'ネオン', 'pastel': 'パステル', 'ivory': 'アイボリー',
    'charcoal': 'チャコール', 'taupe': 'トープ', 'mauve': 'モーヴ',
    'lilac': 'ライラック', 'lavender': 'ラベンダー', 'mint': 'ミント',
    'teal': 'ティール', 'turquoise': 'ターコイズ', 'coral': 'コーラル',
    'peach': 'ピーチ', 'rose': 'ローズ', 'wine': 'ワイン', 'camel': 'キャメル',
    'sand': 'サンド', 'stone': 'ストーン', 'bone': 'ボーン', 'ash': 'アッシュ',
    'sky': 'スカイ', 'sea': 'シー', 'forest': 'フォレスト', 'moss': 'モス',
    'clay': 'クレイ', 'rust': 'ラスト', 'mustard': 'マスタード',
    'plum': 'プラム', 'grape': 'グレープ', 'lemon': 'レモン', 'lime': 'ライム',
    'aqua': 'アクア', 'denim': 'デニム', 'indigo': 'インディゴ',
    'crimson': 'クリムゾン', 'scarlet': 'スカーレット', 'fuchsia': 'フューシャ',
    'magenta': 'マゼンタ', 'violet': 'バイオレット', 'cobalt': 'コバルト',
    'emerald': 'エメラルド', 'jade': 'ジェイド', 'pearl': 'パール',
    'opal': 'オパール', 'bronze': 'ブロンズ', 'copper': 'コッパー',
    'chrome': 'クローム', 'platinum': 'プラチナ', 'ecru': 'エクリュ',
    'natural': 'ナチュラル', 'multi': 'マルチ', 'clear': 'クリア',
    'stardust': 'スターダスト', 'fizz': 'フィズ', 'seafoam': 'シーフォーム',
    'armory': 'アーモリー', 'regal': 'リーガル', 'wheat': 'ウィート',
    'chestnut': 'チェスナット', 'sora': 'ソラ', 'san': 'サン',
}

def ja_name(token_norm):
    words = token_norm.split(' ')
    if all(w in JA_WORD for w in words):
        return ''.join(JA_WORD[w] for w in words)
    return ''

def token_family(token_norm):
    """return (family, family_status, basis)"""
    if token_norm in BASIC:
        fam = WORD_FAMILY.get(token_norm, token_norm)
        return fam, 'CONFIRMED', 'BASIC_WORD'
    words = token_norm.split(' ')
    for w in reversed(words):
        if w in WORD_FAMILY:
            return WORD_FAMILY[w], 'DRAFT', 'CONTAINED_BASIC_WORD'
    return '', 'UNKNOWN', 'UNRESOLVED'

def generate():
    # ---- tokenize all colorways, gather stats ----
    token_stats = {}  # norm -> {original, count, instock, brands Counter, example}
    prod_tokens = {}  # pid -> [ (original, norm) ]
    for p in products:
        pid = p['product_id']
        cw = (p['color_name'] or '').strip()
        toks = []
        if cw:
            for part in cw.split('/'):
                o = part.strip()
                if o == '':
                    continue
                n = norm(o)
                toks.append((o, n))
                st = token_stats.setdefault(n, {'original': o, 'count': 0, 'instock': 0,
                                                'brands': Counter(), 'example': pid})
                st['count'] += 1
                if p['in_stock'] == 'True':
                    st['instock'] += 1
                st['brands'][p['brand']] += 1
        prod_tokens[pid] = toks

    # ---- master: existing + new ----
    master = { (m['scope_type'], m['scope_key'], m['token_normalized']): m for m in existing_master }
    existing_norms = {m['token_normalized'] for m in existing_master}
    new_common, new_brand = [], []
    for n, st in sorted(token_stats.items()):
        if n in existing_norms:
            continue
        fam, fstat, basis = token_family(n)
        in_pal = n in PALETTE
        brands = st['brands']
        if in_pal or basis != 'UNRESOLVED':
            scope, skey = 'COMMON', '*'
        elif len(brands) == 1:
            scope, skey = 'BRAND', next(iter(brands))
        else:
            scope, skey = 'COMMON', '*'
        row = {
            'color_id': '', 'scope_type': scope, 'scope_key': skey,
            'token_normalized': n, 'token_original': st['original'],
            'name_ja': ja_name(n), 'family_internal': fam,
            'display_hex': PALETTE.get(n, ''),
            'family_status': fstat,
            'hex_status': 'DRAFT' if n in PALETTE else 'UNKNOWN',
            'buyma_family_id': '',
            'buyma_family_name': BUYMA_NAME.get(fam, '') if fstat != 'UNKNOWN' else '',
            'buyma_master_version': '',
            'source_type': 'PALETTE_CANDIDATE' if in_pal else basis,
            'source_ref': 'theme/main.js palette' if in_pal else '全件自動分解 2026-11-19',
            'checked_at': '2026-11-19',
            'review_note': '全件処理で自動生成した候補。確定はGPT検収後' + ('' if scope == 'COMMON' else f'（出現ブランド {skey} のみ）'),
            'active': 'TRUE',
        }
        (new_common if scope == 'COMMON' else new_brand).append(row)
    new_common.sort(key=lambda r: r['token_normalized'])
    new_brand.sort(key=lambda r: (r['scope_key'], r['token_normalized']))
    # 採番は一元管理（2026-11-19 GPT再検収 0bb3ab5b の再発防止指示）。
    # COMMON／BRANDで範囲を分けると範囲同士が衝突するため、既存IDの最大値から
    # 通し番号で採番し、全体の一意性をassertで保証する。
    def _idnum(cid):
        try:
            return int(str(cid).split('-')[1])
        except Exception:
            return 0
    next_id = max((_idnum(m['color_id']) for m in existing_master), default=0) + 1
    for r in new_common + new_brand:
        r['color_id'] = f'C-{next_id}'
        next_id += 1
    _all_ids = [m['color_id'] for m in existing_master] + [r['color_id'] for r in new_common + new_brand]
    assert len(_all_ids) == len(set(_all_ids)), 'color_id duplication detected'
    for r in new_common + new_brand:
        master[(r['scope_type'], r['scope_key'], r['token_normalized'])] = r

    def lookup(n, brand):
        m = master.get(('BRAND', brand, n))
        if m:
            return m
        return master.get(('COMMON', '*', n))

    # ---- product rows ----
    rows = []
    reclass = []
    neg = {'multi': [], 'nocolor': [], 'main_only': [], 'unknown_hex': [],
           'unparseable': [], 'same_token_multi_brand': []}
    for n, st in token_stats.items():
        if len(st['brands']) > 1:
            neg['same_token_multi_brand'].append((n, st['count'], dict(st['brands'])))
    summary = Counter()
    for p in products:
        pid = p['product_id']
        raw = raw_by_id.get(pid, {})
        tags = raw.get('tags') or []
        color_tags = [t for t in tags if t.startswith('Color_')]
        main_tags = [t for t in tags if t.startswith('MAIN_COLOR_')]
        style = next((t[6:] for t in tags if t.startswith('STYLE_')), '')
        cw = (p['color_name'] or '').strip()
        toks = prod_tokens[pid]
        notes = []
        # colorway status mapping
        v8 = p['color_name_status']
        if v8 == 'TITLE_CANDIDATE':
            cw_status = 'CONFIRMED_BY_TITLE_RULE'
            notes.append('v8元ステータスTITLE_CANDIDATEをGPT指示によりCONFIRMED_BY_TITLE_RULEとして処理')
        elif cw == '':
            cw_status = 'UNKNOWN'
        else:
            cw_status = v8
        # components
        comp_objs, comp_masters = [], []
        for o, n in toks:
            m = lookup(n, p['brand'])
            comp_objs.append({'position': len(comp_objs) + 1, 'token_original': o,
                              'color_id': m['color_id'] if m else None})
            comp_masters.append(m)
        fams = []
        for m in comp_masters:
            if m and m['family_internal'] and m['family_internal'] not in fams:
                fams.append(m['family_internal'])
        if not toks:
            comp_status = 'UNKNOWN'
            neg['unparseable'].append(pid)
        elif all(m and m['family_status'] == 'CONFIRMED' for m in comp_masters):
            comp_status = 'CONFIRMED'
        elif any(m for m in comp_masters):
            comp_status = 'PARTIAL'
        else:
            comp_status = 'UNKNOWN'
        # main family
        main_fam, main_src, main_stat = '', '', 'UNKNOWN'
        buyma_name, buyma_stat = '', 'UNKNOWN'
        color_fams = {t[6:].casefold() for t in color_tags}
        main_raw = main_tags[0][11:] if main_tags else ''
        if main_tags:
            main_src = 'STORE_MAIN_TAG'
            mf = main_raw.casefold()
            if mf == 'nocolor':
                main_stat = 'UNKNOWN'
                notes.append('MAIN_COLOR_NOCOLORのため主色を付けない')
                neg['nocolor'].append(pid)
            elif not color_tags and not cw:
                main_stat = 'UNKNOWN'
                notes.append('MAINタグのみで色名なし。主色を捏造しない')
                neg['main_only'].append(pid)
            elif not color_tags:
                main_fam = WORD_FAMILY.get(mf, mf)
                main_stat = 'DRAFT'
                notes.append('Colorタグなし・MAINタグのみ（MAINのみ分類）')
                neg['main_only'].append(pid)
            elif mf in color_fams:
                main_fam = WORD_FAMILY.get(mf, mf)
                main_stat = 'TAG_SUPPORTED'
            elif mf in fams:
                main_fam = mf
                main_stat = 'DRAFT'
                notes.append('タグ集合に主色なし→粗分類差（色名の系統と主色タグが整合）')
                reclass.append([pid, p['title_original'], cw, main_raw,
                                json.dumps(color_tags), 'TAG_SET_INCOMPLETE_COARSE'])
            else:
                main_stat = 'CONFLICT'
                notes.append('主色タグがColor集合・色名系統のどちらとも一致しない→真の矛盾候補として保留')
                reclass.append([pid, p['title_original'], cw, main_raw,
                                json.dumps(color_tags), 'TRUE_CONFLICT_CANDIDATE'])
        else:
            if len(fams) == 1 and toks:
                main_fam = fams[0]
                main_src = 'SOLE_FAMILY'
                main_stat = 'CONFIRMED' if comp_status == 'CONFIRMED' else 'DRAFT'
        # BUYMA
        if main_stat == 'CONFLICT':
            buyma_stat = 'HOLD_CONFLICT'
        elif main_fam:
            buyma_name = BUYMA_NAME.get(main_fam, '')
            buyma_stat = 'DRAFT_MAIN_FAMILY' if buyma_name else 'UNKNOWN'
        elif len(fams) >= 2:
            buyma_name = 'マルチカラー'
            buyma_stat = 'DRAFT_MULTI_CANDIDATE'
        # swatch
        hexes = [(m['display_hex'] if m else '') for m in comp_masters[:3]]
        hexes += [''] * (3 - len(hexes))
        if not toks:
            sw_stat = 'UNKNOWN'
        elif all(hexes[i] for i in range(min(3, len(toks)))) and all(
                comp_masters[i]['family_status'] == 'CONFIRMED' for i in range(min(3, len(toks)))):
            sw_stat = 'CONFIRMED'
        else:
            sw_stat = 'DRAFT'
        if any(t[1] == 'multi' for t in toks):
            neg['multi'].append(pid)
        if toks and any(not (m and m['display_hex']) for m in comp_masters):
            neg['unknown_hex'].append(pid)
        rows.append({
            'shop_code': 'SP', 'market': 'US', 'supplier_product_id': pid,
            'supplier_color_key': 'single', 'brand_id': p['brand'], 'style_code': style,
            'colorway_original': cw, 'colorway_ja': '',
            'colorway_source_type': 'TITLE_PARENTHESIS' if cw else 'NONE',
            'colorway_status': cw_status,
            'components_json': json.dumps(comp_objs, ensure_ascii=False),
            'component_count': str(len(toks)), 'component_status': comp_status,
            'store_color_tags_json': json.dumps(color_tags),
            'store_main_color_tags_json': json.dumps(main_tags),
            'main_family_internal': main_fam, 'main_family_source': main_src,
            'main_family_status': main_stat, 'source_url': p['source_url'],
            'observed_at': '2026-11-19 (v8出力・収集済みraw)', 'raw_ref': 'sp-fullstore/out-v8-a + raw',
            'rule_version': 'COLOR-DESIGN-2026-11-19 v1 / GPT phase2 c51beeec',
            'review_note': '。'.join(notes),
            'swatch_hex_1': hexes[0], 'swatch_hex_2': hexes[1], 'swatch_hex_3': hexes[2],
            'swatch_status': sw_stat, 'buyma_family_id': '', 'buyma_family_name': buyma_name,
            'buyma_status': buyma_stat, 'search_families_json': json.dumps(fams),
            '_preserve': pid in existing_keys,
        })
        summary[f'component_status:{comp_status}'] += 1
        summary[f'main_family_status:{main_stat}'] += 1
        summary[f'buyma_status:{buyma_stat}'] += 1
        summary[f'swatch_status:{sw_stat}'] += 1
        summary[f'colorway_status:{cw_status}'] += 1
        summary[f'component_count:{len(toks)}'] += 1
        tagcls = ('both' if color_tags and main_tags else 'color_only' if color_tags
                  else 'main_only' if main_tags else 'neither')
        summary[f'tag_class:{tagcls}'] += 1

    new_master_rows = new_common + new_brand
    unresolved = []
    for (scope, skey, n), m in master.items():
        st = token_stats.get(n)
        if not st:
            continue
        if m['family_status'] in ('UNKNOWN', 'DRAFT') or m['hex_status'] != 'APPROVED_APPROX':
            unresolved.append({
                'token_original': m['token_original'], 'token_normalized': n,
                'scope_type': scope, 'scope_key': skey, 'color_id': m['color_id'],
                'family_internal': m['family_internal'], 'family_status': m['family_status'],
                'display_hex': m['display_hex'], 'hex_status': m['hex_status'],
                'product_count': st['count'], 'in_stock_count': st['instock'],
                'brands': json.dumps(dict(st['brands']), ensure_ascii=False),
                'example_product_id': st['example'],
            })
    unresolved.sort(key=lambda r: (-r['product_count'], r['token_normalized']))
    return rows, new_master_rows, unresolved, reclass, neg, summary, token_stats

def digest(rows, masters):
    h = hashlib.sha256()
    for r in rows:
        h.update(json.dumps(r, sort_keys=True, ensure_ascii=False).encode())
    for m in masters:
        h.update(json.dumps(m, sort_keys=True, ensure_ascii=False).encode())
    return h.hexdigest()

def main():
    rows1, masters1, unres1, reclass1, neg1, summary1, stats1 = generate()
    rows2, masters2, unres2, reclass2, neg2, summary2, stats2 = generate()
    h1, h2 = digest(rows1, masters1), digest(rows2, masters2)
    assert h1 == h2, 'rerun mismatch'
    with open(f'{OUT}/product_color_full.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=PCOLS)
        w.writeheader()
        for r in rows1:
            w.writerow({k: r.get(k, '') for k in PCOLS})
    with open(f'{OUT}/color_master_new.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=MCOLS)
        w.writeheader()
        for m in masters1:
            w.writerow({k: m.get(k, '') for k in MCOLS})
    with open(f'{OUT}/unresolved_tokens.csv', 'w', newline='') as f:
        cols = ['token_original', 'token_normalized', 'scope_type', 'scope_key', 'color_id',
                'family_internal', 'family_status', 'display_hex', 'hex_status',
                'product_count', 'in_stock_count', 'brands', 'example_product_id']
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(unres1)
    with open(f'{OUT}/reclass_inconsistency.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['product_id', 'title', 'colorway', 'main_tag', 'color_tags', 'class'])
        w.writerows(reclass1)
    summary = {
        'input_products': len(products),
        'generated_rows': len(rows1),
        'preserved_existing_keys': sum(1 for r in rows1 if r['_preserve']),
        'new_rows_to_append': sum(1 for r in rows1 if not r['_preserve']),
        'existing_master_tokens': len(existing_master),
        'new_master_tokens': len(masters1),
        'unique_colorway_tokens': len(stats1),
        'rerun_hash': h1, 'rerun_match': True,
        'counts': dict(summary1),
        'reclass_counts': dict(Counter(r[5] for r in reclass1)),
        'negative_tests': {k: {'count': len(v), 'examples': v[:5]} for k, v in neg1.items()},
    }
    json.dump(summary, open(f'{OUT}/summary.json', 'w'), ensure_ascii=False, indent=1)
    print(json.dumps(summary, ensure_ascii=False, indent=1))

if __name__ == '__main__':
    main()
