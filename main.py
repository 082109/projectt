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

    .search-container {
        background: #0d1527;
        border: 2px solid #22d3ee;
        border-radius: 20px;
        padding: 8px 16px;
        box-shadow: 0 0 25px rgba(34, 211, 238, 0.3);
        margin-bottom: 30px;
    }

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

    /* 실제 미디어 콘텐츠 결과물 시각화 카드 스타일 */
    .content-preview-card {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border: 2px solid #22d3ee;
        border-radius: 20px;
        padding: 30px;
        margin-top: 25px;
        box-shadow: 0 0 30px rgba(34, 211, 238, 0.25);
    }
    
    .content-slide {
        background-color: #080c14;
        border: 1px solid #334155;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 15px;
    }

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
st.markdown('<div class="hero-subtitle">트렌드 뉴스를 최신순으로 탐색하고, 세련된 미디어 콘텐츠로 직접 구현하세요.</div>', unsafe_allow_html=True)

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

# Gemini를 통해 실제 미디어 콘텐츠 결과물(카드뉴스 슬라이드 등)을 생성하는 함수
def generate_actual_media_content(selected_title, selected_desc, content_format, api_key):
    try:
        client = genai.Client(api_key=api_key)
        prompt = f"""
        당신은 프로페셔널한 미디어 콘텐츠 크리에이터입니다.
        아래 뉴스 기사를 바탕으로 사용자가 선택한 미디어 형식에 맞는 **실제 콘텐츠 텍스트 및 카드별 구성 내용**을 작성해주세요.

        - 뉴스 제목: {selected_title}
        - 뉴스 내용 요약: {selected_desc}
        - 콘텐츠 형식: {content_format} (인스타그램 카드뉴스, 공익 캠페인 포스터, 미니북, 만화 중 하나)

        반드시 아래 JSON 형태나 명확한 슬라이드 형식으로 각 장(또는 컷)별 들어갈 **[핵심 문구(Title)]**와 **[상세 내용/시각 연출 묘사(Body)]**를 총 4장(슬라이드/컷) 분량으로 작성해줘. 다른 군더더기 인사말은 넣지 말고 결과물 내용만 출력해줘.

        출력 예시 형식:
        [슬라이드 1]
        제목: ...
        본문: ...

        [슬라이드 2]
        제목: ...
        본문: ...

        [슬라이드 3]
        제목: ...
        본문: ...

        [슬라이드 4]
        제목: ...
        본문: ...
        """
        
        candidate_models = ['gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-2.0-flash']
        last_err = ""
        
        for model_name in candidate_models:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                if response and response.text:
                    return response.text
            except Exception as e:
                last_err = str(e)
                continue
                
        return f"❌ 콘텐츠 생성 실패: {last_err}"
            
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
# 5. 2컬럼 레이아웃 (왼쪽: 뉴스목록, 오른쪽: 형식선택 & 실제 콘텐츠 출력)
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
    # [오른쪽 컬럼] 미디어 형식 선택 & 실제 완성된 콘텐츠 출력
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

        submit_plan = st.button("AI 미디어 콘텐츠 생성하기", use_container_width=True)

        if submit_plan:
            if not gemini_key:
                st.error("❌ 사이드바에 Gemini API Key를 입력해 주세요!")
            elif selected_label not in article_options:
                st.warning("⚠️ 선택된 뉴스 기사 정보를 찾을 수 없습니다.")
            else:
                selected_article = article_options[selected_label]
                with st.spinner(f"'{content_format}' 형식의 미디어 콘텐츠를 제작하고 있습니다..."):
                    content_result = generate_actual_media_content(
                        selected_article['title'], 
                        selected_article['desc'], 
                        content_format, 
                        gemini_key
                    )
                    st.session_state['selected_article'] = selected_article
                    st.session_state['content_format'] = content_format
                    st.session_state['content_result'] = content_result

        # 생성된 실제 미디어 콘텐츠 카드 형태로 시각화 출력
        if 'content_result' in st.session_state and st.session_state['content_result']:
            st.markdown('<div class="content-preview-card">', unsafe_allow_html=True)
            st.markdown(f"### 🎬 AI 제작된 [{st.session_state['content_format']}] 결과물")
            
            art = st.session_state['selected_article']
            link_url = art['link']
            st.info(f"기반 뉴스: {art['title']}\n\n[원문 기사 보러가기]({link_url})")
            st.markdown("---")
            
            # AI가 만들어준 콘텐츠 내용을 시각적 카드 슬라이드 박스로 렌더링
            st.markdown(st.session_state['content_result'])
            
            st.markdown('</div>', unsafe_allow_html=True)
