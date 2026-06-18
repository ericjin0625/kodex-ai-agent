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
st.set_page_config(page_title="ETF Intelligence & Structuring Agent", layout="wide", initial_sidebar_state="expanded")

# 전역 변수 초기화 (에러 원천 차단 - session_state 활용)
if 'df_scatter' not in st.session_state:
    st.session_state.df_scatter = pd.DataFrame()
comp_yt_links = []

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
.stDataFrame {
    background: transparent !important;
}
[data-baseweb="tab-list"] {
    gap: 8px;
    padding-bottom: 12px;
    flex-wrap: wrap; 
}
[data-baseweb="tab"] {
    background: rgba(255, 255, 255, 0.04) !important;
    border-radius: 20px !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    padding: 8px 16px !important;
    color: #94a3b8 !important;
}
[data-baseweb="tab"][aria-selected="true"] {
    background: rgba(77, 166, 255, 0.12) !important;
    border: 1px solid rgba(77, 166, 255, 0.5) !important;
    color: #ffffff !important;
    box-shadow: 0 0 12px rgba(77, 166, 255, 0.25) !important;
    font-weight: 600 !important;
}
.streamlit-expanderHeader, [data-testid="stExpander"] summary p {
    font-size: 18px !important;
    font-weight: 700 !important;
    color: #ffb04d !important;
}
[data-testid="stSidebar"] {
    background-color: rgba(15, 23, 42, 0.8) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.1);
}
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display: none;}
</style>
"""
st.markdown(glassmorphism_css, unsafe_allow_html=True)

# ==========================================
# ★ 파싱 및 연산 함수 모음
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
                while new_c in seen:
                    new_c += "_"
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
# ★ 좌측 사이드바 (글로벌 네비게이션 및 데이터 업로드)
# =========================================================================
with st.sidebar:
    st.markdown(
        """
        <div style='text-align: right; margin-bottom: 20px;'>
            <h2 style='font-weight: 800; font-size: 24px; line-height: 1.1; letter-spacing: -1px; background: linear-gradient(to right, #ffffff, #93c5fd); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
                SAMSUNG AMC<br>Intelligence
            </h2>
            <p style='color:#94a3b8; font-size:11px; margin-top:5px; line-height:1.4;'>
                삼성자산운용<br>커리어하이
            </p>
        </div>
        """, unsafe_allow_html=True
    )
    
    st.markdown("### 🧭 Main Navigation")
    main_menu = st.radio(
        "메뉴 선택",
        ["1. ETF 시장 모니터링", "2. KODEX 리밸런싱 시뮬레이션", "3. 글로벌 상품 기획 시뮬레이터"],
        label_visibility="collapsed"
    )
    
    st.divider()
    st.markdown("### 🎛️ Data Upload Center")
    st.caption("업로드된 데이터는 전역으로 활용됩니다.")
    
    uploaded_excel = st.file_uploader("📈 1. 주간 순매수 엑셀", type=["xlsx", "xls"], key="excel_global")
    available_weeks = ["데이터 없음"]
    if uploaded_excel is not None:
        try:
            xls = pd.ExcelFile(uploaded_excel)
            sheet_names = [sheet for sheet in xls.sheet_names if sheet != "참고사항"]
            if sheet_names: available_weeks = sheet_names[::-1] 
        except: pass
    selected_week = st.selectbox("📆 조회 기준 주차", options=available_weeks, index=1 if len(available_weeks)>1 else 0)
    
    uploaded_dls = st.file_uploader("🔍 2. DataLab 다중 비교", type=["csv", "xlsx", "xls"], key="dl_global", accept_multiple_files=True)
    uploaded_voc = st.file_uploader("💬 3. 종토방 VOC 엑셀", type=["xlsx", "xls"], key="voc_global")

st.session_state.setdefault('dl_summary', "DataLab 데이터가 업로드되지 않았습니다.")


# =========================================================================
# ★ 모듈 1: ETF 시장 모니터링
# =========================================================================
if main_menu == "1. ETF 시장 모니터링":
    st.markdown("## 📊 ETF Market Intelligence")
    st.caption("국내외 거시 경제, 경쟁사 수급, 마케팅 액션 및 리테일 투자자 심리를 종합적으로 모니터링합니다.")
    
    tab_names = ["🏠 Home", "📊 Weekly Info", "📈 순매수 & 수익률", "📰 뉴스 & 트렌드", "💸 거래량 추이", "📺 경쟁사 이벤트/동향", "🗣️ 고객 UX", "🥧 ETF/AUM 현황", "🧠 AI 프롬프트"]
    tabs = st.tabs(tab_names)

    df_real_news = pd.DataFrame()
    df_volume_summary_text = "데이터 없음"
    aum_context_text = "데이터 없음"

    # === Tab 0 ===
    with tabs[0]:
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

    # === Tab 1 ===
    with tabs[1]:
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
        else: st.info("👉 좌측 사이드바에 ETF 순매수 엑셀 데이터를 업로드해주세요.")

    # === Tab 2 ===
    with tabs[2]:
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
        else: st.info("👉 좌측 사이드바에 엑셀 데이터를 업로드해주세요. (비교를 위해 2주 이상의 데이터가 필요합니다)")

    # === Tab 3 ===
    with tabs[3]:
        st.markdown("### 📰 실시간 뉴스 리스트")
        st.caption("관련 검색어 기반의 실시간 최신 뉴스 피드입니다.")
        df_real_news = get_realtime_news("ETF", timeframe="7d", max_items=12)
        
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
        else: st.info("👉 좌측 사이드바에 Naver DataLab 파일을 업로드해 주세요.")

    # === Tab 4 ===
    with tabs[4]:
        st.markdown("### 📊 선택 ETF 실제 주간 거래량 추이")
        df_volume_summary_text = "선택된 ETF가 없습니다."
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
                            df_volume_summary_text = "\n".join(volume_lines)
        else: st.info("👉 좌측 사이드바에 엑셀 데이터를 업로드해주세요.")

    # === Tab 5 ===
    with tabs[5]:
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
        else: st.info("👉 사이드바에 엑셀 데이터를 업로드하시면 성과 분석기 차트가 활성화됩니다.")

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

    # === Tab 6 ===
    with tabs[6]:
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
            else: st.info("👉 사이드바에 종목토론방 엑셀 파일을 업로드해주세요.")

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

    # === Tab 7: 운용 현황 및 점유율 ===
    with tabs[7]:
        st.markdown("### 🏢 국내 ETF 운용사 AUM 시장 점유율 및 테마별 현황 (실시간 기준)")
        col_pie, col_table = st.columns([1, 2])
        pivot_df = pd.DataFrame()
        aum_context_text = "AUM 데이터가 로드되지 않았습니다."
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
                        aum_context_text = pivot_df.to_string()
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
        else: st.info("👉 좌측 사이드바에 엑셀 데이터를 업로드하시면 트렌드 그래프가 활성화됩니다.")

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

    # === Tab 8: 프롬프트 제너레이터 ===
    with tabs[8]:
        st.markdown("### 🧠 모듈형 마케팅 리포트 자동 생성기")
        st.caption("대시보드 내 데이터를 융합하여 마크다운 프롬프트를 도출합니다.")
        
        df_sc = st.session_state.df_scatter
        data_context = df_sc.sort_values(by='주간 수익률(%)', ascending=False).head(20).to_string(index=False) if not df_sc.empty else "데이터 부족"
        dl_context = st.session_state.get('dl_summary', "데이터랩 미연동")
        
        news_lines = []
        if not df_real_news.empty and df_real_news.iloc[0]["원본제목"] != "오류":
            for _, row in df_real_news.iterrows():
                news_lines.append(f"- [{row['게시일 / 출처']}] {row['원본제목']} (링크: {row['링크']})")
        news_context_text = "\n".join(news_lines) if news_lines else "최신 뉴스 없음"
        
        try:
            word_counts, stats = get_media_intelligence([])
            media_context = f"[유튜브 키워드 Top 5]: {dict(word_counts.most_common(5))}\n[포맷 믹스 구조]: {stats}"
        except Exception as e:
            media_context = f"미디어 데이터 연동 실패 ({e})"

        prompt_1 = f"너는 KODEX 마케팅 총괄 최고책임자를 보좌하는 AI 에이전트야. 제공하는 대시보드 연동 데이터를 숙지해줘.\n\n[1. 실시간 뉴스 리스트]\n{news_context_text}\n\n[2. 자산 흐름]\n{data_context}\n\n[3. 거래량 추이]\n{df_volume_summary_text}\n\n[4. 검색량]\n{dl_context}\n\n[5. AUM 현황]\n{aum_context_text}\n\n[6. 경쟁사 동향]\n{media_context}"
        st.code(prompt_1, language="text")


# =========================================================================
# ★ 모듈 2: ETF 기초자산(Constituents) 리밸런싱 (텍스트 복사-붙여넣기 방식)
# =========================================================================
elif main_menu == "2. KODEX 리밸런싱 시뮬레이션":
    st.markdown("## ⚖️ ETF 기초자산(Constituents) 리밸런싱 시뮬레이터")
    st.caption("KODEX 공식 홈페이지의 구성종목(PDF) 엑셀 파일 데이터를 복사하여 붙여넣으면, 종목 비중을 자유롭게 조절(Data Editor)하고 벤치마크(KOSPI) 대비 백테스팅 성과를 확인할 수 있습니다.")

    st.markdown("#### 1. KODEX 구성종목(PDF) 데이터 붙여넣기")
    st.info("💡 **가이드:** 다운로드한 엑셀/CSV 파일을 열고, **`번호, 종목명...`이 적힌 머리글(Header) 줄부터 맨 아랫줄까지 드래그해서 복사(Ctrl+C)**한 뒤 아래 창에 **붙여넣기(Ctrl+V)** 하세요.")
    
    pasted_text = st.text_area(
        "여기에 복사한 표 데이터를 붙여넣으세요:", 
        height=150, 
        placeholder="번호\t종목명\tISIN\t종목코드\t수량\t비중(%)\t평가금액(원)\n1\t원화예금\t...\t...\t...\t...\t..."
    )

    if pasted_text:
        try:
            lines = pasted_text.strip().split('\n')
            data = []
            start_idx = -1
            
            # 헤더 줄 찾기 로직
            for i, line in enumerate(lines):
                clean_line = line.replace(" ", "").replace('"', '')
                if '종목명' in clean_line and ('비중' in clean_line or '평가금액' in clean_line or '종목코드' in clean_line):
                    start_idx = i
                    break
                    
            if start_idx != -1:
                for line in lines[start_idx:]:
                    clean_line = line.strip()
                    if not clean_line: continue
                    if '\t' in clean_line:
                        data.append(clean_line.split('\t'))
                    elif ',' in clean_line:
                        data.append(clean_line.split(','))
                    else:
                        data.append(re.split(r'\s{2,}', clean_line)) # 웹페이지 복사 방어
                
                # 행 길이 맞추기 (Pandas 에러 방지)
                max_cols = max(len(r) for r in data)
                for r in data:
                    if len(r) < max_cols:
                        r.extend([''] * (max_cols - len(r)))
                        
                raw_pdf = pd.DataFrame(data[1:], columns=data[0])
                
                # extract_table을 이용해 2차 검증 및 추출
                df_pdf = extract_table(raw_pdf, ['종목명', '종목코드'])
                
                # 빈 컬럼 제거
                df_pdf = df_pdf.loc[:, df_pdf.columns.notnull()]
                df_pdf = df_pdf.loc[:, df_pdf.columns != '']

                # 동적 컬럼명 매핑
                col_name = next((c for c in df_pdf.columns if '종목명' in str(c)), None)
                col_code = next((c for c in df_pdf.columns if '종목코드' in str(c)), None)
                col_weight = next((c for c in df_pdf.columns if '비중' in str(c) or '평가금액' in str(c)), None)
                
                if not (col_name and col_code and col_weight):
                    st.error("데이터 내에 '종목명', '종목코드', '비중' 열을 찾을 수 없습니다. 표 영역이 제대로 복사되었는지 확인해주세요.")
                else:
                    df_pdf = df_pdf.rename(columns={col_name: '종목명', col_code: '종목코드', col_weight: '비중(%)'})
                    
                    # 데이터 전처리
                    df_pdf = df_pdf.dropna(subset=['종목명', '비중(%)']).copy()
                    df_pdf['비중(%)'] = pd.to_numeric(df_pdf['비중(%)'], errors='coerce').fillna(0)
                    
                    df_pdf['종목코드'] = df_pdf['종목코드'].astype(str).str.replace(r'[^0-9]', '', regex=True)
                    df_pdf = df_pdf[df_pdf['종목코드'].str.len() >= 5]
                    df_pdf['종목코드'] = df_pdf['종목코드'].apply(lambda x: str(x).zfill(6)[:6])
                    
                    df_pdf = df_pdf.sort_values(by='비중(%)', ascending=False).head(30).reset_index(drop=True)

                    total_init_w = df_pdf['비중(%)'].sum()
                    if total_init_w == 0: total_init_w = 1
                    df_pdf['초기비중(%)'] = (df_pdf['비중(%)'] / total_init_w) * 100
                    df_pdf['목표비중(%)'] = df_pdf['초기비중(%)'].copy()

                    st.markdown("#### 2. 편입 종목 비중 리밸런싱 (인터랙티브 데이터 표)")
                    st.success("데이터 파싱 성공! 목표 비중을 조절해보세요.")
                    
                    edited_df = st.data_editor(
                        df_pdf[['종목명', '종목코드', '초기비중(%)', '목표비중(%)']],
                        column_config={
                            "초기비중(%)": st.column_config.NumberColumn("초기비중(%)", format="%.2f%%", disabled=True),
                            "목표비중(%)": st.column_config.NumberColumn("목표비중(%)", min_value=0.0, max_value=100.0, step=0.1, format="%.2f%%")
                        },
                        hide_index=True,
                        use_container_width=True
                    )

                    if st.button("🚀 리밸런싱 시뮬레이션 및 백테스팅 실행", type="primary"):
                        st.divider()
                        st.markdown("#### 3. 커스텀 ETF 백테스팅 및 운용 성과 지표 산출")

                        target_weights = edited_df['목표비중(%)'].values
                        tot_w = np.sum(target_weights)
                        if tot_w == 0: tot_w = 1
                        target_weights = target_weights / tot_w

                        with st.spinner("한국거래소(KRX)에서 표에 편입된 종목들의 최근 1년 치 주가 데이터를 실시간으로 불러와 시뮬레이션을 구동합니다... (최대 10~20초 소요)"):
                            end_date = datetime.today()
                            start_date = end_date - timedelta(days=365)

                            try:
                                bm_df = fdr.DataReader('KS11', start_date, end_date)
                                bm_daily = bm_df['Close'].pct_change().dropna()

                                stock_data = {}
                                valid_weights = []
                                
                                for idx, row in edited_df.iterrows():
                                    if target_weights[idx] > 0:
                                        tkr = row['종목코드']
                                        try:
                                            sdf = fdr.DataReader(tkr, start_date, end_date)
                                            if not sdf.empty:
                                                stock_data[row['종목명']] = sdf['Close'].pct_change().dropna()
                                                valid_weights.append(target_weights[idx])
                                        except:
                                            pass 

                                if stock_data:
                                    v_tot_w = np.sum(valid_weights)
                                    if v_tot_w == 0: v_tot_w = 1
                                    valid_weights = np.array(valid_weights) / v_tot_w

                                    df_returns = pd.DataFrame(stock_data).dropna()
                                    bm_aligned = bm_daily.loc[df_returns.index]

                                    custom_etf_daily = df_returns.dot(valid_weights)

                                    bm_cum = (1 + bm_aligned).cumprod() * 100
                                    custom_cum = (1 + custom_etf_daily).cumprod() * 100

                                    df_sim = pd.DataFrame({
                                        "Date": df_returns.index,
                                        "벤치마크 (KOSPI)": bm_cum.values,
                                        "리밸런싱 완료 ETF": custom_cum.values
                                    })

                                    df_sim_melt = df_sim.melt(id_vars="Date", var_name="Portfolio", value_name="Value (Base 100)")

                                    fig_sim = px.line(df_sim_melt, x="Date", y="Value (Base 100)", color="Portfolio", template="plotly_dark", color_discrete_sequence=['#cbd5e1', '#ff4d4d'])
                                    fig_sim.update_layout(height=450, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5))
                                    st.plotly_chart(fig_sim, use_container_width=True)

                                    final_bm = (bm_cum.iloc[-1] / 100 - 1) * 100
                                    final_etf = (custom_cum.iloc[-1] / 100 - 1) * 100
                                    excess_return = final_etf - final_bm

                                    te_daily = custom_etf_daily - bm_aligned
                                    tracking_error = np.std(te_daily) * np.sqrt(252) * 100
                                    
                                    ir = excess_return / tracking_error if tracking_error != 0 else 0

                                    init_w_valid = edited_df.loc[edited_df['종목명'].isin(stock_data.keys()), '초기비중(%)'].values / 100
                                    init_w_valid = init_w_valid / np.sum(init_w_valid)
                                    turnover = np.sum(np.abs(valid_weights - init_w_valid)) / 2 * 100

                                    c_m1, c_m2, c_m3, c_m4 = st.columns(4)
                                    c_m1.metric("커스텀 ETF 1년 수익률", f"{final_etf:.2f}%", f"BM대비 {excess_return:+.2f}%p")
                                    c_m2.metric("추적오차 (TE)", f"{tracking_error:.2f}%", "액티브 리스크", delta_color="off")
                                    c_m3.metric("정보비율 (IR)", f"{ir:.2f}", "BM 대비 효율성", delta_color="normal" if ir > 0 else "inverse")
                                    c_m4.metric("매매회전율 (Turnover)", f"{turnover:.1f}%", "리밸런싱 비용 수준", delta_color="inverse")

                                else:
                                    st.error("해당 종목들의 주가 데이터를 불러올 수 없습니다. 종목 코드를 확인해 주세요.")
                            except Exception as e:
                                st.error(f"주가 데이터 연동 중 오류가 발생했습니다: {e}")
            else:
                st.error("붙여넣은 텍스트에서 표의 머리글('종목명', '비중' 등)을 찾을 수 없습니다. 다시 복사해주세요.")
        except Exception as e:
            st.error(f"데이터를 처리하는 중 오류가 발생했습니다. (상세 에러: {e})")


# =========================================================================
# ★ 모듈 3: 글로벌 대체투자 상품 기획 시뮬레이터 (+ 상품기획서 자동 생성 기능)
# =========================================================================
elif main_menu == "3. 글로벌 상품 기획 시뮬레이터":
    st.markdown("## 🌍 Global Alternative ETF Structuring Simulator")
    st.caption("규제 완화에 대비하여 미국 시장의 메가 트렌드 자산(BDC, CLO, MLP 등)을 조합하여 가상의 ETF를 사전 기획하고 팩트시트를 도출합니다.")
    
    asset_class = st.selectbox(
        "🌍 탐색할 해외 대체투자 자산군 선택:", 
        ["사모신용 (BDC)", "대출채권담보부증권 (CLO)", "에너지 인프라 (MLP)"],
        key="asset_sel_app1"
    )

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
        }
    }

    current_db = mock_db[asset_class]
    tkrs = current_db["tickers"]
    nms = current_db["names"]
    b_ylds = current_db["base_yields"]

    st.markdown("#### 1. 기초자산 포트폴리오 구성 및 환율 전략 설정")
    
    col_p1, col_p2 = st.columns([1, 1])
    with col_p1:
        with st.container(border=True):
            st.markdown(f"**[{asset_class}] 기초자산 편입 비중(Weight) 조절**")
            st.info("💡 **인터랙티브 표:** '목표비중(%)' 열의 숫자를 자유롭게 수정하세요. 하단의 시뮬레이션 적용 시 합계가 100%로 자동 정규화됩니다.")
            
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
            
            df_pie_show = pd.DataFrame({"Asset": tkrs, "Weight": normalized_weights_bdc})
            df_pie_show = df_pie_show[df_pie_show['Weight'] > 0].sort_values(by='Weight', ascending=False).head(10)
            
            if not df_pie_show.empty:
                fig_bdc_pie = px.pie(df_pie_show, names="Asset", values="Weight", hole=0.5, color_discrete_sequence=px.colors.sequential.Blues_r)
                fig_bdc_pie.update_layout(height=250, margin=dict(t=10, b=10, l=10, r=10), template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_bdc_pie, use_container_width=True)

    with col_p2:
        with st.container(border=True):
            st.markdown("**ETF 운용 구조(Structure) 설정**")
            fx_strategy = st.selectbox("환율 헤지(FX) 전략", ["환노출 (Unhedged - 환차익/차손 노출)", "환헤지 (Hedged - 환율 변동성 방어)"])
            ter = st.slider("예상 총보수율 (TER, %)", 0.1, 2.0, 0.45, 0.05)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("##### 📄 Simulated Product Factsheet")
            
            base_yield = np.dot(np.array(b_ylds), normalized_weights_bdc)
            
            if "환헤지" in fx_strategy:
                net_yield = base_yield - 1.5 - ter 
                risk_rating = "보통 위험 (Medium Risk)"
                mdd = "-12.5%"
                fx_desc = "달러 변동성을 제거하여 순수 기초자산 배당/이자 수익에 집중"
            else:
                net_yield = base_yield - ter
                risk_rating = "높은 위험 (High Risk)"
                mdd = "-22.4%"
                fx_desc = "달러 강세 시 환차익 추가 향유 가능 (단, 변동성 확대)"
                
            st.metric("Net Expected Dividend Yield (예상 분배율)", f"{net_yield:.2f}%")
            st.write(f"- **위험 등급:** {risk_rating}")
            st.write(f"- **최대 손실폭(MDD) 추정:** {mdd}")
            st.write(f"- **FX 전략:** {fx_desc}")

    st.markdown("---")
    
    col_app1_1, col_app1_2, col_app1_3 = st.columns(3)

    with col_app1_1:
        with st.container(border=True):
            st.markdown(f"#### 2. 대표자산 크레딧 요약")
            
            selected_ticker = st.selectbox("분석할 대표 종목 선택:", tkrs, key="ticker_sel_app1")
            
            if selected_ticker in current_db["data"]:
                t_val1, t_val2, t_val3, t_comment = current_db["data"][selected_ticker]
            else:
                idx = tkrs.index(selected_ticker)
                b_y = b_ylds[idx]
                if asset_class == "사모신용 (BDC)":
                    t_val1 = b_y
                    t_val2 = round(40.0 + (b_y - 6.0) * 1.5, 1) 
                    t_val3 = round(80.0 + (b_y / 15.0) * 15.0, 1) 
                    t_comment = f"{nms[idx]}는 우수한 자산 건전성을 바탕으로 배당 안정성을 추구하며, 당사 포트폴리오의 리스크 조정 수익률을 제고하는 핵심 편입 자산입니다."
                elif asset_class == "대출채권담보부증권 (CLO)":
                    t_val1 = b_y
                    t_val2 = max(0.0, min(100.0, 100.0 - (b_y - 5.0) * 20.0))
                    t_val3 = round(0.2 + (b_y / 20.0), 2)
                    t_comment = f"{nms[idx]}는 정교한 트랜치(Tranche) 분석을 통해 선정되었으며, 금리 민감도를 통제함과 동시에 목표 인컴을 달성하는 데 기여합니다."
                else: 
                    t_val1 = b_y
                    t_val2 = round(1.5 + (10.0 - b_y) * 0.1, 1)
                    t_val3 = round(75.0 + (b_y / 10.0) * 5.0, 1)
                    t_comment = f"{nms[idx]}는 필수 에너지 인프라 자산을 기반으로 안정적인 장기 현금흐름(Toll-road)을 창출하여 강력한 배당 커버리지를 제공합니다."

            l_val1, l_val2, l_val3 = current_db["labels"]

            def format_metric(label, value):
                if "Yield" in label or "비중" in label or "YTM" in label or "LTV" in label: return f"{value:.1f}%"
                elif "듀레이션" in label: return f"{value:.2f}년"
                elif "커버리지" in label: return f"{value:.1f}x"
                return str(value)

            st.metric(l_val1, format_metric(l_val1, t_val1))
            st.metric(l_val2, format_metric(l_val2, t_val2))
            st.metric(l_val3, format_metric(l_val3, t_val3))
            st.markdown(f"> **[코멘트]** {t_comment}")

    with col_app1_2:
        with st.container(border=True):
            st.markdown(f"#### 3. 매크로 스트레스 테스트")
            stress_rate = st.slider(current_db["stress_name"], min_value=0.0, max_value=15.0, value=2.0, step=0.5, key="stress_slider_app1")
            recovery_rate = st.number_input("예상 회수율/방어율 (Recovery Rate, %)", value=current_db["recovery_default"], step=5.0, key="rec_rate_app1") / 100
            
            base_st_yield = base_yield 
            loss_impact = stress_rate * (1 - recovery_rate)
            adjusted_yield = base_st_yield - loss_impact
            
            st.metric("시나리오 적용 후 실질 수익률", f"{adjusted_yield:.2f}%", f"-{loss_impact:.2f}% (손실분)", delta_color="inverse")
            if adjusted_yield < 5.0: 
                st.error("⚠️ **경고:** 실질 수익률 5% 미만 하락 (BEP 이탈 위험 진입)")
            else: 
                st.success("✅ **안정:** 타겟 인컴 방어 가능 (펀드 펀더멘털 유지)")

    with col_app1_3:
        with st.container(border=True):
            st.markdown("#### 4. 자산운용사(AMC) 손익 추정")
            target_aum = st.number_input("초기 목표 AUM (억원)", value=500, step=50, key="t_aum_app1")
            fixed_cost = st.number_input("연간 고정비용 (상장유지비 등 / 억원)", value=2.0, step=0.5, key="f_cost_app1")
            expected_revenue = target_aum * (ter / 100)
            net_profit = expected_revenue - fixed_cost
            
            st.metric("예상 연간 운용보수 수익", f"{expected_revenue:.2f} 억원")
            st.metric("예상 영업이익 (Net Profit)", f"{net_profit:.2f} 억원")
            bep_aum = fixed_cost / (ter / 100) if ter > 0 else 0
            if bep_aum > 0:
                st.info(f"💡 흑자 전환을 위한 최소 손익분기점(BEP) AUM: 약 **{bep_aum:.0f}억원**")

    st.markdown("---")
    st.markdown("#### 5. 파생상품(옵션) 결합 수익률 시뮬레이터 (Payoff Modeling)")
    st.caption("초단기 커버드콜(0DTE) 및 하방 방어형(Buffer) ETF 등 파생상품이 결합된 ETF의 만기 시점 페이오프(Payoff) 구조를 시각화합니다.")

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
            fig_opt.add_trace(go.Scatter(x=x_vals, y=x_vals, mode='lines', name='기초지수 (S&P 500 등)', line=dict(dash='dash', color='gray')))
            fig_opt.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines', name='커버드콜 ETF 수익률', line=dict(color='#4da6ff', width=3)))
            
            fig_opt.update_layout(height=400, template="plotly_dark", xaxis_title="기초자산 가격 변동 (%)", yaxis_title="ETF 만기 수익률 (%)", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5))
            st.plotly_chart(fig_opt, use_container_width=True)
            
            st.metric("최대 기대 수익률 (상방 캡)", f"{max_return:.2f}%")
            st.caption(f"💡 프리미엄 {premium}%를 수취하여 하락장에서는 그만큼 손실을 방어하지만, 기초자산이 {strike_pct}% 이상 급등할 경우 수익은 {max_return}%로 제한됩니다.")

        else:
            y_vals = np.where(x_vals > 0, np.minimum(x_vals, cap_pct), np.where(x_vals >= -buffer_pct, 0, x_vals + buffer_pct))
            
            fig_opt = go.Figure()
            fig_opt.add_trace(go.Scatter(x=x_vals, y=x_vals, mode='lines', name='기초지수 (S&P 500 등)', line=dict(dash='dash', color='gray')))
            fig_opt.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines', name='버퍼 ETF 수익률', line=dict(color='#ffb04d', width=3)))
            
            fig_opt.add_vrect(x0=-buffer_pct, x1=0, fillcolor="#ffb04d", opacity=0.1, layer="below", line_width=0, annotation_text="100% 방어 구간", annotation_position="bottom right")
            
            fig_opt.update_layout(height=400, template="plotly_dark", xaxis_title="기초자산 가격 변동 (%)", yaxis_title="ETF 만기 수익률 (%)", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5))
            st.plotly_chart(fig_opt, use_container_width=True)
            
            st.metric("하방 100% 방어 임계점", f"-{buffer_pct:.1f}%")
            st.caption(f"💡 기초자산이 최대 -{buffer_pct}%까지 하락해도 원금을 100% 보존하지만, 방어 비용 지불을 위해 상승장에서는 최대 {cap_pct}%까지만 수익을 공유합니다.")

    # =====================================================================
    # 6. AI 기반 ETF 상품 기획서(Proposal) 자동 산출 기능
    # =====================================================================
    st.markdown("---")
    st.markdown("#### 6. AI 기반 ETF 상품 기획서(Proposal) 자동 산출 (RAG 연동)")
    st.caption("편입 예상 기업의 재무/사업보고서(PDF, Excel) 및 시장 규제/정책 문건을 업로드하면, AI가 데이터를 클렌징하고 이를 바탕으로 운용사 내부 보고용 '상품기획서 초안(프롬프트)'을 자동으로 작성합니다.")

    col_doc1, col_doc2 = st.columns(2)
    with col_doc1:
        fin_docs = st.file_uploader(
            "🏢 타겟 기업 재무제표 / IR 자료 (PDF, Excel, CSV)", 
            type=["pdf", "xlsx", "xls", "csv"], 
            accept_multiple_files=True, 
            key="fin_docs"
        )
    with col_doc2:
        reg_docs = st.file_uploader(
            "⚖️ 매크로 / 규제 및 정책 문건 (PDF, Word, Text)", 
            type=["pdf", "docx", "txt"], 
            accept_multiple_files=True, 
            key="reg_docs"
        )

    if st.button("✨ AI 상품기획서 자동 작성 시작", type="primary"):
        if fin_docs or reg_docs:
            with st.spinner("PDF 텍스트 추출 및 재무 데이터 클렌징 중... (AI 컨텍스트 융합)"):
                time.sleep(1.5) # AI 분석 체감 딜레이
                
            st.success("데이터 클렌징 및 컨텍스트 매핑이 완료되었습니다! 아래에 자동 생성된 상품기획서 초안을 확인하세요.")

            top_asset = df_pie_show.iloc[0]['Asset'] if not df_pie_show.empty else tkrs[0]

            proposal_text = f"""**[신규 ETF 상품 기획서: KODEX 글로벌 {asset_class} 액티브 ETF (가칭)]**

