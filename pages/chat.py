import streamlit as st
import urllib.request
import urllib.parse
import json
import random

# ---------------------------------------------------------
# 1. 페이지 설정 및 추리 탐정 스타일링
# ---------------------------------------------------------
st.set_page_config(
    page_title="FrameLens - 미스터리 수사국",
    page_icon="🔍",
    layout="wide"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Myeongjo:wght@400;700;800&family=Noto+Sans+KR:wght@300;400;700&display=swap');

    .stApp {
        background-color: #0b0f19;
        color: #e2e8f0;
        font-family: 'Nanum Myeongjo', serif !important;
    }
    
    section[data-testid="stSidebar"] {
        background-color: #070a12 !important;
        border-right: 1px solid #1e293b !important;
    }
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] div, 
    section[data-testid="stSidebar"] a {
        color: #cbd5e1 !important;
        font-size: 1.05rem !important;
        font-weight: 600 !important;
    }
    [data-testid="stSidebarNav"] a {
        color: #e2e8f0 !important;
        background-color: rgba(30, 41, 59, 0.6) !important;
        border-radius: 8px !important;
        margin-bottom: 6px !important;
        padding: 10px 14px !important;
    }
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: #1e3a8a !important;
        color: #ffffff !important;
        border: 1px solid #3b82f6 !important;
    }

    /* 수사국 타이틀 */
    .investigation-title {
        font-family: 'Nanum Myeongjo', serif !important;
        font-size: 3rem;
        font-weight: 800;
        color: #f8fafc;
        text-align: center;
        margin-top: 20px;
        margin-bottom: 5px;
        letter-spacing: -1px;
    }
    .investigation-subtitle {
        color: #94a3b8;
        font-size: 1.1rem;
        text-align: center;
        margin-bottom: 30px;
        font-family: 'Noto Sans KR', sans-serif !important;
    }

    /* 로비 카드 (수사 파일 스타일) */
    .file-card {
        background: #111827;
        border: 1px solid #374151;
        border-radius: 12px;
        padding: 50px 25px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        transition: all 0.2s ease;
        height: 100%;
    }
    .file-card:hover {
        border-color: #60a5fa;
        background: #131c2e;
    }
    .file-icon { font-size: 4rem; margin-bottom: 20px; }
    .file-title {
        font-family: 'Nanum Myeongjo', serif !important;
        font-size: 2rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 10px;
    }

    /* 메신저 수사 채팅방 */
    .messenger-room {
        background: #070a12;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 25px;
        max-width: 850px;
        margin: 0 auto 20px auto;
        box-shadow: inset 0 2px 10px rgba(0,0,0,0.8);
        height: 500px;
        overflow-y: auto;
    }

    .msg-row-left { display: flex; justify-content: flex-start; margin-bottom: 14px; }
    .msg-row-right { display: flex; justify-content: flex-end; margin-bottom: 14px; }
    .msg-bubble-left {
        background-color: #1e293b;
        color: #f1f5f9;
        padding: 12px 16px;
        border-radius: 4px 12px 12px 12px;
        max-width: 75%;
        border-left: 3px solid #60a5fa;
        font-family: 'Noto Sans KR', sans-serif !important;
        font-size: 1rem;
    }
    .msg-bubble-right {
        background-color: #1d4ed8;
        color: #ffffff;
        padding: 12px 16px;
        border-radius: 12px 4px 12px 12px;
        max-width: 75%;
        border-right: 3px solid #93c5fd;
        font-family: 'Noto Sans KR', sans-serif !important;
        font-size: 1rem;
    }
    .msg-sender { font-size: 0.8rem; color: #94a3b8; margin-bottom: 3px; font-weight: 700; font-family: 'Noto Sans KR', sans-serif !important; }

    /* 버튼 스타일 */
    .stButton > button, div[data-testid="stFormSubmitButton"] > button {
        background: #1e3a8a;
        color: #ffffff;
        border: 1px solid #3b82f6;
        border-radius: 10px;
        font-weight: 700;
        font-size: 1.05rem;
        height: 50px;
        font-family: 'Noto Sans KR', sans-serif !important;
        width: 100%;
        transition: background 0.2s;
    }
    .stButton > button:hover {
        background: #2563eb;
        border-color: #60a5fa;
    }

    h1, h2, h3, h4, label { font-family: 'Nanum Myeongjo', serif !important; }
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
    당신은 추리 게임 진행자입니다. 다음 뉴스 기사를 바탕으로 게임을 구성하세요.
    - 뉴스 제목: {title}
    - 뉴스 요약: {desc}

    4명의 용의자(1: 김시민, 2: 박기자, 3: 최학자, 4: 이스파이)가 있습니다.
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
# 3. 화면 UI 구성
# ---------------------------------------------------------
st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)
st.markdown('<div class="investigation-title">🔍 미스터리 수사국</div>', unsafe_allow_html=True)
st.markdown(f'<div class="investigation-subtitle">실시간 가짜 뉴스 색출 및 추리 | 누적 점수: <span style="color: #60a5fa; font-weight:700;">{st.session_state["total_score"]}점</span></div>', unsafe_allow_html=True)

