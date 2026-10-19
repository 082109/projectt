import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
from google import genai

# ---------------------------------------------------------
# 1. 페이지 기본 설정 (딥 다크 모드)
# ---------------------------------------------------------
st.set_page_config(
    page_title="FrameLens - 뉴스 콘텐츠 기획 도우미",
    page_icon="🎬",
    layout="wide"
)

st.markdown("""
<style>
    .stApp {
        background-color: #030712;
        color: #f3f4f6;
    }
    section[data-testid="stSidebar"] {
        background-color: #0b0f19;
        border-right: 1px solid #1f2937;
    }
    .main-title {
        font-size: 2.3rem;
        font-weight: 900;
        color: #ffffff;
        margin-bottom: 4px;
        letter-spacing: -0.8px;
    }
    .sub-title {
        color: #6b7280;
        font-size: 0.95rem;
        margin-bottom: 25px;
    }
    .guide-box {
        background-color: #0b0f19;
        border: 1px solid #1f2937;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 20px;
        color: #9ca3af;
        font-size: 0.9rem;
    }
    div[data-testid="stForm"], .stTextInput > div > div {
        background-color: #0b0f19 !important;
        border: 1px solid #1f2937 !important;
        border-radius: 10px !important;
        color: #f3f4f6 !important;
    }
    .stButton > button {
        background-color: #1f2937;
        color: #ffffff;
        border: 1px solid #374151;
        border-radius: 8px;
        font-weight: 600;
    }
    .stButton > button:hover {
        background-color: #374151;
        border-color: #4b5563;
        color: #ffffff;
    }
    hr {
        border-color: #1f2937 !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. 헤더 및 세션 상태 초기화
# ---------------------------------------------------------
st.markdown('<div class="main-title">🎬 FrameLens : 뉴스 콘텐츠 기획 도우미</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">관심 뉴스를 검색하고, 다양한 미디어 콘텐츠 형식(카드뉴스·숏폼 등)으로 기획·전환해보세요.</div>', unsafe_allow_html=True)

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

# 네이버 뉴스 수집 함수
def fetch_naver_news(query, display_count=15):
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

# Gemini를 통한 미디어 콘텐츠 기획안 생성 함수
def generate_content_plan(selected_title, content_format, api_key):
    client = genai.Client(api_key=api_key)
    prompt = f"""
    당신은 창의적인 미디어 콘텐츠 프로듀서이자 방송작가입니다.
    다음 뉴스 기사 제목을 바탕으로 선택된 미디어 형식에 맞춘 구체적인 콘텐츠 기획안을 작성해주세요.

    - 뉴스 기사 제목: {selected_title}
    - 타겟 콘텐츠 형식: {content_format} (예: 카드뉴스, 숏폼/릴스, 전문가 인터뷰, 공익 캠페인 등)

    반드시 아래 마크다운 구조에 맞춰서 알차게 작성해줘:
    ### 🎯 1. 기획 의도 및 배경
    ### 👥 2. 타깃 시청층 / 독자
    ### 📝 3. 형식별 전달 방식 및 구성안 (선택한 {content_format}에 맞게 구체적 연출 묘사)
    ### 💡 4. 매체 특성에 따른 메시지 표현 차별점 (이 형식이 왜 효과적인지)
    ### 🔍 5. 추가 취재 또는 조사 방향 제안
    """
    try:
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        return response.text
    except Exception as e:
        return f"기획안 생성 중 오류가 발생했습니다: {e}"

# ---------------------------------------------------------
# 4. 검색 바 (뉴스 검색 기능)
# ---------------------------------------------------------
col_s1, col_s2 = st.columns([4, 1])
with col_s1:
    search_query = st.text_input(
        "뉴스 검색",
        value="청소년 수면 부족",
        placeholder="검색할 키워드를 입력하세요 (예: 청소년 수면 부족, 기후위기, AI 에듀)",
        label_visibility="collapsed"
    )
with col_s2:
    search_btn = st.button("🔍 뉴스 검색", use_container_width=True)

if search_btn or 'news_pool' not in st.session_state:
    if client_id and client_secret:
        with st.spinner("뉴스를 불러오는 중..."):
            st.session_state['news_pool'] = fetch_naver_news(search_query)
            st.session_state['last_query'] = search_query

# ---------------------------------------------------------
# 5. 뉴스 선택 및 콘텐츠 형식 지정 인터페이스
# ---------------------------------------------------------
if 'news_pool' in st.session_state and st.session_state['news_pool']:
    st.markdown(f'<div class="guide-box">📋 <b>\'{st.session_state.get("last_query", "")}\'</b> 관련 뉴스 목록입니다. 기획에 활용할 기사를 선택하고 아래에서 콘텐츠 형식을 골라주세요!</div>', unsafe_allow_html=True)

    with st.form("planning_form"):
        article_options = {}
        for idx, item in enumerate(st.session_state['news_pool']):
            clean_title = item.get('title', '').replace("<b>", "").replace("</b>", "").replace("&quot;", '"').replace("&amp;", "&")
            clean_desc = item.get('description', '').replace("<b>", "").replace("</b>", "").replace("&quot;", '"').replace("&amp;", "&")
            link = item.get('originallink', item.get('link', '#'))
            pub_date = parse_pub_date(item.get('pubDate', ''))
            
            label = f"[{pub_date}] {clean_title}"
            article_options[label] = {"title": clean_title, "link": link, "desc": clean_desc}

        selected_label = st.radio(
            "기획에 활용할 뉴스 기사 선택",
            options=list(article_options.keys()),
            label_visibility="collapsed"
        )

        st.markdown("---")
        st.subheader("🎨 변환할 미디어 콘텐츠 형식 선택")
        content_format = st.selectbox(
            "형식 선택",
            ["인스타그램 카드뉴스 (정보 전달형)", "숏폼 동영상 / 릴스 (트렌드·요약형)", "심층 인터뷰 / 좌담회 (시사·비평형)", "공익 캠페인 / 카드 뉴스 (행동 유도형)"],
            label_visibility="collapsed"
        )

        submit_plan = st.form_submit_button("🚀 미디어 콘텐츠 기획안 생성하기", use_container_width=True)

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
# 6. 생성된 기획안 출력 섹션
# -------------------
if 'plan_result' in st.session_state:
    st.markdown("---")
    st.subheader("📊 AI 미디어 콘텐츠 기획 리포트")
    
    art = st.session_state['selected_article']
    link_url = art['link']
    st.info(f"📌 **활용 뉴스:** {art['title']} ([🔗 원문 보기]({link_url}))")
    st.markdown(f"🎨 **선택한 미디어 형식:** `{st.session_state['content_format']}`")
    
    st.markdown(st.session_state['plan_result'])
