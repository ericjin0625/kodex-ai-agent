import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import FinanceDataReader as fdr
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import json 
import time
import re
from collections import Counter
import io
import streamlit.components.v1 as components
import scipy.stats as stats  

# ==========================================
# 1. 페이지 레이아웃 및 전역 변수 초기화
# ==========================================
st.set_page_config(page_title="ETF Intelligence & Structuring Agent", layout="wide", initial_sidebar_state="collapsed")

if 'df_scatter' not in st.session_state: st.session_state.df_scatter = pd.DataFrame()
if 'dl_summary' not in st.session_state: st.session_state.dl_summary = "DataLab 데이터가 업로드되지 않았습니다."
if 'df_real_news' not in st.session_state: st.session_state.df_real_news = pd.DataFrame()
if 'df_volume_summary_text' not in st.session_state: st.session_state.df_volume_summary_text = "데이터 없음"
if 'aum_context_text' not in st.session_state: st.session_state.aum_context_text = "데이터 없음"
if 'media_context' not in st.session_state: st.session_state.media_context = "데이터 없음"

if 'p_target_etf' not in st.session_state: st.session_state.p_target_etf = "KODEX 200"
if 'p_comp_etf' not in st.session_state: st.session_state.p_comp_etf = "TIGER 200"

if 'p_proxy' not in st.session_state: st.session_state.p_proxy = "데이터 없음"
if 'p_proxy_reason' not in st.session_state: st.session_state.p_proxy_reason = "데이터 없음"
if 'p_purity' not in st.session_state: st.session_state.p_purity = "데이터 없음"
if 'p_weight' not in st.session_state: st.session_state.p_weight = "데이터 없음"
if 'p_cap' not in st.session_state: st.session_state.p_cap = 20
if 'p_ltv' not in st.session_state: st.session_state.p_ltv = 40
if 'p_fcf' not in st.session_state: st.session_state.p_fcf = 10
if 'p_has_csv' not in st.session_state: st.session_state.p_has_csv = False
if 'p_sharpe' not in st.session_state: st.session_state.p_sharpe = 0.0
if 'p_mdd' not in st.session_state: st.session_state.p_mdd = 0.0
if 'p_corr' not in st.session_state: st.session_state.p_corr = 0.0
if 'p_scenario' not in st.session_state: st.session_state.p_scenario = "데이터 없음"
if 'p_fx' not in st.session_state: st.session_state.p_fx = "환노출"
if 'p_aum' not in st.session_state: st.session_state.p_aum = 1000
if 'p_profit' not in st.session_state: st.session_state.p_profit = 0.0
if 'p_launch_budget' not in st.session_state: st.session_state.p_launch_budget = 2.0

if 'stat_did_multiplier' not in st.session_state: st.session_state.stat_did_multiplier = 0.0
if 'stat_p_value' not in st.session_state: st.session_state.stat_p_value = 0.0
if 'stat_net_inflow' not in st.session_state: st.session_state.stat_net_inflow = 0.0

if 't0_week_state' not in st.session_state: st.session_state.t0_week_state = None
if 'p_event_budget' not in st.session_state: st.session_state.p_event_budget = 0.0
if 'stat_roas' not in st.session_state: st.session_state.stat_roas = 0.0

# ==========================================
# 2. 반응형 라이트/다크 모드 커스텀 CSS (아이보리 & 차콜 테마 적용)
# ==========================================
responsive_theme_css = """
<style>
/* 부드러운 화면 전환 효과 */
html, body, [data-testid="stAppViewContainer"] {
    transition: background-color 0.3s ease, color 0.3s ease;
}

/* 데이터 프레임 투명화 및 탭 디자인 조정 */
.stDataFrame { background: transparent !important; }
[data-baseweb="tab-list"] { gap: 8px; padding-bottom: 12px; flex-wrap: wrap; }
[data-baseweb="tab"] { border-radius: 20px !important; padding: 8px 16px !important; }
div[data-testid="stRadio"] > div[role="radiogroup"] { display: flex; flex-direction: row; gap: 10px; background: transparent !important; }
div[data-testid="stRadio"] > div[role="radiogroup"] > label { padding: 8px 15px !important; border-radius: 50px !important; cursor: pointer !important; flex: 1 !important; display: flex !important; align-items: center !important; justify-content: center !important; transition: all 0.3s ease !important; }
div[data-testid="stRadio"] > div[role="radiogroup"] > label p { font-size: 16px !important; font-weight: 800 !important; margin: 0 !important; white-space: nowrap !important; text-align: center !important; }
div[data-testid="stRadio"] > div[role="radiogroup"] > label > div:first-child { display: none !important; }

#MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;} .stDeployButton {display: none;}

/* -----------------------------------------
   [다크 모드] 기기 설정이 다크 모드일 때 
   ----------------------------------------- */
@media (prefers-color-scheme: dark) {
    .stApp { background: linear-gradient(135deg, #0b101e 0%, #171b3c 50%, #0f172a 100%); background-attachment: fixed; }
    h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown, [data-testid="stWidgetLabel"] p, [data-testid="stMetricValue"] div { color: #f8fafc !important; }
    [data-testid="stCaptionContainer"] p, [data-testid="stMetricLabel"] p { color: #cbd5e1 !important; }
    
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255, 255, 255, 0.02) !important;
        backdrop-filter: blur(16px) !important; -webkit-backdrop-filter: blur(16px) !important;
        border-radius: 16px !important; border: 1px solid rgba(255, 255, 255, 0.06) !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2) !important; padding: 20px !important;
    }
    
    [data-baseweb="tab"] { background: rgba(255, 255, 255, 0.04) !important; border: 1px solid rgba(255, 255, 255, 0.08) !important; color: #94a3b8 !important; }
    [data-baseweb="tab"][aria-selected="true"] { background: rgba(77, 166, 255, 0.12) !important; border: 1px solid rgba(77, 166, 255, 0.5) !important; color: #ffffff !important; box-shadow: 0 0 12px rgba(77, 166, 255, 0.25) !important; font-weight: 600 !important; }
    
    div[data-testid="stRadio"] > div[role="radiogroup"] > label { background: rgba(255, 255, 255, 0.05) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label:hover { background: rgba(255, 255, 255, 0.1) !important; }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label[data-checked="true"] { background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%) !important; border: 2px solid #4da6ff !important; box-shadow: 0 0 15px rgba(77, 166, 255, 0.4) !important; }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label p { color: #ffffff !important; }
    
    div[data-baseweb="textarea"] textarea, .stTextArea textarea { background-color: #0f172a !important; color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; border: 1px solid rgba(77, 166, 255, 0.5) !important; }
}

/* -----------------------------------------
   [라이트 모드] 기기 설정이 라이트 모드일 때 (아이보리 & 차콜)
   ----------------------------------------- */
@media (prefers-color-scheme: light) {
    .stApp { background: #FDFBF7 !important; background-attachment: fixed; }
    h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown, [data-testid="stWidgetLabel"] p, [data-testid="stMetricValue"] div { color: #1E293B !important; }
    [data-testid="stCaptionContainer"] p, [data-testid="stMetricLabel"] p { color: #475569 !important; }
    
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255, 255, 255, 0.65) !important;
        backdrop-filter: blur(16px) !important; -webkit-backdrop-filter: blur(16px) !important;
        border-radius: 16px !important; border: 1px solid rgba(30, 41, 59, 0.08) !important;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.04) !important; padding: 20px !important;
    }

    [data-baseweb="tab"] { background: rgba(30, 41, 59, 0.04) !important; border: 1px solid rgba(30, 41, 59, 0.08) !important; color: #64748B !important; }
    [data-baseweb="tab"][aria-selected="true"] { background: rgba(77, 166, 255, 0.1) !important; border: 1px solid rgba(77, 166, 255, 0.6) !important; color: #0F172A !important; box-shadow: 0 0 10px rgba(77, 166, 255, 0.15) !important; font-weight: 700 !important; }

    div[data-testid="stRadio"] > div[role="radiogroup"] > label { background: rgba(30, 41, 59, 0.03) !important; border: 1px solid rgba(30, 41, 59, 0.1) !important; }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label:hover { background: rgba(30, 41, 59, 0.08) !important; }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label[data-checked="true"] { background: #ffffff !important; border: 2px solid #4da6ff !important; box-shadow: 0 0 12px rgba(77, 166, 255, 0.2) !important; }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label p { color: #0F172A !important; }

    div[data-baseweb="textarea"] textarea, .stTextArea textarea, .stTextInput input, .stNumberInput input, .stSelectbox div { background-color: #ffffff !important; color: #1E293B !important; -webkit-text-fill-color: #1E293B !important; border: 1px solid #E2E8F0 !important; }
}
</style>
"""
st.markdown(responsive_theme_css, unsafe_allow_html=True)

# ==========================================
# 3. 파싱 및 연산 함수 모음 (변경 없음)
# ==========================================
def extract_keywords_from_titles(titles, top_n=6):
    try:
        words = []
        stop_words = {'etf', '투자', '증권', '주식', '시장', '종목', '상장', '수익', '수익률', '특징주', '주가', '펀드', '전망', '관련주', '테마', '대비', '위해', '대한', '관련', '가운데', '가장', '지금', '어떤', '이유', '내년', '올해', '최대', '최고', '코스피', '코스닥', '국내', '미국', '글로벌'}
        for t in titles:
            clean_t = re.sub(r'[^\w\s]', '', str(t))
            for w in clean_t.split():
                if len(w) >= 2 and w.lower() not in stop_words and not w.isdigit():
                    words.append(w)
        counter = Counter(words)
        return [word for word, count in counter.most_common(top_n)]
    except:
        return []

def assign_auto_theme(etf_name):
    name = str(etf_name).upper().replace(" ", "")
    if any(kw in name for kw in ['인버스', '베어']): return '📉 인버스 (하락배팅)'
    elif any(kw in name for kw in ['레버리지', '2X']): return '🚀 레버리지 (고변동성)'
    elif any(kw in name for kw in ['배당', '커버드콜', '인컴', '고배당', 'DIV']): return '💰 배당 & 커버드콜'
    elif any(kw in name for kw in ['AI', '반도체']): return '🤖 AI & 반도체'
    elif any(kw in name for kw in ['테크', '기술주', 'TECH', '혁신', '나스닥100', '빅테크', 'FANG']): return '💻 글로벌 빅테크'
    elif any(kw in name for kw in ['S&P', '미국', '다우존스', 'MSCI']): return '🇺🇸 미국 대표지수'
    elif any(kw in name for kw in ['코스피', '코스닥', '200']): return '🇰🇷 국내 대표지수'
    elif any(kw in name for kw in ['채권', '국고채', '금리', 'KOFR', 'CD', '파킹']): return '🛡️ 안전자산 (채권/금리)'
    else: return '📦 기타 섹터/테마'

def normalize_etf_name(name):
    name = str(name).strip()
    aliases = {
        "KODEX 고배당": "KODEX 고배당주",
        "PLUS 고배당주위클리커버드콜": "PLUS 고배당주위클리커버드콜"
    }
    return aliases.get(name, name)

def extract_table(df, expected_cols):
    cols_str = " ".join([str(c) for c in df.columns])
    if all(ec in cols_str for ec in expected_cols): return df
    for i, row in df.iterrows():
        row_str = " ".join([str(val) for val in row.values if pd.notna(val)])
        if all(ec in row_str for ec in expected_cols):
            new_df = df.iloc[i+1:].copy()
            raw_cols = [str(c).strip() for c in row.values]
            seen = set()
            final_cols = []
            for c in raw_cols:
                new_c = c if c not in ['nan', 'None', ''] else 'Unnamed'
                while new_c in seen: new_c += "_"
                seen.add(new_c)
                final_cols.append(new_c)
            new_df.columns = final_cols
            return new_df.dropna(how='all').reset_index(drop=True)
    return df

@st.cache_data(ttl=1800)
def get_macro_snapshot():
    snapshot = {
        "indices": {"코스피": {"val": "정보 불가"}, "코스닥": {"val": "정보 불가"}, "S&P 500": {"val": "정보 불가"}, "나스닥": {"val": "정보 불가"}, "다우존스": {"val": "정보 불가"}},
        "forex": {"미국 USD": {"val": "정보 불가"}, "일본 JPY 100": {"val": "정보 불가"}, "유럽연합 EUR": {"val": "정보 불가"}},
        "rates": {"콜금리": {"val": "정보 불가"}, "CD(91일)": {"val": "정보 불가"}, "국고채(3년)": {"val": "정보 불가"}},
        "others": {"VIX 지수": {"val": "정보 불가"}, "금 가격": {"val": "정보 불가"}, "비트코인 (BTC)": {"val": "정보 불가"}}
    }
    tickers = {
        "indices": {"코스피": ["KS11"], "코스닥": ["KQ11"], "S&P 500": ["US500", "^GSPC"], "나스닥": ["IXIC", "^IXIC"], "다우존스": ["DJI", "^DJI"]},
        "forex": {"미국 USD": ["USD/KRW"], "일본 JPY 100": ["JPY/KRW"], "유럽연합 EUR": ["EUR/KRW"]},
        "others": {"VIX 지수": ["VIX", "^VIX"], "금 가격": ["GC=F", "ZG"], "비트코인 (BTC)": ["BTC/KRW"]}
    }
    end = datetime.today()
    start = end - timedelta(days=14) 
    for category, items in tickers.items():
        for name, ticker_list in items.items():
            for ticker in ticker_list:
                try:
                    df = fdr.DataReader(ticker, start, end).dropna()
                    if len(df) >= 2:
                        c, p = df['Close'].iloc[-1], df['Close'].iloc[-2]
                        if name == "일본 JPY 100" and c < 50: c, p = c * 100, p * 100
                        if name == "비트코인 (BTC)": val_str, delta_str = f"₩{c:,.0f}", f"{c-p:+,.0f}"
                        elif name == "금 가격": val_str, delta_str = f"${c:,.2f}", f"{c-p:+,.2f}"
                        else: val_str, delta_str = f"{c:,.2f}", f"{c-p:+,.2f}"
                        pct_str = f"{(c-p)/p*100:+.2f}%"
                        snapshot[category][name] = {"val": val_str, "delta": delta_str, "pct": pct_str, "is_up": c >= p}
                        break 
                except: pass

    rates_map = {"콜금리": "IRR_CALL", "CD(91일)": "IRR_CD91", "국고채(3년)": "IRR_GOVT03Y"}
    for name, code in rates_map.items():
        try:
            url = f"https://finance.naver.com/marketindex/interestDailyQuote.naver?marketindexCd={code}&page=1"
            res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            res.encoding = 'euc-kr'
            df_ir = pd.read_html(io.StringIO(res.text))[0]
            if not df_ir.empty and len(df_ir) >= 2:
                c = float(str(df_ir.iloc[0, 1]).replace('%', '').strip())
                p = float(str(df_ir.iloc[1, 1]).replace('%', '').strip())
                val_str = f"{c:,.3f}%"
                delta = c - p
                delta_str = f"{delta:+.3f}"
                pct_str = f"{(delta)/p*100:+.2f}%" if p != 0 else "+0.00%"
                snapshot["rates"][name] = {"val": val_str, "delta": delta_str, "pct": pct_str, "is_up": delta >= 0}
        except: pass
    return snapshot

def render_compact_metric(title, data):
    if data['val'] == "정보 불가":
        return f"""<div style="background: rgba(128, 128, 128, 0.05); border: 1px solid rgba(128, 128, 128, 0.1); border-radius: 8px; padding: 12px 16px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;"><div style="font-size: 15px; font-weight: 600;">{title}</div><div style="text-align: right;"><div style="color: #ff4d4d; font-size: 13px; font-weight: 600;">(업데이트 전)</div></div></div>"""
    color = "#ff4d4d" if data['is_up'] else "#4da6ff"
    arrow = "▲" if data['is_up'] else "▼"
    delta_str = str(data['delta']).replace('+', '').replace('-', '')
    return f"""<div style="background: rgba(128, 128, 128, 0.05); border: 1px solid rgba(128, 128, 128, 0.1); border-radius: 8px; padding: 12px 16px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;"><div style="font-size: 15px; font-weight: 600;">{title}</div><div style="text-align: right;"><div style="font-size: 17px; font-weight: 800;">{data['val']}</div><div style="color: {color}; font-size: 12px; font-weight: 600; margin-top: 2px;">{arrow} {delta_str} ({data['pct']})</div></div></div>"""

@st.cache_data(ttl=3600)
def get_realtime_news(keyword="ETF", timeframe="7d", max_items=12):
    url = f"https://news.google.com/rss/search?q={keyword}+when:{timeframe}&hl=ko&gl=KR&ceid=KR:ko"
    try:
        res = requests.get(url, timeout=5)
        root = ET.fromstring(res.text)
        news_list = []
        for item in root.findall('./channel/item')[:max_items]:
            title = item.find('title').text if item.find('title') is not None else "제목 없음"
            link = item.find('link').text if item.find('link') is not None else ""
            pubDate = item.find('pubDate').text[5:16] if item.find('pubDate') is not None else ""
            source = item.find('source').text if item.find('source') is not None else "Google News"
            news_list.append({"게시일 / 출처": f"{pubDate} / {source}", "원본제목": title, "링크": link})
        if not news_list: return pd.DataFrame([{"게시일 / 출처": "-", "원본제목": f"'{keyword}' 관련 뉴스가 없습니다.", "링크": ""}])
        return pd.DataFrame(news_list)
    except: return pd.DataFrame([{"게시일 / 출처": "오류", "원본제목": "실시간 뉴스를 불러올 수 수 없습니다.", "링크": ""}])

@st.cache_data(ttl=1800)
def parse_competitor_blog_last_week(blog_id):
    url = f"https://rss.blog.naver.com/{blog_id}.xml"
    posts = []
    try:
        res = requests.get(url, timeout=5)
        root = ET.fromstring(res.content)
        items = root.findall('./channel/item')[:20]
        
        today = datetime.today()
        idx = (today.weekday() + 1) % 7
        this_sun = today - timedelta(days=idx)
        last_sun = this_sun - timedelta(days=7)
        last_sat = this_sun - timedelta(days=1)
        
        for item in items: 
            title = item.find('title').text
            link = item.find('link').text
            pubDate_str = item.find('pubDate').text 
            try:
                date_parts = pubDate_str.split(',')[1].split()[0:3]
                date_clean = " ".join(date_parts)
                pub_date = datetime.strptime(date_clean, "%d %b %Y").date()
            except: 
                continue 
            
            if last_sun.date() <= pub_date <= last_sat.date():
                posts.append({"title": title, "link": link, "date": pub_date.strftime("%Y-%m-%d")})
    except: pass
    return posts

@st.cache_data(ttl=3600)
def scrape_youtube_search_real(keyword):
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://www.youtube.com/results?search_query={requests.utils.quote(keyword)}"
    feed = []
    try:
        res = requests.get(url, headers=headers, timeout=6)
        if res.status_code != 200: return []
        match = re.search(r'ytInitialData\s*=\s*({.*?});</script>', res.text)
        if not match: return []
        data = json.loads(match.group(1))
        def recurse(node):
            if isinstance(node, list):
                for i in node: recurse(i)
            elif isinstance(node, dict):
                if 'videoRenderer' in node:
                    v = node['videoRenderer']
                    title = v.get('title', {}).get('runs', [{}])[0].get('text', '')
                    vid_id = v.get('videoId', '')
                    pub = v.get('publishedTimeText', {}).get('simpleText', '최근')
                    views_raw = v.get('viewCountText', {}).get('simpleText', '0')
                    views_num = re.sub(r'[^0-9]', '', views_raw)
                    views = int(views_num) if views_num.isdigit() else 0
                    if vid_id and title:
                        feed.append({"title": title, "link": f"https://www.youtube.com/watch?v={vid_id}", "date": pub, "views": views})
                else:
                    for val in node.values(): recurse(val)
        recurse(data)
    except: pass
    return feed[:5]

