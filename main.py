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

# 구글 폰트 Noto Serif KR 전면 적용
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
        font-size: 3rem;
        font-weight: 900;
        color: #ffffff;
        text-align: center;
        margin-top: 10px;
        margin-bottom: 6px;
        letter-spacing: -1px;
    }
    .hero-subtitle {
        font-family: 'Noto Serif KR', serif !important;
        color: #94a3b8;
        font-size: 1.05rem;
        text-align: center;
        margin-bottom: 30px;
        font-weight: 300;
    }

    /* 포털 스타일 대형 시안 네온 검색창 박스 */
    .search-container {
        background: #0d1527;
        border: 2px solid #22d3ee;
        border-radius: 20px;
        padding: 8px 16px;
        box-shadow: 0 0 25px rgba(34, 211, 238, 0.3);
        margin-bottom: 30px;
    }

    /* stTextInput 커스텀 */
    div[data-baseweb="input"] {
        background-color: transparent !important;
        border: none !important;
        color: #ffffff !important;
        font-size: 1.1rem !important;
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
        font-size: 0.95rem;
        height: 46px;
        box-shadow: 0 4px 14px rgba(2, 132, 199, 0.35);
        transition: all 0.2s ease;
        font-family: 'Noto Serif KR', serif !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%);
        box-shadow: 0 6px 18px rgba(56, 189, 248, 0.45);
        transform: translateY(-1px);
    }

    /* 오른쪽 카드 박스 스타일링 */
    .right-card-box {
        background-color: #0d1527;
        border: 1px solid #1e293b;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
    }

    /* 타이틀 및 헤더 요소 폰트 가독성 보장 */
    h1, h2, h3, h4, label {
        font-family: 'Noto Serif KR', serif !important;
    }

    hr {
        border-color: #1e293b !important;
        margin: 20px 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. 헤더 섹션
# ---------------------------------------------------------
st.markdown('<div class="hero-title">FrameLens</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">트렌드 뉴스를 최신순으로 탐색하고, 세련된 미디어 콘텐츠 기획안으로 재구성하세요.</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. API 설정 및 세션 상태 초기화
# ---------------------------------------------------------
st.sidebar.header("API 설정")
client_id = st.secrets.get("NAVER_CLIENT_ID", "").strip() or st.sidebar.text_input("Naver Client ID", type="password").strip()
client_secret = st.secrets.get("NAVER_CLIENT_SECRET", "").strip() or st.sidebar.text_input("Naver Client Secret", type="password").strip()
gemini_key = st.secrets.get("GEMINI_API_KEY", "").strip() or st.sidebar.text_input("Gemini API Key", type="password").strip()

if 'page_number' not in st.session_state:
    st.session_state['page_number'] = 1

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
def fetch_naver_news(query, display_count=100):
    search_term = query.strip() if query and query.strip() else "뉴스"
    url = f"https://naverapihub.apigw.ntruss.com/search/v1/news?query={search_term}&display={display_count}&sort=date"
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

# Gemini 기획안 생성 함수 (오류 및 예외 완전 보완)
def generate_content_plan(selected_title, content_format, api_key):
    try:
        client = genai.Client(api_key=api_key)
        prompt = f"""
        당신은 창의적인 미디어 콘텐츠 프로듀서이자 스토리텔러입니다.
        다음 뉴스 기사 제목을 바탕으로 선택된 미디어 형식에 맞춘 구체적인 콘텐츠 기획안을 작성해주세요.

        - 뉴스 기사 제목: {selected_title}
        - 타겟 콘텐츠 형식: {content_format} (인스타그램 카드뉴스, 공익 캠페인 포스터, 미니북, 만화 중 하나)

        반드시 아래 마크다운 구조에 맞춰서 알차게 작성해줘:
        ### 1. 기획 의도 및 핵심 메시지
        ### 2. 타깃 독자층
        ### 3. 형식별 전달 방식 및 레이아웃/장면 구성안 (선택한 {content_format} 형식의 구체적 컷/페이지/디자인 연출 묘사)
        ### 4. 매체 특성에 따른 메시지 표현 차별점 (이 형식이 왜 효과적인지)
        ### 5. 추가 취재 또는 연출 팁 제안
        """
        
        # 모델 시도
        model_candidates = ['gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-pro']
        last_error = ""
        for model_name in model_candidates:
            try:
                response = client.models.generate_content(model=model_name, contents=prompt)
                if response and response.text:
                    return response.text
            except Exception as e:
                last_error = str(e)
                continue
                
        return f"❌ 기획안 생성 중 오류가 발생했습니다: {last_error}"
    except Exception as err:
        return f"❌ API 연결 오류: {str(err)}"

# ---------------------------------------------------------
# 4. 시안 네온 검색 바 UI
# ---------------------------------------------------------
st.markdown('<div class="search-container">', unsafe_allow_html=True)
search_col1, search_col2 = st.columns([5, 1])
with search_col1:
    search_query = st.text_input(
        "뉴스 검색어 입력",
        value="",
        placeholder="검색어를 입력해 주세요 (예: 청소년 수면, 기후위기, AI 윤리, 딥페이크)",
        label_visibility="collapsed"
    )
with search_col2:
    search_btn = st.button("검색", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

if search_btn or 'news_pool' not in st.session_state:
    if client_id and client_secret:
        with st.spinner("최신 뉴스를 불러오는 중..."):
            st.session_state['news_pool'] = fetch_naver_news(search_query)
            st.session_state['last_query'] = search_query.strip() if search_query.strip() else "전체 최신 이슈"
            st.session_state['page_number'] = 1

# ---------------------------------------------------------
# 5. 2컬럼 레이아웃 (왼쪽: 뉴스목록, 오른쪽: 형식선택 & 리포트)
# ---------------------------------------------------------
if 'news_pool' in st.session_state and st.session_state['news_pool']:
    all_news = st.session_state['news_pool']
    total_news_count = len(all_news)
    
    items_per_page = 10
    total_pages = max(1, (total_news_count + items_per_page - 1) // items_per_page)
    
    current_page = st.session_state['page_number']
    start_idx = (current_page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    current_news_batch = all_news[start_idx:end_idx]

    left_col, right_col = st.columns([1.2, 1])

    # -----------------------------------------------------
    # [왼쪽 컬럼] 최신 뉴스 라인업 & 페이지 네이션
    # -----------------------------------------------------
    with left_col:
        st.markdown(f"### '{st.session_state.get('last_query', '전체 최신 이슈')}' 최신 뉴스 검색 결과 ({total_news_count}건)")
        st.caption(f"최신순으로 정렬된 기사 목록입니다. (페이지 {current_page} / {total_pages})")

        article_options = {}
        for idx, item in enumerate(current_news_batch):
            clean_title = item.get('title', '').replace("<b>", "").replace("</b>", "").replace("&quot;", '"').replace("&amp;", "&")
            clean_desc = item.get('description', '').replace("<b>", "").replace("</b>", "").replace("&quot;", '"').replace("&amp;", "&")
            link = item.get('originallink', item.get('link', '#'))
            pub_date = parse_pub_date(item.get('pubDate', ''))
            
            label = f"[{pub_date}] {clean_title}"
            article_options[label] = {"title": clean_title, "link": link, "desc": clean_desc, "date": pub_date}

        selected_label = st.radio(
            "기사 선택",
            options=list(article_options.keys()),
            key=f"radio_page_{current_page}",
            label_visibility="collapsed"
        )

        p_col1, p_col2, p_col3 = st.columns([1, 2, 1])
        with p_col1:
            if current_page > 1:
                if st.button("◀ 이전 페이지", use_container_width=True):
                    st.session_state['page_number'] -= 1
                    st.rerun()
        with p_col2:
            st.markdown(f"<div style='text-align: center; padding-top: 10px; color: #94a3b8;'>{current_page} / {total_pages} Page</div>", unsafe_allow_html=True)
        with p_col3:
            if current_page < total_pages:
                if st.button("다음 페이지 ▶", use_container_width=True):
                    st.session_state['page_number'] += 1
                    st.rerun()

    # -----------------------------------------------------
    # [오른쪽 컬럼] 변환할 미디어 형식 선택 & AI 리포트 출력
    # -----------------------------------------------------
    with right_col:
        st.markdown("### 기획할 미디어 콘텐츠 유형 선택")
        
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

        submit_plan = st.button("AI 미디어 콘텐츠 기획안 생성하기", use_container_width=True)

        # 버튼 클릭 이벤트 발생 시 기획안 생성 및 세션 저장[cite: 11]
        if submit_plan:
            if not gemini_key:
                st.error("❌ 사이드바에 Gemini API Key를 입력해 주세요!")
            elif selected_label not in article_options:
                st.warning("⚠️ 선택된 뉴스 기사 정보를 찾을 수 없습니다.")
            else:
                selected_article = article_options[selected_label]
                with st.spinner("AI 기획안을 작성하고 있습니다..."):
                    plan_result = generate_content_plan(selected_article['title'], content_format, gemini_key)
                    st.session_state['selected_article'] = selected_article
                    st.session_state['content_format'] = content_format
                    st.session_state['plan_result'] = plan_result

        # 저장된 결과가 있으면 항상 출력되도록 보장
        if 'plan_result' in st.session_state and st.session_state['plan_result']:
            st.markdown('<div class="right-card-box" style="border-color: #22d3ee; box-shadow: 0 0 15px rgba(34, 211, 238, 0.2); margin-top: 25px;">', unsafe_allow_html=True)
            st.markdown("### AI 미디어 콘텐츠 기획 리포트")
            
            art = st.session_state['selected_article']
            link_url = art['link']
            st.info(f"선택한 뉴스: {art['title']} | {art['date']}\n\n[원문 기사 보기]({link_url})")
            st.markdown(f"변환 형식: `{st.session_state['content_format']}`")
            st.markdown("---")
            st.markdown(st.session_state['plan_result'])
            st.markdown('</div>', unsafe_allow_html=True)
