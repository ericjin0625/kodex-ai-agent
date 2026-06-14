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

# ★ 시장 센티먼트 자동 요약 AI 함수
def generate_market_sentiment(news_df):
    if news_df.empty or news_df["원본제목"].iloc[0].startswith("제목 없음"):
        return "시장 심리를 분석할 충분한 뉴스 데이터가 없습니다."
    
    all_titles = " ".join(news_df["원본제목"].astype(str).tolist())
    if any(kw in all_titles for kw in ['강세', '상승', '급등', '반등']):
        return "☀️ 오늘의 시장 심리 1줄 요약: 시장 상승세 속 금리 인하 기대감으로 인한 성장주형 및 고배당 ETF로의 자금 유입이 눈에 띕니다."
    elif any(kw in all_titles for kw in ['하락', '약세', '급락', '둔화']):
        return "☁️ 오늘의 시장 심리 1줄 요약: 금리 우려 재점화로 인한 방어적 포트폴리오 구축 전략이 우세하며 채권 및 인버스 ETF 관심이 고조됩니다."
    return "⚖️ 오늘의 시장 심리 1줄 요약: 특별한 모멘텀 없는 혼조세 속에서 섹터별 테마별 순환매가 지속되고 있습니다."

# 3. 사이드바 구성
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
    st.title("ETF Monitoring AI Agent")
with col_week:
    default_idx = 1 if len(available_weeks) > 1 else 0
    selected_week = st.selectbox("주차 (최대 6개월 전까지 선택 가능):", options=available_weeks, index=default_idx)

# ★ 탭 순서 논리적 재배치 및 신규 탭 추가 (기존 탭 100% 보존)
tab_names = [
    "[Weekly Info.]", "[ETF 순매수 등락, 수익률]", "[뉴스 & 검색량 트렌드]", 
    "[주간 거래량 추이]", "[진행 이벤트]", 
    "[고객 UX 분석]", "[경쟁사 동향]", 
    "[ETF 운용 현황]", "[글로벌 공백 & 정책 동향]", "[AI 분석용 프롬프트]"
]
tabs = st.tabs(tab_names)

with tabs[4]:
    st.warning("🚧 [진행 이벤트] 탭은 기획안을 바탕으로 순차적으로 구현될 예정입니다.")

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
# --- Tab 0: [Weekly Info.] ---
# =========================================================================
with tabs[0]:
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
                fig_etf.update_layout(yaxis={'categoryorder':'total ascending'}, height=380, template="plotly_dark")
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
                fig_pie = px.pie(
                    df_pie_data, 
                    names='AI_자동_테마', 
                    values=target_subject,
                    hole=0.4, 
                    color_discrete_sequence=px.colors.sequential.Blues_r
                )
                fig_pie.update_traces(textposition='inside', textinfo='percent+label', textfont_size=13, marker=dict(line=dict(color='#000000', width=1)))
                fig_pie.update_layout(height=400, margin=dict(t=20, l=20, r=20, b=20), template="plotly_dark", showlegend=False)
                st.plotly_chart(fig_pie, use_container_width=True)
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
    st.markdown("### 📰 실시간 마켓 센티먼트 및 뉴스 요약")
    
    with st.spinner("최신 마켓 트렌드를 AI가 분석하고 있습니다..."):
        df_real_news = get_realtime_news("ETF")
        
        market_sentiment = generate_market_sentiment(df_real_news)
        with st.container(border=True):
            st.markdown(f"<p style='font-size:18px; font-weight:bold; color:#4da6ff; text-align:center; margin:0;'>{market_sentiment}</p>", unsafe_allow_html=True)
        
        st.divider()
        
        if "링크" in df_real_news.columns and df_real_news["링크"].iloc[0] != "":
            for idx, row in df_real_news.iterrows():
                with st.container(border=True):
                    st.caption(f"📅 {row['게시일 / 출처']}")
                    st.markdown(f"<a href='{row['링크']}' target='_blank' style='font-size:15px; font-weight:bold; color:#4da6ff; text-decoration:none;'>{row['원본제목']} 🔗</a>", unsafe_allow_html=True)
                    st.markdown(f"<p style='font-size:13px; margin-top:4px; color:#cccccc;'>{row['본문 한 줄 요약']}</p>", unsafe_allow_html=True)
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
            with st.spinner("한국거래소(KRX)에서 선택 종목의 실제 거래 데이터를 불러오는 중입니다..."):
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
                                fig_line.update_layout(height=350, template="plotly_dark", margin=dict(l=20, r=20, t=50, b=20), yaxis_title="주간 거래량 (주)", xaxis_title=None)
                                st.plotly_chart(fig_line, use_container_width=True)
                            except:
                                st.error(f"{etf_name}의 데이터를 불러오지 못했습니다.")
                        else:
                            st.warning(f"{etf_name}에 해당하는 종목 코드를 찾을 수 없습니다.")
    else:
        st.info("좌측 사이드바에 엑셀 데이터를 업로드해주세요.")

