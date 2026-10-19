import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
from google import genai

# ---------------------------------------------------------
# 1. 페이지 기본 설정 및 우아한 세리프 폰트 UI 스타일링
# ---------------------------------------------------------
st.set_page_config(
    page_title="FrameLens - 뉴스 미디어 기획 포털",
    page_icon="🎬",
    layout="wide"
)

# 구글 폰트 Noto Serif KR 및 가독성 높은 산세리프 혼용 적용
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@300;400;600;700;900&display=swap');

    /* 배경 및 기본 폰트 설정 */
    .stApp {
        background-color: #080c14;
        color: #f3f4f6;
        font-family: 'Noto Serif KR', serif !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #0f172a;
        border-right: 1px solid #1e293b;
        font-family: 'Noto Serif KR', serif !important;
    }
    
    /* 포털 헤더 타이틀 */
    .hero-title {
        font-family: 'Noto Serif KR', serif !important;
        font-size: 3.2rem;
        font-weight: 900;
        color: #ffffff;
        text-align: center;
        margin-top: 15px;
        margin-bottom: 8px;
        letter-spacing: -1px;
    }
    .hero-subtitle {
        font-family: 'Noto Serif KR', serif !important;
        color: #94a3b8;
        font-size: 1.1rem;
        text-align: center;
        margin-bottom: 35px;
        font-weight: 300;
    }

    /* 포털 스타일 대형 시안 네온 검색창 박스 */
    .search-container {
        background: #0d1527;
        border: 2px solid #22d3ee;
        border-radius: 20px;
        padding: 10px 20px;
        box-shadow: 0 0 25px rgba(34, 211, 238, 0.3);
        margin-bottom: 35px;
    }

    /* stTextInput 커스텀 */
    div[data-baseweb="input"] {
        background-color: transparent !important;
        border: none !important;
        color: #ffffff !important;
        font-size: 1.15rem !important;
        font-family: 'Noto Serif KR', serif !important;
    }
    div[data-baseweb="input"] input {
        color: #ffffff !important;
    }

    /* 커스텀 버튼 스타일링 */
    .stButton > button {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
        color: #ffffff;
        border: none;
        border-radius: 12px;
        font-weight: 700;
        font-size: 1rem;
        height: 50px;
        box-shadow: 0 4px 14px rgba(2, 132, 199, 0.35);
        transition: all 0.2s ease;
        font-family: 'Noto Serif KR', serif !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%);
        box-shadow: 0 6px 18px rgba(56, 189, 248, 0.45);
        transform: translateY(-1px);
    }

    /* 뉴스 목록 카드 폰트 및 박스 스타일 */
    .news-card-box {
        font-family: 'Noto Serif KR', serif !important;
    }
    
    /* 폼 영역 박스 커스텀 */
    div[data-testid="stForm"] {
        background-color: #0d1527 !important;
        border: 1px solid #1e293b !important;
        border-radius: 18px !important;
        padding: 26px !important;
        font-family: 'Noto Serif KR', serif !important;
    }

    /* 타이틀 및 헤더 요소 폰트 가독성 보장 */
    h1, h2, h3, h4, label {
        font-family: 'Noto Serif KR', serif !important;
    }

    hr {
        border-color: #1e293b !important;
        margin: 25px 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. 헤더 섹션
# ---------------------------------------------------------
st.markdown('<div class="hero-title">FrameLens</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">트렌드 뉴스를 최신순으로 탐색하고, 세련된 미디어 콘텐츠 기획안으로 재구성하세요.</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. API 설정
# ---------------------------------------------------------
st.sidebar.header("🔑 API 설정")
client_id = st.secrets.get("NAVER_CLIENT_ID", "").strip() or st.sidebar.text_input("Naver Client ID", type="password").strip()
client_secret = st.secrets.get("NAVER_CLIENT_SECRET", "").strip() or st.sidebar.text_input("Naver Client Secret", type="password").strip()
gemini_key = st.secrets.get("GEMINI_API_KEY", "").strip() or st.sidebar.text_input("Gemini API Key", type="password").strip()

if not (client_id and client_secret and gemini_key):
    st.info("💡 사이드바에 API 키를 입력하거나 `.streamlit/secrets.toml`에 설정해주세요.")

# 날짜 변환 함수
def parse_pub_date(pub_date_str):
    if not pub_date_str:
        return "날짜 정보 없음"
    try:
        dt = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %z")
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return pub_date_str

# 네이버 뉴스 수집 함수 (최신순 50개)
def fetch_naver_news(query, display_count=50):
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
            return []
    except Exception:
        return []

# Gemini 기획안 생성 함수
def generate_content_plan(selected_title, content_format, api_key):
    client = genai.Client(api_key=api_key)
    prompt = f"""
    당신은 창의적인 미디어 콘텐츠 프로듀서이자 스토리텔러입니다.
    다음 뉴스 기사 제목을 바탕으로 선택된 미디어 형식에 맞춘 구체적인 콘텐츠 기획안을 작성해주세요.

    - 뉴스 기사 제목: {selected_title}
    - 타겟 콘텐츠 형식: {content_format} (인스타그램 카드뉴스, 공익 캠페인 포스터, 미니북, 만화 중 하나)

    반드시 아래 마크다운 구조에 맞춰서 알차게 작성해줘:
    ### 🎯 1. 기획 의도 및 핵심 메시지
    ### 👥 2. 타깃 독자층
    ### 📝 3. 형식별 전달 방식 및 레이아웃/장면 구성안 (선택한 {content_format} 형식의 구체적 컷/페이지/디자인 연출 묘사)
    ### 💡 4. 매체 특성에 따른 메시지 표현 차별점 (이 형식이 왜 효과적인지)
    ### 🔍 5. 추가 취재 또는 연출 팁 제안
    """
    
    model_candidates = ['gemini-2.5-flash', 'gemini-1.5-flash']
    for model_name in model_candidates:
        try:
            response = client.models.generate_content(model=model_name, contents=prompt)
            return response.text
        except Exception:
            continue
            
    return "기획안 생성 중 오류가 발생했습니다. Gemini API 키 및 모델 상태를 확인해 주세요."

# ---------------------------------------------------------
# 4. 시안 네온 검색 바 UI
# ---------------------------------------------------------
st.markdown('<div class="search-container">', unsafe_allow_html=True)
search_col1, search_col2 = st.columns([5, 1])
with search_col1:
    search_query = st.text_input(
        "뉴스 검색어 입력",
        value="청소년 수면 부족",
        placeholder="🔍 이슈 키워드를 입력하세요 (예: 청소년 수면, 기후위기, AI 윤리, 딥페이크)",
        label_visibility="collapsed"
    )
with search_col2:
    search_btn = st.button("🔍 검색", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

if search_btn or 'news_pool' not in st.session_state:
    if client_id and client_secret:
        with st.spinner("최신 뉴스를 불러오는 중..."):
            st.session_state['news_pool'] = fetch_naver_news(search_query)
            st.session_state['last_query'] = search_query

# ---------------------------------------------------------
# 5. 뉴스 실시간 최신순 라인업 & 콘텐츠 변환 폼
# ---------------------------------------------------------
if 'news_pool' in st.session_state and st.session_state['news_pool']:
    news_count = len(st.session_state['news_pool'])
    st.markdown(f"### 📰 '{st.session_state.get('last_query', '')}' 최신 뉴스 검색 결과 ({news_count}건)")
    st.caption("기사들을 최신 시각순으로 정렬했습니다. 기획으로 발전시킬 뉴스 1개를 선택해보세요.")

    with st.form("planning_form"):
        article_options = {}
        for idx, item in enumerate(st.session_state['news_pool']):
            clean_title = item.get('title', '').replace("<b>", "").replace("</b>", "").replace("&quot;", '"').replace("&amp;", "&")
            clean_desc = item.get('description', '').replace("<b>", "").replace("</b>", "").replace("&quot;", '"').replace("&amp;", "&")
            link = item.get('originallink', item.get('link', '#'))
            pub_date = parse_pub_date(item.get('pubDate', ''))
            
            label = f"[{pub_date}] {clean_title}"
            article_options[label] = {"title": clean_title, "link": link, "desc": clean_desc, "date": pub_date}

        selected_label = st.radio(
            "기사 선택",
            options=list(article_options.keys()),
            label_visibility="collapsed"
        )

        st.markdown("---")
        st.markdown("### 🎨 기획할 미디어 콘텐츠 형식 선택")
        content_format = st.selectbox(
            "형식 선택",
            [
                "인스타그램 카드뉴스",
                "공익 캠페인 포스터",
                "미니북",
                "만화 (컷툰/웹툰)"
            ],
            label_visibility="collapsed"
        )

        submit_plan = st.form_submit_button("🚀 AI 미디어 콘텐츠 기획안 생성하기", use_container_width=True)

    if submit_plan:
        if not gemini_key:
            st.error("❌ Gemini API 키를 입력해 주세요.")
        else:
            selected_article = article_options[selected_label]
            st.session_state['selected_article'] = selected_article
            st.session_state['content_format'] = content_format
            
            with st.spinner(f"'{content_format}' 형식의 미디어 기획안을 작성하는 중..."):
                plan_result = generate_content_plan(selected_article['title'], content_format, gemini_key)
                st.session_state['plan_result'] = plan_result

# ---------------------------------------------------------
# 6. 생성된 기획안 출력 대시보드
# ---------------------------------------------------------
if 'plan_result' in st.session_state:
    st.markdown("---")
    st.markdown("### 📊 AI 미디어 콘텐츠 기획 리포트")
    
    art = st.session_state['selected_article']
    link_url = art['link']
    st.info(f"📌 **선택한 뉴스:** {art['title']} | ⏱️ {art['date']} ([🔗 원문 기사 보기]({link_url}))")
    st.markdown(f"🎨 **변환 형식:** `{st.session_state['content_format']}`")
    
    st.markdown(st.session_state['plan_result'])
