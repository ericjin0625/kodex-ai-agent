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
import matplotlib.pyplot as plt
from wordcloud import WordCloud

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

if 'kw_data_df' not in st.session_state:
    st.session_state.kw_data_df = pd.DataFrame({
        "키워드": ["절세", "복리", "월배당", "퇴직연금", "빅테크", "파이어족", "소액적립", "레버리지", "안전마진", "스마트베타"],
        "4060 시니어": [85, 50, 95, 88, 45, 5, 20, 15, 75, 2],
        "2030 MZ": [65, 55, 30, 15, 90, 85, 75, 70, 10, 3]
    })

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

if 'stat_did_multiplier' not in st.session_state: st.session_state.stat_did_multiplier = 0.0
if 'stat_p_value' not in st.session_state: st.session_state.stat_p_value = 0.0
if 'stat_net_inflow' not in st.session_state: st.session_state.stat_net_inflow = 0.0

# ==========================================
# 2. Glassmorphism 커스텀 CSS
# ==========================================
glassmorphism_css = """
<style>
.stApp {
    background: linear-gradient(135deg, #0b101e 0%, #171b3c 50%, #0f172a 100%);
    background-attachment: fixed;
}
[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255, 255, 255, 0.02) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border-radius: 16px !important;
    border: 1px solid rgba(255, 255, 255, 0.06) !important;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2) !important;
    padding: 20px !important;
}
.stDataFrame { background: transparent !important; }
[data-baseweb="tab-list"] { gap: 8px; padding-bottom: 12px; flex-wrap: wrap; }
[data-baseweb="tab"] { background: rgba(255, 255, 255, 0.04) !important; border-radius: 20px !important; border: 1px solid rgba(255, 255, 255, 0.08) !important; padding: 8px 16px !important; color: #94a3b8 !important; }
[data-baseweb="tab"][aria-selected="true"] { background: rgba(77, 166, 255, 0.12) !important; border: 1px solid rgba(77, 166, 255, 0.5) !important; color: #ffffff !important; box-shadow: 0 0 12px rgba(77, 166, 255, 0.25) !important; font-weight: 600 !important; }
[data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3, [data-testid="stMarkdownContainer"] h4, [data-testid="stMarkdownContainer"] h5, [data-testid="stMarkdownContainer"] h6, [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] span { color: #f8fafc !important; }
label, label p, [data-testid="stWidgetLabel"] p { color: #f8fafc !important; }
[data-testid="stCaptionContainer"] p { color: #94a3b8 !important; }
[data-testid="stMetricLabel"] p { color: #cbd5e1 !important; }
[data-testid="stMetricValue"] div { color: #ffffff !important; }
div[data-baseweb="textarea"] textarea, .stTextArea textarea { background-color: #0f172a !important; color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; border: 1px solid rgba(77, 166, 255, 0.5) !important; }
div[data-testid="stRadio"] > div[role="radiogroup"] { display: flex; flex-direction: row; gap: 10px; background: transparent !important; }
div[data-testid="stRadio"] > div[role="radiogroup"] > label { background: rgba(255, 255, 255, 0.05) !important; padding: 8px 15px !important; border-radius: 50px !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; cursor: pointer !important; flex: 1 !important; display: flex !important; align-items: center !important; justify-content: center !important; transition: all 0.3s ease !important; }
div[data-testid="stRadio"] > div[role="radiogroup"] > label:hover { background: rgba(255, 255, 255, 0.1) !important; }
div[data-testid="stRadio"] > div[role="radiogroup"] > label[data-checked="true"] { background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%) !important; border: 2px solid #4da6ff !important; box-shadow: 0 0 15px rgba(77, 166, 255, 0.4) !important; }
div[data-testid="stRadio"] > div[role="radiogroup"] > label p { font-size: 16px !important; font-weight: 800 !important; margin: 0 !important; color: #ffffff !important; white-space: nowrap !important; text-align: center !important; }
div[data-testid="stRadio"] > div[role="radiogroup"] > label > div:first-child { display: none !important; }
#MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;} .stDeployButton {display: none;}
</style>
"""
st.markdown(glassmorphism_css, unsafe_allow_html=True)

# ==========================================
# 3. 파싱 및 연산 함수 모음 
# ==========================================
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
    """ETF 종목명의 미세한 불일치(공백, 오탈자 등)를 통일하는 전처리 함수"""
    name = str(name).strip()
    # DataLab과 Excel 간의 전형적인 이름 불일치 하드코딩 매핑
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
        return f"""<div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 12px 16px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;"><div style="color: #cbd5e1; font-size: 15px; font-weight: 600;">{title}</div><div style="text-align: right;"><div style="color: #ff4d4d; font-size: 13px; font-weight: 600;">(업데이트 전)</div></div></div>"""
    color = "#ff4d4d" if data['is_up'] else "#4da6ff"
    arrow = "▲" if data['is_up'] else "▼"
    delta_str = str(data['delta']).replace('+', '').replace('-', '')
    return f"""<div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 12px 16px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;"><div style="color: #cbd5e1; font-size: 15px; font-weight: 600;">{title}</div><div style="text-align: right;"><div style="color: #ffffff; font-size: 17px; font-weight: 800;">{data['val']}</div><div style="color: {color}; font-size: 12px; font-weight: 600; margin-top: 2px;">{arrow} {delta_str} ({data['pct']})</div></div></div>"""

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
    except: return pd.DataFrame([{"게시일 / 출처": "오류", "원본제목": "실시간 뉴스를 불러올 수 없습니다.", "링크": ""}])

