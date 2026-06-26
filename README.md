# JLPT Word Shorts Automation

JLPT 단어/문법 학습용 쇼츠와 풀영상을 생성하고, YouTube 업로드와 Google Drive 백업까지 연결하는 로컬 운영형 Python 프로젝트입니다.

이 저장소는 공개용 코드와 학습 데이터를 정리한 버전입니다.  
실제 업로드에 필요한 OAuth 토큰, 개인 API 키, 생성 결과물은 포함하지 않습니다.

## What This Project Does

- JLPT N1~N5 단어/문법 CSV 기반으로 DAY 학습 세트 구성
- 비즈니스 일본어 단어/표현 세트 별도 운영
- 카드 이미지 생성
- 일본어/한국어 TTS 생성
- 단어별 쇼츠 영상 생성
- DAY 단위 쇼츠 합본 생성
- 레벨별 풀영상 생성
- YouTube 업로드 및 예약 변경
- Google Drive 자동 백업 및 로컬 산출물 정리
- Streamlit 대시보드로 생성/업로드/예약 제어

## Key Features

### 1. Daily Shorts Pipeline

- CSV에서 미사용 항목을 DAY 단위로 선별
- `data/words.json` 생성
- 이미지, 음성, 단어별 영상, DAY 쇼츠, 썸네일 생성
- YouTube 업로드 후 Google Drive 자동 백업
- 백업 성공 시 최종 파일 자동 삭제

### 2. Full Compilation Pipeline

- `DAY001~025` 같은 25일 단위 고정 구간 기반 풀영상 생성
- 풀영상 업로드 후 Google Drive 자동 백업
- 백업 성공 시 풀영상 로컬 파일 자동 삭제

### 3. Streamlit Dashboard

- 생성만 / 업로드만 / 전체 실행 분리
- 업로드 예약 시간 설정
- 기존 예약 영상의 날짜 변경
- 업로드/실행 로그 확인
- 사전 점검 기능 제공

## Project Structure

```text
jlpt_word/
├─ assets/
│  ├─ backgrounds/
│  └─ fonts/
├─ data/
│  ├─ jlpt_n1_vocab.csv
│  ├─ jlpt_n1_grammar.csv
│  ├─ ...
│  ├─ business_japanese_vocab.csv
│  └─ business_japanese_phrases.csv
├─ docs/
│  ├─ PORTFOLIO.md
│  ├─ PROJECT_STRUCTURE.md
│  └─ EXECUTION_FLOW.md
├─ src/
│  ├─ cleanup/
│  ├─ data/
│  ├─ drive/
│  ├─ image/
│  ├─ tts/
│  ├─ video/
│  └─ youtube/
├─ main.py
├─ main_business.py
├─ streamlit_app.py
├─ requirements.txt
```

## Requirements

- Python 3.11 권장
- FFmpeg 사용 가능 환경
- Windows 로컬 운영 기준으로 구성

## Installation

```bash
pip install -r requirements.txt
```

## Environment Setup

`.env.example`을 참고해 `.env` 파일을 생성합니다.

```env
OPENAI_API_KEY=your_openai_api_key
UPLOAD_PUBLISH_AT=
```

## OAuth Files

실제 업로드/백업 기능을 사용하려면 아래 파일이 로컬에 있어야 합니다.

- `client_secret.json`
- `token.json` 또는 실행 중 생성되는 YouTube 인증 토큰
- `drive_token.json` 또는 실행 중 생성되는 Drive 인증 토큰

이 파일들은 공개 저장소에 커밋하면 안 됩니다.

## Run

### Main Pipeline

```bash
python main.py
```

### Business-only Pipeline

```bash
python main_business.py
```

### Streamlit Dashboard

```bash
streamlit run streamlit_app.py
```

## Generated Outputs

실행 중 아래 폴더에 산출물이 생성될 수 있습니다.

- `assets/images/`
- `assets/audio/`
- `output/videos/`
- `output/day_videos/`
- `output/compilations/`
- `output/thumbnails/`

공개 저장소에서는 이 결과물을 기본적으로 제외하는 것을 권장합니다.

## Notes

- 이 프로젝트는 `Streamlit Community Cloud` 같은 경량 호스팅보다, 로컬 PC 또는 전용 서버 운영에 더 적합합니다.
- YouTube/Google Drive 인증은 Google Cloud 프로젝트 설정에 따라 달라질 수 있습니다.
- 업로드 자동화 기능을 사용하기 전, API 활성화와 OAuth 설정을 먼저 확인해야 합니다.

## Additional Docs

- [docs/PORTFOLIO.md](docs/PORTFOLIO.md)
- [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)
- [docs/EXECUTION_FLOW.md](docs/EXECUTION_FLOW.md)
