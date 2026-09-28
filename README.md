# 상품 리뷰 자동 생성기

상품 사진, 모델명, 상품 설명 URL 등의 정보를 입력하면 실제 사용 후기처럼 자연스러운 리뷰를 자동으로 생성하는 Streamlit 앱입니다. Gemini API를 사용합니다.

## 주요 기능

- 상품 사진(여러 장), 상품명, 모델명, 상품 설명 URL(해당 페이지 내용을 자동으로 읽어와 반영), 사용 기간을 입력해 리뷰 생성
- 장점 위주로 작성하되 사소한 단점 1~2가지를 자연스럽게 포함
- 리뷰 길이를 100자~1000자 사이에서 슬라이더로 선택
- "AI 티 안 나게 다듬기" 옵션으로 2차 다듬기 수행 (AI 특유의 상투적 문구·규칙적인 문장 리듬 제거)

## 준비물

- Python 3.10+
- Gemini API 키: https://aistudio.google.com/apikey 에서 발급

## 설치 및 실행

```bash
pip install -r requirements.txt
cp .env.example .env
# .env 파일을 열어 GEMINI_API_KEY 값을 채워넣기
streamlit run app.py
```

## 환경 변수 (.env)

| 변수 | 설명 | 필수 |
| --- | --- | --- |
| `GEMINI_API_KEY` | Gemini API 키 | 예 |
| `GEMINI_MODEL` | 사용할 모델 (기본값: `gemini-2.5-flash`) | 아니오 |

`.env` 파일은 `.gitignore`에 포함되어 있어 저장소에는 올라가지 않습니다.

## 배포

Streamlit Community Cloud 등에 배포할 경우, `.env` 대신 각 플랫폼의 Secrets 설정 화면에 `GEMINI_API_KEY`를 등록하세요.
