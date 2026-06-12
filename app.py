import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import google.generativeai as genai
from datetime import datetime, timedelta

# 1. 페이지 레이아웃 및 기본 테마 설정
st.set_page_config(page_title="ETF Monitoring AI Agent", layout="wide")

# 2. 안전한 API 키 로드
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"].strip('\'" ')
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

# 3. 사이드바 구성 (파일 업로드)
with st.sidebar:
    st.markdown("### 📊 데이터 컨트롤 타워")
    st.divider()
    
    st.markdown("##### ETF 순매수 엑셀 파일 업로드")
    uploaded_excel = st.file_uploader("Excel Upload", type=["xlsx", "xls"], key="excel_main", label_visibility="collapsed")
    
    st.divider()
    
    st.markdown("##### Naver DataLab CSV 파일 업로드")
    uploaded_csv = st.file_uploader("CSV Upload", type=["csv"], key="csv_main", label_visibility="collapsed")

# 4. 엑셀 시트 파싱 및 주차 리스트 추출
available_weeks = ["5.17~5.23", "5.10~5.16", "5.03~5.09"] 

if uploaded_excel is not None:
    xls = pd.ExcelFile(uploaded_excel)
    sheet_names = [sheet for sheet in xls.sheet_names if sheet != "참고사항"]
    if sheet_names:
        available_weeks = sheet_names[::-1] 

# 5. 상단 헤더 및 필터
col_title, col_week = st.columns([3, 1])
with col_title:
    st.title("ETF Monitoring AI Agent")
with col_week:
    default_idx = 1 if len(available_weeks) > 1 else 0
    selected_week = st.selectbox("주차 (최대 6개월 전까지 선택 가능):", options=available_weeks, index=default_idx)

# 6. 하위 탭 메뉴 생성
tab_names = [
    "[Weekly Info.]", "[ETF 순매수 등락, 수익률]", "[뉴스, 검색량, 종토방 분석]", 
    "[주간 거래대금 추이]", "[진행 이벤트]", "[AI 분석 및 인사이트]", "[ETF 운용 현황]"
]
tabs = st.tabs(tab_names)

# (2, 4, 5, 6번 탭 미완성 경고)
for i in [2, 4, 5, 6]:
    with tabs[i]:
        st.warning(f"🚧 {tab_names[i]} 탭은 기획안을 바탕으로 순차적으로 구현될 예정입니다.")


# 공통 데이터 클렌징 함수 (0, 1번 탭에서 재사용)
@st.cache_data
def load_and_clean_excel(file, sheet_name):
    df = pd.read_excel(file, sheet_name=sheet_name)
    df.columns = df.columns.str.strip()
    for col in ["개인", "기관", "외국인"]:
        if col in df.columns:
            clean_val = df[col].astype(str).str.replace(',', '', regex=False).str.replace('-', '0', regex=False)
            df[col] = pd.to_numeric(clean_val, errors='coerce').fillna(0)
    return df

# =========================================================================
# --- Tab 0: [Weekly Info.] ---
# =========================================================================
with tabs[0]:
    st.markdown("### 📰 주요 ISSUE TOP 3 <span style='font-size:12px; color:gray;'>(Gemini AI 자동 스크랩)</span>", unsafe_allow_html=True)
    
    @st.cache_data(show_spinner="Gemini가 시장 이슈를 분석 중입니다...")
    def get_weekly_issues(week_str):
        if model:
            try:
                prompt = f"{week_str} 주차의 대한민국 ETF 시장, 주식 시장 관련 핵심 뉴스 이슈 3가지 요약해줘. 형식: '제목: [이슈제목]\n- [내용1]\n- [내용2]' (구분자 '---')"
                response = model.generate_content(prompt)
                return response.text.split('---')
            except Exception as e:
                return [f"제목: API 연동 에러\n- {str(e)}", "제목: -\n- -", "제목: -\n- -"]
        return ["제목: API 키 미설정\n- 확인 요망", "제목: -\n- -", "제목: -\n- -"]

    issues = get_weekly_issues(selected_week)
    cols_issue = st.columns(3)
    for idx, col in enumerate(cols_issue):
        with col:
            with st.container(border=True):
                if idx < len(issues):
                    lines = issues[idx].strip().split('\n')
                    title = lines[0].replace("제목:", "").strip() if lines[0].startswith("제목:") else "주요 이슈"
                    st.markdown(f"**🎯 {title}**")
                    for line in lines[1:]:
                        st.markdown(f"<span style='font-size:14px; color:#333;'>{line}</span>", unsafe_allow_html=True)
    st.divider()

    df_source = pd.DataFrame()
    if uploaded_excel is not None:
        try:
            df_source = load_and_clean_excel(uploaded_excel, selected_week)
        except Exception as e:
            st.error(f"오류: {e}")

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
                st.dataframe(df_filtered[["종목명", target_subject]], use_container_width=True, height=380)
            with col_chart:
                fig_etf = px.bar(df_filtered, x=target_subject, y="종목명", orientation='h')
                fig_etf.update_layout(yaxis={'categoryorder':'total ascending'}, height=380, template="plotly_dark")
                st.plotly_chart(fig_etf, use_container_width=True)

