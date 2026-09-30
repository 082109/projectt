import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
from datetime import datetime
from google import genai

# ---------------------------------------------------------
# 1. 페이지 기본 설정
# ---------------------------------------------------------
st.set_page_config(
    page_title="FrameLens - AI 뉴스 프레임 분석기",
    page_icon="📰",
    layout="wide"
)

# ---------------------------------------------------------
# 2. 커스텀 CSS 스타일링 (다크 네이비 테마 & 뉴스 앱 UI)
# ---------------------------------------------------------
st.markdown("""
<style>
    /* 전체 배경색 다크 네이비 적용 */
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
    }
    
    /* 상단 속보 전광판 (Ticker) 스타일 */
    .ticker-wrap {
        width: 100%;
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 10px 15px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    .ticker-badge {
        background-color: #ef4444;
        color: white;
        padding: 3px 8px;
        font-weight: bold;
        font-size: 0.78rem;
        border-radius: 4px;
        letter-spacing: 0.5px;
        animation: pulse 2s infinite;
    }
    .ticker-text {
        color: #cbd5e1;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }

    /* 서브 타이틀 및 헤더 스타일 */
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #f8fafc;
        margin-bottom: 2px;
        letter-spacing: -0.5px;
    }
    .sub-title {
        color: #94a3b8;
        font-size: 0.98rem;
        margin-bottom: 25px;
    }

    /* 검색 영역 카드 스타일 */
    .search-box-container {
        background: #1e293b;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #334155;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
        margin-bottom: 25px;
    }

    /* 기사 체크박스 카드 스타일 */
    div[data-testid="stForm"] {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
    }

    /* 구분선 컬러 수정 */
    hr {
        border-color: #334155 !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. 실시간 속보 띠 & 헤더
# ---------------------------------------------------------
st.markdown("""
<div class="ticker-wrap">
    <span class="ticker-badge">LIVE BREAKING</span>
    <span class="ticker-text">🔴 FrameLens AI 엔진 가동 중 | 실시간 포털 뉴스 보도 프레임 & 편향성 심층 탐지</span>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📰 FrameLens</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">실시간 이슈 키워드로 언론 보도 프레임과 어조를 입체적으로 분석하세요.</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 4. API 키 불러오기
# ---------------------------------------------------------
st.sidebar.header("🔑 API 설정")

client_id = st.secrets.get("NAVER_CLIENT_ID", "").strip() or st.sidebar.text_input("Naver Client ID", type="password").strip()
client_secret = st.secrets.get("NAVER_CLIENT_SECRET", "").strip() or st.sidebar.text_input("Naver Client Secret", type="password").strip()
gemini_key = st.secrets.get("GEMINI_API_KEY", "").strip() or st.sidebar.text_input("Gemini API Key", type="password").strip()

if not (client_id and client_secret and gemini_key):
    st.info("💡 사이드바에 API 키를 입력하거나 `.streamlit/secrets.toml`에 설정해주세요.")

# ---------------------------------------------------------
# 날짜 포맷 변환 함수 (RFC 822 -> YY-MM-DD HH:MM)
# ---------------------------------------------------------
def parse_pub_date(pub_date_str):
    if not pub_date_str:
        return "날짜 정보 없음"
    try:
        dt = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %z")
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return pub_date_str

# ---------------------------------------------------------
# 5. 네이버 뉴스 API 호출 함수
# ---------------------------------------------------------
def fetch_naver_news(query, display_count=30):
    url = f"https://naverapihub.apigw.ntruss.com/search/v1/news?query={query}&display={display_count}&sort=date"
    
    headers = {
        "X-NCP-APIGW-API-KEY-ID": client_id,
        "X-NCP-APIGW-API-KEY": client_secret
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get('items', [])
        else:
            st.error(f"네이버 API 호출 실패 (상태 코드: {response.status_code}) - Client ID/Secret을 확인해 주세요.")
            return []
    except Exception as e:
        st.error(f"뉴스 수집 중 오류 발생: {e}")
        return []

# ---------------------------------------------------------
# 6. Gemini AI 기사 분석 함수
# ---------------------------------------------------------
def analyze_article_with_gemini(title, description, api_key):
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    당신은 미디어 비평가이자 데이터 저널리스트입니다. 
    다음 뉴스 기사의 제목과 요약 내용을 바탕으로 언론 보도 프레임과 편향성을 객관적으로 분석해주세요.

    기사 제목: {title}
    기사 요약: {description}

    반드시 다른 설명 없이 오직 아래 형식을 맞춘 유효한 JSON 형식으로만 응답하세요:
    {{
        "summary": "기사의 핵심 2줄 요약",
        "frame_category": "보도 프레임 (다음 중 하나 선택: 갈등·대립 / 경제적 여파 / 정책·제도 / 인간적 비극 / 책임 소재 / 기타)",
        "bias_score": -5부터 5 사이의 정수 (-5: 매우 비판적, 0: 중립·객관적, 5: 매우 옹호적),
        "key_keywords": ["주요키워드1", "주요키워드2", "주요키워드3"]
    }}
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        text = response.text.strip()
        
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        if start_idx != -1 and end_idx != -1:
            json_str = text[start_idx:end_idx+1]
            return json.loads(json_str)
        else:
            return json.loads(text)
            
    except Exception as e:
        return {
            "summary": "AI 분석을 완료하지 못했습니다.",
            "frame_category": "기타",
            "bias_score": 0,
            "key_keywords": ["분석오류"]
        }

# ---------------------------------------------------------
# 7. 검색 바 (포털 웹앱 스타일)
# ---------------------------------------------------------
search_col1, search_col2 = st.columns([4, 1])

with search_col1:
    search_query = st.text_input(
        label="뉴스 검색", 
        value="마약", 
        placeholder="검색할 뉴스 키워드나 이슈를 입력하세요 (예: AI 편향성, 기후위기, 마약)",
        label_visibility="collapsed"
    )

with search_col2:
    search_btn = st.button("🔍 뉴스 검색", use_container_width=True)

# Session State 활용
if search_btn or 'news_items' not in st.session_state:
    if client_id and client_secret:
        with st.spinner("최신 관련 뉴스를 수집하는 중..."):
            st.session_state['news_items'] = fetch_naver_news(search_query)
            st.session_state['last_query'] = search_query

# ---------------------------------------------------------
# 8. 뉴스 목록 & AI 분석 신청
# ---------------------------------------------------------
if 'news_items' in st.session_state and st.session_state['news_items']:
    st.markdown(f"### 📋 '{st.session_state.get('last_query', '')}' 관련 실시간 뉴스")
    
    selected_articles = []

    col_sel1, col_sel2 = st.columns([1, 4])
    with col_sel1:
        select_all = st.checkbox("전체 기사 선택")

    with st.form("news_selection_form"):
        for idx, item in enumerate(st.session_state['news_items']):
            clean_title = item.get('title', '').replace("<b>", "").replace("</b>", "").replace("&quot;", '"').replace("&amp;", "&")
            clean_desc = item.get('description', '').replace("<b>", "").replace("</b>", "").replace("&quot;", '"').replace("&amp;", "&")
            link = item.get('originallink', item.get('link', '#'))
            pub_date = parse_pub_date(item.get('pubDate', ''))

            is_selected = st.checkbox(
                f"**{clean_title}**",
                value=select_all,
                key=f"chk_{idx}"
            )
            st.caption(f"⏱️ **보도 일시:** {pub_date}  |  {clean_desc}")
            st.markdown(f"[🔗 원문 기사 보기]({link})")
            st.markdown("---")

            if is_selected:
                selected_articles.append({
                    "title": clean_title,
                    "description": clean_desc,
                    "link": link,
                    "pub_date": pub_date
                })

        submit_analysis = st.form_submit_button("⚡ 선택한 기사 AI 프레임 분석", use_container_width=True)

    # ---------------------------------------------------------
    # 9. AI 분석 및 리포트
    # ---------------------------------------------------------
    if submit_analysis:
        if not selected_articles:
            st.warning("⚠️ 분석할 기사를 1개 이상 선택해 주세요.")
        elif not gemini_key:
            st.error("❌ Gemini API 키를 입력해 주세요.")
        else:
            st.info(f"선택한 {len(selected_articles)}개 기사의 보도 프레임을 정밀 분석 중입니다...")
            
            progress_bar = st.progress(0)
            analyzed_list = []

            for idx, article in enumerate(selected_articles):
                ai_res = analyze_article_with_gemini(article['title'], article['description'], gemini_key)
                
                analyzed_list.append({
                    "제목": article['title'],
                    "보도 일시": article['pub_date'],
                    "AI 요약": ai_res.get("summary", ""),
                    "보도 프레임": ai_res.get("frame_category", "기타"),
                    "편향성 점수": ai_res.get("bias_score", 0),
                    "핵심 키워드": ", ".join(ai_res.get("key_keywords", [])),
                    "링크": article['link']
                })
                
                progress_bar.progress((idx + 1) / len(selected_articles))

            df = pd.DataFrame(analyzed_list)
            st.toast("AI 프레임 분석 완료!", icon="🎉")

            st.markdown("---")
            st.subheader("📊 프레임 & 편향성 분석 리포트")
            
            tab1, tab2 = st.tabs(["보도 프레임 점유율", "어조 / 편향성 분포"])
            
            with tab1:
                col_chart1, col_chart2 = st.columns([1, 1])
                with col_chart1:
                    frame_counts = df['보도 프레임'].value_counts().reset_index()
                    frame_counts.columns = ['보도 프레임', '기사 수']
                    
                    # Plotly 테마도 다크 테마에 어울리게 세팅
                    fig_pie = px.pie(
                        frame_counts, 
                        values='기사 수', 
                        names='보도 프레임',
                        title="보도 프레임 점유율",
                        hole=0.4,
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    fig_pie.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font_color='#f8fafc'
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with col_chart2:
                    st.markdown("#### 💡 프레임별 요약")
                    st.dataframe(frame_counts, hide_index=True, use_container_width=True)

            with tab2:
                fig_bar = px.bar(
                    df,
                    x='제목',
                    y='편향성 점수',
                    color='편향성 점수',
                    color_continuous_scale='RdBu_r',
                    title="기사별 어조 성향 (-5: 비판적 ~ +5: 옹호적)",
                    range_y=[-5, 5]
                )
                fig_bar.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#f8fafc',
                    xaxis_showticklabels=False
                )
                st.plotly_chart(fig_bar, use_container_width=True)

            # 상세 카드
            st.subheader("📋 기사별 AI 분석 상세 카드")
            for idx, row in df.iterrows():
                with st.expander(f"[{row['보도 프레임']}] {row['제목']} ({row['보도 일시']})"):
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.markdown(f"⏱️ **보도 일시:** `{row['보도 일시']}`")
                        st.markdown(f"**AI 요약:** {row['AI 요약']}")
                        st.markdown(f"**핵심 키워드:** `{row['핵심 키워드']}`")
                    with col_b:
                        st.metric("어조/편향성 점수", f"{row['편향성 점수']} / 5")
                        st.markdown(f"[🔗 원문 보기]({row['링크']})")