@st.cache_data(ttl=86400)
def get_etf_mapping():
    try:
        df = fdr.StockListing('ETF/KR')
        return dict(zip(df['Name'], df['Symbol']))
    except: return {}

def get_real_returns(symbols_dict, etf_names):
    end_date = datetime.today()
    start_date = end_date - timedelta(days=14)
    returns_dict = {}
    for name in etf_names:
        symbol = symbols_dict.get(name)
        if symbol:
            try:
                df = fdr.DataReader(symbol, start_date, end_date)
                if len(df) >= 5:
                    yield_pct = ((df['Close'].iloc[-1] - df['Close'].iloc[-5]) / df['Close'].iloc[-5]) * 100
                    returns_dict[name] = round(yield_pct, 2)
                else: returns_dict[name] = 0.0
            except: returns_dict[name] = 0.0
        else: returns_dict[name] = 0.0
    return returns_dict

@st.cache_data
def load_and_clean_excel(file, sheet_name):
    try:
        df = pd.read_excel(file, sheet_name=sheet_name)
        df.columns = df.columns.str.strip()
        if '종목명' in df.columns:
            df['종목명'] = df['종목명'].apply(normalize_etf_name)
        for col in ["개인", "기관", "외국인"]:
            if col in df.columns:
                clean_val = df[col].astype(str).str.replace(',', '', regex=False).str.replace('-', '0', regex=False)
                df[col] = pd.to_numeric(clean_val, errors='coerce').fillna(0)
        return df
    except: return pd.DataFrame()

@st.cache_data(ttl=60)
def load_event_sheet(url):
    if not url or "docs.google.com" not in url: 
        return pd.DataFrame()
    try:
        if "export?format=csv" not in url:
            base_url = url.split('/edit')[0]
            csv_url = f"{base_url}/export?format=csv"
            if 'gid=' in url:
                gid = url.split('gid=')[1].split('&')[0]
                csv_url += f"&gid={gid}"
        else:
            csv_url = url
        df = pd.read_csv(csv_url)
        df.columns = df.columns.str.strip()
        
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.strip()
                
        if '시작일' in df.columns:
            df['시작일'] = pd.to_datetime(df['시작일'].astype(str).str.replace('.', '-', regex=False), errors='coerce')
        if '종료일' in df.columns:
            df['종료일'] = pd.to_datetime(df['종료일'].astype(str).str.replace('.', '-', regex=False), errors='coerce')

        if '타겟/경품 내역 (원)' in df.columns:
            df['경품예산'] = pd.to_numeric(df['타겟/경품 내역 (원)'].astype(str).str.replace(',', '', regex=False).str.replace(' ', '', regex=False), errors='coerce').fillna(0)
            
        return df
    except Exception as e:
        return pd.DataFrame()

def parse_week_range(w_str, year):
    try:
        start_str, end_str = str(w_str).split('-')
        sm, sd = map(int, start_str.split('.'))
        em, ed = map(int, end_str.split('.'))
        start_dt = datetime(int(year), sm, sd)
        end_dt = datetime(int(year), em, ed)
        if em < sm:
            end_dt = datetime(int(year) + 1, em, ed)
        return start_dt, end_dt
    except:
        return None, None

# =========================================================================
# 4. 화면 분할 (메인 콘텐츠 8.75 : 우측 패널 1.25)
# =========================================================================
col_main, col_right = st.columns([8.75, 1.25])

