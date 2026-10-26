import streamlit as st
import urllib.request
import urllib.parse
import json
from datetime import datetime
import io
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------
# 1. 페이지 기본 설정 및 우아한 세리프 폰트 UI 스타일링
# ---------------------------------------------------------
st.set_page_config(
    page_title="FrameLens - 뉴스 미디어 기획 포털",
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
        width: 100%;
    }
    .stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
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

    .image-preview-container {
        background: #0d1527;
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

# Gemini AI를 통한 뉴스 기사 맞춤형 텍스트 콘텐츠 생성
def generate_ai_content_text(title, desc, content_format, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={api_key}"
    
    prompt = f"""
    당신은 프로페셔널한 미디어 콘텐츠 크리에이터입니다.
    다음 뉴스 기사를 바탕으로 '{content_format}' 형식에 어울리는 핵심 맞춤형 문구를 작성해주세요.

    - 뉴스 제목: {title}
    - 뉴스 요약: {desc}
    - 콘텐츠 형식: {content_format}

    반드시 아래 형식으로 딱 2줄만 요약해서 작성해줘 (다른 설명 없이 결과만 출력):
    헤드카피: [눈길을 사로잡는 강렬한 한 줄 카피]
    본문요약: [뉴스의 핵심 내용을 담은 2문장 내외의 요약 설명]
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
        return f"헤드카피: {title}\n본문요약: {desc}"
    except Exception:
        return f"헤드카피: {title}\n본문요약: {desc}"

# AI가 생성한 기사 맞춤형 텍스트를 바탕으로 PIL 이미지 생성
def create_media_content_image(content_format, ai_text_result):
    if content_format == "인스타그램 카드뉴스":
        img_width, img_height = 800, 800
        bg_color = (13, 21, 39)
        accent_color = (34, 211, 238)
        badge_text = "[ INSTAGRAM CARD NEWS ]"
    elif content_format == "공익 캠페인 포스터":
        img_width, img_height = 700, 950
        bg_color = (15, 23, 42)
        accent_color = (250, 204, 21)
        badge_text = "[ PUBLIC CAMPAIGN POSTER ]"
    else:
        img_width, img_height = 850, 600
        bg_color = (30, 27, 75)
        accent_color = (244, 114, 182)
        badge_text = "[ WEBTOON / CUTTOON COMIC ]"

    image = Image.new("RGB", (img_width, img_height), color=bg_color)
    draw = ImageDraw.Draw(image)

    try:
        font_title = ImageFont.truetype("usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
        font_body = ImageFont.truetype("usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        font_badge = ImageFont.truetype("usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
    except Exception:
        font_title = ImageFont.load_default()
        font_body = ImageFont.load_default()
        font_badge = ImageFont.load_default()

    draw.rectangle([25, 25, img_width - 25, img_height - 25], outline=accent_color, width=3)
    draw.text((50, 50), badge_text, fill=accent_color, font=font_badge)

    headcopy = "AI 미디어 콘텐츠 기획"
    bodytext = ai_text_result
    for line in ai_text_result.split("\n"):
        if "헤드카피:" in line:
            headcopy = line.replace("헤드카피:", "").strip()
        elif "본문요약:" in line:
            bodytext = line.replace("본문요약:", "").strip()

    margin = 50
    max_width = img_width - 100
    y_text = 100

    draw.text((margin, y_text), "📌 [핵심 헤드카피]", fill=accent_color, font=font_badge)
    y_text += 30

    words = headcopy.split()
    line = ""
    for word in words:
        test_line = line + word + " "
        if draw.textlength(test_line, font=font_title) <= max_width:
            line = test_line
        else:
            draw.text((margin, y_text), line, fill=(255, 255, 255), font=font_title)
            y_text += 40
            line = word + " "
    if line:
        draw.text((margin, y_text), line, fill=(255, 255, 255), font=font_title)
        y_text += 60

    draw.line([(margin, y_text), (img_width - 50, y_text)], fill=(71, 85, 105), width=2)
    y_text += 40

    draw.text((margin, y_text), "📝 [뉴스 상세 요약 및 연출]", fill=accent_color, font=font_badge)
    y_text += 30

    words = bodytext.split()
    line = ""
    for word in words:
        test_line = line + word + " "
        if draw.textlength(test_line, font=font_body) <= max_width:
            line = test_line
        else:
            draw.text((margin, y_text), line, fill=(203, 213, 225), font=font_body)
            y_text += 30
            line = word + " "
            if y_text > img_height - 100:
                break
    if line:
        draw.text((margin, y_text), line, fill=(203, 213, 225), font=font_body)

    draw.text((margin, img_height - 60), "FrameLens Media Production Portal", fill=accent_color, font=font_badge)

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)
    return buf

# ---------------------------------------------------------
# 화면 1: 초기 검색 창 (st.form을 적용해 엔터 키 입력 시 검색 실행)
# ---------------------------------------------------------
if st.session_state['step'] == 'search':
    st.markdown('<div style="height: 60px;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-title">FrameLens</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">탐색하고 싶은 뉴스 키워드를 입력하고, 맞춤형 미디어 콘텐츠 이미지를 생성해보세요.</div>', unsafe_allow_html=True)

    # st.form으로 감싸서 엔터 키만 눌러도 검색이 실행되도록 처리
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
# 화면 2: 뉴스 기사 선택 및 맞춤형 이미지 생성 화면
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

        # [오른쪽 컬럼] 미디어 형식 선택 및 기사 맞춤형 이미지 생성
        with right_col:
            st.markdown("### 기획할 미디어 콘텐츠 유형 선택")
            
            content_format = st.selectbox(
                "형식 선택",
                [
                    "인스타그램 카드뉴스",
                    "공익 캠페인 포스터",
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

            submit_plan = st.button("기사 맞춤형 이미지 생성하기", use_container_width=True)

            if submit_plan:
                if not gemini_key:
                    st.error("❌ 사이드바에 API Key를 입력해 주세요!")
                elif selected_label not in article_options:
                    st.warning("⚠️ 선택된 뉴스 기사 정보를 찾을 수 없습니다.")
                else:
                    selected_article = article_options[selected_label]
                    
                    with st.spinner(f"⏳ AI가 선택된 뉴스 기사를 분석하고 '{content_format}' 맞춤형 이미지를 제작하고 있습니다..."):
                        ai_text_result = generate_ai_content_text(
                            selected_article['title'], 
                            selected_article['desc'], 
                            content_format, 
                            gemini_key
                        )
                        image_bytes = create_media_content_image(content_format, ai_text_result)
                        
                        st.session_state['selected_article'] = selected_article
                        st.session_state['content_format'] = content_format
                        st.session_state['image_bytes'] = image_bytes

            if 'image_bytes' in st.session_state and st.session_state['image_bytes']:
                st.markdown('<div class="image-preview-container">', unsafe_allow_html=True)
                st.markdown(f"### 🎬 [{st.session_state['content_format']}] 맞춤형 이미지 생성 완료")
                art = st.session_state['selected_article']
                st.markdown(f"**기반 뉴스**: [{art['title']}]({art['link']})")
                st.markdown("---")
                
                st.image(st.session_state['image_bytes'], use_container_width=True, caption=f"{art['title']} - {st.session_state['content_format']}")
                
                st.download_button(
                    label="📥 기사 맞춤형 이미지 다운로드 (PNG)",
                    data=st.session_state['image_bytes'],
                    file_name=f"FrameLens_{st.session_state['content_format'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                    mime="image/png",
                    use_container_width=True
                )
                st.markdown('</div>', unsafe_allow_html=True)
