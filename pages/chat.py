import streamlit as st
import urllib.request
import urllib.parse
import json
import random

# ---------------------------------------------------------
# 1. 페이지 설정 및 수사 서류 배경 스타일링
# ---------------------------------------------------------
st.set_page_config(
    page_title="FrameLens - AI 뉴스 예능 스튜디오",
    page_icon="🕹️",
    layout="wide"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@700&family=Noto+Serif+KR:wght@300;400;600;700;900&display=swap');

    /* 수사 서류와 파일들이 겹겹이 쌓인 브라운/세피아 톤의 증거 자료실 배경 적용 */
    .stApp {
        background: linear-gradient(rgba(20, 10, 5, 0.75), rgba(10, 5, 2, 0.85)), 
                    url('https://image.pollinations.ai/prompt/dark%20vintage%20detective%20case%20files%20documents%20evidence%20board%20background%20sepia%20brown%20tone?width=1920&height=1080&nologo=true');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        color: #f3f4f6;
        font-family: 'Noto Serif KR', serif !important;
    }
    
    section[data-testid="stSidebar"] {
        background-color: rgba(15, 8, 4, 0.95) !important;
        border-right: 1px solid rgba(217, 119, 6, 0.3) !important;
    }
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] div, 
    section[data-testid="stSidebar"] a {
        color: #fef3c7 !important;
        font-size: 1.05rem !important;
        font-weight: 600 !important;
    }
    [data-testid="stSidebarNav"] a {
        color: #fef3c7 !important;
        background-color: rgba(40, 20, 10, 0.8) !important;
        border-radius: 4px !important;
        margin-bottom: 6px !important;
        padding: 10px 14px !important;
    }
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: rgba(217, 119, 6, 0.3) !important;
        color: #ffffff !important;
        border: 1px solid #d97706 !important;
    }

    /* 게임 메인 타이틀 */
    .game-main-title {
        font-family: 'Cinzel', 'Noto Serif KR', serif !important;
        font-size: 3.5rem;
        font-weight: 900;
        color: #fef3c7;
        text-align: center;
        margin-top: 15px;
        margin-bottom: 5px;
        letter-spacing: 4px;
        text-shadow: 0 0 15px rgba(217, 119, 6, 0.5), 0 0 30px rgba(0, 0, 0, 0.9);
    }
    .game-main-subtitle {
        color: #d1d5db;
        font-size: 1.1rem;
        text-align: center;
        margin-bottom: 40px;
        letter-spacing: 2px;
        text-shadow: 0 2px 8px rgba(0,0,0,0.9);
    }

    /* 배경이 은은하게 다 비치는 투명 수사 카드 */
    .transparent-game-card {
        background: rgba(0, 0, 0, 0.35) !important;
        backdrop-filter: blur(4px);
        border: 1px solid rgba(253, 230, 138, 0.3);
        border-radius: 4px;
        padding: 40px 20px;
        text-align: center;
        transition: all 0.3s ease;
    }
    .transparent-game-card:hover {
        border-color: rgba(253, 230, 138, 0.9);
        box-shadow: 0 0 25px rgba(217, 119, 6, 0.3);
        background: rgba(0, 0, 0, 0.5) !important;
    }
    .card-title-text {
        font-size: 1.8rem;
        font-weight: 700;
        color: #fef3c7;
        margin-bottom: 12px;
        letter-spacing: 2px;
        text-shadow: 0 2px 10px rgba(0,0,0,0.9);
    }
    .card-desc-text {
        font-size: 0.95rem;
        color: #d1d5db;
        line-height: 1.6;
        margin-bottom: 25px;
    }

    /* 💡 [핵심] 앱 안에서 직접 기사 내용을 완벽히 읽을 수 있는 인게임 뉴스 리더 박스 */
    .in-app-news-reader {
        background: rgba(25, 12, 4, 0.95);
        border: 2px solid #d97706;
        border-radius: 6px;
        padding: 24px;
        max-width: 850px;
        margin: 0 auto 20px auto;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.85);
    }
    .news-reader-header {
        color: #f59e0b;
        font-size: 0.85rem;
        font-weight: 700;
        letter-spacing: 2px;
        margin-bottom: 8px;
        text-transform: uppercase;
    }
    .news-reader-title {
        font-family: 'Noto Serif KR', serif !important;
        font-size: 1.3rem;
        font-weight: 700;
        color: #fef3c7;
        margin-bottom: 12px;
        line-height: 1.4;
    }
    .news-reader-body {
        font-size: 1.02rem;
        color: #f3f4f6;
        line-height: 1.7;
        background: rgba(0, 0, 0, 0.4);
        padding: 15px;
        border-radius: 4px;
        border-left: 3px solid #d97706;
    }

    /* 빈티지 수사 파일 톤의 버튼 */
    .stButton > button, div[data-testid="stFormSubmitButton"] > button {
        background: rgba(30, 15, 5, 0.7) !important;
        color: #fef3c7 !important;
        border: 1px solid rgba(253, 230, 138, 0.4) !important;
        border-radius: 2px !important;
        font-weight: 600 !important;
        font-size: 1.05rem !important;
        height: 50px !important;
        transition: all 0.25s ease !important;
        letter-spacing: 1px !important;
        width: 100% !important;
    }
    .stButton > button:hover {
        background: rgba(180, 83, 9, 0.6) !important;
        border-color: #fef3c7 !important;
        box-shadow: 0 0 15px rgba(217, 119, 6, 0.5) !important;
    }

    /* 메신저 영역 */
    .messenger-top-bar {
        background: rgba(20, 10, 5, 0.85);
        border: 1px solid rgba(253, 230, 138, 0.3);
        border-bottom: none;
        border-radius: 4px 4px 0 0;
        padding: 12px 20px;
        max-width: 850px;
        margin: 0 auto;
    }
    .messenger-top-title {
        color: #fef3c7;
        font-size: 1.1rem;
        letter-spacing: 2px;
        font-weight: 700;
        text-align: center;
    }

    .messenger-room {
        background: rgba(10, 5, 2, 0.85);
        border: 1px solid rgba(253, 230, 138, 0.3);
        border-radius: 0 0 4px 4px;
        padding: 25px;
        max-width: 850px;
        margin: 0 auto 20px auto;
        height: 380px;
        overflow-y: auto;
    }

    .msg-row-left { display: flex; justify-content: flex-start; margin-bottom: 16px; }
    .msg-row-right { display: flex; justify-content: flex-end; margin-bottom: 16px; }
    
    .msg-bubble-left {
        background-color: rgba(254, 243, 199, 0.9);
        color: #1c1917;
        padding: 10px 16px;
        border-radius: 2px;
        max-width: 75%;
        font-size: 1rem;
        font-weight: 500;
    }
    .msg-bubble-right {
        background-color: rgba(254, 243, 199, 0.9);
        color: #1c1917;
        padding: 10px 16px;
        border-radius: 2px;
        max-width: 75%;
        font-size: 1rem;
        font-weight: 500;
    }
    .msg-sender { font-size: 0.8rem; color: #d1d5db; margin-bottom: 4px; }

    h1, h2, h3, h4, label { font-family: 'Noto Serif KR', serif !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. 세션 상태 초기화
# ---------------------------------------------------------
if 'total_score' not in st.session_state:
    st.session_state['total_score'] = 0

if 'active_chat_game' not in st.session_state:
    st.session_state['active_chat_game'] = None

if 'mafia_phase' not in st.session_state:
    st.session_state['mafia_phase'] = 'init'
if 'mafia_game_data' not in st.session_state:
    st.session_state['mafia_game_data'] = None
if 'messenger_chats' not in st.session_state:
    st.session_state['messenger_chats'] = []

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
    당신은 뉴스 내용 스파이 찾기 게임 진행자입니다. 다음 뉴스 기사를 바탕으로 게임을 구성하세요.
    - 뉴스 제목: {title}
    - 뉴스 요약: {desc}

    4명의 AI 플레이어(1: 김시민, 2: 박기자, 3: 최학자, 4: 이스파이)가 있습니다.
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
        "reply_text": f"좋아요! '{user_word}' 받아서, 저는 **'기후변화'**로 이어갈게요!",
        "next_word": "기후변화"
    }

# ---------------------------------------------------------
# 3. 메인 화면 UI 구성
# ---------------------------------------------------------
st.markdown('<div style="height: 15px;"></div>', unsafe_allow_html=True)
st.markdown('<div class="game-main-title">AI STUDIO ARCADE</div>', unsafe_allow_html=True)
st.markdown(f'<div class="game-main-subtitle">CASE FILE INVESTIGATION | SCORE: {st.session_state["total_score"]}</div>', unsafe_allow_html=True)

# 로비 선택 화면 (서류 배경이 비치는 투명 카드)
if st.session_state['active_chat_game'] is None:
    st.markdown('<div style="height: 30px;"></div>', unsafe_allow_html=True)
    l_col1, l_col2 = st.columns(2, gap="large")

    with l_col1:
        st.markdown("""
        <div class="transparent-game-card">
            <div class="card-title-text">뉴스 내용 스파이 찾기</div>
            <div class="card-desc-text">실시간 뉴스 증언 분석 및 가짜 뉴스 판별 추리 모드</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)
        if st.button("스파이 추리 시작", key="lobby_mafia_btn", use_container_width=True):
            st.session_state['active_chat_game'] = "mafia"
            st.session_state['mafia_phase'] = 'init'
            st.session_state['messenger_chats'] = []
            st.rerun()

    with l_col2:
        st.markdown("""
        <div class="transparent-game-card">
            <div class="card-title-text">뉴스 키워드 쿵쿵따</div>
            <div class="card-desc-text">AI 파트너와 진행하는 실시간 시사 끝말잇기 대결</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)
        if st.button("쿵쿵따 쇼 시작", key="lobby_kung_btn", use_container_width=True):
            st.session_state['active_chat_game'] = "kungkungta"
            chosen_word = random.choice(["인공지능", "경제성장", "기후변화", "우주탐사", "디지털혁신", "글로벌무역"])
            st.session_state['kung_current_word'] = chosen_word
            st.session_state['kung_history'] = [
                {"role": "ai", "text": f"반가워! 뉴스 키워드 쿵쿵따에 입장했어. 첫 제시어는 **'{chosen_word}'**이야! 이어줘!"}
            ]
            st.rerun()

else:
    top_nav1, top_nav2 = st.columns([4, 1])
    with top_nav2:
        if st.button("로비로 돌아가기", use_container_width=True):
            st.session_state['active_chat_game'] = None
            st.session_state['mafia_phase'] = 'init'
            st.rerun()

    st.markdown("---")

    # [뉴스 내용 스파이 찾기 게임 모드]
    if st.session_state['active_chat_game'] == "mafia":
        if st.session_state['mafia_phase'] == 'init':
            st.markdown('<div class="transparent-game-card" style="max-width:700px; margin:0 auto; padding:40px;">', unsafe_allow_html=True)
            st.markdown("### 뉴스 내용 스파이 찾기 가이드")
            st.markdown("""
            <div style="color: #d1d5db; text-align: left; line-height: 1.8; margin: 20px 0; font-size: 0.98rem;">
                1. 버튼을 누르면 실시간 뉴스 사건과 4명의 AI 용의자가 소집됩니다.<br>
                2. 용의자들의 증언을 메신저 대화로 확인하세요.<br>
                3. 교묘하게 왜곡된 가짜 뉴스를 퍼트린 스파이를 찾아 지목하세요.
            </div>
            """, unsafe_allow_html=True)
            st.markdown("---")
            if st.button("추리 토론 시작", use_container_width=True):
                if not gemini_key or not client_id:
                    st.error("API Key가 설정되지 않았습니다!")
                else:
                    with st.spinner("용의자 소집 중..."):
                        random_item = fetch_random_naver_news()
                        if random_item:
                            t = random_item.get('title', '').replace("<b>", "").replace("</b>", "").replace("&quot;", '"').replace("&amp;", "&")
                            d = random_item.get('description', '').replace("<b>", "").replace("</b>", "").replace("&quot;", '"').replace("&amp;", "&")
                            l = random_item.get('originallink', random_item.get('link', '#'))
                            
                            g_data = generate_mafia_game(t, d, gemini_key)
                            g_data['title'] = t
                            g_data['desc'] = d
                            g_data['link'] = l
                            st.session_state['mafia_game_data'] = g_data
                            
                            chats = []
                            for p in g_data['players']:
                                chats.append({"sender": p['name'], "text": p['statement']})
                            st.session_state['messenger_chats'] = chats
                            st.session_state['mafia_phase'] = 'debate'
                            st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        elif st.session_state['mafia_phase'] == 'debate':
            g = st.session_state['mafia_game_data']
            
            # 💡 [핵심] 앱 안에서 직접 전체 내용을 읽을 수 있는 인게임 뉴스 리더 카드
            st.markdown(f"""
            <div class="in-app-news-reader">
                <div class="news-reader-header">OFFICIAL CASE FILE | 실시간 출제 뉴스 브리핑</div>
                <div class="news-reader-title">{g['title']}</div>
                <div class="news-reader-body">{g['desc']}</div>
            </div>
            """, unsafe_allow_html=True)

            # 메신저 상단 바
            st.markdown("""
            <div class="messenger-top-bar">
                <div class="messenger-top-title">CASE FILE ROOM</div>
            </div>
            """, unsafe_allow_html=True)

            # 메신저 채팅방 본체
            st.markdown('<div class="messenger-room">', unsafe_allow_html=True)
            for chat in st.session_state['messenger_chats']:
                if chat['sender'] == "태희 (나)":
                    st.markdown(f"""
                    <div class="msg-row-right">
                        <div>
                            <div class="msg-sender" style="text-align:right;">{chat['sender']}</div>
                            <div class="msg-bubble-right">{chat['text']}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="msg-row-left">
                        <div>
                            <div class="msg-sender">{chat['sender']}</div>
                            <div class="msg-bubble-left">{chat['text']}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            with st.form(key="msg_form", clear_on_submit=True):
                user_msg = st.text_input("메시지 입력", placeholder="예: 3번 진술이 이상합니다.")
                msg_submit = st.form_submit_button("전송", use_container_width=True)

            if msg_submit and user_msg.strip():
                st.session_state['messenger_chats'].append({"sender": "태희 (나)", "text": user_msg.strip()})
                st.rerun()

            st.markdown("---")
            st.markdown("### 스파이 지목 투표")
            player_names = [f"{idx+1}번: {p['name']}" for idx, p in enumerate(g['players'])]
            selected_player = st.selectbox("처형할 용의자 선택", options=player_names)
            
            if st.button("투표 확정", use_container_width=True):
                sel_idx = player_names.index(selected_player)
                st.session_state['selected_vote'] = sel_idx
                st.session_state['mafia_phase'] = 'result'
                st.rerun()

        elif st.session_state['mafia_phase'] == 'result':
            g = st.session_state['mafia_game_data']
            voted_idx = st.session_state['selected_vote']
            voted_player = g['players'][voted_idx]
            spy_player = g['players'][g['spy_index']]
            
            st.markdown('<div class="transparent-game-card" style="max-width:750px; margin:0 auto; padding:30px;">', unsafe_allow_html=True)
            st.markdown(f"### 심판 결과")
            st.markdown(f"**{voted_player['name']}의 최후 변론**: \"{g['defense']}\"")
            st.markdown("---")
            
            if voted_idx == g['spy_index']:
                st.success(f"[시민 승리] {voted_player['name']}(은)는 진짜 스파이였습니다! (+20점)")
                st.session_state['total_score'] += 20
            else:
                st.error(f"[스파이 승리] 시민({voted_player['name']})이 처형되었습니다! 진짜 스파이는 {spy_player['name']}입니다!")

            st.info(f"팩트체크: {g['fact_check']}")
            
            if st.button("다음 사건 진행", use_container_width=True):
                st.session_state['mafia_phase'] = 'init'
                st.session_state['messenger_chats'] = []
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # [뉴스 키워드 쿵쿵따 모드]
    elif st.session_state['active_chat_game'] == "kungkungta":
        st.markdown(f"### 뉴스 키워드 쿵쿵따 (현재 제시어: **{st.session_state['kung_current_word']}** / 끝 글자: **'{st.session_state['kung_current_word'][-1]}'**)")
        st.markdown("---")

        st.markdown("""
        <div class="messenger-top-bar">
            <div class="messenger-top-title">QUIZ ROOM</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="messenger-room" style="height:400px;">', unsafe_allow_html=True)
        for chat in st.session_state['kung_history']:
            if chat['role'] == 'ai':
                st.markdown(f"""
                <div class="msg-row-left">
                    <div>
                        <div class="msg-sender">AI SHOW HOST</div>
                        <div class="msg-bubble-left">{chat['text']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="msg-row-right">
                    <div>
                        <div class="msg-sender" style="text-align:right;">태희 (나)</div>
                        <div class="msg-bubble-right">{chat['text']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        with st.form(key="kung_form", clear_on_submit=True):
            user_word = st.text_input("단어 입력", placeholder=f"'{st.session_state['kung_current_word'][-1]}'로 시작하는 단어")
            kung_submit = st.form_submit_button("단어 전송", use_container_width=True)

        if kung_submit:
            if not user_word.strip():
                st.warning("단어를 입력해 주세요!")
            elif not gemini_key:
                st.error("API Key가 설정되지 않았습니다!")
            else:
                last_w = st.session_state['kung_current_word']
                res = get_kung_reply(user_word.strip(), last_w, gemini_key)
                
                st.session_state['kung_history'].append({"role": "user", "text": user_word.strip()})
                st.session_state['kung_history'].append({"role": "ai", "text": res['reply_text']})
                
                if res['status'] == 'success':
                    st.session_state['total_score'] += 10
                    st.session_state['kung_current_word'] = res['next_word']
                st.rerun()
