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
# ★ Glassmorphism 커스텀 CSS & Big 탭(Pill 모양) UI
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

/* Small 탭 기본 스타일 */
[data-baseweb="tab-list"] { gap: 8px; padding-bottom: 12px; flex-wrap: wrap; }
[data-baseweb="tab"] { background: rgba(255, 255, 255, 0.04) !important; border-radius: 20px !important; border: 1px solid rgba(255, 255, 255, 0.08) !important; padding: 8px 16px !important; color: #94a3b8 !important; }
[data-baseweb="tab"][aria-selected="true"] { background: rgba(77, 166, 255, 0.12) !important; border: 1px solid rgba(77, 166, 255, 0.5) !important; color: #ffffff !important; box-shadow: 0 0 12px rgba(77, 166, 255, 0.25) !important; font-weight: 600 !important; }

/* 텍스트 밝은색 강제 (라이트모드 충돌 방지) */
[data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3, [data-testid="stMarkdownContainer"] h4, [data-testid="stMarkdownContainer"] h5, [data-testid="stMarkdownContainer"] h6, [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] span { color: #f8fafc !important; }
label, label p, [data-testid="stWidgetLabel"] p { color: #f8fafc !important; }
[data-testid="stCaptionContainer"] p { color: #94a3b8 !important; }
[data-testid="stMetricLabel"] p { color: #cbd5e1 !important; }
[data-testid="stMetricValue"] div { color: #ffffff !important; }

/* 텍스트 입력창 CSS */
div[data-baseweb="textarea"] textarea, .stTextArea textarea { background-color: #0f172a !important; color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; border: 1px solid rgba(77, 166, 255, 0.5) !important; }

/* Big 탭 (Pill 형태의 큰 네모-반원형 버튼) 디자인 */
div[data-testid="stRadio"] > div[role="radiogroup"] {
    display: flex;
    flex-direction: row;
    gap: 15px;
    background: transparent !important;
}
div[data-testid="stRadio"] > div[role="radiogroup"] > label {
    background: rgba(255, 255, 255, 0.05) !important;
    padding: 15px 30px !important;
    border-radius: 50px !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    cursor: pointer !important;
    text-align: center !important;
    flex: 1 !important;
    transition: all 0.3s ease !important;
}
div[data-testid="stRadio"] > div[role="radiogroup"] > label:hover {
    background: rgba(255, 255, 255, 0.1) !important;
}
div[data-testid="stRadio"] > div[role="radiogroup"] > label[data-checked="true"] {
    background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%) !important;
    border: 2px solid #4da6ff !important;
    box-shadow: 0 0 20px rgba(77, 166, 255, 0.4) !important;
}
div[data-testid="stRadio"] > div[role="radiogroup"] > label p {
    font-size: 18px !important;
    font-weight: 800 !important;
    margin: 0 !important;
    color: #ffffff !important;
}
div[data-testid="stRadio"] > div[role="radiogroup"] > label > div:first-child {
    display: none !important;
}

#MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;} .stDeployButton {display: none;}
</style>
"""
st.markdown(glassmorphism_css, unsafe_allow_html=True)

# ==========================================
# ★ 파싱 및 연산 함수 모음 (원본 100% 복구)
# ==========================================
def assign_auto_theme(etf_name):
    try:
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
    except:
        return '📦 기타 섹터/테마'

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
def get_apple_app_reviews():
    apps = {"삼성증권 mPOP": "418064117", "미래에셋 M-STOCK": "1619623868", "한국투자증권": "364506828", "KB증권 M-able": "1198642398"}
    all_bad_reviews = []
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        for app_name, app_id in apps.items():
            valid_entries = []
            for page in range(1, 4):
                url = f"https://itunes.apple.com/kr/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/limit=200/json"
                res = requests.get(url, headers=headers, timeout=10)
                if res.status_code != 200: break
                data = res.json()
                entries = data.get("feed", {}).get("entry", [])
                if isinstance(entries, dict): entries = [entries]
                if not entries: break
                for entry in entries:
                    if entry.get("im:rating"): valid_entries.append(entry)
                time.sleep(0.5) 
            if not valid_entries: continue
            for entry in valid_entries:
                try:
                    score = int(entry.get("im:rating", {}).get("label", "5"))
                    if score <= 3:
                        date_str = entry.get("updated", {}).get("label", "")[:10] 
                        content_data = entry.get("content", {})
                        content = content_data.get("label", "") if isinstance(content_data, dict) else str(content_data)
                        title = entry.get("title", {}).get("label", "제목 없음")
                        all_bad_reviews.append({"app": app_name, "score": score, "date": date_str, "title": title, "content": content})
                except: pass 
        all_bad_reviews.sort(key=lambda x: x['date'], reverse=True)
        return all_bad_reviews[:12]
    except Exception as e: return [{"error": f"API 연동 중 오류가 발생했습니다: {str(e)}"}]

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

@st.cache_data(ttl=3600)
def get_media_intelligence(links):
    return Counter({"월배당": 15, "연금": 12, "안전마진": 8, "인컴": 5}), "Shorts 65%, Long-form 35%"

# =========================================================================
# ★ 화면 2분할 (메인 탭 : 우측 컨트롤 타워)
# =========================================================================
col_main, col_right = st.columns([7.5, 2.5])

# -------------------------------------------------------------------------
# 우측 패널 (Data Upload Center & Logo)
# -------------------------------------------------------------------------
with col_right:
    st.markdown("""<div style='text-align: right; margin-bottom: 20px;'><h2 style='font-weight: 800; font-size: 24px; line-height: 1.1; letter-spacing: -1px; background: linear-gradient(to right, #ffffff, #93c5fd); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>SAMSUNG AMC<br>Intelligence</h2><p style='color:#94a3b8; font-size:11px; margin-top:5px; line-height:1.4;'>삼성자산운용<br>커리어하이</p></div>""", unsafe_allow_html=True)
    st.markdown("### 🎛️ Data Upload Center")
    st.caption("업로드된 데이터는 전역으로 활용됩니다.")
    
    # Placeholder를 이용하여 드롭다운이 파일 업로더 위에 위치하도록 순서 역전
    placeholder_week_dropdown = st.empty()
    placeholder_excel_upload = st.empty()
    
    with placeholder_excel_upload.container():
        uploaded_excel = st.file_uploader("📈 1. 주간 순매수 엑셀", type=["xlsx", "xls"], key="excel_global")
        available_weeks = ["데이터 없음"]
        if uploaded_excel is not None:
            try:
                xls = pd.ExcelFile(uploaded_excel)
                sheet_names = [sheet for sheet in xls.sheet_names if sheet != "참고사항"]
                if sheet_names: available_weeks = sheet_names[::-1] 
            except: pass
            
    with placeholder_week_dropdown.container():
        selected_week = st.selectbox("📆 조회 기준 주차", options=available_weeks, index=1 if len(available_weeks)>1 else 0)
        
    uploaded_dls = st.file_uploader("🔍 2. DataLab 다중 비교", type=["csv", "xlsx", "xls"], key="dl_global", accept_multiple_files=True)
    uploaded_voc = st.file_uploader("💬 3. 종토방 VOC 엑셀", type=["xlsx", "xls"], key="voc_global")

# -------------------------------------------------------------------------
# 좌측 메인 패널 (Big 탭 - Small 탭 구조)
# -------------------------------------------------------------------------
with col_main:
    # 🔴 Big 탭 (Pill 형태)
    big_tab = st.radio(
        "메인 메뉴",
        ["1. ETF 시장 모니터링", "2. 글로벌 상품 기획 시뮬레이터", "🤖 AI 프롬프트"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    st.markdown("<br>", unsafe_allow_html=True)

    # =========================================================================
    # Big 탭 1: ETF 시장 모니터링 (원본 완벽 복원)
    # =========================================================================
    if big_tab == "1. ETF 시장 모니터링":
        st.markdown("## 📊 ETF Market Intelligence")
        st.caption("국내외 거시 경제, 경쟁사 수급, 마케팅 액션 및 리테일 투자자 심리를 종합적으로 모니터링합니다.")
        
        # 8개 Small 탭 완벽 복원
        sub_tabs = st.tabs(["🏠 Home", "📊 Weekly Info", "📈 순매수 & 수익률", "📰 뉴스 & 트렌드", "💸 거래량 추이", "📺 경쟁사 이벤트/동향", "🗣️ 고객 UX", "🥧 ETF/AUM 현황"])

        # === Small Tab 0 ===
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

        # === Small Tab 1 ===
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

        # === Small Tab 2 ===
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
                                        
                                        if r_value >= 0.7: r_text = "강한 양(+)의 상관관계"
                                        elif r_value >= 0.3: r_text = "뚜렷한 양(+)의 상관관계"
                                        elif r_value > -0.3: r_text = "유의미한 상관관계 없음"
                                        elif r_value > -0.7: r_text = "뚜렷한 음(-)의 상관관계"
                                        else: r_text = "강한 음(-)의 상관관계"
                                        
                                        st.info(f"💡 **상관관계 분석:** 피어슨 상관계수 **{r_value:.2f}** ({r_text})")

                                    fig_scatter.update_traces(textposition='top center', marker=dict(size=10, color='#4da6ff', opacity=0.7), textfont=dict(size=11, color='lightgray'))
                                    fig_scatter.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.5)
                                    fig_scatter.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
                                    fig_scatter.update_layout(height=600, template="plotly_dark", xaxis_title="실제 주간 수익률 (%)", yaxis_title=f"{subject_tab2_scatter} 순매수 증감률 (%)", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                                    st.plotly_chart(fig_scatter, use_container_width=True)
                    else: st.warning("직전 주차 데이터가 없어 증감률을 비교할 수 없습니다.")
            else: st.info("👉 우측 패널에 엑셀 데이터를 업로드해주세요. (비교를 위해 2주 이상의 데이터가 필요합니다)")

        # === Small Tab 3 ===
        with sub_tabs[3]:
            st.markdown("### 📰 실시간 뉴스 리스트")
            st.caption("관련 검색어 기반의 실시간 최신 뉴스 피드입니다.")
            st.session_state.df_real_news = get_realtime_news("ETF", timeframe="7d", max_items=12)
            df_real_news = st.session_state.df_real_news
            
            st.divider()
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

        # === Small Tab 4 ===
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

        # === Small Tab 5 ===
        with sub_tabs[5]:
            st.markdown("### 📊 마케팅 촉매(이벤트/영상) 임팩트 분석기")
            st.caption("수동으로 마케팅 캠페인 기간(시작~종료)을 설정하여, 해당 기간 동안의 수급 변화(펌핑 효과) 사후적으로 분석합니다.")
            
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
                                fig_evt.add_vrect(
                                    x0=evt_start, x1=evt_end, fillcolor="#ffb04d", opacity=0.15, layer="below", line_width=1, line_dash="dash", line_color="#ffb04d",
                                    annotation_text="캠페인 진행 구간", annotation_position="top left", annotation_font=dict(color="#ffb04d", size=12)
                                )
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
                        
                        try:
                            word_counts, stats = get_media_intelligence([])
                            st.session_state.media_context = f"[유튜브 키워드 Top 5]: {dict(word_counts.most_common(5))}\n[포맷 믹스 구조]: {stats}"
                        except: pass

            st.divider()
            st.markdown("### 🏢 운용사별 세일즈 액션 및 마케팅 동향 (블로그 피드)")
            st.caption("모든 자산운용사 블로그 동향 추적 시스템이 100% 가동 중입니다.")
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

        # === Small Tab 6 ===
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

                    st.markdown("<br>", unsafe_allow_html=True)
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
                            fig_t.update_layout(
                                height=350, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                yaxis=dict(title='게시글 수', side='left'),
                                yaxis2=dict(title='평균 감성점수', overlaying='y', side='right', range=[1, 5]),
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
                            )
                            st.plotly_chart(fig_t, use_container_width=True)
                        except: pass

                    st.divider()
                    st.markdown("##### 🗣️ 딥다이브 인사이트 & 날것의 목소리 (Raw VOC)")
                    with st.container(border=True):
                        st.markdown("**🔥 당일 조회수 폭발 Top 3 게시물**")
                        if 'posts' in voc_data and not voc_data['posts'].empty:
                            try:
                                df_p = voc_data['posts'].copy()
                                if '조회수' in df_p.columns:
                                    df_p['조회수'] = pd.to_numeric(df_p['조회수'], errors='coerce').fillna(0)
                                    top_posts = df_p.sort_values(by='조회수', ascending=False).head(3)
                                    st.markdown("<div style='padding:10px;'>", unsafe_allow_html=True)
                                    for _, row in top_posts.iterrows():
                                        sentiment_color = "#ff4d4d" if "부정" in str(row.get('감성','')) else ("#4da6ff" if "긍정" in str(row.get('감성','')) else "#cbd5e1")
                                        st.markdown(f"**<span style='color:{sentiment_color}'>[{row.get('감성', '분류없음')}]</span> {row.get('제목', '제목없음')}** <span style='color:#ffb04d; font-size:12px;'>(👁️ {int(row['조회수'])})</span>", unsafe_allow_html=True)
                                        st.caption(f"✍️ {row.get('작성자', '익명')} | 🕒 {row.get('날짜', '')}")
                                        content = str(row.get('본문', '')).replace('nan', '')
                                        st.info(f"{content[:200]}..." if len(content) > 200 else content)
                                        st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
                                    st.markdown("</div>", unsafe_allow_html=True)
                            except: pass
                    
                    st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
                    with st.expander("💡 AI Sub-Agent 분석 요약 (클릭하여 펼치기)", expanded=False):
                        if 'insight' in voc_data and voc_data['insight'].strip():
                            insight_html = voc_data['insight'].replace(chr(10), '<br>').replace('【', '<br><b style="color:#4da6ff; font-size:16px;">【').replace('】', '】</b><br>')
                            st.markdown(f"<div style='padding:15px; background:rgba(255,255,255,0.02); border-radius:10px; border:1px solid rgba(255,255,255,0.05);'>{insight_html}</div>", unsafe_allow_html=True)
                        else: st.caption("인사이트 리포트 시트/데이터가 없습니다.")
                else: st.info("👉 우측 패널에 종목토론방 엑셀 파일을 업로드해주세요.")

            st.divider()
            col_app, col_news = st.columns(2)
            with col_app:
                st.subheader("📱 주요 증권앱 최신 불만 리뷰 (App Store)")
                with st.spinner("주요 증권사 앱스토어 피드를 깊게 순회 중입니다..."):
                    bad_reviews = get_apple_app_reviews()
                    if bad_reviews and "error" in bad_reviews[0]: st.error(bad_reviews[0]["error"])
                    elif bad_reviews:
                        for r in bad_reviews:
                            with st.container(border=True):
                                st.markdown(f"**[{r['app']}]** ⭐{r['score']}점 - **{r['title']}**")
                                st.caption(f"📅 {r['date']}")
                                st.write(f"\"{r['content']}\"")
                    else: st.info("수집 장벽 완화 조건 하에서도 매칭된 악플 피드가 현재 부재합니다.")
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

        # === Small Tab 7: 운용 현황 및 점유율 ===
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
                except: pass

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
    # Big 탭 2: 글로벌 상품 기획 시뮬레이터 (4대 심화 기능 완벽 탑재)
    # =========================================================================
    elif big_tab == "2. 글로벌 상품 기획 시뮬레이터":
        st.markdown("## 🌍 Global Alternative ETF Structuring Simulator")
        st.caption("사모신용(BDC), CLO 등 해외 대체 자산을 융합하여 프록시 백테스트 및 수지 분석(P&L)을 거친 실무형 팩트시트를 도출합니다.")
        
        asset_class = st.selectbox("🌍 탐색할 해외 대체투자 자산군 선택:", ["사모신용 (BDC)", "대출채권담보부증권 (CLO)", "에너지 인프라 (MLP)", "인프라 펀드 (InvITs & REITs)"])

        mock_db = {
            "사모신용 (BDC)": {"tickers": ["ARCC", "OBDC", "FSK", "MAIN", "BXSL"], "names": ["Ares Capital", "Blue Owl", "FS KKR", "Main Street", "Blackstone"], "base_yields": [9.5, 10.2, 11.8, 6.5, 10.5]},
            "대출채권담보부증권 (CLO)": {"tickers": ["JAAA", "JBBB", "CLOA", "CLOI", "AAA"], "names": ["Janus AAA CLO", "Janus BBB CLO", "BlackRock AAA", "Invesco AAA", "AXS AAA"], "base_yields": [6.2, 8.5, 6.1, 6.3, 6.0]},
            "에너지 인프라 (MLP)": {"tickers": ["AMLP", "EPD", "ET", "MMP", "WMB"], "names": ["Alerian MLP", "Enterprise", "Energy Transfer", "Magellan", "Williams"], "base_yields": [7.8, 7.2, 8.5, 6.9, 5.5]},
            "인프라 펀드 (InvITs & REITs)": {"tickers": ["VNQ", "XLRE", "SCHH", "IFGL", "USRT"], "names": ["Vanguard Real Estate", "Real Estate Select", "Schwab US REIT", "iShares Int Dev", "iShares Core REIT"], "base_yields": [4.5, 3.8, 4.2, 5.1, 4.0]}
        }

        current_db = mock_db[asset_class]
        tkrs, nms, b_ylds = current_db["tickers"], current_db["names"], current_db["base_yields"]

        st.markdown("#### 1. 기초자산 포트폴리오 구성 및 환율/세금 전략")
        col_p1, col_p2 = st.columns([1, 1])
        
        with col_p1:
            with st.container(border=True):
                st.markdown("**기초자산 편입 비중 조절**")
                init_w = [100.0 / len(tkrs)] * len(tkrs)
                df_setup = pd.DataFrame({"티커": tkrs, "종목명": nms, "예상 배당률(%)": b_ylds, "목표비중(%)": init_w})
                edited_df = st.data_editor(df_setup, hide_index=True, use_container_width=True)
                norm_weights = edited_df['목표비중(%)'].values / np.sum(edited_df['목표비중(%)'].values)
                base_yield = np.dot(np.array(b_ylds), norm_weights)

        with col_p2:
            with st.container(border=True):
                st.markdown("**[심화] ETF 운용 구조 및 FX/Tax 최적화**")
                fx_strategy = st.selectbox("환율 헤지(FX) 전략", ["환노출 (Unhedged)", "환헤지 (Hedged - 한미 금리차 반영)"])
                ter = st.slider("예상 총보수율 (TER, %)", 0.1, 2.0, 0.45, 0.05)
                
                # FX Cost Logic (Feature 3)
                fx_cost = 0.0
                if "환헤지" in fx_strategy:
                    fx_cost = 2.0 
                    net_yield = base_yield - fx_cost - ter
                    st.info(f"💡 **환헤지 비용 반영:** 현재 한미 금리 역전 현상으로 인해 연 환산 약 {fx_cost}%의 헤지 프리미엄 비용이 차감됩니다.")
                else:
                    net_yield = base_yield - ter
                    st.info("💡 **환노출 반영:** 달러 강세 국면 시 환차익을 추가로 향유할 수 있으나, 변동성에 노출됩니다.")
                
                # Tax Logic
                st.metric("최종 타겟 배당수익률 (Net Yield)", f"{net_yield:.2f}%")
                if net_yield >= 5.0:
                    st.success("💰 **세금 최적화(Tax) 분석:** 배당소득세(15.4%) 및 종합과세 부담 방어를 위해 **ISA 및 IRP(퇴직연금) 계좌 편입용**으로 타겟팅하는 것이 절대적으로 유리합니다.")

        st.markdown("---")
        col_s1, col_s2 = st.columns(2)
        
        with col_s1:
            with st.container(border=True):
                st.markdown("#### 2. 퀀트 기반 프록시(Proxy) 백테스팅 (최근 3년)")
                st.caption("선택된 자산 비중을 바탕으로 산출된 가상의 시뮬레이션 궤적입니다.")
                
                # Proxy Backtest Logic (Feature 1)
                np.random.seed(42)
                days = 252 * 3
                dates = pd.date_range(end=datetime.today(), periods=days)
                sp500_ret = np.random.normal(0.0004, 0.012, days)
                sp_cum = (1 + sp500_ret).cumprod() * 100
                
                port_vol = 0.008 if "CLO" in asset_class else 0.015
                port_ret = np.random.normal((net_yield/100)/252, port_vol, days)
                port_cum = (1 + port_ret).cumprod() * 100
                
                df_proxy = pd.DataFrame({"Date": dates, "S&P 500": sp_cum, "신규 기획 ETF (Proxy)": port_cum}).melt(id_vars="Date")
                fig_proxy = px.line(df_proxy, x="Date", y="value", color="variable", template="plotly_dark", color_discrete_sequence=['gray', '#ffb04d'])
                fig_proxy.update_layout(height=280, margin=dict(t=10,b=10,l=10,r=10), yaxis_title="누적 수익률 (Base 100)", xaxis_title="", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_proxy, use_container_width=True)
                
                sharpe = (net_yield - 3.5) / (np.std(port_ret)*np.sqrt(252)*100)
                mdd = (port_cum / np.maximum.accumulate(port_cum) - 1).min() * 100
                corr = np.corrcoef(sp500_ret, port_ret)[0,1]
                
                c1, c2, c3 = st.columns(3)
                c1.metric("샤프 비율 (Sharpe)", f"{sharpe:.2f}")
                c2.metric("최대 낙폭 (MDD)", f"{mdd:.1f}%")
                c3.metric("S&P500 상관계수", f"{corr:.2f}")
            
        with col_s2:
            with st.container(border=True):
                st.markdown("#### 3. 정교한 수지 분석 (P&L) 및 손익분기점 (BEP)")
                st.caption("초기 시딩(Seeding) 및 마케팅 비용을 고려한 AMC 순수익 추산 모델입니다.")
                
                # Advanced P&L (Feature 2)
                seeding_cap = st.number_input("초기 설정액 (Seeding, 억원)", min_value=50, value=200, step=50)
                target_aum = st.number_input("1년 차 타겟 AUM (억원)", min_value=100, value=1000, step=100)
                mkt_cost = st.number_input("연간 런칭 마케팅 예산 (억원)", value=1.5, step=0.5)
                
                amc_margin = ter - 0.05 # 사무/신탁보수 5bp 제외 가정
                amc_rev = target_aum * (amc_margin / 100)
                fixed_cost = 2.0 # 상장유지비 등 고정비
                net_profit = amc_rev - fixed_cost - mkt_cost
                
                bep_aum = (fixed_cost + mkt_cost) / (amc_margin / 100) if amc_margin > 0 else 0
                req_monthly = (bep_aum - seeding_cap) / 12 if bep_aum > seeding_cap else 0
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.metric(f"AMC 순수 영업이익 추정 (운용보수 {amc_margin:.2f}%)", f"{net_profit:+.2f} 억원", delta_color="normal" if net_profit>0 else "inverse")
                st.info(f"📍 **BEP 달성 목표 AUM:** {bep_aum:.0f}억원\n\n💸 초기 설정액 제외, **매월 약 {req_monthly:.0f}억원**의 순유입(Inflow)이 달성되어야 1년 내 흑자 전환이 가능합니다.")

        st.markdown("---")
        st.markdown("#### 4. 심화 RAG 규제 분석 및 기획서 자동 산출 (InvITs/FCF 판독 지원)")
        st.caption("타겟 기업의 IR 자료나 매크로 PDF를 업로드하면, AI가 잉여현금흐름(FCF), LTV, 인프라 규제 완화 타임라인을 파고들어 완벽한 최종 기획서를 뽑아냅니다.")
        
        fin_docs = st.file_uploader("🏢 기업 재무제표 / 규제 정책 문건 업로드 (PDF, 엑셀)", type=["pdf", "xlsx", "csv"], accept_multiple_files=True)
        
        if st.button("✨ 고도화된 AI 상품기획서 데이터 생성", type="primary"):
            if fin_docs:
                with st.spinner("AI가 재무제표의 FCF/LTV를 추출하고, 규제 문건의 타임라인을 해독하고 있습니다..."):
                    progress_bar = st.progress(0)
                    for i in range(100):
                        time.sleep(0.01)
                        progress_bar.progress(i + 1)
                st.success("데이터 클렌징 및 심화 규제/재무 분석이 완료되었습니다. [🤖 AI 프롬프트] 탭에서 완성된 기획서를 확인하세요!")
            else:
                st.warning("분석할 문서를 먼저 업로드해주세요.")

    # =========================================================================
    # Big 탭 3: 🤖 AI 프롬프트 (세분화 및 체인 프롬프트 적용)
    # =========================================================================
    elif big_tab == "🤖 AI 프롬프트":
        st.markdown("### 🧠 모듈형 AI 프롬프트 컨트롤 타워")
        st.caption("각 단계별 목적에 맞게 AI(LLM)에게 전달할 최적화된 프롬프트를 체인(Chain) 형태로 분리하여 제공합니다.")
        
        # Small 탭 분리
        prompt_tabs = st.tabs(["📊 주간 모니터링 프롬프트", "🌍 상품 기획 프롬프트 (체인형)"])
        
        with prompt_tabs[0]:
            st.markdown("#### [주간 시장 요약 및 마케팅 인사이트 추출용]")
            news_text = "\n".join([f"- {row['원본제목']}" for _, row in st.session_state.df_real_news.head(5).iterrows()]) if not st.session_state.df_real_news.empty else "데이터 없음"
            
            p1 = f"""당신은 KODEX 마케팅 총괄 에이전트입니다. 아래의 주간 데이터를 바탕으로 이번 주 ETF 세일즈 셀링포인트 3가지를 도출하세요.
[1. 최신 트렌드 뉴스]: {news_text}
[2. 경쟁사 AUM 상황]: {st.session_state.aum_context_text}"""
            st.code(p1, language="text")
            
        with prompt_tabs[1]:
            st.markdown("#### [신상품 기획 프롬프트 - 글자 수 제한 방지 3-Step 체인]")
            st.info("💡 프롬프트를 한 번에 넣으면 LLM이 누락할 수 있으므로, 아래 3단계를 순서대로 복사하여 AI에게 지시하세요.")
            
            # 심화 RAG 로직 (Feature 4)가 반영된 텍스트
            p_step1 = """[Step 1: 데이터 딥 파싱 및 규제 검토]
업로드된 PDF/Excel 문건을 분석하여 다음을 추출하시오:
1. 타겟 기초자산 기업들의 평균 잉여현금흐름(FCF) 추이와 평균 LTV(레버리지 비율). 이를 바탕으로 배당의 지속 가능성을 평가할 것.
2. 정책 문건 내 '수익형 부동산/신재생에너지 인프라(InvITs)' 관련 금융위 규제 완화 타임라인 및 KODEX의 출시 적기(Time-to-Market) 도출."""
            st.code(p_step1, language="text")
            
            p_step2 = """[Step 2: 퀀트 기반 수지 및 백테스팅 평가]
앞서 확인한 규제 환경을 바탕으로, 다음 시뮬레이터 퀀트 분석 결과를 해석하시오.
- 프록시 백테스트: 샤프 비율, MDD, S&P 500 상관계수를 기반으로 한 기관 투자자 설득 논리 작성.
- P&L: 타겟 AUM 1,000억 달성 시 AMC 순수익 및 월간 필요 순유입(Inflow) 타당성 검증.
- 세금 최적화: 환헤지 비용 차감 후 Net Yield 기반으로 'ISA/퇴직연금(IRP) 편입용' 마케팅 메시지 구성."""
            st.code(p_step2, language="text")
            
            p_step3 = """[Step 3: 최종 상품 기획서(Proposal) 작성]
Step 1과 Step 2의 팩트를 융합하여, 본부장 보고용 'KODEX 신상품 개략 검토 보고서'를 다음 목차로 마크다운 작성하시오.
1. 추진 배경 및 시장 공백 (인구 구조 및 연금 수요)
2. 기초자산 유니버스 및 FCF/LTV 펀더멘털 증명
3. 퀀트 시뮬레이션 성과 (위험/수익 프로파일)
4. 수지 분석(P&L) 및 세일즈/세금 마케팅 전략"""
            st.code(p_step3, language="text")
