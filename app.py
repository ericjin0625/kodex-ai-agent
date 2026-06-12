import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import google.generativeai as genai

# 1. 페이지 레이아웃 및 기본 테마 설정
st.set_page_config(page_title="ETF Monitoring AI Agent", layout="wide")

# 2. 안전한 API 키 로드 (따옴표나 공백이 섞여도 자동 제거하도록 안전장치 추가)
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

# 4. 엑셀 시트 동적 파싱 및 주차(Week) 리스트 추출
available_weeks = ["5.17~5.23", "5.10~5.16", "5.03~5.09"] # 파일 업로드 전 기본 가상 주차

if uploaded_excel is not None:
    xls = pd.ExcelFile(uploaded_excel)
    sheet_names = [sheet for sheet in xls.sheet_names if sheet != "참고사항"]
    if sheet_names:
        available_weeks = sheet_names[::-1] 

# 5. 상단 헤더 및 동적 주차 필터
col_title, col_week = st.columns([3, 1])
with col_title:
    st.title("ETF Monitoring AI Agent")
with col_week:
    selected_week = st.selectbox("주차 (최대 6개월 전까지 선택 가능):", options=available_weeks, index=0)

# 6. 하위 탭 메뉴 생성
tab_names = [
    "[Weekly Info.]", "[ETF 순매수 등락, 수익률]", "[뉴스, 검색량, 종토방 분석]", 
    "[주간 거래대금 추이]", "[진행 이벤트]", "[AI 분석 및 인사이트]", "[ETF 운용 현황]"
]
tabs = st.tabs(tab_names)

for i in range(1, len(tab_names)):
    with tabs[i]:
        st.warning(f"🚧 {tab_names[i]} 탭은 기획안을 바탕으로 순차적으로 구현될 예정입니다.")

