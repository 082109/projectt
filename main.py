import streamlit as st
import urllib.request
import urllib.parse
import json
from datetime import datetime
import io
import os
import time
import random
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------
# 1. 페이지 기본 설정 및 스타일링 (프리미엄 다크 네이비 테마)
# ---------------------------------------------------------
st.set_page_config(
    page_title="FrameLens - AI 미디어 포털",
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
        padding: 20px;
        margin-top: 15px;
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
# 2. 세션 상태 초기화 및 폰트 준비
# ---------------------------------------------------------
if 'step' not in st.session_state:
    st.session_state['step'] = 'search'

if 'page_number' not in st.session_state:
    st.session_state['page_number'] = 1

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

st.sidebar.header("API 설정")
client_id = st.secrets.get("NAVER_CLIENT_ID", "").strip() or st.sidebar.text_input("Naver Client ID", type="password").strip()
client_secret = st.secrets.get("NAVER_CLIENT_SECRET", "").strip() or st.sidebar.text_input("Naver Client Secret", type="password").strip()
gemini_key = st.secrets.get("GEMINI_API_KEY", "").strip() or st.sidebar.text_input("Gemini API Key", type="password").strip()

if not (client_id and client_secret and gemini_key):
    st.info("💡 사이드바에 API 키를 입력하거나 `.streamlit/secrets.toml`에 설정해주세요.")

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

def draw_wrapped_text(draw, text, font, fill, x, y, max_width, line_spacing=5):
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

# ---------------------------------------------------------
# [형식 1] 4컷 만화 생성 (웹툰 일러스트 레이아웃 100% 보장 엔진)
# ---------------------------------------------------------
def generate_comic_scenario(title, desc, user_feedback, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={api_key}"
    feedback_str = f"User Feedback to apply: {user_feedback}" if user_feedback else ""
    
    prompt = f"""
    당신은 전문 웹툰 작가입니다. 다음 뉴스 기사를 바탕으로 인스타그램 4컷 만화의 각 컷별 상황 요약과 대사를 JSON으로 작성해주세요.
    - 뉴스 제목: {title}
    - 뉴스 요약: {desc}
    {feedback_str}
    
    반드시 아래 JSON 포맷으로만 답변하세요:
    {{
      "cut1_title": "1컷 소제목", "cut1_desc": "1컷 일러스트 주제 설명", "cut1_speech": "1컷 말풍선 대사",
      "cut2_title": "2컷 소제목", "cut2_desc": "2컷 일러스트 주제 설명", "cut2_speech": "2컷 말풍선 대사",
      "cut3_title": "3컷 소제목", "cut3_desc": "3컷 일러스트 주제 설명", "cut3_speech": "3컷 말풍선 대사",
      "cut4_title": "4컷 소제목", "cut4_desc": "4컷 일러스트 주제 설명", "cut4_speech": "4컷 말풍선 대사"
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
        "cut1_title": "이슈 발생", "cut1_desc": "뉴스 상황이 시작되는 모습", "cut1_speech": "이게 무슨 일이지?",
        "cut2_title": "원인 분석", "cut2_desc": "문제점을 깊이 살펴보는 모습", "cut2_speech": "정말 심각한데?",
        "cut3_title": "해결 모색", "cut3_desc": "대책을 찾아 해결하는 모습", "cut3_speech": "이렇게 바꿔보자!",
        "cut4_title": "결론 도출", "cut4_desc": "더 나은 미래를 맞이하는 모습", "cut4_speech": "모두 안심이야!"
    }

def create_4cut_comic_image(comic_data, article_title):
    img_w, img_h = 820, 890
    image = Image.new("RGB", (img_w, img_h), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)

    f_maintitle = get_korean_font(16)
    f_cutnum = get_korean_font(12)
    f_cuttitle = get_korean_font(13)
    f_illust_desc = get_korean_font(13)
    f_speech = get_korean_font(12)

    # 상단 웹툰 타이틀 바 (고급 다크 네이비)
    draw.rectangle([20, 20, img_w - 20, 75], fill=(15, 23, 42))
    draw.text((35, 36), f"🎬 [4컷 웹툰] {article_title[:40]}...", fill=(255, 255, 255), font=f_maintitle)

    margin = 20
    top_offset = 95
    panel_w = (img_w - margin * 3) // 2
    panel_h = 360

    positions = [
        (margin, top_offset),
        (margin * 2 + panel_w, top_offset),
        (margin, top_offset + panel_h + margin),
        (margin * 2 + panel_w, top_offset + panel_h + margin)
    ]

    # 각 컷별 고유 파스텔 톤 일러스트 배경
    bg_colors = [(239, 246, 255), (254, 226, 226), (240, 253, 244), (254, 243, 199)]
    accent_colors = [(2, 132, 199), (225, 29, 72), (22, 163, 74), (217, 119, 6)]

    for i in range(1, 5):
        px, py = positions[i-1]
        
        # 1. 컷 패널 배경 및 테두리 (웹툰 스타일)
        draw.rectangle([px, py, px + panel_w, py + panel_h], fill=bg_colors[i-1], outline=(30, 41, 59), width=3)
        
        # 2. 컷 번호 및 소제목 뱃지
        draw.rectangle([px + 12, py + 12, px + 55, py + 34], fill=accent_colors[i-1])
        draw.text((px + 18, py + 14), f"{i}컷", fill=(255, 255, 255), font=f_cutnum)
        
        cut_t = comic_data.get(f"cut{i}_title", "")
        draw.text((px + 65, py + 15), cut_t[:12], fill=(15, 23, 42), font=f_cuttitle)
        draw.line([(px + 12, py + 42), (px + panel_w - 12, py + 42)], fill=(203, 213, 225), width=2)

        # 3. 일러스트 감성 텍스트 및 시각 요소 표현
        cut_desc = comic_data.get(f"cut{i}_desc", "")
        draw.rectangle([px + 20, py + 60, px + panel_w - 20, py + 200], fill=(255, 255, 255), outline=(226, 232, 240), width=1)
        draw_wrapped_text(draw, f"[일러스트 콘셉트]\n{cut_desc}", f_illust_desc, (71, 85, 105), px + 35, py + 75, panel_w - 70, line_spacing=6)

        # 4. 하단 말풍선 오버레이
        speech_text = comic_data.get(f"cut{i}_speech", "")
        sb_x1, sb_y1 = px + 15, py + panel_h - 125
        sb_x2, sb_y2 = px + panel_w - 15, py + panel_h - 15
        
        draw.rounded_rectangle([sb_x1, sb_y1, sb_x2, sb_y2], radius=10, fill=(255, 255, 255), outline=(30, 41, 59), width=2)
        draw_wrapped_text(draw, f"💬 {speech_text}", f_speech, (15, 23, 42), sb_x1 + 12, sb_y1 + 12, (sb_x2 - sb_x1) - 24)

    # 전체 외곽선
    draw.rectangle([0, 0, img_w - 1, img_h - 1], outline=(30, 41, 59), width=3)

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)
    return buf

# ---------------------------------------------------------
# [형식 2] 포스터 생성 함수
# ---------------------------------------------------------
def generate_poster_data(title, desc, user_feedback, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={api_key}"
    feedback_str = f"User Feedback: {user_feedback}" if user_feedback else ""
    
    prompt = f"""
    Analyze this news article and create public campaign poster data in JSON format:
    - News Title: {title}
    - News Summary: {desc}
    {feedback_str}

    JSON structure:
    {{
      "image_prompt": "Highly detailed English image prompt for professional campaign poster illustration",
      "korean_catchphrase": "강렬하고 직관적인 한국어 핵심 한 줄 캐치프레이즈"
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
        "image_prompt": f"Professional public campaign poster illustration about {title}",
        "korean_catchphrase": title
    }

def create_poster_image(catchphrase, desc, image_prompt):
    poster_w, poster_h = 700, 900
    poster = Image.new("RGB", (poster_w, poster_h), color=(255, 255, 255))
    draw = ImageDraw.Draw(poster)

    # 상단 포스터 비주얼 영역 (그라데이션 느낌의 세련된 배경)
    draw.rectangle([0, 0, poster_w, 500], fill=(15, 23, 42))
    f_p_title = get_korean_font(22)
    draw_wrapped_text(draw, f"📢 CAMPAIGN POSTER\n\n{catchphrase}", f_p_title, (255, 255, 255), 40, 180, poster_w - 80, line_spacing=10)

    # 하단 텍스트 영역
    draw.rectangle([0, 500, poster_w, poster_h], fill=(250, 250, 252))
    draw.line([(0, 500), (poster_w, 500)], fill=(200, 205, 215), width=3)

    f_badge = get_korean_font(13)
    f_catch = get_korean_font(22)
    f_body = get_korean_font(14)

    draw.text((40, 530), "📌 [포스터] 핵심 메시지 요약", fill=(2, 132, 199), font=f_badge)
    draw_wrapped_text(draw, f"\"{catchphrase}\"", f_catch, (15, 23, 42), 40, 570, poster_w - 80, line_spacing=8)
    draw_wrapped_text(draw, desc[:150] + "...", f_body, (100, 116, 139), 40, 720, poster_w - 80)
    draw.text((40, poster_h - 45), "FrameLens AI Media Production Studio", fill=(160, 170, 185), font=f_badge)
    draw.rectangle([0, 0, poster_w - 1, poster_h - 1], outline=(30, 41, 59), width=3)

    buf = io.BytesIO()
    poster.save(buf, format="PNG")
    buf.seek(0)
    return buf

# ---------------------------------------------------------
# [형식 3] 인포그래픽 생성 함수
# ---------------------------------------------------------
def create_infographic_image(title, desc):
    img_w, img_h = 800, 900
    image = Image.new("RGB", (img_w, img_h), color=(240, 253, 244))
    draw = ImageDraw.Draw(image)

    f_title = get_korean_font(20)
    f_sub = get_korean_font(14)
    f_chart = get_korean_font(13)

    draw.rectangle([25, 25, img_w - 25, 120], fill=(22, 101, 52))
    draw.text((45, 40), "📊 [인포그래픽 통계 분석]", fill=(134, 239, 172), font=f_sub)
    draw_wrapped_text(draw, title[:40], f_title, (255, 255, 255), 45, 68, img_w - 90)

    gx, gy = 50, 160
    draw.rectangle([gx, gy, gx + 330, gy + 320], fill=(255, 255, 255), outline=(187, 247, 208), width=2)
    draw.text((gx + 20, gy + 15), "📈 주요 지표 및 순위 비교", fill=(20, 83, 45), font=f_sub)
    
    bars = [("1위 (핵심요인)", 260, (21, 128, 61)), 
            ("2위 (영향력)", 200, (34, 197, 94)), 
            ("3위 (발생률)", 140, (74, 222, 128)), 
            ("4위 (기타)", 90, (134, 239, 172))]
    
    by = gy + 55
    for label, b_len, b_color in bars:
        draw.text((gx + 20, by), label, fill=(51, 65, 85), font=f_chart)
        draw.rectangle([gx + 130, by + 4, gx + 130 + b_len, by + 22], fill=b_color)
        by += 50

    px, py = 410, 160
    draw.rectangle([px, py, img_w - 50, py + 320], fill=(255, 255, 255), outline=(187, 247, 208), width=2)
    draw.text((px + 20, py + 15), "🎯 비율 구성비 (분야별)", fill=(20, 83, 45), font=f_sub)
    
    circle_bbox = [px + 85, py + 70, px + 235, py + 220]
    draw.pieslice(circle_bbox, start=0, end=220, fill=(21, 128, 61))
    draw.pieslice(circle_bbox, start=220, end=330, fill=(74, 222, 128))
    draw.pieslice(circle_bbox, start=330, end=360, fill=(187, 247, 208))
    draw.ellipse([px + 120, py + 105, px + 200, py + 185], fill=(255, 255, 255))
    draw.text((px + 138, py + 135), "TOTAL", fill=(22, 101, 52), font=f_sub)

    hx, hy = 50, 510
    draw.rectangle([hx, hy, img_w - 50, img_h - 50], fill=(255, 255, 255), outline=(187, 247, 208), width=2)
    draw.text((hx + 20, hy + 20), "📝 [인포그래픽 종합 인사이트 및 요약]", fill=(20, 83, 45), font=f_sub)
    draw_wrapped_text(draw, desc, f_chart, (51, 65, 85), hx + 20, hy + 60, img_w - 140, line_spacing=8)

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)
    return buf

# ---------------------------------------------------------
# 화면 1: 초기 검색 창
# ---------------------------------------------------------
if st.session_state['step'] == 'search':
    st.markdown('<div style="height: 60px;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-title">FrameLens Studio</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">뉴스 기사를 선택하고 고품질 맞춤형 미디어 콘텐츠를 생성해 보세요!</div>', unsafe_allow_html=True)

    with st.form(key="search_form"):
        st.markdown('<div class="search-container">', unsafe_allow_html=True)
        s_col1, s_col2 = st.columns([5, 1])
        with s_col1:
            keyword_input = st.text_input(
                "뉴스 검색어 입력",
                value="",
                placeholder="검색어를 입력하세요 (예: 기후위기, 청소년 수면, AI 윤리, 딥페이크)",
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
# 화면 2: 뉴스 기사 선택 및 대화형 이미지 생성 화면
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
                    "포스터",
                    "만화 (컷툰/웹툰)",
                    "인포그래픽"
                ],
                label_visibility="collapsed"
            )

            if selected_label in article_options:
                selected_art = article_options[selected_label]
                st.markdown('<div class="right-card-box">', unsafe_allow_html=True)
                st.markdown(f"**선택된 뉴스 기사**")
                st.write(f"📌 {selected_art['title']}")
                st.caption(f"발행일: {selected_art['date']}")
                st.markdown(f"[원문 기사 읽기]({selected_art['link']})")
                st.markdown('</div>', unsafe_allow_html=True)

            current_article_key = f"{selected_label}_{content_format}"
            if 'last_art_key' not in st.session_state or st.session_state['last_art_key'] != current_article_key:
                st.session_state.pop('image_bytes', None)
                st.session_state['last_art_key'] = current_article_key

            submit_plan = st.button("기사 맞춤형 콘텐츠 생성하기", use_container_width=True)

            if submit_plan:
                if not gemini_key:
                    st.error("❌ 사이드바에 API Key를 입력해 주세요!")
                elif selected_label not in article_options:
                    st.warning("⚠️ 선택된 뉴스 기사 정보를 찾을 수 없습니다.")
                else:
                    selected_article = article_options[selected_label]
                    
                    with st.spinner("🔄 고품질 만화 및 미디어 디자인을 렌더링 중입니다... (예상 소요 시간: 약 3~5초)"):
                        if content_format == "만화 (컷툰/웹툰)":
                            comic_data = generate_comic_scenario(selected_article['title'], selected_article['desc'], "", gemini_key)
                            st.session_state['comic_data'] = comic_data
                            image_bytes = create_4cut_comic_image(comic_data, selected_article['title'])
                        elif content_format == "포스터":
                            poster_data = generate_poster_data(selected_article['title'], selected_article['desc'], "", gemini_key)
                            st.session_state['poster_data'] = poster_data
                            image_bytes = create_poster_image(poster_data['korean_catchphrase'], selected_article['desc'], poster_data['image_prompt'])
                        else:
                            image_bytes = create_infographic_image(selected_article['title'], selected_article['desc'])
                        
                        st.session_state['selected_article'] = selected_article
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
                st.markdown("#### 💬 AI에게 물어보기")
                
                user_feedback = st.text_input(
                    "수정 요청 사항",
                    value="",
                    placeholder="수정하고 싶은 내용을 입력하세요...",
                    label_visibility="collapsed"
                )
                
                col_ref, col_down = st.columns([1, 1])
                with col_ref:
                    if st.button("🔄 피드백 반영하여 다시 생성하기", use_container_width=True):
                        if user_feedback.strip():
                            with st.spinner("🔄 AI가 수정 요청을 반영하여 콘텐츠를 다시 다듬고 있습니다... (예상 소요 시간: 약 3~5초)"):
                                if st.session_state['content_format'] == "만화 (컷툰/웹툰)":
                                    comic_data = generate_comic_scenario(art['title'], art['desc'], user_feedback, gemini_key)
                                    image_bytes = create_4cut_comic_image(comic_data, art['title'])
                                elif st.session_state['content_format'] == "포스터":
                                    poster_data = generate_poster_data(art['title'], art['desc'], user_feedback, gemini_key)
                                    image_bytes = create_poster_image(poster_data['korean_catchphrase'], art['desc'], poster_data['image_prompt'])
                                else:
                                    image_bytes = create_infographic_image(art['title'], art['desc'])
                                
                                st.session_state['image_bytes'] = image_bytes
                                st.rerun()
                        else:
                            st.warning("⚠️ 수정하고 싶은 내용을 입력해 주세요!")
                with col_down:
                    st.download_button(
                        label="📥 최종 이미지 다운로드 (PNG)",
                        data=st.session_state['image_bytes'],
                        file_name=f"FrameLens_{st.session_state['content_format'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                        mime="image/png",
                        use_container_width=True
                    )
                st.markdown('</div>', unsafe_allow_html=True)
