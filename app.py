import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from core import SOURCE, METRICS, clean, shortlist, growth

st.set_page_config(page_title='ModelScope Atlas', page_icon='🧭', layout='wide')
st.markdown('''<style>.block-container{padding-top:2rem}h1{letter-spacing:-.04em}div[data-testid="stMetric"]{background:#151e32;border:1px solid #28364c;border-radius:12px;padding:18px}section[data-testid="stSidebar"]{border-right:1px solid #28364c}</style>''', unsafe_allow_html=True)

@st.cache_data(ttl=21600)
def load(live=False):
    if live:
        response = requests.get(SOURCE, timeout=30)
        response.raise_for_status()
        from io import StringIO
        return clean(pd.read_csv(StringIO(response.text))), 'Live Epoch AI download', datetime.now(timezone.utc).isoformat()
    return clean(pd.read_csv(Path(__file__).parent/'data/models.csv')), 'Bundled snapshot · October 11, 2026', '2026-10-11'

with st.sidebar:
    st.title('🧭 ModelScope')
    st.caption('ATLAS / AI RESEARCH INTELLIGENCE')
    page = st.radio('Workspace', ['Overview','Explore','Compare','Research assistant','Scenario lab','Watchlist','Data quality & sources'])
    live = st.toggle('Fetch latest Epoch data', value=False)
try:
    df, origin, fetched = load(live)
except Exception as e:
    st.warning(f'Live data unavailable ({type(e).__name__}). Using the bundled snapshot.')
    df, origin, fetched = load(False)
with st.sidebar:
    st.divider()
    dated = df['Year'].dropna()
    years = st.slider('Publication years', int(dated.min()), int(dated.max()), (2010,int(dated.max())))
    orgs = st.multiselect('Organizations', sorted(df['Organization'].unique()))
    domains = st.multiselect('Domains', sorted({x.strip() for s in df['Domain'] for x in s.split(',')}))
    access = st.multiselect('Accessibility', sorted(df['Model accessibility'].unique()))
    search = st.text_input('Search model, task or description')
    st.caption(origin)
    st.link_button('Epoch AI source & methodology', 'https://epoch.ai/data/ai-models')
mask = df['Year'].between(*years)
if orgs: mask &= df['Organization'].isin(orgs)
if domains: mask &= df['Domain'].apply(lambda x: bool({v.strip() for v in x.split(',')} & set(domains)))
if access: mask &= df['Model accessibility'].isin(access)
if search: mask &= df[['Model','Task','Abstract','Organization']].agg(' '.join,axis=1).str.contains(search,case=False,regex=False)
f = df[mask].copy()
st.session_state.setdefault('watchlist', [])
st.caption('MODELSCOPE ATLAS / '+page.upper())
st.title({'Overview':'See the frontier. Understand the evidence.','Explore':'Explore the model landscape','Compare':'Compare the evidence side by side','Research assistant':'Turn a question into a research shortlist','Scenario lab':'Explore the assumptions behind scale','Watchlist':'Your research watchlist','Data quality & sources':'Trust begins with the source'}[page])
st.caption(f'{len(f):,} matching records · {origin} · All workspace filters apply')

visible = ['Model','Organization','Publication date','Domain','Model accessibility','Confidence'] + METRICS

def table(data):
    st.dataframe(data, hide_index=True, width='stretch')

def export(data, name='models'):
    st.download_button('↓ Export CSV', data.to_csv(index=False).encode(), name+'.csv','text/csv')

if page == 'Overview':
    st.markdown('A research workspace for AI history, model discovery and transparent scenario planning.')
    cols=st.columns(4)
    for col,label,value in zip(cols,['Matching models','Organizations','Compute coverage','Parameter coverage'],[f'{len(f):,}',f['Organization'].nunique(),f'{f[METRICS[0]].notna().mean():.0%}' if len(f) else '—',f'{f[METRICS[1]].notna().mean():.0%}' if len(f) else '—']): col.metric(label,value)
    st.subheader('The scale of progress')
    plot=f.dropna(subset=[METRICS[0],'Publication date'])
    st.plotly_chart(px.scatter(plot,x='Publication date',y=METRICS[0],color='Domain',hover_name='Model',log_y=True,template='plotly_dark'),use_container_width=True)
    a,b=st.columns(2)
    with a:
        st.subheader('Recent releases')
        table(f.sort_values('Publication date',ascending=False)[visible[:6]].head(10))
    with b:
        st.subheader('Organizations in this selection')
        counts=f['Organization'].value_counts().head(12).rename_axis('Organization').reset_index(name='Models')
        st.plotly_chart(px.bar(counts,x='Models',y='Organization',orientation='h',template='plotly_dark'),use_container_width=True)
    st.info('Training compute and parameter count describe scale, not model quality. Missing estimates remain missing; rankings here are not capability benchmarks.')
