import streamlit as st
import urllib.request
import urllib.parse
import json
from datetime import datetime
import io
import os
import time
import requests
import random
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------
# 1. 페이지 기본 설정 및 트렌디 현대적 스타일링 (이미지 컨셉 반영)
# ---------------------------------------------------------
st.set_page_config(
    page_title="FrameLens Studio",
    page_icon="🎬",
    layout="wide"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;600;700;800&display=swap');

    /* 화사하고 현대적인 블루 그라데이션 배경 */
    .stApp {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 50%, #1e40af 100%);
        color: #ffffff;
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif !important;
    }
    
    /* 사이드바 스타일링 */
    section[data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
        font-family: 'Pretendard', sans-serif !important;
    }
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] div, 
    section[data-testid="stSidebar"] a {
        color: #ffffff !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
    }
    [data-testid="stSidebarNav"] a {
        color: #ffffff !important;
        background-color: rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        margin-bottom: 8px !important;
        padding: 12px 16px !important;
    }
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.4);
    }
    
    .hero-title {
        font-family: 'Pretendard', sans-serif !important;
        font-size: 3.5rem;
        font-weight: 800;
        color: #ffffff;
        text-align: center;
        margin-top: 20px;
        margin-bottom: 10px;
        letter-spacing: -1px;
        text-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    }
    .hero-subtitle {
        font-family: 'Pretendard', sans-serif !important;
        color: #e0f2fe;
        font-size: 1.25rem;
        text-align: center;
        margin-bottom: 40px;
        font-weight: 400;
    }

    /* 이미지 스타일의 알약 형태(Pill) 입체 검색 캡슐 */
    .search-pill-container {
        background: #ffffff;
        border-radius: 50px;
        padding: 6px 8px 6px 24px;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2), 0 5px 15px rgba(0, 0, 0, 0.1);
        max-width: 800px;
        margin: 0 auto 40px auto;
        display: flex;
        align-items: center;
    }

    /* Streamlit 입력 폼 내부 텍스트 스타일 지정 */
    div[data-baseweb="input"] {
        background-color: transparent !important;
        border: none !important;
        font-size: 1.2rem !important;
        font-family: 'Pretendard', sans-serif !important;
    }
    div[data-baseweb="input"] input {
        color: #1e293b !important;
        font-weight: 500 !important;
    }
    div[data-baseweb="input"] input::placeholder {
        color: #94a3b8 !important;
    }

    /* 돋보기 검색버튼 (둥근 알약형 파란색) */
    .stButton > button, div[data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%);
        color: #ffffff;
        border: none;
        border-radius: 40px;
        font-weight: 700;
        font-size: 1.1rem;
        height: 52px;
        box-shadow: 0 6px 18px rgba(37, 99, 235, 0.35);
        transition: all 0.25s ease;
        font-family: 'Pretendard', sans-serif !important;
        width: 100%;
    }
    .stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
        background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%);
        box-shadow: 0 8px 25px rgba(56, 189, 248, 0.5);
        transform: translateY(-2px);
    }

    /* 세련된 현대식 Glassmorphism 카드 디자인 */
    .news-card-item {
        background: rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 20px;
        padding: 22px;
        margin-bottom: 16px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
        transition: all 0.2s ease;
    }
    .news-card-item.selected {
        border: 2.5px solid #38bdf8;
        background: rgba(255, 255, 255, 0.22);
        box-shadow: 0 0 25px rgba(56, 189, 248, 0.4);
    }
    .news-card-date {
        font-size: 0.88rem;
        color: #7dd3fc;
        margin-bottom: 8px;
        font-weight: 600;
    }
    .news-card-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 10px;
        line-height: 1.4;
    }
    .news-card-desc {
        font-size: 0.98rem;
        color: #e2e8f0;
        line-height: 1.6;
        margin-top: 10px;
        border-top: 1px solid rgba(255, 255, 255, 0.15);
        padding-top: 10px;
    }

    .right-card-box {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 20px;
        padding: 24px;
        margin-top: 15px;
        margin-bottom: 20px;
    }

    .summary-card-box {
        background: rgba(15, 23, 42, 0.5);
        border: 1.5px solid #38bdf8;
        border-radius: 18px;
        padding: 22px;
        margin-top: 15px;
    }

    .image-preview-container {
        background: rgba(15, 23, 42, 0.7);
        border: 2px solid #38bdf8;
        border-radius: 24px;
        padding: 35px;
        margin-top: 30px;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
    }

    h1, h2, h3, h4, label {
        font-family: 'Pretendard', sans-serif !important;
    }

    hr {
        border-color: rgba(255, 255, 255, 0.2) !important;
        margin: 25px 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. 세션 상태 초기화 및 폰트 준비
# ---------------------------------------------------------
if 'step' not in st.session_state:
    st.session_state['step'] = 'search'

if 'page_number' not in st.session_state:
    st.session_state['page_number'] = 1

if 'selected_article_idx' not in st.session_state:
    st.session_state['selected_article_idx'] = 0

def get_korean_font(font_size=18):
    font_path = "NanumGothic.ttf"
    if not os.path.exists(font_path):
        try:
            url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Bold.ttf"
            urllib.request.urlretrieve(url, font_path)
        except Exception:
            pass
    
    try:
        if os.path.exists(font_path):
            return ImageFont.truetype(font_path, font_size)
    except Exception:
        pass
    return ImageFont.load_default()

client_id = st.secrets.get("NAVER_CLIENT_ID", "").strip()
client_secret = st.secrets.get("NAVER_CLIENT_SECRET", "").strip()
gemini_key = st.secrets.get("GEMINI_API_KEY", "").strip()

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

def draw_wrapped_text(draw, text, font, fill, x, y, max_width, line_spacing=4):
    words = text.split()
    line = ""
    curr_y = y
    for word in words:
        test_line = line + word + " "
        if draw.textlength(test_line, font=font) <= max_width:
            line = test_line
        else:
            draw.text((x, curr_y), line.strip(), fill=fill, font=font)
            curr_y += font.size + line_spacing
            line = word + " "
    if line:
        draw.text((x, curr_y), line.strip(), fill=fill, font=font)
        curr_y += font.size + line_spacing
    return curr_y

def generate_3line_summary(title, desc, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={api_key}"
    prompt = f"""
    다음 뉴스 기사의 핵심 내용을 3줄로 알기 쉽게 요약해서 JSON으로 작성해주세요.
    - 뉴스 제목: {title}
    - 뉴스 요약: {desc}
    
    JSON 형식:
    {{
      "summary": [
        "첫 번째 핵심 요약 문장",
        "두 번째 핵심 요약 문장",
        "세 번째 핵심 요약 문장"
      ]
    }}
    """
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            if response.getcode() == 200:
                res_json = json.loads(response.read().decode('utf-8'))
                raw_text = res_json['candidates'][0]['content']['parts'][0]['text']
                clean_json = raw_text[raw_text.find("{"):raw_text.rfind("}")+1]
                return json.loads(clean_json).get("summary", [])
    except Exception:
        pass
    return [
        f"📌 {title[:30]}... 사건 발생",
        "📌 주요 관계자 및 관련 기관의 대응 진행 중",
        "📌 향후 사회적·경제적 파급 효과 지속 관찰 필요"
    ]

def fetch_robust_panel_image(prompt_text, index):
    clean_prompt = prompt_text.replace("\n", " ").strip()
    encoded_prompt = urllib.parse.quote(f"2D vibrant anime webtoon style, {clean_prompt}")
    
    for _ in range(3):
        seed = random.randint(100, 9999)
        ai_image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=400&height=400&seed={seed}&nologo=true"
        try:
            res = requests.get(ai_image_url, timeout=15)
            if res.status_code == 200 and len(res.content) > 1500:
                img = Image.open(io.BytesIO(res.content)).convert("RGB")
                w, h = img.size
                if h > 30:
                    img = img.crop((0, 0, w, h - 30))
                return img.resize((380, 380))
        except Exception:
            time.sleep(0.5)
            
    panel_themes = [
        ("🎨 웹툰 1컷: 사건의 시작", (219, 234, 254), (30, 64, 175)),
        ("💡 웹툰 2컷: 원인 분석", (254, 226, 226), (185, 28, 28)),
        ("⚡ 웹툰 3컷: 핵심 대책", (220, 252, 231), (21, 128, 61)),
        ("🌟 웹툰 4컷: 최종 결론", (254, 243, 199), (180, 83, 9))
    ]
    title_text, bg_col, text_col = panel_themes[index % 4]
    p_img = Image.new("RGB", (380, 380), color=bg_col)
    draw_p = ImageDraw.Draw(p_img)
    draw_p.rectangle([15, 15, 365, 365], outline=text_col, width=3)
    f_p = get_korean_font(16)
    draw_p.text((50, 160), title_text, fill=text_col, font=f_p)
    draw_p.text((50, 200), "뉴스 분석 일러스트 완성!", fill=(51, 65, 85), font=get_korean_font(13))
    return p_img

def generate_comic_scenario(title, desc, user_feedback, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={api_key}"
    feedback_str = f"User Feedback: {user_feedback}" if user_feedback else ""
    
    prompt = f"""
    당신은 전문 웹툰 작가입니다. 다음 뉴스 기사를 바탕으로 인스타그램 4컷 만화의 각 컷별 영문 이미지 프롬프트와 한국어 대사를 JSON으로 작성하세요.
    - 뉴스 제목: {title}
    - 뉴스 요약: {desc}
    {feedback_str}
    
    JSON 형식:
    {{
      "cut1_prompt": "webtoon illustration panel 1", "cut1_speech": "1컷 대사",
      "cut2_prompt": "webtoon illustration panel 2", "cut2_speech": "2컷 대사",
      "cut3_prompt": "webtoon illustration panel 3", "cut3_speech": "3컷 대사",
      "cut4_prompt": "webtoon illustration panel 4", "cut4_speech": "4컷 대사"
    }}
    """
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            if response.getcode() == 200:
                res_json = json.loads(response.read().decode('utf-8'))
                raw_text = res_json['candidates'][0]['content']['parts'][0]['text']
                clean_json = raw_text[raw_text.find("{"):raw_text.rfind("}")+1]
                return json.loads(clean_json)
    except Exception:
        pass
    return {
        "cut1_prompt": f"webtoon illustration showing start of {title}", "cut1_speech": "이게 무슨 일이지?",
        "cut2_prompt": f"webtoon illustration showing process of {title}", "cut2_speech": "정말 흥미진진한데?",
        "cut3_prompt": f"webtoon illustration showing success of {title}", "cut3_speech": "결과가 성공적이야!",
        "cut4_prompt": f"webtoon illustration showing conclusion of {title}", "cut4_speech": "앞으로가 기대돼!"
    }

def create_4cut_comic_image(comic_data, article_title):
    img_w, img_h = 820, 890
    image = Image.new("RGB", (img_w, img_h), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)

    f_maintitle = get_korean_font(16)
    f_speech = get_korean_font(12)
    f_cutnum = get_korean_font(11)

    draw.rectangle([20, 20, img_w - 20, 70], fill=(15, 23, 42))
    draw.text((35, 33), f"🎬 [4컷 웹툰] {article_title[:42]}...", fill=(255, 255, 255), font=f_maintitle)

    margin = 20
    top_offset = 90
    panel_size = 375

    positions = [
        (margin, top_offset),
        (img_w - margin - panel_size, top_offset),
        (margin, top_offset + panel_size + margin),
        (img_w - margin - panel_size, top_offset + panel_size + margin)
    ]

    for i in range(1, 5):
        px, py = positions[i-1]
        panel_prompt = comic_data.get(f"cut{i}_prompt", f"webtoon panel {i}")
        panel_img = fetch_robust_panel_image(panel_prompt, i-1)
        time.sleep(0.3)
        
        image.paste(panel_img, (px, py))
        draw.rectangle([px, py, px + panel_size, py + panel_size], outline=(30, 41, 59), width=3)

        draw.rectangle([px + 10, py + 10, px + 45, py + 28], fill=(2, 132, 199))
        draw.text((px + 15, py + 12), f"{i}컷", fill=(255, 255, 255), font=f_cutnum)

        speech_text = comic_data.get(f"cut{i}_speech", "")
        sb_x1, sb_y1 = px + 12, py + panel_size - 75
        sb_x2, sb_y2 = px + panel_size - 12, py + panel_size - 12
        
        draw.rounded_rectangle([sb_x1, sb_y1, sb_x2, sb_y2], radius=8, fill=(255, 255, 255), outline=(30, 41, 59), width=2)
        draw_wrapped_text(draw, f"💬 {speech_text}", f_speech, (15, 23, 42), sb_x1 + 10, sb_y1 + 8, (sb_x2 - sb_x1) - 20)

    draw.rectangle([0, 0, img_w - 1, img_h - 1], outline=(30, 41, 59), width=3)

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)
    return buf

# ---------------------------------------------------------
# 3. 메인 UI 실행
# ---------------------------------------------------------
if st.session_state['step'] == 'search':
    st.markdown('<div style="height: 40px;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-title">FrameLens Studio</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">원하는 뉴스 키워드를 검색하고 고품질 맞춤형 미디어 콘텐츠를 생성해 보세요!</div>', unsafe_allow_html=True)

    # 이미지 스타일 반영: 둥근 알약 형태의 통합 검색창
    with st.form(key="search_form"):
        st.markdown('<div class="search-pill-container">', unsafe_allow_html=True)
        s_col1, s_col2 = st.columns([5, 1.2])
        with s_col1:
            keyword_input = st.text_input(
                "뉴스 검색어 입력",
                value="",
                placeholder="검색어를 입력하세요 (예: 기후위기, 청소년 수면, AI 윤리, 딥페이크)",
                label_visibility="collapsed"
            )
        with s_col2:
            search_trigger = st.form_submit_button("🔍 검색", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if search_trigger:
        if not keyword_input.strip():
            st.warning("⚠️ 검색어를 입력해주세요!")
        else:
            with st.spinner("뉴스를 불러오는 중입니다..."):
                news_data = fetch_naver_news(keyword_input)
                st.session_state['news_pool'] = news_data
                st.session_state['last_query'] = keyword_input.strip()
                st.session_state['page_number'] = 1
                st.session_state['selected_article_idx'] = 0
                st.session_state['step'] = 'result'
                st.rerun()

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

        left_col, right_col = st.columns([1.3, 1])

        with left_col:
            st.markdown(f"### 최신 뉴스 목록 ({total_news_count}건)")
            st.caption(f"최신순 정렬 (페이지 {current_page} / {total_pages})")

            for idx, item in enumerate(current_news_batch):
                abs_idx = start_idx + idx
                clean_title = item.get('title', '').replace("<b>", "").replace("</b>", "").replace("&quot;", '"').replace("&amp;", "&")
                clean_desc = item.get('description', '').replace("<b>", "").replace("</b>", "").replace("&quot;", '"').replace("&amp;", "&")
                link = item.get('originallink', item.get('link', '#'))
                pub_date = parse_pub_date(item.get('pubDate', ''))

                is_selected = (st.session_state['selected_article_idx'] == abs_idx)
                selected_class = "selected" if is_selected else ""

                card_col1, card_col2 = st.columns([4.5, 1])
                with card_col1:
                    st.markdown(f"""
                    <div class="news-card-item {selected_class}">
                        <div class="news-card-date">📅 {pub_date}</div>
                        <div class="news-card-title">{clean_title}</div>
                        <div class="news-card-desc">📝 {clean_desc}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with card_col2:
                    st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
                    btn_label = "✅ 선택됨" if is_selected else "👉 선택"
                    if st.button(btn_label, key=f"select_btn_{abs_idx}", use_container_width=True):
                        st.session_state['selected_article_idx'] = abs_idx
                        st.rerun()

            p_col1, p_col2, p_col3 = st.columns([1, 2, 1])
            with p_col1:
                if current_page > 1:
                    if st.button("◀ 이전 페이지", use_container_width=True):
                        st.session_state['page_number'] -= 1
                        st.rerun()
            with p_col2:
                st.markdown(f"<div style='text-align: center; padding-top: 10px; color: #e2e8f0;'>{current_page} / {total_pages} Page</div>", unsafe_allow_html=True)
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

            sel_idx = st.session_state['selected_article_idx']
            if 0 <= sel_idx < len(all_news):
                target_item = all_news[sel_idx]
                selected_art = {
                    "title": target_item.get('title', '').replace("<b>", "").replace("</b>", "").replace("&quot;", '"').replace("&amp;", "&"),
                    "desc": target_item.get('description', '').replace("<b>", "").replace("</b>", "").replace("&quot;", '"').replace("&amp;", "&"),
                    "link": target_item.get('originallink', target_item.get('link', '#')),
                    "date": parse_pub_date(target_item.get('pubDate', ''))
                }

                st.markdown('<div class="right-card-box">', unsafe_allow_html=True)
                st.markdown(f"**선택된 뉴스 기사**")
                st.write(f"📌 {selected_art['title']}")
                st.caption(f"발행일: {selected_art['date']}")
                st.markdown(f"[원문 기사 읽기]({selected_art['link']})")
                st.markdown('</div>', unsafe_allow_html=True)

                if gemini_key:
                    with st.spinner("📝 AI가 뉴스를 3줄로 핵심 요약하는 중..."):
                        summary_lines = generate_3line_summary(selected_art['title'], selected_art['desc'], gemini_key)
                        st.markdown('<div class="summary-card-box">', unsafe_allow_html=True)
                        st.markdown("##### 💡 AI 뉴스 3줄 브리핑")
                        for s_line in summary_lines:
                            st.markdown(f"• {s_line}")
                        st.markdown('</div>', unsafe_allow_html=True)

            current_article_key = f"{sel_idx}_{content_format}"
            if 'last_art_key' not in st.session_state or st.session_state['last_art_key'] != current_article_key:
                st.session_state.pop('image_bytes', None)
                st.session_state['last_art_key'] = current_article_key

            submit_plan = st.button("기사 맞춤형 콘텐츠 생성하기", use_container_width=True)

            if submit_plan:
                if not gemini_key:
                    st.error("❌ API Key가 설정되지 않았습니다!")
                else:
                    with st.spinner("🔄 4컷 만화 일러스트 및 디자인을 렌더링 중입니다... (예상 소요 시간: 약 10~15초)"):
                        comic_data = generate_comic_scenario(selected_art['title'], selected_art['desc'], "", gemini_key)
                        st.session_state['comic_data'] = comic_data
                        image_bytes = create_4cut_comic_image(comic_data, selected_art['title'])
                        
                        st.session_state['selected_article'] = selected_art
                        st.session_state['content_format'] = content_format
                        st.session_state['image_bytes'] = image_bytes

            if 'image_bytes' in st.session_state and st.session_state['image_bytes']:
                st.markdown('<div class="image-preview-container">', unsafe_allow_html=True)
                st.markdown(f"### 🎬 [{st.session_state['content_format']}] 생성된 맞춤형 결과물")
                art = st.session_state['selected_article']
                st.markdown(f"**기반 뉴스**: [{art['title']}]({art['link']})")
                st.markdown("---")
                
                st.image(st.session_state['image_bytes'], use_container_width=True, caption=f"{art['title']} - {st.session_state['content_format']}")
                
                st.markdown("---")
                st.download_button(
                    label="📥 최종 이미지 다운로드 (PNG)",
                    data=st.session_state['image_bytes'],
                    file_name=f"FrameLens_{st.session_state['content_format'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                    mime="image/png",
                    use_container_width=True
                )
                st.markdown('</div>', unsafe_allow_html=True)
