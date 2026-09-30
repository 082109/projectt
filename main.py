import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
from google import genai

# ---------------------------------------------------------
# 1. 페이지 기본 설정 및 타이틀
# ---------------------------------------------------------
st.set_page_config(
    page_title="미디어 프레이밍 & 편향성 분석기",
    page_icon="📰",
    layout="wide"
)

st.title("📰 미디어커뮤니케이션 : 실시간 뉴스 프레이밍 & AI 편향성 분석")
st.markdown("""
이 웹앱은 **네이버 클라우드 API HUB**를 통해 실시간 기사를 수집하고, **Gemini AI API**를 활용해 기사별 **보도 프레임**과 **편향성/어조**를 분석한 뒤 **데이터 저널리즘 차트**로 시각화합니다.
""")
st.divider()

# ---------------------------------------------------------
# 2. API 키 불러오기 (secrets.toml 또는 사이드바 입력)
# ---------------------------------------------------------
st.sidebar.header("🔑 API 설정")

client_id = st.secrets.get("NAVER_CLIENT_ID", "").strip() or st.sidebar.text_input("Naver Client ID", type="password").strip()
client_secret = st.secrets.get("NAVER_CLIENT_SECRET", "").strip() or st.sidebar.text_input("Naver Client Secret", type="password").strip()
gemini_key = st.secrets.get("GEMINI_API_KEY", "").strip() or st.sidebar.text_input("Gemini API Key", type="password").strip()

if not (client_id and client_secret and gemini_key):
    st.info("💡 사이드바에 API 키를 입력하거나 `.streamlit/secrets.toml`에 설정해주세요.")

# ---------------------------------------------------------
# 3. 네이버 클라우드 API HUB 뉴스 호출 함수 (URL 수정 완료)
# ---------------------------------------------------------
def fetch_naver_news(query, display_count=10):
    # NAVER API HUB 뉴스 검색 정식 URL
    url = f"https://naverapihub.apigw.ntruss.com/search/v1/news?query={query}&display={display_count}&sort=date"
    
    # NAVER API HUB 전용 헤더
    headers = {
        "X-NCP-APIGW-API-KEY-ID": client_id,
        "X-NCP-APIGW-API-KEY": client_secret
    }
    
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json().get('items', [])
    else:
        st.error(f"네이버 API 호출 실패 (상태 코드: {response.status_code}) - Client ID와 Secret을 다시 확인해 주세요.")
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
# 5. 메인 UI 및 검색 실행
# ---------------------------------------------------------
col_input1, col_input2 = st.columns([3, 1])

with col_input1:
    search_query = st.text_input("🔍 분석할 미디어 이슈/키워드를 입력하세요", value="마약")

with col_input2:
    num_articles = st.selectbox("분석 기사 수", options=[5, 10, 15, 20], index=1)

start_analysis = st.button("🚀 뉴스 수집 & AI 분석 시작", use_container_width=True)

if start_analysis:
    if not (client_id and client_secret and gemini_key):
        st.error("❌ Naver Client ID, Naver Client Secret, Gemini API 키가 모두 입력되어야 합니다.")
    else:
        with st.spinner("네이버 뉴스 데이터 수집 중..."):
            news_items = fetch_naver_news(search_query, num_articles)
        
        if not news_items:
            st.warning("수집된 데이터가 없습니다. 키워드를 변경하거나 API 키를 확인하세요.")
        else:
            st.success(f"총 {len(news_items)}개의 최신 기사를 가져왔습니다. Gemini AI 분석 중...")
            
            progress_bar = st.progress(0)
            analyzed_list = []
            
            for idx, item in enumerate(news_items):
                clean_title = item.get('title', '').replace("<b>", "").replace("</b>", "").replace("&quot;", '"').replace("&amp;", "&")
                clean_desc = item.get('description', '').replace("<b>", "").replace("</b>", "").replace("&quot;", '"').replace("&amp;", "&")
                
                ai_res = analyze_article_with_gemini(clean_title, clean_desc, gemini_key)
                
                analyzed_list.append({
                    "제목": clean_title,
                    "AI 요약": ai_res.get("summary", ""),
                    "보도 프레임": ai_res.get("frame_category", "기타"),
                    "편향성 점수": ai_res.get("bias_score", 0),
                    "핵심 키워드": ", ".join(ai_res.get("key_keywords", [])),
                    "링크": item.get('originallink', item.get('link', '#'))
                })
                
                progress_bar.progress((idx + 1) / len(news_items))
            
            df = pd.DataFrame(analyzed_list)
            st.toast("AI 분석 완료!", icon="🎉")

            # ---------------------------------------------------------
            # 6. 데이터 시각화 대시보드
            # ---------------------------------------------------------
            st.subheader("📊 미디어 보도 경향 분석 결과")
            
            tab1, tab2 = st.tabs(["보도 프레임 분석", "편향성/어조 분포"])
            
            with tab1:
                col_chart1, col_chart2 = st.columns([1, 1])
                with col_chart1:
                    frame_counts = df['보도 프레임'].value_counts().reset_index()
                    frame_counts.columns = ['보도 프레임', '기사 수']
                    fig_pie = px.pie(
                        frame_counts, 
                        values='기사 수', 
                        names='보도 프레임',
                        title="언론 보도 프레임 점유율",
                        hole=0.4,
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with col_chart2:
                    st.markdown("#### 💡 프레임 분석 해설")
                    st.write("언론이 이 주제를 다룰 때 어떤 **프레임(시각)**을 집중적으로 사용하는지 비율로 보여줍니다.")
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

            # ---------------------------------------------------------
            # 7. 기사 상세 카드 목록
            # ---------------------------------------------------------
            st.subheader("📋 기사별 AI 분석 상세")
            for idx, row in df.iterrows():
                with st.expander(f"[{row['보도 프레임']}] {row['제목']}"):
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.markdown(f"**AI 요약:** {row['AI 요약']}")
                        st.markdown(f"**핵심 키워드:** `{row['핵심 키워드']}`")
                    with col_b:
                        st.metric("편향성/어조 점수", f"{row['편향성 점수']} / 5")
                        st.markdown(f"[🔗 원문 기사 링크]({row['링크']})")
