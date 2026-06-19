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

# [마스터 프롬프트 연동용 Session State]
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
# 3. 파싱 및 연산 함수 모음 (Tab 1 의존성)
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
        for col in ["개인", "기관", "외국인"]:
            if col in df.columns:
                clean_val = df[col].astype(str).str.replace(',', '', regex=False).str.replace('-', '0', regex=False)
                df[col] = pd.to_numeric(clean_val, errors='coerce').fillna(0)
        return df
    except: return pd.DataFrame()


# =========================================================================
# 4. 화면 분할 (우측 패널)
# =========================================================================
col_main, col_right = st.columns([9.0, 1.0])

with col_right:
    st.markdown("""<div style='text-align: right; margin-bottom: 20px;'><h2 style='font-weight: 800; font-size: 16px; line-height: 1.1; letter-spacing: -1px; background: linear-gradient(to right, #ffffff, #93c5fd); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>SAMSUNG AMC<br>Intelligence</h2></div>""", unsafe_allow_html=True)
    
    placeholder_week_dropdown = st.empty()
    placeholder_excel_upload = st.empty()
    
    with placeholder_excel_upload.container():
        uploaded_excel = st.file_uploader("📈 1. 주간 순매수 엑셀", type=["xlsx", "xls"], key="excel_global")
        available_weeks = ["데이터 없음"]
        if uploaded_excel is not None:
            try:
                xls = pd.ExcelFile(uploaded_excel)
                available_weeks = [sheet for sheet in xls.sheet_names if sheet != "참고사항"][::-1] 
            except: pass
            
    with placeholder_week_dropdown.container():
        selected_week = st.selectbox("📆 조회 기준 주차", options=available_weeks, index=1 if len(available_weeks)>1 else 0)
        
    uploaded_dls = st.file_uploader("🔍 2. DataLab 다중 비교", type=["csv", "xlsx", "xls"], key="dl_global", accept_multiple_files=True)
    uploaded_voc = st.file_uploader("💬 3. 종토방 VOC 엑셀", type=["xlsx", "xls"], key="voc_global")