elif page == 'Explore':
    a,b,c=st.columns(3)
    metric=a.selectbox('Measure',METRICS)
    color=b.selectbox('Color by',['Domain','Organization','Model accessibility','Confidence'])
    log=c.toggle('Logarithmic scale',True)
    plotted=f.dropna(subset=[metric,'Publication date'])
    st.caption(f'{len(plotted):,} plotted; {len(f)-len(plotted):,} omitted because date or measure is missing.')
    st.plotly_chart(px.scatter(plotted,x='Publication date',y=metric,color=color,hover_name='Model',hover_data=['Confidence','Organization'],log_y=log,template='plotly_dark'),use_container_width=True)
    n=st.slider('Leaderboard size',5,50,15)
    table(f.dropna(subset=[metric]).sort_values(metric,ascending=False)[visible].head(n))
    st.subheader('Browse all matching records')
    table(f[visible]); export(f.drop(columns='Record'))
elif page == 'Compare':
    choices=st.multiselect('Choose up to six records',f['Record'].tolist(),max_selections=6)
    selected=f[f['Record'].isin(choices)]
    if not choices: st.info('Choose records to compare scale, accessibility, uncertainty and source material.')
    else:
        table(selected[visible].set_index('Model').T)
        metric=st.selectbox('Compare measure',METRICS)
        st.plotly_chart(px.bar(selected.dropna(subset=[metric]),x='Model',y=metric,color='Organization',log_y=True,template='plotly_dark'),use_container_width=True)
        for _,row in selected.iterrows():
            with st.expander(row['Model']+' · source details'):
                st.write(row['Abstract'])
                if row['Link'].startswith(('https://','http://')): st.link_button('Original publication',row['Link'])
                st.write('Confidence:',row['Confidence'])
                st.write('Compute notes:',row.get('Training compute notes','Not available'))
        if st.button('Save selected to watchlist'):
            st.session_state.watchlist=list(dict.fromkeys(st.session_state.watchlist+choices)); st.success('Saved for this session.')
        export(selected.drop(columns='Record'),'comparison')
elif page == 'Research assistant':
    st.markdown('Search across model names, tasks, domains and abstracts. Results show why they matched, so you can inspect the evidence.')
    query=st.text_area('Describe your research need',placeholder='Open language models for code generation')
    open_only=st.checkbox('Require explicitly open weights')
    pool=f[f['Open model weights?'].str.lower().eq('yes')] if open_only else f
    if query:
        results=shortlist(pool,query)
        st.caption('Explainable keyword retrieval; no LLM, capability scoring, or arbitrary code execution. Larger scores mean more matching terms.')
        if results.empty: st.info('No matches. Try terms such as language, vision, code, translation or an organization name.')
        else:
            table(results[['Model','Match score','Why matched','Organization','Task','Model accessibility','Confidence']])
            brief=f'# ModelScope Atlas research brief\n\nQuestion: {query}\n\nFilters: {years}, organizations={orgs}, domains={domains}, accessibility={access}\n\nSource: {origin}; Epoch AI, CC BY 4.0, https://epoch.ai/data/ai-models\n\n'
            for _,r in results.iterrows():
                brief+=f"## {r['Model']}\nOrganization: {r['Organization']}\nMatch: {r['Why matched']}\nConfidence: {r['Confidence']}\nReference: {r['Link']}\n\n"
            brief+='These are text matches, not validated deployment recommendations. Verify licensing, benchmarks, inference cost and hardware requirements separately.\n'
            st.download_button('↓ Download research brief',brief,'research-brief.md','text/markdown')
    st.subheader('Ask a structured data question')
    question=st.selectbox('Question',['Which records have the most training compute?','Who has the most records?','How much evidence is missing?','Which models were released most recently?'])
    if question.startswith('Which records'): table(f.sort_values(METRICS[0],ascending=False).dropna(subset=[METRICS[0]])[visible].head(10))
    elif question.startswith('Who'): table(f['Organization'].value_counts().rename_axis('Organization').reset_index(name='Models').head(15))
    elif question.startswith('How'): table(pd.DataFrame({'Measure':METRICS,'Missing records':[f[m].isna().sum() for m in METRICS]}))
    else: table(f.sort_values('Publication date',ascending=False)[visible].head(10))
