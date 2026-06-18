# JLPT Auto Shorts

JLPT 단어와 문법 데이터를 기반으로 학습용 숏폼 영상을 자동 생성하고, DAY 단위 영상과 레벨별 풀영상까지 확장해 YouTube 업로드로 연결하는 Python 자동화 프로젝트입니다.

## Overview

- 레벨별 JLPT 단어/문법 CSV를 기반으로 하루치 학습 세트를 자동 구성
- 카드 이미지, 일본어/한국어 TTS, 단어별 쇼츠, DAY 영상, 썸네일까지 순차 생성
- YouTube Data API를 사용해 DAY 영상 업로드 및 재생목록 등록 자동화
- DAY 영상 여러 개를 합친 풀영상 생성 및 업로드 구조 지원
- TikTok 업로드용 Playwright 자동화 모듈 별도 구성

## Pipeline

1. `data/day_status.json`에서 현재 DAY 번호 조회
2. 레벨별 CSV에서 미사용 단어 5개, 문법 2개 선별
3. `data/words.json` 생성
4. 카드 이미지 생성
5. 일본어/한국어 TTS 생성
6. 단어별 쇼츠 mp4 생성
7. DAY 영상 생성
8. DAY 썸네일 생성
9. YouTube 업로드 및 업로드 로그 저장
10. DAY 번호 증가

## Project Docs

- [docs/PORTFOLIO.md](docs/PORTFOLIO.md)
- [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)
- [docs/EXECUTION_FLOW.md](docs/EXECUTION_FLOW.md)

## Tech Stack

- Python
- Pillow
- MoviePy
- Edge TTS
- Google YouTube Data API
- Playwright
- Requests / BeautifulSoup
- OpenAI API
- CSV / JSON

## Directory

```text
jlpt_word/
├─ main.py
├─ upload_tiktok_only.py
├─ assets/
├─ data/
├─ docs/
├─ output/
└─ src/
```

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment variables

Create a local `.env` file based on `.env.example`.

```env
OPENAI_API_KEY=your_openai_api_key
YOUTUBE_API_KEY=your_google_oauth_client_id
```

### 3. Prepare OAuth files locally

The following files are required for actual YouTube upload, but must not be committed:

- `client_secret.json`
- `token.json`
- `.env`

## Run

### Main pipeline

```bash
python main.py
```

### TikTok upload only

```bash
python upload_tiktok_only.py
```

## Output

- `assets/images/`: generated card images
- `assets/audio/`: generated Japanese/Korean TTS
- `output/videos/`: word-level short videos
- `output/day_videos/`: DAY compilation videos
- `output/compilations/`: full compilation videos
- `output/thumbnails/`: thumbnails

## Notes

- 이 저장소에는 민감한 인증 파일, 토큰, 대용량 생성 산출물을 포함하지 않는 것을 권장합니다.
- 실제 업로드 기능을 사용하기 전에는 Google OAuth 클라이언트와 YouTube 채널 권한 설정이 필요합니다.
