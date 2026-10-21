#!/usr/bin/env python3
"""Tests of the build tools' border rule (standard library only).

  python3 tools/test_tools.py
"""
import csv
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_border  # noqa: E402
import building_stats as BS  # noqa: E402

# a test border: a square around Praia, about 2.2 km a side
SQUARE = 'POLYGON((-23.55 14.90,-23.53 14.90,-23.53 14.92,-23.55 14.92,-23.55 14.90))'
COLS = ['src', 'bid', 'muni', 'lon', 'lat', 'area', 'perim', 'tags', 'h', 'cats', 'cid', 'ckind', 'cname', 'carea', 'gates', 'wkt']


class BorderDecides(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.mkdtemp()
        with open(os.path.join(self.work, 'border.wkt'), 'w', encoding='utf-8') as f:
            f.write(SQUARE + '\n')

    def tearDown(self):
        shutil.rmtree(self.work)

    def test_footprints_across_the_border_are_dropped(self):
        rows = [('inside', 14.91, -23.54), ('within 300 m', 14.91, -23.53 + 200 / 107600),
                ('1 km out', 14.91, -23.53 + 1000 / 107600), ('far', 15.50, -27.00)]
        path = os.path.join(self.work, 'features.csv')
        with open(path, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(COLS)
            for bid, lat, lon in rows:
                w.writerow(['osm', bid, 'CV-PR', lon, lat, 80, 36, '', '', '', '', '', '', '', '', ''])
        kept = [r['bid'] for r in BS.load(path)]
        self.assertEqual(kept, ['inside', 'within 300 m'])

    def test_simplified_outline_measures_its_deviation(self):
        # a wavy edge: simplification removes the wiggles and says by how much
        pts = [(-23.55 + i * 0.0002, 14.90 + (0.0002 if i % 2 else 0)) for i in range(101)]
        ring = pts + [(-23.53, 14.92), (-23.55, 14.92), pts[0]]
        wkt = 'POLYGON((' + ','.join(f'{x} {y}' for x, y in ring) + '))'
        f = build_border.build(wkt)
        p = f['properties']
        self.assertLess(p['pointsShipped'], p['pointsFull'])
        self.assertGreater(p['deviationM'], 15)
        self.assertLessEqual(p['deviationM'], build_border.TOLERANCE_M + 1)


if __name__ == '__main__':
    unittest.main()
