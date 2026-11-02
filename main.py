import streamlit as st
import urllib.request
import urllib.parse
import json

# ---------------------------------------------------------
# 1. 페이지 설정 및 다크 네이비 프리미엄 스타일링 (사이드바 글씨 개선)
# ---------------------------------------------------------
st.set_page_config(
    page_title="FrameLens - 뉴스 키워드 쿵쿵따 쇼",
    page_icon="🎤",
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
    
    /* 사이드바 글씨 선명하게 설정 */
    section[data-testid="stSidebar"] {
        background-color: #0f172a;
        border-right: 1px solid #1e293b;
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
        color: #f8fafc !important;
        background-color: rgba(30, 41, 59, 0.6) !important;
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

if 'kung_history' not in st.session_state:
    st.session_state['kung_history'] = [
        {"role": "ai", "text": "반가워! 지금부터 뉴스 키워드 쿵쿵따 게임을 시작할게. 첫 단어는 **'인공지능'**이야! 다음 단어를 이어줘!"}
    ]

if 'kung_current_word' not in st.session_state:
    st.session_state['kung_current_word'] = "인공지능"

gemini_key = st.secrets.get("GEMINI_API_KEY", "").strip()

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
# 3. 챗 화면 UI 구성 (쿵쿵따 전용 쇼)
# ---------------------------------------------------------
st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)
st.markdown('<div class="hero-title">🎤 뉴스 키워드 쿵쿵따 쇼</div>', unsafe_allow_html=True)
st.markdown(f'<div class="hero-subtitle">AI와 함께 시사 상식을 겨루는 릴레이 쿵쿵따 게임! | 누적 점수: <span style="color: #22d3ee; font-weight: bold; font-size: 1.2rem;">{st.session_state["total_score"]}점</span></div>', unsafe_allow_html=True)

st.sidebar.markdown("### 🎤 게임 규칙")
st.sidebar.info("1. 제시된 단어의 **마지막 글자**로 시작하는 단어를 입력하세요.\n2. 뉴스, 경제, 사회, 시사 관련 단어면 최고!\n3. 맞출 때마다 점수가 쑥쑥 올라갑니다.")

st.markdown('<div class="game-box">', unsafe_allow_html=True)
st.markdown(f"### 🚀 현재 제시어: **{st.session_state['kung_current_word']}** (구멍 글자: **'{st.session_state['kung_current_word'][-1]}'**)")
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
