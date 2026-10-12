import unittest
from unittest.mock import patch, Mock
from pathlib import Path
import requests
from data_source import fetch_latest, resolve
import pandas as pd
from core import clean, shortlist, growth
from streamlit.testing.v1 import AppTest

class Tests(unittest.TestCase):
    def test_data_integrity(self):
        raw=pd.DataFrame({'Model':['A','B','C'], 'Publication date':['2020-01-01','2021-01-01','2022-01-01'], 'Training compute (FLOP)':[100,200,400], 'Task':['code generation','vision','translation']})
        data=clean(raw)
        self.assertAlmostEqual(growth(data,'Training compute (FLOP)')[1],2,places=6)
        self.assertEqual(shortlist(data,'code').iloc[0]['Model'],'A')
        self.assertTrue(shortlist(data,'[').empty)
        self.assertEqual(data['Record'].tolist(),clean(raw).sort_index()['Record'].tolist())
        self.assertTrue(clean(raw.assign(Parameters=[0,-2,None]))['Parameters'].isna().all())
    def test_refresh_and_fallback(self):
        fetch_latest.clear()
        csv='Model,Publication date\nFirst,2026-01-01\n'
        with patch('data_source.requests.get', return_value=Mock(text=csv, content=csv.encode())) as get:
            first=fetch_latest()
            self.assertEqual(len(first['data']),1)
            fetch_latest()
            self.assertEqual(get.call_count,1)
        csv+='New release,2026-02-01\n'
        fetch_latest.clear()
        with patch('data_source.requests.get', return_value=Mock(text=csv, content=csv.encode())):
            refreshed=fetch_latest()
            self.assertEqual(len(refreshed['data']),2)
            self.assertNotEqual(first['version'],refreshed['version'])
        fetch_latest.clear()
        with patch('data_source.requests.get', side_effect=requests.Timeout):
            failure=fetch_latest()
            self.assertIsNone(failure['data'])
            selected,label=resolve(failure,refreshed)
            self.assertEqual(len(selected['data']),2)
            self.assertIn('Last successful',label)
            selected,label=resolve(failure)
            self.assertFalse(selected['data'].empty)
            self.assertIn('Bundled',label)
        fetch_latest.clear()
        with patch('data_source.requests.get', return_value=Mock(text='bad,columns\n1,2',content=b'bad')):
            self.assertIsNotNone(fetch_latest()['error'])
        fetch_latest.clear()

    @patch('data_source.requests.get')
    def test_pages(self, get):
        fetch_latest.clear()
        text=Path('data/models.csv').read_text()
        get.return_value=Mock(text=text, content=text.encode())
        app=AppTest.from_file('app.py',default_timeout=30).run()
        self.assertEqual(len(app.exception),0)
        app.sidebar.button[0].click().run()
        self.assertEqual(get.call_count,2)
        self.assertEqual(len(app.exception),0)
        for page in ['Explore','Compare','Research assistant','Scenario lab','Watchlist','Data quality & sources']:
            app.sidebar.radio[0].set_value(page).run()
            self.assertEqual(len(app.exception),0, page)
        app.sidebar.radio[0].set_value('Research assistant').run()
        app.text_area[0].set_value('language code generation').run()
        self.assertEqual(len(app.exception),0)
        app.sidebar.radio[0].set_value('Compare').run()
        choices=app.multiselect[-1].options[:2]
        app.multiselect[-1].set_value(choices).run()
        self.assertEqual(len(app.exception),0)
        app.sidebar.text_input[0].set_value('zzzznothingmatches').run()
        self.assertEqual(len(app.exception),0)

if __name__=='__main__': unittest.main()