with col_right:
    # 사이즈 매칭 및 정렬
    st.markdown(
        """
        <div style='text-align: right; margin-bottom: 25px;'>
            <span style='font-size: 23px; font-weight: 800; letter-spacing: -0.5px; line-height: 1.3;'>
                SAMSUNG AMC<br>Intelligence
            </span>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    placeholder_week_dropdown = st.empty()
    placeholder_excel_upload = st.empty()
    
    with placeholder_excel_upload.container():
        # 디폴트 시트 링크 세팅
        default_sheet_url = "https://docs.google.com/spreadsheets/d/1vbgATMYbSBBh3VsYyBIaPslPnmJ0nzhdlpyflcW6-kk/edit?usp=sharing"
        st.text_input("🔗 1. 이벤트 시트 (공유 링크)", value=default_sheet_url, key="sheet_url_global")
        
        uploaded_excel = st.file_uploader("📈 2. 주간 순매수 엑셀", type=["xlsx", "xls"], key="excel_global")
        available_weeks = ["데이터 없음"]
        if uploaded_excel is not None:
            try:
                xls = pd.ExcelFile(uploaded_excel)
                available_weeks = [sheet for sheet in xls.sheet_names if sheet != "참고사항"][::-1] 
            except: pass
            
    with placeholder_week_dropdown.container():
        selected_week = st.selectbox("📆 조회 기준 주차", options=available_weeks, index=1 if len(available_weeks)>1 else 0)
        
    uploaded_dls = st.file_uploader("🔍 3. DataLab 다중 비교", type=["csv", "xlsx", "xls"], key="dl_global", accept_multiple_files=True)
    uploaded_voc = st.file_uploader("💬 4. 종토방 VOC 엑셀", type=["xlsx", "xls"], key="voc_global")

    # 사이드바 하단 텍스트 (위 타이틀과 크기 동일 매칭)
    st.markdown(
        """
        <div style='margin-top: 80px; padding-top: 20px; border-top: 1px solid rgba(128,128,128,0.15); text-align: right;'>
            <div style='font-size: 23px; font-weight: 800; margin-bottom: 12px; letter-spacing: -0.5px;'>
                커리어하이
            </div>
            <div style='font-size: 23px; font-weight: 800; letter-spacing: -0.5px;'>
                삼성자산운용
            </div>
        </div>
        """, 
        unsafe_allow_html=True
    )

# =========================================================================
# 5. 메인 패널 
# =========================================================================
with col_main:
    # [수정 영역] 상위 탭 2개로 통합
    big_tab = st.radio(
        "메인 메뉴",
        ["📊 ETF 시장 모니터링", "🌍 정책 모니터링 및 상품 기획 시뮬레이터"],
        horizontal=True,
        label_visibility="collapsed"
    )
    st.markdown("<br>", unsafe_allow_html=True)

# -------------------------------------------------------------------------
    # Big 탭 1: ETF 시장 모니터링 
# -------------------------------------------------------------------------
    if big_tab == "📊 ETF 시장 모니터링":
        st.markdown("## 📊 ETF Market Intelligence")
        st.caption("국내외 거시 경제, 경쟁사 수급, 마케팅 액션 및 리테일 투자자 심리를 종합적으로 모니터링합니다.")
        
        # [수정 영역] 서브 탭의 맨 마지막에 AI 프롬프트 탭 추가
        sub_tabs = st.tabs(["🏠 Home", "📊 Weekly Info", "📈 순매수/거래대금 및 수익률", "📰 뉴스 & 트렌드", "📺 이벤트 및 성과 검증", "🗣️ 고객 UX", "🥧 ETF/AUM 현황", "🤖 주간 브리핑 AI 프롬프트"])

        with sub_tabs[0]:
            st.markdown("<br><div style='text-align: center;'><h1>Macro & Market Dashboard</h1><p>실시간 거시 경제 및 시장 지표 요약</p></div><br>", unsafe_allow_html=True)
            macros = get_macro_snapshot()
            c_m1, c_m2, c_m3 = st.columns(3)
            with c_m1: 
                st.markdown("#### 📈 핵심 대표 지수")
                for k,v in macros["indices"].items(): st.markdown(render_compact_metric(k,v), unsafe_allow_html=True)
            with c_m2: 
                st.markdown("#### 💱 주요 환율")
                for k,v in macros["forex"].items(): st.markdown(render_compact_metric(k,v), unsafe_allow_html=True)
                st.markdown("<br>#### 🏦 금리 지표", unsafe_allow_html=True)
                for k,v in macros["rates"].items(): st.markdown(render_compact_metric(k,v), unsafe_allow_html=True)
            with c_m3: 
                st.markdown("#### 📌 기타 주요 지표")
                for k,v in macros["others"].items(): st.markdown(render_compact_metric(k,v), unsafe_allow_html=True)

        with sub_tabs[1]:
            if uploaded_excel is not None and selected_week != "데이터 없음":
                df_source = load_and_clean_excel(uploaded_excel, selected_week)
                if not df_source.empty and '종목명' in df_source.columns:
                    st.markdown("### 🏆 해당 주 순매수 ETF 순위")
                    col_subject, col_space, col_slider = st.columns([2, 3, 3])
                    with col_subject: target_subject = st.selectbox("주체:", ["개인", "기관", "외국인"], key="main_sub")
                    with col_slider: top_n = st.slider("TOP N개 설정", 5, 50, 10, 5, label_visibility="collapsed")
                    
                    df_filtered = df_source[df_source["종목명"] != "전체"].sort_values(by=target_subject, ascending=False).head(top_n)
                    c_tbl, c_cht = st.columns([4, 5])
                    with c_tbl: st.dataframe(df_filtered[["종목명", target_subject]], use_container_width=True, hide_index=True)
                    with c_cht:
                        fig = px.bar(df_filtered, x=target_subject, y="종목명", orientation='h', template="plotly_dark")
                        fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=380, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig, use_container_width=True)
                    
                    st.divider()
                    st.markdown("### 🔥 AI 자동 분류 테마 비중 (순매수 유입 기준)")
                    df_source['AI_자동_테마'] = df_source['종목명'].apply(assign_auto_theme)
                    df_theme_pos = df_source[(df_source["종목명"] != "전체") & (df_source[target_subject] > 0)]
                    df_theme = df_theme_pos.groupby('AI_자동_테마')[target_subject].sum().reset_index().sort_values(by=target_subject, ascending=False)
                    
                    if len(df_theme) > top_n:
                        df_top = df_theme.head(top_n)
                        df_others = pd.DataFrame([{'AI_자동_테마': "🧩 기타 합산 (Others)", target_subject: df_theme.iloc[top_n:][target_subject].sum()}])
                        df_pie_data = pd.concat([df_top, df_others], ignore_index=True)
                    else: 
                        df_pie_data = df_theme

                    col_theme_table, col_theme_chart = st.columns([3, 7])
                    with col_theme_table: st.dataframe(df_pie_data, use_container_width=True, height=400, hide_index=True)
                    with col_theme_chart:
                        fig_pie = px.pie(df_pie_data, names='AI_자동_테마', values=target_subject, hole=0.4, color_discrete_sequence=px.colors.sequential.Blues_r)
                        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                        fig_pie.update_layout(height=400, template="plotly_dark", showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig_pie, use_container_width=True)
                else: st.warning("업로드된 엑셀 파일의 양식이 올바르지 않습니다.")
            else: st.info("👉 우측 패널에 ETF 순매수 엑셀 데이터를 업로드해주세요.")

        with sub_tabs[2]:
            if uploaded_excel is not None and selected_week != "데이터 없음":
                st.markdown("### 📈 기간별 ETF 순매수 현황")
                col_start, col_text, col_slider, col_space, col_inv = st.columns([1.5, 3, 2.5, 0.5, 1.5])
                with col_start: start_week = st.selectbox("시작 주차:", options=available_weeks[::-1], index=0, key="start_week")
                with col_text: st.markdown(f"<p style='margin-top: 30px; font-weight: bold;'>부터    {selected_week} 까지의</p>", unsafe_allow_html=True)
                with col_slider: top_n_tab2 = st.slider("TOP N개 ETF 순매수 순위:", 10, 100, 50, 10, key="top_n_tab2", label_visibility="collapsed")
                with col_inv:
                    st.markdown("<div style='margin-bottom:-15px; font-size:13px; color:#94a3b8;'>분석 주체:</div>", unsafe_allow_html=True)
                    inv_type_tab2 = st.selectbox("투자자 선택", ["개인", "기관", "외국인"], label_visibility="collapsed", key="inv_type_tab2")
                
                st.divider()
                df_tab2_combined = pd.DataFrame()
                if start_week in available_weeks and selected_week in available_weeks:
                    start_idx, end_idx = available_weeks.index(start_week), available_weeks.index(selected_week)
                    if start_idx >= end_idx:
                        target_sheets = available_weeks[end_idx:start_idx+1]
                        all_sheets_data = []
                        for sheet in target_sheets:
                            temp_df = load_and_clean_excel(uploaded_excel, sheet)
                            if not temp_df.empty and '종목명' in temp_df.columns:
                                temp_df = temp_df[temp_df['종목명'] != '전체']
                                temp_df['전체순매수'] = temp_df.get('개인', 0) + temp_df.get('기관', 0) + temp_df.get('외국인', 0)
                                all_sheets_data.append(temp_df[['종목명', '전체순매수', '개인', '기관', '외국인']])
                        if all_sheets_data: 
                            df_tab2_combined = pd.concat(all_sheets_data).groupby('종목명').sum().reset_index()

                if not df_tab2_combined.empty:
                    col_chart1, col_chart2 = st.columns(2)
                    with col_chart1:
                        st.markdown("#### 전체 순매수 금액")
                        df_total = df_tab2_combined.sort_values(by="전체순매수", ascending=False).head(top_n_tab2)
                        with st.container(border=True):
                            fig_total = px.bar(df_total, x="전체순매수", y="종목명", orientation='h', color_discrete_sequence=['#4da6ff'])
                            fig_total.update_layout(xaxis_title="전체 순매수 금액 (억원)", yaxis={'categoryorder':'total ascending'}, height=500, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                            st.plotly_chart(fig_total, use_container_width=True)

                    with col_chart2:
                        st.markdown(f"#### {inv_type_tab2}별 순매수 금액")
                        df_inv = df_tab2_combined.sort_values(by=inv_type_tab2, ascending=False).head(top_n_tab2)
                        with st.container(border=True):
                            fig_inv = px.bar(df_inv, x=inv_type_tab2, y="종목명", orientation='h', color_discrete_sequence=['#ff4d4d'])
                            fig_inv.update_layout(xaxis_title=f"{inv_type_tab2} 순매수 금액 (억원)", yaxis={'categoryorder':'total ascending'}, height=500, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                            st.plotly_chart(fig_inv, use_container_width=True)

                st.divider()
                st.markdown("### 🎯 시차별 수익률 vs. AUM 대비 순매수 산점도 (T-0, T-1, T-2)")
                col_subject_tab2_scatter, _ = st.columns([2, 8])
                with col_subject_tab2_scatter: 
                    subject_tab2_scatter = st.selectbox("산점도 분석 주체 선택:", ["개인", "기관", "외국인"], key="subject_tab2_scatter")

                df_curr = load_and_clean_excel(uploaded_excel, selected_week)
                if not df_curr.empty and '종목명' in df_curr.columns:
                    df_c = df_curr[df_curr['종목명'] != '전체'][['종목명', subject_tab2_scatter]].rename(columns={subject_tab2_scatter: '이번주'})
                    all_etfs_scatter = df_c['종목명'].dropna().tolist()
                    default_selection = all_etfs_scatter[:10] if len(all_etfs_scatter) >= 10 else all_etfs_scatter
                    selected_scatter_etfs = st.multiselect("📍 산점도에 표시할 ETF를 검색/선택하세요:", options=all_etfs_scatter, default=default_selection, key="scatter_multiselect_tab2")
                    
                    if selected_scatter_etfs:
                        with st.spinner("실시간 KRX AUM 및 과거 3주 치 수익률 데이터를 연동 중입니다..."):
                            try:
                                df_etf = fdr.StockListing('ETF/KR')
                                aum_mapping = dict(zip(df_etf['Name'], df_etf['MarCap']))
                                symbols_mapping = dict(zip(df_etf['Name'], df_etf['Symbol']))
                            except:
                                aum_mapping, symbols_mapping = {}, {}

                            scatter_data = []
                            end_date = datetime.today()
                            start_date = end_date - timedelta(days=40)
                            
                            for etf in selected_scatter_etfs:
                                this_week_val = df_c[df_c['종목명'] == etf]['이번주'].values[0]
                                aum_raw = aum_mapping.get(etf, 0)
                                
                                if pd.isna(aum_raw) or aum_raw == 0:
                                    ratio = 0
                                else:
                                    ratio = (this_week_val / aum_raw) * 100
                                    if abs(ratio) < 0.0001 and this_week_val != 0:
                                        ratio = ((this_week_val * 100_000_000) / aum_raw) * 100
                                
                                sym = symbols_mapping.get(etf)
                                ret_t0, ret_t1, ret_t2 = 0.0, 0.0, 0.0
                                if sym:
                                    try:
                                        df_hist = fdr.DataReader(sym, start_date, end_date)
                                        if len(df_hist) >= 15:
                                            p0 = df_hist['Close'].iloc[-1]
                                            p1 = df_hist['Close'].iloc[-6]
                                            p2 = df_hist['Close'].iloc[-11]
                                            p3 = df_hist['Close'].iloc[-16]
                                            ret_t0 = ((p0 - p1) / p1) * 100
                                            ret_t1 = ((p1 - p2) / p2) * 100
                                            ret_t2 = ((p2 - p3) / p3) * 100
                                    except: pass
                                    
                                scatter_data.append({
                                    "종목명": etf,
                                    "이번주 순매수": this_week_val,
                                    "AUM 대비 순매수(%)": ratio,
                                    "T-0 수익률(%)": ret_t0,
                                    "T-1 수익률(%)": ret_t1,
                                    "T-2 수익률(%)": ret_t2
                                })
                            
                            df_scatter = pd.DataFrame(scatter_data)
                            
                            c_s1, c_s2, c_s3 = st.columns(3)
                            
                            def draw_scatter(col, x_col, title):
                                with col:
                                    fig = px.scatter(df_scatter, x=x_col, y="AUM 대비 순매수(%)", text="종목명", hover_data=["이번주 순매수"], title=title)
                                    if len(df_scatter) > 1:
                                        x_data, y_data = df_scatter[x_col], df_scatter["AUM 대비 순매수(%)"]
                                        std_x, std_y = np.std(x_data), np.std(y_data)
                                        if std_x > 0 and std_y > 0:
                                            r_val = np.corrcoef(x_data, y_data)[0, 1]
                                            z = np.polyfit(x_data, y_data, 1)
                                            p = np.poly1d(z)
                                            fig.add_scatter(x=x_data, y=p(x_data), mode='lines', name='추세선', line=dict(color='#ff4d4d', dash='dot'))
                                            fig.add_annotation(x=0.05, y=0.95, xref="paper", yref="paper", text=f"상관계수 r = {r_val:.2f}", showarrow=False, font=dict(color="#ffb04d", size=14), bgcolor="rgba(0,0,0,0.5)")
                                    
                                    fig.update_traces(textposition='top center', marker=dict(size=9, color='#4da6ff', opacity=0.7), textfont=dict(size=11, color='lightgray'))
                                    fig.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.5)
                                    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
                                    fig.update_layout(height=450, margin=dict(l=10,r=10,t=40,b=10), template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                                    st.plotly_chart(fig, use_container_width=True)
                            
                            draw_scatter(c_s1, "T-0 수익률(%)", "**T-0 (이번주 수익률) 반응**")
                            draw_scatter(c_s2, "T-1 수익률(%)", "**T-1 (지난주 수익률) 반응**")
                            draw_scatter(c_s3, "T-2 수익률(%)", "**T-2 (지지난주 수익률) 반응**")
                
                st.divider()
                st.markdown("### 📊 선택 ETF 실제 주간 거래량(거래대금 프록시) 추이")
                df_source = load_and_clean_excel(uploaded_excel, selected_week)
                if not df_source.empty and '종목명' in df_source.columns:
                    extracted_etfs = df_source[df_source['종목명'] != '전체']['종목명'].dropna().unique().tolist()
                    selected_etfs = st.multiselect("검색 및 선택 (원하시는 만큼 무제한 선택 가능합니다):", options=extracted_etfs, default=extracted_etfs[:4] if len(extracted_etfs) >= 4 else extracted_etfs, key="vol_multiselect")
                    st.divider()
                    if selected_etfs:
                        volume_lines = []
                        with st.spinner("한국거래소(KRX)에서 거래 데이터를 불러오는 중 창입니다..."):
                            cols = st.columns(2)
                            symbols_mapping = get_etf_mapping()
                            end_date = datetime.today()
                            start_date = end_date - timedelta(weeks=8) 
                            for i, etf_name in enumerate(selected_etfs):
                                with cols[i % 2]:
                                    symbol = symbols_mapping.get(etf_name)
                                    if symbol:
                                        try:
                                            df_hist = fdr.DataReader(symbol, start_date, end_date)
                                            df_weekly = df_hist['Volume'].resample('W').sum().reset_index()
                                            df_weekly.columns = ['주 시작일', '거래량']
                                            last_vol = df_weekly['거래량'].iloc[-1] if not df_weekly.empty else 0
                                            volume_lines.append(f"- {etf_name}: 최근 주간 거래량 {last_vol:,.0f}주")
                                            
                                            fig_line = px.line(df_weekly, x='주 시작일', y='거래량', title=f"**{etf_name}** 실제 주간 거래량 추이", markers=True, color_discrete_sequence=['#4da6ff'])
                                            fig_line.update_layout(height=350, template="plotly_dark", yaxis_title="주간 거래량 (주)", xaxis_title=None, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                                            st.plotly_chart(fig_line, use_container_width=True)
                                        except: st.error(f"{etf_name}의 데이터를 불러오지 못했습니다.")
                            if volume_lines:
                                st.session_state.df_volume_summary_text = "\n".join(volume_lines)
            else: st.info("👉 우측 패널에 엑셀 데이터를 업로드해주세요. (비교를 위해 2주 이상의 데이터가 필요합니다)")

        with sub_tabs[3]:
            st.markdown("### 📰 실시간 뉴스 리스트")
            
            top_keyword = "ETF"
            if uploaded_excel is not None and selected_week != "데이터 없음":
                try:
                    df_temp = load_and_clean_excel(uploaded_excel, selected_week)
                    df_temp['테마'] = df_temp['종목명'].apply(assign_auto_theme)
                    top_theme = df_temp[df_temp['종목명'] != '전체'].groupby('테마')['개인'].sum().idxmax()
                    top_keyword = re.sub(r'[^\w\s]', '', top_theme).strip()
                except:
                    pass
            
            st.markdown("#### 🌐 일반 ETF 트렌드 뉴스 (거시/업계 동향)")
            df_general_news = get_realtime_news("ETF", timeframe="7d", max_items=12)
            if "링크" in df_general_news.columns and df_general_news["링크"].iloc[0] != "":
                
                titles_gen = df_general_news["원본제목"].tolist()
                kws_gen = extract_keywords_from_titles(titles_gen, top_n=7)
                if kws_gen:
                    tags_html = "".join([f"<span style='background:rgba(77, 166, 255, 0.15); border: 1px solid rgba(77, 166, 255, 0.4); border-radius: 15px; padding: 4px 10px; margin-right: 8px; font-size: 13px; font-weight: bold; color: #4da6ff;'>#{kw}</span>" for kw in kws_gen])
                    st.markdown(f"<div style='margin-bottom: 15px;'>{tags_html}</div>", unsafe_allow_html=True)

                for i in range(0, len(df_general_news), 2):
                    cols = st.columns(2)
                    for j in range(2):
                        if i + j < len(df_general_news):
                            row = df_general_news.iloc[i + j]
                            with cols[j]:
                                with st.container(border=True):
                                    st.caption(f"📅 {row['게시일 / 출처']}")
                                    st.markdown(f"<a href='{row['링크']}' target='_blank' style='font-size:15px; font-weight:bold; color:#4da6ff; text-decoration:none;'>{row['원본제목']} 🔗</a>", unsafe_allow_html=True)
            else: st.dataframe(df_general_news, use_container_width=True, hide_index=True)
                
            st.divider()

            st.markdown(f"#### 🎯 주간 수급 Top 테마 동적 뉴스 ({top_keyword})")
            search_kw_dynamic = f"{top_keyword} ETF"
            st.session_state.df_real_news = get_realtime_news(search_kw_dynamic, timeframe="7d", max_items=12)
            df_dynamic_news = st.session_state.df_real_news
            
            news_summary = "\n".join([f"- {row['원본제목']}" for _, row in df_dynamic_news.head(5).iterrows()])
            st.session_state.weekly_dynamic_news = f"[{search_kw_dynamic} 검색 결과]\n{news_summary}"
            
            if "링크" in df_dynamic_news.columns and df_dynamic_news["링크"].iloc[0] != "":
                
                titles_dyn = df_dynamic_news["원본제목"].tolist()
                kws_dyn = extract_keywords_from_titles(titles_dyn, top_n=7)
                if kws_dyn:
                    tags_dyn_html = "".join([f"<span style='background:rgba(255, 176, 77, 0.15); border: 1px solid rgba(255, 176, 77, 0.4); border-radius: 15px; padding: 4px 10px; margin-right: 8px; font-size: 13px; font-weight: bold; color: #ffb04d;'>#{kw}</span>" for kw in kws_dyn])
                    st.markdown(f"<div style='margin-bottom: 15px;'>{tags_dyn_html}</div>", unsafe_allow_html=True)

                for i in range(0, len(df_dynamic_news), 2):
                    cols = st.columns(2)
                    for j in range(2):
                        if i + j < len(df_dynamic_news):
                            row = df_dynamic_news.iloc[i + j]
                            with cols[j]:
                                with st.container(border=True):
                                    st.caption(f"📅 {row['게시일 / 출처']}")
                                    st.markdown(f"<a href='{row['링크']}' target='_blank' style='font-size:15px; font-weight:bold; color:#4da6ff; text-decoration:none;'>{row['원본제목']} 🔗</a>", unsafe_allow_html=True)
            else: st.dataframe(df_dynamic_news, use_container_width=True, hide_index=True)

        with sub_tabs[4]:
            sheet_url = st.session_state.get('sheet_url_global', '')
            df_events = load_event_sheet(sheet_url)
            df_ongoing, df_ended = pd.DataFrame(), pd.DataFrame()
            if not df_events.empty and '이벤트명' in df_events.columns:
                today = pd.to_datetime(datetime.today().date())
                df_ongoing = df_events[df_events['종료일'] >= today]
                df_ended = df_events[df_events['종료일'] < today]

            st.markdown("### 🔍 [심화 분석] 마케팅 인과관계 통계 검증 (이중차분 & 시차 상관관계)")
            st.caption("업로드된 실제 데이터(Excel, DataLab)를 바탕으로 Pandas와 Scipy 라이브러리를 통해 진짜 통계 수치를 산출합니다.")
            
            df_trend = pd.DataFrame(columns=['주차', '종목명', '전체순매수']) 
            target_sheets = []
            
            if uploaded_excel is not None and len(available_weeks) > 1 and available_weeks[0] != "데이터 없음":
                temp_list_df = load_and_clean_excel(uploaded_excel, available_weeks[0])
                if not temp_list_df.empty and '종목명' in temp_list_df.columns:
                    all_etf_names = sorted(temp_list_df[temp_list_df['종목명'] != '전체']['종목명'].dropna().unique().tolist())
                    col_sel1, col_sel2 = st.columns(2)
                    with col_sel1:
                        st.markdown("**1. 분석 대상 ETF 선택**")
                        default_target_idx = all_etf_names.index("KODEX 200") if "KODEX 200" in all_etf_names else 0
                        default_comp_idx = all_etf_names.index("TIGER 200") if "TIGER 200" in all_etf_names else (1 if len(all_etf_names) > 1 else 0)
                        
                        target_etf = st.selectbox("🎯 Target 연동 (자사):", options=all_etf_names, index=default_target_idx)
                        st.session_state.p_target_etf = target_etf
                        
                        comp_etf = st.selectbox("⚔️ Competitor ETF (타사):", options=all_etf_names, index=default_comp_idx)
                        st.session_state.p_comp_etf = comp_etf
                    with col_sel2:
                        st.markdown("**2. 차트 조회 기간 설정**")
                        c_a1, c_a2 = st.columns(2)
                        with c_a1: ana_start = st.selectbox("📈 전체 분석 시작 주차:", options=available_weeks[::-1], index=0)
                        with c_a2: ana_end = st.selectbox("📈 전체 분석 종료 주차:", options=available_weeks, index=0)

                    s_idx = available_weeks.index(ana_start)
                    e_idx = available_weeks.index(ana_end)
                    target_sheets = available_weeks[s_idx:e_idx+1] if s_idx < e_idx else available_weeks[e_idx:s_idx+1]
                    target_sheets = target_sheets[::-1] 

                    trend_data = []
                    for w in target_sheets:
                        t_df = load_and_clean_excel(uploaded_excel, w)
                        if not t_df.empty and '종목명' in t_df.columns:
                            t_df = t_df[t_df['종목명'].isin([target_etf, comp_etf])].copy()
                            t_df['전체순매수'] = t_df.get('개인', 0) + t_df.get('기관', 0) + t_df.get('외국인', 0)
                            t_df['주차'] = w
                            trend_data.append(t_df[['주차', '종목명', '전체순매수']])
                    
                    if trend_data:
                        df_trend = pd.concat(trend_data)

                    with st.container(border=True):
                        col_evt1, col_evt2 = st.columns([1, 3])
                        with col_evt1:
                            if target_sheets:
                                if st.session_state.get('t0_week_state') not in target_sheets:
                                    st.session_state.t0_week_state = target_sheets[len(target_sheets)//2]
                            
                            event_start_week = st.selectbox("📍 이벤트가 발생한 기준 주차 (T=0):", target_sheets, key="t0_week_state")
                        
                        with col_evt2:
                            if event_start_week:
                                st.info(f"**DiD 설계:** '{event_start_week}' 이전 기간을 **Pre**, 이후 기간을 **Post**로 지정하여 실제 순매수 증감을 계산합니다.")
                            else:
                                st.warning("**DiD 설계:** 기준 주차(T=0)를 먼저 선택해 주세요.")
                    
                    with st.spinner("Scipy 및 Pandas로 실제 통계값을 연산 중입니다..."):
                        pre_weeks = target_sheets[:target_sheets.index(event_start_week)] if event_start_week in target_sheets else []
                        post_weeks = target_sheets[target_sheets.index(event_start_week):] if event_start_week in target_sheets else []
                        
                        target_pre_sum = df_trend[(df_trend['종목명'] == target_etf) & (df_trend['주차'].isin(pre_weeks))]['전체순매수'].sum() if pre_weeks else 0
                        target_post_sum = df_trend[(df_trend['종목명'] == target_etf) & (df_trend['주차'].isin(post_weeks))]['전체순매수'].sum() if post_weeks else 0
                        comp_pre_sum = df_trend[(df_trend['종목명'] == comp_etf) & (df_trend['주차'].isin(pre_weeks))]['전체순매수'].sum() if pre_weeks else 0
                        comp_post_sum = df_trend[(df_trend['종목명'] == comp_etf) & (df_trend['주차'].isin(post_weeks))]['전체순매수'].sum() if post_weeks else 0

                        target_diff = target_post_sum - target_pre_sum
                        comp_diff = comp_post_sum - comp_pre_sum
                        
                        real_did_multiplier = float('inf')
                        if comp_diff > 0 and target_diff > 0:
                            real_did_multiplier = round(target_diff / comp_diff, 2)
                        elif comp_diff == 0:
                            real_did_multiplier = round(target_diff, 2)

                        calc_p_value = None
                        brand_search_inc = None
                        lag_corrs = []
                        data_year = datetime.today().year
                        
                        if uploaded_dls and event_start_week:
                            try:
                                dl_file = uploaded_dls[0]
                                df_dl = pd.read_csv(dl_file, skiprows=6, encoding='cp949') if dl_file.name.endswith('csv') else pd.read_excel(dl_file, skiprows=6)
                                date_col = df_dl.columns[0]
                                df_dl[date_col] = pd.to_datetime(df_dl[date_col])
                                
                                if not df_dl[date_col].empty:
                                    data_year = df_dl[date_col].dt.year.max()
                                
                                val_cols = [c for c in df_dl.columns if '날짜' not in c and 'Unnamed' not in c]
                                
                                if val_cols:
                                    first_col = val_cols[0]
                                    
                                    evt_month, evt_day = map(int, event_start_week.split('-')[0].split('.'))
                                    evt_date = datetime(int(data_year), evt_month, evt_day)
                                    
                                    pre_data = df_dl[df_dl[date_col] < evt_date][first_col].dropna()
                                    post_data = df_dl[df_dl[date_col] >= evt_date][first_col].dropna()
                                    
                                    if len(pre_data) > 2 and len(post_data) > 2:
                                        t_stat, p_val = stats.ttest_ind(pre_data, post_data, equal_var=False)
                                        calc_p_value = p_val
                                        pre_mean, post_mean = post_data.mean(), post_data.mean()
                                        if pre_mean > 0:
                                            brand_search_inc = round(((post_mean - pre_mean) / pre_mean) * 100, 1)

                                    dl_weekly_search = {}
                                    for w in target_sheets:
                                        s_dt, e_dt = parse_week_range(w, data_year)
                                        if s_dt and e_dt:
                                            mask = (df_dl[date_col] >= s_dt) & (df_dl[date_col] <= e_dt)
                                            avg_search = df_dl.loc[mask, first_col].mean()
                                            dl_weekly_search[w] = avg_search
                                        else:
                                            dl_weekly_search[w] = np.nan
                                            
                                    target_trend = df_trend[df_trend['종목명'] == target_etf].copy()
                                    chronological_weeks = list(reversed(target_sheets))
                                    target_trend['주차_순서'] = pd.Categorical(target_trend['주차'], categories=chronological_weeks, ordered=True)
                                    target_trend = target_trend.sort_values('주차_순서').reset_index(drop=True)
                                    
                                    target_trend['검색량'] = target_trend['주차'].map(dl_weekly_search)
                                    
                                    if len(target_trend) >= 4:
                                        for lag in range(5):
                                            shifted_search = target_trend['검색량'].shift(lag)
                                            valid_data = pd.concat([target_trend['전체순매수'], shifted_search], axis=1).dropna()
                                            if len(valid_data) >= 3:
                                                r = valid_data.corr().iloc[0, 1]
                                                lag_corrs.append(r if not pd.isna(r) else 0)
                                            else:
                                                lag_corrs.append(0)
                            except Exception as e:
                                st.error(f"통계 연산 중 오류 발생: {e}")

                        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                        with col_m1:
                            sign = "+" if target_diff > 0 else ""
                            st.metric("타겟 ETF 순매수 변동(설정효과)", f"{sign}{target_diff:,.0f}억원", "Pre 대비 Post 누적", delta_color="normal")
                        with col_m2:
                            mult_str = f"{real_did_multiplier}배" if real_did_multiplier != float('inf') else "압도적 우위"
                            st.metric("이중차분(DiD) 성과 배수", mult_str, f"대조군({comp_etf}) 변동 대비", delta_color="normal")
                        with col_m3:
                            if brand_search_inc is not None:
                                s_sign = "+" if brand_search_inc > 0 else ""
                                st.metric("브랜드 검색 관심도 변화", f"{s_sign}{brand_search_inc}%", "데이터랩 기준", delta_color="normal")
                            else:
                                st.metric("브랜드 검색 관심도", "데이터 없음", "DataLab 업로드 필요", delta_color="off")
                        with col_m4:
                            if calc_p_value is not None:
                                p_text = f"p < 0.001" if calc_p_value < 0.001 else f"p = {calc_p_value:.3f}"
                                p_desc = "유의미함 (p < 0.05)" if calc_p_value < 0.05 else "유의미하지 않음"
                                st.metric("통계적 유의성 (Welch's t-test)", p_text, p_desc, delta_color="normal" if calc_p_value < 0.05 else "inverse")
                            else:
                                st.metric("통계적 유의성", "계산 불가", "검색량 데이터 부족", delta_color="off")

                        st.session_state.stat_net_inflow = round(target_diff, 2)
                        st.session_state.stat_did_multiplier = real_did_multiplier
                        st.session_state.stat_p_value = round(calc_p_value, 4) if calc_p_value is not None else 1.0

                        c_chart1, c_chart2 = st.columns([1, 1])
                        with c_chart1:
                            with st.container(border=True):
                                st.markdown("**📊 시장효과 vs 설정효과 분해 추정치**")
                                try:
                                    end_dt = datetime.today()
                                    start_dt = end_dt - timedelta(weeks=len(target_sheets)+2)
                                    ks_df = fdr.DataReader('KS11', start_dt, end_dt)
                                    ks_weekly = ks_df['Close'].resample('W-MON').last().pct_change() * 100
                                    
                                    market_eff = []
                                    setup_eff = []
                                    valid_weeks = []
                                    
                                    for w in target_sheets:
                                        w_date, _ = parse_week_range(w, data_year)
                                        val = df_trend[(df_trend['종목명'] == target_etf) & (df_trend['주차'] == w)]['전체순매수'].sum()
                                        
                                        if w_date:
                                            nearest_idx = ks_weekly.index.get_indexer([w_date], method='nearest')[0]
                                            idx_ret = ks_weekly.iloc[nearest_idx] if nearest_idx >= 0 else 0
                                            m_eff = val * (abs(idx_ret)/10) if not pd.isna(idx_ret) else 0 
                                            s_eff = val - m_eff
                                            market_eff.append(m_eff)
                                            setup_eff.append(s_eff)
                                            valid_weeks.append(w)

                                    fig_decomp = go.Figure(data=[
                                        go.Bar(name='시장효과 (지수변동 추정)', x=valid_weeks, y=market_eff, marker_color='gray'),
                                        go.Bar(name='순수 설정효과 (순매수)', x=valid_weeks, y=setup_eff, marker_color='#ff4d4d')
                                    ])
                                    fig_decomp.update_layout(barmode='stack', height=350, margin=dict(t=10, b=10, l=10, r=10), template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5))
                                    st.plotly_chart(fig_decomp, use_container_width=True)
                                except:
                                    st.info("시장효과를 분리할 기초 지수 데이터 매칭에 실패했습니다.")
                                    
                        with c_chart2:
                            with st.container(border=True):
                                st.markdown("**⏱️ 시차 상관관계 (Lag Cross Correlation)**")
                                if lag_corrs and any(lag_corrs) and len(lag_corrs) == 5:
                                    lags = ["0주 (당일)", "+1주", "+2주", "+3주", "+4주"]
                                    max_idx = np.argmax(lag_corrs)
                                    colors = ['gray'] * 5
                                    colors[max_idx] = '#4da6ff'
                                    
                                    fig_lag = go.Figure(data=[
                                        go.Bar(x=lags, y=lag_corrs, marker_color=colors, text=[f"{c:.2f}" for c in lag_corrs], textposition='auto')
                                    ])
                                    fig_lag.add_annotation(x=lags[max_idx], y=lag_corrs[max_idx], text=f"최대 상관 시점", showarrow=True, arrowhead=1, arrowcolor="#ffb04d", font=dict(color="#ffb04d", size=13), yshift=10)
                                    fig_lag.update_layout(height=350, yaxis_title="Pearson (r)", xaxis_title="경과 시간", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                                    st.plotly_chart(fig_lag, use_container_width=True)
                                else:
                                    st.warning("실제 데이터랩과 주간 순매수 간 매칭되는 데이터 기간이 부족하여 상관계수를 도출할 수 없습니다. (데이터랩과 순매수 엑셀의 날짜 구간을 맞춰주세요.)")
            else:
                st.warning("👉 위의 '분석 대상 ETF' 및 '조회 기간' 설정과 엑셀 업로드가 선행되어야 통계 분석이 가능합니다.")

            st.divider()

            st.markdown("### 📊 마케팅 촉매(이벤트/영상) 임팩트 분석기")
            if not df_trend.empty:
                selected_ongoing = []
                selected_ended = []
                if not df_events.empty and '이벤트명' in df_events.columns:
                    c_evt1, c_evt2 = st.columns(2)
                    with c_evt1:
                        ongoing_list = df_ongoing['이벤트명'].tolist() if not df_ongoing.empty else []
                        selected_ongoing = st.multiselect("🟢 진행 중인 이벤트 (차트 음영 표시):", options=ongoing_list)
                    with c_evt2:
                        ended_list = df_ended['이벤트명'].tolist() if not df_ended.empty else []
                        selected_ended = st.multiselect("🔴 종료된 이벤트 (차트 음영 표시):", options=ended_list)
                else:
                    st.warning("이벤트 시트가 연동되지 않아 음영 매핑 기능이 비활성화되었습니다.")

                all_selected = selected_ongoing + selected_ended

                st.markdown("**💰 이벤트 마케팅 예산 vs 파급력(수급/트렌드) 효율성 분석**")
                if len(all_selected) >= 2 and not df_events.empty:
                    event_scatter_data = []
                    for evt_name in all_selected:
                        row_e = df_events[df_events['이벤트명'] == evt_name].iloc[0]
                        budget = row_e.get('경품예산', 0)
                        brand = row_e.get('ETF 브랜드', '기타')
                        
                        est_y = df_trend[(df_trend['주차'] >= event_start_week) & (df_trend['종목명'] == target_etf)]['전체순매수'].mean() if not df_trend.empty else 0
                        
                        event_scatter_data.append({
                            "이벤트명": evt_name,
                            "브랜드": brand,
                            "경품예산(원)": budget,
                            "파급력(주간평균 유입액)": est_y
                        })
                        
                    df_evt_scatter = pd.DataFrame(event_scatter_data)
                    fig_evt_scatter = px.scatter(df_evt_scatter, x="경품예산(원)", y="파급력(주간평균 유입액)", text="이벤트명", color="브랜드", size="경품예산(원)", hover_data=["경품예산(원)"])
                    fig_evt_scatter.update_traces(textposition='top center', marker=dict(opacity=0.8), textfont=dict(size=11, color='lightgray'))
                    fig_evt_scatter.update_layout(height=350, margin=dict(l=10,r=10,t=20,b=10), template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_evt_scatter, use_container_width=True)
                    st.caption("우측 상단으로 갈수록 고비용-고효율, 좌측 상단에 위치할수록 저비용-고효율(바이럴 굿즈 등) 이벤트입니다.")
                elif len(all_selected) == 1:
                    st.info("💡 이벤트 마케팅 예산 vs 파급력 산점도는 비교 분석을 위해 이벤트를 2개 이상 선택해야 활성화됩니다.")
                else:
                    st.info("💡 이벤트 드롭다운에서 분석할 이벤트를 선택하시면 예산 대비 효율성 산점도가 활성화됩니다.")

                with st.spinner("수급 임팩트 데이터를 렌더링하고 있습니다..."):
                    fig_evt = px.line(df_trend, x='주차', y='전체순매수', color='종목명', markers=True, template="plotly_dark", color_discrete_map={target_etf: '#ff4d4d', comp_etf: '#4da6ff'})
                    
                    vol_data = []
                    symbols_mapping = get_etf_mapping()
                    sym_target = symbols_mapping.get(target_etf)
                    sym_comp = symbols_mapping.get(comp_etf)
                    
                    data_year = datetime.today().year
                    try:
                        all_parsed_dates = [parse_week_range(w, data_year) for w in target_sheets]
                        valid_starts = [d[0] for d in all_parsed_dates if d[0] is not None]
                        valid_ends = [d[1] for d in all_parsed_dates if d[1] is not None]
                        
                        if valid_starts and valid_ends:
                            s_dt_min = min(valid_starts) - timedelta(days=7)
                            e_dt_max = max(valid_ends) + timedelta(days=7)
                            df_target_hist = fdr.DataReader(sym_target, s_dt_min, e_dt_max) if sym_target else pd.DataFrame()
                            df_comp_hist = fdr.DataReader(sym_comp, s_dt_min, e_dt_max) if sym_comp else pd.DataFrame()
                        else:
                            df_target_hist, df_comp_hist = pd.DataFrame(), pd.DataFrame()
                    except Exception as e:
                        df_target_hist = pd.DataFrame()
                        df_comp_hist = pd.DataFrame()
                        
                    for w in target_sheets:
                        s_dt, e_dt = parse_week_range(w, data_year)
                        v_target, v_comp = 0, 0
                        if s_dt and e_dt:
                            try:
                                s_str = s_dt.strftime('%Y-%m-%d')
                                e_str = e_dt.strftime('%Y-%m-%d')
                                if not df_target_hist.empty: v_target = df_target_hist.loc[s_str:e_str, 'Volume'].sum()
                                if not df_comp_hist.empty: v_comp = df_comp_hist.loc[s_str:e_str, 'Volume'].sum()
                            except: pass
                        vol_data.append({'주차': w, '종목명': target_etf, '거래량': v_target})
                        vol_data.append({'주차': w, '종목명': comp_etf, '거래량': v_comp})
                        
                    df_vol = pd.DataFrame(vol_data)
                    
                    fig_vol = px.line(df_vol, x='주차', y='거래량', color='종목명', markers=True, template="plotly_dark", color_discrete_map={target_etf: '#ff4d4d', comp_etf: '#4da6ff'})

                    BRAND_COLORS = {
                        'KODEX': 'rgba(10, 88, 202, 0.2)',
                        'TIGER': 'rgba(255, 114, 0, 0.2)',
                        'ACE': 'rgba(0, 166, 126, 0.2)',
                        'RISE': 'rgba(255, 186, 0, 0.2)',
                        'DEFAULT': 'rgba(128, 128, 128, 0.2)'
                    }

                    def find_closest_week_str(dt, weeks_list):
                        if pd.isnull(dt) or not weeks_list: return None
                        best_w = weeks_list[-1]
                        min_diff = float('inf')
                        for w in weeks_list:
                            try:
                                s_str = w.split('-')[0]
                                s_m, s_d = map(int, s_str.split('.'))
                                w_dt = datetime(dt.year, s_m, s_d)
                                diff = abs((dt - w_dt).days)
                                if diff < min_diff:
                                    min_diff = diff
                                    best_w = w
                            except: pass
                        return best_w

                    for evt_name in all_selected:
                        evt_row = df_events[df_events['이벤트명'] == evt_name].iloc[0]
                        e_start = evt_row['시작일']
                        e_end = evt_row['종료일']
                        e_brand = evt_row.get('ETF 브랜드', '')
                        
                        x0_str = find_closest_week_str(e_start, target_sheets)
                        x1_str = find_closest_week_str(e_end, target_sheets)
                        
                        color = BRAND_COLORS.get(e_brand, BRAND_COLORS['DEFAULT'])
                        
                        if x0_str and x1_str:
                            try:
                                fig_evt.add_vrect(
                                    x0=x0_str, x1=x1_str, fillcolor=color.replace('0.2', '0.15'), opacity=1, layer="below", 
                                    line_width=1, line_dash="dash", line_color=color.replace('0.2', '0.8'),
                                    annotation_text=evt_name[:10] + '..' if len(evt_name) > 10 else evt_name, 
                                    annotation_position="top left", annotation_font_size=11, annotation_font_color=color.replace('0.2', '1.0')
                                )
                                fig_vol.add_vrect(
                                    x0=x0_str, x1=x1_str, fillcolor=color.replace('0.2', '0.15'), opacity=1, layer="below", 
                                    line_width=1, line_dash="dash", line_color=color.replace('0.2', '0.8'),
                                    annotation_text=evt_name[:10] + '..' if len(evt_name) > 10 else evt_name, 
                                    annotation_position="top left", annotation_font_size=11, annotation_font_color=color.replace('0.2', '1.0')
                                )
                            except: pass

                    fig_evt.update_layout(height=400, margin=dict(l=20, r=20, t=20, b=20), xaxis_title=None, yaxis_title="전체 순매수 금액 합계", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5))
                    fig_vol.update_layout(height=400, margin=dict(l=20, r=20, t=20, b=20), xaxis_title=None, yaxis_title="주간 거래량 합계 (거래대금 프록시)", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
                    
                    with st.container(border=True):
                        st.markdown("##### 1️⃣ 이벤트 기반 [전체 순매수] 추이 궤적")
                        st.plotly_chart(fig_evt, use_container_width=True)
                    
                    with st.container(border=True):
                        st.markdown("##### 2️⃣ 이벤트 기반 [거래대금/거래량] 추이 궤적")
                        st.plotly_chart(fig_vol, use_container_width=True)

            else:
                st.info("👉 우측 패널에 엑셀 데이터를 업로드하시면 성과 분석기 차트가 활성화됩니다.")

            st.divider()

            st.markdown("### 📢 운용사별 이벤트 모니터링 (Sheet 연동)")
            if not df_events.empty and '이벤트명' in df_events.columns:
                evt_tab1, evt_tab2 = st.tabs(["🟢 진행 중인 이벤트", "🔴 종료된 이벤트"])
                
                with evt_tab1:
                    if not df_ongoing.empty:
                        for brand, group in df_ongoing.groupby('ETF 브랜드'):
                            with st.expander(f"🔵 {brand} ({len(group)}건)", expanded=True):
                                for _, row in group.iterrows():
                                    start_str = row['시작일'].strftime('%Y.%m.%d') if pd.notna(row.get('시작일')) else "미상"
                                    end_str = row['종료일'].strftime('%Y.%m.%d') if pd.notna(row.get('종료일')) else "미상"
                                    st.markdown(f"- **{row.get('이벤트명', '')}** (대상: {row.get('대상 ETF의 종목 코드', '')}) | {start_str} ~ {end_str}")
                    else:
                        st.write("진행 중인 이벤트가 없습니다.")
                        
                with evt_tab2:
                    if not df_ended.empty:
                        for brand, group in df_ended.groupby('ETF 브랜드'):
                            with st.expander(f"🔴 {brand} ({len(group)}건)", expanded=False):
                                for _, row in group.iterrows():
                                    start_str = row['시작일'].strftime('%Y.%m.%d') if pd.notna(row.get('시작일')) else "미상"
                                    end_str = row['종료일'].strftime('%Y.%m.%d') if pd.notna(row.get('종료일')) else "미상"
                                    st.markdown(f"- **{row.get('이벤트명', '')}** (대상: {row.get('대상 ETF의 종목 코드', '')}) | {start_str} ~ {end_str}")
                    else:
                        st.write("종료된 이벤트가 없습니다.")
            else:
                st.info("👉 우측 패널 '1. 이벤트 시트 링크' 칸에 구글 스프레드시트 공유 링크를 입력해주세요.")
            
            st.divider()

            st.markdown("### 📊 키워드 검색비율 추이 (다중 비교 지원)")
            if uploaded_dls:
                dl_summaries = []
                for dl_file in uploaded_dls:
                    try:
                        file_name_without_ext = dl_file.name.rsplit('.', 1)[0]
                        st.markdown(f"#### 📉 {file_name_without_ext}")
                        df_dl = pd.read_csv(dl_file, skiprows=6, encoding='cp949') if dl_file.name.endswith('csv') else pd.read_excel(dl_file, skiprows=6)
                        if not df_dl.empty:
                            master_date = df_dl.iloc[:, 0]
                            value_cols = [col for col in df_dl.columns if '날짜' not in col and 'Unnamed' not in col]
                            clean_df = pd.DataFrame({'날짜': master_date})
                            for col in value_cols: clean_df[col] = df_dl[col]
                            clean_df['날짜'] = pd.to_datetime(clean_df['날짜'])
                            recent_14d_mean = clean_df.tail(14).mean(numeric_only=True).round(1)
                            dl_summaries.append(f"[{file_name_without_ext}]\n" + "\n".join([f"- {idx}: {val}" for idx, val in recent_14d_mean.items()]))
                            df_melted = clean_df.melt(id_vars=['날짜'], var_name='종목명', value_name='검색량')
                            with st.container(border=True):
                                fig_trend = px.line(df_melted, x='날짜', y='검색량', color='종목명', template="plotly_dark")
                                fig_trend.update_layout(height=350, xaxis_title=None, yaxis_title="상대적 검색량", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5))
                                st.plotly_chart(fig_trend, use_container_width=True)
                    except: pass
                st.session_state['dl_summary'] = "\n\n".join(dl_summaries) if dl_summaries else "데이터랩 연동 오류"
            else: st.info("👉 우측 패널에 Naver DataLab 파일을 업로드해 주세요.")

            st.divider()

            st.markdown("### 📺 유튜브 사후 성과 분석 (Post-Hoc Analysis)")
            current_target = target_etf if 'target_etf' in locals() else "KODEX 200"
            current_comp = comp_etf if 'comp_etf' in locals() else "TIGER 200"
            
            top_keyword = "ETF"
            if uploaded_excel is not None and selected_week != "데이터 없음":
                try:
                    df_temp = load_and_clean_excel(uploaded_excel, selected_week)
                    df_temp['테마'] = df_temp['종목명'].apply(assign_auto_theme)
                    top_theme = df_temp[df_temp['종목명'] != '전체'].groupby('테마')['개인'].sum().idxmax()
                    top_keyword = re.sub(r'[^\w\s]', '', top_theme).strip()
                except:
                    pass
            current_theme = top_keyword
            
            yt_keywords = {
                f"🎯 자사 타겟 ({current_target})": current_target, 
                f"⚔️ 경쟁 대조군 ({current_comp})": current_comp,
                f"🔥 주간 핫 테마 ({current_theme} ETF)": f"{current_theme} ETF"
            }
            
            with st.spinner("타겟 종목 및 경쟁사 유튜브 영상 성과를 실시간으로 비교 파싱 중입니다..."):
                yt_data = []
                for brand, kw in yt_keywords.items():
                    vids = scrape_youtube_search_real(kw)
                    for v in vids: yt_data.append({"검색 타겟": brand, "영상 제목": v['title'], "조회수": v['views'], "업로드": v['date'], "링크": v['link']})
                
                if yt_data:
                    df_yt = pd.DataFrame(yt_data)
                    df_yt_sorted = df_yt.sort_values(by="조회수", ascending=False)
                    
                    target_vids = df_yt[df_yt['검색 타겟'].str.contains("🎯")].sort_values(by="조회수", ascending=False)
                    if not target_vids.empty:
                        top_vid = target_vids.iloc[0]
                        st.session_state.yt_target_insights = f"타겟 종목({current_target}) 최고 바이럴 영상: '{top_vid['영상 제목']}' (조회수 {top_vid['조회수']:,}회) - 업로드 시기: {top_vid['업로드']}"
                    else:
                        st.session_state.yt_target_insights = f"타겟 종목({current_target}) 관련 유의미한 유튜브 바이럴 없음."

                    c_yt1, c_yt2 = st.columns([1, 1])
                    with c_yt1:
                        st.markdown("#### 🏆 타겟 vs 대조군 관련 영상 평균 조회수")
                        df_agg = df_yt.groupby("검색 타겟")["조회수"].mean().reset_index()
                        
                        color_map = {
                            f"🎯 자사 타겟 ({current_target})": '#ff4d4d',
                            f"⚔️ 경쟁 대조군 ({current_comp})": '#4da6ff',
                            f"🔥 주간 핫 테마 ({current_theme} ETF)": '#ffb04d'
                        }
                        
                        fig_yt = px.bar(df_agg, x="검색 타겟", y="조회수", text_auto='.0f', color="검색 타겟", color_discrete_map=color_map, template="plotly_dark")
                        fig_yt.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False, xaxis_title=None)
                        st.plotly_chart(fig_yt, use_container_width=True)
                    with c_yt2:
                        st.markdown("#### 📝 실시간 영상 성과 및 업로드 타이밍")
                        st.dataframe(df_yt_sorted[["검색 타겟", "영상 제목", "조회수", "업로드"]], use_container_width=True, height=350, hide_index=True)

            st.divider()

            st.markdown("### 🏢 운용사별 블로그 포스트")
            brand_mappings = {
                "KODEX (삼성)": {"blog": "etf_kodex"}, 
                "TIGER (미래에셋)": {"blog": "m_invest"},
                "ACE (한국투자)": {"blog": "aceetf"}, "RISE (KB)": {"blog": "riseetf"},
                "SOL (신한)": {"blog": "soletf"}, "PLUS (한화)": {"blog": "hanwhaasset"},
                "HANARO (NH아문디)": {"blog": "nh_amundi"}, "1Q (하나)": {"blog": "1qetf"},
                "TIMEFOLIO (타임폴리오)": {"blog": "timefolioetf"}, "KIWOOM (키움)": {"blog": "kiwoomammkt"},
                "WON (우리)": {"blog": "wooriam_kr"}
            }
            
            with st.spinner("지난주(일~토) 블로그 포스트를 스크래핑 중입니다..."):
                kodex_posts = parse_competitor_blog_last_week(brand_mappings["KODEX (삼성)"]["blog"])
                other_posts = {}
                empty_brands = []
                
                for brand, items in brand_mappings.items():
                    if brand == "KODEX (삼성)": continue
                    posts = parse_competitor_blog_last_week(items['blog'])
                    if posts:
                        other_posts[brand] = posts
                    else:
                        empty_brands.append(brand.split(' ')[0])
                        
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**🔵 KODEX (삼성) 블로그**")
                    if kodex_posts:
                        for p in kodex_posts:
                            st.markdown(f"- [{p['date']}] <a href='{p['link']}' target='_blank' style='color:#4da6ff; text-decoration:none;'>{p['title']}</a>", unsafe_allow_html=True)
                    else:
                        st.info("지난 주 KODEX 블로그에 올라온 포스트가 없습니다.")
                        
                with c2:
                    st.markdown("**🔵 기타 운용사 블로그**")
                    if other_posts:
                        for brand, posts in other_posts.items():
                            with st.expander(f"{brand} ({len(posts)}건)"):
                                for p in posts:
                                    st.markdown(f"- [{p['date']}] <a href='{p['link']}' target='_blank' style='color:#4da6ff; text-decoration:none;'>{p['title']}</a>", unsafe_allow_html=True)
                    else:
                        st.info("지난 주 기타 운용사 블로그에 올라온 포스트가 없습니다.")
                
                if empty_brands:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.warning(f"💤 **지난주 신규 포스팅 없음 (모니터링 대상):** {', '.join(empty_brands)}")

        with sub_tabs[5]:
            st.markdown("### 🗣️ 고객 Voice (VOC) & 투자자 심리 모니터링")

            # =====================================================================
            # [신규 추가] Sub-Agent 다운로드 및 사용 가이드 영역
            # =====================================================================
            with st.container(border=True):
                st.markdown("#### 🤖 [데이터 수집] 네이버 종토방 크롤링 Sub-Agent")
                st.caption("메인 대시보드에 연동할 종토방 엑셀 데이터를 추출하고 1차 감성분석을 수행하는 외부 코드입니다.")
                
                try:
                    with open("naver_jongtobang_crawler.ipynb", "r", encoding="utf-8") as f:
                        ipynb_raw_text = f.read()
                        
                    st.download_button(
                        label="📥 Sub-Agent 파이썬 코드 다운로드 (.ipynb)",
                        data=ipynb_raw_text.encode('utf-8'),
                        file_name="naver_jongtobang_crawler_분석.ipynb",
                        mime="application/json",
                        use_container_width=True
                    )
                except FileNotFoundError:
                    st.error("⚠️ 'naver_jongtobang_crawler.ipynb' 파일을 찾을 수 없습니다. 깃허브 최상위 경로에 파일이 업로드되었는지 확인해주세요.")
                    ipynb_raw_text = "파일을 찾을 수 없습니다."

                with st.expander("💡 Sub-Agent 사용 가이드 (클릭하여 펼치기)"):
                    st.markdown("""
                    **[Sub-Agent 실행 및 대시보드 연동 방법]**
                    1. **환경 세팅:** 다운로드한 `.ipynb` 파일을 **Google Colab** 또는 로컬 Jupyter 환경에서 엽니다.
                    2. **변수 설정:** 코드 두 번째 셀의 `STOCK_CODE`(종목코드)와 `TARGET_DATE`(수집 날짜)를 분석하고자 하는 타겟으로 변경합니다.
                    3. **데이터 수집:** 위에서부터 순서대로 셀을 실행하여 크롤링 및 감성 분석을 진행합니다.
                    4. **파일 획득:** 실행이 모두 완료되면 하단에서 통합 분석 결과가 담긴 **엑셀 파일이 자동 다운로드**됩니다.
                    5. **대시보드 연동:** 다운로드된 엑셀 파일을 본 대시보드 우측 패널의 **'4. 종토방 VOC 엑셀'** 칸에 업로드하시면 아래 시각화 차트가 즉시 활성화됩니다.
                    """)
                
                with st.expander("💻 Sub-Agent 전체 코드 미리보기"):
                    st.info("파일 다운로드 없이 바로 코드를 복사해서 사용하실 분들을 위한 영역입니다.")
                    st.code(ipynb_raw_text, language="python")

            st.divider()

            with st.container(border=True):
                st.markdown("#### 📊 [Sub-Agent 연동] 네이버 종토방 분석 결과 시각화")
                if uploaded_voc is not None:
                    voc_data = {}
                    try:
                        xls_voc = pd.ExcelFile(uploaded_voc)
                        for sheet in xls_voc.sheet_names:
                            df_raw = pd.read_excel(xls_voc, sheet_name=sheet)
                            sheet_lower = str(sheet).lower()
                            if '감성' in sheet_lower:
                                df_parsed = extract_table(df_raw, ['감성', '비율'])
                                for c in df_parsed.columns:
                                    if '감성' in str(c) and str(c) != '평균 감성점수': df_parsed.rename(columns={c: '감성'}, inplace=True)
                                    if '비율' in str(c): df_parsed.rename(columns={c: '비율(%)'}, inplace=True)
                                voc_data['sentiment'] = df_parsed
                            elif '키워드' in sheet_lower:
                                df_parsed = extract_table(df_raw, ['키워드', '언급'])
                                for c in df_parsed.columns:
                                    if '키워드' in str(c): df_parsed.rename(columns={c: '키워드'}, inplace=True)
                                    if '언급' in str(c): df_parsed.rename(columns={c: '언급횟수'}, inplace=True)
                                voc_data['keyword'] = df_parsed
                            elif '시간' in sheet_lower:
                                df_parsed = extract_table(df_raw, ['시간', '게시글'])
                                for c in df_parsed.columns:
                                    if '시간' in str(c): df_parsed.rename(columns={c: '시간대'}, inplace=True)
                                    if '게시글' in str(c): df_parsed.rename(columns={c: '게시글 수'}, inplace=True)
                                    if '감성' in str(c): df_parsed.rename(columns={c: '평균 감성점수'}, inplace=True)
                                voc_data['time'] = df_parsed
                            elif '인사이트' in sheet_lower or '요약' in sheet_lower:
                                texts = [" ".join([str(v) for v in row.values if pd.notna(v) and str(v).strip() != '']) for _, row in df_raw.iterrows()]
                                voc_data['insight'] = "\n\n".join([t for t in texts if t.strip()])
                            elif '게시글' in sheet_lower or '전체' in sheet_lower or '원문' in sheet_lower:
                                df_parsed = extract_table(df_raw, ['제목', '본문'])
                                for c in df_parsed.columns:
                                    if '제목' in str(c): df_parsed.rename(columns={c: '제목'}, inplace=True)
                                    if '본문' in str(c): df_parsed.rename(columns={c: '본문'}, inplace=True)
                                    if '조회' in str(c): df_parsed.rename(columns={c: '조회수'}, inplace=True)
                                    if '감성' in str(c) and str(c) != '평균 감성점수': df_parsed.rename(columns={c: '감성'}, inplace=True)
                                    if '작성자' in str(c): df_parsed.rename(columns={c: '작성자'}, inplace=True)
                                    if '날짜' in str(c): df_parsed.rename(columns={c: '날짜'}, inplace=True)
                                voc_data['posts'] = df_parsed
                    except Exception as e: st.error(f"엑셀 파일 파싱 오류: {e}")

                    c_voc1, c_voc2 = st.columns(2)
                    with c_voc1:
                        st.markdown("##### 🌡️ 실시간 투자자 심리 온도계")
                        if 'sentiment' in voc_data and not voc_data['sentiment'].empty:
                            try:
                                df_s = voc_data['sentiment'].dropna(subset=['감성'])
                                fig_s = px.pie(df_s, names='감성', values='비율(%)', hole=0.5, color='감성', color_discrete_map={'긍정':'#4da6ff', '중립':'#cbd5e1', '부정':'#ff4d4d'})
                                fig_s.update_layout(height=300, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                                st.plotly_chart(fig_s, use_container_width=True)
                            except: pass
                    with c_voc2:
                        st.markdown("##### 🧠 리테일 투자자 핫 키워드 Top 10")
                        if 'keyword' in voc_data and not voc_data['keyword'].empty:
                            try:
                                df_k = voc_data['keyword'].dropna(subset=['키워드']).head(10)
                                fig_k = px.bar(df_k, x='언급횟수', y='키워드', orientation='h', template="plotly_dark", color_discrete_sequence=['#ffb04d'])
                                fig_k.update_layout(yaxis={'categoryorder':'total ascending'}, height=300, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                                st.plotly_chart(fig_k, use_container_width=True)
                            except: pass

                    st.divider()
                    st.markdown("##### ⏰ 커뮤니티 골든 타임 추적기 (시간대별 활동)")
                    if 'time' in voc_data and not voc_data['time'].empty:
                        try:
                            df_t = voc_data['time'].dropna(subset=['시간대'])
                            fig_t = go.Figure()
                            fig_t.add_trace(go.Bar(x=df_t['시간대'], y=df_t['게시글 수'], name='게시글 수', marker_color='#4da6ff', yaxis='y1'))
                            fig_t.add_trace(go.Scatter(x=df_t['시간대'], y=df_t['평균 감성점수'], name='평균 감성점수', mode='lines+markers', marker_color='#ffb04d', yaxis='y2'))
                            fig_t.update_layout(height=350, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', yaxis=dict(title='게시글 수', side='left'), yaxis2=dict(title='평균 감성점수', overlaying='y', side='right', range=[1, 5]), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5))
                            st.plotly_chart(fig_t, use_container_width=True)
                        except: pass

                    st.divider()
                    st.markdown("##### 🗣️ 딥다이브 인사이트 & 날것의 목소리 (Raw VOC)")
                    with st.container(border=True):
                        if 'posts' in voc_data and not voc_data['posts'].empty:
                            try:
                                df_p = voc_data['posts'].copy()
                                if '조회수' in df_p.columns:
                                    df_p['조회수'] = pd.to_numeric(df_p['조회수'], errors='coerce').fillna(0)
                                    top_posts = df_p.sort_values(by='조회수', ascending=False).head(3)
                                    for _, row in top_posts.iterrows():
                                        sentiment_color = "#ff4d4d" if "부정" in str(row.get('감성','')) else ("#4da6ff" if "긍정" in str(row.get('감성','')) else "#cbd5e1")
                                        st.markdown(f"**<span style='color:{sentiment_color}'>[{row.get('감성', '분류없음')}]</span> {row.get('제목', '제목없음')}** <span style='color:#ffb04d; font-size:12px;'>(👁️ {int(row['조회수'])})</span>", unsafe_allow_html=True)
                                        content = str(row.get('본문', '')).replace('nan', '')
                                        st.info(f"{content[:200]}..." if len(content) > 200 else content)
                            except: pass
                    
                    with st.expander("💡 AI Sub-Agent 분석 요약 (클릭하여 펼치기)", expanded=False):
                        if 'insight' in voc_data and voc_data['insight'].strip():
                            insight_html = voc_data['insight'].replace(chr(10), '<br>').replace('【', '<br><b style="color:#4da6ff; font-size:16px;">【').replace('】', '】</b><br>')
                            st.markdown(f"<div style='padding:15px; background:rgba(255,255,255,0.02); border-radius:10px; border:1px solid rgba(255,255,255,0.05);'>{insight_html}</div>", unsafe_allow_html=True)
                else: st.info("👉 우측 패널에 종목토론방 엑셀 파일을 업로드해주세요.")

            st.divider()
            
            st.markdown("### 📰 언론 보도 증권앱/MTS 중대 오류 이슈")
            with st.spinner("MTS 장애/지연 관련 중대 1년 치 아카이브를 탐색 중입니다..."):
                df_app_voc = get_realtime_news('"MTS 오류" OR "증권앱 먹통" OR "접속지연"', timeframe="1y", max_items=5)
                if "링크" in df_app_voc.columns and df_app_voc["링크"].iloc[0] != "":
                    for idx, row in df_app_voc.iterrows():
                        with st.container(border=True):
                            st.markdown(f"🚨 <a href='{row['링크']}' target='_blank' style='color:#ff4d4d; text-decoration:none;'>{row['원본제목']} 🔗</a>", unsafe_allow_html=True)
                            st.caption(f"📅 {row['게시일 / 출처']}")
                else: st.info("검색 범위(최대 1년) 내 포착된 리스크성 기사가 없습니다.")

        with sub_tabs[6]:
            st.markdown("### 🏢 국내 ETF 운용사 AUM 시장 점유율 및 테마별 현황 (실시간 기준)")
            col_pie, col_table = st.columns([1, 2])
            pivot_df = pd.DataFrame()
            with st.spinner("KRX 마켓 캡 데이터를 고속 파싱 중입니다..."):
                try:
                    df_all_etf = fdr.StockListing('ETF/KR')
                    if not df_all_etf.empty:
                        df_all_etf['브랜드'] = df_all_etf['Name'].apply(lambda x: str(x).split(' ')[0]).replace('KBSTAR', 'RISE')
                        df_all_etf['AUM(억원)'] = df_all_etf['MarCap'].fillna(0)
                        with col_pie:
                            st.markdown("#### 🥧 전체 시장 점유율 (AUM 기준)")
                            top_n_brands = st.slider("표시할 상위 운용사 수 설정", min_value=3, max_value=15, value=6, step=1)
                            df_brand_aum = df_all_etf.groupby('브랜드')['AUM(억원)'].sum().reset_index().sort_values(by='AUM(억원)', ascending=False)
                            if len(df_brand_aum) > top_n_brands:
                                df_top = df_brand_aum.head(top_n_brands)
                                df_pie_final = pd.concat([df_top, pd.DataFrame([{'브랜드': "🧩 기타 운용사", 'AUM(억원)': df_brand_aum.iloc[top_n_brands:]['AUM(억원)'].sum()}])], ignore_index=True)
                            else: df_pie_final = df_brand_aum
                            fig_market_share = px.pie(df_pie_final, names='브랜드', values='AUM(억원)', hole=0.4, color_discrete_sequence=px.colors.sequential.Blues_r)
                            fig_market_share.update_traces(textposition='inside', textinfo='percent+label')
                            fig_market_share.update_layout(height=420, margin=dict(t=20, l=20, r=20, b=20), template="plotly_dark", showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                            st.plotly_chart(fig_market_share, use_container_width=True)
                        with col_table:
                            c_title, c_btn = st.columns([7, 3])
                            with c_title:
                                st.markdown("#### 📊 TOP 4 운용사 테마별 AUM 현황")
                            with c_btn:
                                st.markdown("<div style='margin-bottom: 5px;'></div>", unsafe_allow_html=True)
                                
                            target_brands = ['KODEX', 'TIGER', 'ACE', 'RISE']
                            df_top_brands = df_all_etf[df_all_etf['브랜드'].isin(target_brands)].copy()
                            df_top_brands['분류_테마'] = df_top_brands['Name'].apply(assign_auto_theme)
                            pivot_df = pd.pivot_table(df_top_brands, values='AUM(억원)', index='분류_테마', columns='브랜드', aggfunc='sum', fill_value=0)
                            pivot_df = pivot_df[[c for col in target_brands if col in pivot_df.columns for c in [col]]].astype(int)
                            if '📦 기타 섹터/테마' in pivot_df.index: pivot_df = pivot_df.reindex([i for i in pivot_df.index if i != '📦 기타 섹터/테마'] + ['📦 기타 섹터/테마'])
                            
                            pivot_df = pivot_df.loc[(pivot_df != 0).any(axis=1)]
                            pivot_df.loc['총 AUM'] = pivot_df.sum(numeric_only=True)
                            
                            with c_btn:
                                csv_data = pivot_df.to_csv().encode('utf-8-sig')
                                st.download_button(label="📥 CSV 다운로드", data=csv_data, file_name='AUM_현황.csv', mime='text/csv', use_container_width=True)

                            def style_aum(row):
                                styles = []
                                for col in pivot_df.columns:
                                    s = ""
                                    if row.name == '총 AUM': s += "color: #ff4d4d; font-weight: bold; "
                                    if col == 'KODEX': s += "font-weight: bold; "
                                    styles.append(s)
                                return styles
                                
                            styled_df = pivot_df.style.format("{:,}").apply(style_aum, axis=1)
                            st.dataframe(styled_df, use_container_width=True)
                            st.session_state.aum_context_text = pivot_df.to_string()
                except:
                    pass

            st.divider()
            st.markdown("### 📈 테마별 운용사 전체 순매수 트렌드 (과거 추이)")
            if uploaded_excel is not None and available_weeks[0] != "데이터 없음":
                col_theme, col_weeks = st.columns(2)
                with col_theme: selected_theme = st.selectbox("분석할 테마 선택:", list(pivot_df.index) if not pivot_df.empty else ['🤖 AI & 반도체'])
                with col_weeks: n_weeks = st.slider("조회할 과거 주차 (N주):", min_value=1, max_value=len(available_weeks), value=min(4, len(available_weeks)))
                trend_data = []
                for w in available_weeks[:n_weeks][::-1]:
                    try:
                        temp_df = load_and_clean_excel(uploaded_excel, w)
                        if not temp_df.empty and '종목명' in temp_df.columns:
                            temp_df = temp_df[temp_df['종목명'] != '전체'].copy()
                            temp_df['브랜드'] = temp_df['종목명'].apply(lambda x: str(x).split(' ')[0]).replace('KBSTAR', 'RISE')
                            temp_df['분류_테마'] = temp_df['종목명'].apply(assign_auto_theme)
                            theme_df = temp_df[(temp_df['분류_테마'] == selected_theme) & (temp_df['브랜드'].isin(['KODEX', 'TIGER', 'ACE', 'RISE']))].copy()
                            theme_df['순매수합계'] = theme_df.get('개인', 0) + theme_df.get('기관', 0) + theme_df.get('외국인', 0)
                            brand_sum = theme_df.groupby('브랜드')['순매수합계'].sum().reset_index()
                            brand_sum['주차'] = w
                            trend_data.append(brand_sum)
                    except: pass
                if trend_data:
                    df_trend = pd.concat(trend_data)
                    fig_trend = px.line(df_trend, x='주차', y='순매수합계', color='브랜드', markers=True, template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Set2)
                    fig_trend.update_layout(height=400, yaxis_title="전체 순매수 합계", xaxis_title=None, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_trend, use_container_width=True)
            else: st.info("👉 우측 패널에 엑셀 데이터를 업로드하시면 트렌드 그래프가 활성화됩니다.")

        # [신규 통합] 🤖 주간 브리핑 AI 프롬프트 하위 탭 
        with sub_tabs[7]:
            st.markdown("#### [주간 세일즈 & 마케팅 브리핑 프롬프트 - 5-Step 체인]")
            st.info("💡 대시보드의 실시간 데이터를 프롬프트 내부에 직접 주입(Injection)했습니다. 한 번에 하나씩 복사하여 제미나이(Gemini)나 GPT에 입력하세요.")
            
            tgt = st.session_state.get('p_target_etf', '타겟 ETF')
            cmp = st.session_state.get('p_comp_etf', '경쟁 ETF')

            macro_raw = get_macro_snapshot()
            macro_text = ""
            for cat, items in macro_raw.items():
                for k, v in items.items():
                    if v['val'] != "정보 불가":
                        macro_text += f"- {k}: {v['val']} (변동: {v.get('pct', '')})\n"
            if not macro_text: macro_text = "현재 수집된 매크로 데이터 없음"

            df_news = st.session_state.get('df_real_news', pd.DataFrame())
            news_text = ""
            if not df_news.empty and "링크" in df_news.columns and df_news["링크"].iloc[0] != "":
                for _, row in df_news.head(12).iterrows():
                    news_text += f"- [{row['원본제목']}]({row['링크']})\n"
            else:
                news_text = "뉴스 데이터 없음"

            st.markdown("**📌 [Step 1: Market & Macro Overview (시장 및 거시 환경 분석)]**")
            p1_step1 = f"""[Step 1: Market & Macro Overview (시장 및 거시 환경 분석)]
다음은 시스템이 수집한 이번 주 핵심 매크로 지표 및 주간 뉴스 Raw Data입니다.

[실시간 매크로 지표 및 환율 동향]:
{macro_text}
[이번 주 핵심 타겟 ETF 관련 뉴스 (링크 포함)]:
{news_text}
위 Raw Data와 첨부된 링크 내용들을 바탕으로, 현재 거시 경제(금리/환율) 흐름이 ETF 시장 전반의 투자 심리 및 특정 테마 쏠림에 어떤 영향을 미치고 있는지 3줄로 진단하시오. (다음 단계들을 위해 분석 결과를 메모리에 유지할 것)"""
            st.code(p1_step1, language="text")

            st.markdown("**📌 [Step 2: AUM & Flow Analysis (수급 및 점유율 동향)]**")
            st.warning("📸 **[필수 스크린샷 첨부 1]** [순매수/거래대금 및 수익률] 하위 탭에 있는 **'시차별 수익률 vs AUM 대비 순매수 산점도'** 이미지를 캡처하여 AI 대화창에 업로드하세요!")
            
            symbols_mapping_pr = get_etf_mapping()
            end_dt_pr = datetime.today()
            start_dt_pr = end_dt_pr - timedelta(days=14)
            tgt_v, cmp_v = 0, 0
            try:
                sym_tgt = symbols_mapping_pr.get(tgt)
                if sym_tgt: tgt_v = fdr.DataReader(sym_tgt, start_dt_pr, end_dt_pr).resample('W').sum()['Volume'].iloc[-1]
                sym_cmp = symbols_mapping_pr.get(cmp)
                if sym_cmp: cmp_v = fdr.DataReader(sym_cmp, start_dt_pr, end_dt_pr).resample('W').sum()['Volume'].iloc[-1]
            except: pass
            dynamic_vol_text = f"- {tgt}: 최근 주간 거래량 {tgt_v:,.0f}주\n- {cmp}: 최근 주간 거래량 {cmp_v:,.0f}주"

            p1_step2 = f"""[Step 2: AUM & Flow Analysis (수급 및 점유율 동향)]
다음은 시스템이 추출한 실제 AUM 및 거래량 데이터입니다.

[운용사별 주요 테마 AUM 현황 (단위: 억원)]:
{st.session_state.get('aum_context_text', 'AUM 데이터 없음')}

[선택된 주요 ETF 최근 주간 거래량 추이]:
{dynamic_vol_text}

위 데이터를 바탕으로 타겟 ETF인 [{tgt}]와 경쟁 대조군인 [{cmp}] 간의 테마 내 AUM 점유율 및 주간 거래량 동향을 비교 분석하시오. 
추가로, 내가 함께 첨부한 '수익률 vs 순매수 산점도(Scatter Plot)' 이미지를 판독하여, 이번 주 리테일 자금이 '과거 수익률(T-1, T-2)'을 쫓아 들어왔는지, '당일 테마(T-0)'에 직각적으로 반응했는지 자금 유입의 성격을 진단하시오."""
            st.code(p1_step2, language="text")

            st.markdown("**📌 [Step 3: Marketing Impact & ROI Attribution (마케팅 기여도 및 투자 효율성 검증)]**")
            st.warning("📸 **[필수 스크린샷 첨부 2]** [이벤트 및 성과 검증] 하위 탭에 있는 **'예산 vs 파급력 산점도'** 및 **'전체 순매수 추이 궤적'** 차트 캡처 이미지를 AI 대화창에 업로드하세요!")
            p1_step3 = f"""[Step 3: Marketing Impact & ROI Attribution (마케팅 기여도 및 자본 효율성 검증)]
다음은 시스템이 연산한 마케팅 ROI(ROAS)와 인과관계 통계(이중차분, DiD) Raw Data입니다.

[집행된 이벤트 마케팅 총 예산]: {st.session_state.get('p_event_budget', 0):,.0f} 원
[타겟 ETF({tgt}) 순매수 변동액]: {st.session_state.get('stat_net_inflow', 0)} 억원
[마케팅 자본 유치 효율성 (ROAS)]: {st.session_state.get('stat_roas', 0):,.0f} 배 (1원 투자 시 유치한 자금량)
[대조군({cmp}) 대비 이중차분(DiD) 성과 배수]: {st.session_state.get('stat_did_multiplier', 0)} 배
[통계적 유의성 (p-value)]: {st.session_state.get('stat_p_value', 1.0)}

[{tgt}]에 유입된 전체 순매수 중 단순 시장 상승분이 아닌 마케팅/영업의 순수 기여분(설정효과)을 위 통계 수치를 바탕으로 분석하시오.
특히, 투입된 '마케팅 총 예산' 대비 도출된 'ROAS 배수'를 재무적 관점에서 해석하고, 첨부한 '예산 vs 파급력 산점도'를 참고하여 이번에 실행된 프로모션이 비용 효율적인(Cost-effective) 캠페인이었는지, 아니면 지출 대비 유입이 저조한 한계 효용 상태였는지 철저히 진단하시오."""
            st.code(p1_step3, language="text")

            vids = scrape_youtube_search_real(tgt)
            yt_text = ""
            if vids:
                top_vid = vids[0]
                yt_text = f"- 타겟 종목({tgt}) 최고 바이럴 영상: [{top_vid['title']}]({top_vid['link']}) (조회수 {top_vid['views']:,}회)"
            else:
                yt_text = st.session_state.get('yt_target_insights', '유튜브 바이럴 데이터 없음')

            st.markdown("**📌 [Step 4: Retail VOC & Competitor Media (투자자 심리 및 경쟁사 동향)]**")
            st.error("📥 **[필수 엑셀 파일 첨부]** 우측 패널에 업로드했던 **'종토방 VOC 엑셀 파일'**을 프롬프트와 함께 AI 대화창에 그대로 업로드해 주세요!")
            p1_step4 = f"""[Step 4: Retail VOC & Competitor Media (투자자 심리 및 경쟁사 동향)]
다음은 시스템이 수집한 경쟁사 유튜브 바이럴 및 브랜드 검색량 Raw Data입니다.

[타겟/경쟁사 유튜브 검색 바이럴 최상위 영상 성과 (링크 포함)]:
{yt_text}

[네이버 데이터랩 주요 키워드 검색량 추이 요약]:
{st.session_state.get('dl_summary', '데이터랩 요약 없음')}

내가 첨부한 '종토방 VOC 엑셀 파일'의 원문 데이터와 위 미디어/유튜브 링크 Raw Data를 모두 크로스체크하여 분석하시오. 
1) VOC 엑셀 데이터를 바탕으로 [{tgt}]에 대한 리테일 투자자들의 페인 포인트(불만)나 열광하는 핵심 키워드를 추출할 것.
2) 위 유튜브 및 데이터랩 추이를 바탕으로 경쟁사 [{cmp}]가 최근 어떤 테마를 집중적으로 밀고 있는지(차기 마케팅 테마) 예측할 것."""
            st.code(p1_step4, language="text")

            st.markdown("**📌 [Step 5: Actionable Insights (투트랙 세일즈 & 마케팅 액션 플랜)]**")
            p1_step5 = f"""[Step 5: Actionable Insights (투트랙 세일즈 & 마케팅 액션 플랜)]
