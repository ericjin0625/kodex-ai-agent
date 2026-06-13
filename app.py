import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import FinanceDataReader as fdr
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# 1. 페이지 레이아웃 및 기본 테마 설정
st.set_page_config(page_title="ETF Monitoring AI Agent", layout="wide")

# 2. 실시간 데이터 파싱 함수 (뉴스 연동)
@st.cache_data(ttl=3600)
def get_realtime_news(keyword="ETF"):
    url = f"https://news.google.com/rss/search?q={keyword}+when:7d&hl=ko&gl=KR&ceid=KR:ko"
    try:
        res = requests.get(url, timeout=5)
        root = ET.fromstring(res.text)
        
        news_list = []
        for item in root.findall('./channel/item')[:5]:
            title = item.find('title').text if item.find('title') is not None else "제목 없음"
            link = item.find('link').text if item.find('link') is not None else ""
            pubDate = item.find('pubDate').text[5:16] if item.find('pubDate') is not None else ""
            source = item.find('source').text if item.find('source') is not None else "Google News"
            
            desc_html = item.find('description').text if item.find('description') is not None else ""
            desc_text = BeautifulSoup(desc_html, 'html.parser').get_text(separator=' ', strip=True)
            
            clean_text = desc_text.split("...")[0].strip() if "..." in desc_text else desc_text
            if "다." in clean_text:
                one_line = clean_text.split("다.")[0].strip() + "다."
            else:
                one_line = clean_text
                
            if len(one_line) < 10 and desc_text:
                one_line = desc_text[:60] + "..."
            
            news_list.append({
                "게시일 / 출처": f"{pubDate} / {source}", 
                "원본제목": title, 
                "링크": link,
                "본문 한 줄 요약": f"👉 {one_line}"
            })
            
        if not news_list:
            return pd.DataFrame([{"게시일 / 출처": "-", "원본제목": "뉴스 검색 결과가 없습니다.", "링크": "", "본문 한 줄 요약": "-"}])
            
        return pd.DataFrame(news_list)
        
    except Exception as e:
        return pd.DataFrame([{"게시일 / 출처": "오류", "원본제목": "실시간 뉴스를 불러올 수 없습니다.", "링크": "", "본문 한 줄 요약": str(e)}])

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

# 3. 사이드바 구성 (CSV 및 엑셀 모두 허용)
with st.sidebar:
    st.markdown("### 📊 데이터 컨트롤 타워")
    st.divider()
    uploaded_excel = st.file_uploader("ETF 순매수 엑셀 업로드", type=["xlsx", "xls"], key="excel_main")
    st.divider()
    uploaded_dl = st.file_uploader("DataLab 데이터 업로드 (CSV/Excel)", type=["csv", "xlsx", "xls"], key="dl_main")

# 4. 엑셀 시트 파싱
available_weeks = ["5.17~5.23", "5.10~5.16", "5.03~5.09"] 
if uploaded_excel is not None:
    xls = pd.ExcelFile(uploaded_excel)
    sheet_names = [sheet for sheet in xls.sheet_names if sheet != "참고사항"]
    if sheet_names:
        available_weeks = sheet_names[::-1] 

col_title, col_week = st.columns([3, 1])
with col_title:
    st.title("ETF Monitoring AI Agent (Real-time)")
with col_week:
    default_idx = 1 if len(available_weeks) > 1 else 0
    selected_week = st.selectbox("주차 (최대 6개월 전까지 선택 가능):", options=available_weeks, index=default_idx)

