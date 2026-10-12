"""Cached live data checks with explicit freshness and failure metadata."""
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
import hashlib

import pandas as pd
import requests
import streamlit as st
from core import SOURCE, clean

REFRESH_SECONDS = 300

@st.cache_data(ttl=REFRESH_SECONDS, show_spinner=False)
def fetch_latest():
    checked = datetime.now(timezone.utc).isoformat()
    try:
        response = requests.get(SOURCE, timeout=(5, 25), headers={'Cache-Control': 'no-cache'})
        response.raise_for_status()
        data = clean(pd.read_csv(StringIO(response.text)))
        if data.empty or data['Publication date'].notna().sum() == 0:
            raise ValueError('Source contains no usable dated model records.')
        return {'data': data, 'checked': checked, 'version': hashlib.sha256(response.content).hexdigest(), 'error': None}
    except (requests.RequestException, ValueError, pd.errors.ParserError) as error:
        # Cache failures too, so an outage does not trigger a request on every interaction.
        return {'data': None, 'checked': checked, 'version': None, 'error': type(error).__name__}

@st.cache_data(show_spinner=False)
def snapshot():
    return clean(pd.read_csv(Path(__file__).parent / 'data/models.csv'))


def resolve(result, previous=None):
    if result['data'] is not None:
        return result, 'Live Epoch AI dataset'
    if previous is not None:
        return previous, 'Last successful live dataset'
    return {'data': snapshot(), 'checked': '2026-10-11', 'version': 'bundled', 'error': None}, 'Bundled snapshot · October 11, 2026'
