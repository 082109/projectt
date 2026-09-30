import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
from datetime import datetime
from google import genai

# ---------------------------------------------------------
# 1. 페이지 기본 설정 및 타이틀
# ---------------------------------------------------------
st.set_page_config(
    page_title="FrameLens - AI 뉴스 프레임 분석기",
    page_icon="📰",
    layout="wide"
)

st.title("📰 FrameLens : AI 기반 뉴스 보도 프레임 & 편향성 분석기")
st.markdown("""
이 웹앱은 **네이버 클라우드 API HUB**를 통해 관련 뉴스 기사를 실시간으로 가져옵니다.  
분석하고 싶은 기사를 직접 선택하여 **Gemini AI** 기반의 **보도 프레임 및 편향성 분석**을 진행해 보세요.
""")
st.divider()

# ---------------------------------------------------------
# 2. API 키 불러오기
# ---------------------------------------------------------
st.sidebar.header("🔑 API 설정")

client_id = st.secrets.get("NAVER_CLIENT_ID", "").strip() or st.sidebar.text_input("Naver Client ID", type="password").strip()
client_secret = st.secrets.get("NAVER_CLIENT_SECRET", "").strip() or st.sidebar.text_input("Naver Client Secret", type="password").strip()
gemini_key = st.secrets.get("GEMINI_API_KEY", "").strip() or st.sidebar.text_input("Gemini API Key", type="password").strip()

if not (client_id and client_secret and gemini_key):
    st.info("💡 사이드바에 API 키를 입력하거나 `.streamlit/secrets.toml`에 설정해주세요.")

# ---------------------------------------------------------
# 날짜 포맷 변환 함수 (RFC 822 -> YY-MM-DD HH:MM)
# ---------------------------------------------------------
def parse_pub_date(pub_date_str):
    if not pub_date_str:
        return "날짜 정보 없음"
    try:
        # 네이버 API 날짜 형식 (예: Mon, 30 Sep 2026 13:20:00 +0900)
        dt = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %z")
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return pub_date_str

