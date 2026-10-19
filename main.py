
import os
import requests
import streamlit as st
from google import genai

# -------------------------------
# 기본 설정
# -------------------------------
st.set_page_config(
    page_title="뉴스픽 스튜디오",
    page_icon="📰",
    layout="wide"
)

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

st.markdown("""
<style>
.block-container {
    max-width: 1050px;
    padding-top: 2rem;
}
.hero {
    padding: 35px;
    border-radius: 20px;
    background: linear-gradient(120deg, #172554, #2563a6);
    color: white;
    margin-bottom: 25px;
}
.hero h1 { color: white; font-size: 38px; }
.hero p { color: #e2e8f0; font-size: 17px; }
.news-card {
    border: 1px solid #e2e8f0;
    padding: 18px;
    border-radius: 14px;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <h1>📰 뉴스픽 스튜디오</h1>
    <p>뉴스에서 발견한 이슈를 나만의 콘텐츠로</p>
    <p>관심 있는 뉴스를 검색하고, 나만의 콘텐츠를 기획해 보세요.</p>
</div>
""", unsafe_allow_html=True)


# -------------------------------
# 네이버 뉴스 검색 API
# -------------------------------
def search_news(query, display=10):
    url = "https://openapi.naver.com/v1/search/news.json"

    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }

    params = {
        "query": query,
        "display": display,
        "sort": "date"
    }

    response = requests.get(
        url, headers=headers, params=params, timeout=15
    )
    response.raise_for_status()

    return response.json().get("items", [])


def clean_html(text):
    import re
    text = re.sub(r"<[^>]*>", "", text or "")
    return (
        text.replace("&quot;", '"')
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&#39;", "'")
    )