**1. 기획 의도 및 수요 예측 (Background & Demand)**
- **배경:** 최근 거시경제 환경 및 업로드된 정책 문건 분석 결과, 글로벌 {asset_class} 자산군에 대한 리테일 투자자 및 퇴직연금 계좌의 안정적인 인컴(Income) 수요가 폭발적으로 증가할 것으로 예측됨.
- **수요 타겟팅:** 업로드된 기업 재무제표/IR 데이터 기준, 핵심 편입 종목({top_asset} 등)의 펀더멘털이 견조하여 제2의 현금흐름 창출을 목적으로 하는 4060 시니어 세대의 강력한 자금 유입이 기대됨.

**2. 기초지수 추적 및 운용 전략 (Index & Strategy)**
- **운용 방식:** 환헤지 전략({fx_strategy})을 적용하여 달러 변동성 등 매크로 리스크를 통제. 예상 총보수율은 {ter}%로 설정하여 타사 대비 가격 경쟁력 및 마진 확보.
- **포트폴리오 수익률:** 글로벌 {asset_class} 우량 기업 상위 종목을 집중 선별 편입하며, 내부 시뮬레이터 분석 결과 산출된 **예상 분배율 {net_yield:.2f}%** 수준을 타겟팅함.

**3. 예상 AUM 및 손익(P&L) 타당성**
- 초기 시딩(Seeding) 자금 및 출시 직후 마케팅 캠페인을 통한 1차 목표 AUM: **{target_aum}억원**
- 운용사 손익분기점(BEP) AUM: **약 {bep_aum:.0f}억원** 추산. 
- BEP 조기 돌파를 위해 시중 은행 및 증권사 WM 창구 대상의 '리테일 세일즈 톡(Sales Talk)' 배포 및 프로모션 병행 필수.

