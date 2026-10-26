import streamlit as st
import urllib.request
import urllib.parse
import json
from datetime import datetime
import io
import time # 이미지 생성 대기용
import requests # Imagen API 호출용 (urllib 대체)

# ---------------------------------------------------------
# 1. 페이지 기본 설정 및 스타일링
# ---------------------------------------------------------
st.set_page_config(
    page_title="FrameLens - AI 미디어 이미지 포털",
    page_icon="🎬",
    layout="wide"
)

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

    .stButton > button, div[data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(135deg, #e11d48 0%, #b91c1c 100%); /* 진짜 이미지 생성을 강조하는 컬러 */
        color: #ffffff;
        border: none;
        border-radius: 12px;
        font-weight: 700;
        font-size: 0.95rem;
        height: 48px;
        box-shadow: 0 4px 14px rgba(225, 29, 72, 0.35);
        transition: all 0.2s ease;
        font-family: 'Noto Serif KR', serif !important;
        width: 100%;
    }
    .stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
        background: linear-gradient(135deg, #fb7185 0%, #e11d48 100%);
        box-shadow: 0 6px 18px rgba(251, 113, 133, 0.45);
        transform: translateY(-1px);
    }

    .right-card-box {
        background-color: #0d1527;
        border: 1px solid #1e293b;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
    }

    .image-preview-container {
        background: #0d1527;
        border: 2px solid #e11d48;
        border-radius: 20px;
        padding: 30px;
        margin-top: 25px;
        box-shadow: 0 0 30px rgba(225, 29, 72, 0.25);
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
# 2. 세션 상태 초기화 및 폰트 준비 (Pillow 삭제로 폰트 불필요)
# ---------------------------------------------------------
if 'step' not in st.session_state:
    st.session_state['step'] = 'search'

if 'page_number' not in st.session_state:
    st.session_state['page_number'] = 1

if 'api_key_set' not in st.session_state:
    st.session_state['api_key_set'] = False

st.sidebar.header("API 설정")
client_id = st.secrets.get("NAVER_CLIENT_ID", "").strip() or st.sidebar.text_input("Naver Client ID", type="password").strip()
client_secret = st.secrets.get("NAVER_CLIENT_SECRET", "").strip() or st.sidebar.text_input("Naver Client Secret", type="password").strip()
gemini_key = st.secrets.get("GEMINI_API_KEY", "").strip() or st.sidebar.text_input("Gemini (Imagen) API Key", type="password").strip()

if not (client_id and client_secret and gemini_key):
    st.info("💡 사이드바에 API 키를 입력하거나 `.streamlit/secrets.toml`에 설정해주세요.")
else:
    st.session_state['api_key_set'] = True

def parse_pub_date(pub_date_str):
    if not pub_date_str:
        return "날짜 정보 없음"
    try:
        dt = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %z")
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return pub_date_str

def fetch_naver_news(query, display_count=100):
    search_term = query.strip() if query and query.strip() else "뉴스"
    encText = urllib.parse.quote(search_term)
    # 네이버 클라우드 플랫폼 NCP APIGW 사용 예시 (client_id/secret 헤더 사용)
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

# ---------------------------------------------------------
# [핵심] Imagen (이미지 생성 모델) API 호출 함수 - 진짜 AI 그림 생성
# ---------------------------------------------------------
def generate_real_ai_image(title, desc, content_format, api_key):
    # Imagen-3 모델 또는 사용 가능한 최신 이미지 생성 모델 엔드포인트
    # (구글 AI Studio 또는 Vertex AI 엔드포인트 형식)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0:generateImages?key={api_key}"
    
    # 형식에 맞는 구체적인 이미지 생성 프롬프트 구성
    if content_format == "만화 (컷툰/웹툰)":
        prompt_style = "A detailed 4-panel Korean webtoon comic strip with thick borders and speech bubbles,"
        prompt_logic = f"Illustrate a story based on the news '{title}'. Panel 1: Introduce the issue: '{desc[:50]}...'. Panel 2: The conflict. Panel 3: Key point. Panel 4: Conclusion. Full color, expressive characters, cute and humorous webtoon style, white background."
    elif content_format == "포스터":
        prompt_style = "A sleek, minimalist public campaign poster,"
        prompt_logic = f"Design a strong visual symbol at the top illustrating the theme '{title}'. A clear catchphrase '{title[:25]}...' at the bottom. Full color, digital art style, deep colors, bold design, centered composition, border."
    else: # 인포그래픽
        prompt_style = "A professional, clean data infographic,"
        prompt_logic = f"A prominent title '{title[:30]}...' at the top banner. Visual sections for statistics including a clear bar chart and a pie chart illustrating '{desc[:60]}...'. Use icons, full color, modern graphic design style, data visual feel, mint green accent color, white background."

    final_prompt = f"{prompt_style} {prompt_logic} The news is about: '{title}', '{desc}'."

    payload = {
        "contents": [{"parts": [{"text": final_prompt}]}],
        "parameters": {
            "imageCount": 1,
            # 모델에 따라 parameters 형식 다를 수 있음 (Vertex AI vs AI Studio)
            # 여기서는 AI Studio 예시
            "aspectRatio": "16:9" # 또는 1:1, 9:16 등 형식별 최적화 가능
        }
    }
    
    headers = {
        'Content-Type': 'application/json',
    }
    
    try:
        # requests 라이브러리 사용
        with st.spinner("⏳ AI가 뉴스 기사를 분석하고 진짜 시각적 이미지를 렌더링하고 있습니다... (약 10~15초 소요)"):
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                res_json = response.json()
                # 이미지 바이너리 데이터 추출 (base64 인코딩 가정)
                base64_image = res_json['images'][0]['image']
                import base64
                image_bytes = base64.b64decode(base64_image)
                return image_bytes
            else:
                st.error(f"❌ Imagen API 호출 실패: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"❌ 이미지 생성 중 오류 발생: {e}")

    return None

# ---------------------------------------------------------
# 화면 1: 초기 검색 창 (st.form 적용으로 엔터 키 검색 지원)
# ---------------------------------------------------------
if st.session_state['step'] == 'search':
    st.markdown('<div style="height: 60px;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-title">FrameLens AI Media</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">뉴스 키워드를 입력하고, AI가 뉴스에 맞춰 생성한 진짜 시각 이미지를 체험해보세요. 제발된다고!</div>', unsafe_allow_html=True)

    with st.form(key="search_form"):
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
            search_trigger = st.form_submit_button("검색", use_container_width=True)
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
# 화면 2: 뉴스 기사 선택 및 진짜 AI 이미지 생성 화면
# ---------------------------------------------------------
elif st.session_state['step'] == 'result':
    top_col1, top_col2 = st.columns([4, 1])
    with top_col1:
        st.markdown(f"## FrameLens AI | '{st.session_state.get('last_query', '')}' 뉴스 탐색")
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

        with right_col:
            st.markdown("### 기획할 미디어 콘텐츠 유형 선택")
            
            content_format = st.selectbox(
                "형식 선택",
                [
                    "만화 (컷툰/웹툰)",
                    "포스터",
                    "인포그래픽"
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

            submit_plan = st.button("AI 시각 이미지 생성하기", use_container_width=True)

            if submit_plan:
                if not st.session_state['api_key_set']:
                    st.error("❌ 사이드바에 Imagen API Key를 입력해 주세요!")
                elif selected_label not in article_options:
                    st.warning("⚠️ 선택된 뉴스 기사 정보를 찾을 수 없습니다.")
                else:
                    selected_article = article_options[selected_label]
                    
                    # [핵심] 진짜 AI 그림 생성 함수 호출
                    image_bytes = generate_real_ai_image(
                        selected_article['title'], 
                        selected_article['desc'], 
                        content_format, 
                        gemini_key
                    )
                    
                    if image_bytes:
                        st.session_state['selected_article'] = selected_article
                        st.session_state['content_format'] = content_format
                        st.session_state['real_image_bytes'] = image_bytes
                    else:
                        st.error("❌ 이미지 생성에 실패했습니다. 다시 시도해 주세요.")

            # 생성된 진짜 AI 이미지 결과물 렌더링 및 다운로드
            if 'real_image_bytes' in st.session_state and st.session_state['real_image_bytes']:
                st.markdown('<div class="image-preview-container">', unsafe_allow_html=True)
                st.markdown(f"### 🎬 AI가 뉴스에 맞춰 생성한 [{st.session_state['content_format']}] 이미지")
                art = st.session_state['selected_article']
                st.markdown(f"**기반 뉴스**: [{art['title']}]({art['link']})")
                st.markdown("---")
                
                # Pillow가 아닌 st.image로 바이너리 데이터 직접 출력
                st.image(st.session_state['real_image_bytes'], use_container_width=True, caption=f"{art['title']} - {st.session_state['content_format']} (AI Generated)")
                
                st.download_button(
                    label="📥 AI 생성 고화질 이미지 다운로드 (PNG)",
                    data=st.session_state['real_image_bytes'],
                    file_name=f"FrameLens_AI_{st.session_state['content_format'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                    mime="image/png",
                    use_container_width=True
                )
                st.markdown('</div>', unsafe_allow_html=True)
