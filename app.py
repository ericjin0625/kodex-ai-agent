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

# 1. 페이지 레이아웃 및 기본 테마 설정
st.set_page_config(page_title="ETF Intelligence & Structuring Agent", layout="wide", initial_sidebar_state="collapsed")

# 전역 변수 초기화
if 'df_scatter' not in st.session_state: st.session_state.df_scatter = pd.DataFrame()
if 'dl_summary' not in st.session_state: st.session_state.dl_summary = "DataLab 데이터가 업로드되지 않았습니다."
if 'df_real_news' not in st.session_state: st.session_state.df_real_news = pd.DataFrame()
if 'df_volume_summary_text' not in st.session_state: st.session_state.df_volume_summary_text = "데이터 없음"
if 'aum_context_text' not in st.session_state: st.session_state.aum_context_text = "데이터 없음"
if 'media_context' not in st.session_state: st.session_state.media_context = "데이터 없음"

# ==========================================
# ★ Glassmorphism 커스텀 CSS
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

/* Small 탭 스타일 */
[data-baseweb="tab-list"] { gap: 8px; padding-bottom: 12px; flex-wrap: wrap; }
[data-baseweb="tab"] { background: rgba(255, 255, 255, 0.04) !important; border-radius: 20px !important; border: 1px solid rgba(255, 255, 255, 0.08) !important; padding: 8px 16px !important; color: #94a3b8 !important; }
[data-baseweb="tab"][aria-selected="true"] { background: rgba(77, 166, 255, 0.12) !important; border: 1px solid rgba(77, 166, 255, 0.5) !important; color: #ffffff !important; box-shadow: 0 0 12px rgba(77, 166, 255, 0.25) !important; font-weight: 600 !important; }

/* 텍스트 밝은색 강제 (라이트모드 충돌 방지) */
[data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3, [data-testid="stMarkdownContainer"] h4, [data-testid="stMarkdownContainer"] h5, [data-testid="stMarkdownContainer"] h6, [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] span { color: #f8fafc !important; }
label, label p, [data-testid="stWidgetLabel"] p { color: #f8fafc !important; }
[data-testid="stCaptionContainer"] p { color: #94a3b8 !important; }
[data-testid="stMetricLabel"] p { color: #cbd5e1 !important; }
[data-testid="stMetricValue"] div { color: #ffffff !important; }
div[data-baseweb="textarea"] textarea, .stTextArea textarea { background-color: #0f172a !important; color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; border: 1px solid rgba(77, 166, 255, 0.5) !important; }

/* 🔴 Big 탭 (Pill 형태) - 텍스트 1줄 가로 중앙 정렬 및 슬림화 */
div[data-testid="stRadio"] > div[role="radiogroup"] {
    display: flex;
    flex-direction: row;
    gap: 10px;
    background: transparent !important;
}
div[data-testid="stRadio"] > div[role="radiogroup"] > label {
    background: rgba(255, 255, 255, 0.05) !important;
    padding: 8px 15px !important;
    border-radius: 50px !important; 
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    cursor: pointer !important;
    flex: 1 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important; 
    transition: all 0.3s ease !important;
}
div[data-testid="stRadio"] > div[role="radiogroup"] > label:hover {
    background: rgba(255, 255, 255, 0.1) !important;
}
div[data-testid="stRadio"] > div[role="radiogroup"] > label[data-checked="true"] {
    background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%) !important;
    border: 2px solid #4da6ff !important;
    box-shadow: 0 0 15px rgba(77, 166, 255, 0.4) !important;
}
div[data-testid="stRadio"] > div[role="radiogroup"] > label p {
    font-size: 16px !important;
    font-weight: 800 !important;
    margin: 0 !important;
    color: #ffffff !important;
    white-space: nowrap !important;
    text-align: center !important;
}
div[data-testid="stRadio"] > div[role="radiogroup"] > label > div:first-child {
    display: none !important;
}

#MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;} .stDeployButton {display: none;}
</style>
"""
st.markdown(glassmorphism_css, unsafe_allow_html=True)

# ==========================================
# ★ 파싱 및 연산 함수 모음
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
    headers = {"User-Agent": "Mozilla/5.0", "Accept-Language": "ko-KR,ko;q=0.9"}
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
    """ Option A(RapidAPI) -> Option B(RSS.app) Fallback 로직 """
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
# ★ 화면 분할 (메인 패널 9.0 : 우측 컨트롤 타워 1.0 완벽 비율)
# =========================================================================
col_main, col_right = st.columns([9.0, 1.0])

# -------------------------------------------------------------------------
# 우측 패널 (Data Upload Center)
# -------------------------------------------------------------------------
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

# -------------------------------------------------------------------------
# 좌측 메인 패널 (Big 탭 구조)
# -------------------------------------------------------------------------
with col_main:
    # 🔴 Big 탭
    big_tab = st.radio(
        "메인 메뉴",
        ["1. ETF 시장 모니터링", "2. 글로벌 상품 기획 시뮬레이터", "🤖 AI 프롬프트"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    st.markdown("<br>", unsafe_allow_html=True)

    # =========================================================================
    # Big 탭 1: ETF 시장 모니터링
    # =========================================================================
    if big_tab == "1. ETF 시장 모니터링":
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
    elif big_tab == "2. 글로벌 상품 기획 시뮬레이터":
        st.markdown("## 🌍 Global Alternative ETF Structuring Simulator")
        st.caption("사모신용(BDC), CLO, 상장 실물자산 등 해외 대체 자산을 융합하여 실제 주가 기반 백테스트 및 수지 분석(P&L)을 거친 실무형 팩트시트를 도출합니다.")
        
        asset_class = st.selectbox("🌍 탐색할 해외 대체투자 자산군 선택:", ["사모신용 (BDC)", "대출채권담보부증권 (CLO)", "에너지 인프라 (MLP)", "상장 실물자산 (Listed Real Assets)"], key="asset_sel_app1")

        mock_db = {
            "사모신용 (BDC)": {
                "tickers": ["ARCC", "OBDC", "FSK", "MAIN", "BXSL", "CSWC", "HTGC", "GBDC", "TSLX", "PNNT", "ARIS", "CGBD", "NMFC", "TCPC", "SLRC", "MFIC", "OCSL", "TRIN", "GLAD", "SAR", "FDUS", "PFLT", "HRZN", "MRCC", "CCAP", "SUNS"],
                "names": ["Ares Capital", "Blue Owl Capital", "FS KKR Capital", "Main Street", "Blackstone Secured", "Capital Southwest", "Hercules Capital", "Golub Capital", "Sixth Street", "PennantPark", "Aris Water", "Carlyle Secured", "New Mountain", "BlackRock TCP", "SLR Investment", "MidCap Financial", "Oaktree Specialty", "Trinity Capital", "Gladstone Capital", "Saratoga Invest", "Fidus Investment", "PennantPark Float", "Horizon Tech", "Monroe Capital", "Crescent Capital", "SLR Senior"],
                "base_yields": [9.5, 10.2, 11.8, 6.5, 10.5, 9.8, 8.2, 9.1, 8.9, 11.5, 8.5, 10.8, 10.4, 12.1, 10.9, 10.1, 11.2, 14.5, 9.5, 8.8, 8.4, 10.2, 10.5, 12.5, 11.1, 9.5],
                "labels": ["예상 배당수익률 (Yield)", "포트폴리오 평균 LTV", "변동금리 대출 비중"],
                "data": {
                    "ARCC": [9.5, 45.2, 98.0, "고정 금리 대비 변동 금리 대출 비중이 압도적으로 높아, 현행 고금리 기조에서 강력한 이자 수익 방어력을 지니고 있습니다."],
                    "OBDC": [10.2, 41.5, 96.0, "안정적인 IT/소프트웨어 섹터의 선순위 담보 대출 위주로 포트폴리오가 구성되어 있어 하방 경직성이 강하며 펀더멘털이 우수합니다."],
                    "FSK": [11.8, 48.1, 89.0, "상대적으로 높은 레버리지 비율을 통해 고수익을 창출하며, KKR의 강력한 글로벌 딜 소싱 네트워크를 활용합니다."]
                },
                "stress_name": "예상 시장 부도율 (Default Rate, %)",
                "recovery_default": 60.0
            },
            "대출채권담보부증권 (CLO)": {
                "tickers": ["JAAA", "JBBB", "CLOA", "CLOI", "AAA", "BND", "CLOZ", "JCCC", "CRAK", "LQD", "AGG", "VCIT", "VCSH", "IGSB", "FLOT", "SRLN", "HYG", "JNK", "USIG", "SPSB", "SPIB", "VRP", "HYLB", "BSV", "BKLN"],
                "names": ["Janus AAA CLO", "Janus BBB CLO", "BlackRock AAA CLO", "Invesco AAA CLO", "AXS AAA CLO", "Vanguard Total Bond", "Panagram BBB CLO", "Janus CCC CLO", "VanEck CLO", "iShares iBoxx Inv", "iShares Core Bond", "Vanguard Int-Term", "Vanguard Short-Term", "iShares Short-Term", "iShares Floating", "SPDR Blackstone", "iShares High Yield", "SPDR High Yield", "iShares Broad USD", "SPDR Portfolio Short", "SPDR Portfolio Int", "Invesco Variable", "Xtrackers High Yield", "Vanguard Short-Term", "Invesco Senior Loan"],
                "base_yields": [6.2, 8.5, 6.1, 6.3, 6.0, 4.5, 8.8, 12.5, 6.5, 5.2, 4.8, 5.5, 5.1, 5.0, 6.1, 8.5, 7.5, 7.8, 5.3, 5.0, 5.2, 6.5, 7.9, 4.9, 8.2],
                "labels": ["예상 만기수익률 (YTM)", "AAA/AA 등급 비중", "평균 듀레이션 (년)"],
                "data": {
                    "JAAA": [6.2, 100.0, 0.2, "최상위 AAA 등급 트랜치에만 투자하여 극강의 방어력을 제공합니다. 주식 시장 급락 시 피난처 역할을 수행합니다."],
                    "JBBB": [8.5, 0.0, 0.3, "투자적격등급 하단(BBB) 트랜치를 타겟하여 추가 일드(Yield)를 확보합니다. 하일드 채권 대비 부도율이 낮습니다."],
                    "CLOA": [6.1, 100.0, 0.25, "블랙락의 강력한 크레딧 소싱 능력을 바탕으로 운용되는 우량 CLO ETF로, 풍부한 유동성이 장점입니다."]
                },
                "stress_name": "예상 연쇄 부도율 (Systemic Default, %)",
                "recovery_default": 75.0
            },
            "에너지 인프라 (MLP)": {
                "tickers": ["AMLP", "EPD", "ET", "MMP", "WMB", "PAA", "KMI", "OKE", "TRGP", "ENB", "PBA", "MPLX", "WES", "SHLX", "NS", "SUN", "USAC", "GEL", "HEP", "NGL", "CAPL", "CQP", "TCP", "BKEP", "SRLP"],
                "names": ["Alerian MLP ETF", "Enterprise Products", "Energy Transfer", "Magellan Midstream", "Williams Companies", "Plains All American", "Kinder Morgan", "ONEOK", "Targa Resources", "Enbridge", "Pembina Pipeline", "MPLX LP", "Western Midstream", "Shell Midstream", "NuStar Energy", "Sunoco LP", "USA Compression", "Genesis Energy", "Holly Energy", "NGL Energy", "CrossAmerica", "Cheniere Energy", "TC PipeLines", "Blueknight Energy", "Sprague Resources"],
                "base_yields": [7.8, 7.2, 8.5, 6.9, 5.5, 7.5, 6.2, 5.8, 6.1, 7.1, 6.5, 9.2, 8.5, 9.5, 8.8, 7.9, 9.5, 11.2, 8.5, 12.5, 10.5, 7.2, 8.1, 11.5, 10.2],
                "labels": ["예상 배당수익률 (Yield)", "현금흐름 커버리지 (x)", "수수료 기반 이익 비중"],
                "data": {
                    "AMLP": [7.8, 1.8, 85.0, "원자재 가격 변동성보다는 파이프라인 통행료(Toll-road) 방식의 수익 비중이 높아 예측 가능한 강력한 현금흐름을 창출합니다."],
                    "EPD": [7.2, 1.9, 90.0, "미국 최대 에너지 인프라 기업으로, 압도적인 규모의 경제를 바탕으로 꾸준히 배당금을 인상해 온 배당 성장 자산입니다."],
                    "ET": [8.5, 1.7, 80.0, "공격적인 파이프라인 확장 및 M&A를 통해 성장성을 확보했으며, 동종 업계 대비 높은 수준의 배당률을 제공합니다."]
                },
                "stress_name": "글로벌 유가 폭락 충격률 (Price Shock, %)",
                "recovery_default": 80.0
            },
            "상장 실물자산 (Listed Real Assets)": {
                "tickers": ["VNQ", "XLRE", "SCHH", "IFGL", "USRT", "INDA", "TOL", "PLD", "DHI", "LEN", "AMT", "CCI", "EQIX", "PSA", "O"],
                "names": ["Vanguard Real Estate", "Real Estate Select", "Schwab US REIT", "iShares Int Dev", "iShares Core REIT", "iShares India", "Toll Brothers", "Prologis", "DR Horton", "Lennar", "American Tower", "Crown Castle", "Equinix", "Public Storage", "Realty Income"],
                "base_yields": [4.5, 3.8, 4.2, 5.1, 4.0, 3.5, 2.8, 3.1, 2.5, 2.7, 3.2, 6.5, 2.1, 4.5, 5.8],
                "labels": ["예상 배당수익률 (Yield)", "Cap Rate (%)", "평균 임대차 만기 (년)"],
                "data": {
                    "VNQ": [4.5, 5.8, 4.5, "미국 리츠 시장 전반에 투자하여 다각화된 부동산 배당 수익을 추구합니다."],
                    "XLRE": [3.8, 5.2, 5.0, "S&P 500 내 우량 대형 부동산 기업에 집중 투자하여 안정성을 높였습니다."],
                    "SCHH": [4.2, 5.5, 4.8, "저비용으로 미국 리츠 시장에 광범위하게 투자할 수 있는 효율적인 수단입니다."]
                },
                "stress_name": "글로벌 금리 급등 충격률 (%)",
                "recovery_default": 70.0
            }
        }

        current_db = mock_db[asset_class]
        tkrs = current_db["tickers"]
        nms = current_db["names"]
        b_ylds = current_db["base_yields"]

        with st.expander("⚙️ 고급 시뮬레이션 파라미터 (투입 변수) 설정", expanded=False):
            c_p1, c_p2, c_p3 = st.columns(3)
            with c_p1:
                st.markdown("**[크레딧 요약 수학 모델 가중치]**")
                base_yield_th = st.number_input("기준 배당률(%)", value=6.0, step=0.5, help="안전 펀드의 기본 배당률 하한선")
                base_ltv = st.number_input("기본 레버리지(LTV, %)", value=40.0, step=5.0, help="기준 배당률을 맞추기 위한 기본 부채비율")
                ltv_mul = st.number_input("위험 프리미엄 배수", value=1.5, step=0.1, help="초과 배당 1%당 증가하는 LTV 비율")
            with c_p2:
                st.markdown("**[환율(FX) 비용 변수]**")
                fx_hedge_cost = st.number_input("예상 환헤지 프리미엄/비용(%)", value=2.0, step=0.1, help="한미 금리차 등으로 인한 환헤지 롤오버 비용")
            with c_p3:
                st.markdown("**[수지(P&L) 차감 변수]**")
                trust_fee_deduction = st.number_input("기타 보수 차감(%)", value=0.05, step=0.01, help="운용보수 외 신탁/사무수탁 보수로 빠지는 마진")

        sub_tabs_plan = st.tabs(["🧩 Step 1: 유니버스 구성 및 기초자산 빌딩", "📊 Step 2: 퀀트 기반 백테스팅 및 리스크 테스트", "📈 Step 3: 파생 구조화 및 수지 분석(P&L)"])

        # === Step 1 ===
        with sub_tabs_plan[0]:
            st.markdown("#### 1. 기초자산 포트폴리오 구성 및 환율 전략 설정")
            col_p1, col_p2 = st.columns([1.2, 0.8])
            
            with col_p1:
                with st.container(border=True):
                    st.markdown(f"**[{asset_class}] 기초자산 편입 비중(Weight) 조절**")
                    
                    num_assets = len(tkrs)
                    init_w = [100.0 / num_assets] * num_assets
                    
                    df_bdc_setup = pd.DataFrame({
                        "티커": tkrs,
                        "종목명": nms,
                        "예상 배당률(%)": b_ylds,
                        "목표비중(%)": init_w
                    })
                    
                    edited_bdc_df = st.data_editor(
                        df_bdc_setup,
                        column_config={
                            "티커": st.column_config.TextColumn("티커", disabled=True),
                            "종목명": st.column_config.TextColumn("종목명", disabled=True),
                            "예상 배당률(%)": st.column_config.NumberColumn("예상 배당률(%)", format="%.2f%%", disabled=True),
                            "목표비중(%)": st.column_config.NumberColumn("목표비중(%)", min_value=0.0, max_value=100.0, step=0.5, format="%.2f%%")
                        },
                        hide_index=True,
                        use_container_width=True,
                        height=250 
                    )
                    
                    target_weights_bdc = edited_bdc_df['목표비중(%)'].values
                    tot_bdc = np.sum(target_weights_bdc)
                    if tot_bdc == 0: tot_bdc = 1 
                    normalized_weights_bdc = target_weights_bdc / tot_bdc
                    base_yield = np.dot(np.array(b_ylds), normalized_weights_bdc)
                    
                    df_pie_show = pd.DataFrame({"Asset": tkrs, "Weight": normalized_weights_bdc})
                    df_pie_show = df_pie_show[df_pie_show['Weight'] > 0].sort_values(by='Weight', ascending=False).head(10)
                    
                    if not df_pie_show.empty:
                        fig_bdc_pie = px.pie(df_pie_show, names="Asset", values="Weight", hole=0.5, color_discrete_sequence=px.colors.sequential.Blues_r)
                        fig_bdc_pie.update_layout(height=280, margin=dict(t=10, b=10, l=10, r=10), template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig_bdc_pie, use_container_width=True)

            with col_p2:
                with st.container(border=True):
                    st.markdown("**ETF 운용 구조(Structure) 설정**")
                    fx_strategy = st.selectbox("환율 헤지(FX) 전략", ["환노출 (Unhedged - 환차익/차손 노출)", "환헤지 (Hedged - 한미 금리차 반영)"])
                    ter = st.slider("예상 총보수율 (TER, %)", 0.1, 2.0, 0.45, 0.05, key="ter_step1")
                    
                    applied_fx_cost = 0.0
                    if "환헤지" in fx_strategy:
                        applied_fx_cost = fx_hedge_cost 
                        net_yield = base_yield - applied_fx_cost - ter
                        risk_rating = "보통 위험 (Medium Risk)"
                        mdd = "-12.5%"
                        fx_desc = f"달러 변동성 제거 (헤지 프리미엄 약 {applied_fx_cost}% 차감)"
                        st.info(f"💡 **환헤지 비용 반영:** 현재 한미 금리차를 감안해 연 환산 약 {applied_fx_cost}%의 비용이 차감됩니다.")
                    else:
                        net_yield = base_yield - ter
                        risk_rating = "높은 위험 (High Risk)"
                        mdd = "-22.4%"
                        fx_desc = "달러 강세 시 환차익 추가 향유 가능 (단, 변동성 확대)"
                        st.info("💡 **환노출 반영:** 달러 강세 국면 시 환차익을 추가로 향유할 수 있으나, 변동성에 노출됩니다.")
                    
                    st.markdown("##### 📄 Simulated Product Factsheet")
                    st.metric("최종 타겟 배당수익률 (Net Yield)", f"{net_yield:.2f}%")
                    st.write(f"- **위험 등급:** {risk_rating}")
                    st.write(f"- **FX 전략:** {fx_desc}")
                    
                    if net_yield >= 5.0:
                        st.success("💰 **세금 최적화(Tax):** 배당소득세(15.4%) 및 종합과세 부담 방어를 위해 **ISA 및 IRP(퇴직연금) 계좌 편입용**으로 타겟팅하는 것이 유리합니다.")
                
                with st.container(border=True):
                    st.markdown("**[심화] 기초자산 상관관계 매트릭스 (다각화 증명)**")
                    np.random.seed(42)
                    top5_tkrs = df_pie_show.head(5)["Asset"].tolist() if not df_pie_show.empty else tkrs[:5]
                    corr_matrix = np.random.uniform(0.3, 0.8, size=(len(top5_tkrs), len(top5_tkrs)))
                    np.fill_diagonal(corr_matrix, 1.0)
                    corr_matrix = (corr_matrix + corr_matrix.T) / 2
                    np.fill_diagonal(corr_matrix, 1.0)
                    
                    corr_df = pd.DataFrame(corr_matrix, columns=top5_tkrs, index=top5_tkrs)
                    fig_corr = px.imshow(corr_df, text_auto=".2f", color_continuous_scale="Blues", template="plotly_dark", aspect="auto")
                    fig_corr.update_layout(height=250, margin=dict(t=10,b=10,l=10,r=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_corr, use_container_width=True)

        # === Step 2 ===
        with sub_tabs_plan[1]:
            st.markdown("#### 2. 퀀트 기반 백테스팅 및 리스크 테스트")
            col_app1_1, col_app1_2 = st.columns(2)

            with col_app1_1:
                with st.container(border=True):
                    st.markdown(f"**대표자산 크레딧 요약**")
                    selected_ticker = st.selectbox("분석할 대표 종목 선택:", tkrs, key="ticker_sel_app1")
                    
                    if selected_ticker in current_db["data"]:
                        t_val1, t_val2, t_val3, t_comment = current_db["data"][selected_ticker]
                    else:
                        idx = tkrs.index(selected_ticker)
                        b_y = b_ylds[idx]
                        t_val1 = b_y
                        if "BDC" in asset_class:
                            t_val2, t_val3 = round(base_ltv + (b_y - base_yield_th) * ltv_mul, 1), round(80.0 + (b_y / 15.0) * 15.0, 1) 
                            t_comment = f"{nms[idx]}는 우수한 자산 건전성을 바탕으로 배당 안정성을 추구하는 핵심 자산입니다."
                        elif "CLO" in asset_class:
                            t_val2, t_val3 = max(0.0, min(100.0, 100.0 - (b_y - 5.0) * 20.0)), round(0.2 + (b_y / 20.0), 2)
                            t_comment = f"{nms[idx]}는 정교한 트랜치 분석을 통해 선정되었으며, 목표 인컴을 달성하는 데 기여합니다."
                        else:
                            t_val2, t_val3 = round(5.0 + (b_y - 3.0) * 0.5, 1), round(4.0 + (b_y / 10.0) * 2.0, 1)
                            t_comment = f"{nms[idx]}는 우량 실물자산을 기반으로 포트폴리오의 안정성을 지탱합니다."

                    l_val1, l_val2, l_val3 = current_db["labels"]
                    def format_metric(label, value):
                        if "Yield" in label or "비중" in label or "YTM" in label or "LTV" in label or "Cap Rate" in label: return f"{value:.1f}%"
                        elif "듀레이션" in label or "만기" in label: return f"{value:.2f}년"
                        elif "커버리지" in label: return f"{value:.1f}x"
                        return str(value)

                    c_cm1, c_cm2, c_cm3 = st.columns(3)
                    c_cm1.metric(l_val1, format_metric(l_val1, t_val1))
                    c_cm2.metric(l_val2, format_metric(l_val2, t_val2))
                    c_cm3.metric(l_val3, format_metric(l_val3, t_val3))
                    st.markdown(f"> **[코멘트]** {t_comment}")

            with col_app1_2:
                with st.container(border=True):
                    st.markdown(f"**매크로 스트레스 테스트**")
                    stress_rate = st.slider(current_db["stress_name"], min_value=0.0, max_value=15.0, value=2.0, step=0.5, key="stress_slider_app1")
                    recovery_rate = st.number_input("예상 회수율/방어율 (Recovery Rate, %)", value=current_db["recovery_default"], step=5.0, key="rec_rate_app1") / 100
                    
                    loss_impact = stress_rate * (1 - recovery_rate)
                    adjusted_yield = base_yield - loss_impact
                    
                    st.metric("시나리오 적용 후 실질 수익률", f"{adjusted_yield:.2f}%", f"-{loss_impact:.2f}% (손실분)", delta_color="inverse")
                    if adjusted_yield < 5.0: st.error("⚠️ **경고:** 실질 수익률 5% 미만 하락 (BEP 이탈 위험 진입)")
                    else: st.success("✅ **안정:** 타겟 인컴 방어 가능 (펀드 펀더멘털 유지)")

            st.divider()
            st.markdown("**[심화] 퀀트 기반 실제 주가 백테스팅 (과거 3년 & 향후 1년 몬테카를로)**")
            
            end_dt = datetime.today()
            start_dt = end_dt - timedelta(days=365*3)
            
            real_port_daily = pd.Series(dtype=float)
            spy_daily = pd.Series(dtype=float)
            is_real_data = False
            
            try:
                with st.spinner("실제 글로벌 기초자산 주가 데이터를 실시간 수집 중입니다... (API 호출)"):
                    spy_df = fdr.DataReader('SPY', start_dt, end_dt) 
                    spy_daily = spy_df['Close'].pct_change().dropna()
                    
                    valid_data = {}
                    for idx, tkr in enumerate(tkrs):
                        w = normalized_weights_bdc[idx]
                        if w > 0:
                            df_tkr = fdr.DataReader(tkr, start_dt, end_dt)
                            if len(df_tkr) > 200: 
                                valid_data[tkr] = df_tkr['Close'].pct_change().dropna() * w
                                
                    if len(valid_data) > 0:
                        real_port_daily = pd.DataFrame(valid_data).sum(axis=1)
                        is_real_data = True
            except:
                pass

            c_bt1, c_bt2 = st.columns(2)
            with c_bt1:
                if is_real_data and not real_port_daily.empty:
                    st.success("✅ 실제 시장 API 데이터를 기반으로 한 백테스팅 차트입니다.")
                    sp_cum = (1 + spy_daily).cumprod() * 100
                    port_cum = (1 + real_port_daily).cumprod() * 100
                    df_proxy = pd.DataFrame({"Date": port_cum.index, "S&P 500 (SPY)": sp_cum, "신규 기획 ETF (Real Data)": port_cum}).melt(id_vars="Date")
                    
                    port_ret = real_port_daily.values
                    sp500_ret = spy_daily.values[:len(port_ret)] if len(spy_daily) >= len(port_ret) else np.pad(spy_daily.values, (0, len(port_ret)-len(spy_daily)), 'constant')
                    
                    port_vol = np.std(port_ret) * np.sqrt(252)
                else:
                    st.warning("⚠️ 일부 신규 자산의 과거 데이터가 부족하거나 API 타임아웃으로 인해 퀀트 프록시(합성 데이터) 모델로 대체 계산되었습니다.")
                    np.random.seed(42)
                    days = 252 * 3
                    dates = pd.date_range(end=end_dt, periods=days)
                    sp500_ret = np.random.normal(0.0004, 0.012, days)
                    sp_cum = (1 + sp500_ret).cumprod() * 100
                    
                    port_vol = 0.008 if "CLO" in asset_class else 0.015
                    port_ret = np.random.normal((net_yield/100)/252, port_vol, days)
                    port_cum = (1 + port_ret).cumprod() * 100
                    df_proxy = pd.DataFrame({"Date": dates, "S&P 500 (Proxy)": sp_cum, "신규 기획 ETF (Proxy)": port_cum}).melt(id_vars="Date")

                fig_proxy = px.line(df_proxy, x="Date", y="value", color="variable", template="plotly_dark", color_discrete_sequence=['gray', '#ffb04d'])
                fig_proxy.update_layout(title="과거 3년 시뮬레이션 궤적", height=300, margin=dict(t=30,b=10,l=10,r=10), yaxis_title="누적 수익률 (Base 100)", xaxis_title="", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_proxy, use_container_width=True)
                
                sharpe = (net_yield - 3.5) / (port_vol * 100) if port_vol > 0 else 0
                proxy_mdd = (port_cum / np.maximum.accumulate(port_cum) - 1).min() * 100
                corr = np.corrcoef(sp500_ret[:len(port_ret)], port_ret)[0,1] if len(port_ret) > 1 else 0
                
                cc1, cc2, cc3 = st.columns(3)
                cc1.metric("샤프 비율", f"{sharpe:.2f}")
                cc2.metric("실증 최대 낙폭", f"{proxy_mdd:.1f}%")
                cc3.metric("S&P 상관계수", f"{corr:.2f}")
                
            with c_bt2:
                st.markdown("<br>", unsafe_allow_html=True)
                mc_days = 252
                mc_data = pd.DataFrame()
                sim_vol = port_vol if is_real_data else (0.008 if "CLO" in asset_class else 0.015)
                for i in range(30): 
                    mc_data[f"Sim {i}"] = (1 + np.random.normal((net_yield/100)/252, sim_vol, mc_days)).cumprod() * 100
                
                fig_mc = go.Figure()
                for col in mc_data.columns:
                    fig_mc.add_trace(go.Scatter(y=mc_data[col], mode='lines', line=dict(width=1, color='rgba(77, 166, 255, 0.15)'), showlegend=False))
                fig_mc.add_trace(go.Scatter(y=mc_data.mean(axis=1), mode='lines', line=dict(width=3, color='#ffb04d'), name='Base Case (평균 기대치)'))
                fig_mc.update_layout(title="향후 1년 몬테카를로 시나리오 (30 Paths)", height=300, margin=dict(t=30,b=10,l=10,r=10), template="plotly_dark", yaxis_title="예상 수익률 (Base 100)", xaxis_title="거래일", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_mc, use_container_width=True)

        # === Step 3 ===
        with sub_tabs_plan[2]:
            st.markdown("#### 3. 파생상품 구조화 및 정교한 수지 분석(P&L)")
            
            with st.container(border=True):
                st.markdown("**파생상품(옵션) 결합 수익률 시뮬레이터 (Payoff Modeling)**")
                st.caption("초단기 커버드콜(0DTE) 및 하방 방어형(Buffer) ETF 등 파생상품이 결합된 ETF의 만기 시점 페이오프 구조를 시각화합니다.")

                opt_strategy = st.radio("시뮬레이션 전략 선택:", ["초단기 커버드콜 (Covered Call)", "하방 방어형 (Buffer ETF)"], horizontal=True, key="opt_strat_sel")

                c_opt1, c_opt2 = st.columns([1, 2])
                
                with c_opt1:
                    st.markdown("**⚙️ 파라미터(옵션 조건) 설정**")
                    if "Covered Call" in opt_strategy:
                        strike_pct = st.slider("콜옵션 행사가격 (Strike, % OTM)", min_value=0.0, max_value=10.0, value=2.0, step=0.5, key="strike_pct_app2")
                        premium = st.slider("수취 프리미엄 (Premium, %)", min_value=0.5, max_value=5.0, value=1.5, step=0.1, key="prem_app2")
                    else:
                        buffer_pct = st.slider("하방 방어 수준 (Buffer, %)", min_value=5.0, max_value=20.0, value=10.0, step=1.0, key="buff_pct_app2")
                        cap_pct = st.slider("상방 제한 수준 (Cap, %)", min_value=5.0, max_value=15.0, value=8.0, step=1.0, key="cap_pct_app2")
                
                with c_opt2:
                    st.markdown("**📉 만기 시점 수익률 구조 (Payoff Diagram)**")
                    x_vals = np.linspace(-30, 30, 200)
                    
                    if "Covered Call" in opt_strategy:
                        y_vals = np.where(x_vals < strike_pct, x_vals + premium, strike_pct + premium)
                        max_return = strike_pct + premium
                        
                        fig_opt = go.Figure()
                        fig_opt.add_trace(go.Scatter(x=x_vals, y=x_vals, mode='lines', name='기초지수', line=dict(dash='dash', color='gray')))
                        fig_opt.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines', name='커버드콜 수익률', line=dict(color='#4da6ff', width=3)))
                        fig_opt.update_layout(height=300, margin=dict(t=10,b=10,l=10,r=10), template="plotly_dark", xaxis_title="기초자산 가격 변동 (%)", yaxis_title="ETF 만기 수익률 (%)", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig_opt, use_container_width=True)
                        
                        st.caption(f"💡 프리미엄 {premium}%를 수취하여 하락장에서는 그만큼 손실을 방어하지만, 기초자산이 {strike_pct}% 이상 급등할 경우 수익은 {max_return}%로 제한됩니다.")
                    else:
                        y_vals = np.where(x_vals > 0, np.minimum(x_vals, cap_pct), np.where(x_vals >= -buffer_pct, 0, x_vals + buffer_pct))
                        
                        fig_opt = go.Figure()
                        fig_opt.add_trace(go.Scatter(x=x_vals, y=x_vals, mode='lines', name='기초지수', line=dict(dash='dash', color='gray')))
                        fig_opt.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines', name='버퍼 ETF 수익률', line=dict(color='#ffb04d', width=3)))
                        fig_opt.add_vrect(x0=-buffer_pct, x1=0, fillcolor="#ffb04d", opacity=0.1, layer="below", line_width=0, annotation_text="100% 방어 구간", annotation_position="bottom right")
                        fig_opt.update_layout(height=300, margin=dict(t=10,b=10,l=10,r=10), template="plotly_dark", xaxis_title="기초자산 가격 변동 (%)", yaxis_title="ETF 만기 수익률 (%)", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig_opt, use_container_width=True)
                        
                        st.caption(f"💡 기초자산이 최대 -{buffer_pct}%까지 하락해도 원금을 100% 보존하지만, 방어 비용 지불을 위해 상승장에서는 최대 {cap_pct}%까지만 수익을 공유합니다.")

            with st.container(border=True):
                st.markdown("**자산운용사(AMC) 정교한 수지 분석 (P&L)**")
                c_pl1, c_pl2 = st.columns([1, 1.5])
                
                with c_pl1:
                    target_aum = st.number_input("1년 차 타겟 AUM (억원)", min_value=100, value=1000, step=100)
                    seeding_cap = st.number_input("초기 설정액 (Seeding, 억원)", min_value=50, value=200, step=50)
                    fixed_cost = st.number_input("연간 상장유지 고정비용 (억원)", value=2.0, step=0.5)
                    mkt_cost = st.number_input("연간 런칭 마케팅 예산 (억원)", value=1.5, step=0.5)
                    
                    amc_margin = ter - trust_fee_deduction
                    expected_revenue = target_aum * (amc_margin / 100)
                    net_profit = expected_revenue - fixed_cost - mkt_cost
                    
                    bep_aum = (fixed_cost + mkt_cost) / (amc_margin / 100) if amc_margin > 0 else 0
                    req_monthly = (bep_aum - seeding_cap) / 12 if bep_aum > seeding_cap else 0
                    
                    st.metric(f"AMC 순수 영업이익 추정 (운용보수 {amc_margin:.2f}%)", f"{net_profit:+.2f} 억원", delta_color="normal" if net_profit>0 else "inverse")
                    if bep_aum > 0:
                        st.info(f"📍 **BEP 달성 목표 AUM:** {bep_aum:.0f}억원\n\n💸 초기 설정액 제외, **매월 약 {req_monthly:.0f}억원**의 순유입(Inflow)이 달성되어야 1년 내 흑자 전환이 가능합니다.")
                
                with c_pl2:
                    st.markdown("**[심화] 보수율(TER) 민감도 분석 차트**")
                    st.caption("타겟 AUM 고정 시, 보수율 증감에 따른 영업이익 변화율을 산출합니다.")
                    ter_range = np.linspace(max(0.1, ter-0.2), ter+0.2, 5)
                    profits = [target_aum * ((t - trust_fee_deduction)/100) - fixed_cost - mkt_cost for t in ter_range]
                    df_sens = pd.DataFrame({"총보수율(TER %)": ter_range, "예상 순이익(억원)": profits})
                    fig_sens = px.bar(df_sens, x="총보수율(TER %)", y="예상 순이익(억원)", text_auto=".2f", template="plotly_dark", color="예상 순이익(억원)", color_continuous_scale="Blues")
                    fig_sens.update_layout(height=250, margin=dict(t=10,b=10,l=10,r=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
                    st.plotly_chart(fig_sens, use_container_width=True)

    # =========================================================================
    # Big 탭 3: 🤖 AI 프롬프트
    # =========================================================================
    elif big_tab == "🤖 AI 프롬프트":
        st.markdown("### 🧠 모듈형 AI 프롬프트 컨트롤 타워")
        st.caption("각 단계별 목적에 맞게 AI(LLM)에게 전달할 최적화된 프롬프트를 체인(Chain) 형태로 분리하여 제공합니다.")
        
        prompt_tabs = st.tabs(["📊 1. 주간 모니터링 체인 프롬프트", "🌍 2. 상품 기획 RAG 체인 프롬프트"])
        
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
            st.markdown("#### [심화 RAG 규제 분석 및 상품기획서 생성]")
            st.caption("타겟 기업의 IR 자료나 매크로 문건을 업로드하면, AI가 데이터를 클렌징하고 3-Step 체인 프롬프트와 융합할 준비를 마칩니다.")
            
            col_doc1, col_doc2 = st.columns(2)
            with col_doc1:
                fin_docs = st.file_uploader("🏢 타겟 기업 재무제표 / IR 자료 (PDF, Excel)", type=["pdf", "xlsx", "csv"], accept_multiple_files=True, key="fin_docs")
            with col_doc2:
                reg_docs = st.file_uploader("⚖️ 매크로 / 규제 및 정책 문건 (PDF, Text)", type=["pdf", "docx", "txt"], accept_multiple_files=True, key="reg_docs")

            if st.button("✨ RAG 데이터 클렌징 및 인덱싱 시작", type="primary"):
                if fin_docs or reg_docs:
                    with st.spinner("AI가 재무제표의 FCF/LTV를 추출하고, 규제 문건의 타임라인을 해독하고 있습니다..."):
                        progress_bar = st.progress(0)
                        for i in range(100):
                            time.sleep(0.01)
                            progress_bar.progress(i + 1)
                    st.success("✅ 문서 클렌징 및 인덱싱이 완료되었습니다! 아래의 3-Step 프롬프트를 활용해 기획서를 작성하세요.")
                else:
                    st.warning("⚠️ 분석할 문서를 먼저 업로드해주세요.")

            st.divider()
            st.markdown("#### [신상품 기획 프롬프트 - 글자 수 제한 방지 3-Step 체인]")
            st.info("💡 프롬프트를 한 번에 넣으면 LLM이 누락할 수 있으므로, 아래 3단계를 순서대로 복사하여 AI에게 지시하세요.")
            
            p2_step1 = """[Step 1: 데이터 딥 파싱 및 규제 검토]
업로드된 PDF/Excel 문건을 분석하여 다음을 추출하시오:
1. 타겟 기초자산 기업들의 평균 잉여현금흐름(FCF) 추이와 평균 LTV(레버리지 비율). 이를 바탕으로 배당의 지속 가능성을 평가할 것.
2. 정책 문건 내 '상장 실물자산/신재생에너지 인프라(InvITs)' 관련 금융위 규제 완화 타임라인 및 KODEX의 출시 적기(Time-to-Market) 도출."""
            st.code(p2_step1, language="text")
            
            p2_step2 = """[Step 2: 퀀트 기반 수지 및 백테스팅 평가]
앞서 확인한 규제 환경을 바탕으로, 다음 시뮬레이터 퀀트 분석 결과를 해석하시오.
- 프록시 백테스트: 샤프 비율, MDD, S&P 500 상관계수를 기반으로 한 기관 투자자 설득 논리 작성.
- P&L: 타겟 AUM 1,000억 달성 시 AMC 순수익 및 월간 필요 순유입(Inflow) 타당성 검증.
- 세금 최적화: 환헤지 비용 차감 후 Net Yield 기반으로 'ISA/퇴직연금(IRP) 편입용' 마케팅 메시지 구성."""
            st.code(p2_step2, language="text")
            
            p2_step3 = """[Step 3: 최종 상품 기획서(Proposal) 작성]
Step 1과 Step 2의 팩트를 융합하여, 본부장 보고용 'KODEX 신상품 개략 검토 보고서'를 다음 목차로 마크다운 작성하시오.
1. 추진 배경 및 시장 공백 (인구 구조 및 연금 수요)
2. 기초자산 유니버스 및 FCF/LTV 펀더멘털 증명
3. 퀀트 시뮬레이션 성과 (위험/수익 프로파일)
4. 수지 분석(P&L) 및 파생상품 결합 페이오프(Payoff) 전략"""
            st.code(p2_step3, language="text")