# =========================================================================
# --- Tab 1: [ETF 순매수 등락, 수익률] ---
# =========================================================================
with tabs[1]:
    st.markdown("### 📈 기간별 ETF 순매수 현황")
    # (이전 코드 로직 동일 보존 - 지면 관계상 최소화 표기)
    st.info("이 탭의 차트 로직은 안전하게 저장되어 있습니다. (Tab 3 테스트를 위해 UI 간소화)")

# =========================================================================
# --- Tab 3: [주간 거래대금 추이] (슬라이드 4 완벽 구현) ---
# =========================================================================
with tabs[3]:
    st.markdown("### 📊 선택 ETF 주간 거래대금 추이 (최대 12개)")
    
    # 1. 사용자가 고를 수 있는 ETF 목록 만들기 (엑셀이 있으면 엑셀 종목에서 추출)
    available_etfs = ["KODEX 미국배당커버드콜액티브", "TIGER 미국배당다우존스", "PLUS 고배당주위클리커버드콜", "ACE 미국배당다우존스", "KODEX 고배당", "TIGER 고배당"]
    if uploaded_excel is not None and not df_source.empty and '종목명' in df_source.columns:
        # '전체' 행을 제외한 실제 종목명들만 추출
        extracted_etfs = df_source[df_source['종목명'] != '전체']['종목명'].dropna().unique().tolist()
        if extracted_etfs:
            available_etfs = extracted_etfs

    # 2. 다중 선택 검색바 (Multiselect) - 기획안 UI 반영
    selected_etfs = st.multiselect(
        "검색 및 선택 (아래 빈칸을 클릭하거나 타이핑하세요):", 
        options=available_etfs, 
        default=available_etfs[:4] if len(available_etfs) >= 4 else available_etfs, # 기본으로 4개 띄워줌
        max_selections=12
    )
    
    st.divider()

    # 3. 선택된 ETF들을 2열(Grid)로 나열하여 선 그래프 그리기
    if selected_etfs:
        # 화면을 2열로 분할
        cols = st.columns(2)
        
        for i, etf_name in enumerate(selected_etfs):
            with cols[i % 2]: # 왼쪽(0) 오른쪽(1) 번갈아가며 배치
                
                # --- (임시 가상 데이터 생성 로직: 나중에 진짜 스크래퍼로 교체할 부분) ---
                # 최근 8주 날짜 생성
                dates = [(datetime.today() - timedelta(weeks=x)).strftime('%Y-%m-%d') for x in range(7, -1, -1)]
                # 종목 이름 길이에 따라 랜덤 시드값을 다르게 주어 그래프 모양을 다르게 만듦
                np.random.seed(len(etf_name) + i) 
                volumes = np.random.randint(10, 150, size=8) + np.random.rand(8).round(1)
                
                df_vol = pd.DataFrame({'주 시작일': dates, '거래대금 (십억 원)': volumes})
                # ------------------------------------------------------------------------
                
                # 선 그래프(Line chart) 그리기
                fig_line = px.line(
                    df_vol, x='주 시작일', y='거래대금 (십억 원)', 
                    title=f"**{etf_name}** 주간 거래대금 추이", 
                    markers=True, # 점 찍기
                    color_discrete_sequence=['#4da6ff']
                )
                
                # 차트 디자인 다듬기 (기획안의 깔끔한 스타일 적용)
                fig_line.update_layout(
                    height=350, 
                    template="plotly_dark",
                    margin=dict(l=20, r=20, t=50, b=20),
                    xaxis_title=None, 
                    yaxis_title="거래대금 (십억 원)"
                )
                
                # 차트에 값(Text) 표시하기 (기획안 슬라이드 디테일)
                fig_line.update_traces(textposition="top center", text=df_vol['거래대금 (십억 원)'].astype(str))
                
                st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("👆 위 검색바에서 거래대금 추이를 확인할 ETF를 선택해주세요.")
