import streamlit as st
import urllib.request
import urllib.parse
import json
import random

# ---------------------------------------------------------
# 1. 페이지 설정 및 다크 네이비 프리미엄 스타일링 (사이드바 배경 밝게 변경)
# ---------------------------------------------------------
st.set_page_config(
    page_title="FrameLens - AI 뉴스 예능 & 퀴즈 쇼",
    page_icon="🎮",
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
    
    /* 사이드바 배경을 밝은 톤(#172033)으로 변경하여 가독성 극대화 */
    section[data-testid="stSidebar"] {
        background-color: #172033 !important;
        border-right: 1px solid #334155 !important;
        font-family: 'Noto Serif KR', serif !important;
    }
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] div, 
    section[data-testid="stSidebar"] a {
        color: #ffffff !important;
        font-size: 1.05rem !important;
        font-weight: 600 !important;
    }
    [data-testid="stSidebarNav"] a {
        color: #ffffff !important;
        background-color: rgba(30, 41, 59, 0.9) !important;
        border-radius: 10px !important;
        margin-bottom: 6px !important;
        padding: 10px 14px !important;
    }
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
        color: #ffffff !important;
        border: 1px solid #38bdf8 !important;
    }

    .hero-title {
        font-family: 'Noto Serif KR', serif !important;
        font-size: 3.2rem;
        font-weight: 900;
        color: #ffffff;
        text-align: center;
        margin-top: 20px;
        margin-bottom: 8px;
        letter-spacing: -1.5px;
    }
    .hero-subtitle {
        font-family: 'Noto Serif KR', serif !important;
        color: #94a3b8;
        font-size: 1.1rem;
        text-align: center;
        margin-bottom: 30px;
        font-weight: 300;
    }

    .game-box {
        background: #0d1527;
        border: 2px solid #22d3ee;
        border-radius: 20px;
        padding: 25px;
        margin: 0 auto 20px auto;
        max-width: 850px;
        box-shadow: 0 0 30px rgba(34, 211, 238, 0.2);
    }

    .search-box {
        background: #0d1527;
        border: 2px solid #38bdf8;
        border-radius: 20px;
        padding: 15px 25px;
        max-width: 850px;
        margin: 0 auto 25px auto;
        box-shadow: 0 0 25px rgba(56, 189, 248, 0.15);
    }

    .stButton > button, div[data-testid="stFormSubmitButton"] > button {
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
        width: 100%;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%);
        box-shadow: 0 6px 18px rgba(56, 189, 248, 0.45);
        transform: translateY(-1px);
    }

    h1, h2, h3, h4, label {
        font-family: 'Noto Serif KR', serif !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. 세션 상태 초기화
# ---------------------------------------------------------
if 'total_score' not in st.session_state:
    st.session_state['total_score'] = 0

if 'spy_game_data' not in st.session_state:
    st.session_state['spy_game_data'] = None
if 'spy_submitted' not in st.session_state:
    st.session_state['spy_submitted'] = False

if 'kung_history' not in st.session_state:
    st.session_state['kung_history'] = [
        {"role": "ai", "text": "반가워! 지금부터 뉴스 키워드 쿵쿵따 게임을 시작할게. 첫 단어는 **'인공지능'**이야! 다음 단어를 이어줘!"}
    ]
if 'kung_current_word' not in st.session_state:
    st.session_state['kung_current_word'] = "인공지능"

client_id = st.secrets.get("NAVER_CLIENT_ID", "").strip()
client_secret = st.secrets.get("NAVER_CLIENT_SECRET", "").strip()
gemini_key = st.secrets.get("GEMINI_API_KEY", "").strip()

def fetch_naver_news(query, display_count=5):
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

def generate_spy_game(title, desc, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={api_key}"
    prompt = f"""
    당신은 뉴스 팩트체크 게임 출제자입니다. 다음 진짜 뉴스 기사를 바탕으로 4개의 요약 문장을 만들어주세요.
    단, 4개 중 3개는 진짜 기사 내용(Fact)이고, 1개는 교묘하게 수치나 핵심 사실을 약간 왜곡한 '가짜 문장(Spy Fake)'이어야 합니다.
    - 뉴스 제목: {title}
    - 뉴스 요약: {desc}
    
    반드시 아래 JSON 포맷으로만 답변하세요:
    {{
      "statements": [
        "1번 문장 내용",
        "2번 문장 내용",
        "3번 문장 내용",
        "4번 문장 내용"
      ],
      "fake_index": 가짜 문장의 인덱스 번호 (0, 1, 2, 3 중 하나),
      "explanation": "왜 이 문장이 가짜(스파이)인지와 실제 사실에 대한 유쾌한 팩트체크 해설"
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
        "statements": [
            f"{title} 관련 첫 번째 핵심 보도 내용입니다.",
            f"이 사건은 최근 큰 이슈가 되어 사회적 관심이 높습니다.",
            f"전문가들은 이 사건으로 인해 내일부터 외계로 이주한다고 밝혔습니다.",
            f"{desc[:40]}... 의 내용이 기사에 포함되어 있습니다."
        ],
        "fake_index": 2,
        "explanation": "3번 문장은 AI 스파이가 조작한 가짜 정보입니다!"
    }

def get_kung_reply(user_word, last_word, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={api_key}"
    prompt = f"""
    당신은 뉴스 키워드 쿵쿵따 게임 AI 파트너입니다.
    마지막 단어: '{last_word}'
    사용자가 제시한 단어: '{user_word}'
    
    규칙:
    1. 사용자가 마지막 단어의 끝글자로 시작하는 올바른 단어를 말했다면, 칭찬하고 그 단어의 끝글자로 시작하는 새로운 뉴스/시사 관련 단어를 이어주세요.
    2. 글자가 틀렸거나 시사/단어 규칙에 맞지 않으면 유쾌하게 지적하고 다시 기회를 주세요.
    
    반드시 JSON 형식으로만 답변하세요:
    {{
      "status": "success" 또는 "fail",
      "reply_text": "AI의 대화 및 반응 메시지",
      "next_word": "성공 시 AI가 이어갈 새로운 단어 (실패 시 기존 단어 유지)"
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
        "status": "success",
        "reply_text": f"좋어요! '{user_word}' 받아서, 저는 **'기후변화'**로 이어갈게요!",
        "next_word": "기후변화"
    }

# ---------------------------------------------------------
# 3. 챗 화면 UI 구성 (사이드바 모드 선택)
# ---------------------------------------------------------
st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)
st.markdown('<div class="hero-title">🎮 AI 뉴스 예능 & 스파이 퀴즈 쇼</div>', unsafe_allow_html=True)
st.markdown(f'<div class="hero-subtitle">미디어 탐정 능력을 시험하고 AI와 쿵쿵따 게임을 즐겨보세요! | 총 누적 점수: <span style="color: #22d3ee; font-weight: bold; font-size: 1.2rem;">{st.session_state["total_score"]}점</span></div>', unsafe_allow_html=True)

game_mode = st.sidebar.radio("🎯 예능 퀴즈 모드 선택", ["🕵️‍♂️ 가짜 뉴스 스파이 잡기", "🎤 뉴스 키워드 쿵쿵따 쇼"])
st.sidebar.markdown("---")
st.sidebar.info("💡 뉴스를 바탕으로 AI와 두뇌 게임을 즐겨보세요!")

# ---------------------------------------------------------
# [모드 1] 가짜 뉴스 스파이 잡기 게임
# ---------------------------------------------------------
if game_mode == "🕵️‍♂️ 가짜 뉴스 스파이 잡기":
    st.markdown('<div class="search-box">', unsafe_allow_html=True)
    search_keyword = st.text_input("스파이를 추적할 뉴스 주제 입력", placeholder="예: 딥페이크, 인공지능, 우주 탐사, 경제")
    if st.button("🔍 뉴스 스파이 사건 수사 시작", use_container_width=True):
        if not gemini_key or not client_id:
            st.error("❌ API Key가 설정되지 않았습니다!")
        elif not search_keyword.strip():
            st.warning("⚠️ 검색어를 입력해 주세요!")
        else:
            with st.spinner("🕵️‍♂️ AI가 진짜 기사 사이에 가짜 정보(스파이)를 몰래 섞는 중입니다..."):
                news_items = fetch_naver_news(search_keyword, display_count=5)
                if news_items:
                    target_news = random.choice(news_items)
                    t = target_news.get('title', '').replace("<b>", "").replace("</b>", "").replace("&quot;", '"')
                    d = target_news.get('description', '').replace("<b>", "").replace("</b>", "").replace("&quot;", '"')
                    
                    g_data = generate_spy_game(t, d, gemini_key)
                    g_data['news_title'] = t
                    st.session_state['spy_game_data'] = g_data
                    st.session_state['spy_submitted'] = False
                    st.rerun()
                else:
                    st.warning("관련 뉴스를 찾지 못했습니다.")
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state['spy_game_data']:
        g = st.session_state['spy_game_data']
        st.markdown('<div class="game-box">', unsafe_allow_html=True)
        st.markdown(f"#### 📌 사건 기사: {g['news_title']}")
        st.markdown("---")
        st.markdown("### ❓ 다음 4개 요약 문장 중 '거짓(가짜 뉴스)'인 스파이 문장은 몇 번일까요?")
        
        options = [f"{idx+1}번: {stmt}" for idx, stmt in enumerate(g['statements'])]
        user_choice = st.radio("스파이 지목하기", options=options, key="spy_radio")
        
        if not st.session_state['spy_submitted']:
            if st.button("🚨 스파이 검거 제출", use_container_width=True):
                selected_idx = options.index(user_choice)
                if selected_idx == g['fake_index']:
                    st.session_state['total_score'] += 15
                    st.session_state['spy_submitted'] = 'correct'
                else:
                    st.session_state['spy_submitted'] = 'wrong'
                st.rerun()
        else:
            if st.session_state['spy_submitted'] == 'correct':
                st.success("🎉 완벽한 검거! AI 스파이(가짜 문장)를 정확히 찾아냈습니다! (+15점)")
            else:
                st.error(f"❌ 검거 실패! 진짜 스파이는 {g['fake_index']+1}번 문장이었습니다!")
            
            st.info(f"💡 **팩트체크 해설**: {g['explanation']}")
            
            if st.button("🔄 다음 뉴스 사건 수사하기", use_container_width=True):
                st.session_state['spy_game_data'] = None
                st.session_state['spy_submitted'] = False
                st.rerun()
                
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# [모드 2] 뉴스 키워드 쿵쿵따 쇼
# ---------------------------------------------------------
elif game_mode == "🎤 뉴스 키워드 쿵쿵따 쇼":
    st.markdown('<div class="game-box">', unsafe_allow_html=True)
    st.markdown(f"### 🎤 쿵쿵따 대결 진행 중! (현재 제시어: **{st.session_state['kung_current_word']}**) 구멍 글자: **'{st.session_state['kung_current_word'][-1]}'**")
    st.markdown("---")

    for chat in st.session_state['kung_history']:
        if chat['role'] == 'ai':
            st.markdown(f"🤖 **AI 쇼호스트**: {chat['text']}")
        else:
            st.markdown(f"👤 **태희 탐정**: {chat['text']}")

    st.markdown("---")
    with st.form(key="kung_form", clear_on_submit=True):
        user_word = st.text_input("끝말잇기 단어 입력", placeholder=f"'{st.session_state['kung_current_word'][-1]}'로 시작하는 단어를 입력하세요!")
        kung_submit = st.form_submit_button("단어 던지기 🚀", use_container_width=True)

    if kung_submit:
        if not user_word.strip():
            st.warning("단어를 입력해 주세요!")
        elif not gemini_key:
            st.error("❌ API Key가 설정되지 않았습니다!")
        else:
            last_w = st.session_state['kung_current_word']
            res = get_kung_reply(user_word.strip(), last_w, gemini_key)
            
            st.session_state['kung_history'].append({"role": "user", "text": user_word.strip()})
            st.session_state['kung_history'].append({"role": "ai", "text": res['reply_text']})
            
            if res['status'] == 'success':
                st.session_state['total_score'] += 10
                st.session_state['kung_current_word'] = res['next_word']
            st.rerun()
            
    st.markdown('</div>', unsafe_allow_html=True)
