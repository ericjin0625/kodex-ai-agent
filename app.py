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

# 1. 페이지 레이아웃 및 기본 테마 설정 (반드시 최상단에 위치)
st.set_page_config(page_title="ETF Monitoring AI Agent", layout="wide")

# ==========================================
# ★ Glassmorphism 프리미엄 커스텀 CSS 주입
# ==========================================
glassmorphism_css = """
<style>
/* 1. 전체 배경: 딥 네이비 & 퍼플 프리미엄 오로라 그라데이션 */
.stApp {
    background: linear-gradient(135deg, #0b101e 0%, #171b3c 50%, #0f172a 100%);
    background-attachment: fixed;
}

/* 2. 사이드바: 반투명 유리 블러 효과 */
[data-testid="stSidebar"] {
    background: rgba(15, 23, 42, 0.4) !important;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-right: 1px solid rgba(255, 255, 255, 0.05);
}

/* 3. 메인 컨테이너 테두리: 둥근 모서리와 은은한 글래스 광택 */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255, 255, 255, 0.02) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border-radius: 16px !important;
    border: 1px solid rgba(255, 255, 255, 0.06) !important;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2) !important;
    padding: 25px !important;
    margin-bottom: 20px !important;
}

/* 4. 데이터프레임 배경 투명화 */
.stDataFrame {
    background: transparent !important;
}

/* 5. 탭(Tabs) 디자인: 둥글고 트렌디한 캡슐 알약(Pill) 스타일 */
[data-baseweb="tab-list"] {
    gap: 8px;
    padding-bottom: 12px;
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

/* 6. 독립 솔루션 마감을 위한 기본 UI 강제 숨김 */
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display: none;}
</style>
"""
st.markdown(glassmorphism_css, unsafe_allow_html=True)

# ==========================================
# ★ AI 테마 자동 분류 로직
# ==========================================
def assign_auto_theme(etf_name):
    name = str(etf_name).upper().replace(" ", "")
    if any(kw in name for kw in ['인버스', '베어']):
        return '📉 인버스 (하락배팅)'
    elif any(kw in name for kw in ['레버리지', '2X']):
        return '🚀 레버리지 (고변동성)'
    elif any(kw in name for kw in ['배당', '커버드콜', '인컴', '고배당', 'DIV']):
        return '💰 배당 & 커버드콜'
    elif any(kw in name for kw in ['AI', '반도체']):
        return '🤖 AI & 반도체'
    elif any(kw in name for kw in ['테크', '기술주', 'TECH', '혁신', '나스닥100', '빅테크', 'FANG']):
        return '💻 글로벌 빅테크'
    elif any(kw in name for kw in ['S&P', '미국', '다우존스', 'MSCI']):
        return '🇺🇸 미국 대표지수'
    elif any(kw in name for kw in ['코스피', '코스닥', '200']):
        return '🇰🇷 국내 대표지수'
    elif any(kw in name for kw in ['채권', '국고채', '금리', 'KOFR', 'CD', '파킹']):
        return '🛡️ 안전자산 (채권/금리)'
    else:
        return '📦 기타 섹터/테마'

# 실시간 뉴스 파싱 함수
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
            
            news_list.append({
                "게시일 / 출처": f"{pubDate} / {source}", 
                "원본제목": title, 
                "링크": link
            })
            
        if not news_list:
            return pd.DataFrame([{"게시일 / 출처": "-", "원본제목": f"'{keyword}' 관련 뉴스가 없습니다.", "링크": ""}])
            
        return pd.DataFrame(news_list)
        
    except Exception as e:
        return pd.DataFrame([{"게시일 / 출처": "오류", "원본제목": "실시간 뉴스를 불러올 수 없습니다.", "링크": ""}])

