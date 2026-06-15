import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import FinanceDataReader as fdr
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import json 
import time

# 1. 페이지 레이아웃 및 기본 테마 설정 (사이드바 기본 숨김 처리)
st.set_page_config(page_title="ETF Monitoring AI Agent", layout="wide", initial_sidebar_state="collapsed")

# 전역 데이터 변수
df_scatter = pd.DataFrame()

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

@st.cache_data(ttl=1800)
def get_macro_snapshot():
    snapshot = {
        "indices": {
            "코스피": {"val": "2,750.20", "delta": "+15.30", "pct": "+0.56%", "is_up": True},
            "코스닥": {"val": "860.50", "delta": "-2.10", "pct": "-0.24%", "is_up": False},
            "S&P 500": {"val": "5,304.72", "delta": "-10.20", "pct": "-0.19%", "is_up": False},
            "나스닥": {"val": "18,920.58", "delta": "-45.10", "pct": "-0.26%", "is_up": False},
            "다우존스": {"val": "38,500.12", "delta": "+50.20", "pct": "+0.13%", "is_up": True}
        },
        "forex": {
            "미국 USD": {"val": "1,365.50", "delta": "+2.50", "pct": "+0.18%", "is_up": True},
            "일본 JPY 100": {"val": "875.20", "delta": "-1.50", "pct": "-0.17%", "is_up": False},
            "유럽연합 EUR": {"val": "1,480.12", "delta": "+3.10", "pct": "+0.21%", "is_up": True},
            "중국 CNY": {"val": "188.40", "delta": "-0.50", "pct": "-0.26%", "is_up": False},
            "영국 GBP": {"val": "1,740.50", "delta": "+5.20", "pct": "+0.30%", "is_up": True},
            "호주 AUD": {"val": "910.30", "delta": "+1.10", "pct": "+0.12%", "is_up": True}
        },
        "rates": {
            "콜금리": {"val": "3.520%", "delta": "+0.010", "pct": "+0.28%", "is_up": True},
            "CD(91일)": {"val": "3.610%", "delta": "+0.020", "pct": "+0.55%", "is_up": True},
            "국고채(3년)": {"val": "3.415%", "delta": "-0.012", "pct": "-0.35%", "is_up": False}
        },
        "others": {
            "VIX 지수": {"val": "13.45", "delta": "+0.25", "pct": "+1.89%", "is_up": True},
            "금 가격": {"val": "$2,350.10", "delta": "-5.50", "pct": "-0.23%", "is_up": False},
            "비트코인 (BTC)": {"val": "₩99,089,024", "delta": "+1,200,000", "pct": "+1.22%", "is_up": True}
        }
    }
    
    try:
        end = datetime.today()
        start = end - timedelta(days=10)
        
        df_usd = fdr.DataReader('USD/KRW', start, end)
        if len(df_usd) >= 2:
            c, p = df_usd['Close'].iloc[-1], df_usd['Close'].iloc[-2]
            snapshot["forex"]["미국 USD"] = {"val": f"{c:,.2f}", "delta": f"{c-p:+,.2f}", "pct": f"{(c-p)/p*100:+.2f}%", "is_up": c >= p}
            
        df_ks = fdr.DataReader('KS11', start, end)
        if len(df_ks) >= 2:
            c, p = df_ks['Close'].iloc[-1], df_ks['Close'].iloc[-2]
            snapshot["indices"]["코스피"] = {"val": f"{c:,.2f}", "delta": f"{c-p:+,.2f}", "pct": f"{(c-p)/p*100:+.2f}%", "is_up": c >= p}
            
        df_btc = fdr.DataReader('BTC/KRW', start, end)
        if len(df_btc) >= 2:
            c, p = df_btc['Close'].iloc[-1], df_btc['Close'].iloc[-2]
            snapshot["others"]["비트코인 (BTC)"] = {"val": f"₩{c:,.0f}", "delta": f"{c-p:+,.0f}", "pct": f"{(c-p)/p*100:+.2f}%", "is_up": c >= p}
    except: pass
    return snapshot

def render_compact_metric(title, data):
    color = "#ff4d4d" if data['is_up'] else "#4da6ff"
    arrow = "▲" if data['is_up'] else "▼"
    delta_str = str(data['delta']).replace('+', '').replace('-', '')
    
    return f"""
    <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 12px 16px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <div style="color: #cbd5e1; font-size: 15px; font-weight: 600;">{title}</div>
        <div style="text-align: right;">
            <div style="color: #ffffff; font-size: 17px; font-weight: 800;">{data['val']}</div>
            <div style="color: {color}; font-size: 12px; font-weight: 600; margin-top: 2px;">{arrow} {delta_str} ({data['pct']})</div>
        </div>
    </div>
    """

@st.cache_data(ttl=3600)
def get_realtime_news(keyword="ETF", timeframe="7d", max_items=5):
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