위 1~4단계에서 도출된 팩트와 Raw Data 분석을 총합하여, 다음 주 영업/마케팅 본부가 즉시 실행해야 할 액션 플랜을 2가지 타겟으로 분리하여 제시하시오.

1. 리테일 타겟 (마케팅/콘텐츠 본부용): 앞선 3단계의 마케팅 ROAS 결과를 고려할 때, 예산을 증액하여 비슷한 캠페인을 이어갈지 혹은 바이럴 위주의 굿즈/콘텐츠로 선회할지 방향을 잡고, 데이터랩 트렌드를 찌를 수 있는 자사 유튜브/블로그 후킹(Hooking) 콘텐츠 주제 및 카피라이팅 1가지를 제안할 것.
2. 기관 타겟 (법인영업/세일즈 본부용): [{tgt}]가 [{cmp}] 대비 보유한 강점(AUM 규모, 실제 거래량 유동성, 설정효과 방어력 등 앞선 데이터 기반)을 엮어, PB들이 거액 자산가/연기금 기관에게 던질 수 있는 강력하고 묵직한 '원 라이너(1-liner) 세일즈 멘트'를 도출할 것."""
            st.code(p1_step5, language="text")

# -------------------------------------------------------------------------
    # Big 탭 2: 정책 모니터링 및 상품 기획 시뮬레이터
# -------------------------------------------------------------------------
    elif big_tab == "🌍 정책 모니터링 및 상품 기획 시뮬레이터":
        st.markdown("## 🌍 ETF Structuring Simulator")
        st.caption("다양한 자산을 융합하여 실제 주가 기반 백테스트 및 수지 분석(P&L)을 거친 실무형 팩트시트를 도출합니다.")
        
        c_sel1, c_sel2 = st.columns(2)
        with c_sel1:
            asset_class_options = [
                "사모신용 (BDC)", 
                "대출채권담보부증권 (CLO)", 
                "상장 실물자산 (Listed Real Assets)",
                "특수 목적 리츠 (통신탑/데이터센터)", 
                "국내 배당/그룹 테마 (SK그룹 등)",
                "➕ 직접 입력 (Manual)"
            ]
            selected_asset_ui = st.selectbox("🌍 탐색할 핵심 자산군 선택:", asset_class_options, key="asset_sel_app1")
            
            if selected_asset_ui == "➕ 직접 입력 (Manual)":
                with st.container(border=True):
                    st.markdown("**✍️ 커스텀 자산군 설정**")
                    custom_asset = st.text_input("자산군 수동 입력 (예: 글로벌 비만치료제, 우주항공):", value="글로벌 비만치료제")
                    asset_class = custom_asset.strip()
            else:
                asset_class = selected_asset_ui
                
            st.session_state.p_asset_class = asset_class

        proxy_options = []
        if asset_class == "사모신용 (BDC)": proxy_options = ["ARCC", "BIZD", "OBDC", "HTGC"]
        elif asset_class == "대출채권담보부증권 (CLO)": proxy_options = ["JAAA", "JBBB", "CLOA"]
        elif asset_class == "상장 실물자산 (Listed Real Assets)": proxy_options = ["VNQ", "XLRE"]
        elif asset_class == "특수 목적 리츠 (통신탑/데이터센터)": proxy_options = ["AMT", "CCI", "SRVR"]
        elif asset_class == "국내 배당/그룹 테마 (SK그룹 등)": proxy_options = ["017670", "034730", "TIGER 지주회사"]
        
        proxy_reason_map = {
            "ARCC": "미국 BDC 시가총액 1위 종목으로, 가장 다각화된 포트폴리오를 보유하여 우량 사모신용의 펀더멘털을 가장 잘 대변함.",
            "BIZD": "미국 BDC 산업 전체 추종하는 ETF로, 사모신용 섹터 전반의 평균적인 위험/수익 프로파일을 반영함.",
            "OBDC": "신흥 우량 담보 대출 위주의 포트폴리오로, 하방 경직성이 뛰어난 프록시 역할을 수행함.",
            "HTGC": "벤처 및 테크 기업 대출에 특화되어 고수익/고변동성 환경의 테스트에 적합함.",
            "JAAA": "최상위 AAA 등급 트랜치에 집중하여 주식 시장 급락 시 피난처(Safe Haven) 역할을 가장 잘 대변함.",
            "JBBB": "투자적격등급 하단(BBB) 트랜치를 타겟하여 추가 일드(Yield) 확보 전략을 검증하기에 적합함.",
            "CLOA": "풍부한 유동성을 바탕으로 전반적인 우량 CLO 시장의 흐름을 추종함.",
            "VNQ": "미국 리츠(REITs) 시장 전반에 투자하여 가장 표준적인 부동산 배당 수익 궤적을 제공함.",
            "XLRE": "S&P 500 내 대형 우량 부동산 기업에 집중하여, 상대적으로 변동성이 통제된 리츠 모델을 대변함.",
            "AMT": "글로벌 최대 통신탑 리츠(American Tower)로, 5G 인프라 확장에 따른 장기 임대 수익 구조를 대변함.",
            "CCI": "미국 내 통신 인프라(Crown Castle)에 집중하며, 높은 배당 성장성을 갖춘 통신탑 섹터 핵심 프록시.",
            "SRVR": "데이터센터 및 통신탑 리츠를 모아놓은 ETF로, 디지털 인프라 실물 자산 전반의 흐름을 추종함.",
            "017670": "SK텔레콤. 국내 통신 3사 중 압도적인 시장 점유율과 안정적인 현금흐름을 바탕으로 한 고배당 매력.",
            "034730": "SK(주). 그룹 내 핵심 성장 동력과 배당(인컴)을 동시에 추구하는 지주사 프록시.",
            "TIGER 지주회사": "국내 주요 그룹 지주사에 분산 투자하여 '배당+성장' 팩터를 동시에 검증할 수 있는 대표 ETF."
        }

        with c_sel2:
            proxy_options.append("➕ 직접 입력 (Manual)")
            selected_proxy_ui = st.selectbox("📍 백테스트 프록시 (대표 지표) 선택:", proxy_options)
            
            if selected_proxy_ui == "➕ 직접 입력 (Manual)":
                with st.container(border=True):
                    st.markdown("**✍️ 커스텀 프록시 설정**")
                    custom_ticker = st.text_input("티커 수동 입력 (예: SRVR, PFF, 017670):", value="SRVR")
                    st.session_state.p_proxy = custom_ticker.strip().upper()
                    st.session_state.p_proxy_reason = "사용자 직접 입력 (본 기획서의 핵심 아이디어 및 거시적 트렌드를 대변하는 전략적 편입 자산)"
            else:
                st.session_state.p_proxy = selected_proxy_ui
                st.session_state.p_proxy_reason = proxy_reason_map.get(selected_proxy_ui, "선정 논리 데이터 없음")
            
        st.info(f"💡 **프록시 선정 논리(AI 프롬프트 연동):** {st.session_state.p_proxy_reason}")

        # 상품 기획 탭 추가
        sub_tabs_plan = st.tabs([
            "📡 1. 규제 공백 및 신상품 모니터링", 
            "🔍 2. 기존 프록시 기반 상품 구조화 (Proxy Simulator)", 
            "💡 3. 가상 지수 샌드박스 (Index Sandbox)",
            "🌟 4. 상품 기획 마스터 프롬프트"
        ])

        # === 1. 규제 공백 및 신상품 모니터링 ===
        with sub_tabs_plan[0]:
            st.markdown("### 🇺🇸 혁신 구조 공백 분석 (Mega Trends vs 당사 라인업)")
            st.caption("시장에서 자금이 유입되는 혁신 테마 중, 국내 시장 및 자사 라인업에 공백이 있는 영역을 모니터링합니다.")
            
            raw_keywords = ["타겟 인컴 ETF 버퍼형", "0DTE 초단기 옵션 커버드콜 ETF", "가상자산 비트코인 현물 ETF", "BDC 기업성장집합투자기구 대체투자", "하방 방어형 100% 버퍼 ETF"]
            
            search_kw_map = {
                "사모신용 (BDC)": '"사모신용" OR "BDC"',
                "대출채권담보부증권 (CLO)": '"CLO" OR "대출채권담보부증권"',
                "상장 실물자산 (Listed Real Assets)": '"리츠" OR "실물자산" OR "부동산 ETF"',
                "특수 목적 리츠 (통신탑/데이터센터)": '"통신 리츠" OR "데이터센터" OR "디지털 인프라"',
                "국내 배당/그룹 테마 (SK그룹 등)": '"배당" OR "지주사" OR "밸류업"',
                "타겟 인컴 ETF 버퍼형": '"타겟 인컴" OR "버퍼형" OR "인컴 ETF"',
                "0DTE 초단기 옵션 커버드콜 ETF": '"0DTE" OR "초단기" OR "위클리 커버드콜"',
                "가상자산 비트코인 현물 ETF": '"비트코인 현물" OR "가상자산 ETF"',
                "BDC 기업성장집합투자기구 대체투자": '"BDC" OR "사모신용"',
                "하방 방어형 100% 버퍼 ETF": '"하방 방어" OR "버퍼 ETF"'
            }
            
            if asset_class not in search_kw_map:
                search_kw_map[asset_class] = f'"{asset_class}"'

            trend_strengths = []
            
            with st.spinner("혁신 테마 트렌드를 스캔 중입니다..."):
                for kw in raw_keywords:
                    search_query = search_kw_map.get(kw, f'"{kw}"')
                    temp_news = get_realtime_news(search_query, timeframe="14d", max_items=5)
                    c = len(temp_news) if not temp_news.empty and temp_news.iloc[0]["게시일 / 출처"] != "-" else 0
                    trend_strengths.append("🔥🔥🔥 최고조" if c >= 3 else ("🔥🔥 강세" if c >= 1 else "🔥 꾸준함"))
                    
            st.dataframe(pd.DataFrame({
                "혁신 상품 구조 (메가 트렌드)": raw_keywords, 
                "최근 뉴스 기반 유입 강도": trend_strengths, 
                "당사 라인업 현황": ["공백 (0개)", "일부 유사 (1개)", "규제 한계 (0개)", "규제 한계 (0개)", "공백 (0개)"], 
                "전략적 제언 (Action Plan)": ["즉시 벤치마킹 기획 가동", "분배율 메시지 고도화", "정책 완화 시그널 추적", "법안 통과 즉시 선점", "하락장 방어 포트폴리오 설계"]
            }), use_container_width=True, hide_index=True)
            
            st.divider()
            
            st.markdown(f"### 📡 `[정책 시그널]` 핵심 혁신 구조 규제 완화 동향")
            
            policy_options = [asset_class] + [kw for kw in raw_keywords if kw != asset_class]
            selected_trend_label = st.selectbox("🔍 규제 모니터링망 가동할 혁신 구조 선택:", options=policy_options, index=0)
            st.session_state['selected_trend_label'] = selected_trend_label
            
            with st.spinner("선택된 테마의 규제 완화 관련 뉴스를 스크랩 중입니다..."):
                policy_query = f'({search_kw_map.get(selected_trend_label, f'"{selected_trend_label}"')}) AND ("금융위" OR "규제" OR "법안" OR "가이드라인")'
                df_gap_news = get_realtime_news(policy_query, timeframe="30d", max_items=6)
                if "링크" in df_gap_news.columns and df_gap_news["링크"].iloc[0] != "":
                    cols_grid = st.columns(2)
                    for idx, row in df_gap_news.iterrows():
                        with cols_grid[idx % 2]:
                            with st.container(border=True):
                                st.caption(f"📅 {row['게시일 / 출처']}")
                                st.markdown(f"<a href='{row['링크']}' target='_blank' style='font-size:14px; font-weight:bold; color:#ffb04d; text-decoration:none;'>[규제] {row['원본제목']} 🔗</a>", unsafe_allow_html=True)
                else: 
                    st.info("관련된 최신 정책/규제 뉴스 피드가 존재하지 않습니다.")
            
            st.divider()
            
            st.markdown(f"### 📰 핵심 동향 모니터링 (지난주 일~토)")
            
            base_news_options = [
                "사모신용 (BDC)", "대출채권담보부증권 (CLO)", "상장 실물자산 (Listed Real Assets)", 
                "특수 목적 리츠 (통신탑/데이터센터)", "국내 배당/그룹 테마 (SK그룹 등)"
            ]
            if asset_class not in base_news_options:
                base_news_options.insert(0, asset_class)

            news_options = base_news_options + [kw for kw in raw_keywords if kw not in base_news_options]
            selected_news_kw = st.selectbox("🔍 뉴스 검색망 가동할 핵심 키워드 선택:", options=news_options, index=0)
            
            with st.spinner("해당 키워드의 지난주 뉴스를 정확히 필터링 중입니다..."):
                search_query = search_kw_map.get(selected_news_kw, f'"{selected_news_kw}"')
                raw_news_df = get_realtime_news(search_query, timeframe="14d", max_items=20)
                
                today = datetime.today()
                last_sat = today - timedelta(days=today.weekday() + 2)
                last_sun = last_sat - timedelta(days=6)
                
                filtered_news = []
                if "링크" in raw_news_df.columns and raw_news_df["링크"].iloc[0] != "":
                    for _, row in raw_news_df.iterrows():
                        try:
                            date_str = row['게시일 / 출처'].split(' / ')[0].strip()
                            pub_date = datetime.strptime(date_str, "%d %b %Y").date()
                            if last_sun.date() <= pub_date <= last_sat.date():
                                filtered_news.append(row)
                        except:
                            pass
                
                if filtered_news:
                    cols_grid = st.columns(2)
                    for idx, row in enumerate(filtered_news):
                        with cols_grid[idx % 2]:
                            with st.container(border=True):
                                st.caption(f"📅 {row['게시일 / 출처']}")
                                st.markdown(f"<a href='{row['링크']}' target='_blank' style='font-size:14px; font-weight:bold; color:#4da6ff; text-decoration:none;'>{row['원본제목']} 🔗</a>", unsafe_allow_html=True)
                else:
                    st.info(f"선택하신 '{selected_news_kw}' 관련 지난주({last_sun.strftime('%Y-%m-%d')} ~ {last_sat.strftime('%Y-%m-%d')}) 기사가 존재하지 않습니다.")

        # === 2. 기존 프록시 기반 상품 구조화 (Proxy Simulator) ===
        with sub_tabs_plan[1]:
            st.markdown("#### Step 1. 펀더멘털 스크리닝 및 가중치 모델 설정")
            with st.container(border=True):
                c_s1, c_s2 = st.columns(2)
                with c_s1:
                    st.markdown("**🔍 기초자산 펀더멘털 스크리닝 (허들 설정)**")
                    st.caption("AI를 통한 실제 종목 필터링 지시 기준이 될 재무 비율을 설정합니다.")
                    ltv_limit = st.slider("[AI 유니버스 필터링 지시용] 최대 LTV (부채비율) 한도 (%)", 10, 80, 45, step=5)
                    fcf_limit = st.slider("[AI 유니버스 필터링 지시용] 최소 잉여현금흐름(FCF) 마진 (%)", 0, 30, 15, step=1)
                    st.session_state.p_ltv = ltv_limit
                    st.session_state.p_fcf = fcf_limit
                with c_s2:
                    st.markdown("**⚖️ 포트폴리오 가중치 및 리스크 통제**")
                    weight_opt = st.selectbox("비중 배분 방식 선택:", [
                        "Top 3 핵심종목 75% 편중 (Akros Core-Satellite)",
                        "시가총액 가중 방식 (Cap-weighted)",
                        "Log-Market Cap 기반 비선형 가중 (대형주 쏠림 방지)"
                    ])
                    st.session_state.p_weight = weight_opt
                    cap_limit = st.slider("단일 종목 최대 편입 상한선 (Cap, %)", 10, 30, 25, step=1)
                    st.session_state.p_cap = cap_limit
                    
                st.info("💡 **안내:** 본 대시보드의 백테스트 차트는 대표 프록시 ETF의 실제 과거 수익률을 추종합니다. 위 슬라이더로 설정한 펀더멘털 룰은 차트를 실시간으로 변경하지 않으며, 하단의 'AI 기획서 프롬프트'에 조건값으로 주입되어 최종 기획서 작성에 활용됩니다.")
                st.session_state.p_has_csv = st.checkbox("✅ 외부 AI(ChatGPT 등)에 유니버스 엑셀 파일을 직접 첨부할 예정입니다.", value=False)

            st.divider()

            st.markdown("#### Step 2. 퀀트 기반 백테스팅 및 리스크")
            c_bt1, c_bt2 = st.columns([1.2, 1])
            
            port_daily = None
            dates = None
            backtest_success = False
            
            with c_bt1:
                with st.container(height=550, border=True):
                    st.markdown(f"**📈 {st.session_state.p_proxy} 과거 3년 백테스트 (자본차익 vs 배당수익 분해)**")
                    
                    lp_cost = st.slider("예상 LP 호가 스프레드 및 마찰비용 (연 %)", 0.0, 1.0, 0.2, 0.1)
                    st.session_state.p_lp_cost = lp_cost
                    
                    end_dt = datetime.today()
                    start_dt = end_dt - timedelta(days=365*3)
                    
                    annual_yield = 0.08 if "BDC" in asset_class else (0.06 if "CLO" in asset_class else 0.04)
                    
                    with st.spinner(f"API에서 {st.session_state.p_proxy} 데이터를 불러옵니다..."):
                        try:
                            port_df = fdr.DataReader(st.session_state.p_proxy, start_dt, end_dt)
                            if len(port_df) > 10:
                                port_daily = port_df['Close'].pct_change().dropna()
                                
                                port_cum = (1 + port_daily).cumprod() * 100
                                discount_array = (1 - lp_cost/100) ** (np.arange(len(port_cum)) / 252)
                                port_cum = port_cum * discount_array
                                
                                dates = port_cum.index
                                port_vol = np.std(port_daily) * np.sqrt(252)
                                ann_ret = (port_cum.iloc[-1] / 100) ** (1/3) - 1
                                sharpe = (ann_ret - 0.035) / port_vol if port_vol > 0 else 0
                                mdd = (port_cum / np.maximum.accumulate(port_cum) - 1).min() * 100
                                backtest_success = True
                            else:
                                st.error("🚨 주가 데이터를 불러오지 못했습니다. 올바른 티커인지 확인해주세요.")
                        except Exception as e:
                            st.error("🚨 API 서버 응답 지연으로 데이터를 불러올 수 없습니다. 잠시 후 다시 시도해 주세요.")
                            
                    if backtest_success:
                        st.session_state.p_sharpe = round(sharpe, 2)
                        st.session_state.p_mdd = round(mdd, 1)

                        daily_yield = annual_yield / 252
                        income_return = (np.cumprod(1 + np.full(len(port_cum), daily_yield)) * 100) - 100
                        total_return_pct = port_cum.values - 100
                        price_return = total_return_pct - income_return
                        
                        fig_decomp = go.Figure()
                        fig_decomp.add_trace(go.Scatter(x=dates, y=income_return, mode='lines', stackgroup='one', name=f'누적 배당/이자 (연 {annual_yield*100:.1f}%)', line=dict(color='#ffb04d')))
                        fig_decomp.add_trace(go.Scatter(x=dates, y=price_return, mode='lines', stackgroup='one', name='누적 자본 차익 (가격변동)', line=dict(color='#4da6ff')))
                        fig_decomp.update_layout(height=250, margin=dict(t=10,b=10,l=10,r=10), yaxis_title="누적 수익률 (%)", xaxis_title="", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig_decomp, use_container_width=True)

                        cc1, cc2 = st.columns(2)
                        cc1.metric("샤프 비율", f"{st.session_state.p_sharpe}")
                        cc2.metric("실증 최대 낙폭(MDD)", f"{st.session_state.p_mdd}%")

            with c_bt2:
                with st.container(height=550, border=True):
                    st.markdown("**🌪️ 매크로 스트레스 테스트 시나리오**")
                    scenario = st.selectbox("과거 위기 시나리오 국면을 선택하세요:", [
                        "2022년 급격한 금리 인상기 (인플레이션 쇼크)",
                        "2020년 코로나 팬데믹 (글로벌 셧다운 및 신용경색)",
                        "2023년 실리콘밸리은행(SVB) 파산 (단기 유동성 위기)"
                    ])
                    st.session_state.p_scenario = scenario
                    
                    if "코로나" in scenario:
                        s_start, s_end, desc = "2020-02-19", "2020-03-23", "극단적 신용 스프레드 확대에 대한 회복력 증명"
                    elif "금리" in scenario:
                        s_start, s_end, desc = "2022-01-03", "2022-10-12", "고금리 환경 수혜 자산에 의한 방어력 증명"
                    else:
                        s_start, s_end, desc = "2023-03-01", "2023-05-01", "우량 담보에 의한 하방 경직성 증명"
                        
                    with st.spinner("해당 국면의 과거 실제 주가 데이터를 조회 중입니다..."):
                        try:
                            sp_df = fdr.DataReader('KS11' if "국내" in asset_class else 'US500', s_start, s_end)['Close']
                            my_df = fdr.DataReader(st.session_state.p_proxy, s_start, s_end)['Close']
                            
                            if len(sp_df) > 0 and len(my_df) > 0:
                                sp_drop = (sp_df / sp_df.cummax() - 1).min() * 100
                                my_drop = (my_df / my_df.cummax() - 1).min() * 100
                                
                                bm_name = "코스피" if "국내" in asset_class else "S&P 500"
                                df_bar = pd.DataFrame({"자산": [bm_name, f"기획 Proxy ({st.session_state.p_proxy})"], "최대 낙폭 (%)": [sp_drop, my_drop]})
                                fig_bar = px.bar(df_bar, x="자산", y="최대 낙폭 (%)", text="최대 낙폭 (%)", color="자산", color_discrete_map={bm_name: "gray", f"기획 Proxy ({st.session_state.p_proxy})": "#ffb04d"}, template="plotly_dark")
                                fig_bar.update_traces(textposition='auto', texttemplate='%{text:.1f}%')
                                fig_bar.update_layout(height=250, margin=dict(t=10, b=10, l=10, r=10), showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                                st.plotly_chart(fig_bar, use_container_width=True)
                                st.info(f"💡 **AI 프롬프트 연동:** {desc} 로직이 자동 탑재됩니다.")
                            else:
                                st.error("🚨 해당 시기의 데이터가 API에 존재하지 않습니다.")
                        except Exception as e:
                            st.error("🚨 API 서버 응답 지연으로 과거 낙폭 데이터를 계산할 수 없습니다. 잠시 후 다시 시도해 주세요.")

            st.divider()

            st.markdown("#### Step 3. 구조화, 세일즈 타겟팅 및 P&L")
            
            with st.expander("➕ 파생상품(옵션) 오버레이 전략 추가하기 (선택형 심화 모듈)", expanded=True):
                st.markdown("**📈 옵션 페이오프(Payoff) 개념 구조도**")
                st.caption("설정된 옵션 파라미터를 기반으로 만기 시점의 개념적인 수익률 페이오프 구조를 시각화합니다.")
                
                opt_strategy = st.radio("시뮬레이션 전략 선택:", ["초단기 커버드콜 (Covered Call)", "적용 안 함 (순수 자산)", "하방 방어형 (Buffer ETF)"], horizontal=True)

                if opt_strategy != "적용 안 함 (순수 자산)":
                    c_opt1, c_opt2 = st.columns([1, 2])
                    with c_opt1:
                        st.markdown("**⚙️ 옵션 파라미터 설정**")
                        if "Covered Call" in opt_strategy:
                            strike_pct = st.slider("콜옵션 행사가격 (월간 OTM, %)", 0.0, 10.0, 3.0, 0.5)
                            premium = st.slider("수취 프리미엄 (월간, %)", 0.1, 5.0, 0.35, 0.05)
                        else:
                            buffer_pct = st.slider("하방 방어 수준 (연간 Buffer, %)", 5.0, 20.0, 10.0, 1.0)
                            cap_pct = st.slider("상방 제한 수준 (연간 Cap, %)", 5.0, 15.0, 8.0, 1.0)
                    
                    with c_opt2:
                        x_vals = np.linspace(-20, 20, 100)
                        if "Covered" in opt_strategy:
                            y_vals = np.where(x_vals > strike_pct, strike_pct + premium, x_vals + premium)
                        else:
                            y_vals = np.where(x_vals > 0, np.minimum(x_vals, cap_pct), 
                                              np.where(x_vals >= -buffer_pct, 0, x_vals + buffer_pct))
                                              
                        fig_opt = go.Figure()
                        fig_opt.add_trace(go.Scatter(x=x_vals, y=x_vals, mode='lines', name='기초자산 (Base)', line=dict(color='gray', dash='dot')))
                        fig_opt.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines', name=f'{opt_strategy} 페이오프', line=dict(color='#4da6ff' if "Covered" in opt_strategy else '#ffb04d', width=3)))
                        
                        fig_opt.update_layout(height=230, margin=dict(t=10,b=10,l=10,r=10), template="plotly_dark", xaxis_title="기초자산 수익률 (%)", yaxis_title="전략 수익률 (%)", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5))
                        st.plotly_chart(fig_opt, use_container_width=True)

            with st.container(border=True):
                st.markdown("**💱 환율 전략 및 비용 시뮬레이터**")
                
                c_fx1, c_fx2 = st.columns([1, 2])
                with c_fx1:
                    fx_strategy = st.selectbox("환율 전략 선택:", ["환노출 (Unhedged - 환차익/차손 노출)", "환헤지 (Hedged - 변동성 제거)", "국내 자산 (원화 Base)"])
                    st.session_state.p_fx = fx_strategy
                    ter = st.slider("예상 총보수율 (TER, %)", 0.1, 1.5, 0.40, 0.05)
                    fx_hedge_cost = 2.0 if "환헤지" in fx_strategy else 0.0
                    annual_yield = 8.0 if "BDC" in asset_class else 6.0
                    net_yield = annual_yield - ter - fx_hedge_cost
                    
                with c_fx2:
                    if backtest_success:
                        if "국내" in fx_strategy:
                            st.info("국내 자산으로 설정되어 별도의 환율 시뮬레이션(USD/KRW)을 진행하지 않습니다.")
                        else:
                            with st.spinner("과거 3년 실제 환율(USD/KRW) 데이터를 결합 중입니다..."):
                                try:
                                    usdkrw_df = fdr.DataReader('USD/KRW', start_dt, end_dt)['Close']
                                    fx_aligned = usdkrw_df.reindex(dates).ffill().bfill()
                                    fx_cum = fx_aligned / fx_aligned.iloc[0]

                                    daily_hedge_cost = (fx_hedge_cost / 100) / 252
                                    hedged_cum = (1 + port_daily - daily_hedge_cost).cumprod() * 100
                                    unhedged_cum = ((1 + port_daily).cumprod() * 100) * fx_cum
                                    
                                    df_fx = pd.DataFrame({"기간": dates, "환헤지(H)": hedged_cum.values, "환노출(UH)": unhedged_cum.values}).melt(id_vars="기간")
                                    fig_fx = px.line(df_fx, x="기간", y="value", color="variable", template="plotly_dark", color_discrete_map={"환헤지(H)": "#4da6ff", "환노출(UH)": "#ff4d4d"})
                                    fig_fx.update_layout(height=220, margin=dict(t=10,b=10,l=10,r=10), yaxis_title="수익률 궤적", xaxis_title="", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                                    st.plotly_chart(fig_fx, use_container_width=True)
                                except Exception:
                                    st.error("🚨 환율(USD/KRW) 데이터를 불러오지 못했습니다.")
                    else:
                        st.warning("상단 백테스트 데이터가 없어 환율 궤적을 그릴 수 없습니다.")

            with st.container(border=True):
                st.markdown("**🏢 자산운용사(AMC) 수지 분석 (1년 차 vs 안정화 기간)**")
                
                col_in1, col_in2, col_in3 = st.columns(3)
                
                with col_in1:
                    comp_ticker = st.text_input("타겟 경쟁사 ETF 티커", value="TIGER 미국MSCI리츠")
                    st.session_state.p_comp_ticker = comp_ticker
                    comp_ter = st.number_input("경쟁사 보수율 (%)", value=0.50, step=0.01)
                    st.session_state.p_comp_ter = comp_ter
                    
                with col_in2:
                    target_aum = st.number_input("당사 유지 타겟 AUM (억원)", value=1500, step=100)
                    st.session_state.p_aum = target_aum
                    mkt_cost_y1 = st.number_input("1년 차 런칭 마케팅 예산 (억원)", value=3.0, step=0.5)
                    st.session_state.p_launch_budget = mkt_cost_y1
                    
                with col_in3:
                    ter_diff = comp_ter - ter
                    if ter_diff > 0:
                        st.success(f"🔥 가격 경쟁력 확보: 경쟁사 대비 {ter_diff:.2f}% 저렴합니다.")
                    else:
                        st.warning(f"⚠️ 보수율 열위: 경쟁사 대비 보수율이 높거나 같으므로 차별화 포인트가 필요합니다.")
                    
                    amc_margin = ter - 0.05
                    expected_revenue = target_aum * (amc_margin / 100)
                    
                    # 1년 차 계산
                    fixed_cost_y1 = 2.0  # 지수 산출 의뢰 비용(0.5억) 반영
                    profit_y1 = expected_revenue - fixed_cost_y1 - mkt_cost_y1
                    st.session_state.p_profit_y1 = round(profit_y1, 2)
                    
                    # 2년 차(안정화) 계산
                    fixed_cost_y2 = 1.5  # 지수 유지비용만 반영
                    mkt_cost_y2 = 0.5    # 리텐션 마케팅 비용
                    profit_y2 = expected_revenue - fixed_cost_y2 - mkt_cost_y2
                    st.session_state.p_profit_y2 = round(profit_y2, 2)
                    
                    if amc_margin > 0:
                        bep_aum = (fixed_cost_y1 + mkt_cost_y1) / (amc_margin / 100)
                        st.info(f"💡 **1년 차 BEP(손익분기점) 달성 필요 AUM:** 약 {bep_aum:,.0f}억 원")
                    else:
                        st.error("마진이 0 또는 마이너스입니다. 보수율(TER)을 높이거나 고정비를 줄이세요.")

                st.divider()
                st.markdown("##### 📈 운용사 P&L 워터폴 시각화")
                
                c_wf1, c_wf2 = st.columns(2)
                
                with c_wf1:
                    fig_wf1 = go.Figure(go.Waterfall(
                        name = "1년 차", orientation = "v",
                        measure = ["relative", "relative", "relative", "total"],
                        x = ["총 운용수익", "고정비(개발비 포함)", "초기 런칭 예산", "최종 순이익"],
                        textposition = "outside",
                        text = [f"+{expected_revenue:.1f}억", f"-{fixed_cost_y1:.1f}억", f"-{mkt_cost_y1:.1f}억", f"{profit_y1:.1f}억"],
                        y = [expected_revenue, -fixed_cost_y1, -mkt_cost_y1, profit_y1],
                        connector = {"line":{"color":"rgba(255,255,255,0.2)"}},
                        decreasing = {"marker":{"color":"#ff4d4d"}},
                        increasing = {"marker":{"color":"#4da6ff"}},
                        totals = {"marker":{"color":"#ffb04d" if profit_y1 > 0 else "gray"}}
                    ))
                    fig_wf1.update_layout(title="**[1년 차] 런칭 및 BEP 방어기**", title_x=0.5, height=320, margin=dict(t=40, b=20, l=10, r=10), template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_wf1, use_container_width=True)

                with c_wf2:
                    fig_wf2 = go.Figure(go.Waterfall(
                        name = "2년 차", orientation = "v",
                        measure = ["relative", "relative", "relative", "total"],
                        x = ["총 운용수익", "유지 고정비", "리텐션 마케팅", "최종 순이익"],
                        textposition = "outside",
                        text = [f"+{expected_revenue:.1f}억", f"-{fixed_cost_y2:.1f}억", f"-{mkt_cost_y2:.1f}억", f"{profit_y2:.1f}억"],
                        y = [expected_revenue, -fixed_cost_y2, -mkt_cost_y2, profit_y2],
                        connector = {"line":{"color":"rgba(255,255,255,0.2)"}},
                        decreasing = {"marker":{"color":"#ff4d4d"}},
                        increasing = {"marker":{"color":"#4da6ff"}},
                        totals = {"marker":{"color":"#ffb04d" if profit_y2 > 0 else "gray"}}
                    ))
                    fig_wf2.update_layout(title="**[2년 차 이후] 안정화 및 캐시카우**", title_x=0.5, height=320, margin=dict(t=40, b=20, l=10, r=10), template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_wf2, use_container_width=True)

            with st.container(border=True):
                st.markdown("##### 📄 Simulated Product Factsheet")
                st.metric("최종 타겟 배당수익률 (Net Yield)", f"{net_yield:.2f}%")
                
                risk_level = "보통 위험 (Medium Risk)" if "환헤지" in fx_strategy or "국내" in fx_strategy else "높은 위험 (High Risk)"
                fx_desc = f"달러 변동성 제거 (헤지 프리미엄 연 약 {fx_hedge_cost}% 발생)" if "환헤지" in fx_strategy else ("국내 원화 기반" if "국내" in fx_strategy else "달러 강세 시 환차익 추가 향유 가능 (변동성 노출)")
                tax_desc = "퇴직연금(IRP/DC) 내 안전자산(30%) 룸 편입용" if "환헤지" in fx_strategy else "배당소득세 및 종합과세 방어를 위한 ISA 계좌 편입용"
                
                st.write(f"- **위험 등급:** {risk_level}")
                st.write(f"- **FX 전략:** {fx_desc}")
                st.success(f"💰 **세금 최적화(Tax):** {tax_desc}으로 타겟팅하는 세일즈에 유리합니다.")
                st.info("해당 팩트시트의 핵심 소구 포인트는 우측 상단의 'AI 프롬프트' 탭으로 전달되어 최종 마케팅 제안서 작성에 자동으로 활용됩니다.")

        # === 3. 가상 지수 샌드박스 ===
        with sub_tabs_plan[2]:
            st.markdown("### 💡 가상 지수 샌드박스 (Synthetic Index Simulator)")
            st.caption("실제 지수 편입 종목을 시뮬레이션하고, S&P 500 등 벤치마크 대비 복제 오차(TE)와 상관관계를 검증합니다.")

            with st.container(border=True):
                st.markdown("#### 1. 퀀트 시뮬레이션 컨트롤 패널 (Total Return 기반 분해)")
                
                sandbox_tickers_input = st.text_input("📌 지수 편입 종목 (쉼표로 구분):", value="AMT, CCI, EQIX, DLR, SBAC, IRM, DBRG, UNIT, CCOI, GLPI")
                sandbox_tickers = [t.strip().upper() for t in sandbox_tickers_input.split(",") if t.strip()]
                
                sandbox_weights_input = st.text_input("⚖️ 종목별 편입 비중 (티커 순서대로 쉼표로 구분, 단위: %):", value="25, 25, 25, 5, 5, 4, 3, 3, 3, 2")
                raw_weights = [float(w.strip()) for w in sandbox_weights_input.split(",") if w.strip()]
                
                col_sb1, col_sb2, col_sb3 = st.columns([1, 1, 1])
                with col_sb1:
                    sandbox_weight = st.selectbox("⚖️ 비중 배분 룰:", ["사용자 지정 비중 (Custom Weights)", "동일 가중 (Equal Weight)", "시가총액 가중 방식 (Cap-weighted)"])
                with col_sb2:
                    sandbox_div = st.slider("💰 포트폴리오 예상 연 배당수익률 (%)", 0.0, 15.0, 7.5, 0.5, help="배당이 제외된 주가 궤적(Price Return) 위에 누적 인컴(Income) 면적으로 독립 시각화됩니다.")
                with col_sb3:
                    sandbox_error = st.slider("🌪️ 예상 오차율/마찰 비용 (Tracking Error, 연간 ±%)", 0.5, 5.0, 2.5, 0.5)
                    sandbox_hedging = st.checkbox("🛡️ 환헤지 프리미엄 비용 차감 (연 -1.5%)")
                    
                sandbox_rebal_cost = st.slider("🔄 연간 리밸런싱 마찰 비용 (Turnover Cost, %)", 0.0, 1.0, 0.2, 0.1, help="잦은 매매로 인해 깎여나가는 거래 비용을 일할 차감하여 백테스트의 보수성을 높입니다.")

            st.markdown("#### 2. 하이브리드 시나리오 차트 및 복제 오차(TE) 모니터링")
            if len(sandbox_tickers) > 0:
                with st.spinner("API에서 실제 주가 데이터를 수집하여 Total Return 지수를 합성하고 있습니다..."):
                    end_dt = datetime.today()
                    start_dt = end_dt - timedelta(days=365*3)
                    
                    df_list = []
                    valid_tickers = []
                    
                    for t in sandbox_tickers:
                        try:
                            df_t = fdr.DataReader(t, start_dt, end_dt)['Close'].pct_change().dropna()
                            df_t.name = t
                            df_list.append(df_t)
                            valid_tickers.append(t)
                        except Exception:
                            pass 
                    
                    if len(df_list) > 0:
                        df_merged = pd.concat(df_list, axis=1).dropna()
                        
                        if sandbox_weight == "사용자 지정 비중 (Custom Weights)":
                            if len(raw_weights) == len(sandbox_tickers):
                                ticker_weight_map = dict(zip(sandbox_tickers, raw_weights))
                                valid_weights = [ticker_weight_map[t] for t in valid_tickers]
                                total_w = sum(valid_weights)
                                weights = np.array([(w / total_w) for w in valid_weights])
                            else:
                                st.error("⚠️ 티커 개수와 비중 개수가 일치하지 않습니다. 동일 가중(1/N)으로 임시 계산합니다.")
                                weights = np.array([1/len(valid_tickers)] * len(valid_tickers))
                        else:
                            weights = np.array([1/len(valid_tickers)] * len(valid_tickers))
                        
                        port_daily_ret_price = df_merged.dot(weights)
                        
                        if sandbox_hedging:
                            port_daily_ret_price -= (1.5 / 252 / 100)
                        port_daily_ret_price -= (sandbox_rebal_cost / 100 / 252)
                            
                        base_cum_returns_price = (1 + port_daily_ret_price).cumprod() * 100
                        dates = base_cum_returns_price.index
                        
                        years = np.arange(1, len(dates) + 1) / 252.0
                        
                        income_pts = 100 * (((1 + sandbox_div/100) ** years) - 1)
                        
                        y_price = base_cum_returns_price - 100
                        y_total = y_price + income_pts
                        
                        envelope = (sandbox_error / 100) * np.sqrt(years) * 100
                        best_cum_returns = y_total + envelope
                        worst_cum_returns = y_total - envelope
                        
                        api_error = False
                        try:
                            bm_ticker = 'KS11' if "국내" in asset_class else 'US500'
                            bm_df = fdr.DataReader(bm_ticker, start_dt, end_dt)['Close'].pct_change().dropna()
                            bm_df = bm_df.reindex(dates).fillna(0)
                            bm_df += (1.5 / 100 / 252)
                            bm_cum_returns = (1 + bm_df).cumprod() * 100 - 100
                            
                            corr_with_bm = port_daily_ret_price.corr(bm_df)
                            tracking_error_annual = np.std(port_daily_ret_price - bm_df) * np.sqrt(252) * 100
                            st.session_state.p_corr = round(corr_with_bm, 2)
                            
                        except Exception:
                            api_error = True
                            st.error("🚨 API 서버 오류로 벤치마크 데이터를 불러오지 못했습니다.")

                        if not api_error:
                            fig_fan = go.Figure()
                            bm_name = "코스피" if "국내" in asset_class else "S&P 500"
                            fig_fan.add_trace(go.Scatter(x=dates, y=bm_cum_returns, mode='lines', name=f'{bm_name} (BM Price)', line=dict(color='gray', width=1, dash='dot')))
                            
                            fig_fan.add_trace(go.Scatter(x=dates, y=y_price, mode='lines', name='순수 주가 수익률 (Price)', line=dict(color='#4da6ff', width=2)))
                            fig_fan.add_trace(go.Scatter(x=dates, y=y_total, mode='none', name=f'누적 배당 수익 (연 {sandbox_div}%)', fill='tonexty', fillcolor='rgba(255, 176, 77, 0.3)'))
                            fig_fan.add_trace(go.Scatter(x=dates, y=y_total, mode='lines', name='총 수익률 (Total Return)', line=dict(color='#ffb04d', width=3)))

                            fig_fan.add_trace(go.Scatter(x=dates, y=worst_cum_returns, mode='lines', name=f'Worst Case (-{sandbox_error}%)', line=dict(color='#ff4d4d', width=1, dash='dash')))
                            fig_fan.add_trace(go.Scatter(x=dates, y=best_cum_returns, mode='lines', name=f'Best Case (+{sandbox_error}%)', fill='tonexty', fillcolor='rgba(77, 166, 255, 0.1)', line=dict(color='#4da6ff', width=1, dash='dash')))

                            fig_fan.update_xaxes(
                                rangeselector=dict(
                                    buttons=list([
                                        dict(count=6, label="6개월", step="month", stepmode="backward"),
                                        dict(count=1, label="1년", step="year", stepmode="backward"),
                                        dict(step="all", label="전체(3년)")
                                    ]),
                                    bgcolor="#1e3a8a", activecolor="#3b82f6", font=dict(color="white")
                                )
                            )

                            fig_fan.update_layout(
                                height=450, margin=dict(t=20, b=20, l=20, r=20),
                                yaxis_title="누적 수익률 (%)", xaxis_title="",
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                                template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
                            )
                            
                            st.markdown(f"##### **📈 실제 주가 기반 가상 지수 수익률 (편입 종목: {', '.join(valid_tickers)})**")
                            st.plotly_chart(fig_fan, use_container_width=True)

                            c_m1, c_m2, c_m3, c_m4 = st.columns(4)
                            final_base = base_cum_returns_price.iloc[-1]
                            mdd_base = (base_cum_returns_price / np.maximum.accumulate(base_cum_returns_price) - 1).min() * 100
                            years_elapsed = years[-1] if years[-1] > 0 else 1
                            cagr_price = ((final_base/100)**(1/years_elapsed)-1)*100
                            
                            c_m1.metric("연환산 주가 수익률 (Price CAGR)", f"{cagr_price:.1f}%")
                            c_m2.metric("최종 총수익률 (Total Return)", f"{y_total.iloc[-1]:.1f}%", f"배당(인컴) 분해 적용")
                            
                            corr_color = "normal" if corr_with_bm < 0.5 else "off"
                            c_m3.metric(f"{bm_name} 상관계수 (분산도)", f"{corr_with_bm:.2f}", "수치가 낮을수록 헷지 우수", delta_color=corr_color)
                            c_m4.metric("복제 추적오차 (Tracking Error)", f"{tracking_error_annual:.1f}%", "벤치마크 대비 변동성 차이", delta_color="inverse")
                            
                            st.success("💡 **QC(품질 관리) 모니터링:** 벤치마크 대비 상관계수와 추적오차가 적정 수준인지 검증하여, 마케팅 시 세일즈 포인트(낮은 상관관계에 따른 분산투자 효과)로 활용할 수 있습니다.")
                            
                        if len(valid_tickers) < len(sandbox_tickers):
                            missing = set(sandbox_tickers) - set(valid_tickers)
                            st.warning(f"⚠️ 일부 티커({', '.join(missing)})는 API에서 데이터를 찾을 수 없어 연산에서 제외되었습니다.")
                    else:
                        st.error("🚨 입력하신 티커들의 데이터를 불러올 수 없습니다. 올바른 티커인지 확인해 주세요.")
            else:
                st.info("👉 편입할 티커를 하나 이상 입력해주세요.")

        # [신규 통합] 🌟 상품 기획 마스터 프롬프트 하위 탭 
        with sub_tabs_plan[3]:
            st.markdown("#### [글로벌 대체자산 ETF 상품기획 프롬프트 - 5-Step 체인]")
            st.caption("대시보드에서 산출된 퀀트 수치, 동적 P&L, 샌드박스 편입 종목 등의 Raw Data를 프롬프트에 꽉 채워 넣었습니다. 순서대로 복사하여 AI에 입력하세요.")

            with st.container(border=True):
                st.markdown("##### 💡 0. 기획 상품 핵심 컨셉 요약 (AI 주입용)")
                st.caption("여기에 작성한 컨셉이 아래 Step 1 프롬프트에 자동 반영되어 AI가 어떤 상품을 기획해야 하는지 뚜렷한 방향성을 잡아줍니다.")
                user_idea = st.text_area("✍️ 기획하고자 하는 ETF의 핵심 아이디어를 자유롭게 적어주세요:", 
                                         value="AI 전력난 수혜를 입는 미국 핵심 데이터센터와 통신탑 리츠에만 집중 투자. LTV 45% 이하, FCF 마진 15% 이상의 퀄리티 필터링 적용. 단일 종목 캡 25%를 엄수하여 Top 3 종목에 75%를 편중. OTM 초단기 커버드콜과 환노출 전략을 결합하여 연 7.5% 인컴과 하방 버퍼를 제공하는 프리미엄 커스텀 지수 ETF.", height=80)

            if st.session_state.get('p_has_csv', False):
                st.error("📥 **[필수 엑셀 파일 첨부]** '외부 AI에 엑셀 첨부' 옵션을 체크하셨습니다. 프롬프트 입력 시 다운로드하신 **'기초자산 유니버스 엑셀(CSV) 파일'**을 대화창에 반드시 함께 업로드해 주세요!")
                csv_directive = f"내가 함께 첨부한 유니버스 엑셀(CSV) 원본 데이터를 분석하여, 아래 펀더멘털 필터링 룰(LTV {st.session_state.get('p_ltv', 45)}% 이하, FCF 마진 {st.session_state.get('p_fcf', 15)}% 이상)을 통과한 최종 편입 종목의 리스트를 추출하고 기획서 포트폴리오 섹션에 표 형태로 출력할 것."
            else:
                csv_directive = f"구체적인 개별 종목 데이터가 없으므로, 아래 펀더멘털 필터링 룰(LTV {st.session_state.get('p_ltv', 45)}% 이하, FCF 마진 {st.session_state.get('p_fcf', 15)}% 이상)을 적용했을 때 편입될 수 있는 대표적인 우량 기초자산들의 예시와 해당 필터링 방식의 논리적 타당성을 퀀트적 관점에서 서술할 것."

            trend_label = st.session_state.get('selected_trend_label', '혁신 타겟 인컴')
            
            # 여기서도 동기화
            if asset_class not in search_kw_map:
                search_kw_map[asset_class] = f'"{asset_class}"'
                
            policy_query = f'({search_kw_map.get(trend_label, trend_label)}) AND ("금융위" OR "규제" OR "법안" OR "가이드라인")'
            df_gap_news = get_realtime_news(policy_query, timeframe="30d", max_items=5)
            policy_news_text = ""
            if not df_gap_news.empty and "링크" in df_gap_news.columns and df_gap_news["링크"].iloc[0] != "":
                for _, row in df_gap_news.iterrows():
                    policy_news_text += f"- [{row['원본제목']}]({row['링크']})\n"
            else:
                policy_news_text = "최근 30일 내 관련 규제/정책 뉴스 없음"

            st.markdown("**📌 [Step 1: 기획 배경 및 글로벌 트렌드]**")
            p2_step1 = f"""너는 최고 수준의 자산운용사 ETF 상품개발(PD) 시니어 수석 매니저야. 첫 번째 작업으로 아래 Raw Data와 지시사항을 바탕으로 **[1. 기획 배경 및 글로벌 트렌드]** 파트를 아주 상세하게(약 1페이지 분량) 작성해 줘.