# ---------------------------------------------------------
# 3. 네이버 뉴스 API 호출 함수 (최대 30건 수집)
# ---------------------------------------------------------
def fetch_naver_news(query, display_count=30):
    url = f"https://naverapihub.apigw.ntruss.com/search/v1/news?query={query}&display={display_count}&sort=date"
    
    headers = {
        "X-NCP-APIGW-API-KEY-ID": client_id,
        "X-NCP-APIGW-API-KEY": client_secret
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get('items', [])
        else:
            st.error(f"네이버 API 호출 실패 (상태 코드: {response.status_code}) - Client ID/Secret을 확인해 주세요.")
            return []
    except Exception as e:
        st.error(f"뉴스 수집 중 오류 발생: {e}")
        return []

# ---------------------------------------------------------
# 4. Gemini AI 기사 분석 함수
# ---------------------------------------------------------
def analyze_article_with_gemini(title, description, api_key):
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    당신은 미디어 비평가이자 데이터 저널리스트입니다. 
    다음 뉴스 기사의 제목과 요약 내용을 바탕으로 언론 보도 프레임과 편향성을 객관적으로 분석해주세요.

    기사 제목: {title}
    기사 요약: {description}

    반드시 다른 설명 없이 오직 아래 형식을 맞춘 유효한 JSON 형식으로만 응답하세요:
    {{
        "summary": "기사의 핵심 2줄 요약",
        "frame_category": "보도 프레임 (다음 중 하나 선택: 갈등·대립 / 경제적 여파 / 정책·제도 / 인간적 비극 / 책임 소재 / 기타)",
        "bias_score": -5부터 5 사이의 정수 (-5: 매우 비판적, 0: 중립·객관적, 5: 매우 옹호적),
        "key_keywords": ["주요키워드1", "주요키워드2", "주요키워드3"]
    }}
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        text = response.text.strip()
        
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        if start_idx != -1 and end_idx != -1:
            json_str = text[start_idx:end_idx+1]
            return json.loads(json_str)
        else:
            return json.loads(text)
            
    except Exception as e:
        return {
            "summary": "AI 분석을 완료하지 못했습니다.",
            "frame_category": "기타",
            "bias_score": 0,
            "key_keywords": ["분석오류"]
        }

# ---------------------------------------------------------
# 5. 검색 및 뉴스 목록 표시
# ---------------------------------------------------------
search_col1, search_col2 = st.columns([4, 1])

with search_col1:
    search_query = st.text_input("🔍 분석할 뉴스 주제나 키워드를 입력하세요", value="마약")

with search_col2:
    st.write("") 
    st.write("")
    search_btn = st.button("🔎 뉴스 검색", use_container_width=True)

# Session State를 활용해 검색 결과 저장
if search_btn or 'news_items' not in st.session_state:
    if client_id and client_secret:
        with st.spinner("최신 관련 뉴스 기사를 검색하는 중..."):
            st.session_state['news_items'] = fetch_naver_news(search_query)
            st.session_state['last_query'] = search_query

# 뉴스 목록 및 선택 체크박스 출력
if 'news_items' in st.session_state and st.session_state['news_items']:
    st.subheader(f"📋 '{st.session_state.get('last_query', '')}' 관련 뉴스 목록")
    st.info("분석하고 싶은 기사의 체크박스를 선택한 후 아래 [선택한 기사 AI 분석 시작] 버튼을 눌러주세요.")

    selected_articles = []

    # 전체 선택 버튼 지원
    select_all = st.checkbox("전체 기사 선택 / 해제")

    # 기사 목록 출력
    with st.form("news_selection_form"):
        for idx, item in enumerate(st.session_state['news_items']):
            clean_title = item.get('title', '').replace("<b>", "").replace("</b>", "").replace("&quot;", '"').replace("&amp;", "&")
            clean_desc = item.get('description', '').replace("<b>", "").replace("</b>", "").replace("&quot;", '"').replace("&amp;", "&")
            link = item.get('originallink', item.get('link', '#'))
            pub_date = parse_pub_date(item.get('pubDate', ''))

            is_selected = st.checkbox(
                f"**{idx+1}. {clean_title}**",
                value=select_all,
                key=f"chk_{idx}"
            )
            st.caption(f"🗓️ **보도 일시:** {pub_date} | 요약: {clean_desc}")
            st.markdown(f"[🔗 원문 기사 보기]({link})")
            st.markdown("---")

            if is_selected:
                selected_articles.append({
                    "title": clean_title,
                    "description": clean_desc,
                    "link": link,
                    "pub_date": pub_date
                })

        submit_analysis = st.form_submit_button("🚀 선택한 기사 AI 분석 시작", use_container_width=True)

    # ---------------------------------------------------------
    # 6. 선택한 기사 AI 분석 및 결과 시각화
    # ---------------------------------------------------------
    if submit_analysis:
        if not selected_articles:
            st.warning("⚠️ 최소 1개 이상의 기사를 선택해 주세요!")
        elif not gemini_key:
            st.error("❌ Gemini API 키를 입력해 주세요.")
        else:
            st.success(f"선택한 {len(selected_articles)}개의 기사를 분석 중입니다...")
            
            progress_bar = st.progress(0)
            analyzed_list = []

            for idx, article in enumerate(selected_articles):
                ai_res = analyze_article_with_gemini(article['title'], article['description'], gemini_key)
                
                analyzed_list.append({
                    "제목": article['title'],
                    "보도 일시": article['pub_date'],
                    "AI 요약": ai_res.get("summary", ""),
                    "보도 프레임": ai_res.get("frame_category", "기타"),
                    "편향성 점수": ai_res.get("bias_score", 0),
                    "핵심 키워드": ", ".join(ai_res.get("key_keywords", [])),
                    "링크": article['link']
                })
                
                progress_bar.progress((idx + 1) / len(selected_articles))

            df = pd.DataFrame(analyzed_list)
            st.toast("AI 분석 완료!", icon="🎉")

            # 대시보드 시각화
            st.subheader("📊 선택 기사 미디어 보도 경향 분석 결과")
            
            tab1, tab2 = st.tabs(["보도 프레임 분포", "편향성/어조 점수"])
            
            with tab1:
                col_chart1, col_chart2 = st.columns([1, 1])
                with col_chart1:
                    frame_counts = df['보도 프레임'].value_counts().reset_index()
                    frame_counts.columns = ['보도 프레임', '기사 수']
                    fig_pie = px.pie(
                        frame_counts, 
                        values='기사 수', 
                        names='보도 프레임',
                        title="보도 프레임 점유율",
                        hole=0.4,
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with col_chart2:
                    st.markdown("#### 💡 프레임 집계 요약")
                    st.dataframe(frame_counts, hide_index=True, use_container_width=True)

            with tab2:
                fig_bar = px.bar(
                    df,
                    x='제목',
                    y='편향성 점수',
                    color='편향성 점수',
                    color_continuous_scale='RdBu_r',
                    title="기사별 어조/편향성 점수 (-5: 비판적 ~ +5: 옹호적)",
                    range_y=[-5, 5]
                )
                fig_bar.update_layout(xaxis_showticklabels=False)
                st.plotly_chart(fig_bar, use_container_width=True)

            # 상세 결과 출력
            st.subheader("📋 선택 기사 상세 분석 카드")
            for idx, row in df.iterrows():
                with st.expander(f"[{row['보도 프레임']}] {row['제목']} ({row['보도 일시']})"):
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.markdown(f"🗓️ **보도 일시:** `{row['보도 일시']}`")
                        st.markdown(f"**AI 요약:** {row['AI 요약']}")
                        st.markdown(f"**핵심 키워드:** `{row['핵심 키워드']}`")
                    with col_b:
                        st.metric("어조/편향성 점수", f"{row['편향성 점수']} / 5")
                        st.markdown(f"[🔗 원문 기사 링크]({row['링크']})")