@st.cache_data(ttl=3600)
def get_event_news(keyword, start_date, end_date, max_items=4):
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = (end_date + timedelta(days=1)).strftime("%Y-%m-%d")
    url = f"https://news.google.com/rss/search?q={keyword}+after:{start_str}+before:{end_str}&hl=ko&gl=KR&ceid=KR:ko"
    try:
        res = requests.get(url, timeout=5)
        root = ET.fromstring(res.text)
        news_list = []
        for item in root.findall('./channel/item'):
            title = item.find('title').text if item.find('title') is not None else "제목 없음"
            link = item.find('link').text if item.find('link') is not None else ""
            pubDate = item.find('pubDate').text[5:16] if item.find('pubDate') is not None else ""
            source = item.find('source').text if item.find('source') is not None else "Google News"
            news_list.append({"게시일 / 출처": f"{pubDate} / {source}", "원본제목": title, "링크": link})
            if len(news_list) >= max_items: break
        return pd.DataFrame(news_list)
    except: return pd.DataFrame()

@st.cache_data(ttl=1800)
def get_competitor_blog(blog_id):
    url = f"https://rss.blog.naver.com/{blog_id}.xml"
    try:
        res = requests.get(url, timeout=5)
        root = ET.fromstring(res.content)
        posts = []
        for item in root.findall('./channel/item')[:3]: 
            title = item.find('title').text
            link = item.find('link').text
            posts.append((title, link))
        if not posts: return [("최신 게시글이 없습니다.", "https://blog.naver.com/" + blog_id)]
        return posts
    except: return [("실시간 연동 지연 (클릭 시 이동)", "https://blog.naver.com/" + blog_id)]

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

def generate_market_sentiment(news_df):
    if news_df.empty or news_df["원본제목"].iloc[0].startswith("'"): 
        return "<ul><li>뉴스 데이터가 충분하지 않아 시장 심리를 분석할 수 없습니다.</li></ul>"
    all_titles = " ".join(news_df["원본제목"].astype(str).tolist())
    bullet1 = "<li>📈 <b>전반적 흐름</b>: "
    bullet2 = "<li>💡 <b>수급 모멘텀</b>: "
    bullet3 = "<li>⚠️ <b>투자자 심리</b>: "
    if any(kw in all_titles for kw in ['강세', '상승', '급등', '반등']): 
        bullet1 += "시장 상승세 속에서 금리 인하 기대감이 시장을 주도하고 있습니다.</li>"
        bullet2 += "성장주 및 고배당 ETF를 중심으로 자금 유입이 뚜렷하게 나타납니다.</li>"
        bullet3 += "단기 차익 실현보다는 중장기적 관점의 매수 심리가 우세합니다.</li>"
    elif any(kw in all_titles for kw in ['하락', '약세', '급락', '둔화']): 
        bullet1 += "금리 및 매크로 우려 재점화로 시장 변동성이 확대되는 구간입니다.</li>"
        bullet2 += "채권 및 인버스 ETF 등 방어적 포트폴리오로 자금이 이동하고 있습니다.</li>"
        bullet3 += "위험 자산 회피 심리가 강해지며 관망세가 짙어지고 있습니다.</li>"
    else: 
        bullet1 += "특별한 상승/하락 모멘텀 없이 시장 전반이 혼조세를 보이고 있습니다.</li>"
        bullet2 += "섹터별, 테마별로 짧은 주기의 순환매 장세가 지속 중입니다.</li>"
        bullet3 += "명확한 방향성이 부재하여 투자자들의 신중한 접근이 요구됩니다.</li>"
    return f"<ul style='margin-bottom:0;'>{bullet1}{bullet2}{bullet3}</ul>"

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
# ★ 메인 화면 분할 (메인 85% / 우측 컨트롤 타워 15%)
# =========================================================================
col_main, col_spacing, col_right = st.columns([4.5, 0.1, 0.8])

# ---------------------------------------------------------
# [우측 패널] 타이틀 & 데이터 컨트롤 센터
# ---------------------------------------------------------
with col_right:
    st.markdown(
        """
        <div style='text-align: right; margin-bottom: 25px; margin-top: 5px;'>
            <h2 style='font-weight: 800; font-size: 36px; line-height: 1.1; letter-spacing: -1px; background: linear-gradient(to left, #ffffff, #93c5fd); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
                ETF Monitoring<br>AI Agent
            </h2>
            <p style='color:#94a3b8; font-size:12px; margin-top:5px;'>Data Intelligence Dashboard</p>
        </div>
        """, unsafe_allow_html=True
    )

    with st.container(border=True):
        st.markdown("<h4 style='text-align:center; font-size: 16px;'>🎛️ 데이터 컨트롤</h4>", unsafe_allow_html=True)
        st.divider()
        
        available_weeks = ["데이터 없음"]
        uploaded_excel_temp = st.session_state.get('excel_main') 
        
        week_placeholder = st.empty()
        st.divider()
        uploaded_excel = st.file_uploader("📈 ETF 순매수 엑셀", type=["xlsx", "xls"], key="excel_main")
        
        if uploaded_excel is not None:
            try:
                xls = pd.ExcelFile(uploaded_excel)
                sheet_names = [sheet for sheet in xls.sheet_names if sheet != "참고사항"]
                if sheet_names:
                    available_weeks = sheet_names[::-1] 
            except: pass

        default_idx = 1 if len(available_weeks) > 1 else 0
        selected_week = week_placeholder.selectbox("📆 조회 기준 주차", options=available_weeks, index=default_idx)
        
        st.divider()
        # ★ DataLab 검색량 파일을 무제한 다중 선택 가능하도록 accept_multiple_files=True 적용
        uploaded_dls = st.file_uploader("🔍 DataLab 다중 비교", type=["csv", "xlsx", "xls"], key="dl_main", accept_multiple_files=True)

    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:right; color: #64748b; font-size: 10px; letter-spacing: 2px; font-weight: 600; margin-bottom: 10px;'>POWERED BY</p>", unsafe_allow_html=True)
    
    _, col_logo_r = st.columns([1, 1.5])
    with col_logo_r:
        try:
            st.image("20220927092603_1800954_640_640.png", use_container_width=True)
            st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
            st.image("커리어하이 로고(하양).png", use_container_width=True)
        except:
            st.markdown("<p style='text-align:right; color:#94a3b8; font-size:12px;'>삼성자산운용 x 커리어하이</p>", unsafe_allow_html=True)

