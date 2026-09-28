import os

import requests
import streamlit as st
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image

load_dotenv()


def get_secret(name, default=None):
    value = os.getenv(name)
    if value:
        return value
    try:
        return st.secrets[name]
    except Exception:
        return default


API_KEY = get_secret("GEMINI_API_KEY")
MODEL_NAME = get_secret("GEMINI_MODEL", "gemini-2.5-flash")

st.set_page_config(page_title="상품 리뷰 생성기", page_icon="📝")

if not API_KEY:
    st.error(
        "GEMINI_API_KEY가 설정되어 있지 않습니다. "
        "로컬에서는 .env 파일에, Streamlit Cloud에서는 앱 Settings의 Secrets에 입력해주세요. "
        "(.env.example 참고)"
    )
    st.stop()

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(MODEL_NAME)


def fetch_page_text(url, max_chars=4000):
    headers = {"User-Agent": "Mozilla/5.0 (compatible; ReviewGeneratorBot/1.0)"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = " ".join(soup.stripped_strings)
    return text[:max_chars]


def build_draft_prompt(product_name, model_no, price, usage_info, page_info, usage_context, length):
    return f"""당신은 이 제품을 실제로 구매해서 사용해 본 일반 소비자입니다.
아래 정보를 참고해서, 쇼핑몰 리뷰 게시판에 올릴 법한 실제 사용 후기를 작성하세요.

[제품 정보]
- 상품명: {product_name}
- 모델명: {model_no or "미기재"}
- 가격(쿠팡 최저가 기준): {price or "미기재"}
- 사용법/주요 기능: {usage_info or "미기재"}
- 상품 설명 페이지 내용(자동 추출): {page_info or "미기재"}
- 사용 기간/상황: {usage_context or "미기재"}

[작성 규칙]
- 1인칭 사용 후기 톤으로 작성
- 기본적으로 장점 위주로 작성할 것
- 단점은 아주 미미하게만 다루고, 언급할지 말지는 리뷰 맥락상 자연스러운 쪽으로 알아서 판단할 것 (단점 없이 장점만으로 마무리해도 됨)
- 단점을 언급하는 경우, 가격 대비 만족도나 다른 기능적 장점이 그 단점을 충분히 상쇄한다는 뉘앙스로 자연스럽게 연결해서 단점이 부각되지 않도록 할 것
- 광고 문구처럼 과장하지 말고, 실제 사용 장면과 구체적인 느낀 점을 담을 것
- 이모티콘은 쓰지 않거나 최소화
- 전체 글자 수는 공백 포함 약 {length}자 내외로 맞출 것
- 사진이 첨부되어 있다면 사진에 보이는 디테일(색상, 크기, 마감 등)을 자연스럽게 언급에 활용

리뷰 본문만 출력하세요. 제목이나 설명은 붙이지 마세요."""


def build_adjust_prompt(draft, length):
    return f"""아래 리뷰의 글자 수를 공백 포함 약 {length}자에 최대한 맞춰서 다시 써주세요.
내용(장점/단점)과 말투는 그대로 유지하고, 분량만 조절하세요.

[원문]
{draft}

조정한 리뷰 본문만 출력하세요."""


def build_humanize_prompt(draft):
    return f"""다음은 AI가 작성한 상품 후기 초안입니다. AI가 쓴 티가 나지 않고,
실제 사람이 무심하게 남긴 후기처럼 느껴지도록 자연스럽게 다듬어주세요.

[다듬을 때 유의할 점]
- 문장 길이를 다양하게 섞어서 규칙적인 리듬을 깨기
- "정말 만족스러웠습니다", "강력 추천합니다" 같은 상투적인 AI 문구 피하기
- 지나치게 깔끔한 문단 구조 대신, 실제 사람처럼 약간 구어체 섞기
- 형용사·미사여구 나열 줄이기
- 원문의 핵심 내용(장점/단점)과 전체 글자 수는 거의 그대로 유지

[원문]
{draft}

다듬은 리뷰 본문만 출력하세요."""


def call_model(parts, temperature=0.9):
    response = model.generate_content(
        parts,
        generation_config=genai.GenerationConfig(temperature=temperature),
    )
    return response.text.strip()


st.title("📝 상품 리뷰 자동 생성기")
st.caption("제품 정보를 입력하면 실제 사용 후기 느낌의 리뷰를 생성합니다. (Gemini API 사용)")

with st.form("review_form"):
    product_name = st.text_input("상품명 *", placeholder="예: 무선 진공청소기")
    model_no = st.text_input("모델명", placeholder="예: XV-2000")
    price = st.text_input("가격(쿠팡 최저가 기준)", placeholder="예: 49,900원")
    usage_info = st.text_area(
        "사용법 / 주요 기능 (선택)", placeholder="예: 물걸레 겸용, 무선 충전식, 최대 40분 사용 가능"
    )
    product_url = st.text_input(
        "상품 설명 URL (선택, 읽어오지 못할 수도 있으니 위 사용법 입력란과 함께 활용)",
        placeholder="예: https://www.example.com/product/12345",
    )
    usage_context = st.text_input(
        "사용 기간 / 상황 (선택)", placeholder="예: 2주간 매일 거실 청소에 사용"
    )
    photos = st.file_uploader(
        "상품 사진 (선택, 여러 장 가능)",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
    )

    length = st.slider("리뷰 길이 (글자 수)", min_value=100, max_value=1000, value=300, step=50)
    humanize = st.checkbox("AI 티 안 나게 다듬기", value=True)

    submitted = st.form_submit_button("리뷰 생성하기")

if submitted:
    if not product_name.strip():
        st.warning("상품명을 입력해주세요.")
        st.stop()

    images = [Image.open(f) for f in photos] if photos else []

    page_info = ""
    if product_url.strip():
        try:
            with st.spinner("상품 설명 페이지에서 정보를 가져오는 중..."):
                page_info = fetch_page_text(product_url.strip())
        except Exception as e:
            st.warning(f"URL에서 정보를 가져오지 못했습니다 ({e}). 나머지 정보만으로 리뷰를 생성합니다.")

    with st.spinner("리뷰 초안을 작성하는 중..."):
        draft_prompt = build_draft_prompt(
            product_name, model_no, price, usage_info, page_info, usage_context, length
        )
        draft = call_model([draft_prompt, *images])

    if len(draft) < length * 0.7 or len(draft) > length * 1.3:
        with st.spinner("글자 수를 맞추는 중..."):
            draft = call_model([build_adjust_prompt(draft, length)])

    final_review = draft
    if humanize:
        with st.spinner("자연스럽게 다듬는 중..."):
            final_review = call_model([build_humanize_prompt(draft)], temperature=0.8)

    st.subheader("생성된 리뷰")
    st.text_area("결과", value=final_review, height=250, label_visibility="collapsed")
    st.caption(f"글자 수: {len(final_review)}자 (목표 {length}자)")
