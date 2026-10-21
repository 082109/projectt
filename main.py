import streamlit as st
import urllib.request
import urllib.parse
import json
from datetime import datetime

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
        font-size: 3.5rem;
        font-weight: 900;
        color: #ffffff;
        text-align: center;
        margin-top: 40px;
        margin-bottom: 8px;
        letter-spacing: -1.5px;
    }
    .hero-subtitle {
        font-family: 'Noto Serif KR', serif !important;
        color: #94a3b8;
        font-size: 1.15rem;
        text-align: center;
        margin-bottom: 40px;
        font-weight: 300;
    }

    .search-container {
        background: #0d1527;
        border: 2px solid #22d3ee;
        border-radius: 24px;
        padding: 12px 20px;
        box-shadow: 0 0 35px rgba(34, 211, 238, 0.25);
        margin: 0 auto 30px auto;
        max-width: 800px;
    }

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

    .stButton > button {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
        color: #ffffff;
        border: none;
        border-radius: 12px;
        font-weight: 700;
        font-size: 0.95rem;
        height: 48px;
        box-shadow: 0 4px 14px rgba(2, 132, 199, 0.35);
        transition: all 0.2s ease;
        font-family: 'Noto Serif KR', serif !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%);
        box-shadow: 0 6px 18px rgba(56, 189, 248, 0.45);
        transform: translateY(-1px);
    }

    .right-card-box {
        background-color: #0d1527;
        border: 1px solid #1e293b;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
    }

    .content-preview-card {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border: 2px solid #22d3ee;
        border-radius: 20px;
        padding: 30px;
        margin-top: 25px;
        box-shadow: 0 0 30px rgba(34, 211, 238, 0.25);
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
# 2. 세션 상태 초기화
# ---------------------------------------------------------
if 'step' not in st.session_state:
    st.session_state['step'] = 'search'

if 'page_number' not in st.session_state:
    st.session_state['page_number'] = 1

st.sidebar.header("API 설정")
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
def fetch_naver_news(query, display_count=100):
    search_term = query.strip() if query and query.strip() else "뉴스"
    encText = urllib.parse.quote(search_term)
    url = f"https://naverapihub.apigw.ntruss.com/search/v1/news?query={encText}&display={display_count}&sort=date"
    
    req = urllib.request.Request(url)
    req.add_header("X-NCP-APIGW-API-KEY-ID", client_id)
    req.add_header("X-NCP-APIGW-API-KEY", client_secret)
    
    try:
        with urllib.request.urlopen(req) as response:
            if response.getcode() == 200:
                data = json.loads(response.read().decode('utf-8'))
                return data.get('items', [])
        return []
    except Exception:
        return []

# Gemini AI 콘텐츠 생성 함수 (gemini-1.5-flash 표준 엔드포인트 적용)
def generate_actual_media_content(selected_title, selected_desc, content_format, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    prompt = f"""
    당신은 프로페셔널한 미디어 콘텐츠 크리에이터입니다.
    아래 뉴스 기사를 바탕으로 사용자가 선택한 미디어 형식에 맞는 **실제 콘텐츠 내용 및 카드별 구성**을 작성해주세요.

    - 뉴스 제목: {selected_title}
    - 뉴스 요약: {selected_desc}
    - 콘텐츠 형식: {content_format}

    선택한 형식({content_format})의 특성을 살려 4개의 카드/컷/페이지로 나누어 구체적인 문구와 연출을 작성해줘:
    
    [1장 / 1컷]
    - 메인 헤드카피:
    - 시각 연출 및 디자인 묘사:
    - 본문 내용:

    [2장 / 2컷]
    - 메인 헤드카피:
    - 시각 연출 및 디자인 묘사:
    - 본문 내용:

    [3장 / 3컷]
    - 메인 헤드카피:
    - 시각 연출 및 디자인 묘사:
    - 본문 내용:

    [4장 / 4컷]
    - 메인 헤드카피:
    - 시각 연출 및 디자인 묘사:
    - 본문 내용:
    """

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req) as response:
            if response.getcode() == 200:
                res_json = json.loads(response.read().decode('utf-8'))
                return res_json['candidates'][0]['content']['parts'][0]['text']
        return "❌ AI 응답을 받아오지 못했습니다."
    except Exception as err:
        return f"❌ 오류 발생: {str(err)}"

# ---------------------------------------------------------
# 화면 1: 초기 검색 창만 심플하게 뜨는 메인 홈
# ---------------------------------------------------------
if st.session_state['step'] == 'search':
    st.markdown('<div style="height: 60px;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-title">FrameLens</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">탐색하고 싶은 뉴스 키워드를 입력하고, 세련된 미디어 콘텐츠를 기획해보세요.</div>', unsafe_allow_html=True)

    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    s_col1, s_col2 = st.columns([5, 1])
    with s_col1:
        keyword_input = st.text_input(
            "뉴스 검색어 입력",
            value="",
            placeholder="검색어를 입력하세요 (예: 청소년 수면, 기후위기, AI 윤리, 딥페이크)",
            label_visibility="collapsed"
        )
    with s_col2:
        search_trigger = st.button("검색", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if search_trigger:
        if not keyword_input.strip():
            st.warning("⚠️ 검색어를 입력해주세요!")
        elif client_id and client_secret:
            with st.spinner("뉴스를 불러오는 중입니다..."):
                news_data = fetch_naver_news(keyword_input)
                st.session_state['news_pool'] = news_data
                st.session_state['last_query'] = keyword_input.strip()
                st.session_state['page_number'] = 1
                st.session_state['step'] = 'result'
                st.rerun()

# ---------------------------------------------------------
# 화면 2: 뉴스 기사 선택 및 AI 콘텐츠 생성 화면
# ---------------------------------------------------------
elif st.session_state['step'] == 'result':
    top_col1, top_col2 = st.columns([4, 1])
    with top_col1:
        st.markdown(f"## FrameLens | '{st.session_state.get('last_query', '')}' 뉴스 탐색")
    with top_col2:
        if st.button("← 다시 검색하기", use_container_width=True):
            st.session_state['step'] = 'search'
            st.rerun()

    st.markdown("---")

    all_news = st.session_state.get('news_pool', [])
    total_news_count = len(all_news)

    if total_news_count == 0:
        st.warning("검색 결과가 없습니다. 다른 검색어로 다시 시도해보세요.")
    else:
        items_per_page = 10
        total_pages = max(1, (total_news_count + items_per_page - 1) // items_per_page)
        
        current_page = st.session_state['page_number']
        start_idx = (current_page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        current_news_batch = all_news[start_idx:end_idx]

        left_col, right_col = st.columns([1.2, 1])

        # [왼쪽 컬럼] 뉴스 목록
        with left_col:
            st.markdown(f"### 최신 뉴스 목록 ({total_news_count}건)")
            st.caption(f"최신순 정렬 (페이지 {current_page} / {total_pages})")

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

        # [오른쪽 컬럼] 미디어 형식 선택 및 AI 콘텐츠 생성
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

            st.markdown('<div class="right-card-box" style="margin-top: 20px;">', unsafe_allow_html=True)
            if selected_label in article_options:
                selected_art = article_options[selected_label]
                st.markdown(f"**선택된 뉴스 기사**")
                st.write(f"📌 {selected_art['title']}")
                st.caption(f"발행일: {selected_art['date']}")
                st.markdown(f"[원문 기사 읽기]({selected_art['link']})")
            st.markdown('</div>', unsafe_allow_html=True)

            submit_plan = st.button("AI 미디어 콘텐츠 생성하기", use_container_width=True)

            if submit_plan:
                if not gemini_key:
                    st.error("❌ 사이드바에 Gemini API Key를 입력해 주세요!")
                elif selected_label not in article_options:
                    st.warning("⚠️ 선택된 뉴스 기사 정보를 찾을 수 없습니다.")
                else:
                    selected_article = article_options[selected_label]
                    
                    # Streamlit 기본 로딩 스피너와 예상 소요 시간 안내 적용 (두 번째 사진의 회전 아이콘 효과)
                    with st.spinner("⏳ AI가 선택된 형식을 바탕으로 미디어 콘텐츠를 제작하고 있습니다... (예상 소요 시간: 약 3~5초)"):
                        content_result = generate_actual_media_content(
                            selected_article['title'], 
                            selected_article['desc'], 
                            content_format, 
                            gemini_key
                        )
                        st.session_state['selected_article'] = selected_article
                        st.session_state['content_format'] = content_format
                        st.session_state['content_result'] = content_result

            # 생성된 결과가 있으면 하단에 멋진 카드 형태로 렌더링
            if 'content_result' in st.session_state and st.session_state['content_result']:
                st.markdown('<div class="content-preview-card">', unsafe_allow_html=True)
                st.markdown(f"### 🎬 AI 제작된 [{st.session_state['content_format']}] 결과물")
                art = st.session_state['selected_article']
                st.markdown(f"**기반 뉴스**: [{art['title']}]({art['link']})")
                st.markdown("---")
                st.markdown(st.session_state['content_result'])
                st.markdown('</div>', unsafe_allow_html=True)