# ---------------------------------------------------------
# [중앙 화면] 가로형 탭 로직
# ---------------------------------------------------------
with col_main:
    st.session_state.setdefault('dl_summary', "DataLab 데이터가 업로드되지 않았습니다.")
    
    tab_names = [
        "🏠 Home", "📊 Weekly Info", "📈 순매수 & 수익률", "📰 뉴스 & 트렌드", 
        "💸 거래량 추이", "🎉 이벤트 성과", "🗣️ 고객 UX", "🏢 경쟁사 동향", 
        "🥧 AUM 현황", "🇺🇸 글로벌 동향", "🧠 AI 프롬프트"
    ]
    tabs = st.tabs(tab_names)

    # === Tab 0: Home ===
    with tabs[0]:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            """
            <div style='text-align: center; padding: 10px;'>
                <h1 style='font-size: 54px; font-weight: 800; letter-spacing: -1.5px; background: linear-gradient(to right, #ffffff, #93c5fd); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
                    ETF Marketing Intelligence
                </h1>
                <p style='font-size: 19px; color: #94a3b8; margin-top: 15px; font-weight: 400; letter-spacing: -0.5px;'>
                    데이터 기반의 전략적 자금 추적 및 마케팅 의사결정 컨트롤 타워
                </p>
            </div>
            """, unsafe_allow_html=True
        )
        st.markdown("<br>", unsafe_allow_html=True)
        
        macros = get_macro_snapshot()
        
        c_m1, c_m2, c_m3 = st.columns(3)
        with c_m1:
            with st.container(border=True):
                st.markdown("#### 📈 핵심 대표 지수")
                st.divider()
                for key, data in macros["indices"].items():
                    st.markdown(render_compact_metric(key, data), unsafe_allow_html=True)
        with c_m2:
            with st.container(border=True):
                st.markdown("#### 💱 주요 환율")
                st.divider()
                for key, data in macros["forex"].items():
                    st.markdown(render_compact_metric(key, data), unsafe_allow_html=True)
        with c_m3:
            with st.container(border=True):
                st.markdown("#### 🏦 금리 지표")
                st.divider()
                for key, data in macros["rates"].items():
                    st.markdown(render_compact_metric(key, data), unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("#### 📌 기타 주요 지표")
        c_o1, c_o2, c_o3 = st.columns(3)
        with c_o1: st.markdown(render_compact_metric("VIX 지수", macros["others"]["VIX 지수"]), unsafe_allow_html=True)
        with c_o2: st.markdown(render_compact_metric("금 가격", macros["others"]["금 가격"]), unsafe_allow_html=True)
        with c_o3: st.markdown(render_compact_metric("비트코인 (BTC)", macros["others"]["비트코인 (BTC)"]), unsafe_allow_html=True)

    # === Tab 1: Weekly Info ===
    with tabs[1]:
        if uploaded_excel is not None and selected_week != "데이터 없음":
            df_source = load_and_clean_excel(uploaded_excel, selected_week)
            if not df_source.empty and '종목명' in df_source.columns:
                st.markdown("### 🏆 해당 주 순매수 ETF 순위")
                col_subject, col_space, col_slider = st.columns([2, 3, 3])
                with col_subject:
                    target_subject = st.selectbox("주체:", ["개인", "기관", "외국인"], key="main_sub")
                with col_slider:
                    top_n = st.slider("TOP N개 설정", 5, 50, 10, 5, label_visibility="collapsed")
                    st.markdown(f"<p style='text-align:right; color:red; font-weight:bold; margin-top:-10px;'>{top_n}</p>", unsafe_allow_html=True)

                df_filtered = df_source.dropna(subset=[target_subject]).copy()
                df_filtered = df_filtered[df_filtered["종목명"] != "전체"].sort_values(by=target_subject, ascending=False).head(top_n)

                col_table, col_chart = st.columns([4, 5])
                with col_table:
                    st.dataframe(df_filtered[["종목명", target_subject]], use_container_width=True, height=380, hide_index=True)
                with col_chart:
                    fig_etf = px.bar(df_filtered, x=target_subject, y="종목명", orientation='h')
                    fig_etf.update_layout(yaxis={'categoryorder':'total ascending'}, height=380, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_etf, use_container_width=True)

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
                with col_theme_table:
                    st.dataframe(df_pie_data, use_container_width=True, height=400, hide_index=True)
                with col_theme_chart:
                    fig_pie = px.pie(df_pie_data, names='AI_자동_테마', values=target_subject, hole=0.4, color_discrete_sequence=px.colors.sequential.Blues_r)
                    fig_pie.update_traces(textposition='inside', textinfo='percent+label', textfont_size=13, marker=dict(line=dict(color='#000000', width=1)))
                    fig_pie.update_layout(height=400, margin=dict(t=20, l=20, r=20, b=20), template="plotly_dark", showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.warning("업로드된 엑셀 파일의 양식이 올바르지 않습니다.")
        else:
            st.info("👉 우측 패널에 ETF 순매수 엑셀 데이터를 업로드해주세요.")

    # === Tab 2: 순매수 등락, 수익률 ===
    with tabs[2]:
        if uploaded_excel is not None and selected_week != "데이터 없음" and len(available_weeks) > 1:
            st.markdown("### 📈 기간별 ETF 순매수 현황")
            
            col_start, col_text, col_slider, col_space, col_inv = st.columns([1.5, 3, 2.5, 0.5, 1.5])
            with col_start:
                start_week = st.selectbox("시작 주차:", options=available_weeks[::-1], index=0, key="start_week")
            with col_text:
                st.markdown(f"<p style='margin-top: 30px; font-weight: bold;'>부터 &nbsp;&nbsp; {selected_week} 까지의</p>", unsafe_allow_html=True)
            with col_slider:
                top_n_tab2 = st.slider("TOP N개 ETF 순매수 순위:", 10, 100, 50, 10, key="top_n_tab2", label_visibility="collapsed")
                st.markdown(f"<p style='text-align:right; color:red; font-weight:bold; margin-top:-10px;'>{top_n_tab2}</p>", unsafe_allow_html=True)
            with col_inv:
                st.markdown("<div style='margin-bottom:-15px; font-size:13px; color:#94a3b8;'>분석 주체:</div>", unsafe_allow_html=True)
                inv_type_tab2 = st.selectbox("투자자 선택", ["개인", "기관", "외국인"], label_visibility="collapsed", key="inv_type_tab2")
            
            st.divider()

            df_tab2_combined = pd.DataFrame()
            start_idx = available_weeks.index(start_week)
            end_idx = available_weeks.index(selected_week)
            
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
                        fig_total.update_layout(yaxis={'categoryorder':'total ascending'}, height=500, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=10, r=10, t=10, b=10))
                        st.plotly_chart(fig_total, use_container_width=True)

                with col_chart2:
                    st.markdown(f"#### {inv_type_tab2}별 순매수 금액")
                    df_inv = df_tab2_combined.sort_values(by=inv_type_tab2, ascending=False).head(top_n_tab2)
                    with st.container(border=True):
                        fig_inv = px.bar(df_inv, x=inv_type_tab2, y="종목명", orientation='h', color_discrete_sequence=['#ff4d4d'])
                        fig_inv.update_layout(yaxis={'categoryorder':'total ascending'}, height=500, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=10, r=10, t=10, b=10))
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
                                df_scatter = df_scatter_filtered.dropna()
                                
                                fig_scatter = px.scatter(df_scatter, x="주간 수익률(%)", y="순매수 증감률(%)", text="종목명", hover_data=["이번주", "지난주"], title=f"**실제 수익률 vs. {subject_tab2_scatter} 순매수 증감률**")
                                if len(df_scatter) > 1:
                                    x_data = df_scatter["주간 수익률(%)"]
                                    y_data = df_scatter["순매수 증감률(%)"]
                                    r_value = np.corrcoef(x_data, y_data)[0, 1]
                                    z = np.polyfit(x_data, y_data, 1)
                                    p = np.poly1d(z)
                                    
                                    if r_value >= 0.7: r_text = "강한 양(+)의 상관관계"
                                    elif r_value >= 0.3: r_text = "뚜렷한 양(+)의 상관관계"
                                    elif r_value > -0.3: r_text = "유의미한 상관관계 없음"
                                    elif r_value > -0.7: r_text = "뚜렷한 음(-)의 상관관계"
                                    else: r_text = "강한 음(-)의 상관관계"
                                    
                                    fig_scatter.add_scatter(x=x_data, y=p(x_data), mode='lines', name='추세선 (Trendline)', line=dict(color='#ff4d4d', dash='dot'))
                                    st.info(f"💡 **상관관계 분석:** 현재 선택된 종목들의 주간 수익률과 {subject_tab2_scatter} 순매수 증감률 간의 피어슨 상관계수는 **{r_value:.2f}**로, **{r_text}**를 보이고 있습니다.")

                                fig_scatter.update_traces(textposition='top center', marker=dict(size=10, color='#4da6ff', opacity=0.7), textfont=dict(size=11, color='lightgray'))
                                fig_scatter.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.5)
                                fig_scatter.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
                                fig_scatter.update_layout(height=600, template="plotly_dark", xaxis_title="실제 주간 수익률 (%)", yaxis_title=f"{subject_tab2_scatter} 순매수 증감률 (%)", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                                st.plotly_chart(fig_scatter, use_container_width=True)
                else:
                    st.warning("직전 주차 데이터가 없어 증감률을 비교할 수 없습니다.")
        else:
            st.info("👉 우측 패널에 엑셀 데이터를 업로드해주세요. (비교를 위해 2주 이상의 데이터가 필요합니다)")

    # === Tab 3: 뉴스 & 검색 트렌드 (DataLab 다중 업로드 & 자동 2열 그리드 로직) ===
    with tabs[3]:
        st.markdown("### 📰 실시간 마켓 센티먼트 및 뉴스 요약")
        with st.spinner("최신 마켓 트렌드를 AI가 3줄 요약하고 있습니다..."):
            df_real_news = get_realtime_news("ETF", timeframe="7d", max_items=6)
            market_sentiment = generate_market_sentiment(df_real_news)
            st.session_state['market_sentiment'] = market_sentiment
            
            with st.container(border=True):
                st.markdown(f"<div style='font-size:15px; color:#e2e8f0; line-height:1.8; padding:5px;'>{market_sentiment}</div>", unsafe_allow_html=True)
            
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
            else:
                st.dataframe(df_real_news, use_container_width=True, hide_index=True)
                    
        st.divider()
        st.markdown("### 📊 키워드 검색비율 추이 (다중 비교 지원)")
        st.caption("Naver DataLab 연동 차트 (우측 패널에 여러 개의 파일을 업로드하시면 2열로 나란히 비교할 수 있습니다.)")
        
        if uploaded_dls:
            dl_summaries = []
            
            # 업로드된 여러 파일을 2열(2xN) 배열로 깔끔하게 렌더링
            for i in range(0, len(uploaded_dls), 2):
                cols = st.columns(2)
                for j in range(2):
                    if i + j < len(uploaded_dls):
                        dl_file = uploaded_dls[i + j]
                        with cols[j]:
                            try:
                                # 파일명을 차트 소제목으로 활용 (.csv, .xlsx 확장자 절삭)
                                file_name_without_ext = dl_file.name.rsplit('.', 1)[0]
                                st.markdown(f"#### 📉 {file_name_without_ext}")
                                
                                file_ext = dl_file.name.split('.')[-1].lower()
                                if file_ext == 'csv': 
                                    df_dl = pd.read_csv(dl_file, skiprows=6, encoding='cp949')
                                else: 
                                    df_dl = pd.read_excel(dl_file, skiprows=6)

                                if not df_dl.empty:
                                    master_date = df_dl.iloc[:, 0]
                                    value_cols = [col for col in df_dl.columns if '날짜' not in col and 'Unnamed' not in col]
                                    clean_df = pd.DataFrame({'날짜': master_date})
                                    for col in value_cols: clean_df[col] = df_dl[col]
                                    clean_df['날짜'] = pd.to_datetime(clean_df['날짜'])
                                    
                                    # 프롬프트 생성용 통합 요약 데이터 구축
                                    recent_14d_mean = clean_df.tail(14).mean(numeric_only=True).round(1)
                                    dl_summaries.append(f"[{file_name_without_ext}]\n" + "\n".join([f"- {idx}: {val}" for idx, val in recent_14d_mean.items()]))
                                    
                                    df_melted = clean_df.melt(id_vars=['날짜'], var_name='종목명', value_name='검색량')
                                    
                                    with st.container(border=True):
                                        fig_trend = px.line(df_melted, x='날짜', y='검색량', color='종목명', template="plotly_dark")
                                        fig_trend.update_layout(
                                            height=350, margin=dict(l=10, r=10, t=10, b=10), 
                                            xaxis_title=None, yaxis_title="상대적 검색량", 
                                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5) # 범례를 하단으로 내려 공간 확보
                                        )
                                        st.plotly_chart(fig_trend, use_container_width=True)
                            except Exception as e:
                                st.error(f"{dl_file.name} 처리 중 오류 발생: {e}")
            
            # 다중 파일 요약을 글로벌 변수로 통합 전달
            st.session_state['dl_summary'] = "\n\n".join(dl_summaries) if dl_summaries else "데이터랩 연동 오류"
        else:
            st.info("👉 우측 패널에 Naver DataLab 파일을 업로드해 주세요.")

    # === Tab 4: 주간 거래량 추이 ===
    with tabs[4]:
        st.markdown("### 📊 선택 ETF 실제 주간 거래량 추이")
        if uploaded_excel is not None and selected_week != "데이터 없음":
            df_source = load_and_clean_excel(uploaded_excel, selected_week)
            if not df_source.empty and '종목명' in df_source.columns:
                extracted_etfs = df_source[df_source['종목명'] != '전체']['종목명'].dropna().unique().tolist()
                selected_etfs = st.multiselect("검색 및 선택 (원하시는 만큼 무제한 선택 가능합니다):", options=extracted_etfs, default=extracted_etfs[:4] if len(extracted_etfs) >= 4 else extracted_etfs)
                st.divider()

                if selected_etfs:
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
                                        fig_line = px.line(df_weekly, x='주 시작일', y='거래량', title=f"**{etf_name}** 실제 주간 거래량 추이", markers=True, color_discrete_sequence=['#4da6ff'])
                                        fig_line.update_layout(height=350, template="plotly_dark", margin=dict(l=20, r=20, t=50, b=20), yaxis_title="주간 거래량 (주)", xaxis_title=None, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                                        st.plotly_chart(fig_line, use_container_width=True)
                                    except:
                                        st.error(f"{etf_name}의 데이터를 불러오지 못했습니다.")
        else:
            st.info("👉 우측 패널에 엑셀 데이터를 업로드해주세요.")

    # === Tab 5: 진행 이벤트 성과 ===
    with tabs[5]:
        st.markdown("### 📊 이벤트 성과 분석기 (수급 임팩트 트래킹)")
        st.caption("아래 뉴스 스크랩에서 확인한 이벤트 진행 기간을 바탕으로, 자사와 타사 ETF의 실제 순매수 유입 효과(ROI)를 직관적으로 비교 분석합니다.")
        if uploaded_excel is not None and len(available_weeks) > 1 and available_weeks[0] != "데이터 없음":
            temp_list_df = load_and_clean_excel(uploaded_excel, available_weeks[0])
            if not temp_list_df.empty and '종목명' in temp_list_df.columns:
                all_etf_names = sorted(temp_list_df[temp_list_df['종목명'] != '전체']['종목명'].dropna().unique().tolist())
                col_sel1, col_sel2 = st.columns(2)
                with col_sel1:
                    st.markdown("**1. 분석 대상 ETF 선택**")
                    default_target_idx = all_etf_names.index("KODEX 200") if "KODEX 200" in all_etf_names else 0
                    default_comp_idx = all_etf_names.index("TIGER 200") if "TIGER 200" in all_etf_names else (1 if len(all_etf_names) > 1 else 0)
                    target_etf = st.selectbox("🎯 Target ETF (자사):", options=all_etf_names, index=default_target_idx)
                    comp_etf = st.selectbox("⚔️ Competitor ETF (타사):", options=all_etf_names, index=default_comp_idx)
                with col_sel2:
                    st.markdown("**2. 차트 조회 기간 및 이벤트 음영 설정**")
                    c_a1, c_a2 = st.columns(2)
                    with c_a1: ana_start = st.selectbox("📈 전체 분석 시작 주차:", options=available_weeks[::-1], index=0)
                    with c_a2: ana_end = st.selectbox("📈 전체 분석 종료 주차:", options=available_weeks, index=0)
                    c_h1, c_h2 = st.columns(2)
                    with c_h1: hl_start = st.selectbox("🖍️ 이벤트 시작 주차 (하이라이트):", options=available_weeks[::-1], index=0)
                    with c_h2: hl_end = st.selectbox("🖍️ 이벤트 종료 주차 (하이라이트):", options=available_weeks, index=0)

                s_idx = available_weeks.index(ana_start)
                e_idx = available_weeks.index(ana_end)
                target_sheets = available_weeks[s_idx:e_idx+1] if s_idx < e_idx else available_weeks[e_idx:s_idx+1]
                target_sheets = target_sheets[::-1] 

                trend_data = []
                with st.spinner("수급 데이터를 렌더링하고 있습니다..."):
                    for w in target_sheets:
                        t_df = load_and_clean_excel(uploaded_excel, w)
                        if not t_df.empty and '종목명' in t_df.columns:
                            t_df = t_df[t_df['종목명'].isin([target_etf, comp_etf])].copy()
                            t_df['전체순매수'] = t_df.get('개인', 0) + t_df.get('기관', 0) + t_df.get('외국인', 0)
                            t_df['주차'] = w
                            trend_data.append(t_df[['주차', '종목명', '전체순매수']])
                    if trend_data:
                        df_trend = pd.concat(trend_data)
                        fig_evt = px.line(df_trend, x='주차', y='전체순매수', color='종목명', markers=True, template="plotly_dark", color_discrete_map={target_etf: '#ff4d4d', comp_etf: '#4da6ff'}, title=f"**[{target_etf}] vs [{comp_etf}] 마케팅 성과 트래킹**")
                        try:
                            fig_evt.add_vrect(x0=hl_start, x1=hl_end, fillcolor="rgba(255, 77, 77, 0.15)", layer="below", line_width=1, line_color="rgba(255, 77, 77, 0.5)", line_dash="dash", annotation_text="★ 이벤트 집중 마케팅 구간", annotation_position="top left", annotation_font_color="#ff4d4d")
                        except: pass
                        fig_evt.update_layout(height=450, margin=dict(l=20, r=20, t=50, b=20), xaxis_title=None, yaxis_title="전체 순매수 금액 합계", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig_evt, use_container_width=True)
        else:
            st.info("👉 우측 패널에 엑셀 데이터를 업로드하시면 성과 분석기 차트가 활성화됩니다.")

        st.divider()
        st.markdown("### 🎉 운용사별 ETF 진행 이벤트 (뉴스 보도자료 스크랩)")
        col_d1, col_d2, _ = st.columns([2, 2, 6])
        with col_d1: evt_start = st.date_input("🗓️ 시작일 선택", datetime.today() - timedelta(days=30))
        with col_d2: evt_end = st.date_input("🗓️ 종료일 선택", datetime.today())
        st.divider()
        
        if evt_start > evt_end: st.error("🚨 시작일이 종료일보다 늦을 수 없습니다.")
        else:
            top_brands = ["KODEX", "TIGER", "RISE", "ACE", "SOL", "KIWOOM", "PLUS", "HANARO", "1Q", "TIMEFOLIO", "KoAct", "WON"]
            with st.spinner("이벤트 보도자료를 실시간 스크랩 중입니다..."):
                has_any_event = False
                for brand in top_brands:
                    df_evt = get_event_news(f'"{brand}" ETF (이벤트 OR 상장 OR 프로모션)', evt_start, evt_end, max_items=4)
                    if not df_evt.empty:
                        has_any_event = True
                        st.markdown(f"#### 🔵 {brand}")
                        cols = st.columns(len(df_evt) if len(df_evt) < 4 else 4)
                        for idx, row in df_evt.iterrows():
                            with cols[idx % 4]:
                                with st.container(border=True):
                                    st.markdown(f"**<a href='{row['링크']}' target='_blank' style='color:#4da6ff; text-decoration:none;'>{row['원본제목']}</a>**", unsafe_allow_html=True)
                                    st.caption(f"📅 {row['게시일 / 출처']}")
                df_other_evt = get_event_news(f'ETF (이벤트 OR 상장 OR 프로모션) ' + " ".join([f'-"{b}"' for b in top_brands]), evt_start, evt_end, max_items=8)
                if not df_other_evt.empty:
                    has_any_event = True
                    st.markdown(f"#### 🧩 기타 운용사")
                    cols = st.columns(4)
                    for idx, row in df_other_evt.iterrows():
                        with cols[idx % 4]:
                            with st.container(border=True):
                                st.markdown(f"**<a href='{row['링크']}' target='_blank' style='color:#ffb04d; text-decoration:none;'>{row['원본제목']}</a>**", unsafe_allow_html=True)
                                st.caption(f"📅 {row['게시일 / 출처']}")
                if not has_any_event:
                    st.info("해당 기간 동안 감지된 이벤트 보도자료가 없습니다.")

    # === Tab 6: 고객 UX 분석 ===
    with tabs[6]:
        st.markdown("### 🗣️ 고객 Voice (VOC) & 시스템 리스크 모니터링")
        st.caption("외부 라이브러리 없이 애플 앱스토어의 최근 찐 불만 리뷰(1~3점)와 기사화된 중대 오작동 리스크를 1:1 비교합니다.")
        st.divider()
        col_app, col_news = st.columns(2)
        with col_app:
            st.subheader("📱 주요 증권앱 최신 불만 리뷰 (App Store)")
            with st.spinner("주요 증권사 앱스토어 피드를 깊게 순회 중입니다..."):
                bad_reviews = get_apple_app_reviews()
                if bad_reviews and "error" in bad_reviews[0]:
                    st.error(bad_reviews[0]["error"])
                elif bad_reviews:
                    for r in bad_reviews:
                        with st.container(border=True):
                            st.markdown(f"**[{r['app']}]** ⭐{r['score']}점 - **{r['title']}**")
                            st.caption(f"📅 {r['date']}")
                            st.write(f"\"{r['content']}\"")
                else:
                    st.info("수집 장벽 완화 조건 하에서도 매칭된 악플 피드가 현재 부재합니다.")
        with col_news:
            st.subheader("📰 언론 보도 증권앱/MTS 중대 오류 이슈")
            with st.spinner("MTS 장애/지연 관련 중대 1년 치 아카이브를 탐색 중입니다..."):
                df_app_voc = get_realtime_news('"MTS 오류" OR "증권앱 먹통" OR "접속지연"', timeframe="1y", max_items=5)
                if "링크" in df_app_voc.columns and df_app_voc["링크"].iloc[0] != "":
                    for idx, row in df_app_voc.iterrows():
                        with st.container(border=True):
                            st.markdown(f"🚨 <a href='{row['링크']}' target='_blank' style='color:#ff4d4d; text-decoration:none;'>{row['원본제목']} 🔗</a>", unsafe_allow_html=True)
                            st.caption(f"📅 {row['게시일 / 출처']}")
                else:
                    st.info("검색 범위(최대 1년) 내 포착된 리스크성 기사가 없습니다.")

    # === Tab 7: 경쟁사 마케팅 동향 ===
    with tabs[7]:
        st.markdown("### 🏢 타사 공식 마케팅 채널 동향 (실시간 RSS)")
        st.caption("경쟁 운용사들의 공식 네이버 블로그 최신 피드를 정기 구독하여 상품 세일즈 메시지를 역추적합니다.")
        st.divider()
        blog_map = {
            "🐯 TIGER ETF (미래에셋)": ("m_invest", "https://blog.naver.com/m_invest"),
            "♠️ ACE ETF (한국투자)": ("aceetf", "https://blog.naver.com/aceetf"),
            "📈 RISE ETF (KB자산운용)": ("riseetf", "https://blog.naver.com/riseetf"),
            "☀️ SOL ETF (신한자산운용)": ("soletf", "https://blog.naver.com/soletf"),
            "➕ PLUS ETF (한화자산운용)": ("hanwhaasset", "https://blog.naver.com/hanwhaasset"),
            "🌾 HANARO ETF (NH아문디)": ("nh_amundi", "https://blog.naver.com/nh_amundi"),
            "1️⃣ 1Q ETF (하나자산운용)": ("1qetf", "https://blog.naver.com/1qetf"),
            "⏳ TIMEFOLIO ETF (타임폴리오)": ("timefolioetf", "https://blog.naver.com/timefolioetf"),
            "🔵 WON ETF (우리자산운용)": ("wooriam_kr", "https://wooriam.com/"),
            "🅚 KIWOOM ETF (키움투자자산운용)": ("kiwoomammkt", "https://blog.naver.com/kiwoomammkt")
        }
        blog_items = list(blog_map.items())
        with st.spinner("운용사 블로그 피드를 동시 수집 중입니다..."):
            for i in range(0, len(blog_items), 2):
                c1, c2 = st.columns(2)
                name1, (b_id1, url1) = blog_items[i]
                with c1:
                    st.subheader(f"[{name1}]({url1})")
                    with st.container(border=True):
                        for p_title, p_link in get_competitor_blog(b_id1):
                            st.markdown(f"- <a href='{p_link}' target='_blank' style='color:#4da6ff; text-decoration:none;'>{p_title} 🔗</a>", unsafe_allow_html=True)
                if i + 1 < len(blog_items):
                    name2, (b_id2, url2) = blog_items[i+1]
                    with c2:
                        st.subheader(f"[{name2}]({url2})")
                        with st.container(border=True):
                            for p_title, p_link in get_competitor_blog(b_id2):
                                st.markdown(f"- <a href='{p_link}' target='_blank' style='color:#4da6ff; text-decoration:none;'>{p_title} 🔗</a>", unsafe_allow_html=True)

    # === Tab 8: 운용 현황 및 점유율 ===
    with tabs[8]:
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
                        st.markdown("#### 📊 4대장 운용사 테마별 AUM 현황")
                        target_brands = ['KODEX', 'TIGER', 'ACE', 'RISE']
                        df_top_brands = df_all_etf[df_all_etf['브랜드'].isin(target_brands)].copy()
                        df_top_brands['분류_테마'] = df_top_brands['Name'].apply(assign_auto_theme)
                        pivot_df = pd.pivot_table(df_top_brands, values='AUM(억원)', index='분류_테마', columns='브랜드', aggfunc='sum', fill_value=0)
                        pivot_df = pivot_df[[c for col in target_brands if col in pivot_df.columns for c in [col]]].astype(int)
                        if '📦 기타 섹터/테마' in pivot_df.index:
                            pivot_df = pivot_df.reindex([i for i in pivot_df.index if i != '📦 기타 섹터/테마'] + ['📦 기타 섹터/테마'])
                        st.dataframe(pivot_df.style.format("{:,}"), use_container_width=True, height=420)
            except Exception as e: st.error(f"오류: {e}")

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
                fig_trend.update_layout(height=400, margin=dict(l=20, r=20, t=50, b=20), yaxis_title="전체 순매수 합계", xaxis_title=None, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("👉 우측 패널에 엑셀 데이터를 업로드하시면 트렌드 그래프가 활성화됩니다.")

    # === Tab 9: 글로벌 공백 & 정책 동향 ===
    with tabs[9]:
        st.markdown("### 🇺🇸 글로벌 혁신 구조 공백 분석 (US Mega Trends vs KODEX)")
        raw_keywords = [
            "타겟 인컴 ETF 버퍼형", 
            "0DTE 초단기 옵션 커버드콜 ETF", 
            "가상자산 비트코인 현물 ETF", 
            "BDC 기업성장집합투자기구 대체투자", 
            "하방 방어형 100% 버퍼 ETF"
        ]
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
            else:
                st.info("관련된 최신 정책 뉴스 피드가 존재하지 않습니다.")

    # === Tab 10: AI 프롬프트 생성기 ===
    with tabs[10]:
        st.markdown("### 🧠 전술 & 전략 AI 프롬프트 자동 생성기")
        st.caption("단순한 데이터 요약을 넘어, 대시보드의 모든 인텔리전스(수급, 규제, 고객 VOC, 경쟁사)를 결합하여 실무팀에 하달할 구체적인 '행동 지침(Action Item)'을 도출합니다.")
        st.divider()

        data_context = df_scatter.sort_values(by='주간 수익률(%)', ascending=False).head(20).to_string(index=False) if not df_scatter.empty else "데이터가 부족합니다. (우측 패널에 엑셀 데이터를 업로드해주세요.)"
        dl_context = st.session_state.get('dl_summary', "데이터랩 미연동")
        
        raw_sentiment = st.session_state.get('market_sentiment', "혼조세 지속")
        if "<ul>" in raw_sentiment:
            clean_sentiment = raw_sentiment.replace("<ul>", "").replace("</ul>", "").replace("<li>", "- ").replace("</li>", "\n").replace("<b>", "").replace("</b>", "")
        else:
            clean_sentiment = raw_sentiment
        
        try:
            current_trend = st.session_state.get('selected_trend_label', "가상자산/옵션형")
        except:
            current_trend = "가상자산/옵션형"

        prompt_1 = f"너는 KODEX 마케팅 총괄 최고책임자(CMO)야. 다음 지표를 기반으로 마케팅 전술 리포트를 세부 작성해줘.\n\n[수급현황]\n{data_context}\n\n[포털 검색량]\n{dl_context}\n\n[시장심리 요약]\n{clean_sentiment}"
        prompt_2 = f"너는 KODEX 신상품 전략 수석 기획자야. 미국 {current_trend} 자금 쏠림 현상과 국내 규제 리스크 장벽을 해소하며 선점할 수 있는 차기 ETF 기획 초안을 설계해줘."
        
        st.markdown("#### 🔵 `[Track 1]` 주간 마케팅 & 세일즈 대응 전략 도출용")
        st.code(prompt_1, language="text")
        st.markdown("#### 🔴 `[Track 2]` 상품 기획 및 글로벌 장벽 선점 전략 도출용")
        st.code(prompt_2, language="text")
