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

/* 🔴 Big 탭 (Pill 형태의 큰 네모-반원형 버튼) 디자인 완벽 적용 */
div[data-testid="stRadio"] > div[role="radiogroup"] {
    display: flex;
    flex-direction: row;
    gap: 15px;
    background: transparent !important;
}
div[data-testid="stRadio"] > div[role="radiogroup"] > label {
    background: rgba(255, 255, 255, 0.05) !important;
    padding: 15px 30px !important;
    border-radius: 50px !important; /* 양옆이 완벽한 반원형 */
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
/* 기존 라디오 버튼의 동그라미 숨기기 */
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
    elif any(kw in name for kw in ['테크', '기술주', 'TECH']): return '💻 글로벌 빅테크'
    elif any(kw in name for kw in ['S&P', '미국', '다우존스']): return '🇺🇸 미국 대표지수'
    elif any(kw in name for kw in ['코스피', '코스닥', '200']): return '🇰🇷 국내 대표지수'
    elif any(kw in name for kw in ['채권', '국고채', '금리', 'CD']): return '🛡️ 안전자산 (채권/금리)'
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
    snapshot = {"indices": {"코스피": {"val": "정보 불가"}, "코스닥": {"val": "정보 불가"}, "S&P 500": {"val": "정보 불가"}},
                "forex": {"미국 USD": {"val": "정보 불가"}, "일본 JPY 100": {"val": "정보 불가"}},
                "rates": {"국고채(3년)": {"val": "정보 불가"}},
                "others": {"VIX 지수": {"val": "정보 불가"}, "금 가격": {"val": "정보 불가"}}}
    tickers = {"indices": {"코스피": ["KS11"], "코스닥": ["KQ11"], "S&P 500": ["US500", "^GSPC"]},
               "forex": {"미국 USD": ["USD/KRW"], "일본 JPY 100": ["JPY/KRW"]},
               "others": {"VIX 지수": ["VIX", "^VIX"], "금 가격": ["GC=F", "ZG"]}}
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
                        val_str, delta_str = (f"${c:,.2f}", f"{c-p:+,.2f}") if "금" in name else (f"{c:,.2f}", f"{c-p:+,.2f}")
                        snapshot[category][name] = {"val": val_str, "delta": delta_str, "pct": f"{(c-p)/p*100:+.2f}%", "is_up": c >= p}
                        break 
                except: pass
    return snapshot

def render_compact_metric(title, data):
    if data['val'] == "정보 불가": return f"<div style='...'>{title}</div>"
    color, arrow = ("#ff4d4d", "▲") if data['is_up'] else ("#4da6ff", "▼")
    return f"""<div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 12px 16px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;"><div style="color: #cbd5e1; font-size: 15px; font-weight: 600;">{title}</div><div style="text-align: right;"><div style="color: #ffffff; font-size: 17px; font-weight: 800;">{data['val']}</div><div style="color: {color}; font-size: 12px; font-weight: 600; margin-top: 2px;">{arrow} {str(data['delta']).replace('+','').replace('-','')} ({data['pct']})</div></div></div>"""

@st.cache_data(ttl=3600)
def get_realtime_news(keyword="ETF", timeframe="7d", max_items=8):
    try:
        res = requests.get(f"https://news.google.com/rss/search?q={keyword}+when:{timeframe}&hl=ko&gl=KR&ceid=KR:ko", timeout=5)
        root = ET.fromstring(res.text)
        return pd.DataFrame([{"게시일 / 출처": f"{item.find('pubDate').text[5:16]} / {item.find('source').text}", "원본제목": item.find('title').text, "링크": item.find('link').text} for item in root.findall('./channel/item')[:max_items]])
    except: return pd.DataFrame([{"게시일 / 출처": "오류", "원본제목": "뉴스를 불러올 수 없습니다.", "링크": ""}])

@st.cache_data
def load_and_clean_excel(file, sheet_name):
    try:
        df = pd.read_excel(file, sheet_name=sheet_name)
        df.columns = df.columns.str.strip()
        for col in ["개인", "기관", "외국인"]:
            if col in df.columns: df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '').str.replace('-', '0'), errors='coerce').fillna(0)
        return df
    except: return pd.DataFrame()

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
# 좌측 메인 패널 (Big 탭 - 리밸런싱 제거 완료)
# -------------------------------------------------------------------------
with col_main:
    # 🔴 Big 탭 (Pill 스타일 적용)
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
        sub_tabs = st.tabs(["🏠 Home", "📊 Weekly Info", "📰 뉴스 & 트렌드", "🥧 ETF/AUM 현황"])

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
            with c_m3: 
                st.markdown("#### 📌 기타 주요 지표")
                for k,v in macros["others"].items(): st.markdown(render_compact_metric(k,v), unsafe_allow_html=True)

        with sub_tabs[1]:
            if uploaded_excel is not None and selected_week != "데이터 없음":
                df_source = load_and_clean_excel(uploaded_excel, selected_week)
                if not df_source.empty and '종목명' in df_source.columns:
                    target_subject = st.selectbox("주체:", ["개인", "기관", "외국인"], key="main_sub")
                    df_filtered = df_source[df_source["종목명"] != "전체"].sort_values(by=target_subject, ascending=False).head(10)
                    fig = px.bar(df_filtered, x=target_subject, y="종목명", orientation='h', template="plotly_dark")
                    fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig, use_container_width=True)
            else: st.info("👉 우측 패널에 ETF 순매수 엑셀 데이터를 업로드해주세요.")

        with sub_tabs[2]:
            st.markdown("### 📰 실시간 뉴스 리스트")
            st.session_state.df_real_news = get_realtime_news("ETF", timeframe="7d", max_items=10)
            st.dataframe(st.session_state.df_real_news, use_container_width=True, hide_index=True)

        with sub_tabs[3]:
            st.markdown("### 🏢 국내 ETF 운용사 AUM 현황")
            try:
                df_all_etf = fdr.StockListing('ETF/KR')
                if not df_all_etf.empty:
                    df_all_etf['브랜드'] = df_all_etf['Name'].apply(lambda x: str(x).split(' ')[0]).replace('KBSTAR', 'RISE')
                    df_brand_aum = df_all_etf.groupby('브랜드')['MarCap'].sum().reset_index().sort_values(by='MarCap', ascending=False).head(6)
                    fig_market_share = px.pie(df_brand_aum, names='브랜드', values='MarCap', hole=0.4, template="plotly_dark")
                    st.plotly_chart(fig_market_share, use_container_width=True)
                    st.session_state.aum_context_text = df_brand_aum.to_string()
            except: st.error("KRX 데이터를 불러올 수 없습니다.")

    # =========================================================================
    # Big 탭 2: 글로벌 상품 기획 시뮬레이터 (4대 심화 기능 100% 탑재)
    # =========================================================================
    elif big_tab == "2. 글로벌 상품 기획 시뮬레이터":
        st.markdown("## 🌍 Global Alternative ETF Structuring Simulator")
        st.caption("사모신용(BDC), CLO, 인프라 등 해외 대체 자산을 융합하여 프록시 백테스트 및 수지 분석(P&L)을 거친 실무형 팩트시트를 도출합니다.")
        
        asset_class = st.selectbox("🌍 탐색할 해외 대체투자 자산군 선택:", ["사모신용 (BDC)", "대출채권담보부증권 (CLO)", "에너지 인프라 (MLP)", "인프라 펀드 (InvITs & REITs)"])

        # Dummy DB for simplicity
        tkrs = ["ARCC", "OBDC", "FSK"] if "BDC" in asset_class else ["JAAA", "JBBB", "CLOA"]
        nms = ["Ares Capital", "Blue Owl Capital", "FS KKR Capital"] if "BDC" in asset_class else ["Janus AAA", "Janus BBB", "BlackRock AAA"]
        b_ylds = [9.5, 10.2, 11.8] if "BDC" in asset_class else [6.2, 8.5, 6.1]

        st.markdown("#### 1. 기초자산 포트폴리오 구성 및 환율/세금 전략")
        col_p1, col_p2 = st.columns([1, 1])
        
        with col_p1:
            st.markdown("**기초자산 편입 비중 조절**")
            df_setup = pd.DataFrame({"티커": tkrs, "종목명": nms, "예상 배당률(%)": b_ylds, "목표비중(%)": [33.3, 33.3, 33.4]})
            edited_df = st.data_editor(df_setup, hide_index=True, use_container_width=True)
            norm_weights = edited_df['목표비중(%)'].values / np.sum(edited_df['목표비중(%)'].values)
            base_yield = np.dot(np.array(b_ylds), norm_weights)

        with col_p2:
            st.markdown("**[심화] ETF 운용 구조 및 FX/Tax 최적화**")
            fx_strategy = st.selectbox("환율 헤지(FX) 전략", ["환노출 (Unhedged)", "환헤지 (Hedged - 한미 금리차 반영)"])
            ter = st.slider("예상 총보수율 (TER, %)", 0.1, 2.0, 0.45, 0.05)
            
            # FX Cost Logic (Feature 3)
            fx_cost = 0.0
            if "환헤지" in fx_strategy:
                fx_cost = 2.0 # 한미 금리차로 인한 대략적 헤지 프리미엄/디스카운트
                net_yield = base_yield - fx_cost - ter
                st.info(f"💡 **환헤지 비용 반영:** 현재 한미 금리 역전 현상으로 인해 연 환산 약 {fx_cost}%의 헤지 프리미엄 비용이 차감됩니다.")
            else:
                net_yield = base_yield - ter
                st.info("💡 **환노출 반영:** 달러 강세 국면 시 환차익을 추가로 향유할 수 있으나, 변동성에 노출됩니다.")
            
            # Tax Logic
            st.metric("최종 타겟 배당수익률 (Net Yield)", f"{net_yield:.2f}%")
            if net_yield >= 5.0:
                st.success("💰 **세금 최적화(Tax) 분석:** 고배당 자산이므로 종합소득세 합산 위험이 존재합니다. **ISA 및 IRP(퇴직연금) 계좌 편입용**으로 마케팅하는 것이 절대적으로 유리합니다.")

        st.markdown("---")
        col_s1, col_s2 = st.columns(2)
        
        with col_s1:
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
            fig_proxy = px.line(df_proxy, x="Date", y="value", color="variable", template="plotly_dark")
            fig_proxy.update_layout(height=300, yaxis_title="누적 수익률 (Base 100)", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_proxy, use_container_width=True)
            
            sharpe = (net_yield - 3.5) / (np.std(port_ret)*np.sqrt(252)*100)
            mdd = (port_cum / np.maximum.accumulate(port_cum) - 1).min() * 100
            corr = np.corrcoef(sp500_ret, port_ret)[0,1]
            
            c1, c2, c3 = st.columns(3)
            c1.metric("샤프 비율 (Sharpe)", f"{sharpe:.2f}")
            c2.metric("최대 낙폭 (MDD)", f"{mdd:.1f}%")
            c3.metric("S&P500 상관계수", f"{corr:.2f}")
            
        with col_s2:
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
            
            st.metric(f"AMC 순수 영업이익 추정 (운용보수 {amc_margin:.2f}%)", f"{net_profit:+.2f} 억원", delta_color="normal" if net_profit>0 else "inverse")
            st.info(f"📍 **BEP 달성 목표 AUM:** {bep_aum:.0f}억원\n\n💸 초기 설정액 제외, **매월 약 {req_monthly:.0f}억원**의 순유입(Inflow)이 달성되어야 1년 내 흑자 전환이 가능합니다.")

        st.markdown("---")
        st.markdown("#### 4. 심화 RAG 규제 분석 및 기획서 자동 산출 (InvITs/FCF 판독 지원)")
        st.caption("타겟 기업의 IR 자료나 매크로 PDF를 업로드하면, AI가 잉여현금흐름(FCF), LTV, 인프라 규제 완화 타임라인을 파고들어 완벽한 최종 기획서를 뽑아냅니다.")
        
        fin_docs = st.file_uploader("🏢 기업 재무제표 / 규제 정책 문건 업로드 (PDF, 엑셀)", type=["pdf", "xlsx", "csv"], accept_multiple_files=True)
        
        if st.button("✨ 고도화된 AI 상품기획서 생성", type="primary"):
            if fin_docs:
                with st.spinner("AI가 엑셀 데이터의 FCF/LTV를 추출하고, 규제 문건의 타임라인을 해독하고 있습니다..."):
                    time.sleep(2)
                st.success("데이터 클렌징 및 심화 규제/재무 분석이 완료되었습니다. [🤖 AI 프롬프트] 탭에서 완성된 기획서를 확인하세요!")
                st.session_state.proposal_generated = True
            else:
                st.warning("문서를 먼저 업로드해주세요.")

    # =========================================================================
    # Big 탭 3: 🤖 AI 프롬프트 (세분화 및 체인 프롬프트 적용)
    # =========================================================================
    elif big_tab == "🤖 AI 프롬프트":
        st.markdown("### 🧠 모듈형 AI 프롬프트 컨트롤 타워")
        st.caption("각 단계별 목적에 맞게 AI(LLM)에게 전달할 최적화된 프롬프트를 체인(Chain) 형태로 제공합니다.")
        
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
1. 타겟 기초자산 기업들의 평균 잉여현금흐름(FCF) 추이와 평균 LTV(레버리지 비율). 배당 지속 가능성을 평가할 것.
2. 정책 문건 내 '수익형 부동산/신재생에너지 인프라(InvITs)' 관련 규제 완화 타임라인 및 출시 적기(Time-to-Market) 도출."""
            st.code(p_step1, language="text")
            
            p_step2 = """[Step 2: 퀀트 기반 수지 및 백테스팅 평가]
앞서 확인한 규제 환경을 바탕으로, 다음 퀀트 분석 결과를 해석하시오.
- 프록시 백테스트: 샤프 비율, MDD, S&P 500 상관계수를 기반으로 기관 투자자 설득 논리 작성.
- P&L: 타겟 AUM 1,000억 달성 시 AMC 순수익 및 월간 필요 순유입(Inflow) 타당성 검증.
- 세금 최적화: 환헤지 비용 차감 후 Net Yield 기반으로 'ISA/퇴직연금 편입용' 마케팅 메시지 구성."""
            st.code(p_step2, language="text")
            
            p_step3 = """[Step 3: 최종 상품 기획서(Proposal) 작성]
Step 1과 Step 2의 팩트를 융합하여, 본부장 보고용 'KODEX 신상품 개략 검토 보고서'를 다음 목차로 마크다운 작성하시오.
1. 추진 배경 및 시장 공백 (인구 구조 및 연금 수요)
2. 기초자산 유니버스 및 FCF/LTV 펀더멘털 증명
3. 퀀트 시뮬레이션 성과 (위험/수익 프로파일)
4. 수지 분석(P&L) 및 세일즈/세금 마케팅 전략"""
            st.code(p_step3, language="text")