# =========================================================================
# --- Tab 0: [Weekly Info.] ---
# =========================================================================
with tabs[0]:
    
    # -------------------------------------------------------------------------
    # PART 1: 지난 주 주요 ISSUE TOP 3 
    # -------------------------------------------------------------------------
    st.markdown("### 📰 주요 ISSUE TOP 3 <span style='font-size:12px; color:gray;'>(Gemini AI 기반 실시간 스크랩 & 요약)</span>", unsafe_allow_html=True)
    
    @st.cache_data(show_spinner="Gemini가 선택된 주차의 시장 이슈를 분석 중입니다...")
    def get_weekly_issues(week_str):
        if model:
            try:
                prompt = f"{week_str} 주차의 대한민국 ETF 시장, 주식 시장, 거시경제 관련 가장 중요한 핵심 뉴스 이슈 3가지를 요약해줘. 형식: '제목: [이슈제목]\n- [내용1]\n- [내용2]\n- [내용3]' (각 이슈는 '---'로 구분)"
                response = model.generate_content(prompt)
                return response.text.split('---')
            except Exception as e:
                # 구글 API 거절(403) 등 에러 발생 시 원인을 명확히 출력
                return [f"제목: API 연동 실패\n- 에러코드: {str(e)}\n- API 키가 'AIza'로 시작하는지 확인하세요.", "제목: - \n- -", "제목: - \n- -"]
        else:
            return ["제목: API 키 미설정\n- Streamlit Secrets 설정을 확인해주세요.", "제목: - \n- -", "제목: - \n- -"]

    issues = get_weekly_issues(selected_week)
    
    cols_issue = st.columns(3)
    for idx, col in enumerate(cols_issue):
        with col:
            with st.container(border=True):
                if idx < len(issues):
                    lines = issues[idx].strip().split('\n')
                    title = lines[0].replace("제목:", "").strip() if lines[0].startswith("제목:") else "주요 시장 이슈"
                    st.markdown(f"**🎯 {title}**")
                    for line in lines[1:]:
                        st.markdown(f"<span style='font-size:14px; color:#333;'>{line}</span>", unsafe_allow_html=True)

    st.divider()

    # -------------------------------------------------------------------------
    # PART 2: 데이터 연동 및 강력한 클렌징 (오류 원인 완벽 제거)
    # -------------------------------------------------------------------------
    if uploaded_excel is not None:
        try:
            df_source = pd.read_excel(uploaded_excel, sheet_name=selected_week)
            df_source.columns = df_source.columns.str.strip() 
            
            # ★ 핵심 해결 로직: 쉼표, 하이픈(-) 등 불순물을 제거하고 무조건 숫자로 변환
            for col in ["개인", "기관", "외국인"]:
                if col in df_source.columns:
                    clean_data = df_source[col].astype(str).str.replace(',', '', regex=False).str.replace('-', '0', regex=False)
                    df_source[col] = pd.to_numeric(clean_data, errors='coerce').fillna(0)
                    
        except Exception as e:
            st.error(f"엑셀 데이터를 읽는 중 오류가 발생했습니다: {e}")
            df_source = pd.DataFrame()
    else:
        mock_data = {
            "종목명": ["전체", "TIGER SK하이닉스단일종목레버리지", "KODEX SK하이닉스단일종목레버리지", "TIGER 미국우량테크", "SOL AI반도체TOP2플러스", "KODEX 고배당"],
            "대표테마": ["기타", "레버리지", "레버리지", "빅테크", "AI", "배당"],
            "개인": [4327874393, 1040476291, 1035108397, 888880331, 799680607, 325405611],
            "기관": [2100000000, -500000000, -480000000, 300000000, 400000000, 120000000],
            "외국인": [2227874393, 1540476291, 1515108397, 588880331, 399680607, 205405611]
        }
        df_source = pd.DataFrame(mock_data)

    # -------------------------------------------------------------------------
    # PART 3: 해당 주 순매수 ETF 순위 차트 렌더링
    # -------------------------------------------------------------------------
    if not df_source.empty:
        st.markdown("### 🏆 해당 주 순매수 ETF 순위")
        
        col_subject, col_space, col_slider = st.columns([2, 3, 3])
        with col_subject:
            target_subject = st.selectbox("주체:", ["개인", "기관", "외국인"], key="main_subject")
        with col_slider:
            top_n = st.slider("TOP N개 설정", min_value=5, max_value=50, value=10, step=5, label_visibility="collapsed")
            st.markdown(f"<p style='text-align:right; color:red; font-weight:bold; margin-top:-10px;'>{top_n}</p>", unsafe_allow_html=True)

        df_filtered = df_source.dropna(subset=[target_subject]).copy()
        if '종목명' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered["종목명"] != "전체"]
            
        df_filtered = df_filtered.sort_values(by=target_subject, ascending=False).head(top_n)

        col_table, col_chart = st.columns([4, 5])
        with col_table:
            st.dataframe(
                df_filtered[["종목명", target_subject]] if '종목명' in df_filtered.columns else df_filtered, 
                use_container_width=True, height=380
            )
            
        with col_chart:
            if '종목명' in df_filtered.columns:
                fig_etf = px.bar(
                    df_filtered, x=target_subject, y="종목명", orientation='h',
                    title=f"{target_subject} 순매수 상위 TOP {top_n}"
                )
                fig_etf.update_layout(yaxis={'categoryorder':'total ascending'}, height=380, template="plotly_dark")
                st.plotly_chart(fig_etf, use_container_width=True)
            else:
                st.warning("엑셀 파일에 '종목명' 컬럼이 존재하지 않아 그래프를 그릴 수 없습니다.")

        st.divider()

        # -------------------------------------------------------------------------
        # PART 4: 해당 주 인기 테마
        # -------------------------------------------------------------------------
        st.markdown("### 🔥 해당 주 인기 테마")
        
        if '대표테마' in df_source.columns and '종목명' in df_source.columns:
            df_theme = df_source[df_source["종목명"] != "전체"].groupby("대표테마")[target_subject].sum().reset_index()
            df_theme = df_theme.sort_values(by=target_subject, ascending=False)

            col_theme_table, col_theme_chart = st.columns([4, 5])
            with col_theme_table:
                st.dataframe(df_theme, use_container_width=True, height=300)
            with col_theme_chart:
                fig_theme = px.bar(
                    df_theme, x="대표테마", y=target_subject,
                    title=f"{selected_week} 대표테마별 {target_subject} 순매수 현황"
                )
                fig_theme.update_layout(height=300, template="plotly_dark")
                st.plotly_chart(fig_theme, use_container_width=True)
        else:
            st.info("엑셀 파일에 '대표테마' 컬럼이 없어 테마 분석을 생략합니다.")
