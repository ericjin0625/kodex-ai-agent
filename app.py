import streamlit as st
import pandas as pd
import plotly.express as px
import FinanceDataReader as fdr
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# 1. 페이지 레이아웃 및 기본 테마 설정
st.set_page_config(page_title="ETF Monitoring AI Agent", layout="wide")

# 2. 실시간 데이터 파싱 함수 (가짜 데이터 대체용)
@st.cache_data(ttl=3600)
def get_realtime_news(keyword="ETF"):
    url = f"https://search.naver.com/search.naver?where=news&query={keyword}&sm=tab_opt&sort=1"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        news_list = []
        items = soup.select(".news_area")[:5]
        for item in items:
            title = item.select_one(".news_tit").get_text()
            press = item.select_one(".info_group").select_one(".info").get_text()
            desc = item.select_one(".news_dsc").get_text()
            date = item.select_one(".info_group").select(".info")[-1].get_text()
            news_list.append({"게시일 / 출처": f"{date} / {press}", "제목": title, "핵심 요약": desc})
        return pd.DataFrame(news_list)
    except:
        return pd.DataFrame([{"게시일 / 출처": "오류", "제목": "실시간 뉴스를 불러올 수 없습니다.", "핵심 요약": "네이버 뉴스 서버 응답 지연"}])

@st.cache_data(ttl=86400)
def get_etf_mapping():
    # KRX ETF 전체 목록을 가져와 이름과 종목코드(Symbol) 매핑
    df = fdr.StockListing('ETF/KR')
    return dict(zip(df['Name'], df['Symbol']))

def get_real_returns(symbols_dict, etf_names):
    # 선택된 ETF들의 최근 2주간 가격을 기반으로 실제 주간 수익률 계산
    end_date = datetime.today()
    start_date = end_date - timedelta(days=14)
    returns_dict = {}
    
    for name in etf_names:
        symbol = symbols_dict.get(name)
        if symbol:
            try:
                df = fdr.DataReader(symbol, start_date, end_date)
                if len(df) >= 5:
                    # 최근 종가와 5영업일(약 1주일) 전 종가 비교
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

# 3. 사이드바 구성 (파일 업로드)
with st.sidebar:
    st.markdown("### 📊 데이터 컨트롤 타워")
    st.divider()
    uploaded_excel = st.file_uploader("Excel Upload", type=["xlsx", "xls"], key="excel_main", label_visibility="collapsed")
    st.divider()
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
    st.title("ETF Monitoring AI Agent (Real-time)")
with col_week:
    default_idx = 1 if len(available_weeks) > 1 else 0
    selected_week = st.selectbox("주차 (최대 6개월 전까지 선택 가능):", options=available_weeks, index=default_idx)

# 6. 하위 탭 메뉴 생성
tab_names = [
    "[Weekly Info.]", "[ETF 순매수 등락, 수익률]", "[뉴스, 검색량, 종토방 분석]", 
    "[주간 거래대금 추이]", "[진행 이벤트]", "[AI 분석용 프롬프트]", "[ETF 운용 현황]"
]
tabs = st.tabs(tab_names)

for i in [4, 6]:
    with tabs[i]:
        st.warning(f"🚧 {tab_names[i]} 탭은 기획안을 바탕으로 순차적으로 구현될 예정입니다.")

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
# --- Tab 0: [Weekly Info.] (정량적 데이터만 유지, 이슈 요약은 삭제) ---
# =========================================================================
with tabs[0]:
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
        else:
            st.info("업로드하신 엑셀 파일에 '대표테마' 열(Column)이 존재하지 않아 테마 분석을 건너뜁니다.")
    else:
        st.info("좌측 사이드바에 엑셀 데이터를 업로드해주세요.")