elif page == 'Scenario lab':
    st.subheader('Historical annual-maximum trend')
    metric=st.selectbox('Trend measure',METRICS)
    fit=growth(f,metric)
    if fit:
        annual,multiplier,slope,intercept=fit
        st.metric('Fitted annual multiplier',f'{multiplier:.2f}×')
        st.caption(f'Log-linear fit to {len(annual)} annual maxima in your selection. Selection bias and missing records affect this descriptive fit; it is not a forecast.')
        st.line_chart(annual.apply(np.log10).rename('log10 '+metric))
    else: st.info('At least three distinct years with measured values are required.')
    st.subheader('Compute → energy → emissions')
    a,b,c=st.columns(3)
    flop=a.number_input('Training compute (FLOP)',min_value=1e10,value=1e25,format='%.2e')
    throughput=b.number_input('Sustained FLOP / watt-second',min_value=1e6,value=1e11,format='%.2e')
    pue=c.number_input('Facility PUE',min_value=1.0,value=1.2,step=.1)
    intensity=st.slider('Grid intensity (g CO₂e / kWh)',0,1000,400)
    kwh=flop/throughput/3.6e6*pue
    a,b=st.columns(2);a.metric('Scenario energy',f'{kwh:,.0f} kWh');b.metric('Scenario emissions',f'{kwh*intensity/1e6:,.1f} tonnes CO₂e')
    st.caption('Energy = FLOP ÷ sustained FLOP per joule ÷ 3,600,000 × PUE. Emissions = kWh × grid intensity. Assumptions exclude hardware manufacture, inference and other lifecycle emissions.')
elif page == 'Watchlist':
    st.caption('Saved in this browser session. Export JSON to preserve it and import it later.')
    imported=st.file_uploader('Import watchlist JSON',type='json')
    if imported:
        try:
            names=json.load(imported)
            if not isinstance(names,list) or not all(isinstance(x,str) for x in names): raise ValueError('Expected a list of record identifiers.')
            st.session_state.watchlist=list(dict.fromkeys(names))
        except (ValueError,TypeError) as e: st.error(str(e))
    saved=df[df['Record'].isin(st.session_state.watchlist)]
    table(saved[visible]); export(saved.drop(columns='Record'),'watchlist')
    st.download_button('↓ Export watchlist JSON',json.dumps(st.session_state.watchlist),'watchlist.json','application/json')
    remove=st.multiselect('Remove records',st.session_state.watchlist)
    if st.button('Remove selected'):
        st.session_state.watchlist=[x for x in st.session_state.watchlist if x not in remove];st.rerun()
    st.caption('Watchlist displays saved records across all filters. Imported identifiers may not match a changed dataset snapshot.')
else:
    st.markdown('Data: [Epoch AI, Data on AI models](https://epoch.ai/data/ai-models), used under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Cleaning converts dates and positive numeric measures; missing values are preserved. This app is independently implemented and inspired by the AI Model Evolution Explorer interface.')
    st.write('Dataset loaded:',origin,'Retrieved:',fetched)
    coverage=pd.DataFrame({'Measure':METRICS,'Present':[f[m].notna().sum() for m in METRICS],'Missing':[f[m].isna().sum() for m in METRICS]})
    table(coverage)
    table(f['Confidence'].value_counts().rename_axis('Confidence').reset_index(name='Records'))
    st.warning('Epoch estimates can be uncertain. Confidence applies to dataset records and should be read with estimation notes. The data is non-exhaustive and historical training costs are in 2023 USD, not current API prices.')
    st.link_button('Read the complete methodology','https://epoch.ai/data/ai-models')
    export(f.drop(columns='Record'),'source-records')
st.divider()
st.caption('ModelScope Atlas · Independent research workspace · Epoch AI data / CC BY 4.0 · No API key required')
