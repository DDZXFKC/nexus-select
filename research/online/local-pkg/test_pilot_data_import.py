"""Regression checks for the GLM quarantine adapter with the handed-over data."""
import csv
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from pilot_data_import import audit, compare_csv, load_json, validate, FILES

FIXTURES = Path(__file__).with_name('glm-pilot-data')


class PilotDataTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.main = load_json((FIXTURES / 'candidates.json').read_text(encoding='utf-8-sig'))
        self.discover = load_json((FIXTURES / 'discover_test.json').read_text(encoding='utf-8-sig'))
        self.csv_text = (FIXTURES / 'candidates.csv').read_bytes().decode('utf-8-sig')

    def test_real_data(self):
        out = self.root / 'out'
        result = audit(FIXTURES, out)
        self.assertTrue(result['csv_json_equivalent'])
        self.assertEqual(result['csv_candidates'], 8)
        self.assertEqual(result['pilot']['reference_claims'], 145)
        self.assertEqual(result['discover_test']['reference_claims'], 282)
        self.assertFalse(result['discover_merged_into_pilot'])
        self.assertEqual(result['pilot']['buyma_fallback_candidate_ids'], ['AHC-007', 'AHC-008'])
        self.assertEqual(result['discover_test']['common_buyma_listing_keys_across_all_candidates'], 20)
        for label, filename, decision_file, original in (
            ('pilot', 'report_claims.json', 'decisions.json', self.main),
            ('discover_test', 'discover_test_claims.json', 'discover_test_decisions.json', self.discover),
        ):
            claims = json.loads((out / filename).read_text(encoding='utf-8'))
            decisions = json.loads((out / decision_file).read_text(encoding='utf-8'))
            self.assertEqual(len(claims), len(original))
            for item, row, decision in zip(claims, original, decisions):
                reported = item['report_claims']
                restored = dict(reported['raw_candidate'], references=[r['raw_reference'] for r in reported['references']])
                self.assertEqual(restored, row)
                self.assertEqual(item['offers'], [])
                self.assertEqual(item['references'], [])
                self.assertEqual(item['cost_inputs'], {})
                self.assertNotIn('style_code', item['candidate'])
                self.assertTrue(all(r['status'] == 'UNVERIFIED_GLM_CLAIM' for r in reported['references']))
                self.assertEqual(decision['decision'], 'HOLD')
                self.assertFalse(decision['review_ready'])
                self.assertFalse(decision['approved_for_import'])
                self.assertIsNone(decision['profit_jpy'])
            self.assertEqual(result[label]['hold'], 8)
            for key in ('verified_offers', 'verified_sales', 'verified_profits', 'approved_for_import', 'published'):
                self.assertEqual(result[label][key], 0)
        with (out / 'candidate_watchlist.csv').open(encoding='utf-8-sig', newline='') as f:
            watchlist = list(csv.DictReader(f))
        self.assertEqual(len(watchlist), 8)
        self.assertTrue(all(r['verified_buy_price'] == '' and r['verified_profit_jpy'] == '' and r['verified_stock'] == 'UNKNOWN' for r in watchlist))

    def test_replay(self):
        a, b = self.root / 'a', self.root / 'b'
        self.assertEqual(audit(FIXTURES, a), audit(FIXTURES, b))
        self.assertEqual({p.name for p in a.iterdir()}, {p.name for p in b.iterdir()})
        for p in a.iterdir():
            self.assertEqual(p.read_bytes(), (b / p.name).read_bytes())

    def test_no_overwrite(self):
        out = self.root / 'out'
        out.mkdir()
        sentinel = out / 'sentinel'
        sentinel.write_text('keep')
        with self.assertRaises(FileExistsError):
            audit(FIXTURES, out)
        self.assertEqual(sentinel.read_text(), 'keep')
        self.assertEqual(list(out.iterdir()), [sentinel])

    def test_duplicate_candidate(self):
        with self.assertRaises(ValueError):
            validate(self.main + [self.main[0]])

    def test_duplicate_json_key(self):
        with self.assertRaises(ValueError):
            load_json('{"id":"AHC-001","id":"AHC-002"}')

    def test_reference_schema(self):
        self.main[0]['references'][0].pop('observed_at')
        with self.assertRaises(ValueError):
            validate(self.main)

    def test_csv_price_mismatch(self):
        self.main[0]['buy_price'] += 1
        with self.assertRaises(ValueError):
            compare_csv(self.csv_text, self.main)

    def test_csv_sources_mismatch(self):
        self.main[0]['sources'].append('unexpected')
        with self.assertRaises(ValueError):
            compare_csv(self.csv_text, self.main)

    def test_csv_reference_mismatch(self):
        self.main[0]['references'][0]['price_jpy'] += 1
        with self.assertRaises(ValueError):
            compare_csv(self.csv_text, self.main)

    def test_invalid_input_creates_no_output(self):
        inputs = self.root / 'input'
        inputs.mkdir()
        for filename in FILES:
            shutil.copyfile(FIXTURES / filename, inputs / filename)
        self.main[0]['buy_price'] += 1
        (inputs / 'candidates.json').write_text(json.dumps(self.main, ensure_ascii=False), encoding='utf-8')
        out = self.root / 'out'
        with self.assertRaises(ValueError):
            audit(inputs, out)
        self.assertFalse(out.exists())


if __name__ == '__main__':
    unittest.main()