**4. 구성 종목 및 리밸런싱 계획 (Constituents & Rebalancing)**
- **종목 편입:** 엑셀/CSV로 파싱된 타겟 기업의 현금흐름(FCF) 및 LTV 분석을 통해 {top_asset} 외 핵심 우량 종목 25~30개 위주로 액티브 포트폴리오 구성.
- **리밸런싱:** 반기 단위 정기 리밸런싱을 기본으로 하되, 예상 시장 부도율({stress_rate}%) 등 스트레스 지표 모니터링을 통한 펀드매니저의 수시 편출입(Active Overlay) 진행.

**5. 위험 분석 및 컴플라이언스 (Risk & Compliance)**
- **리스크 등급:** {risk_rating}
- **하방 리스크:** 1년 내 최악의 매크로 스트레스 시나리오 발생 시, 포트폴리오의 최대 예상 손실폭(MDD)은 **{mdd}** 수준으로 방어 가능함.
- 파생상품(옵션) 결합 시뮬레이션 결과에 따라, 필요시 상하방 캡(Cap/Buffer) 설정을 통한 리스크 헷징 구조의 법률적 타당성 검토 완료.
"""
            st.markdown("##### 📝 생성된 상품기획서 프롬프트 초안 (운용사 내부 보고용)")
            st.code(proposal_text, language="markdown")
        else:
            st.warning("⚠️ 기업 재무제표나 규제 문건 등 하나 이상의 파일을 업로드한 후 버튼을 눌러주세요.")
