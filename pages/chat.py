import streamlit as st
import urllib.request
import urllib.parse
import json
import random

# ---------------------------------------------------------
# 1. 페이지 설정 및 레트로 아케이드 픽셀 폰트 스타일링
# ---------------------------------------------------------
st.set_page_config(
    page_title="FrameLens - 레트로 아케이드",
    page_icon="🕹️",
    layout="wide"
)

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/oungda/galmuri/dist/galmuri.css');

    .stApp {
        background: #09090b;
        color: #f3f4f6;
        font-family: 'Galmuri11', monospace !important;
    }
    
    section[data-testid="stSidebar"] {
        background-color: #121216 !important;
        border-right: 2px solid #3f3f46 !important;
    }
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] div, 
    section[data-testid="stSidebar"] a {
        font-family: 'Galmuri11', monospace !important;
        color: #e4e4e7 !important;
        font-size: 1.05rem !important;
    }

    /* 상단 메인 타이틀 */
    .game-main-title {
        font-family: 'Galmuri11', monospace !important;
        font-size: 3.5rem;
        font-weight: 900;
        color: #facc15;
        text-align: center;
        margin-top: 15px;
        margin-bottom: 5px;
        letter-spacing: 2px;
        text-shadow: 3px 3px 0px #b45309, 0 0 15px rgba(250, 204, 21, 0.5);
    }
    .game-main-subtitle {
        font-family: 'Galmuri11', monospace !important;
        color: #a1a1aa;
        font-size: 1.15rem;
        text-align: center;
        margin-bottom: 35px;
        letter-spacing: 1px;
    }

    /* 오락실 캐비닛 스타일 카드 박스 */
    .transparent-game-card {
        background: #18181b !important;
        border: 3px solid #52525b;
        border-radius: 0px;
        padding: 45px 20px;
        text-align: center;
        box-shadow: 5px 5px 0px #000000;
        transition: all 0.2s ease;
    }
    .transparent-game-card:hover {
        border-color: #facc15;
        box-shadow: 5px 5px 0px #713f12;
        transform: translate(-2px, -2px);
    }
    
    .card-title-text {
        font-family: 'Galmuri11', monospace !important;
        font-size: 2rem;
        font-weight: 900 !important;
        color: #ffffff;
        margin: 0;
        word-break: keep-all;
        line-height: 1.5;
        letter-spacing: -1px;
        text-shadow: 2px 2px 0px #000000;
    }

    /* 뉴스 기사 내용 표시 박스 */
    .in-app-news-reader {
        background: #18181b;
        border: 3px solid #f59e0b;
        border-radius: 0px;
        padding: 18px 20px;
        max-width: 850px;
        margin: 0 auto 12px auto;
        box-shadow: 4px 4px 0px #000000;
    }
    .news-reader-header {
        font-family: 'Galmuri11', monospace !important;
        color: #f59e0b;
        font-size: 0.95rem;
        font-weight: 700;
        margin-bottom: 6px;
    }
    .news-reader-title {
        font-family: 'Galmuri11', monospace !important;
        font-size: 1.15rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 8px;
        line-height: 1.4;
    }
    .news-reader-body {
        font-family: 'Galmuri11', monospace !important;
        font-size: 0.95rem;
        color: #e4e4e7;
        line-height: 1.6;
        background: #09090b;
        padding: 14px;
        border-left: 4px solid #f59e0b;
        max-height: 200px;
        overflow-y: auto;  
        margin-bottom: 12px;
        white-space: pre-wrap;
    }
    .news-link-btn {
        display: inline-block;
        font-family: 'Galmuri11', monospace !important;
        color: #facc15 !important;
        font-size: 0.88rem;
        font-weight: 700;
        text-decoration: none;
        border: 1px solid #facc15;
        padding: 5px 12px;
        background: #27272a;
    }
    .news-link-btn:hover {
        background: #facc15;
        color: #000000 !important;
    }

    /* 레트로 아케이드 버튼 스타일 */
    .stButton > button, div[data-testid="stFormSubmitButton"] > button {
        font-family: 'Galmuri11', monospace !important;
        background: #ca8a04 !important;
        color: #ffffff !important;
        border: 2px solid #fef08a !important;
        border-radius: 0px !important;
        font-weight: 700 !important;
        font-size: 1.2rem !important;
        height: 50px !important;
        box-shadow: 3px 3px 0px #000000 !important;
        transition: all 0.1s ease !important;
        letter-spacing: 1px !important;
        width: 100% !important;
    }
    .stButton > button:hover {
        background: #eab308 !important;
        transform: translate(-1px, -1px);
        box-shadow: 4px 4px 0px #000000 !important;
    }

    /* 메신저 상단 바 및 설명 박스 */
    .messenger-top-bar {
        background: #27272a;
        border: 2px solid #52525b;
        border-bottom: none;
        padding: 8px 16px;
        max-width: 850px;
        margin: 0 auto;
    }
    .messenger-top-title {
        font-family: 'Galmuri11', monospace !important;
        color: #facc15;
        font-size: 1rem;
        font-weight: 700;
        text-align: center;
        letter-spacing: 2px;
    }

    .explanation-room {
        background: #18181b;
        border: 2px solid #52525b;
        border-top: none;
        padding: 30px;
        max-width: 850px;
        margin: 0 auto 20px auto;
        box-shadow: 4px 4px 0px #000000;
    }

    h1, h2, h3, h4, label, p, span, div {
        font-family: 'Galmuri11', monospace !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. 세션 상태 초기화 및 유틸 함수
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
    뉴스 내용 스파이 찾기 게임 진행자 역할을 수행한다. 다음 실제 뉴스 기사 요약 정보를 바탕으로 게임을 풍성하게 구성한다.
    - 뉴스 제목: {title}
    - 뉴스 요약 내용: {desc}

    지시사항:
    1. 위 뉴스 정보를 바탕으로 플레이어가 게임을 원활히 즐길 수 있도록 **상세하고 풍성한 본문 내용(news_body)**을 3~4문단 분량으로 확장해서 작성해라.
    2. 4명의 AI 용의자 플레이어(김시민, 박기자, 최학자, 이스파이)가 존재한다. 이 중 한 명은 스파이며, 뉴스 내용을 왜곡하거나 거짓 발언을 한다.

    반드시 아래 JSON 형식으로만 답변한다:
    {{
      "news_body": "여기에 확장된 상세 뉴스 본문 내용을 작성한다.",
      "players": [
        {{"name": "김시민", "role": "시민", "statement": "진짜 기사 내용에 기반한 1번 증언"}},
        {{"name": "박기자", "role": "시민", "statement": "진짜 기사 내용에 기반한 2번 증언"}},
        {{"name": "최학자", "role": "시민", "statement": "진짜 기사 내용에 기반한 3번 증언"}},
        {{"name": "이스파이", "role": "스파이", "statement": "교묘하게 왜곡된 가짜 뉴스 증언"}}
      ],
      "spy_index": 3,
      "defense": "스파이가 최후의 변론으로 하는 변명",
      "fact_check": "진짜 뉴스 본문에 따른 팩트체크 해설"
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
        "news_body": f"최근 보도된 '{title}'와 관련하여 사회 각계의 다양한 의견이 대립하고 있다. 이번 사건은 향후 관련 정책 및 동향에 적지 않은 영향을 미칠 것으로 보이며, 철저한 사실 확인과 다각도의 분석이 요구되고 있다.",
        "players": [
            {"name": "김시민", "role": "시민", "statement": f"이번 기사는 {title[:15]} 관련 사건이 확실하다."},
            {"name": "박기자", "role": "시민", "statement": "보도된 바에 따르면 해당 사안은 철저한 분석이 필요하다."},
            {"name": "최학자", "role": "시민", "statement": "전문가들도 기사 내용과 동일한 입장을 밝혔다."},
            {"name": "이스파이", "role": "스파이", "statement": "사실 이번 기사는 전부 거짓이며 외계인이 개입했다!"}
        ],
        "spy_index": 3,
        "defense": "나는 진짜 시민이다! 나를 처형하면 스파이에게 패배한다!",
        "fact_check": "4번 증언은 완전히 왜곡된 가짜 뉴스다."
    }

def get_kung_reply(user_word, last_word, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={api_key}"
    prompt = f"""
    뉴스 키워드 쿵쿵따 게임 AI 파트너 역할을 수행한다.
    마지막 단어: '{last_word}'
    사용자가 제시한 단어: '{user_word}'
    
    규칙:
    1. 사용자가 마지막 단어의 끝글자로 시작하는 올바른 단어를 말했다면 칭찬하고, 그 단어의 끝글자로 시작하는 새로운 뉴스/시사 관련 단어를 이어준다.
    2. 글자가 틀렸거나 시사/단어 규칙에 맞지 않으면 지적하고 다시 기회를 준다.
    
    반드시 JSON 형식으로만 답변한다:
    {{
      "status": "success" 또는 "fail",
      "reply_text": "AI의 대화 및 반응 메시지 (~다 체 사용)",
      "next_word": "성공 시 AI가 이어갈 새로운 단어"
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
        "reply_text": f"좋다! '{user_word}'에 이어 **'기후변화'**로 진행한다.",
        "next_word": "기후변화"
    }

# ---------------------------------------------------------
# 3. 메인 화면 UI 구성
# ---------------------------------------------------------
st.markdown('<div style="height: 15px;"></div>', unsafe_allow_html=True)
st.markdown('<div class="game-main-title">RETRO ARCADE</div>', unsafe_allow_html=True)
st.markdown(f'<div class="game-main-subtitle">INSERT COIN | SCORE: {st.session_state["total_score"]}</div>', unsafe_allow_html=True)

# 로비 선택 화면
if st.session_state['active_chat_game'] is None:
    st.markdown('<div style="height: 30px;"></div>', unsafe_allow_html=True)
    l_col1, l_col2 = st.columns(2, gap="large")

    with l_col1:
        st.markdown("""
        <div class="transparent-game-card">
            <div class="card-title-text">뉴스 내용<br>스파이 찾기</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div style="height: 14px;"></div>', unsafe_allow_html=True)
        if st.button("GAME START", key="lobby_mafia_btn", use_container_width=True):
            st.session_state['active_chat_game'] = "mafia"
            st.session_state['mafia_phase'] = 'init'
            st.session_state['messenger_chats'] = []
            st.rerun()

    with l_col2:
        st.markdown("""
        <div class="transparent-game-card">
            <div class="card-title-text">뉴스 키워드<br>쿵쿵따</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div style="height: 14px;"></div>', unsafe_allow_html=True)
        if st.button("GAME START", key="lobby_kung_btn", use_container_width=True):
            st.session_state['active_chat_game'] = "kungkungta"
            chosen_word = random.choice(["인공지능", "경제성장", "기후변화", "우주탐사", "디지털혁신", "글로벌무역"])
            st.session_state['kung_current_word'] = chosen_word
            st.session_state['kung_history'] = [
                {"role": "ai", "text": f"뉴스 키워드 쿵쿵따에 입장했다. 첫 제시어는 **'{chosen_word}'**이다. 이어서 입력해라."}
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
            st.markdown("""
            <div class="messenger-top-bar">
                <div class="messenger-top-title">EXPLANATION (게임 설명)</div>
            </div>
            <div class="explanation-room">
                <div style="font-size: 1.8rem; font-weight: 900; color: #ffffff; text-align: center; margin-bottom: 10px;">뉴스 내용 스파이 찾기</div>
                <div style="color: #facc15; font-size: 1.1rem; font-weight: 600; text-align: center; margin-bottom: 25px;">
                    실시간 뉴스 증언 분석 및 가짜 뉴스 판별 추리 모드
                </div>
                <div style="color: #e4e4e7; text-align: left; line-height: 1.8; font-size: 1.05rem; max-width: 650px; margin: 0 auto 30px auto;">
                    1. 버튼을 누르면 실시간 뉴스 기사와 4명의 AI 용의자가 소집된다.<br>
                    2. 용의자들의 증언을 메신저 대화로 확인한다.<br>
                    3. 교묘하게 왜곡된 가짜 뉴스를 퍼트린 스파이를 찾아 지목한다.
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("GAME START", use_container_width=True):
                if not gemini_key or not client_id:
                    st.error("API Key가 설정되지 않았다!")
                else:
                    with st.spinner("실시간 뉴스 소집 및 분석 중..."):
                        random_item = fetch_random_naver_news()
                        if random_item:
                            t = random_item.get('title', '').replace("<b>", "").replace("</b>", "").replace("&quot;", '"').replace("&amp;", "&")
                            d = random_item.get('description', '').replace("<b>", "").replace("</b>", "").replace("&quot;", '"').replace("&amp;", "&")
                            l = random_item.get('originallink', random_item.get('link', '#'))
                            
                            g_data = generate_mafia_game(t, d, gemini_key)
                            g_data['title'] = t
                            g_data['link'] = l
                            st.session_state['mafia_game_data'] = g_data
                            
                            chats = []
                            for idx, p in enumerate(g_data['players']):
                                chats.append({"sender": f"{idx+1}번 용의자 [{p['name']}]", "text": p['statement']})
                            st.session_state['messenger_chats'] = chats
                            st.session_state['mafia_phase'] = 'debate'
                            st.rerun()

        elif st.session_state['mafia_phase'] == 'debate':
            g = st.session_state['mafia_game_data']
            news_link = g.get('link', '#')
            news_body = g.get('news_body', '')
            
            # 💡 실제 뉴스 기반 풍성한 본문과 원문 링크 출력
            st.markdown(f"""
            <div class="in-app-news-reader">
                <div class="news-reader-header">> BRIEFING: 실시간 출제 뉴스 브리핑</div>
                <div class="news-reader-title">{g['title']}</div>
                <div class="news-reader-body">{news_body}</div>
                <div style="text-align: right;">
                    <a href="{news_link}" target="_blank" class="news-link-btn">🔗 네이버 원문 기사 전체 읽기 ➔</a>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # CHATTING ROOM 상단 바
            st.markdown("""
            <div class="messenger-top-bar">
                <div class="messenger-top-title">CHATTING ROOM (용의자 증언 대화창)</div>
            </div>
            """, unsafe_allow_html=True)

            chat_box = st.container(height=280)
            with chat_box:
                st.markdown('<div style="padding: 5px;">', unsafe_allow_html=True)
                for chat in st.session_state['messenger_chats']:
                    sender = chat.get('sender', '알 수 없음')
                    text = chat.get('text', '')
                    if sender == "태희 (나)":
                        st.markdown(f"""
                        <div style="display: flex; justify-content: flex-end; margin-bottom: 12px;">
                            <div>
                                <div style="font-family: 'Galmuri11', monospace; font-size: 0.82rem; color: #ffffff; text-align: right; margin-bottom: 3px; font-weight: 700;">{sender}</div>
                                <div style="font-family: 'Galmuri11', monospace; background-color: #ca8a04; color: #ffffff; padding: 8px 12px; border: 1px solid #fef08a; font-size: 0.95rem; line-height: 1.4;">{text}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style="display: flex; justify-content: flex-start; margin-bottom: 12px;">
                            <div>
                                <div style="font-family: 'Galmuri11', monospace; font-size: 0.82rem; color: #facc15; margin-bottom: 3px; font-weight: 700;">{sender}</div>
                                <div style="font-family: 'Galmuri11', monospace; background-color: #27272a; color: #f4f4f5; padding: 8px 12px; border: 1px solid #52525b; font-size: 0.95rem; line-height: 1.4;">{text}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            with st.form(key="msg_form", clear_on_submit=True):
                user_msg = st.text_input("메시지 입력", placeholder="예: 3번 진술이 이상하다. 거짓말 같다.")
                msg_submit = st.form_submit_button("전송", use_container_width=True)

            if msg_submit and user_msg.strip():
                st.session_state['messenger_chats'].append({"sender": "태희 (나)", "text": user_msg.strip()})
                st.rerun()

            st.markdown("---")
            st.markdown("### 스파이 지목 투표")
            player_names = [f"{idx+1}번 용의자: {p['name']}" for idx, p in enumerate(g['players'])]
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
                st.success(f"[시민 승리] {voted_player['name']}(은)는 진짜 스파이였다! (+20점)")
                st.session_state['total_score'] += 20
            else:
                st.error(f"[스파이 승리] 시민({voted_player['name']})이 처형당했다! 진짜 스파이는 {spy_player['name']}이다!")

            st.info(f"팩트체크: {g['fact_check']}")
            
            if st.button("다음 사건 진행", use_container_width=True):
                st.session_state['mafia_phase'] = 'init'
                st.session_state['messenger_chats'] = []
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # [뉴스 키워드 쿵쿵따 모드]
    elif st.session_state['active_chat_game'] == "kungkungta":
        st.markdown(f"### 뉴스 키워드 쿵쿵따 (현재 제시어: **{st.session_state['kung_current_word']}** / 끝 글자: **'{st.session_state['kung_current_word'][-1]}'**)")
        st.markdown("""
        <div style="color: #facc15; font-size: 1.1rem; font-weight: 500; margin-bottom: 15px;">
            AI 파트너와 진행하는 실시간 시사 끝말잇기 대결
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

        st.markdown("""
        <div class="messenger-top-bar">
            <div class="messenger-top-title">QUIZ ROOM</div>
        </div>
        """, unsafe_allow_html=True)

        kung_box = st.container(height=290)
        with kung_box:
            st.markdown('<div style="padding: 5px;">', unsafe_allow_html=True)
            for chat in st.session_state['kung_history']:
                text = chat.get('text', '')
                if chat.get('role') == 'ai':
                    st.markdown(f"""
                    <div style="display: flex; justify-content: flex-start; margin-bottom: 12px;">
                        <div>
                            <div style="font-family: 'Galmuri11', monospace; font-size: 0.82rem; color: #facc15; margin-bottom: 3px; font-weight: 700;">AI SHOW HOST</div>
                            <div style="font-family: 'Galmuri11', monospace; background-color: #27272a; color: #f4f4f5; padding: 8px 12px; border: 1px solid #52525b; font-size: 0.95rem; line-height: 1.4;">{text}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="display: flex; justify-content: flex-end; margin-bottom: 12px;">
                        <div>
                            <div style="font-family: 'Galmuri11', monospace; font-size: 0.82rem; color: #ffffff; text-align: right; margin-bottom: 3px; font-weight: 700;">태희 (나)</div>
                            <div style="font-family: 'Galmuri11', monospace; background-color: #ca8a04; color: #ffffff; padding: 8px 12px; border: 1px solid #fef08a; font-size: 0.95rem; line-height: 1.4;">{text}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with st.form(key="kung_form", clear_on_submit=True):
            user_word = st.text_input("단어 입력", placeholder=f"'{st.session_state['kung_current_word'][-1]}'로 시작하는 단어")
            kung_submit = st.form_submit_button("단어 전송", use_container_width=True)

        if kung_submit:
            if not user_word.strip():
                st.warning("단어를 입력해라!")
            elif not gemini_key:
                st.error("API Key가 설정되지 않았다!")
            else:
                last_w = st.session_state['kung_current_word']
                res = get_kung_reply(user_word.strip(), last_w, gemini_key)
                
                st.session_state['kung_history'].append({"role": "user", "text": user_word.strip()})
                st.session_state['kung_history'].append({"role": "ai", "text": res.get('reply_text', '')})
                
                if res.get('status') == 'success':
                    st.session_state['total_score'] += 10
                    st.session_state['kung_current_word'] = res.get('next_word', last_w)
                st.rerun()