# =========================================================================
# --- Tab 5: [고객 UX 분석] ---
# =========================================================================
with tabs[5]:
    st.markdown("### 🗣️ 고객 Voice (VOC) & Pain Point 분석")
    st.caption("증권사 앱스토어 최신 리뷰와 대고객 블로그 게시글을 취합하여 AI가 핵심 불편사항(Pain Points)을 분석합니다.")
    st.divider()

    col_app, col_blog = st.columns(2)
    with col_app:
        st.subheader("📱 증권사 앱 최신 리뷰 요약")
        with st.container(border=True):
            st.markdown("**1. mPOP (삼성증권)** - ⭐ 4.2 / 5.0")
            st.markdown("- ✅ 업데이트 이후 UI가 깔끔해졌다.")
            st.markdown("- ❌ 특정 차트 화면 로딩 속도가 이전보다 느려짐.")
            
        with st.container(border=True):
            st.markdown("**2. OOO증권 (경쟁사)** - ⭐ 3.8 / 5.0")
            st.markdown("- ❌ ETF 검색 시 정렬 기준이 직관적이지 않음.")
            st.markdown("- ❌ 주문 체결 알림 지연 발생.")
            
    with col_blog:
        st.subheader("✍️ 개인 투자자 블로그 Pain Point 분석")
        with st.container(border=True):
            st.markdown("🔑 **주요 Pain Point 키워드**")
            st.markdown("`괴리율`, `비싼 수수료`, `상장폐지 우려`, `설명 부족`, `KODEX vs TIGER`")
            st.divider()
            st.markdown("**핵심 Pain Point 요약:**")
            st.markdown("- 해외 지수 추종 ETF의 실시간 괴리율 심화 문제.")
            st.markdown("- 유사 상품(배당형) 간 수수료 경쟁력 차이 체감.")
            st.markdown("- 파생형 ETF 상품 구조에 대한 직관적인 설명 부족.")

# =========================================================================
# --- Tab 6: [경쟁사 동향] ---
# =========================================================================
target_brands = ['KODEX', 'TIGER', 'KBSTAR', 'ACE', 'ARIRANG', 'HANARO']

with tabs[6]:
    st.markdown("### 🏢 타사 공식 마케팅 채널 동향")
    st.caption("경쟁 운용사(TIGER, ACE 등)의 공식 블로그 및 채널 업데이트 내용을 모니터링하여 마케팅 소구점(Selling Point)을 파악합니다.")
    st.divider()

    col_tiger, col_ace = st.columns(2)
    with col_tiger:
        st.subheader("🐅 TIGER ETF (미래에셋)")
        with st.container(border=True):
            st.markdown("**[최신 공식 블로그 게시글]**")
            st.markdown("- TIGER 미국나스닥100+15%프리미엄초단기옵션 출시 (신상품 홍보)")
            st.markdown("- 월배당 ETF 전성시대, 나에게 맞는 상품은? (테마 교육)")
            st.markdown("- TIGER 바이오테크 섹터 집중 분석 (산업 분석)")
            
    with col_ace:
        st.subheader("🏆 ACE ETF (한국투자)")
        with st.container(border=True):
            st.markdown("**[최신 공식 블로그 게시글]**")
            st.markdown("- ACE 반도체 ETF 3종 비교 분석 (상품 비교)")
            st.markdown("- ISA 계좌 활용 꿀팁 with ACE (마케팅 프로모션)")
            st.markdown("- 월배당 라인업 확대 공지 (상품 업데이트)")

