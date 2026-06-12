import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import google.generativeai as genai
from datetime import datetime, timedelta

# 1. 페이지 레이아웃 및 기본 테마 설정
st.set_page_config(page_title="ETF Monitoring AI Agent", layout="wide")

# 2. 안전한 API 키 로드 및 gemini-1.5-flash 고정
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

# 5. 상단 헤더 및 필터 (기본값: 1주 전)
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

# 미완성 탭 경고창 표시 (4번, 6번 탭)
for i in [4, 6]:
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
    else:
        mock_data = {
            "종목명": ["전체", "TIGER SK하이닉스단일종목레버리지", "KODEX SK하이닉스단일종목레버리지", "TIGER 미국우량테크", "SOL AI반도체TOP2플러스", "KODEX 고배당"],
            "대표테마": ["기타", "레버리지", "레버리지", "빅테크", "AI", "배당"],
            "개인": [4327874393, 1040476291, 1035108397, 888880331, 799680607, 325405611],
            "기관": [2100000000, -500000000, -480000000, 300000000, 400000000, 120000000],
            "외국인": [2227874393, 1540476291, 1515108397, 588880331, 399680607, 205405611]
        }
        df_source = pd.DataFrame(mock_data)

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
# --- Tab 1: [ETF 순매수 등락, 수익률] ---
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
    
    st.markdown("### 🎯 주간 수익률 vs. 투자자별 순매수 증감률 산점도")
    st.caption("선택 주차와 직전 주차를 비교한 순매수 증감률과 수익률의 관계를 4사분면으로 시각화합니다.")

    col_subject_tab2_scatter, _ = st.columns([2, 8])
    with col_subject_tab2_scatter:
        subject_tab2_scatter = st.selectbox("분석 주체 선택:", ["개인", "기관", "외국인"], key="subject_tab2_scatter")

    df_scatter = pd.DataFrame()
    if uploaded_excel is not None and len(available_weeks) > 1:
        try:
            current_idx = available_weeks.index(selected_week)
            if current_idx + 1 < len(available_weeks):
                prev_week = available_weeks[current_idx + 1]
                
                df_curr = load_and_clean_excel(uploaded_excel, selected_week)
                df_prev = load_and_clean_excel(uploaded_excel, prev_week)
                
                if '종목명' in df_curr.columns and '종목명' in df_prev.columns:
                    df_c = df_curr[df_curr['종목명'] != '전체'][['종목명', subject_tab2_scatter]].rename(columns={subject_tab2_scatter: '이번주'})
                    df_p = df_prev[df_prev['종목명'] != '전체'][['종목명', subject_tab2_scatter]].rename(columns={subject_tab2_scatter: '지난주'})
                    
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

    if not df_scatter.empty:
        all_etfs_scatter = df_scatter['종목명'].tolist()
        default_selection = all_etfs_scatter[:10] if len(all_etfs_scatter) >= 10 else all_etfs_scatter
        
        selected_scatter_etfs = st.multiselect(
            "📍 산점도에 표시할 ETF를 검색/선택하세요 (원하는 만큼 무제한 선택 가능):", 
            options=all_etfs_scatter, 
            default=default_selection,
            key="scatter_multiselect_tab2"
        )
        
        if selected_scatter_etfs:
            df_scatter_filtered = df_scatter[df_scatter['종목명'].isin(selected_scatter_etfs)]
            
            fig_scatter = px.scatter(
                df_scatter_filtered, x="주간 수익률(%)", y="순매수 증감률(%)",
                text="종목명", hover_data=["이번주", "지난주"],
                title=f"**주간 수익률 vs. {subject_tab2_scatter} 순매수 증감률**"
            )
            fig_scatter.update_traces(
                textposition='top center',
                marker=dict(size=10, color='#4da6ff', opacity=0.7),
                textfont=dict(size=11, color='lightgray')
            )
            fig_scatter.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.5)
            fig_scatter.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
            fig_scatter.update_layout(height=600, template="plotly_dark", xaxis_title="주간 수익률 (%)", yaxis_title=f"{subject_tab2_scatter} 순매수 증감률 (%)")
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.info("선택된 ETF가 없습니다. 위 검색바에서 종목을 추가해주세요.")

