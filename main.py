import streamlit as st
from google import genai
import re

# -----------------------------
# 기본 설정
# -----------------------------
st.set_page_config(
    page_title="News Frame | 뉴스 프레임 비교",
    page_icon="📰",
    layout="wide"
)

st.markdown("""
<style>
    .stApp {
        background: #f7f7f8;
    }
    .main-title {
        font-size: 42px;
        font-weight: 800;
        color: #111111;
        margin-bottom: 4px;
    }
    .sub-title {
        color: #666666;
        font-size: 17px;
        margin-bottom: 25px;
    }
    .news-card {
        background: white;
        border: 1px solid #e5e5e5;
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    .news-source {
        color: #d71920;
        font-size: 14px;
        font-weight: 700;
    }
    .news-title {
        color: #111111;
        font-size: 19px;
        font-weight: 750;
        line-height: 1.45;
        margin: 7px 0;
    }
    .news-summary {
        color: #555555;
        line-height: 1.6;
        font-size: 14px;
    }
    .compare-box {
        background: white;
        border-radius: 14px;
        padding: 22px;
        border: 1px solid #e5e5e5;
        line-height: 1.75;
    }
    div[data-testid="stButton"] button {
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# API 연결
# -----------------------------
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Gemini API 키가 없습니다. Streamlit Cloud의 Secrets에 GEMINI_API_KEY를 추가해주세요.")
    st.stop()

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
MODEL = "gemini-3.7-flash"

# -----------------------------
# Gemini 호출 함수
# -----------------------------
def ask_gemini(prompt):
    """Gemini에 Google Search를 함께 사용해 질문한다."""
    response = client.interactions.create(
        model=MODEL,
        input=prompt,
        tools=[{"type": "google_search"}]
    )
    return response

def get_output_text(response):
    """Gemini 응답에서 최종 텍스트를 가져온다."""
    return getattr(response, "output_text", "") or ""

def get_citations(response):
    """Google Search가 실제로 사용한 출처 URL을 가져온다."""
    citations = []
    try:
        for step in response.steps:
            if getattr(step, "type", "") != "model_output":
                continue

            for block in getattr(step, "content", []):
                if getattr(block, "type", "") != "text":
                    continue

                for ann in getattr(block, "annotations", []) or []:
                    if getattr(ann, "type", "") == "url_citation":
                        url = getattr(ann, "url", "")
                        title = getattr(ann, "title", "")
                        if url and not any(x["url"] == url for x in citations):
                            citations.append({
                                "title": title or "출처",
                                "url": url
                            })
    except Exception:
        pass
    return citations

def search_news(keyword):
    """검색어와 관련된 최근 뉴스 기사 후보를 검색한다."""
    prompt = f"""
한국어 뉴스 검색 서비스처럼 행동해줘.

검색어: {keyword}

현재 웹에서 이 검색어와 직접 관련된 최근 한국어 뉴스 기사 8개를 찾아줘.
가능하면 서로 다른 언론사의 기사를 골라줘.

각 기사마다 반드시 다음 형식으로 한 줄씩 작성해:
[기사] 제목 || 언론사 || 날짜 || URL || 기사에서 다루는 핵심 내용 한 문장

조건:
- 실제 검색 결과에서 확인되는 기사만 사용해.
- 존재하지 않는 기사나 URL을 만들지 마.
- 뉴스 기사 자체를 우선하고 블로그, 쇼핑, 홍보 페이지는 제외해.
- 제목은 기사 제목을 가능한 한 그대로 적어.
- URL은 실제 기사 URL을 적어.
- 최근 기사부터 정리해.
"""
    response = ask_gemini(prompt)
    text = get_output_text(response)
    citations = get_citations(response)

    articles = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("[기사]"):
            continue

        parts = [p.strip() for p in line.replace("[기사]", "", 1).split("||")]
        if len(parts) >= 5:
            title, source, date, url, summary = parts[:5]

            # URL이 검색 결과의 출처와 일치하는 경우를 우선 사용
            if not url.startswith("http"):
                url = ""

            articles.append({
                "title": title,
                "source": source,
                "date": date,
                "url": url,
                "summary": summary
            })

    # 파싱이 잘 안 되는 경우 검색 결과의 인용 링크를 보조적으로 표시
    if not articles and citations:
        for c in citations[:8]:
            articles.append({
                "title": c["title"],
                "source": "Google Search 출처",
                "date": "",
                "url": c["url"],
                "summary": "검색 결과에서 확인된 관련 출처입니다."
            })

    return articles, citations

def compare_articles(article1, article2):
    """선택한 두 기사의 중심 내용과 관점을 비교한다."""
    prompt = f"""
너는 미디어커뮤니케이션학과 학생의 뉴스 분석을 도와주는 분석 도우미야.

아래 두 기사를 비교해서 '뉴스 프레임' 관점에서 분석해줘.
기사에 실제로 나타난 내용만 근거로 판단하고, 언론사의 의도나 기자의 생각을 추측하지 마.

[기사 A]
제목: {article1['title']}
언론사: {article1['source']}
날짜: {article1['date']}
요약: {article1['summary']}
URL: {article1['url']}

[기사 B]
제목: {article2['title']}
언론사: {article2['source']}
날짜: {article2['date']}
요약: {article2['summary']}
URL: {article2['url']}

다음 순서로 한국어로 작성해줘.

### 기사 A의 중심 내용
기사 A가 무엇을 가장 중요하게 다루는지 2~3문장으로 설명.

### 기사 B의 중심 내용
기사 B가 무엇을 가장 중요하게 다루는지 2~3문장으로 설명.

### 관점과 프레임 비교
두 기사가 같은 사건이나 주제를 어떤 서로 다른 측면에서 보여주는지 설명.
예: 원인 중심 / 해결책 중심 / 개인 경험 중심 / 정책 중심 / 경제적 영향 중심 / 사회적 영향 중심 등.
정해진 분류에 억지로 끼워 맞추지 말고 기사 내용에 맞게 설명.

### 사용한 근거
각 기사의 제목, 핵심 내용, 인용된 사람이나 통계 등 어떤 요소가 프레임을 만드는 데 영향을 주는지 간단히 설명.

### 한눈에 비교
A:
B:
차이:
"""
    response = ask_gemini(prompt)
    return get_output_text(response)

# -----------------------------
# 화면
# -----------------------------
st.markdown('<div class="main-title">📰 News Frame</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">같은 이슈를 언론은 어떻게 다르게 보여줄까?</div>',
    unsafe_allow_html=True
)

st.info(
    "검색어를 입력하면 Gemini의 Google Search를 이용해 실제 웹의 관련 뉴스를 찾고, "
    "원하는 기사 2개를 골라 중심 내용과 뉴스 프레임을 비교할 수 있어요."
)

keyword = st.text_input(
    "🔎 뉴스 검색",
    placeholder="예: 저출생, 인공지능 교육, 기후변화, 독거노인 사회적 고립"
)

if "articles" not in st.session_state:
    st.session_state.articles = []

if "comparison" not in st.session_state:
    st.session_state.comparison = ""

if st.button("뉴스 검색하기", type="primary", use_container_width=True):
    if not keyword.strip():
        st.warning("검색어를 입력해주세요.")
    else:
        with st.spinner("웹에서 관련 뉴스를 찾고 있어요..."):
            try:
                articles, citations = search_news(keyword.strip())
                st.session_state.articles = articles
                st.session_state.comparison = ""
            except Exception as e:
                st.error(
                    "뉴스 검색 중 문제가 발생했습니다. Gemini API 키와 사용량 제한을 확인한 뒤 다시 시도해주세요."
                )

# -----------------------------
# 기사 목록
# -----------------------------
articles = st.session_state.articles

if articles:
    st.markdown("## 🗞️ 검색 결과")
    st.caption(f"'{keyword}'와 관련된 뉴스 후보 {len(articles)}개")

    selected = []

    for i, article in enumerate(articles):
        st.markdown(
            f"""
            <div class="news-card">
                <div class="news-source">{article['source']} · {article['date']}</div>
                <div class="news-title">{article['title']}</div>
                <div class="news-summary">{article['summary']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        col1, col2 = st.columns([1, 5])
        with col1:
            checked = st.checkbox("선택", key=f"article_{i}")
        with col2:
            if article["url"]:
                st.markdown(f"[🔗 원문 기사 열기]({article['url']})")

        if checked:
            selected.append(i)

    st.divider()

    if len(selected) == 2:
        a = articles[selected[0]]
        b = articles[selected[1]]

        st.markdown("## 🔍 두 기사 비교")
        st.write(f"**A.** {a['title']}")
        st.write(f"**B.** {b['title']}")

        if st.button("✨ 뉴스 프레임 분석하기", type="primary", use_container_width=True):
            with st.spinner("두 기사의 내용을 비교하고 있어요..."):
                try:
                    st.session_state.comparison = compare_articles(a, b)
                except Exception:
                    st.error(
                        "기사 분석 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요."
                    )

    elif len(selected) > 2:
        st.warning("비교할 기사는 정확히 2개만 선택해주세요.")
    else:
        st.caption("비교하려면 기사 2개를 선택해주세요.")

# -----------------------------
# 분석 결과
# -----------------------------
if st.session_state.comparison:
    st.divider()
    st.markdown("## 📊 뉴스 프레임 비교 결과")
    st.markdown(
        f'<div class="compare-box">{st.session_state.comparison.replace(chr(10), "<br>")}</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "※ AI 분석은 기사에 나타난 표현과 정보에 근거한 참고용 분석입니다. "
        "실제 기사의 원문을 함께 확인하는 것이 좋습니다."
    )
else:
    st.markdown("### 💡 이 앱에서 볼 수 있는 것")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**① 뉴스 검색**")
        st.write("검색어와 관련된 실제 웹 뉴스 후보를 찾아봅니다.")

    with col2:
        st.markdown("**② 기사 선택**")
        st.write("서로 다른 기사 2개를 직접 골라봅니다.")

    with col3:
        st.markdown("**③ 프레임 비교**")
        st.write("각 기사가 어떤 내용과 관점을 중심으로 다루는지 비교합니다.")