[기획 의도]: 
{user_idea}

[시장 배경 (글로벌 메가트렌드 및 최근 규제 동향 뉴스)]: 
현재 시장에서는 '{trend_label}' 테마가 강세로 자금을 강하게 흡수하고 있으나, 당사 라인업은 공백 상태임.
다음은 해당 테마와 관련된 최근 국내 정책/규제 뉴스(링크 포함)임.
{policy_news_text}

[지시사항]: 
위 기획 의도와 첨부된 규제 뉴스 링크 내용들을 근거로, 왜 지금 당장 이 상품을 선제적으로 기획하여 시장에 출시해야 하는지 '출시 당위성 및 거시적 배경'을 논리적으로 작성할 것."""
            st.code(p2_step1, language="text")

            st.markdown("**📌 [Step 2: 지수 산출 방법론 및 유니버스]**")
            p2_step2 = f"""두 번째 작업으로 본 ETF의 뼈대가 될 **[2. 지수 산출 방법론 및 유니버스]** 파트를 작성해 줘.

[기초자산 프록시 및 선정 논리]: 
- 프록시: {st.session_state.get('p_proxy', '데이터 없음')}
- 선정 논리: {st.session_state.get('p_proxy_reason', '데이터 없음')}

[펀더멘털 스크리닝 허들]: 
- LTV(부채비율) {st.session_state.get('p_ltv', 45)}% 이하
- 잉여현금흐름(FCF) 마진 {st.session_state.get('p_fcf', 15)}% 이상