# =========================================================================
# --- Tab 1: [ETF 순매수 등락, 수익률] (실시간 수익률 연동 산점도) ---
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

    if not df_tab2_combined.empty:
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
        
        # --- 실제 수익률 반영 산점도 ---
        st.markdown("### 🎯 주간 수익률 vs. 투자자별 순매수 증감률 산점도 (실시간 데이터 연동)")
        
        col_subject_tab2_scatter, _ = st.columns([2, 8])
        with col_subject_tab2_scatter:
            subject_tab2_scatter = st.selectbox("분석 주체 선택:", ["개인", "기관", "외국인"], key="subject_tab2_scatter")

        if len(available_weeks) > 1:
            with st.spinner("KRX 실시간 주식 데이터를 연동하여 실제 수익률을 계산 중입니다... (약 10초 소요)"):
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
                        
                        # ★ 가짜 랜덤 데이터 제거 및 실제 데이터 삽입
                        symbols_mapping = get_etf_mapping()
                        real_returns = get_real_returns(symbols_mapping, df_merged['종목명'].tolist())
                        df_merged['주간 수익률(%)'] = df_merged['종목명'].map(real_returns)
                        
                        df_scatter = df_merged.dropna()
                        
                        all_etfs_scatter = df_scatter['종목명'].tolist()
                        default_selection = all_etfs_scatter[:15] if len(all_etfs_scatter) >= 15 else all_etfs_scatter
                        
                        selected_scatter_etfs = st.multiselect(
                            "📍 산점도에 표시할 ETF를 선택하세요:", 
                            options=all_etfs_scatter, 
                            default=default_selection,
                            key="scatter_multiselect_tab2"
                        )
                        
                        if selected_scatter_etfs:
                            df_scatter_filtered = df_scatter[df_scatter['종목명'].isin(selected_scatter_etfs)]
                            
                            fig_scatter = px.scatter(
                                df_scatter_filtered, x="주간 수익률(%)", y="순매수 증감률(%)",
                                text="종목명", hover_data=["이번주", "지난주"],
                                title=f"**실제 수익률 vs. {subject_tab2_scatter} 순매수 증감률**"
                            )
                            fig_scatter.update_traces(
                                textposition='top center',
                                marker=dict(size=10, color='#4da6ff', opacity=0.7),
                                textfont=dict(size=11, color='lightgray')
                            )
                            fig_scatter.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.5)
                            fig_scatter.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
                            fig_scatter.update_layout(height=600, template="plotly_dark", xaxis_title="실제 주간 수익률 (%)", yaxis_title=f"{subject_tab2_scatter} 순매수 증감률 (%)")
                            st.plotly_chart(fig_scatter, use_container_width=True)
                else:
                    st.warning("직전 주차 데이터가 없어 증감률을 비교할 수 없습니다.")

# =========================================================================
# --- Tab 2: [뉴스, 검색량, 종토방 분석] (실시간 네이버 뉴스 연동) ---
# =========================================================================
with tabs[2]:
    st.markdown("### 📰 실시간 ETF 마켓 뉴스 <span style='font-size:12px; color:gray;'>(Naver News 자동 크롤링)</span>", unsafe_allow_html=True)
    
    with st.spinner("최신 뉴스 데이터를 수집하고 있습니다..."):
        df_real_news = get_realtime_news("ETF")
        st.dataframe(df_real_news, use_container_width=True, hide_index=True)
    
    st.divider()

    col_wip1, col_wip2 = st.columns(2)
    with col_wip1:
        st.markdown("### 📊 키워드 트렌드 요약 및 검색비율 추이")
        st.warning("🚧 네이버 DataLab CSV 파일 연동 기능 구현 중입니다.")
    with col_wip2:
        st.markdown("### 💬 종목토론방 분석")
        st.warning("🚧 실시간 종목토론방 감성 분석 로직 연동 중입니다.")