# 실시간 애플 앱스토어 리뷰 파싱 함수
@st.cache_data(ttl=1800)
def get_apple_app_reviews():
    apps = {
        "삼성증권 mPOP": "418064117",
        "미래에셋 M-STOCK": "1619623868",
        "한국투자증권": "364506828",
        "KB증권 M-able": "1198642398"
    }
    all_bad_reviews = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        for app_name, app_id in apps.items():
            valid_entries = []
            for page in range(1, 4):
                url = f"https://itunes.apple.com/kr/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/limit=200/json"
                res = requests.get(url, headers=headers, timeout=10)
                if res.status_code != 200:
                    break
                data = res.json()
                entries = data.get("feed", {}).get("entry", [])
                if isinstance(entries, dict):
                    entries = [entries]
                if not entries:
                    break
                for entry in entries:
                    if entry.get("im:rating"):
                        valid_entries.append(entry)
                time.sleep(0.5) 

            if not valid_entries:
                continue

            for entry in valid_entries:
                try:
                    score = int(entry.get("im:rating", {}).get("label", "5"))
                    if score <= 3:
                        date_str = entry.get("updated", {}).get("label", "")[:10] 
                        content_data = entry.get("content", {})
                        content = content_data.get("label", "") if isinstance(content_data, dict) else str(content_data)
                        title = entry.get("title", {}).get("label", "제목 없음")
                        
                        all_bad_reviews.append({
                            "app": app_name,
                            "score": score,
                            "date": date_str,
                            "title": title,
                            "content": content
                        })
                except:
                    pass 
                    
        all_bad_reviews.sort(key=lambda x: x['date'], reverse=True)
        return all_bad_reviews[:12]
        
    except Exception as e:
        return [{"error": f"API 연동 중 오류가 발생했습니다: {str(e)}"}]

# 실시간 데이터 파싱 함수 (이벤트 캘린더 전용)
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
            if len(news_list) >= max_items:
                break
        return pd.DataFrame(news_list)
    except Exception as e:
        return pd.DataFrame()

# 타 운용사 네이버 블로그 실시간 RSS 파싱 함수
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
        if not posts:
            return [("최신 게시글이 없습니다.", "https://blog.naver.com/" + blog_id)]
        return posts
    except Exception as e:
        return [("실시간 연동 지연 (클릭 시 이동)", "https://blog.naver.com/" + blog_id)]

@st.cache_data(ttl=86400)
def get_etf_mapping():
    df = fdr.StockListing('ETF/KR')
    return dict(zip(df['Name'], df['Symbol']))

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
                    current_price = df['Close'].iloc[-1]
                    past_price = df['Close'].iloc[-5]
                    yield_pct = ((current_price - past_price) / past_price) * 100
                    returns_dict[name] = round(yield_pct, 2)
                else:
                    returns_dict[name] = 0.0
            except:
                returns_dict[name] = 0.0
        else:
            returns_dict[name] = 0.0
    return returns_dict

def generate_market_sentiment(news_df):
    if news_df.empty or news_df["원본제목"].iloc[0].startswith("'"):
        return "시장 심리를 분석할 충분한 뉴스 데이터가 없습니다."
    all_titles = " ".join(news_df["원본제목"].astype(str).tolist())
    if any(kw in all_titles for kw in ['강세', '상승', '급등', '반등']):
        return "☀️ 오늘의 시장 심리 1줄 요약: 시장 상승세 속 금리 인하 기대감으로 인한 성장주형 및 고배당 ETF로의 자금 유입이 눈에 땕니다."
    elif any(kw in all_titles for kw in ['하락', '약세', '급락', '둔화']):
        return "☁️ 오늘의 시장 심리 1줄 요약: 금리 우려 재점화로 인한 방어적 포트폴리오 구축 전략이 우세하며 채권 및 인버스 ETF 관심이 고조됩니다."
    return "⚖️ 오늘의 시장 심리 1줄 요약: 특별한 모멘텀 없는 혼조세 속에서 섹터별 테마별 순환매가 지속되고 있습니다."

# 3. 사이드바 구성
with st.sidebar:
    st.markdown("### 📊 데이터 컨트롤 타워")
    sidebar_top = st.container()
    st.divider()
    uploaded_excel = st.file_uploader("ETF 순매수 엑셀 업로드", type=["xlsx", "xls"], key="excel_main")
    st.divider()
    uploaded_dl = st.file_uploader("DataLab 데이터 업로드 (CSV/Excel)", type=["csv", "xlsx", "xls"], key="dl_main")