[포트폴리오 가중치 및 리스크 통제 룰]:
- 비중 배분: {st.session_state.get('p_weight', '데이터 없음')}
- 단일 종목 상한선(Cap): {st.session_state.get('p_cap', 25)}%

[지시사항]: 
{csv_directive}
위의 확정된 스크리닝 룰과 가중치 배분 원칙을 명시하고, 기초자산의 유상증자/합병 시 S&P DJI 방식의 리밸런싱/이벤트 처리 원칙을 통해 어떻게 지수 연속성을 유지할 것인지 명시할 것."""
            st.code(p2_step2, language="text")

            st.markdown("**📌 [Step 3: 퀀트 성과 및 리스크 검증]**")
            st.warning("📸 **[필수 스크린샷 첨부]** [가상 지수 샌드박스] 하단의 **'하이브리드 시나리오 차트'** 이미지를 캡처하여 프롬프트와 함께 첨부해 주세요!")
            p2_step3 = f"""세 번째 작업으로 대시보드에서 연산된 퀀트 백테스트 Raw Data를 바탕으로 **[3. 퀀트 퍼포먼스 및 리스크 검증]** 파트를 작성해 줘.

[퀀트 백테스트 연산 결과 (최근 3년 기준)]:
- 샤프비율 (Sharpe Ratio): {st.session_state.get('p_sharpe', 0.0)}
- 실증 최대 낙폭 (MDD): {st.session_state.get('p_mdd', 0.0)}%
- S&P 500과의 상관계수: {st.session_state.get('p_corr', 0.0)}
(※ 위 수치는 보수적인 마찰비용 할인율이 이미 차감된 실전적 수치임)