tab_names = [
    "[Weekly Info.]", "[ETF 순매수 등락, 수익률]", "[뉴스 & 검색량 트렌드]", 
    "[주간 거래량 추이]", "[진행 이벤트]", "[AI 분석용 프롬프트]", "[ETF 운용 현황]"
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

df_scatter = pd.DataFrame()
st.session_state['dl_summary'] = "DataLab 데이터가 업로드되지 않았습니다."

# =========================================================================
# --- Tab 0: [Weekly Info.] (유연한 컬럼 인식 및 기타 파이 차트 적용) ---
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

        st.markdown("### 🔥 해당 주 인기 테마 (순매수 유입 비중)")
        
        # 1. 엑셀 파일 내에서 '테마'라는 단어가 포함된 열을 유연하게 찾습니다.
        theme_col = next((col for col in df_source.columns if '테마' in col), None)

        if theme_col and '종목명' in df_source.columns:
            # 양수(>0)인 인기 테마만 필터링
            df_theme_pos = df_source[(df_source["종목명"] != "전체") & (df_source[target_subject] > 0)]
            df_theme = df_theme_pos.groupby(theme_col)[target_subject].sum().reset_index()
            df_theme = df_theme.sort_values(by=target_subject, ascending=False)

            # 2. TOP N과 '기타' 조각 분리 로직
            if len(df_theme) > top_n:
                df_top = df_theme.head(top_n)
                others_val = df_theme.iloc[top_n:][target_subject].sum()
                df_others = pd.DataFrame([{theme_col: "기타 (Others)", target_subject: others_val}])
                df_pie_data = pd.concat([df_top, df_others], ignore_index=True)
            else:
                df_pie_data = df_theme

            col_theme_table, col_theme_chart = st.columns([3, 7])
            with col_theme_table:
                # 표는 전체 테마 목록을 모두 보여줍니다.
                st.dataframe(df_theme, use_container_width=True, height=400)
            with col_theme_chart:
                # 파이 차트 (가운데가 살짝 뚫린 도넛 형태로 세련되게 렌더링)
                fig_pie = px.pie(
                    df_pie_data, 
                    names=theme_col, 
                    values=target_subject,
                    hole=0.4,
                    color_discrete_sequence=px.colors.sequential.Blues_r
                )
                # 라벨과 퍼센티지를 조각 안쪽에 함께 표시
                fig_pie.update_traces(textposition='inside', textinfo='percent+label', textfont_size=12)
                fig_pie.update_layout(height=400, margin=dict(t=20, l=20, r=20, b=20), template="plotly_dark", showlegend=False)
                st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("업로드하신 엑셀 파일의 첫 줄에 '테마'라는 단어가 포함된 열(Column)이 존재하지 않아 테마 분석을 건너뜁니다.")
    else:
        st.info("좌측 사이드바에 엑셀 데이터를 업로드해주세요.")

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
                    df_merged['순매수 증감률(%)'] = np.where(
                        df_merged['지난주'] != 0,
                        ((df_merged['이번주'] - df_merged['지난주']) / df_merged['지난주'].abs()) * 100, 0
                    ).clip(-300, 300)
                    
                    all_etfs_scatter = df_merged['종목명'].dropna().tolist()
                    default_selection = all_etfs_scatter[:10] if len(all_etfs_scatter) >= 10 else all_etfs_scatter
                    
                    selected_scatter_etfs = st.multiselect(
                        "📍 산점도에 표시할 ETF를 검색/선택하세요:", 
                        options=all_etfs_scatter, 
                        default=default_selection,
                        key="scatter_multiselect_tab2"
                    )
                    
                    if selected_scatter_etfs:
                        with st.spinner("선택된 종목의 실시간 수익률을 불러오는 중입니다..."):
                            symbols_mapping = get_etf_mapping()
                            real_returns = get_real_returns(symbols_mapping, selected_scatter_etfs)
                            
                            df_scatter_filtered = df_merged[df_merged['종목명'].isin(selected_scatter_etfs)].copy()
                            df_scatter_filtered['주간 수익률(%)'] = df_scatter_filtered['종목명'].map(real_returns)
                            df_scatter = df_scatter_filtered.dropna()
                            
                            fig_scatter = px.scatter(
                                df_scatter, x="주간 수익률(%)", y="순매수 증감률(%)",
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
# --- Tab 2: [뉴스 & 검색량 트렌드] ---
# =========================================================================
with tabs[2]:
    col_news, col_trend = st.columns([4, 6])
    
    with col_news:
        st.markdown("### 📰 실시간 ETF 마켓 뉴스")
        st.caption("Google News 자동 크롤링")
        with st.spinner("최신 뉴스 데이터를 수집하고 있습니다..."):
            df_real_news = get_realtime_news("ETF")
            
            if "링크" in df_real_news.columns and df_real_news["링크"].iloc[0] != "":
                for idx, row in df_real_news.iterrows():
                    with st.container(border=True):
                        st.caption(f"📅 {row['게시일 / 출처']}")
                        st.markdown(f"<a href='{row['링크']}' target='_blank' style='font-size:15px; font-weight:bold; color:#4da6ff; text-decoration:none;'>{row['원본제목']} 🔗</a>", unsafe_allow_html=True)
                        st.markdown(f"<p style='font-size:13px; margin-top:4px; color:#cccccc;'>{row['본문 한 줄 요약']}</p>", unsafe_allow_html=True)
            else:
                st.dataframe(df_real_news, use_container_width=True, hide_index=True)
                
    with col_trend:
        st.markdown("### 📊 키워드 트렌드 요약 및 검색비율 추이")
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
                    
                    fig_trend = px.line(
                        df_melted, 
                        x='날짜', 
                        y='검색량', 
                        color='종목명',
                        template="plotly_dark"
                    )
                    fig_trend.update_layout(height=450, margin=dict(l=20, r=20, t=20, b=20), xaxis_title=None, yaxis_title="상대적 검색량 (최대 100)")
                    st.plotly_chart(fig_trend, use_container_width=True)
                
            except Exception as e:
                st.error(f"파일 처리 중 오류가 발생했습니다. 네이버 데이터랩 원본 파일이 맞는지 확인해주세요: {e}")
        else:
            st.info("👈 좌측 사이드바에 Naver DataLab 파일(CSV/Excel)을 업로드하시면 비교 트렌드 차트가 나타납니다.")

# =========================================================================
# --- Tab 3: [주간 거래량 추이] ---
# =========================================================================
with tabs[3]:
    st.markdown("### 📊 선택 ETF 실제 주간 거래량 추이 (최대 12개)")
    
    if uploaded_excel is not None and