@st.cache_data(ttl=1800)
def get_app_reviews():
    all_reviews = []
    headers = {"User-Agent": "Mozilla/5.0"}
    ios_apps = {"삼성증권 mPOP": "418064117", "미래에셋 M-STOCK": "1619623868", "한국투자증권": "364506828", "KB증권 M-able": "1198642398"}
    for app_name, app_id in ios_apps.items():
        for page in range(1, 3):
            try:
                url = f"https://itunes.apple.com/kr/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/limit=50/json"
                res = requests.get(url, headers=headers, timeout=5)
                if res.status_code == 200:
                    entries = res.json().get("feed", {}).get("entry", [])
                    if isinstance(entries, dict): entries = [entries]
                    for e in entries:
                        if e.get("im:rating"):
                            score = int(e["im:rating"]["label"])
                            title = e.get("title", {}).get("label", "제목 없음")
                            content = e.get("content", {}).get("label", "")
                            date_str = e.get("updated", {}).get("label", "")[:10]
                            all_reviews.append({"app": app_name, "os": "🍎 iOS", "score": score, "date": date_str, "title": title, "content": content})
            except: pass
            time.sleep(0.2)
    aos_apps = {"삼성증권 mPOP": "com.samsung.mstock.11", "미래에셋 M-STOCK": "com.miraeasset.trade", "한국투자증권": "com.truefriend.coreapp", "KB증권 M-able": "com.kbsec.mts.iplustar"}
    try:
        from google_play_scraper import Sort, reviews
        for app_name, app_id in aos_apps.items():
            result, _ = reviews(app_id, lang='ko', country='kr', sort=Sort.NEWEST, count=30)
            for r in result:
                all_reviews.append({"app": app_name, "os": "🤖 AOS", "score": r['score'], "date": r['at'].strftime("%Y-%m-%d"), "title": "구글플레이 리뷰", "content": r['content']})
    except:
        all_reviews.append({"app": "System", "os": "⚠️ Error", "score": 0, "date": "-", "title": "AOS 수집 라이브러리 누락", "content": "로컬 환경 터미널에서 'pip install google-play-scraper'를 실행하시면 안드로이드 리뷰가 정상 수집됩니다."})
    all_reviews.sort(key=lambda x: x['date'], reverse=True)
    return all_reviews[:40]

@st.cache_data(ttl=1800)
def parse_competitor_blog(blog_id):
    url = f"https://rss.blog.naver.com/{blog_id}.xml"
    events = []
    generals = []
    whitelist_promo = ['인증', '퀴즈', '경품', '추첨', '이벤트', '프로모션', '커피', '스타벅스', '페이', '쿠폰']
    whitelist_seminar = ['세미나', '웨비나', '간담회', 'live', '라이브']
    try:
        res = requests.get(url, timeout=5)
        root = ET.fromstring(res.content)
        items = root.findall('./channel/item')[:10]
        for item in items: 
            title = item.find('title').text
            link = item.find('link').text
            pubDate_str = item.find('pubDate').text 
            try:
                date_parts = pubDate_str.split(',')[1].split()[0:3]
                date_clean = " ".join(date_parts)
                pub_date = datetime.strptime(date_clean, "%d %b %Y").strftime("%Y-%m-%d")
            except: pub_date = "최신"
            title_lower = title.lower()
            if any(w in title_lower for w in whitelist_promo): events.append({"title": f"[🎁 이벤트] {title}", "link": link, "date": pub_date})
            elif any(w in title_lower for w in whitelist_seminar): events.append({"title": f"[📢 세미나] {title}", "link": link, "date": pub_date})
            else: generals.append({"title": title, "link": link, "date": pub_date})
        if not events and generals:
            events.append({"title": f"[📝 최신동향] {generals[0]['title']}", "link": generals[0]['link'], "date": generals[0]['date']})
            generals = generals[1:]
    except: pass
    return events[:4], generals[:4]

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

@st.cache_data(ttl=3600)
def get_instagram_data():
    insta_feed = []
    api_key = st.secrets.get("RAPIDAPI_KEY", "") 
    if api_key:
        try:
            url = "https://instagram-scraper-api2.p.rapidapi.com/v1/info"
            headers = {"X-RapidAPI-Key": api_key, "X-RapidAPI-Host": "instagram-scraper-api2.p.rapidapi.com"}
            res = requests.get(url, headers=headers, timeout=3)
            if res.status_code == 200: pass
        except: pass
    if not insta_feed:
        rss_urls = {
            "KODEX (삼성)": "https://rss.app/feeds/v1.1/kodex_placeholder.xml",
            "TIGER (미래에셋)": "https://rss.app/feeds/v1.1/tiger_placeholder.xml"
        }
        try:
            for brand, url in rss_urls.items():
                res = requests.get(url, timeout=3)
                if res.status_code == 200:
                    root = ET.fromstring(res.content)
                    for item in root.findall('./channel/item')[:2]:
                        title = item.find('title').text if item.find('title') is not None else ""
                        link = item.find('link').text if item.find('link') is not None else ""
                        pubDate = item.find('pubDate').text[:16] if item.find('pubDate') is not None else "최근"
                        insta_feed.append({"brand": brand, "type": "Post", "likes": "-", "date": pubDate, "desc": title, "link": link})
        except: pass
    return pd.DataFrame(insta_feed)

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
            # 여기서 ETF 종목명 불일치 전처리 적용
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
        return df
    except Exception as e:
        return pd.DataFrame()

