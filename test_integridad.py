"""Pruebas sin red: el proveedor nunca puede relajar una selección solicitada."""
import ast
import json
import re
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

source = ast.parse(Path(__file__).with_name('app.py').read_text())
names = {'con_tf', 'construir_payload', 'escanear'}
functions = [n for n in source.body if isinstance(n, ast.FunctionDef) and n.name in names]
for f in functions:
    f.decorator_list = []
ns = dict(json=json, re=re, HEADERS={}, CAMPOS_API=['close', 'change', 'RSI', 'logoid'],
          CAMPOS={'close': None, 'RSI': None}, TECNICOS={'RSI'})
exec(compile(ast.Module(body=functions, type_ignores=[]), 'app.py', 'exec'), ns)

class Integridad(unittest.TestCase):
    def call(self, payload, responses):
        post = Mock(side_effect=[SimpleNamespace(ok=ok, status_code=200 if ok else 400,
                    text=str(body), json=lambda body=body: body) for ok, body in responses])
        ns['requests'] = SimpleNamespace(post=post, RequestException=RuntimeError)
        result = ns['escanear']('https://example.invalid/scan', json.dumps(payload), '')
        return result, post

    def payload(self, filters=(), order=None, excluded=()):
        return ns['construir_payload'](filters, '60', order, 'desc', 50, excluded)

    def test_unknown_filter_blocks_results(self):
        result, post = self.call(self.payload([('RSI', 'greater', 50)]),
                                 [(False, {'error': 'Unknown field "RSI|60"'})])
        self.assertTrue(result[-1]); self.assertEqual(result[0], []); self.assertEqual(post.call_count, 1)

    def test_unknown_right_operand_blocks(self):
        result, _ = self.call(self.payload([('close', 'greater', 'RSI')]),
                              [(False, {'error': 'Unknown field "RSI|60"'})])
        self.assertTrue(result[-1])

    def test_unknown_sort_blocks(self):
        result, _ = self.call(self.payload(order='RSI'), [(False, {'error': 'Unknown field "RSI|60"'})])
        self.assertTrue(result[-1])

    def test_optional_column_can_be_removed(self):
        result, post = self.call(self.payload(), [(False, {'error': 'Unknown field "logoid"'}),
                                    (True, {'data': [], 'totalCount': 0})])
        self.assertIsNone(result[-1]); self.assertEqual(post.call_count, 2)
        self.assertEqual(result[3], ['logoid'])

    def test_old_exclusions_never_remove_filter_or_sort(self):
        p = self.payload([('RSI', 'greater', 50)], 'RSI', ['RSI'])
        self.assertEqual(p['filter'][0]['left'], 'RSI|60')
        self.assertEqual(p['sort']['sortBy'], 'RSI|60')

    def test_primary_filter_is_preserved(self):
        p = ns['construir_payload']([], '', None, 'desc', 10, ['is_primary'], primarios=True)
        self.assertTrue(any(f['left'] == 'is_primary' for f in p['filter']))

    def test_bad_success_response_is_error(self):
        for body in ([], {}, {'unexpected': 'value'}):
            result, _ = self.call(self.payload(), [(True, body)])
            self.assertTrue(result[-1])

    def test_essential_column_cannot_disappear(self):
        result, _ = self.call(self.payload(), [(False, {'error': 'Unknown field "change"'})])
        self.assertTrue(result[-1])

if __name__ == '__main__':
    unittest.main()