# =========================================================================
# --- Tab 3: [주간 거래대금 추이] (실제 KRX 거래대금 연동) ---
# =========================================================================
with tabs[3]:
    st.markdown("### 📊 선택 ETF 실제 주간 거래대금 추이 (최대 12개)")
    
    if uploaded_excel is not None and not df_source.empty and '종목명' in df_source.columns:
        extracted_etfs = df_source[df_source['종목명'] != '전체']['종목명'].dropna().unique().tolist()
        
        selected_etfs = st.multiselect(
            "검색 및 선택 (아래 빈칸을 클릭하거나 타이핑하세요):", 
            options=extracted_etfs, 
            default=extracted_etfs[:4] if len(extracted_etfs) >= 4 else extracted_etfs, 
            max_selections=12
        )
        
        st.divider()

        if selected_etfs:
            with st.spinner("한국거래소(KRX)에서 실제 거래 데이터를 불러오는 중입니다..."):
                cols = st.columns(2)
                symbols_mapping = get_etf_mapping()
                end_date = datetime.today()
                start_date = end_date - timedelta(weeks=8) # 최근 8주 데이터
                
                for i, etf_name in enumerate(selected_etfs):
                    with cols[i % 2]:
                        symbol = symbols_mapping.get(etf_name)
                        if symbol:
                            try:
                                df_hist = fdr.DataReader(symbol, start_date, end_date)
                                # 주 단위(W)로 거래량(Volume) 혹은 거래대금 합산 처리
                                df_weekly = df_hist['Volume'].resample('W').sum().reset_index()
                                df_weekly.columns = ['주 시작일', '거래량']
                                
                                fig_line = px.line(df_weekly, x='주 시작일', y='거래량', title=f"**{etf_name}** 실제 주간 거래량", markers=True, color_discrete_sequence=['#4da6ff'])
                                fig_line.update_layout(height=350, template="plotly_dark", margin=dict(l=20, r=20, t=50, b=20), xaxis_title=None)
                                st.plotly_chart(fig_line, use_container_width=True)
                            except:
                                st.error(f"{etf_name}의 데이터를 불러오지 못했습니다.")
                        else:
                            st.warning(f"{etf_name}에 해당하는 종목 코드를 찾을 수 없습니다.")
    else:
        st.info("좌측 사이드바에 데이터를 업로드해주세요.")

# =========================================================================
# --- Tab 5: [AI 분석용 프롬프트 생성기] (에러 차단용 복붙 코드) ---
# =========================================================================
with tabs[5]:
    st.markdown("### 🧠 AI 분석용 프롬프트 자동 생성기")
    st.caption("실시간으로 계산된 완벽한 데이터를 복사하여, 사용 중인 유료 AI(ChatGPT, Claude 등)에 직접 붙여넣어 완벽한 인사이트를 도출하세요.")

    data_context = "데이터가 생성되지 않았습니다. [ETF 순매수 등락, 수익률] 탭에서 산점도를 먼저 확인해주세요."
    if 'df_scatter' in locals() and not df_scatter.empty:
        # AI가 읽기 쉽도록 상위 20개 종목 데이터만 추출
        data_context = df_scatter.sort_values(by='주간 수익률(%)', ascending=False).head(20).to_string(index=False)

    prompt_text = f"""너는 KODEX 상품기획 및 마케팅을 담당하는 최고 책임자(CMO)야.
다음은 {selected_week} 주차의 주요 ETF 실제 자금 유입(순매수 증감률) 및 주간 실제 수익률 데이터야.

[ETF 데이터]
{data_context}

이 데이터를 바탕으로 전문가다운 마케팅 인사이트 보고서를 한글로 작성해줘.
반드시 아래 3가지 제목을 포함해서 논리적이고 깊이 있게 분석해야 해.

1. Executive Summary (시장 자금 흐름의 핵심 요약)
2. Signal Interpretation (특징적인 수익률/순매수 움직임을 보이는 종목 분석)
3. Next Month Watchlist (다음 달 마케팅/세일즈 역량을 집중해야 할 ETF 추천 및 명확한 이유)
"""

    st.code(prompt_text, language="text")
    st.info("👆 우측 상단의 'Copy' 버튼을 눌러 복사한 뒤, 사용 중이신 AI 모델 대화창에 그대로 붙여넣으세요.")
