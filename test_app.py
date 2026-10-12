import unittest
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
    def test_pages(self):
        app=AppTest.from_file('app.py',default_timeout=30).run()
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
