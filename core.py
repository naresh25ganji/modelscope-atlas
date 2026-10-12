from pathlib import Path
import re
import hashlib
import numpy as np
import pandas as pd

SOURCE = 'https://epoch.ai/data/all_ai_models.csv'
METRICS = ['Training compute (FLOP)', 'Parameters', 'Training compute cost (2023 USD)', 'Training dataset size (total)', 'Training power draw (W)']

def clean(df):
    if 'Model' not in df or 'Publication date' not in df:
        raise ValueError('Dataset must contain Model and Publication date columns.')
    df = df.copy()
    df['Publication date'] = pd.to_datetime(df['Publication date'], errors='coerce', utc=True).dt.tz_localize(None)
    for col in METRICS + ['Training time (hours)']:
        df[col] = pd.to_numeric(df.get(col, pd.Series(index=df.index, dtype=float)), errors='coerce')
        df.loc[df[col] <= 0, col] = np.nan
    for col in ['Organization', 'Domain', 'Model accessibility', 'Confidence', 'Country (of organization)', 'Abstract', 'Link', 'Task', 'Open model weights?']:
        df[col] = df.get(col, pd.Series(index=df.index, dtype=str)).fillna('Unknown').astype(str)
    df = df.dropna(subset=['Model']).reset_index(drop=True)
    df['Year'] = df['Publication date'].dt.year
    identity = df['Model'].astype(str) + '|' + df['Organization'] + '|' + df['Publication date'].astype(str)
    df['Record'] = df['Model'] + ' · ' + df['Organization'] + ' · ' + identity.apply(lambda x: hashlib.sha256(x.encode()).hexdigest()[:12])
    return df

def shortlist(df, query, limit=10):
    words = set(re.findall(r'[a-z0-9]+', query.lower())) - {'a','an','the','for','and','with','model','models','i','want','to','of','best'}
    if not words:
        return df.iloc[:0].copy()
    result = df.copy()
    fields = {'Model':4, 'Domain':3, 'Task':3, 'Abstract':1, 'Organization':2}
    result['Match score'] = 0
    result['Why matched'] = ''
    for field, weight in fields.items():
        count = result[field].str.lower().apply(lambda s: sum(bool(re.search(r'\b'+re.escape(w)+r'\b', s)) for w in words))
        result['Match score'] += count * weight
        result['Why matched'] += count.apply(lambda n: f'{field} ({n} matches); ' if n else '')
    return result[result['Match score'] > 0].sort_values(['Match score','Publication date'], ascending=False).head(limit)

def growth(df, metric):
    annual = df.dropna(subset=['Year',metric]).groupby('Year')[metric].max()
    if len(annual) < 3:
        return None
    slope, intercept = np.polyfit(annual.index.to_numpy(), np.log10(annual.to_numpy()), 1)
    return annual, float(10**slope), float(slope), float(intercept)