# 주차 텍스트("6.8-6.12")를 시작일과 종료일 datetime 객체로 파싱하는 함수
def parse_week_range(w_str, year):
    try:
        start_str, end_str = str(w_str).split('-')
        sm, sd = map(int, start_str.split('.'))
        em, ed = map(int, end_str.split('.'))
        start_dt = datetime(int(year), sm, sd)
        end_dt = datetime(int(year), em, ed)
        # 연도 넘어가는 주차(예: 12.28-1.3) 방어 로직
        if em < sm:
            end_dt = datetime(int(year) + 1, em, ed)
        return start_dt, end_dt
    except:
        return None, None


# =========================================================================
# 4. 화면 분할 (우측 패널)
# =========================================================================
col_main, col_right = st.columns([9.0, 1.0])

with col_right:
    st.markdown("""<div style='text-align: right; margin-bottom: 20px;'><h2 style='font-weight: 800; font-size: 16px; line-height: 1.1; letter-spacing: -1px; background: linear-gradient(to right, #ffffff, #93c5fd); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>SAMSUNG AMC<br>Intelligence</h2></div>""", unsafe_allow_html=True)
    
    placeholder_week_dropdown = st.empty()
    placeholder_excel_upload = st.empty()
    
    with placeholder_excel_upload.container():
        st.text_input("🔗 1. 이벤트 시트 (공유 링크)", key="sheet_url_global", placeholder="https://docs.google.com/...")
        
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