[매크로 스트레스 테스트 시나리오]:
- 타겟 위기 국면: {st.session_state.get('p_scenario', '데이터 없음')}

[지시사항]: 
1) 입력된 수치와 내가 첨부한 '시나리오 밴드 차트' 이미지를 시각적으로 분석하여, 총수익률을 자본차익과 인컴수익으로 철저히 분해하고 하락장 방어 논리를 어필할 것.
2) 벤치마크와의 낮은 상관계수({st.session_state.get('p_corr', 0.0)})를 근거로, 기관 투자자가 기존 전통자산 포트폴리오에 이 ETF를 편입했을 때 얻을 수 있는 분산(헷지) 효과를 증명할 것.
3) 지정된 과거 매크로 위기 국면 당시의 벤치마크 대비 하방 경직성을 서술하고, 추적오차를 통제하기 위한 실제 운용 매니저 관점의 대응 전략을 추가할 것."""
            st.code(p2_step3, language="text")

            st.markdown("**📌 [Step 4: 상품 구조화 및 운용사 동적 P&L 분석]**")
            st.warning("📸 **[필수 스크린샷 첨부]** **'P&L 워터폴(1년 차 vs 2년 차)'** 이미지를 캡처하여 프롬프트와 함께 첨부해 주세요!")
            
            p2_step4 = f"""네 번째 작업으로, 실질적인 상품 런칭 및 재무 타당성을 다루는 **[4. 상품 구조화 및 운용사 비즈니스 모델]** 파트를 경영진 보고용으로 작성해 줘.