# 4. 엑셀 시트 파싱 및 주차 연동
available_weeks = ["5.17~5.23", "5.10~5.16", "5.03~5.09"] 
if uploaded_excel is not None:
    xls = pd.ExcelFile(uploaded_excel)
    sheet_names = [sheet for sheet in xls.sheet_names if sheet != "참고사항"]
    if sheet_names:
        available_weeks = sheet_names[::-1] 

with sidebar_top:
    default_idx = 1 if len(available_weeks) > 1 else 0
    selected_week = st.selectbox("주차 (최대 6개월 전까지 선택 가능):", options=available_weeks, index=default_idx)

# ★ 탭 레이아웃 맨 앞에 [🏠 Home] 표지 추가
tab_names = [
    "🏠 Home", "[Weekly Info.]", "[ETF 순매수 등락, 수익률]", "[뉴스 & 검색량 트렌드]", 
    "[주간 거래량 추이]", "[진행 이벤트]", "[고객 UX 분석]", "[경쟁사 동향]", 
    "[ETF 운용 현황]", "[글로벌 공백 & 정책 동향]", "[AI 분석용 프롬프트]"
]
tabs = st.tabs(tab_names)

# =========================================================================
# --- ★ 새롭게 추가된 Tab 0: [🏠 Home] (표저 및 고해상도 로직 주입) ---
# =========================================================================
with tabs[0]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Hero 타이틀 섹션
    st.markdown(
        """
        <div style='text-align: center; padding: 10px;'>
            <h1 style='font-size: 54px; font-weight: 800; letter-spacing: -1.5px; background: linear-gradient(to right, #ffffff, #93c5fd); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
                ETF Monitoring AI Agent
            </h1>
            <p style='font-size: 19px; color: #94a3b8; margin-top: 15px; font-weight: 400; letter-spacing: -0.5px;'>
                데이터 기반의 전략적 자금 추적 및 마케팅 인사이트 도출을 위한 인텔리전스 컨트롤 타워
            </p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Core Value 3성 카드 레이아웃
    c_p1, c_p2, c_p3 = st.columns(3)
    with c_p1:
        with st.container(border=True):
            st.markdown("### 📊 수급 및 성과 어트리뷰션")
            st.write("투자자별(개인/기관/외국인) 주간 순매수 흐름을 다차원 산점도로 분석하고, 마케팅 이벤트의 수급 기여도(ROI)를 직관적으로 추적합니다.")
    with c_p2:
        with st.container(border=True):
            st.markdown("### 📡 실시간 마켓 인텔리전스")
            st.write("구글 뉴스 RSS 및 네이버 데이터랩 포털 검색 비율을 결합하여 시장의 실시간 센티먼트를 감지하고 잠재적 시스템 리스크를 선제 방어합니다.")
    with c_p3:
        with st.container(border=True):
            st.markdown("### 🧠 전술 전략 프롬프트 빌더")
            st.write("수집된 모든 수급 지표와 규제 동향, 고객 Pain Point를 결합하여 실무팀에 즉시 하달할 수 있는 세일즈/상품 기획 액션 플랜을 도출합니다.")
            
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    
    # ★ 하단 브랜딩 로고 락업 (호환성과 고해상도를 다 잡은 HTML/CSS 배지 디자인)
    # 실무 환경에서 파일이 있다면 st.image("로고파일명.png")로 바로 교체 가능하도록 가이드를 짜두었습니다.
    st.markdown(
        """
        <div style='text-align: center; padding: 25px; opacity: 0.8;'>
            <p style='color: #64748b; font-size: 11px; letter-spacing: 3px; font-weight: 600; margin-bottom: 18px;'>CO-DEVELOPED BY</p>
            <div style='display: inline-block; vertical-align: middle;'>
                <span style='font-family: "Arial Black", sans-serif; font-size: 16px; font-weight: 900; color: #ffffff; letter-spacing: 0.5px; border: 1px solid rgba(255,255,255,0.12); padding: 6px 14px; border-radius: 6px; background: rgba(255,255,255,0.04); box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-right: 12px;'>
                    SAMSUNG <span style='font-weight: 400; font-size: 13px; color: #93c5fd; padding-left: 4px;'>삼성자산운용</span>
                </span>
                <span style='font-family: "Impact", sans-serif; font-size: 16px; color: #ff4d4d; letter-spacing: 1.5px; border: 1px solid rgba(255,77,77,0.25); padding: 6px 14px; border-radius: 6px; background: rgba(255,77,77,0.04); box-shadow: 0 4px 12px rgba(255,77,77,0.05);'>
                    CAREER HIGH <span style='font-family: sans-serif; font-weight: 400; font-size: 12px; color: #ffffff; padding-left: 3px;'>커리어하이</span>
                </span>
            </div>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # ※ 방법 2: 실제 이미지 파일로 띄우고 싶으실 경우, 프로젝트 폴더에 이미지 파일을 넣고 
    # 아래 3줄의 주석(#)을 해제하여 사용하시면 다른 PC에서도 완벽하게 로고로 출력됩니다.
    # col_img1, col_img2, col_img3 = st.columns([3, 2, 3])
    # with col_img2:
    #     st.image(["samsung_logo.png", "careerhigh_logo.png"], width=160)

# =========================================================================
# --- Tab 1: [Weekly Info.] ---
# =========================================================================
with tabs[1]:
    df_source = pd.DataFrame()
    if uploaded_excel is not None:
        try:
            df_source = load_and_clean_excel(uploaded_excel, selected_week)
        except Exception as e:
            st.error(f"엑셀을 읽는 중 오류가 발생했습니다: {e}")

    if not df_source.empty:
        st.markdown("### 🏆 해당 주 순매수 ETF 순위")
        col_subject, col_space, col_slider = st.columns([2, 3, 3])
        with col_subject:
            target_subject = st.selectbox("주체:", ["개인", "기관", "외국인"], key="main_sub")
        with col_slider:
            top_n = st.slider("TOP N개 설정", 5, 50, 10, 5, label_visibility="collapsed")
            st.markdown(f"<p style='text-align:right; color:red; font-weight:bold; margin-top:-10px;'>{top_n}</p>", unsafe_allow_html=True)

        df_filtered = df_source.dropna(subset=[target_subject]).copy()
        if '종목명' in df_filtered.columns:
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
        if '종목명' in df_source.columns:
            df_source['AI_자동_테마'] = df_source['종목명'].apply(assign_auto_theme)
            df_theme_pos = df_source[(df_source["종목명"] != "전체") & (df_source[target_subject] > 0)]
            df_theme = df_theme_pos.groupby('AI_자동_테마')[target_subject].sum().reset_index()
            df_theme = df_theme.sort_values(by=target_subject, ascending=False)

            if len(df_theme) > top_n:
                df_top = df_theme.head(top_n)
                others_val = df_theme.iloc[top_n:][target_subject].sum()
                df_others = pd.DataFrame([{'AI_자동_테마': "🧩 기타 합산 (Others)", target_subject: others_val}])
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
        st.info("좌측 사이드바에 엑셀 데이터를 업로드해주세요.")

# =========================================================================
# --- Tab 2: [ETF 순매수 등락, 수익률] ---
# =========================================================================
with tabs[2]:
    st.markdown("### 📈 기간별 ETF 순매수 현황")
    col_start, col_text, col_slider = st.columns([1.5, 3.5, 3])
    with col_start:
        start_week = st.selectbox("시작 주차:", options=available_weeks[::-1], index=0, key="start_week")
    with col_text:
        st.markdown(f"<p style='margin-top: 30px; font-weight: bold;'>부터 &nbsp;&nbsp; {selected_week} (현재 선택 주차) 까지의</p>", unsafe_allow_html=True)
    with col_slider:
        top_n_tab2 = st.slider("TOP N개 ETF 순매수 순위:", min_value=10, max_value=100, value=50, step=10, key="top_n_tab2", label_visibility="collapsed")
        st.markdown(f"<p style='text-align:right; color:red; font-weight:bold; margin-top:-10px;'>{top_n_tab2}</p>", unsafe_allow_html=True)
    
    st.divider()

    df_tab2_combined = pd.DataFrame()
    if uploaded_excel is not None:
        try:
            start_idx = available_weeks.index(start_week) if start_week in available_weeks else -1
            end_idx = available_weeks.index(selected_week) if selected_week in available_weeks else -1
            if start_idx != -1 and end_idx != -1 and start_idx >= end_idx:
                target_sheets = available_weeks[end_idx:start_idx+1]
                all_sheets_data = []
                for sheet in target_sheets:
                    temp_df = load_and_clean_excel(uploaded_excel, sheet)
                    if '종목명' in temp_df.columns:
                        temp_df = temp_df[temp_df['종목명'] != '전체']
                        temp_df['전체순매수'] = temp_df.get('개인', 0) + temp_df.get('기관', 0) + temp_df.get('외국인', 0)
                        all_sheets_data.append(temp_df[['종목명', '전체순매수', '개인', '기관', '외국인']])
                if all_sheets_data:
                    df_tab2_combined = pd.concat(all_sheets_data).groupby('종목명').sum().reset_index()
        except Exception as e:
            st.error(f"데이터 병합 중 오류 발생: {e}")

    if not df_tab2_combined.empty:
        st.markdown("#### 전체 순매수 금액")
        df_total = df_tab2_combined.sort_values(by="전체순매수", ascending=False).head(top_n_tab2)
        with st.container(border=True):
            fig_total = px.bar(df_total, x="전체순매수", y="종목명", orientation='h', color_discrete_sequence=['#4da6ff'])
            fig_total.update_layout(yaxis={'categoryorder':'total ascending'}, height=500, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_total, use_container_width=True)

        st.divider()

        col_inv_title, col_inv_drop = st.columns([2, 8])
        with col_inv_title:
            st.markdown("#### 투자자별 순매수 금액")
        with col_inv_drop:
            inv_type_tab2 = st.selectbox("투자자 선택", ["개인", "기관", "외국인"], label_visibility="collapsed", key="inv_type_tab2")
            
        df_inv = df_tab2_combined.sort_values(by=inv_type_tab2, ascending=False).head(top_n_tab2)
        with st.container(border=True):
            fig_inv = px.bar(df_inv, x=inv_type_tab2, y="종목명", orientation='h', color_discrete_sequence=['#4da6ff'])
            fig_inv.update_layout(yaxis={'categoryorder':'total ascending'}, height=500, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_inv, use_container_width=True)

        st.divider()
        
        st.markdown("### 🎯 주간 수익률 vs. 투자자별 순매수 증감률 산점도 (실시간 데이터 연동)")
        col_subject_tab2_scatter, _ = st.columns([2, 8])
        with col_subject_tab2_scatter:
            subject_tab2_scatter = st.selectbox("분석 주체 선택:", ["개인", "기관", "외국인"], key="subject_tab2_scatter")

        if len(available_weeks) > 1:
            current_idx = available_weeks.index(selected_week)
            if current_idx + 1 < len(available_weeks):
                prev_week = available_weeks[current_idx + 1]
                df_curr = load_and_clean_excel(uploaded_excel, selected_week)
                df_prev = load_and_clean_excel(uploaded_excel, prev_week)
                
                if '종목명' in df_curr.columns and '종목명' in df_prev.columns:
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
                                fig_scatter.add_scatter(x=x_data, y=p(x_data), mode='lines', name=f'상관관계(Trendline)<br>Pearson: {r_value:.2f}', line=dict(color='#ff4d4d', dash='dot'))

                            fig_scatter.update_traces(textposition='top center', marker=dict(size=10, color='#4da6ff', opacity=0.7), textfont=dict(size=11, color='lightgray'))
                            fig_scatter.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.5)
                            fig_scatter.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
                            fig_scatter.update_layout(height=600, template="plotly_dark", xaxis_title="실제 주간 수익률 (%)", yaxis_title=f"{subject_tab2_scatter} 순매수 증감률 (%)", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                            st.plotly_chart(fig_scatter, use_container_width=True)
            else:
                st.warning("직전 주차 데이터가 없어 증감률을 비교할 수 없습니다.")

# =========================================================================
# --- Tab 3: [뉴스 & 검색량 트렌드] ---
# =========================================================================
with tabs[3]:
    st.markdown("### 📰 실시간 마켓 센티먼트 및 뉴스 요약")
    with st.spinner("최신 마켓 트렌드를 AI가 분석하고 있습니다..."):
        df_real_news = get_realtime_news("ETF", timeframe="7d")
        market_sentiment = generate_market_sentiment(df_real_news)
        st.session_state['market_sentiment'] = market_sentiment
        with st.container(border=True):
            st.markdown(f"<p style='font-size:18px; font-weight:bold; color:#4da6ff; text-align:center; margin:0;'>{market_sentiment}</p>", unsafe_allow_html=True)
        st.divider()
        if "링크" in df_real_news.columns and df_real_news["링크"].iloc[0] != "":
            for idx, row in df_real_news.iterrows():
                with st.container(border=True):
                    st.caption(f"📅 {row['게시일 / 출처']}")
                    st.markdown(f"<a href='{row['링크']}' target='_blank' style='font-size:15px; font-weight:bold; color:#4da6ff; text-decoration:none;'>{row['원본제목']} 🔗</a>", unsafe_allow_html=True)
        else:
            st.dataframe(df_real_news, use_container_width=True, hide_index=True)
                
    st.divider()
    st.markdown("### 📊 키워드 검색비율 추이")
    st.caption("Naver DataLab 연동 차트")
    if uploaded_dl is not None:
        try:
            file_ext = uploaded_dl.name.split('.')[-1].lower()
            if file_ext == 'csv':
                df_dl = pd.read_csv(uploaded_dl, skiprows=6, encoding='cp949')
            elif file_ext in ['xlsx', 'xls']:
                df_dl = pd.read_excel(uploaded_dl, skiprows=6)
            else:
                st.error("지원하지 않는 파일 형식입니다. CSV나 Excel 파일을 업로드해주세요.")
                df_dl = pd.DataFrame()

            if not df_dl.empty:
                master_date = df_dl.iloc[:, 0]
                value_cols = [col for col in df_dl.columns if '날짜' not in col and 'Unnamed' not in col]
                clean_df = pd.DataFrame({'날짜': master_date})
                for col in value_cols:
                    clean_df[col] = df_dl[col]
                clean_df['날짜'] = pd.to_datetime(clean_df['날짜'])
                recent_14d_mean = clean_df.tail(14).mean(numeric_only=True).round(1)
                dl_summary_text = "\n".join([f"- {idx}: {val}" for idx, val in recent_14d_mean.items()])
                st.session_state['dl_summary'] = dl_summary_text
                df_melted = clean_df.melt(id_vars=['날짜'], var_name='종목명', value_name='검색량')
                
                fig_trend = px.line(df_melted, x='날짜', y='검색량', color='종목명', template="plotly_dark")
                fig_trend.update_layout(height=450, margin=dict(l=20, r=20, t=20, b=20), xaxis_title=None, yaxis_title="상대적 검색량 (최대 100)", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_trend, use_container_width=True)
        except Exception as e:
            st.error(f"파일 처리 중 오류가 발생했습니다: {e}")
    else:
        st.info("👈 좌측 사이드바에 Naver DataLab 파일을 업로드하시면 트렌드 차트가 활성화됩니다.")

# =========================================================================
# --- Tab 4: [주간 거래량 추이] ---
# =========================================================================
with tabs[4]:
    st.markdown("### 📊 선택 ETF 실제 주간 거래량 추이")
    if uploaded_excel is not None and not df_source.empty and '종목명' in df_source.columns:
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
        st.info("좌측 사이드바에 엑셀 데이터를 업로드해주세요.")

# =========================================================================
# --- Tab 5: [진행 이벤트] ---
# =========================================================================
with tabs[5]:
    st.markdown("### 📊 이벤트 성과 분석기 (수급 임팩트 트래킹)")
    st.caption("아래 뉴스 스크랩에서 확인한 이벤트 진행 기간을 바탕으로, 자사와 타사 ETF의 실제 순매수 유입 효과(ROI)를 직관적으로 비교 분석합니다.")
    if uploaded_excel is not None:
        temp_list_df = load_and_clean_excel(uploaded_excel, available_weeks[0])
        if '종목명' in temp_list_df.columns:
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
                with c_a1:
                    ana_start = st.selectbox("📈 전체 분석 시작 주차:", options=available_weeks[::-1], index=0)
                with c_a2:
                    ana_end = st.selectbox("📈 전체 분석 종료 주차:", options=available_weeks, index=0)
                c_h1, c_h2 = st.columns(2)
                with c_h1:
                    hl_start = st.selectbox("🖍️ 이벤트 시작 주차 (하이라이트):", options=available_weeks[::-1], index=0)
                with c_h2:
                    hl_end = st.selectbox("🖍️ 이벤트 종료 주차 (하이라이트):", options=available_weeks, index=0)

            s_idx = available_weeks.index(ana_start)
            e_idx = available_weeks.index(ana_end)
            target_sheets = available_weeks[s_idx:e_idx+1] if s_idx < e_idx else available_weeks[e_idx:s_idx+1]
            target_sheets = target_sheets[::-1] 

            trend_data = []
            with st.spinner("수급 데이터를 렌더링하고 있습니다..."):
                for w in target_sheets:
                    t_df = load_and_clean_excel(uploaded_excel, w)
                    if '종목명' in t_df.columns:
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
        st.info("👈 좌측 사이드바에 엑셀 데이터를 업로드하시면 성과 분석기 차트가 연동됩니다.")

    st.divider()
    st.markdown("### 🎉 운용사별 ETF 진행 이벤트 (뉴스 보도자료 스크랩)")
    col_d1, col_d2, _ = st.columns([2, 2, 6])
    with col_d1:
        evt_start = st.date_input("🗓️ 시작일 선택", datetime.today() - timedelta(days=30))
    with col_d2:
        evt_end = st.date_input("🗓️ 종료일 선택", datetime.today())
    st.divider()
    if evt_start > evt_end:
        st.error("🚨 시작일이 종료일보다 늦을 수 없습니다.")
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
                                st.markdown(f"**<a href='{row['text'] if 'text' in row else row['링크']}' target='_blank' style='color:#4da6ff; text-decoration:none;'>{row['원본제목']}</a>**", unsafe_allow_html=True)
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

# =========================================================================
# --- Tab 6: [고객 UX 분석] (3개월 무제한 로직 적용 및 디시인사이드 완전 삭제) ---
# =========================================================================
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
                st.info("수집 장벽 완화 수 조건 하에서도 매칭된 악플 피드가 현재 부재합니다.")
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

# =========================================================================
# --- Tab 7: [경쟁사 동향] ---
# =========================================================================
with tabs[7]:
    st.markdown("### 🏢 타사 공식 마케팅 채널 동향 (실시간 RSS)")
    st.caption("경쟁 운용사들의 네이버 블로그 최신 피드를 정기 구독하여 상품 세일즈 메시지를 역추적합니다.")
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
        "🔵 WON ETF (우리자산운용)": ("wooriam_kr", "https://blog.naver.com/wooriam_kr"),
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

# =========================================================================
# --- Tab 8: [ETF 운용 현황] ---
# =========================================================================
with tabs[8]:
    st.markdown("### 🏢 국내 ETF 운용사 AUM 시장 점유율 및 테마별 현황 (실시간 기준)")
    col_pie, col_table = st.columns([1, 2])
    pivot_df = pd.DataFrame()
    with st.spinner("KRX 마켓 캡 데이터를 고속 파싱 중입니다..."):
        try:
            df_all_etf = fdr.StockListing('ETF/KR')
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
    if uploaded_excel is not None:
        col_theme, col_weeks = st.columns(2)
        with col_theme: selected_theme = st.selectbox("분석할 테마 선택:", list(pivot_df.index) if not pivot_df.empty else ['🤖 AI & 반도체'])
        with col_weeks: n_weeks = st.slider("조회할 과거 주차 (N주):", min_value=1, max_value=len(available_weeks), value=min(4, len(available_weeks)))
        trend_data = []
        for w in available_weeks[:n_weeks][::-1]:
            try:
                temp_df = load_and_clean_excel(uploaded_excel, w)
                if '종목명' in temp_df.columns:
                    temp_df = temp_df[temp_df['종목명'] != '전체'].copy()
                    temp_df['브랜드'] = temp_df['종목명'].apply(lambda x: str(x).split(' ')[0]).replace('KBSTAR', 'RISE')
                    temp_df['분류_테마'] = temp_df['종목명'].apply(assign_auto_theme)
                    theme_df = temp_df[(temp_df['분류_테마'] == selected_theme) & (temp_df['브랜드'].isin(target_brands))].copy()
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

# =========================================================================
# --- Tab 9: [글로벌 공백 & 정책 동향] ---
# =========================================================================
with tabs[9]:
    st.markdown("### 🇺🇸 글로벌 혁신 구조 공백 분석 (US Mega Trends vs KODEX)")
    raw_keywords = ["타겟 인컴 ETF 버퍼형", "0DTE 초단기 옵션 커버드콜 ETF", "가상자산 비트코인 현물 ETF", "BDC BDC 대체투자", "하방 방어형 100% 버퍼 ETF"]
    trend_strengths = []
    for kw in raw_keywords:
        c = len(get_realtime_news(kw, timeframe="7d", max_items=10))
        trend_strengths.append("🔥🔥🔥 최고조" if c >= 5 else ("🔥🔥 강세" if c >= 2 else "🔥 꾸준함"))
    st.dataframe(pd.DataFrame({"혁신 상품 구조 (미국 메가 트렌드)": raw_keywords, "최근 뉴스 기반 유입 강도": trend_strengths, "KODEX 라인업 현황": ["공백 (0개)", "일부 유사 (1개)", "규제 한계 (0개)", "규제 한계 (0개)", "공백 (0개)"], "전략적 제언 (Action Plan)": ["즉시 벤치마킹 기획 가동", "분배율 메시지 고도화", "정책 완화 시그널 추적", "법안 통과 즉시 선점", "하락장 방어 포트폴리오 설계"]}), use_container_width=True, hide_index=True)
    
    st.divider()
    selected_trend_label = st.selectbox("🔍 뉴스 검색망 가동할 혁신 구조 선택:", options=raw_keywords, index=2)
    st.markdown(f"#### 📡 `[실시간 정책 시그널]` {selected_trend_label} 관련 완화 동향")
    df_gap_news = get_realtime_news(selected_trend_label + " 금융위 규제", timeframe="7d")
    if "링크" in df_gap_news.columns and df_gap_news["링크"].iloc[0] != "":
        cols_grid = st.columns(2)
        for idx, row in df_gap_news.iterrows():
            with cols_grid[idx % 2]:
                with st.container(border=True):
                    st.caption(f"📅 {row['게시일 / 출처']}")
                    st.markdown(f"<a href='{row['링크']}' target='_blank' style='font-size:14px; font-weight:bold; color:#ffb04d; text-decoration:none;'>[규제] {row['원본제목']} 🔗</a>", unsafe_allow_html=True)

# =========================================================================
# --- Tab 10: [AI 분석용 프롬프트 생성기] ---
# =========================================================================
with tabs[10]:
    st.markdown("### 🧠 전술 & 전략 AI 프롬프트 자동 생성기")
    data_context = df_scatter.sort_values(by='주간 수익률(%)', ascending=False).head(20).to_string(index=False) if 'df_scatter' in locals() and not df_scatter.empty else "데이터 부족"
    dl_context = st.session_state.get('dl_summary', "데이터랩 미연동")
    market_sentiment = st.session_state.get('market_sentiment', "혼조세 지속")
    current_trend = st.session_state.get('selected_trend_label', "가상자산/옵션형")

    prompt_1 = f"너는 KODEX 마케팅 총괄 최고책임자(CMO)야. 다음 지표를 기반으로 마케팅 전술 리포트를 세부 작성해줘.\n\n[수급현황]\n{data_context}\n\n[포털 검색량]\n{dl_context}\n\n[시장심리]\n{market_sentiment}"
    prompt_2 = f"너는 KODEX 신상품 전략 수석 기획자야. 미국 {current_trend} 자금 쏠림 현상과 국내 규제 리스크 장벽을 해소하며 선점할 수 있는 차기 ETF 기획 초안을 설계해줘."
    
    st.markdown("#### 🔵 `[Track 1]` 주간 마케팅 & 세일즈 대응 전략 도출용")
    st.code(prompt_1, language="text")
    st.markdown("#### 🔴 `[Track 2]` 상품 기획 및 글로벌 장벽 선점 전략 도출용")
    st.code(prompt_2, language="text")