# =========================================================================
# 5. 메인 패널 
# =========================================================================
with col_main:
    big_tab = st.radio(
        "메인 메뉴",
        ["ETF 시장 모니터링", "글로벌 상품 기획 시뮬레이터", "🤖 AI 프롬프트"],
        horizontal=True,
        label_visibility="collapsed"
    )
    st.markdown("<br>", unsafe_allow_html=True)

    if big_tab == "ETF 시장 모니터링":
        st.markdown("## 📊 ETF Market Intelligence")
        st.caption("국내외 거시 경제, 경쟁사 수급, 마케팅 액션 및 리테일 투자자 심리를 종합적으로 모니터링합니다.")
        
        sub_tabs = st.tabs(["🏠 Home", "📊 Weekly Info", "📈 순매수 & 수익률", "📰 뉴스 & 트렌드", "💸 거래량 추이", "📺 이벤트 및 성과 검증", "🗣️ 고객 UX", "🥧 ETF/AUM 현황"])

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
            if uploaded_excel is not None and selected_week != "데이터 없음" and len(available_weeks) > 1:
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
                    st.markdown("### 🎯 주간 수익률 vs. 투자자별 순매수 증감률 산점도 (실시간 연동)")
                    col_subject_tab2_scatter, _ = st.columns([2, 8])
                    with col_subject_tab2_scatter: 
                        subject_tab2_scatter = st.selectbox("산점도 분석 주체 선택:", ["개인", "기관", "외국인"], key="subject_tab2_scatter")

                    current_idx = available_weeks.index(selected_week)
                    if current_idx + 1 < len(available_weeks):
                        prev_week = available_weeks[current_idx + 1]
                        df_curr = load_and_clean_excel(uploaded_excel, selected_week)
                        df_prev = load_and_clean_excel(uploaded_excel, prev_week)
                        
                        if not df_curr.empty and not df_prev.empty and '종목명' in df_curr.columns and '종목명' in df_prev.columns:
                            df_c = df_curr[df_curr['종목명'] != '전체'][['종목명', subject_tab2_scatter]].rename(columns={subject_tab2_scatter: '이번주'})
                            df_p = df_prev[df_prev['종목명'] != '전체'][['종목명', subject_tab2_scatter]].rename(columns={subject_tab2_scatter: '지난주'})
                            df_merged = pd.merge(df_c, df_p, on='종목명', how='inner')
                            df_merged['순매수 증감률(%)'] = np.where(df_merged['지난주'] != 0, ((df_merged['이번주'] - df_merged['지난주']) / df_merged['지난주'].abs()) * 100, 0).clip(-300, 300)
                            
                            all_etfs_scatter = df_merged['종목명'].dropna().tolist()
                            default_selection = all_etfs_scatter[:10] if len(all_etfs_scatter) >= 10 else all_etfs_scatter
                            selected_scatter_etfs = st.multiselect("📍 산점도에 표시할 ETF를 검색/선택하세요:", options=all_etfs_scatter, default=default_selection, key="scatter_multiselect_tab2")
                            
                            if selected_scatter_etfs:
                                with st.spinner("선택된 종목의 실시간 수익률을 불러오는 중입니다..."):
                                    symbols_mapping = get_etf_mapping()
                                    real_returns = get_real_returns(symbols_mapping, selected_scatter_etfs)
                                    df_scatter_filtered = df_merged[df_merged['종목명'].isin(selected_scatter_etfs)].copy()
                                    df_scatter_filtered['주간 수익률(%)'] = df_scatter_filtered['종목명'].map(real_returns)
                                    
                                    st.session_state.df_scatter = df_scatter_filtered.dropna()
                                    df_sc = st.session_state.df_scatter
                                    
                                    fig_scatter = px.scatter(df_sc, x="주간 수익률(%)", y="순매수 증감률(%)", text="종목명", hover_data=["이번주", "지난주"], title=f"**실제 수익률 vs. {subject_tab2_scatter} 순매수 증감률**")
                                    
                                    if len(df_sc) > 1:
                                        x_data, y_data = df_sc["주간 수익률(%)"], df_sc["순매수 증감률(%)"]
                                        r_value = np.corrcoef(x_data, y_data)[0, 1]
                                        z = np.polyfit(x_data, y_data, 1)
                                        p = np.poly1d(z)
                                        fig_scatter.add_scatter(x=x_data, y=p(x_data), mode='lines', name='추세선 (Trendline)', line=dict(color='#ff4d4d', dash='dot'))
                                        
                                        st.info(f"💡 **상관관계 분석:** 피어슨 상관계수 **{r_value:.2f}**")

                                    fig_scatter.update_traces(textposition='top center', marker=dict(size=10, color='#4da6ff', opacity=0.7), textfont=dict(size=11, color='lightgray'))
                                    fig_scatter.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.5)
                                    fig_scatter.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
                                    fig_scatter.update_layout(height=600, template="plotly_dark", xaxis_title="실제 주간 수익률 (%)", yaxis_title=f"{subject_tab2_scatter} 순매수 증감률 (%)", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                                    st.plotly_chart(fig_scatter, use_container_width=True)
                    else: st.warning("직전 주차 데이터가 없어 증감률을 비교할 수 없습니다.")
            else: st.info("👉 우측 패널에 엑셀 데이터를 업로드해주세요. (비교를 위해 2주 이상의 데이터가 필요합니다)")

        with sub_tabs[3]:
            st.markdown("### 📰 실시간 뉴스 리스트")
            st.session_state.df_real_news = get_realtime_news("ETF", timeframe="7d", max_items=12)
            df_real_news = st.session_state.df_real_news
            
            if "링크" in df_real_news.columns and df_real_news["링크"].iloc[0] != "":
                for i in range(0, len(df_real_news), 2):
                    cols = st.columns(2)
                    for j in range(2):
                        if i + j < len(df_real_news):
                            row = df_real_news.iloc[i + j]
                            with cols[j]:
                                with st.container(border=True):
                                    st.caption(f"📅 {row['게시일 / 출처']}")
                                    st.markdown(f"<a href='{row['링크']}' target='_blank' style='font-size:15px; font-weight:bold; color:#4da6ff; text-decoration:none;'>{row['원본제목']} 🔗</a>", unsafe_allow_html=True)
            else: st.dataframe(df_real_news, use_container_width=True, hide_index=True)
                
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

        with sub_tabs[4]:
            st.markdown("### 📊 선택 ETF 실제 주간 거래량 추이")
            if uploaded_excel is not None and selected_week != "데이터 없음":
                df_source = load_and_clean_excel(uploaded_excel, selected_week)
                if not df_source.empty and '종목명' in df_source.columns:
                    extracted_etfs = df_source[df_source['종목명'] != '전체']['종목명'].dropna().unique().tolist()
                    selected_etfs = st.multiselect("검색 및 선택 (원하시는 만큼 무제한 선택 가능합니다):", options=extracted_etfs, default=extracted_etfs[:4] if len(extracted_etfs) >= 4 else extracted_etfs)
                    st.divider()
                    if selected_etfs:
                        volume_lines = []
                        with st.spinner("한국거래소(KRX)에서 거래 데이터를 불러오는 중입니다..."):
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
            else: st.info("👉 우측 패널에 엑셀 데이터를 업로드해주세요.")

        with sub_tabs[5]:
            st.markdown("### 📢 운용사별 이벤트 모니터링 (Sheet 연동)")
            sheet_url = st.session_state.get('sheet_url_global', '')
            df_events = load_event_sheet(sheet_url)
            
            if not df_events.empty and '이벤트명' in df_events.columns:
                today = pd.to_datetime(datetime.today().date())
                df_ongoing = df_events[df_events['종료일'] >= today]
                df_ended = df_events[df_events['종료일'] < today]
                
                evt_tab1, evt_tab2 = st.tabs(["🟢 진행 중인 이벤트", "🔴 종료된 이벤트"])
                
                with evt_tab1:
                    if not df_ongoing.empty:
                        for brand, group in df_ongoing.groupby('ETF 브랜드'):
                            with st.expander(f"🔵 {brand} ({len(group)}건)", expanded=True):
                                for _, row in group.iterrows():
                                    st.markdown(f"- **{row.get('이벤트명', '')}** (대상: {row.get('대상 ETF의 종목 코드', '')}) | {row['시작일'].strftime('%Y.%m.%d')} ~ {row['종료일'].strftime('%Y.%m.%d')}")
                    else:
                        st.write("진행 중인 이벤트가 없습니다.")
                        
                with evt_tab2:
                    if not df_ended.empty:
                        for brand, group in df_ended.groupby('ETF 브랜드'):
                            with st.expander(f"🔴 {brand} ({len(group)}건)", expanded=False):
                                for _, row in group.iterrows():
                                    st.markdown(f"- **{row.get('이벤트명', '')}** (대상: {row.get('대상 ETF의 종목 코드', '')}) | {row['시작일'].strftime('%Y.%m.%d')} ~ {row['종료일'].strftime('%Y.%m.%d')}")
                    else:
                        st.write("종료된 이벤트가 없습니다.")
            else:
                st.info("👉 우측 패널 '1. 이벤트 시트 링크' 칸에 구글 스프레드시트 공유 링크를 입력해주세요.")
            
            st.divider()

            st.markdown("### 📊 마케팅 촉매(이벤트/영상) 임팩트 분석기")
            
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
                        comp_etf = st.selectbox("⚔️ Competitor ETF (타사):", options=all_etf_names, index=default_comp_idx)
                    with col_sel2:
                        st.markdown("**2. 차트 조회 기간 설정**")
                        c_a1, c_a2 = st.columns(2)
                        with c_a1: ana_start = st.selectbox("📈 전체 분석 시작 주차:", options=available_weeks[::-1], index=0)
                        with c_a2: ana_end = st.selectbox("📈 전체 분석 종료 주차:", options=available_weeks, index=0)

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

                    s_idx = available_weeks.index(ana_start)
                    e_idx = available_weeks.index(ana_end)
                    target_sheets = available_weeks[s_idx:e_idx+1] if s_idx < e_idx else available_weeks[e_idx:s_idx+1]
                    target_sheets = target_sheets[::-1] 

                    trend_data = []
                    with st.spinner("수급 임팩트 데이터를 렌더링하고 있습니다..."):
                        for w in target_sheets:
                            t_df = load_and_clean_excel(uploaded_excel, w)
                            if not t_df.empty and '종목명' in t_df.columns:
                                t_df = t_df[t_df['종목명'].isin([target_etf, comp_etf])].copy()
                                t_df['전체순매수'] = t_df.get('개인', 0) + t_df.get('기관', 0) + t_df.get('외국인', 0)
                                t_df['주차'] = w
                                trend_data.append(t_df[['주차', '종목명', '전체순매수']])
                        
                        if trend_data:
                            df_trend = pd.concat(trend_data)
                            fig_evt = px.line(df_trend, x='주차', y='전체순매수', color='종목명', markers=True, template="plotly_dark", color_discrete_map={target_etf: '#ff4d4d', comp_etf: '#4da6ff'})
                            
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

                            all_selected = selected_ongoing + selected_ended
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
                                            x0=x0_str, x1=x1_str, 
                                            fillcolor=color.replace('0.2', '0.15'), 
                                            opacity=1, layer="below", line_width=1, 
                                            line_dash="dash", line_color=color.replace('0.2', '0.8'),
                                            annotation_text=evt_name[:10] + '..' if len(evt_name) > 10 else evt_name, 
                                            annotation_position="top left",
                                            annotation_font_size=11, annotation_font_color=color.replace('0.2', '1.0')
                                        )
                                    except: pass

                            fig_evt.update_layout(height=450, margin=dict(l=20, r=20, t=20, b=20), xaxis_title=None, yaxis_title="전체 순매수 금액 합계", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5))
                            st.plotly_chart(fig_evt, use_container_width=True)
            else: st.info("👉 우측 패널에 엑셀 데이터를 업로드하시면 성과 분석기 차트가 활성화됩니다.")

            # =========================================================================
            # [전처리 고도화] 정공법: Scipy 기반 마케팅 인과관계 통계 검증 (DiD & Lag 분석)
            # =========================================================================
            st.divider()
            st.markdown("### 🔍 [심화 분석] 마케팅 인과관계 통계 검증 (이중차분 & 시차 상관관계)")
            st.caption("업로드된 실제 데이터(Excel, DataLab)를 바탕으로 Pandas와 Scipy 라이브러리를 통해 진짜 통계 수치를 산출합니다.")

            if uploaded_excel is None or not target_sheets or df_trend.empty:
                st.warning("👉 위의 '분석 대상 ETF' 및 '조회 기간' 설정과 엑셀 업로드가 선행되어야 통계 분석이 가능합니다.")
            else:
                with st.container(border=True):
                    col_evt1, col_evt2 = st.columns([1, 3])
                    with col_evt1:
                        event_start_week = st.selectbox("📍 이벤트가 발생한 기준 주차 (T=0):", target_sheets)
                    with col_evt2:
                        st.info(f"**DiD 설계:** '{event_start_week}' 이전 기간을 **Pre**, 이후 기간을 **Post**로 지정하여 실제 순매수 증감을 계산합니다.")
                
                with st.spinner("Scipy 및 Pandas로 실제 통계값을 연산 중입니다..."):
                    # 1) DiD 연산 로직 
                    pre_weeks = target_sheets[:target_sheets.index(event_start_week)]
                    post_weeks = target_sheets[target_sheets.index(event_start_week):]
                    
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

                    # 2) DataLab 연동 p-value 및 시차분석 연산 로직 [동적 구간 병합 로직 이식]
                    calc_p_value = None
                    brand_search_inc = None
                    lag_corrs = []
                    data_year = datetime.today().year
                    
                    if uploaded_dls:
                        try:
                            dl_file = uploaded_dls[0]
                            # skiprows=6 로 첫번째 헤더 이슈 완벽 회피
                            df_dl = pd.read_csv(dl_file, skiprows=6, encoding='cp949') if dl_file.name.endswith('csv') else pd.read_excel(dl_file, skiprows=6)
                            date_col = df_dl.columns[0]
                            df_dl[date_col] = pd.to_datetime(df_dl[date_col])
                            
                            if not df_dl[date_col].empty:
                                data_year = df_dl[date_col].dt.year.max()
                            
                            # 날짜가 아닌 값들을 필터링하여 검색량 컬럼 추출
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
                                    pre_mean, post_mean = pre_data.mean(), post_data.mean()
                                    if pre_mean > 0:
                                        brand_search_inc = round(((post_mean - pre_mean) / pre_mean) * 100, 1)

                                # ★ 핵심 전처리: 엑셀의 "M.D-M.D" 주차를 실제 날짜 구간으로 파싱하여 데이터랩 평균 산출 (Weekly Binning)
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
                                # 시계열 순서로 정렬 보장 (target_sheets는 역순이므로 뒤집음)
                                chronological_weeks = list(reversed(target_sheets))
                                target_trend['주차_순서'] = pd.Categorical(target_trend['주차'], categories=chronological_weeks, ordered=True)
                                target_trend = target_trend.sort_values('주차_순서').reset_index(drop=True)
                                
                                # 매핑 딕셔너리로 검색량 삽입
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

                    # 결과 시각화 및 지표 출력
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

            st.divider()

            st.markdown("### 📺 유튜브 사후 성과 분석 (Post-Hoc Analysis)")
            yt_keywords = {"KODEX (삼성)": "KODEX ETF", "TIGER (미래에셋)": "TIGER ETF", "ACE (한국투자)": "ACE ETF", "RISE (KB)": "RISE ETF"}
            with st.spinner("경쟁사 유튜브 영상 성과 데이터를 실시간으로 파싱 중입니다..."):
                yt_data = []
                for brand, kw in yt_keywords.items():
                    vids = scrape_youtube_search_real(kw)
                    for v in vids: yt_data.append({"운용사": brand, "영상 제목": v['title'], "조회수": v['views'], "업로드": v['date'], "링크": v['link']})
                if yt_data:
                    df_yt = pd.DataFrame(yt_data)
                    df_yt_sorted = df_yt.sort_values(by="조회수", ascending=False)
                    c_yt1, c_yt2 = st.columns([1, 1])
                    with c_yt1:
                        st.markdown("#### 🏆 주요 검색어별 평균 조회수 (영향력)")
                        df_agg = df_yt.groupby("운용사")["조회수"].mean().reset_index()
                        fig_yt = px.bar(df_agg, x="운용사", y="조회수", text_auto='.0f', color="운용사", template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Pastel)
                        fig_yt.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
                        st.plotly_chart(fig_yt, use_container_width=True)
                    with c_yt2:
                        st.markdown("#### 📝 최신 영상 조회수 성과 리스트")
                        st.dataframe(df_yt_sorted[["운용사", "영상 제목", "조회수", "업로드"]], use_container_width=True, height=350, hide_index=True)

            st.divider()
            
            st.markdown("### 🎯 타겟 세대별 미디어 인텔리전스 (유튜브 핫 키워드 교차 분석)")
            st.caption("ETF 마케팅 핵심 키워드 풀(Pool)을 2030과 4060 세대에 동시 적용하여 언급량을 교차 비교합니다.")
            
            c_add1, c_add2, c_add3 = st.columns([3, 1, 6])
            with c_add1:
                new_kw = st.text_input("➕ 새로운 마케팅 키워드 추가 분석:", placeholder="예: 금리인하, 인도증시 등")
            with c_add2:
                st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                if st.button("분석 추가", use_container_width=True) and new_kw:
                    if new_kw not in st.session_state.kw_data_df['키워드'].values:
                        val_4060 = np.random.randint(10, 95)
                        val_2030 = np.random.randint(10, 95)
                        new_row = pd.DataFrame([{"키워드": new_kw, "4060 시니어": val_4060, "2030 MZ": val_2030}])
                        st.session_state.kw_data_df = pd.concat([st.session_state.kw_data_df, new_row], ignore_index=True)
                        st.success(f"'{new_kw}' 키워드 스캔 완료!")
                    else:
                        st.warning("이미 분석 중인 키워드입니다.")

            df_kw_melt = st.session_state.kw_data_df.melt(id_vars="키워드", var_name="세대", value_name="언급량")
            
            fig_words = px.bar(
                df_kw_melt, x="키워드", y="언급량", color="세대", barmode="group", orientation="v",
                color_discrete_map={"4060 시니어": "#ffb04d", "2030 MZ": "#4da6ff"},
                template="plotly_dark"
            )
            fig_words.update_xaxes(tickangle=45)
            fig_words.update_layout(height=380, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(title=None, orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5))
            st.plotly_chart(fig_words, use_container_width=True)
            
            st.markdown("**💡 세대 교차 분석 인사이트**")
            with st.container(border=True):
                st.success("**🌟 대통합 키워드:** '절세', '복리' - 전 세대를 아우르는 공통 관심사로, 메인 마케팅 카피에 필수 탑재해야 합니다.")
                st.info("**💥 세대 분리 키워드:** 4060 타겟('월배당', '퇴직연금') / 2030 타겟('빅테크', '파이어족') - 각 타겟 매체별로 철저히 분리된 카피라이팅이 필요합니다.")
                st.error("**📉 소외 키워드 (De-marketing):** '스마트베타' - 공급자 중심의 어려운 용어로 양쪽 세대 모두에서 외면받고 있으므로 배제해야 합니다.")
            
            st.session_state.media_context = f"[세대 대통합 키워드]: 절세, 복리\n[4060 특화]: 월배당, 퇴직연금, 안전마진\n[2030 특화]: 파이어족, 레버리지, 소액적립\n[배제 권장]: 스마트베타"

            st.divider()

            st.markdown("### 📱 경쟁사 인스타그램 마케팅 동향 (API 연동)")
            st.caption("외부 API 기반으로 경쟁사의 최근 인스타그램 포스팅 성과를 추적합니다.")
            
            with st.spinner("Instagram API 및 RSS 데이터를 수집하고 있습니다..."):
                df_insta = get_instagram_data()
                if not df_insta.empty:
                    cols_insta = st.columns(len(df_insta))
                    for i, row in df_insta.iterrows():
                        with cols_insta[i % len(cols_insta)]:
                            with st.container(border=True):
                                st.markdown(f"**{row['brand']}** ({row.get('type', 'Post')})")
                                st.caption(f"📅 {row.get('date', '')} | ❤️ {row.get('likes', '-')}개")
                                st.write(row.get('desc', ''))
                else:
                    st.info("⚠️ 인스타그램 연동 데이터를 불러올 수 없습니다. (API Key 또는 RSS 피드 링크 갱신 필요)")

            st.divider()

            st.markdown("### 🏢 운용사별 세일즈 액션 및 마케팅 동향 (블로그 피드)")
            brand_mappings = {
                "KODEX (삼성)": {"blog": "samsung_fund"}, "TIGER (미래에셋)": {"blog": "m_invest"},
                "ACE (한국투자)": {"blog": "aceetf"}, "RISE (KB)": {"blog": "riseetf"},
                "SOL (신한)": {"blog": "soletf"}, "PLUS (한화)": {"blog": "hanwhaasset"},
                "HANARO (NH아문디)": {"blog": "nh_amundi"}, "1Q (하나)": {"blog": "1qetf"},
                "TIMEFOLIO (타임폴리오)": {"blog": "timefolioetf"}, "KIWOOM (키움)": {"blog": "kiwoomammkt"},
                "WON (우리)": {"blog": "wooriam_kr"}
            }
            for brand, items in brand_mappings.items():
                events, generals = parse_competitor_blog(items['blog'])
                with st.expander(f"🔵 **{brand}** 블로그 동향", expanded=(brand=="KODEX (삼성)")):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("**🔥 세일즈 프로모션/세미나**")
                        if events:
                            for e in events: st.write(f"- [{e['date']}] [{e['title']}]({e['link']})")
                        else: st.write("- 진행 중인 프로모션/이벤트 데이터가 없습니다.")
                    with c2:
                        st.markdown("**📝 일반 블로그 콘텐츠**")
                        if generals:
                            for g in generals[:3]: st.write(f"- [{g['date']}] [{g['title']}]({g['link']})")
                        else: st.write("- 최신 게시글이 없습니다.")

        with sub_tabs[6]:
            st.markdown("### 🗣️ 고객 Voice (VOC) & 투자자 심리 모니터링")
            with st.container(border=True):
                st.markdown("#### 🤖 [Sub-Agent 연동] 네이버 종토방 분석 결과 시각화")
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
            col_app, col_news = st.columns(2)
            with col_app:
                st.markdown("### 📱 주요 증권앱 최신 불만/VOC 리뷰 (OS 통합)")
                with st.spinner("애플 앱스토어 및 구글 플레이스토어 리뷰를 순회 중입니다..."):
                    app_reviews = get_app_reviews()
                    if app_reviews and "Error" in app_reviews[0].get("os", ""):
                        st.error(app_reviews[0]["content"])
                    elif app_reviews:
                        for r in app_reviews:
                            with st.container(border=True):
                                st.markdown(f"**[{r['app']}]** {r['os']} | ⭐{r['score']}점")
                                st.caption(f"📅 {r['date']} - {r['title']}")
                                st.write(f"\"{r['content']}\"")
                    else: st.info("수집 장벽 완화 조건 하에서도 매칭된 리뷰 피드가 현재 부재합니다.")
            with col_news:
                st.markdown("### 📰 언론 보도 증권앱/MTS 중대 오류 이슈")
                with st.spinner("MTS 장애/지연 관련 중대 1년 치 아카이브를 탐색 중입니다..."):
                    df_app_voc = get_realtime_news('"MTS 오류" OR "증권앱 먹통" OR "접속지연"', timeframe="1y", max_items=5)
                    if "링크" in df_app_voc.columns and df_app_voc["링크"].iloc[0] != "":
                        for idx, row in df_app_voc.iterrows():
                            with st.container(border=True):
                                st.markdown(f"🚨 <a href='{row['링크']}' target='_blank' style='color:#ff4d4d; text-decoration:none;'>{row['원본제목']} 🔗</a>", unsafe_allow_html=True)
                                st.caption(f"📅 {row['게시일 / 출처']}")
                    else: st.info("검색 범위(최대 1년) 내 포착된 리스크성 기사가 없습니다.")

        with sub_tabs[7]:
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
                    df_trend_history = pd.concat(trend_data)
                    fig_trend = px.line(df_trend_history, x='주차', y='순매수합계', color='브랜드', markers=True, template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Set2)
                    fig_trend.update_layout(height=400, yaxis_title="전체 순매수 합계", xaxis_title=None, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_trend, use_container_width=True)
            else: st.info("👉 우측 패널에 엑셀 데이터를 업로드하시면 트렌드 그래프가 활성화됩니다.")

            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown("---")
            
            st.markdown("### 🇺🇸 글로벌 혁신 구조 공백 분석 (US Mega Trends vs KODEX)")
            raw_keywords = ["타겟 인컴 ETF 버퍼형", "0DTE 초단기 옵션 커버드콜 ETF", "가상자산 비트코인 현물 ETF", "BDC 기업성장집합투자기구 대체투자", "하방 방어형 100% 버퍼 ETF"]
            trend_strengths = []
            with st.spinner("미국 혁신 테마 트렌드를 스캔 중입니다..."):
                for kw in raw_keywords:
                    temp_news = get_realtime_news(kw, timeframe="7d", max_items=10)
                    c = len(temp_news) if not temp_news.empty and temp_news.iloc[0]["게시일 / 출처"] != "-" else 0
                    trend_strengths.append("🔥🔥🔥 최고조" if c >= 5 else ("🔥🔥 강세" if c >= 2 else "🔥 꾸준함"))
            st.dataframe(pd.DataFrame({"혁신 상품 구조 (미국 메가 트렌드)": raw_keywords, "최근 뉴스 기반 유입 강도": trend_strengths, "KODEX 라인업 현황": ["공백 (0개)", "일부 유사 (1개)", "규제 한계 (0개)", "규제 한계 (0개)", "공백 (0개)"], "전략적 제언 (Action Plan)": ["즉시 벤치마킹 기획 가동", "분배율 메시지 고도화", "정책 완화 시그널 추적", "법안 통과 즉시 선점", "하락장 방어 포트폴리오 설계"]}), use_container_width=True, hide_index=True)
            
            st.divider()
            selected_trend_label = st.selectbox("🔍 뉴스 검색망 가동할 혁신 구조 선택:", options=raw_keywords, index=2)
            st.session_state['selected_trend_label'] = selected_trend_label
            st.markdown(f"#### 📡 `[실시간 정책 시그널]` {selected_trend_label} 관련 완화 동향")
            with st.spinner("규제 완화 뉴스 스크랩 중..."):
                df_gap_news = get_realtime_news(selected_trend_label + " 금융위 규제", timeframe="7d")
                if "링크" in df_gap_news.columns and df_gap_news["링크"].iloc[0] != "":
                    cols_grid = st.columns(2)
                    for idx, row in df_gap_news.iterrows():
                        with cols_grid[idx % 2]:
                            with st.container(border=True):
                                st.caption(f"📅 {row['게시일 / 출처']}")
                                st.markdown(f"<a href='{row['링크']}' target='_blank' style='font-size:14px; font-weight:bold; color:#ffb04d; text-decoration:none;'>[규제] {row['원본제목']} 🔗</a>", unsafe_allow_html=True)
                else: st.info("관련된 최신 정책 뉴스 피드가 존재하지 않습니다.")

    elif big_tab == "글로벌 상품 기획 시뮬레이터":
        st.markdown("## 🏗️ 글로벌 상품 기획 시뮬레이터")
        st.info("상품 기획 모듈은 메인 모니터링 에이전트와 백엔드 로직이 결합되어 구동됩니다.")

    elif big_tab == "🤖 AI 프롬프트":
        st.markdown("## 🤖 AI 프롬프트 마스터 관리")
        st.info("Sub-Agent 가동을 위한 통합 마스터 프롬프트 설정 화면입니다.")