# 로비 화면
if st.session_state['active_chat_game'] is None:
    st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)
    l_col1, l_col2 = st.columns(2, gap="large")

    with l_col1:
        st.markdown("""
        <div class="file-card">
            <div class="file-icon">🕵️‍♂️</div>
            <div class="file-title">마피아42: 스파이 잡기</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div style="height: 15px;"></div>', unsafe_allow_html=True)
        if st.button("수사 파일 열기 (입장)", key="lobby_mafia_btn", use_container_width=True):
            st.session_state['active_chat_game'] = "mafia"
            st.session_state['mafia_phase'] = 'init'
            st.session_state['messenger_chats'] = []
            st.rerun()

    with l_col2:
        st.markdown("""
        <div class="file-card">
            <div class="file-icon">🎤</div>
            <div class="file-title">뉴스 키워드 쿵쿵따 쇼</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div style="height: 15px;"></div>', unsafe_allow_html=True)
        if st.button("퀴즈 스튜디오 입장", key="lobby_kung_btn", use_container_width=True):
            st.session_state['active_chat_game'] = "kungkungta"
            random_first_words = ["인공지능", "경제성장", "기후변화", "우주탐사", "디지털혁신", "글로벌무역", "스마트폰"]
            chosen_word = random.choice(random_first_words)
            st.session_state['kung_current_word'] = chosen_word
            st.session_state['kung_history'] = [
                {"role": "ai", "text": f"수사관님 환영합니다. 첫 제시어는 **'{chosen_word}'**입니다. 단어를 이어주세요."}
            ]
            st.rerun()

else:
    top_nav1, top_nav2 = st.columns([4, 1])
    with top_nav2:
        if st.button("← 로비로 돌아가기", use_container_width=True):
            st.session_state['active_chat_game'] = None
            st.session_state['mafia_phase'] = 'init'
            st.rerun()

    st.markdown("---")

    # [마피아 게임 모드]
    if st.session_state['active_chat_game'] == "mafia":
        if st.session_state['mafia_phase'] == 'init':
            st.markdown('<div class="file-card" style="max-width:700px; margin:0 auto; padding:40px;">', unsafe_allow_html=True)
            st.markdown("### 🕵️‍♂️ [사건 파일 #42] 스파이 색출 작전")
            st.markdown("""
            <div style="color: #94a3b8; text-align: left; line-height: 1.8; margin: 20px 0; font-family: 'Noto Sans KR', sans-serif !important; font-size: 1rem;">
                📌 <b>수사 가이드</b><br>
                1. [수사 개시]를 누르면 실시간 뉴스 사건과 4명의 용의자가 소집됩니다.<br>
                2. 용의자들은 왼쪽에 각자의 증언(진실 또는 조작된 가짜 뉴스)을 진술합니다.<br>
                3. 채팅창을 통해 의견을 나누고, 가짜를 퍼뜨린 스파이를 지목해 체포하세요!
            </div>
            """, unsafe_allow_html=True)
            st.markdown("---")
            if st.button("🚨 수사 개시 (용의자 소집)", use_container_width=True):
                if not gemini_key or not client_id:
                    st.error("❌ API Key가 설정되지 않았습니다!")
                else:
                    with st.spinner("📂 사건 파일 수신 및 용의자 심문 준비 중..."):
                        random_item = fetch_random_naver_news()
                        if random_item:
                            t = random_item.get('title', '').replace("<b>", "").replace("</b>", "").replace("&quot;", '"').replace("&amp;", "&")
                            d = random_item.get('description', '').replace("<b>", "").replace("</b>", "").replace("&quot;", '"').replace("&amp;", "&")
                            
                            g_data = generate_mafia_game(t, d, gemini_key)
                            g_data['title'] = t
                            st.session_state['mafia_game_data'] = g_data
                            
                            chats = [{"sender": "상황실", "text": f"📌 [긴급 속보] {t}"}]
                            for p in g_data['players']:
                                chats.append({"sender": p['name'], "text": p['statement']})
                            st.session_state['messenger_chats'] = chats
                            st.session_state['mafia_phase'] = 'debate'
                            st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        elif st.session_state['mafia_phase'] == 'debate':
            g = st.session_state['mafia_game_data']
            
            st.markdown(f"#### 📌 수사 대상 사건: {g['title']}")
            
            st.markdown('<div class="messenger-room">', unsafe_allow_html=True)
            for chat in st.session_state['messenger_chats']:
                if chat['sender'] == "수사관 (나)":
                    st.markdown(f"""
                    <div class="msg-row-right">
                        <div>
                            <div class="msg-sender" style="text-align:right;">{chat['sender']}</div>
                            <div class="msg-bubble-right">{chat['text']}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                elif chat['sender'] == "상황실":
                    st.markdown(f"""
                    <div style="text-align:center; color:#60a5fa; font-size:0.9rem; margin:12px 0; font-weight:bold; font-family:'Noto Sans KR',sans-serif;">
                        {chat['text']}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="msg-row-left">
                        <div>
                            <div class="msg-sender">👤 용의자: {chat['sender']}</div>
                            <div class="msg-bubble-left">{chat['text']}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            with st.form(key="msg_form", clear_on_submit=True):
                user_msg = st.text_input("수사관 의견 입력", placeholder="예: 3번 용의자 진술에 모순이 있습니다.")
                msg_submit = st.form_submit_button("의견 기록 📝", use_container_width=True)

            if msg_submit and user_msg.strip():
                st.session_state['messenger_chats'].append({"sender": "수사관 (나)", "text": user_msg.strip()})
                st.rerun()

            st.markdown("---")
            st.markdown("### ⚖️ [최종 체포] 가짜 뉴스를 유포한 스파이를 지목하세요")
            player_names = [f"{idx+1}번 용의자: {p['name']}" for idx, p in enumerate(g['players'])]
            selected_player = st.selectbox("체포할 용의자 선택", options=player_names)
            
            if st.button("🚨 스파이 체포 영장 집행", use_container_width=True):
                sel_idx = player_names.index(selected_player)
                st.session_state['selected_vote'] = sel_idx
                st.session_state['mafia_phase'] = 'result'
                st.rerun()

        elif st.session_state['mafia_phase'] == 'result':
            g = st.session_state['mafia_game_data']
            voted_idx = st.session_state['selected_vote']
            voted_player = g['players'][voted_idx]
            spy_player = g['players'][g['spy_index']]
            
            st.markdown('<div class="file-card" style="max-width:750px; margin:0 auto; padding:35px;">', unsafe_allow_html=True)
            st.markdown(f"### ⚖️ [수사 결과보고서]")
            st.markdown(f"💥 **{voted_player['name']}의 최후 변론**: \"{g['defense']}\"")
            st.markdown("---")
            
            if voted_idx == g['spy_index']:
                st.balloons()
                st.success(f"🎉 [수사 성공] {voted_player['name']}(은)는 진짜 스파이였습니다! (+20점)")
                st.session_state['total_score'] += 20
            else:
                st.error(f"💀 [수사 실패] 무고한 시민({voted_player['name']})을 체포했습니다! 진짜 스파이는 **{spy_player['name']}**이었습니다!")

            st.info(f"💡 **팩트체크 보고서**: {g['fact_check']}")
            
            if st.button("📂 새로운 사건 파일 배당받기", use_container_width=True):
                st.session_state['mafia_phase'] = 'init'
                st.session_state['messenger_chats'] = []
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # [쿵쿵따 쇼 모드]
    elif st.session_state['active_chat_game'] == "kungkungta":
        st.markdown(f"### 🎤 쿵쿵따 스튜디오 (현재 제시어: **{st.session_state['kung_current_word']}**) 끝 글자: **'{st.session_state['kung_current_word'][-1]}'**")
        st.markdown("---")

        st.markdown('<div class="messenger-room" style="height:450px;">', unsafe_allow_html=True)
        for chat in st.session_state['kung_history']:
            if chat['role'] == 'ai':
                st.markdown(f"""
                <div class="msg-row-left">
                    <div>
                        <div class="msg-sender">진행자 AI</div>
                        <div class="msg-bubble-left">{chat['text']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="msg-row-right">
                    <div>
                        <div class="msg-sender" style="text-align:right;">수사관 (나)</div>
                        <div class="msg-bubble-right">{chat['text']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        with st.form(key="kung_form", clear_on_submit=True):
            user_word = st.text_input("단어 입력", placeholder=f"'{st.session_state['kung_current_word'][-1]}'로 시작하는 단어를 입력하세요")
            kung_submit = st.form_submit_button("단어 제출 🚀", use_container_width=True)

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
