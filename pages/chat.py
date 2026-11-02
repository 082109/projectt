import streamlit as st
import urllib.request
import urllib.parse
import json
import random

# ---------------------------------------------------------
# 1. 페이지 설정 및 게임 전용 네온 아케이드 스타일링
# ---------------------------------------------------------
st.set_page_config(
    page_title="FrameLens - AI 뉴스 예능 스튜디오",
    page_icon="🕹️",
    layout="wide"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Black+Han+Sans&family=Noto+Serif+KR:wght@300;400;600;700;900&display=swap');

    .stApp {
        background: radial-gradient(circle at center, #0f172a 0%, #050811 100%);
        color: #f3f4f6;
        font-family: 'Noto Serif KR', serif !important;
    }
    
    section[data-testid="stSidebar"] {
        background-color: #0b1120 !important;
        border-right: 1px solid #1e293b !important;
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
        background-color: rgba(30, 41, 59, 0.8) !important;
        border-radius: 10px !important;
        margin-bottom: 6px !important;
        padding: 10px 14px !important;
    }
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%) !important;
        color: #ffffff !important;
        border: 1px solid #a78bfa !important;
    }

    /* 게임 로비 타이틀 (오락실 아케이드 네온 폰트 느낌) */
    .arcade-title {
        font-family: 'Black Han Sans', sans-serif !important;
        font-size: 3.8rem;
        font-weight: 400;
        color: #ffffff;
        text-align: center;
        margin-top: 20px;
        margin-bottom: 10px;
        text-shadow: 0 0 20px rgba(124, 58, 237, 0.8), 0 0 40px rgba(79, 70, 229, 0.6);
        letter-spacing: 2px;
    }
    .arcade-subtitle {
        color: #a78bfa;
        font-size: 1.25rem;
        text-align: center;
        margin-bottom: 40px;
        font-weight: 600;
        text-shadow: 0 0 10px rgba(167, 139, 250, 0.4);
    }

    /* 리얼 게임 스타일 대형 카드 (마피아42 / 쿵쿵따 로비 카드) */
    .game-lobby-card {
        background: linear-gradient(145deg, #111827 0%, #0b1120 100%);
        border: 3px solid #374151;
        border-radius: 28px;
        padding: 45px 30px;
        text-align: center;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.7), inset 0 0 20px rgba(255, 255, 255, 0.03);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        height: 100%;
        position: relative;
        overflow: hidden;
    }
    .game-lobby-card:hover {
        border-color: #a78bfa;
        box-shadow: 0 0 40px rgba(124, 58, 237, 0.5), inset 0 0 30px rgba(124, 58, 237, 0.2);
        transform: translateY(-8px);
    }
    .card-icon-box {
        font-size: 4.5rem;
        margin-bottom: 20px;
        text-shadow: 0 0 20px rgba(255, 255, 255, 0.2);
    }
    .card-title {
        font-family: 'Black Han Sans', sans-serif !important;
        font-size: 2rem;
        color: #ffffff;
        margin-bottom: 15px;
        letter-spacing: 1px;
    }
    .card-desc {
        color: #9ca3af;
        font-size: 1.05rem;
        line-height: 1.7;
        margin-bottom: 30px;
    }

    /* 게임 내부 컨테이너 박스 */
    .game-play-box {
        background: linear-gradient(145deg, #111827 0%, #0b1120 100%);
        border: 2.5px solid #4f46e5;
        border-radius: 24px;
        padding: 35px;
        margin: 0 auto 20px auto;
        max-width: 950px;
        box-shadow: 0 0 40px rgba(79, 70, 229, 0.3);
    }

    .chat-bubble-ai {
        background-color: #1f2937;
        border-left: 5px solid #a78bfa;
        padding: 16px 20px;
        border-radius: 12px;
        margin-bottom: 14px;
        font-size: 1.1rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }

    /* 네온 입체 버튼 스타일 */
    .stButton > button, div[data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%);
        color: #ffffff;
        border: 2px solid #a78bfa;
        border-radius: 16px;
        font-weight: 800;
        font-size: 1.15rem;
        height: 55px;
        box-shadow: 0 6px 20px rgba(124, 58, 237, 0.5);
        transition: all 0.2s ease;
        font-family: 'Black Han Sans', sans-serif !important;
        letter-spacing: 1px;
        width: 100%;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #8b5cf6 > 0%, #6366f1 100%);
        box-shadow: 0 0 25px rgba(167, 139, 250, 0.8);
        transform: translateY(-2px);
        border-color: #ffffff;
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

if 'active_chat_game' not in st.session_state:
    st.session_state['active_chat_game'] = None # 로비 화면 노출

if 'mafia_phase' not in st.session_state:
    st.session_state['mafia_phase'] = 'init'
if 'mafia_game_data' not in st.session_state:
    st.session_state['mafia_game_data'] = None

if 'kung_history' not in st.session_state:
    st.session_state['kung_history'] = []
if 'kung_current_word' not in st.session_state:
    st.session_state['kung_current_word'] = None

client_id = st.secrets.get("NAVER_CLIENT_ID", "").strip()
client_secret = st.secrets.get("NAVER_CLIENT_SECRET", "").strip()
gemini_key = st.secrets.get("GEMINI_API_KEY", "").strip()

def fetch_random_naver_news():
    random_keywords = ["사회", "경제", "기술", "인공지능", "환경", "문화", "과학", "디지털", "스타트업", "글로벌"]
    chosen_query = random.choice(random_keywords)
    encText = urllib.parse.quote(chosen_query)
    url = f"https://naverapihub.apigw.ntruss.com/search/v1/news?query={encText}&display=20&sort=date"
    
    req = urllib.request.Request(url)
    req.add_header("X-NCP-APIGW-API-KEY-ID", client_id)
    req.add_header("X-NCP-APIGW-API-KEY", client_secret)
    
    try:
        with urllib.request.urlopen(req) as response:
            if response.getcode() == 200:
                data = json.loads(response.read().decode('utf-8'))
                items = data.get('items', [])
                if items:
                    return random.choice(items)
        return None
    except Exception:
        return None

def generate_mafia_game(title, desc, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={api_key}"
    prompt = f"""
    당신은 마피아42 스타일의 뉴스 추리 게임 진행자입니다. 다음 뉴스 기사를 바탕으로 게임을 구성하세요.
    - 뉴스 제목: {title}
    - 뉴스 요약: {desc}

    4명의 플레이어(1: 김시민, 2: 박기자, 3: 최학자, 4: 이스파이)가 있습니다.
    이 중 한 명은 스파이라서 뉴스 내용을 거짓으로 주장하거나 왜곡된 발언을 합니다.

    JSON 형식으로 아래처럼 답하세요:
    {{
      "players": [
        {{"name": "김시민", "role": "시민", "statement": "진짜 기사 관련 1번 증언"}},
        {{"name": "박기자", "role": "시민", "statement": "진짜 기사 관련 2번 증언"}},
        {{"name": "최학자", "role": "시민", "statement": "진짜 기사 관련 3번 증언"}},
        {{"name": "이스파이", "role": "스파이", "statement": "교묘하게 왜곡된 가짜 뉴스 증언"}}
      ],
      "spy_index": 3,
      "defense": "스파이가 최후의 변론으로 하는 구차한 변명",
      "fact_check": "진짜 뉴스 팩트체크 해설"
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
                data = json.loads(clean_json)
                random.shuffle(data['players'])
                for idx, p in enumerate(data['players']):
                    if p['role'] == '스파이':
                        data['spy_index'] = idx
                return data
    except Exception:
        pass
    return {
        "players": [
            {"name": "김시민", "role": "시민", "statement": f"이번 기사는 {title[:15]} 관련 사건이 확실합니다."},
            {"name": "박기자", "role": "시민", "statement": f"보도된 바에 따르면 {desc[:25]} 내용입니다."},
            {"name": "최학자", "role": "시민", "statement": "전문가 분석 결과도 기사 본문과 동일합니다."},
            {"name": "이스파이", "role": "스파이", "statement": "사실 이번 기사는 전부 거짓이며 외계인이 개입했습니다!"}
        ],
        "spy_index": 3,
        "defense": "저는 진짜 시민입니다! 저를 처형하면 스파이에게 이기게 됩니다!",
        "fact_check": "4번 증언은 완전히 왜곡된 가짜 뉴스입니다."
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
# 3. 화면 UI 및 아케이드 스타일 로비 구성
# ---------------------------------------------------------
st.markdown('<div style="height: 15px;"></div>', unsafe_allow_html=True)
st.markdown('<div class="arcade-title">🕹️ AI 예능 스튜디오 아케이드</div>', unsafe_allow_html=True)
st.markdown(f'<div class="arcade-subtitle">실시간 서바이벌 추리 & 퀴즈 쇼 | 누적 서바이벌 점수: <span style="color: #38bdf8; font-size: 1.3rem;">{st.session_state["total_score"]}점</span></div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# [로비 화면] 게임 미선택 시: 고품질 입체 아케이드 카드 2개 배치
# ---------------------------------------------------------
if st.session_state['active_chat_game'] is None:
    st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)
    l_col1, l_col2 = st.columns(2, gap="large")

    with l_col1:
        st.markdown("""
        <div class="game-lobby-card">
            <div class="card-icon-box">🕵️‍♂️</div>
            <div class="card-title">마피아42: 스파이 잡기</div>
            <div class="card-desc">
                실시간 랜덤 뉴스 속에서 가짜 정보를 유포하는<br>
                잠입 스파이(마피아)를 찾아내어 처형하라!<br>
                치열한 증언 토론과 투표 서바이벌 게임.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div style="height: 15px;"></div>', unsafe_allow_html=True)
        if st.button("🔴 마피아42 방 입장하기", key="lobby_mafia_btn", use_container_width=True):
            st.session_state['active_chat_game'] = "mafia"
            st.rerun()

    with l_col2:
        st.markdown("""
        <div class="game-lobby-card">
            <div class="card-icon-box">🎤</div>
            <div class="card-title">뉴스 키워드 쿵쿵따 쇼</div>
            <div class="card-desc">
                시사, 경제, IT 대격돌 릴레이 끝말잇기 퀴즈 쇼!<br>
                매 라운드 무작위로 튀어나오는 첫 제시어 속에서<br>
                AI 쇼호스트와 맞서는 스피드 두뇌 대결.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div style="height: 15px;"></div>', unsafe_allow_html=True)
        if st.button("🔵 쿵쿵따 쇼 방 입장하기", key="lobby_kung_btn", use_container_width=True):
            st.session_state['active_chat_game'] = "kungkungta"
            random_first_words = ["인공지능", "경제성장", "기후변화", "우주탐사", "디지털혁신", "글로벌무역", "스마트폰"]
            chosen_word = random.choice(random_first_words)
            st.session_state['kung_current_word'] = chosen_word
            st.session_state['kung_history'] = [
                {"role": "ai", "text": f"반가워! 쿵쿵따 쇼 스튜디오에 입장한 걸 환영해. 이번 판의 랜덤 첫 제시어는 **'{chosen_word}'**이야! 자, 다음 단어를 이어줘!"}
            ]
            st.rerun()

# ---------------------------------------------------------
# [게임 플레이 화면]
# ---------------------------------------------------------
else:
    top_nav1, top_nav2 = st.columns([4, 1])
    with top_nav2:
        if st.button("🏠 로비로 돌아가기", use_container_width=True):
            st.session_state['active_chat_game'] = None
            st.session_state['mafia_phase'] = 'init'
            st.session_state['mafia_game_data'] = None
            st.rerun()

    st.markdown("---")

    # ---------------------------------------------------------
    # [게임 1] 마피아42 스타일 스파이 잡기 게임
    # ---------------------------------------------------------
    if st.session_state['active_chat_game'] == "mafia":
        st.markdown('<div class="game-play-box">', unsafe_allow_html=True)
        st.markdown("### 🕵️‍♂️ [마피아42 서바이벌] 실시간 뉴스 스파이 추리")
        st.markdown("시민들 사이에 숨어 거짓 증언을 내뱉는 **스파이**를 투표로 검거하세요!")
        st.markdown("---")

        if st.session_state['mafia_phase'] == 'init':
            if st.button("⚡ 긴급 뉴스 사건 및 용의자 소집하기", use_container_width=True):
                if not gemini_key or not client_id:
                    st.error("❌ API Key가 설정되지 않았습니다!")
                else:
                    with st.spinner("🚨 긴급 속보 수신 중... 용의자들의 증언 조작을 분석하고 있습니다..."):
                        random_item = fetch_random_naver_news()
                        if random_item:
                            t = random_item.get('title', '').replace("<b>", "").replace("</b>", "").replace("&quot;", '"').replace("&amp;", "&")
                            d = random_item.get('description', '').replace("<b>", "").replace("</b>", "").replace("&quot;", '"').replace("&amp;", "&")
                            
                            g_data = generate_mafia_game(t, d, gemini_key)
                            g_data['title'] = t
                            st.session_state['mafia_game_data'] = g_data
                            st.session_state['mafia_phase'] = 'debate'
                            st.rerun()
                        else:
                            st.warning("뉴스 데이터를 불러오지 못했습니다. 다시 시도해 주세요!")

        elif st.session_state['mafia_phase'] == 'debate':
            g = st.session_state['mafia_game_data']
            st.markdown(f"#### 📌 사건 뉴스: {g['title']}")
            st.markdown("---")
            st.markdown("#### 🗣️ 용의자들의 실시간 법정 증언")
            
            for idx, p in enumerate(g['players']):
                st.markdown(f"""
                <div class="chat-bubble-ai">
                    <strong>👤 {p['name']}</strong>: "{p['statement']}"
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("### 🗳️ [최후 투표] 가짜 증언으로 선동하는 스파이를 지목하세요!")
            
            player_names = [f"{idx+1}번: {p['name']}" for idx, p in enumerate(g['players'])]
            selected_player = st.radio("처형할 용의자 선택", options=player_names)
            
            if st.button("⚖️ 스파이 처형 투표 확정", use_container_width=True):
                sel_idx = player_names.index(selected_player)
                st.session_state['selected_vote'] = sel_idx
                st.session_state['mafia_phase'] = 'result'
                st.rerun()

        elif st.session_state['mafia_phase'] == 'result':
            g = st.session_state['mafia_game_data']
            voted_idx = st.session_state['selected_vote']
            voted_player = g['players'][voted_idx]
            spy_player = g['players'][g['spy_index']]
            
            st.markdown(f"### ⚖️ [심판의 시간 - 최후 변론]")
            st.markdown(f"💥 **{voted_player['name']}의 최후 변론**: \"{g['defense']}\"")
            st.markdown("---")
            
            if voted_idx == g['spy_index']:
                st.balloons()
                st.success(f"🎉 [시민 진영 승리] {voted_player['name']}(은)는 진짜 AI 스파이였습니다! (+20점)")
                st.session_state['total_score'] += 20
            else:
                st.error(f"💀 [스파이 진영 승리] 억울한 시민({voted_player['name']})이 처형당했습니다! 진짜 스파이는 **{spy_player['name']}**이었습니다!")

            st.info(f"💡 **진짜 뉴스 팩트체크**: {g['fact_check']}")
            
            if st.button("🔄 다음 긴급 사건 수사하러 가기", use_container_width=True):
                st.session_state['mafia_phase'] = 'init'
                st.session_state['mafia_game_data'] = None
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    # ---------------------------------------------------------
    # [게임 2] 뉴스 키워드 쿵쿵따 쇼
    # ---------------------------------------------------------
    elif st.session_state['active_chat_game'] == "kungkungta":
        st.markdown('<div class="game-play-box">', unsafe_allow_html=True)
        st.markdown(f"### 🎤 쿵쿵따 쇼 대결 중! (현재 제시어: **{st.session_state['kung_current_word']}**) 구멍 글자: **'{st.session_state['kung_current_word'][-1]}'**")
        st.markdown("---")

        for chat in st.session_state['kung_history']:
            if chat['role'] == 'ai':
                st.markdown(f"🤖 **쇼호스트 AI**: {chat['text']}")
            else:
                st.markdown(f"👤 **플레이어**: {chat['text']}")

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