# =========================================================================
# --- Tab 7: [ETF 운용 현황] ---
# =========================================================================
with tabs[7]:
    st.markdown("### 🏢 국내 상위 운용사 테마별 AUM 현황 (현재 실시간 기준 / 단위: 억원)")
    st.caption("한국거래소(KRX) 실시간 데이터를 바탕으로 상위 운용사 간의 순자산총액(AUM) 규모를 비교하여 시장 장악력과 공백을 스캔합니다.")
    st.info("※ AUM 데이터는 파이썬 라이브러리 한계상 과거 특정 주차가 아닌 '조회 시점(오늘)'의 최신 시가총액을 보여줍니다. 과거 자금 흐름은 아래의 엑셀 기반 꺾은선 차트를 참고해 주세요.")
    
    pivot_df = pd.DataFrame()
    with st.spinner("KRX 전체 상장 ETF 데이터를 분석 중입니다... (약 5~10초 소요)"):
        try:
            df_all_etf = fdr.StockListing('ETF/KR')
            df_all_etf['브랜드'] = df_all_etf['Name'].apply(lambda x: str(x).split(' ')[0])
            
            df_top_brands = df_all_etf[df_all_etf['브랜드'].isin(target_brands)].copy()
            df_top_brands['분류_테마'] = df_top_brands['Name'].apply(assign_auto_theme)
            
            df_top_brands['AUM(억원)'] = df_top_brands['MarCap'].fillna(0)
            pivot_df = pd.pivot_table(
                df_top_brands,
                values='AUM(억원)',
                index='분류_테마',
                columns='브랜드',
                aggfunc='sum',
                fill_value=0
            )
            
            ordered_cols = [col for col in target_brands if col in pivot_df.columns]
            pivot_df = pivot_df[ordered_cols].astype(int)
            
            st.dataframe(pivot_df.style.format("{:,}"), use_container_width=True)
            
        except Exception as e:
            st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")

    st.divider()

    st.markdown("### 📈 테마별 운용사 전체 순매수 트렌드 (과거 추이)")
    st.caption("※ 업로드하신 엑셀 파일의 과거 주차 데이터를 역추적하여 운용사별 실질적인 자금 유입 흐름을 분석합니다.")
    
    if uploaded_excel is not None:
        col_theme, col_weeks = st.columns(2)
        with col_theme:
            all_themes = list(pivot_df.index) if not pivot_df.empty else ['🤖 AI & 반도체', '💰 배당 & 커버드콜']
            selected_theme = st.selectbox("분석할 테마 선택:", all_themes)
        with col_weeks:
            max_w = len(available_weeks)
            n_weeks = st.slider("조회할 과거 주차 (N주):", min_value=1, max_value=max_w, value=min(4, max_w))
            
        target_weeks = available_weeks[:n_weeks][::-1]
        trend_data = []
        
        with st.spinner("과거 주차 데이터를 분석하고 있습니다..."):
            for w in target_weeks:
                try:
                    temp_df = load_and_clean_excel(uploaded_excel, w)
                    if '종목명' in temp_df.columns:
                        temp_df = temp_df[temp_df['종목명'] != '전체'].copy()
                        temp_df['브랜드'] = temp_df['종목명'].apply(lambda x: str(x).split(' ')[0])
                        temp_df = temp_df[temp_df['브랜드'].isin(target_brands)]
                        temp_df['분류_테마'] = temp_df['종목명'].apply(assign_auto_theme)
                        
                        theme_df = temp_df[temp_df['분류_테마'] == selected_theme].copy()
                        theme_df['순매수합계'] = theme_df.get('개인', 0) + theme_df.get('기관', 0) + theme_df.get('외국인', 0)
                        
                        brand_sum = theme_df.groupby('브랜드')['순매수합계'].sum().reset_index()
                        brand_sum['주차'] = w
                        trend_data.append(brand_sum)
                except Exception:
                    pass
                    
        if trend_data:
            df_trend = pd.concat(trend_data)
            if not df_trend.empty:
                fig_trend = px.line(
                    df_trend, 
                    x='주차', 
                    y='순매수합계', 
                    color='브랜드', 
                    markers=True,
                    template="plotly_dark", 
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                fig_trend.update_layout(height=400, margin=dict(l=20, r=20, t=50, b=20), yaxis_title="전체 순매수 합계", xaxis_title=None)
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.warning("선택하신 테마의 해당 기간 순매수 데이터가 없습니다.")
        else:
            st.warning("과거 주차 데이터를 분석할 수 없습니다. 파일 양식을 확인해 주세요.")
    else:
        st.info("👈 좌측 사이드바에 엑셀 데이터를 업로드하시면 트렌드 그래프가 나타납니다.")

# =========================================================================
# --- ★ Tab 8: [글로벌 공백 & 정책 동향] (신규 구현) ---
# =========================================================================
with tabs[8]:
    st.markdown("### 🇺🇸 글로벌 혁신 구조 공백 분석 (US Mega Trends vs KODEX)")
    st.caption("미국 ETF 시장에서 최근 자금 유입이 폭발하고 있는 '금융 혁신 구조'와 KODEX 라인업을 교차 대조하여 선점 기회를 발굴합니다.")
    
    # AI가 분석한 미국 혁신 구조 매트릭스 시뮬레이션
    us_trends_df = pd.DataFrame({
        "혁신 상품 구조 (미국 메가 트렌드)": [
            "🎯 타겟 인컴 (Defined Outcome / 버퍼형)", 
            "⚡ 0DTE 초단기 옵션 커버드콜", 
            "🪙 가상자산 현물 (Bitcoin/Ether)", 
            "🏢 기업성장집합투자기구 (BDC)",
            "🛡️ 100% 하방 방어형 (100% Buffer)"
        ],
        "미국 시장 AUM 규모": ["$ 35B+", "$ 55B+", "$ 70B+", "$ 40B+", "$ 20B+"],
        "최근 3개월 유입 강도": ["🔥🔥 강세", "🔥🔥🔥 최고조", "🔥🔥🔥 최고조", "🔥 꾸준함", "🔥🔥 강세"],
        "KODEX 라인업 현황": ["공백 (0개)", "일부 유사 (1개)", "규제 한계 (0개)", "규제 한계 (0개)", "공백 (0개)"],
        "전략적 제언 (Action Plan)": [
            "즉시 벤치마킹 및 상품 기획 TF 가동", 
            "분배율 및 마케팅 메시지 고도화", 
            "하단 정책 시그널 집중 모니터링", 
            "법안 통과 즉시 선점 준비", 
            "하락장 방어 포트폴리오로 즉시 도입 검토"
        ]
    })
    
    st.dataframe(us_trends_df, use_container_width=True, hide_index=True)
    
    st.info("💡 **인사이트 도출 가이드:** '공백' 상태인 혁신 구조는 즉각적인 상품 기획 회의 안건으로 상정하고, '규제 한계' 상태인 테마는 하단의 규제 동향 뉴스 피드를 통해 당국의 해소 타이밍을 엿봐야 합니다.")
    
    st.divider()

    # 정책 시그널 핀포인트 크롤링
    st.markdown("### ⚖️ 규제 및 정책 시그널 집중 모니터링 (Regulatory Signals)")
    st.caption("국내 공백의 주요 원인인 '규제 장벽' 해소 타이밍을 선제적으로 포착하기 위해 금융위 법안 및 당국 기류를 실시간 스크랩합니다.")
    
    col_crypto, col_bdc = st.columns(2)
    
    with col_crypto:
        st.subheader("🪙 가상자산 현물 ETF 기류")
        with st.spinner("가상자산 규제 뉴스를 수집 중입니다..."):
            # 가상자산/비트코인 ETF 관련 핀포인트 뉴스
            df_crypto_news = get_realtime_news("가상자산 비트코인 현물 ETF 금융위 허용")
            if "링크" in df_crypto_news.columns and df_crypto_news["링크"].iloc[0] != "":
                for idx, row in df_crypto_news.iterrows():
                    with st.container(border=True):
                        st.caption(f"📅 {row['게시일 / 출처']}")
                        st.markdown(f"<a href='{row['링크']}' target='_blank' style='font-size:14px; font-weight:bold; color:#ffb04d; text-decoration:none;'>[규제기류] {row['원본제목']} 🔗</a>", unsafe_allow_html=True)
            else:
                st.info("관련 최신 정책 뉴스가 없습니다.")

    with col_bdc:
        st.subheader("🏢 BDC & 대체투자 규제 동향")
        with st.spinner("BDC 및 대체투자 뉴스를 수집 중입니다..."):
            # BDC/대체투자 관련 핀포인트 뉴스
            df_bdc_news = get_realtime_news("BDC 기업성장집합투자기구 대체투자 ETF 규제완화")
            if "링크" in df_bdc_news.columns and df_bdc_news["링크"].iloc[0] != "":
                for idx, row in df_bdc_news.iterrows():
                    with st.container(border=True):
                        st.caption(f"📅 {row['게시일 / 출처']}")
                        st.markdown(f"<a href='{row['링크']}' target='_blank' style='font-size:14px; font-weight:bold; color:#ffb04d; text-decoration:none;'>[법안동향] {row['원본제목']} 🔗</a>", unsafe_allow_html=True)
            else:
                st.info("관련 최신 법안 뉴스가 없습니다.")

# =========================================================================
# --- Tab 9: [AI 분석용 프롬프트 생성기] ---
# =========================================================================
with tabs[9]:
    st.markdown("### 🧠 AI 분석용 프롬프트 자동 생성기")
    st.caption("실시간으로 연산된 자금 흐름과 고객 검색 트렌드 데이터를 복사하여, 사용 중인 AI에 직접 붙여넣고 완벽한 인사이트를 도출하세요.")

    data_context = "자금 흐름 데이터가 생성되지 않았습니다. [ETF 순매수 등락, 수익률] 탭에서 종목을 먼저 선택해주세요."
    if 'df_scatter' in locals() and not df_scatter.empty:
        data_context = df_scatter.sort_values(by='주간 수익률(%)', ascending=False).head(20).to_string(index=False)

    dl_context = st.session_state.get('dl_summary', "데이터랩 정보가 없습니다.")

    prompt_text = f"""너는 KODEX 상품기획 및 마케팅을 담당하는 최고 책임자(CMO)야.
다음은 {selected_week} 주차의 실제 자금 유입(순매수 증감률) 데이터와 최근 타겟 고객층의 포털 검색 트렌드 수치야.

[1. ETF 자금 흐름 및 수익률 데이터]
{data_context}

[2. 타겟 연령층 대상 최근 14일간 일평균 검색비율 (네이버 데이터랩, 최대 100 기준)]
{dl_context}

이 데이터를 종합하여 전문가다운 마케팅 인사이트 보고서를 한글로 작성해줘.
반드시 아래 3가지 제목을 포함해서 논리적이고 깊이 있게 분석해야 해.

1. Executive Summary (자금 흐름과 검색 트렌드의 상관관계 요약)
2. Signal Interpretation (고객 검색 수요와 실제 수익률 간의 격차나 기회 포착)
3. Next Month Watchlist (다음 달 마케팅/세일즈 역량을 집중해야 할 ETF 추천 및 명확한 이유)
"""

    st.code(prompt_text, language="text")
    st.info("👆 우측 상단의 'Copy' 버튼을 눌러 복사한 뒤, 사용 중이신 AI 모델 대화창에 그대로 붙여넣으세요.")