[환율 전략 및 타겟 페르소나]:
- 채택된 FX 전략: {st.session_state.get('p_fx', '환노출')}

[운용사 동적 P&L 시뮬레이션 Raw Data]:
- 타겟 경쟁사 티커: {st.session_state.get('p_comp_ticker', '유사ETF')}
- 경쟁사 보수율: {st.session_state.get('p_comp_ter', 0.50)}%
- 당사 유지 타겟 AUM: {st.session_state.get('p_aum', 1500)} 억 원
- 1년 차(런칭기) 총비용: 초기 마케팅 {st.session_state.get('p_launch_budget', 3.0):.2f}억 + 고정비 2.0억(지수개발비 포함)
- 1년 차(런칭기) 예상 순이익: {st.session_state.get('p_profit_y1', 0.0)} 억 원
- 2년 차(안정기) 총비용: 리텐션 마케팅 0.5억 + 유지 고정비 1.5억
- 2년 차(안정기) 예상 순이익: {st.session_state.get('p_profit_y2', 0.0)} 억 원

[지시사항]: 
1) 채택된 환율 전략({st.session_state.get('p_fx', '환노출')})과 인컴 속성을 고려할 때, 고객의 세후 수익률 측면에서 유리한 연금/ISA 채널 타겟팅 전략을 서술할 것.
2) 입력된 P&L Raw Data와 당사의 보수율 경쟁력을 기반으로 AUM 뺏어오기(Switching) 영업 전략을 구체화할 것.
3) 내가 함께 첨부한 'P&L 워터폴(1년 차 vs 2년 차)' 이미지를 근거로 삼아, 1년 차에는 지수 개발비 등 막대한 초기 비용을 감수하고도 BEP를 방어하며(Survival), 2년 차 안정화 기간부터는 마케팅/고정비가 축소되어 마진이 극대화되는 '캐시카우(Cash Cow)' 비즈니스 구조임을 임원진에게 강력하게 어필할 것."""
            st.code(p2_step4, language="text")

            st.markdown("**📌 [Step 5: 요약 보고서 및 투트랙 팩트시트 산출]**")
            p2_step5 = """마지막 작업이야. Step 1부터 Step 4까지 전개한 모든 퀀트 논리와 주입된 Raw Data를 총망라하여, 다음 두 가지 실무 산출물을 각각 분리해서 최종 완성해 줘.

1. **[Executive Summary (임원 보고용 요약본)]**: 
   본부장 및 C-Level 임원진이 1분 안에 의사결정을 내릴 수 있도록 1페이지 분량으로 요약된 공문서. (출시 당위성, 핵심 퀀트 성과, 1년 차 BEP 달성 및 2년 차 흑자 전환 구조, 경쟁사 타겟팅 전략이 일목요연하게 정리되어야 함)

2. **[Two-Track Sales Factsheet (투트랙 세일즈 팩트시트)]**: 
   - **리테일/PB용 (1p):** 일반 고객을 사로잡을 직관적인 카피라이팅, 핵심 소구 포인트 3가지, 투자 위험도 및 세금(Tax) 혜택 활용법을 알기 쉽게 도출.
   - **기관/법인영업용 (1p):** 연기금 등 기관 투자자를 설득하기 위해, 데이터로 증명된 퀀트 로직(추적오차 통제, 상관계수, 꼬리 위험 헷지 효과)과 유동성 안정성 위주의 논리 전개.

모든 출력물은 금융 투자 분석사 및 상품 개발 실무자의 전문적인 톤앤매너를 엄격히 준수하라."""
            st.code(p2_step5, language="text")
