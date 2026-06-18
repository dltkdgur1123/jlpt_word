# JLPT 자동 쇼츠 프로젝트

## 프로젝트 개요
이 프로젝트는 JLPT 단어와 문법 데이터를 기반으로 학습용 쇼츠 영상을 자동 생성하고, DAY 단위 영상과 풀영상까지 확장해 YouTube 업로드까지 연결하는 Python 자동화 프로젝트다.

핵심 목표는 다음과 같다.
- JLPT 레벨별 학습 콘텐츠를 매일 일정량 자동 생성
- 텍스트 데이터를 이미지, 음성, 영상 자산으로 변환
- 쇼츠 영상과 DAY 묶음 영상, 레벨별 풀영상을 일관된 규칙으로 생성
- YouTube 업로드와 업로드 이력 관리까지 자동화

## 포트폴리오 관점의 핵심 포인트
- 데이터 선택, 이미지 생성, TTS 생성, 영상 합성, 썸네일 생성, 업로드를 하나의 파이프라인으로 연결했다.
- `data/day_status.json`, `data/uploaded_log.json`을 사용해 일차 진행 상태와 업로드 이력을 분리 관리한다.
- 쇼츠 1개 생성에 그치지 않고 `단어별 영상 -> DAY 영상 -> 25일 단위 풀영상`으로 확장되는 구조를 갖는다.
- YouTube는 API 기반 자동 업로드, TikTok은 Playwright 기반 브라우저 자동화로 채널 특성에 맞게 분리 설계했다.
- 단어 데이터는 원천 CSV와 동기화된 상태로 운영하고, 문법 데이터는 레벨별로 꾸준히 확장할 수 있게 설계했다.

## 데이터 규모
- 단어 CSV는 `N1 2699 / N2 1906 / N3 2140 / N4 668 / N5 718` 수준으로 운영된다.
- 문법 CSV는 현재 `N1 101 / N2 96 / N3 126 / N4 112 / N5 117`로 확장되어 있다.
- `raw_vocab`와 본문 vocab CSV는 같은 기준으로 맞춰져 있어, 학습 데이터와 생성 데이터의 연결이 일관적이다.

## 자동화 범위
### 1. 학습 데이터 운영
- JLPT 레벨별 단어/문법 CSV 관리
- 미사용 항목 선별
- 당일 학습 대상 `words.json` 구성
- DAY 번호 증가 및 상태 저장
- 문법 데이터와 단어 데이터를 학습용 한국어 표현으로 정리

### 2. 콘텐츠 생성
- 단어 카드 이미지 생성
- 일본어/한국어 TTS 생성
- 단어별 쇼츠 영상 생성
- DAY 단위 묶음 영상 생성
- 썸네일 생성

### 3. 배포 자동화
- YouTube 쇼츠 업로드
- 재생목록 자동 등록
- 업로드 이력 저장
- TikTok 업로드 보조 자동화
- 25일 단위 풀영상 업로드

## 전체 실행 흐름 요약
1. 현재 JLPT 레벨의 DAY 번호를 조회한다.
2. CSV에서 아직 사용하지 않은 단어 5개와 문법 2개를 선택해 `words.json`을 구성한다.
3. 선택된 항목을 기반으로 카드 이미지를 만든다.
4. 일본어/한국어 TTS 음성을 생성한다.
5. 이미지와 음성을 합쳐 단어별 쇼츠 영상을 만든다.
6. 단어별 영상을 이어 붙여 DAY 영상을 만든다.
7. DAY 썸네일을 생성한다.
8. YouTube에 업로드하고 재생목록에 등록한다.
9. 업로드 완료 후 DAY 번호를 증가시킨다.

## YouTube 자동 업로드 구조
- `src/youtube/youtube_uploader.py`가 OAuth 로그인, 업로드, 썸네일 등록, 예약 공개 시간 계산, 재생목록 등록을 담당한다.
- `data/uploaded_log.json`을 기준으로 이미 업로드한 DAY는 중복 업로드하지 않는다.
- 레벨별 재생목록 ID를 분리해 업로드 후 자동 분류한다.

## 풀영상 생성 및 업로드 구조
- `src/video/level_compilation_generator.py`가 DAY 영상 여러 개를 합쳐 레벨별 풀영상을 만든다.
- `src/image/level_thumbnail_generator.py`가 풀영상 전용 썸네일을 만든다.
- `src/youtube/compilation_uploader.py`가 풀영상을 일반 영상 형태로 업로드한다.
- 기본 파일 규칙은 `N1_DAY_001_025_FULL.mp4` 같은 형식이다.

## 기술 스택
- Language: Python
- Media Processing: MoviePy, Pillow, ffmpeg-python, OpenCV, NumPy
- TTS: Edge TTS
- Web/API: Google YouTube Data API, Requests, BeautifulSoup
- Browser Automation: Playwright
- AI 활용: OpenAI API 기반 이미지 프롬프트 및 배경 이미지 생성 보조 모듈
- Data Storage: CSV, JSON
- Auth/Config: python-dotenv, OAuth client credentials

## 포트폴리오용 요약 문장
- JLPT 학습용 숏폼 콘텐츠를 데이터 선별부터 영상 생성, 썸네일 제작, YouTube 업로드까지 자동화한 Python 기반 콘텐츠 파이프라인 프로젝트.
- 단어/문법 CSV를 일차별 학습 세트로 구성하고, 이미지·음성·영상 자산을 조합해 쇼츠와 풀영상을 함께 운영하는 자동 제작 시스템.
- 교육용 콘텐츠 제작 흐름을 파일 단위 상태 관리와 업로드 이력 관리까지 포함해 운영 가능한 형태로 구현한 자동화 프로젝트.

## 함께 보면 좋은 문서
- `docs/PROJECT_STRUCTURE.md`
- `docs/EXECUTION_FLOW.md`