# -------------------------------
# 제미나이 콘텐츠 기획
# -------------------------------
def make_content_plan(articles, content_type, audience, purpose):
    client = genai.Client(api_key=GEMINI_API_KEY)

    news_text = "\n\n".join([
        f"기사 {i+1}\n"
        f"제목: {article['title']}\n"
        f"언론사: {article['source']}\n"
        f"요약 정보: {article['description']}\n"
        f"링크: {article['url']}"
        for i, article in enumerate(articles)
    ])

    prompt = f"""
당신은 뉴스 기반 콘텐츠 기획을 돕는 미디어 기획자입니다.

사용자가 선택한 뉴스의 제목과 검색 결과에 표시된 정보만을 바탕으로
실행 가능한 콘텐츠 기획안을 작성하세요.

[선택한 뉴스]
{news_text}

[기획 조건]
콘텐츠 유형: {content_type}
주요 대상: {audience}
전달 목적: {purpose}

다음 항목으로 한국어 기획안을 작성하세요.

1. 콘텐츠 제목 후보 3개
2. 기획 의도
3. 핵심 전달 메시지
4. 콘텐츠 구성 및 전개 순서
5. 관심을 끌 수 있는 도입 방식
6. 추가로 확인하거나 취재할 질문 3개
7. 사실 확인 시 주의할 점

주의사항:
- 기사에 없는 사실이나 통계를 만들어 내지 마세요.
- 제목과 짧은 요약만으로 확인할 수 없는 내용은 단정하지 마세요.
- 확인이 필요한 정보는 원문 확인이 필요하다고 밝혀 주세요.
- 추상적인 설명보다 실제 콘텐츠 제작에 활용할 수 있는 구체적인 아이디어를 제시하세요.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text


# -------------------------------
# 뉴스 검색 화면
# -------------------------------
st.subheader("🔎 1. 관심 있는 뉴스 검색")

with st.form("search_form"):
    query = st.text_input(
        "검색어",
        placeholder="예: 청소년 스마트폰 사용, 환경 문제, 대중문화"
    )
    search_button = st.form_submit_button(
        "뉴스 검색하기", type="primary", use_container_width=True
    )

st.caption("추천 주제: 청소년 · 환경 · 사회문제 · 문화 · 경제")

if "news_items" not in st.session_state:
    st.session_state.news_items = []

if search_button:
    if not query.strip():
        st.warning("검색할 키워드를 입력해 주세요.")
    elif not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        st.error("네이버 API 키를 환경 변수에 설정해 주세요.")
    else:
        try:
            with st.spinner("관련 뉴스를 검색하고 있어요..."):
                results = search_news(query.strip())

            st.session_state.news_items = [
                {
                    "title": clean_html(item.get("title", "")),
                    "source": "네이버 뉴스 검색 결과",
                    "description": clean_html(item.get("description", "")),
                    "url": item.get("originallink") or item.get("link", ""),
                    "date": item.get("pubDate", "")
                }
                for item in results
            ]

            st.session_state.search_query = query.strip()

            if not results:
                st.info("검색 결과가 없습니다. 다른 키워드를 입력해 보세요.")

        except requests.RequestException as e:
            st.error(f"뉴스 검색에 실패했어요. API 키와 요청 설정을 확인해 주세요. ({e})")

# -------------------------------
# 검색 결과 표시 및 기사 선택
# -------------------------------
articles = st.session_state.news_items

if articles:
    st.divider()
    st.subheader("🗞️ 2. 기획에 활용할 뉴스 선택")
    st.write("콘텐츠 기획에 사용할 기사를 하나 이상 선택해 주세요.")

    selected_indices = []

    for i, article in enumerate(articles):
        with st.container(border=True):
            st.markdown(f"**{i+1}. {article['title']}**")
            st.caption(f"게시일: {article['date']}")
            st.write(article["description"])

            if article["url"]:
                st.markdown(f"[기사 원문 확인하기]({article['url']})")

            if st.checkbox("이 기사 선택", key=f"article_{i}"):
                selected_indices.append(i)

    selected_articles = [articles[i] for i in selected_indices]

    st.divider()
    st.subheader("💡 3. 어떤 콘텐츠를 만들까요?")

    col1, col2 = st.columns(2)

    with col1:
        content_type = st.selectbox(
            "콘텐츠 유형",
            ["카드뉴스", "숏폼 영상", "인터뷰", "자유 기획"]
        )

        audience = st.selectbox(
            "주요 대상",
            ["청소년", "일반 대중", "학생 및 교육 공동체", "직접 입력"]
        )

        if audience == "직접 입력":
            audience = st.text_input("주요 대상 직접 입력")

    with col2:
        purpose = st.selectbox(
            "전달 목적",
            ["정보 전달", "문제 제기", "인식 개선", "다양한 관점 소개"]
        )

        st.info(
            "선택한 뉴스와 제작 조건을 바탕으로 "
            "제미나이가 콘텐츠 기획 초안을 작성합니다."
        )

    if st.button(
        "✨ 콘텐츠 기획안 만들기",
        type="primary",
        use_container_width=True
    ):
        if not selected_articles:
            st.warning("먼저 뉴스 기사를 선택해 주세요.")
        elif not GEMINI_API_KEY:
            st.error("제미나이 API 키를 환경 변수에 설정해 주세요.")
        else:
            try:
                with st.spinner("뉴스를 바탕으로 기획안을 작성하고 있어요..."):
                    plan = make_content_plan(
                        selected_articles,
                        content_type,
                        audience,
                        purpose
                    )

                st.session_state.generated_plan = plan

            except Exception as e:
                st.error(
                    "기획안 생성에 실패했어요. 제미나이 API 키, "
                    f"모델 지원 여부 및 사용량을 확인해 주세요. ({e})"
                )

# -------------------------------
# 생성된 기획안
# -------------------------------
if st.session_state.get("generated_plan"):
    st.divider()
    st.subheader("📝 4. 나의 콘텐츠 기획안")

    plan = st.session_state.generated_plan

    st.markdown(plan)

    st.download_button(
        label="기획안 다운로드",
        data=plan,
        file_name="뉴스픽_콘텐츠_기획안.txt",
        mime="text/plain",
        use_container_width=True
    )

st.divider()
st.caption("뉴스픽 스튜디오 | 뉴스 검색 결과를 바탕으로 콘텐츠 아이디어를 기획합니다.")
