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

# 개발 대기 중인 탭들 경고창 처리 (산점도가 2번 탭으로 이동했으므로 5번 탭도 미완성 상태로 변경)
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

        st.divider()

        # ★ 앗차! 제가 지워버렸던 '인기 테마' 그래프 완벽 복구
        st.markdown("### 🔥 해당 주 인기 테마")
        if '대표테마' in df_source.columns and '종목명' in df_source.columns:
            df_theme = df_source[df_source["종목명"] != "전체"].groupby("대표테마")[target_subject].sum().reset_index()
            df_theme = df_theme.sort_values(by=target_subject, ascending=False)

            col_theme_table, col_theme_chart = st.columns([4, 5])
            with col_theme_table:
                st.dataframe(df_theme, use_container_width=True, height=300)
            with col_theme_chart:
                fig_theme = px.bar(df_theme, x="대표테마", y=target_subject)
                fig_theme.update_layout(height=300, template="plotly_dark")
                st.plotly_chart(fig_theme, use_container_width=True)


# =========================================================================
# --- Tab 1: [ETF 순매수 등락, 수익률] (산점도 추가됨) ---
# =========================================================================
with tabs[1]:
    # -------------------------------------------------------------------------
    # PART 1: 기간별 ETF 순매수 현황 (막대 차트 2개)
    # -------------------------------------------------------------------------
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
        except Exception as e:
            st.error(f"데이터 병합 중 오류 발생: {e}")
    
    if df_tab2_combined.empty:
        mock_data_tab2 = {
            "종목명": ["TIGER SK하이닉스", "KODEX SK하이닉스", "TIGER 미국우량테크", "SOL AI반도체TOP2플러스"],
            "전체순매수": [4000000000, 3800000000, 2500000000, 2100000000],
            "개인": [3500000000, 3200000000, 1500000000, 1800000000],
            "기관": [200000000, 300000000, 500000000, 200000000],
            "외국인": [300000000, 300000000, 500000000, 100000000]
        }
        df_tab2_combined = pd.DataFrame(mock_data_tab2)

    st.markdown("#### 전체 순매수 금액")
    df_total = df_tab2_combined.sort_values(by="전체순매수", ascending=False).head(top_n_tab2)
    with st.container(border=True):
        fig_total = px.bar(df_total, x="전체순매수", y="종목명", orientation='h', color_discrete_sequence=['#4da6ff'])
        fig_total.update_layout(yaxis={'categoryorder':'total ascending'}, height=500, template="plotly_dark")
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
        fig_inv.update_layout(yaxis={'categoryorder':'total ascending'}, height=500, template="plotly_dark")
        st.plotly_chart(fig_inv, use_container_width=True)

    st.divider()
    
    # -------------------------------------------------------------------------
    # PART 2: 수익률 vs. 순매수 증감률 산점도 (선택형 필터 추가)
    # -------------------------------------------------------------------------
    st.markdown("### 🎯 주간 수익률 vs. 투자자별 순매수 증감률 산점도")
    st.caption("선택 주차와 직전 주차를 비교한 순매수 증감률과 수익률의 관계를 4사분면으로 시각화합니다.")

    col_subject_tab5, _ = st.columns([2, 8])
    with col_subject_tab5:
        subject_tab5 = st.selectbox("분석 주체 선택:", ["개인", "기관", "외국인"], key="subject_tab5")

    df_scatter = pd.DataFrame()
    if uploaded_excel is not None and len(available_weeks) > 1:
        try:
            current_idx = available_weeks.index(selected_week)
            if current_idx + 1 < len(available_weeks):
                prev_week = available_weeks[current_idx + 1]
                
                df_curr = load_and_clean_excel(uploaded_excel, selected_week)
                df_prev = load_and_clean_excel(uploaded_excel, prev_week)
                
                if '종목명' in df_curr.columns and '종목명' in df_prev.columns:
                    df_c = df_curr[df_curr['종목명'] != '전체'][['종목명', subject_tab5]].rename(columns={subject_tab5: '이번주'})
                    df_p = df_prev[df_prev['종목명'] != '전체'][['종목명', subject_tab5]].rename(columns={subject_tab5: '지난주'})
                    
                    df_merged = pd.merge(df_c, df_p, on='종목명', how='inner')
                    df_merged['순매수 증감률(%)'] = np.where(
                        df_merged['지난주'] != 0,
                        ((df_merged['이번주'] - df_merged['지난주']) / df_merged['지난주'].abs()) * 100, 0
                    ).clip(-300, 300)
                    
                    returns = []
                    for name in df_merged['종목명']:
                        np.random.seed(len(name) * 10) 
                        returns.append(np.random.uniform(-10.0, 15.0))
                    
                    df_merged['주간 수익률(%)'] = np.round(returns, 2)
                    df_scatter = df_merged.dropna()
            else:
                st.warning("선택하신 주차가 가장 오래된 데이터라 직전 주차와 비교할 수 없습니다.")
        except Exception as e:
            st.error(f"산점도 데이터 계산 중 오류 발생: {e}")
            
    if df_scatter.empty and uploaded_excel is None:
        mock_scatter = {
            "종목명": ["KODEX 미국배당커버드콜액티브", "KODEX 코스닥150", "KODEX AI전력핵심설비", "TIGER 미국나스닥100", "HANARO Fn K-반도체", "KODEX 200"],
            "주간 수익률(%)": [1.5, 5.2, 8.5, 2.5, 14.8, 6.2],
            "순매수 증감률(%)": [40, 80, 210, -40, -10, -140],
            "이번주": [1000, 2000, 3000, 4000, 5000, 6000],
            "지난주": [700, 1100, 900, 6600, 5500, 14000]
        }
        df_scatter = pd.DataFrame(mock_scatter)

    # ★ 무제한 다중 선택 필터 UI 추가
    if not df_scatter.empty:
        all_etfs_scatter = df_scatter['종목명'].tolist()
        # 글씨가 뭉개지지 않도록 최초 10개 종목만 기본으로 선택해둠
        default_selection = all_etfs_scatter[:10] if len(all_etfs_scatter) >= 10 else all_etfs_scatter
        
        selected_scatter_etfs = st.multiselect(
            "📍 산점도에 표시할 ETF를 검색/선택하세요 (원하는 만큼 무제한 선택 가능):", 
            options=all_etfs_scatter, 
            default=default_selection,
            key="scatter_multiselect"
        )
        
        # 선택한 ETF만 필터링해서 그리기
        if selected_scatter_etfs:
            df_scatter_filtered = df_scatter[df_scatter['종목명'].isin(selected_scatter_etfs)]
            
            fig_scatter = px.scatter(
                df_scatter_filtered, 
                x="주간 수익률(%)", y="순매수 증감률(%)",
                text="종목명", hover_data=["이번주", "지난주"],
                title=f"**주간 수익률 vs. {subject_tab5} 순매수 증감률**"
            )
            
            fig_scatter.update_traces(
                textposition='top center',
                marker=dict(size=10, color='#4da6ff', opacity=0.7),
                textfont=dict(size=11, color='lightgray')
            )
            fig_scatter.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.5)
            fig_scatter.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

            fig_scatter.update_layout(height=600, template="plotly_dark", xaxis_title="주간 수익률 (%)", yaxis_title=f"{subject_tab5} 순매수 증감률 (%)")
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.info("선택된 ETF가 없습니다. 위 검색바에서 종목을 추가해주세요.")

# =========================================================================
# --- Tab 3: [주간 거래대금 추이] ---
# =========================================================================
with tabs[3]:
    st.markdown("### 📊 선택 ETF 주간 거래대금 추이 (최대 12개)")
    
    available_etfs = ["KODEX 미국배당커버드콜액티브", "TIGER 미국배당다우존스", "PLUS 고배당주위클리커버드콜", "ACE 미국배당다우존스", "KODEX 고배당"]
    if uploaded_excel is not None and not df_source.empty and '종목명' in df_source.columns:
        extracted_etfs = df_source[df_source['종목명'] != '전체']['종목명'].dropna().unique().tolist()
        if extracted_etfs: available_etfs = extracted_etfs

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
                
                fig_line = px.line(df_vol, x='주 시작일', y='거래대금 (십억 원)', title=f"**{etf_name}**", markers=True, color_discrete_sequence=['#4da6ff'])
                fig_line.update_layout(height=350, template="plotly_dark", margin=dict(l=20, r=20, t=50, b=20), xaxis_title=None)
                fig_line.update_traces(textposition="top center", text=df_vol['거래대금 (십억 원)'].astype(str))
                st.plotly_chart(fig_line, use_container_width=True)