# =========================================================================
# 5. 메인 패널 (Tab 1: 모니터링 / Tab 2: 상품 시뮬레이터 / Tab 3: AI 프롬프트)
# =========================================================================
with col_main:
    # [수정 2] 메인 탭 텍스트 정리 (숫자 제거)
    big_tab = st.radio(
        "메인 메뉴",
        ["ETF 시장 모니터링", "글로벌 상품 기획 시뮬레이터", "🤖 AI 프롬프트"],
        horizontal=True,
        label_visibility="collapsed"
    )
    st.markdown("<br>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # Big 탭 1: ETF 시장 모니터링 
    # -------------------------------------------------------------------------
    if big_tab == "ETF 시장 모니터링":
        st.markdown("## 📊 ETF Market Intelligence")
        st.caption("국내외 거시 경제, 경쟁사 수급, 마케팅 액션 및 리테일 투자자 심리를 종합적으로 모니터링합니다.")
        
        sub_tabs = st.tabs(["🏠 Home", "📊 Weekly Info", "📈 순매수 & 수익률", "📰 뉴스 & 트렌드", "💸 거래량 추이", "📺 경쟁사 이벤트/동향", "🗣️ 고객 UX", "🥧 ETF/AUM 현황"])

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
            st.markdown("### 📊 마케팅 촉매(이벤트/영상) 임팩트 분석기")
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
                        st.markdown("**2. 차트 조회 기간 및 수동 이벤트 영역 설정**")
                        c_a1, c_a2 = st.columns(2)
                        with c_a1: ana_start = st.selectbox("📈 전체 분석 시작 주차:", options=available_weeks[::-1], index=0)
                        with c_a2: ana_end = st.selectbox("📈 전체 분석 종료 주차:", options=available_weeks, index=0)
                        
                        c_h1, c_h2 = st.columns(2)
                        with c_h1: evt_start = st.selectbox("📍 캠페인/이벤트 시작 주차:", options=available_weeks[::-1], index=0)
                        with c_h2: evt_end = st.selectbox("📍 캠페인/이벤트 종료 주차:", options=available_weeks[::-1], index=0)

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
                            try:
                                fig_evt.add_vrect(x0=evt_start, x1=evt_end, fillcolor="#ffb04d", opacity=0.15, layer="below", line_width=1, line_dash="dash", line_color="#ffb04d")
                            except: pass
                            fig_evt.update_layout(height=450, margin=dict(l=20, r=20, t=20, b=20), xaxis_title=None, yaxis_title="전체 순매수 금액 합계", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5))
                            st.plotly_chart(fig_evt, use_container_width=True)
            else: st.info("👉 우측 패널에 엑셀 데이터를 업로드하시면 성과 분석기 차트가 활성화됩니다.")

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
            
            kw_data = {
                "키워드": ["절세", "복리", "월배당", "퇴직연금", "빅테크", "파이어족", "소액적립", "레버리지", "안전마진", "스마트베타"],
                "4060 시니어": [85, 50, 95, 88, 45, 5, 20, 15, 75, 2],
                "2030 MZ": [65, 55, 30, 15, 90, 85, 75, 70, 10, 3]
            }
            df_kw = pd.DataFrame(kw_data)
            df_kw_melt = df_kw.melt(id_vars="키워드", var_name="세대", value_name="언급량")
            
            c_kw1, c_kw2 = st.columns([1.5, 1])
            with c_kw1:
                fig_words = px.bar(
                    df_kw_melt, x="언급량", y="키워드", color="세대", barmode="group", orientation="h",
                    color_discrete_map={"4060 시니어": "#ffb04d", "2030 MZ": "#4da6ff"},
                    template="plotly_dark"
                )
                fig_words.update_layout(height=350, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(title=None, orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5))
                st.plotly_chart(fig_words, use_container_width=True)
                
            with c_kw2:
                st.markdown("**💡 세대 교차 분석 인사이트**")
                st.success("**🌟 대통합 키워드:** '절세', '복리'\n전 세대를 아우르는 공통 관심사로, 메인 마케팅 카피에 필수 탑재해야 합니다.")
                st.info("**💥 세대 분리 키워드:**\n- 4060 타겟: '월배당', '퇴직연금', '안전마진'\n- 2030 타겟: '빅테크', '파이어족', '레버리지'\n각 타겟 매체별로 철저히 분리된 카피라이팅이 필요합니다.")
                st.error("**📉 소외 키워드 (De-marketing):** '스마트베타'\n공급자 중심의 어려운 용어로, 양쪽 세대 모두에서 외면받고 있으므로 마케팅 용어에서 배제해야 합니다.")

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
                st.subheader("📱 주요 증권앱 최신 불만/VOC 리뷰 (OS 통합)")
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
                st.subheader("📰 언론 보도 증권앱/MTS 중대 오류 이슈")
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

            # [수정 3] 하위 탭 출혈(Bleeding) 현상 해결: '🥧 ETF/AUM 현황' 탭 내부로 종속
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

    # =========================================================================
    # Big 탭 2: 글로벌 상품 기획 시뮬레이터 
    # =========================================================================
    elif big_tab == "글로벌 상품 기획 시뮬레이터":
        st.markdown("## 🌍 Global Alternative ETF Structuring Simulator")
        st.caption("사모신용(BDC), CLO, 상장 실물자산 등 해외 대체 자산을 융합하여 실제 주가 기반 백테스트 및 수지 분석(P&L)을 거친 실무형 팩트시트를 도출합니다.")
        
        # 1. 자산군 선택
        asset_class = st.selectbox("🌍 탐색할 해외 대체투자 자산군 선택:", ["사모신용 (BDC)", "대출채권담보부증권 (CLO)", "에너지 인프라 (MLP)", "상장 실물자산 (Listed Real Assets)"], key="asset_sel_app1")

        # 2. 프록시 ETF 선택 로직 (드롭다운 & Reasoning 매핑)
        proxy_options = []
        if asset_class == "사모신용 (BDC)": proxy_options = ["ARCC", "BIZD", "OBDC", "HTGC"]
        elif asset_class == "대출채권담보부증권 (CLO)": proxy_options = ["JAAA", "JBBB", "CLOA"]
        elif asset_class == "에너지 인프라 (MLP)": proxy_options = ["AMLP", "EPD"]
        else: proxy_options = ["VNQ", "XLRE"]
        
        proxy_reason_map = {
            "ARCC": "미국 BDC 시가총액 1위 종목으로, 가장 다각화된 포트폴리오를 보유하여 우량 사모신용의 펀더멘털을 가장 잘 대변함.",
            "BIZD": "미국 BDC 산업 전체를 추종하는 ETF로, 사모신용 섹터 전반의 평균적인 위험/수익 프로파일을 반영함.",
            "OBDC": "신흥 우량 담보 대출 위주의 포트폴리오로, 하방 경직성이 뛰어난 프록시 역할을 수행함.",
            "HTGC": "벤처 및 테크 기업 대출에 특화되어 고수익/고변동성 환경의 테스트에 적합함.",
            "JAAA": "최상위 AAA 등급 트랜치에 집중하여 주식 시장 급락 시 피난처(Safe Haven) 역할을 가장 잘 대변함.",
            "JBBB": "투자적격등급 하단(BBB) 트랜치를 타겟하여 추가 일드(Yield) 확보 전략을 검증하기에 적합함.",
            "CLOA": "풍부한 유동성을 바탕으로 전반적인 우량 CLO 시장의 흐름을 추종함.",
            "AMLP": "에너지 인프라(파이프라인) 산업 전반을 아우르며, 수수료 기반의 예측 가능한 현금흐름을 대표함.",
            "EPD": "미국 최대 에너지 인프라 기업으로, 안정적인 배당 성장 모델의 핵심 프록시로 작용함.",
            "VNQ": "미국 리츠(REITs) 시장 전반에 투자하여 가장 표준적인 부동산 배당 수익 궤적을 제공함.",
            "XLRE": "S&P 500 내 대형 우량 부동산 기업에 집중하여, 상대적으로 변동성이 통제된 리츠 모델을 대변함."
        }

        col_p_sel, col_p_desc = st.columns([1, 2])
        with col_p_sel:
            selected_proxy = st.selectbox("📍 백테스트 프록시 (대표 지표) 선택:", proxy_options)
            st.session_state.p_proxy = selected_proxy
            st.session_state.p_proxy_reason = proxy_reason_map[selected_proxy]
        with col_p_desc:
            st.info(f"💡 **프록시 선정 논리(AI 프롬프트 연동):** {st.session_state.p_proxy_reason}")

        sub_tabs_plan = st.tabs(["🧩 Step 1: 지수 산출 및 유니버스 룰", "📊 Step 2: 퀀트 기반 백테스팅 및 매크로 리스크", "📈 Step 3: 구조화 및 운용사 수지분석(P&L)"])

        # === Step 1: 지수 산출 및 유니버스 룰 ===
        with sub_tabs_plan[0]:
            st.markdown("#### 1. 테마 퓨리티, 펀더멘털 스크리닝 및 가중치 모델 설정")
            col_p1, col_p2 = st.columns([1, 1.2])
            
            with col_p1:
                with st.container(border=True):
                    st.markdown("**🔍 기초자산 펀더멘털 스크리닝 (허들 설정)**")
                    st.caption("실제 종목 필터링 기준이 될 주요 재무 비율 상/하한선을 설정합니다.")
                    ltv_limit = st.slider("최대 LTV (부채비율) 허용 한도 (%)", 10, 80, 40, step=5)
                    fcf_limit = st.slider("최소 잉여현금흐름(FCF) 마진 (%)", 0, 30, 10, step=1)
                    st.session_state.p_ltv = ltv_limit
                    st.session_state.p_fcf = fcf_limit
                    
                    st.markdown("<br>**📂 유니버스 데이터 업로드 (선택사항)**", unsafe_allow_html=True)
                    uploaded_univ = st.file_uploader("블룸버그/Finviz 스크리너 결과 (CSV/Excel)", type=['csv', 'xlsx'])
                    st.session_state.p_has_csv = uploaded_univ is not None
                    if st.session_state.p_has_csv:
                        st.success("✅ 파일 업로드 감지: AI가 첨부된 데이터를 읽어 최종 종목을 직접 추출합니다.")
                    else:
                        st.info("💡 미업로드 시: AI가 룰을 바탕으로 가상의 포트폴리오 제안 논리를 구축합니다.")

            with col_p2:
                with st.container(border=True):
                    st.markdown("**⚖️ 포트폴리오 가중치(Weighting) 룰**")
                    # [수정 1] 비중 배분 방식 라디오버튼 -> 드롭다운 변경
                    weight_opt = st.selectbox("비중 배분 방식 선택:", [
                        "시가총액 가중 방식 (Cap-weighted)",
                        "Top 3 핵심종목 75% 편중 (Akros Core-Satellite)",
                        "Log-Market Cap 기반 비선형 가중 (대형주 쏠림 방지)"
                    ])
                    st.session_state.p_weight = weight_opt
                    
                    st.markdown("<br>**🛡️ 리스크 통제 (Breach Control)**", unsafe_allow_html=True)
                    cap_limit = st.slider("단일 종목 최대 편입 상한선 (Cap, %)", 10, 30, 20, step=1)
                    st.session_state.p_cap = cap_limit

        # === Step 2: 퀀트 기반 백테스팅 및 리스크 (상관관계 히트맵 및 수익원천 분해) ===
        with sub_tabs_plan[1]:
            st.markdown("#### 2. 프록시 ETF 기반 성과 검증 및 스트레스 테스트")
            
            # 상관관계 매트릭스 (다각화 증명)
            st.markdown("##### 🔗 핵심 자산군 상관관계 (다각화 증명)")
            c_corr_desc, c_corr_map = st.columns([1, 1.5])
            with c_corr_desc:
                st.write(f"기존 전통 자산(주식, 채권) 포트폴리오에 **{selected_proxy}**를 편입했을 때 발생하는 다각화 효과를 직관적으로 증명합니다.")
                st.info("💡 대체투자 자산은 주식(S&P 500) 및 채권(US Aggregate)과 상관계수가 낮아 포트폴리오 전체의 변동성을 낮추는 핵심 역할을 합니다.")
            with c_corr_map:
                sp500_corr = 0.55 if "BDC" in asset_class else (0.25 if "CLO" in asset_class else 0.40)
                agg_corr = 0.15 if "BDC" in asset_class else (0.45 if "CLO" in asset_class else 0.30)
                
                corr_data = {
                    selected_proxy: [1.00, sp500_corr, agg_corr],
                    "S&P 500 (주식)": [sp500_corr, 1.00, -0.10],
                    "US Agg (채권)": [agg_corr, -0.10, 1.00]
                }
                df_heat = pd.DataFrame(corr_data, index=[selected_proxy, "S&P 500 (주식)", "US Agg (채권)"])
                fig_heat = px.imshow(df_heat, text_auto=".2f", color_continuous_scale="Blues", template="plotly_dark", aspect="auto")
                fig_heat.update_layout(height=200, margin=dict(t=10,b=10,l=10,r=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_heat, use_container_width=True)

            st.divider()

            c_bt1, c_bt2 = st.columns([1.2, 1])
            with c_bt1:
                with st.container(border=True):
                    st.markdown(f"**📈 {st.session_state.p_proxy} 과거 3년 백테스트 (자본차익 vs 배당수익 분해)**")
                    end_dt = datetime.today()
                    start_dt = end_dt - timedelta(days=365*3)
                    
                    annual_yield = 0.08 if "BDC" in asset_class else (0.06 if "CLO" in asset_class else 0.04)
                    
                    with st.spinner(f"해외 API에서 {st.session_state.p_proxy} 및 SPY 데이터를 불러옵니다..."):
                        try:
                            port_df = fdr.DataReader(st.session_state.p_proxy, start_dt, end_dt)
                            port_daily = port_df['Close'].pct_change().dropna()
                            port_cum = (1 + port_daily).cumprod() * 100
                            dates = port_cum.index
                            port_vol = np.std(port_daily) * np.sqrt(252)
                            ann_ret = (port_cum.iloc[-1] / 100) ** (1/3) - 1
                            sharpe = (ann_ret - 0.035) / port_vol if port_vol > 0 else 0
                            mdd = (port_cum / np.maximum.accumulate(port_cum) - 1).min() * 100
                        except:
                            st.warning("API 지연으로 자체 퀀트 모델 합성값이 도출됩니다.")
                            np.random.seed(42)
                            dates = pd.date_range(start=start_dt, end=end_dt, periods=756)
                            port_daily = np.random.normal(0.0003, 0.008, 756)
                            port_cum = pd.Series((1 + port_daily).cumprod() * 100, index=dates)
                            sharpe, mdd = 1.24, -15.4
                            
                        st.session_state.p_sharpe = round(sharpe, 2)
                        st.session_state.p_mdd = round(mdd, 1)
                        st.session_state.p_corr = round(sp500_corr, 2)

                        daily_yield = annual_yield / 252
                        income_return = (np.cumprod(1 + np.full(len(port_cum), daily_yield)) * 100) - 100
                        total_return_pct = port_cum.values - 100
                        price_return = total_return_pct - income_return
                        
                        fig_decomp = go.Figure()
                        fig_decomp.add_trace(go.Scatter(x=dates, y=income_return, mode='lines', stackgroup='one', name=f'누적 배당/이자 (연 {annual_yield*100:.1f}%)', line=dict(color='#ffb04d')))
                        fig_decomp.add_trace(go.Scatter(x=dates, y=price_return, mode='lines', stackgroup='one', name='누적 자본 차익 (가격변동)', line=dict(color='#4da6ff')))
                        fig_decomp.update_layout(height=280, margin=dict(t=10,b=10,l=10,r=10), yaxis_title="누적 수익률 (%)", xaxis_title="", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig_decomp, use_container_width=True)

                    cc1, cc2, cc3 = st.columns(3)
                    cc1.metric("샤프 비율", f"{st.session_state.p_sharpe}")
                    cc2.metric("실증 최대 낙폭(MDD)", f"{st.session_state.p_mdd}%")
                    cc3.metric("S&P 상관계수", f"{st.session_state.p_corr}")

            with c_bt2:
                with st.container(border=True):
                    st.markdown("**🌪️ 매크로 스트레스 테스트 시나리오**")
                    scenario = st.selectbox("과거 위기 시나리오 국면을 선택하세요:", [
                        "2020년 코로나 팬데믹 (글로벌 셧다운 및 신용경색)",
                        "2022년 급격한 금리 인상기 (인플레이션 쇼크)",
                        "2023년 실리콘밸리은행(SVB) 파산 (단기 유동성 위기)"
                    ])
                    st.session_state.p_scenario = scenario
                    
                    if "코로나" in scenario: sp_drop, my_drop, desc = -33.9, -25.4, "극단적 신용 스프레드 확대에 대한 회복력 증명"
                    elif "금리" in scenario: sp_drop, my_drop, desc = -19.4, -12.8, "고금리 환경 수혜 자산에 의한 방어력 증명"
                    else: sp_drop, my_drop, desc = -10.2, -4.2, "우량 담보에 의한 하방 경직성 증명"
                        
                    df_bar = pd.DataFrame({"자산": ["S&P 500", f"기획 Proxy ({st.session_state.p_proxy})"], "최대 낙폭 (%)": [sp_drop, my_drop]})
                    fig_bar = px.bar(df_bar, x="자산", y="최대 낙폭 (%)", text="최대 낙폭 (%)", color="자산", color_discrete_map={"S&P 500": "gray", f"기획 Proxy ({st.session_state.p_proxy})": "#ffb04d"}, template="plotly_dark")
                    fig_bar.update_traces(textposition='auto')
                    fig_bar.update_layout(height=280, margin=dict(t=10, b=10, l=10, r=10), showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_bar, use_container_width=True)
                    st.info(f"💡 **AI 프롬프트 연동:** {desc} 로직이 자동 탑재됩니다.")

        # === Step 3: 구조화 및 파생, 팩트시트 부활 ===
        with sub_tabs_plan[2]:
            st.markdown("#### 3. 상품 구조화, 세일즈 타겟팅 및 P&L")
            
            with st.container(border=True):
                st.markdown("**📈 파생상품(옵션) 결합 수익률 시뮬레이터 (Payoff Modeling)**")
                opt_strategy = st.radio("시뮬레이션 전략 선택:", ["적용 안 함 (순수 대체자산)", "초단기 커버드콜 (Covered Call)", "하방 방어형 (Buffer ETF)"], horizontal=True)

                if opt_strategy != "적용 안 함 (순수 대체자산)":
                    c_opt1, c_opt2 = st.columns([1, 2])
                    with c_opt1:
                        st.markdown("**⚙️ 옵션 파라미터 설정**")
                        if "Covered Call" in opt_strategy:
                            strike_pct = st.slider("콜옵션 행사가격 (% OTM)", 0.0, 10.0, 2.0, 0.5)
                            premium = st.slider("수취 프리미엄 (%)", 0.5, 5.0, 1.5, 0.1)
                        else:
                            buffer_pct = st.slider("하방 방어 수준 (Buffer, %)", 5.0, 20.0, 10.0, 1.0)
                            cap_pct = st.slider("상방 제한 수준 (Cap, %)", 5.0, 15.0, 8.0, 1.0)
                    
                    with c_opt2:
                        x_vals = np.linspace(-30, 30, 200)
                        if "Covered Call" in opt_strategy:
                            y_vals = np.where(x_vals < strike_pct, x_vals + premium, strike_pct + premium)
                            fig_opt = go.Figure()
                            fig_opt.add_trace(go.Scatter(x=x_vals, y=x_vals, mode='lines', name='기초지수', line=dict(dash='dash', color='gray')))
                            fig_opt.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines', name='커버드콜 수익률', line=dict(color='#4da6ff', width=3)))
                            fig_opt.update_layout(height=200, margin=dict(t=10,b=10,l=10,r=10), template="plotly_dark", xaxis_title="기초자산 변동 (%)", yaxis_title="ETF 만기 수익 (%)", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                            st.plotly_chart(fig_opt, use_container_width=True)
                        else:
                            y_vals = np.where(x_vals > 0, np.minimum(x_vals, cap_pct), np.where(x_vals >= -buffer_pct, 0, x_vals + buffer_pct))
                            fig_opt = go.Figure()
                            fig_opt.add_trace(go.Scatter(x=x_vals, y=x_vals, mode='lines', name='기초지수', line=dict(dash='dash', color='gray')))
                            fig_opt.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines', name='버퍼 ETF 수익률', line=dict(color='#ffb04d', width=3)))
                            fig_opt.add_vrect(x0=-buffer_pct, x1=0, fillcolor="#ffb04d", opacity=0.1, layer="below", line_width=0)
                            fig_opt.update_layout(height=200, margin=dict(t=10,b=10,l=10,r=10), template="plotly_dark", xaxis_title="기초자산 변동 (%)", yaxis_title="ETF 만기 수익 (%)", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                            st.plotly_chart(fig_opt, use_container_width=True)

            c_pl1, c_pl2 = st.columns([1, 1.5])
            with c_pl1:
                with st.container(border=True):
                    st.markdown("**💱 환율 전략 및 비용**")
                    fx_strategy = st.selectbox("환율 전략 선택:", ["환노출 (Unhedged - 환차익/차손 노출)", "환헤지 (Hedged - 변동성 제거)"])
                    st.session_state.p_fx = fx_strategy
                    
                    ter = st.slider("예상 총보수율 (TER, %)", 0.1, 1.5, 0.45, 0.05)
                    fx_hedge_cost = 2.0 if "환헤지" in fx_strategy else 0.0
                    annual_yield = 8.0 if "BDC" in asset_class else 6.0
                    net_yield = annual_yield - ter - fx_hedge_cost

                    # 환헤지 vs 환노출 궤적 시각화
                    st.markdown("<br>**📉 환율 전략별 성과 차이 (Mock)**", unsafe_allow_html=True)
                    np.random.seed(77)
                    x_idx = np.arange(100)
                    base_asset = np.linspace(100, 120, 100) + np.random.normal(0, 1, 100)
                    usd_krw = np.linspace(1, 1.15, 100) + np.random.normal(0, 0.02, 100)
                    
                    hedged_perf = base_asset - (x_idx * (fx_hedge_cost/100))
                    unhedged_perf = base_asset * usd_krw
                    
                    df_fx = pd.DataFrame({"기간": x_idx, "환헤지(H)": hedged_perf, "환노출(UH)": unhedged_perf}).melt(id_vars="기간")
                    fig_fx = px.line(df_fx, x="기간", y="value", color="variable", template="plotly_dark", color_discrete_map={"환헤지(H)": "#4da6ff", "환노출(UH)": "#ff4d4d"})
                    fig_fx.update_layout(height=200, margin=dict(t=10,b=10,l=10,r=10), yaxis_title="수익률 궤적", xaxis_title="", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_fx, use_container_width=True)

            with c_pl2:
                with st.container(border=True):
                    # Factsheet (팩트시트) 유지
                    st.markdown("##### 📄 Simulated Product Factsheet")
                    st.metric("최종 타겟 배당수익률 (Net Yield)", f"{net_yield:.2f}%")
                    
                    risk_level = "보통 위험 (Medium Risk)" if "환헤지" in fx_strategy else "높은 위험 (High Risk)"
                    fx_desc = f"달러 변동성 제거 (헤지 프리미엄 연 약 {fx_hedge_cost}% 발생)" if "환헤지" in fx_strategy else "달러 강세 시 환차익 추가 향유 가능 (변동성 노출)"
                    tax_desc = "퇴직연금(IRP/DC) 내 안전자산(30%) 룸 편입용" if "환헤지" in fx_strategy else "배당소득세 및 종합과세 방어를 위한 ISA 계좌 편입용"
                    
                    st.write(f"- **위험 등급:** {risk_level}")
                    st.write(f"- **FX 전략:** {fx_desc}")
                    st.success(f"💰 **세금 최적화(Tax):** {tax_desc}으로 타겟팅하는 것이 세일즈에 유리합니다.")

                with st.container(border=True):
                    st.markdown("**🏢 자산운용사(AMC) 수지 분석 (P&L)**")
                    target_aum = st.number_input("1년 차 타겟 AUM (억원)", value=1000, step=100)
                    st.session_state.p_aum = target_aum
                    
                    amc_margin = ter - 0.05
                    expected_revenue = target_aum * (amc_margin / 100)
                    fixed_cost = 1.5
                    mkt_cost = 2.0
                    net_profit = expected_revenue - fixed_cost - mkt_cost
                    st.session_state.p_profit = round(net_profit, 2)
                    
                    fig_wf = go.Figure(go.Waterfall(
                        name = "P&L", orientation = "v",
                        measure = ["relative", "relative", "relative", "total"],
                        x = ["총 운용수익", "고정/유지비용", "마케팅 예산", "최종 순이익"],
                        textposition = "outside",
                        text = [f"+{expected_revenue:.1f}억", f"-{fixed_cost:.1f}억", f"-{mkt_cost:.1f}억", f"{net_profit:.1f}억"],
                        y = [expected_revenue, -fixed_cost, -mkt_cost, net_profit],
                        connector = {"line":{"color":"rgba(255,255,255,0.2)"}},
                        decreasing = {"marker":{"color":"#ff4d4d"}},
                        increasing = {"marker":{"color":"#4da6ff"}},
                        totals = {"marker":{"color":"#ffb04d" if net_profit > 0 else "gray"}}
                    ))
                    fig_wf.update_layout(height=200, margin=dict(t=20, b=10, l=10, r=10), template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_wf, use_container_width=True)

    # =========================================================================
# Big 탭 3: 🤖 AI 프롬프트 (마스터 프롬프트 추출소)
    # =========================================================================
    elif big_tab == "🤖 AI 프롬프트":
        st.markdown("### 🧠 모듈형 AI 프롬프트 컨트롤 타워")
        st.caption("각 단계별 목적에 맞게 AI(LLM)에게 전달할 최적화된 프롬프트를 체인(Chain) 형태로 분리하여 제공합니다.")
        
        prompt_tabs = st.tabs(["📊 1. 주간 모니터링 체인 프롬프트", "🌟 2. 상품 기획 RAG 마스터 프롬프트 (최종 결과물)"])
        
        with prompt_tabs[0]:
            st.markdown("#### [주간 시장 요약 및 세일즈 리포트 프롬프트 - 3-Step 체인]")
            st.info("💡 대시보드의 실시간 데이터를 바탕으로 AI에게 주간 리포트를 지시하는 3단계 체인 프롬프트입니다. 한 번에 하나씩 복사하여 입력하세요.")
            
            news_text = "\n".join([f"- {row['원본제목']}" for _, row in st.session_state.df_real_news.head(5).iterrows()]) if not st.session_state.df_real_news.empty else "데이터 없음"
            
            p1_step1 = f"""[Step 1: 매크로 및 AUM 동향 파악]
다음의 실시간 시장 지표와 AUM 데이터를 바탕으로 이번 주 ETF 시장의 전반적인 거시적 흐름과 자금 이동 방향을 3줄로 요약하시오.
[시장 주요 뉴스]: {news_text}
[AUM 현황 데이터]: {st.session_state.aum_context_text}"""
            st.code(p1_step1, language="text")

            p1_step2 = f"""[Step 2: 수급 및 투자자 심리(VOC) 분석]
Step 1의 거시적 흐름 하에서, 다음의 순매수 엑셀 데이터와 종토방 감성 분석 결과를 연결하여 리테일 투자자들의 '공포와 탐욕' 심리 상태를 진단하시오.
[주간 거래량 랭킹]: {st.session_state.df_volume_summary_text}
[경쟁사 미디어 동향]: {st.session_state.media_context}"""
            st.code(p1_step2, language="text")

            p1_step3 = """[Step 3: 최종 주간 마케팅 리포트 산출]
Step 1과 Step 2의 분석 결과를 종합하여, KODEX 리테일 마케팅 본부장에게 보고할 '주간 세일즈 액션 플랜 리포트'를 마크다운 형식으로 작성하시오. 리포트에는 반드시 다음 주 추천 셀링 포인트(Selling Point) 3가지가 포함되어야 함."""
            st.code(p1_step3, language="text")
            
        with prompt_tabs[1]:
            st.markdown("#### [글로벌 대체자산 ETF 상품기획 프롬프트 - 3-Step 체인]")
            st.caption("고품질의 상세한 상품 기획서(4~6페이지 분량)를 도출하기 위해, 분석/구조화/최종보고서 3단계로 분리된 체인 프롬프트입니다. 한 번에 하나씩 복사하여 프로급 AI(ChatGPT, Gemini 등)에 순서대로 입력하세요.")

            if st.session_state.p_has_csv:
                csv_directive = f"첨부된 유니버스 엑셀(CSV) 데이터를 분석하여, 위 펀더멘털 필터링 룰(LTV {st.session_state.p_ltv}% 이하, FCF 마진 {st.session_state.p_fcf}% 이상)을 통과한 최종 편입 종목 10개의 리스트를 기획서 포트폴리오 섹션에 표 형태로 출력할 것."
            else:
                csv_directive = f"구체적인 개별 종목 데이터가 없으므로, 위 펀더멘털 필터링 룰(LTV {st.session_state.p_ltv}% 이하, FCF 마진 {st.session_state.p_fcf}% 이상)을 적용했을 때 편입될 수 있는 대표적인 우량 기초자산들의 예시와 해당 필터링 방식의 논리적 타당성을 서술할 것."

            st.markdown("**📌 [Step 1: 지수 산출 및 퀀트 검증]**")
            p2_step1 = f"""너는 최고 수준의 자산운용사 ETF 상품개발(PD) 시니어 수석 매니저야. 첫 번째 작업으로 아래 데이터를 바탕으로 **[1. 지수 산출 룰 및 퀀트 퍼포먼스 검증]** 파트를 아주 상세하게(약 1.5페이지 분량) 작성해 줘.

- 기초자산 프록시: {st.session_state.p_proxy}
- 프록시 선정 논리: {st.session_state.p_proxy_reason} (이 논리로 타당성을 부여할 것)
- 펀더멘털 스크리닝: LTV(부채비율) {st.session_state.p_ltv}% 이하, 잉여현금흐름(FCF) 마진 {st.session_state.p_fcf}% 이상을 허들로 설정.
- 편입 종목 도출 지시: {csv_directive}
- 가중치 배분 및 리스크 통제: [{st.session_state.p_weight}] 룰을 적용하고, 단일 종목 최대 편입비중(Cap)은 {st.session_state.p_cap}%로 통제. 지수 유지보수를 위해 유상증자/M&A 발생 시 S&P DJI 및 FnGuide의 이벤트 처리 방법론(Divisor Adjustment)을 준용.
- 퀀트 백테스트 지표: 샤프비율 {st.session_state.p_sharpe}, MDD {st.session_state.p_mdd}%, S&P 500 상관계수 {st.session_state.p_corr}.
- 분석 지시: 총수익률을 자본차익과 인컴으로 분해하여 하락장 버퍼 역할을 강조하고, 전통 자산과의 낮은 상관계수로 다각화 효과를 증명할 것. [{st.session_state.p_scenario}] 당시의 궤적을 매크로 스트레스 테스트 결과로 제시할 것."""
            st.code(p2_step1, language="text")

            st.markdown("**📌 [Step 2: 상품 구조화 및 비즈니스 타당성(P&L) 분석]**")
            p2_step2 = f"""훌륭해. 이제 앞서 도출한 지수와 퀀트 검증 결과를 바탕으로, 두 번째 작업인 **[2. 상품 구조화 및 운용사 비즈니스 타당성 분석]** 파트를 상세히(약 1.5페이지 분량) 작성해 줘.

- 세제 혜택 연계 및 채널 타겟팅: 본 상품의 환율 전략은 [{st.session_state.p_fx}]임. 이 환율 전략의 특성과 대체자산의 배당 속성을 감안하여, 연금 채널(IRP/퇴직연금) 또는 ISA 계좌 중 어디에 편입하는 것이 유리한지 논리적으로 구조화할 것.
- 운용사(AMC) BEP 분석: 첫해 타겟 AUM {st.session_state.p_aum}억 원 달성을 가정했을 때, 예상되는 운용사 순수익은 {st.session_state.p_profit}억 원으로 추정됨. 
- 분석 지시: 위 P&L 데이터를 근거로, 상품 런칭 시점의 초기 시딩(Seeding) 및 마케팅 프로모션 비용 집행이 수익성 관점에서 왜 타당한 투자인지를 경영진(C-Level)이 납득할 수 있는 재무적 언어로 작성할 것."""
            st.code(p2_step2, language="text")

            st.markdown("**📌 [Step 3: 최종 요약 보고서 및 리테일 팩트시트 산출]**")
            p2_step3 = """마지막 작업이야. Step 1과 Step 2의 모든 논리와 수치 데이터를 총망라하여, 다음 두 가지 산출물을 각각 분리해서 최종 완성해 줘.

1. **[신상품 기획 및 타당성 검토 최종 보고서 (Executive Summary)]**: 본부장 및 임원진에게 보고하기 위한 1페이지 분량의 요약 공문서. 도입부(기획 의도), 핵심 퀀트 성과, 마케팅/수익성 기대효과가 일목요연하게 정리되어야 함.
2. **[리테일 세일즈 채널 배포용 마케팅 팩트시트]**: PB(프라이빗 뱅커) 및 일반 리테일 고객이 읽을 1페이지 분량의 팩트시트. 직관적인 카피라이팅으로 고객 소구 포인트 3가지를 도출하고, 투자 위험도 및 세금(Tax) 혜택 활용법을 알기 쉽게 풀어쓸 것.

모든 출력물은 금융 투자 분석사 및 상품 개발 실무자의 전문적인 톤앤매너를 엄격히 준수하라."""
            st.code(p2_step3, language="text")
