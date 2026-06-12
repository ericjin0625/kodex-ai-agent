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

for i in [2, 4, 5, 6]:
    with tabs[i]:
        st.warning(f"🚧 {tab_names[i]} 탭은 기획안을 바탕으로 순차적으로 구현될 예정입니다.")


# 공통 데이터 클렌징 함수
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
# --- Tab 1: [ETF 순매수 등락, 수익률] (완벽 복원) ---
# =========================================================================
with tabs[1]:
    st.markdown("### 📈 기간별 ETF 순매수 현황")
    
    col_start, col_end, col_text, col_slider = st.columns([1.5, 1.5, 2, 3])
    with col_start:
        start_week = st.selectbox("시작 주차:", options=available_weeks[::-1], index=0, key="start_week")
    with col_end:
        end_week = st.selectbox("종료 주차:", options=available_weeks, index=0, key="end_week")
    with col_text:
        st.markdown(f"<p style='margin-top: 30px; font-weight: bold;'>부터 &nbsp;&nbsp; {end_week} 까지의</p>", unsafe_allow_html=True)
    with col_slider:
        top_n_tab2 = st.slider("TOP N개 ETF 순매수 순위:", min_value=10, max_value=100, value=50, step=10, key="top_n_tab2", label_visibility="collapsed")
        st.markdown(f"<p style='text-align:right; color:red; font-weight:bold; margin-top:-10px;'>{top_n_tab2}</p>", unsafe_allow_html=True)
    
    st.divider()

    df_tab2_combined = pd.DataFrame()
    
    if uploaded_excel is not None:
        try:
            start_idx = available_weeks.index(start_week) if start_week in available_weeks else -1
            end_idx = available_weeks.index(end_week) if end_week in available_weeks else -1
            
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
            else:
                st.warning("시작 주차가 종료 주차보다 과거여야 합니다.")
        except Exception as e:
            st.error(f"데이터 병합 중 오류 발생: {e}")
    
    if df_tab2_combined.empty:
        mock_data_tab2 = {
            "종목명": ["TIGER SK하이닉스단일종목레버리지", "KODEX SK하이닉스단일종목레버리지", "TIGER 미국우량테크", "SOL AI반도체TOP2플러스", "KODEX 삼성전자단일종목레버리지", "TIGER 삼성전자단일종목레버리지", "KODEX 코스닥150레버리지", "KODEX 200"],
            "전체순매수": [4000000000, 3800000000, 2500000000, 2100000000, 1800000000, 1500000000, 1200000000, 900000000],
            "개인": [3500000000, 3200000000, 1500000000, 1800000000, 1200000000, 1100000000, 800000000, 400000000],
            "기관": [200000000, 300000000, 500000000, 200000000, 400000000, 300000000, 200000000, 300000000],
            "외국인": [300000000, 300000000, 500000000, 100000000, 200000000, 100000000, 200000000, 200000000]
        }
        df_tab2_combined = pd.DataFrame(mock_data_tab2)

    st.markdown("#### 전체 순매수 금액")
    df_total = df_tab2_combined.sort_values(by="전체순매수", ascending=False).head(top_n_tab2)
    
    with st.container(border=True):
        fig_total = px.bar(
            df_total, x="전체순매수", y="종목명", orientation='h',
            color_discrete_sequence=['#4da6ff']
        )
        fig_total.update_layout(
            yaxis={'categoryorder':'total ascending'}, 
            height=500, template="plotly_dark",
            xaxis_title="change", yaxis_title=None
        )
        st.plotly_chart(fig_total, use_container_width=True)
        
    st.divider()

    col_inv_title, col_inv_drop = st.columns([2, 8])
    with col_inv_title:
        st.markdown("#### 투자자별 순매수 금액")
    with col_inv_drop:
        inv_type_tab2 = st.selectbox("투자자 선택", ["개인", "기관", "외국인"], label_visibility="collapsed", key="inv_type_tab2")
        
    df_inv = df_tab2_combined.sort_values(by=inv_type_tab2, ascending=False).head(top_n_tab2)
    
    with st.container(border=True):
        fig_inv = px.bar(
            df_inv, x=inv_type_tab2, y="종목명", orientation='h',
            color_discrete_sequence=['#4da6ff']
        )
        fig_inv.update_layout(
            yaxis={'categoryorder':'total ascending'}, 
            height=500, template="plotly_dark",
            xaxis_title="change", yaxis_title=None
        )
        st.plotly_chart(fig_inv, use_container_width=True)

# =========================================================================
# --- Tab 3: [주간 거래대금 추이] ---
# =========================================================================
with tabs[3]:
    st.markdown("### 📊 선택 ETF 주간 거래대금 추이 (최대 12개)")
    
    available_etfs = ["KODEX 미국배당커버드콜액티브", "TIGER 미국배당다우존스", "PLUS 고배당주위클리커버드콜", "ACE 미국배당다우존스", "KODEX 고배당", "TIGER 고배당"]
    if uploaded_excel is not None and not df_source.empty and '종목명' in df_source.columns:
        extracted_etfs = df_source[df_source['종목명'] != '전체']['종목명'].dropna().unique().tolist()
        if extracted_etfs:
            available_etfs = extracted_etfs

    selected_etfs = st.multiselect(
        "검색 및 선택 (아래 빈칸을 클릭하거나 타이핑하세요):", 
        options=available_etfs, 
        default=available_etfs[:4] if len(available_etfs) >= 4 else available_etfs, 
        max_selections=12
    )
    
    st.divider()

    if selected_etfs:
        cols = st.columns(2)
        
        for i, etf_name in enumerate(selected_etfs):
            with cols[i % 2]: 
                dates = [(datetime.today() - timedelta(weeks=x)).strftime('%Y-%m-%d') for x in range(7, -1, -1)]
                np.random.seed(len(etf_name) + i) 
                volumes = np.random.randint(10, 150, size=8) + np.random.rand(8).round(1)
                
                df_vol = pd.DataFrame({'주 시작일': dates, '거래대금 (십억 원)': volumes})
                
                fig_line = px.line(
                    df_vol, x='주 시작일', y='거래대금 (십억 원)', 
                    title=f"**{etf_name}** 주간 거래대금 추이", 
                    markers=True, 
                    color_discrete_sequence=['#4da6ff']
                )
                
                fig_line.update_layout(
                    height=350, 
                    template="plotly_dark",
                    margin=dict(l=20, r=20, t=50, b=20),
                    xaxis_title=None, 
                    yaxis_title="거래대금 (십억 원)"
                )
                
                fig_line.update_traces(textposition="top center", text=df_vol['거래대금 (십억 원)'].astype(str))
                
                st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("👆 위 검색바에서 거래대금 추이를 확인할 ETF를 선택해주세요.")