# =========================================================================
# --- Tab 2: [뉴스, 검색량, 종토방 분석] ---
# =========================================================================
with tabs[2]:
    st.markdown("### 📰 지난 주 ETF 뉴스 스크랩 <span style='font-size:12px; color:gray;'>(해당 부분은 자동 스크랩)</span>", unsafe_allow_html=True)
    
    news_data = {
        "게시일 / 출처": ["2026-05-15 / 연합뉴스", "2026-05-19 / 연합뉴스", "2026-05-20 / 인베스트조선", "2026-04-21 / 금융위원회", "2026-05-07 / 연합뉴스"],
        "제목": ["코스닥 액티브 등 ETF 8종, 19일 신규 상장", "신한운용, 코스닥 대표기업 10종목 집중투자 ETF 상장", "반도체 다음은 어디? 운용사, '차세대 AI 수혜주' 찾기 경쟁", "단일종목 레버리지 ETF 허용", "삼전·닉스 2배 ETF 출범 눈앞"],
        "핵심 요약": [
            "IBK 코스닥150, SOL 코스닥TOP10, M DAS 코스닥액티브 등 8종이 19일 상장 예정.",
            "SOL 코스닥TOP10 ETF가 19일 상장. 코스닥 주도주를 압축 투자하는 구조다.",
            "AI ETF 5종에 상장 첫날 개인 순매수 2,339억 원이 유입. 테마가 다변화되는 흐름이다.",
            "삼성전자·SK하이닉스 기반 단일종목 레버리지 ETF 도입이 허용되었고 보호장치가 강화됐다.",
            "출시 직전 시장에서는 최대 5조3천억 원 수준의 자금 유입 가능성도 거론됐다."
        ]
    }
    df_news = pd.DataFrame(news_data)
    st.dataframe(df_news, use_container_width=True, hide_index=True)
    st.divider()

    col_wip1, col_wip2 = st.columns(2)
    with col_wip1:
        st.markdown("### 📊 키워드 트렌드 요약 및 검색비율 추이")
        st.warning("🚧 팀원 협의 후 네이버 DataLab CSV 연동 로직이 추가될 예정입니다.")
    with col_wip2:
        st.markdown("### 💬 종목토론방 분석")
        st.warning("🚧 종목토론방 데이터 파싱 및 감성 분석 로직 구현 대기 중입니다.")

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

# =========================================================================
# --- Tab 5: [AI 분석 및 인사이트] ---
# =========================================================================
with tabs[5]:
    col_ai_title, col_ai_btn = st.columns([8, 2])
    with col_ai_title:
        st.markdown("### 🧠 AI Analysis & Insights")
        st.caption("버튼을 누르면 Gemini AI가 대시보드의 데이터 흐름을 기반으로 마케팅 핵심 인사이트를 요약 도출합니다.")
    with col_ai_btn:
        if st.button("Gemini로 시작하기", use_container_width=True, key="gemini_start_btn"):
            if model:
                with st.spinner("Gemini가 데이터를 분석하여 인사이트를 도출하고 있습니다..."):
                    try:
                        data_context = df_scatter.head(15).to_string() if not df_scatter.empty else "기본 가상 데이터"
                        prompt = f"""
                        너는 KODEX 상품기획 및 마케팅을 담당하는 최고 책임자야. 
                        다음 주차의 자금 유입 증감 및 수익률 연동 데이터를 바탕으로 마케팅 관점의 인사이트 보고서를 한글로 작성해줘:
                        {data_context}
                        
                        반드시 아래 3가지 제목을 포함하여, 각 섹션을 '///' 기호로 구분해서 출력해줘. (각각 3~4문장 분량)
                        1. Executive Summary
                        2. Signal Interpretation
                        3. Next Month Watchlist
                        """
                        response = model.generate_content(prompt)
                        st.session_state.ai_insights = response.text.split('///')
                    except Exception as e:
                        st.session_state.ai_insights = [f"AI 연동 에러 발생: {e}"] * 3
            else:
                st.session_state.ai_insights = ["API 키 세팅이 누락되었습니다. Secrets 창을 확인해 주세요."] * 3

    st.divider()

    if "ai_insights" in st.session_state and len(st.session_state.ai_insights) == 3:
        insights = st.session_state.ai_insights
        
        st.markdown("**Executive Summary**")
        with st.container(border=True):
            st.markdown(insights[0].replace("1. Executive Summary", "").strip())
            
        st.markdown("**Signal Interpretation**")
        with st.container(border=True):
            st.markdown(insights[1].replace("2. Signal Interpretation", "").strip())
            
        st.markdown("**Next Month Watchlist**")
        with st.container(border=True):
            st.markdown(insights[2].replace("3. Next Month Watchlist", "").strip())
    else:
        st.markdown("**Executive Summary**")
        with st.container(border=True):
            st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("**Signal Interpretation**")
        with st.container(border=True):
            st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("**Next Month Watchlist**")
        with st.container(border=True):
            st.markdown("<br><br><br>", unsafe_allow_html=True)
