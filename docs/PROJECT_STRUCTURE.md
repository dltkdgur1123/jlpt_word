# 프로젝트 구조

## 폴더 구조
```text
jlpt_word/
├─ main.py
├─ upload_tiktok_only.py
├─ requirements.txt
├─ docs/
├─ assets/
│  ├─ audio/
│  ├─ backgrounds/
│  ├─ fonts/
│  └─ images/
├─ data/
│  ├─ day_status.json
│  ├─ uploaded_log.json
│  ├─ words.json
│  ├─ translation_cache.json
│  ├─ source_data.csv
│  ├─ jlpt_n1_vocab.csv ~ jlpt_n5_vocab.csv
│  ├─ jlpt_n1_grammar.csv ~ jlpt_n5_grammar.csv
│  └─ raw_vocab/
├─ output/
│  ├─ videos/
│  ├─ day_videos/
│  ├─ compilations/
│  └─ thumbnails/
└─ src/
   ├─ data/
   ├─ image/
   ├─ tiktok/
   ├─ tts/
   ├─ video/
   └─ youtube/
```

## 최상위 파일
### `main.py`
- 전체 자동 생성 파이프라인 진입점
- 레벨별 DAY 조회, 데이터 선택, 이미지 생성, TTS 생성, 쇼츠 생성, DAY 영상 생성, 썸네일 생성, YouTube 업로드까지 순차 실행

### `upload_tiktok_only.py`
- 이미 생성된 DAY 영상을 TikTok에만 업로드하는 보조 실행 파일
- 전체 생성 파이프라인과 업로드 채널을 분리할 때 사용

### `requirements.txt`
- 영상 처리, TTS, 브라우저 자동화, YouTube API, AI 연동에 필요한 패키지 목록

## `assets/`
### `assets/audio/`
- 일본어 TTS, 한국어 TTS 결과 mp3 저장
- 파일명 규칙: `{romaji}_jp.mp3`, `{romaji}_kr.mp3`

### `assets/backgrounds/`
- 카드 이미지와 썸네일 제작용 배경 이미지 저장
- 레벨별 썸네일 배경과 기본 카드 배경 포함

### `assets/fonts/`
- 일본어, 한국어, 썸네일용 폰트 보관

### `assets/images/`
- 단어 카드 형태의 세로형 이미지 출력 경로
- 파일명 규칙: `{romaji}.png`

## `data/`
### `day_status.json`
- JLPT 레벨별 현재 DAY 번호 저장
- 다음 실행 시 어떤 일차를 생성할지 결정하는 기준 상태 파일

### `uploaded_log.json`
- YouTube 업로드 완료 여부 기록
- 키 형식 예시: `N4_DAY_025`

### `words.json`
- 당일 생성 대상이 되는 단어/문법 목록
- 이미지, TTS, 쇼츠 생성의 공통 입력 파일

### `jlpt_n*_vocab.csv`
- 레벨별 단어 원본 및 운영 데이터
- `score`, `used`, `day` 컬럼으로 우선순위와 사용 이력을 함께 관리
- `raw_vocab/`의 원천 데이터와 맞물려 현재 vocab 규모를 유지하는 기준 데이터

### `jlpt_n*_grammar.csv`
- 레벨별 문법 데이터
- 단어 CSV와 같은 방식으로 운영
- 현재는 레벨별 문법 풀이 확장된 상태이며, 영상 학습용 한국어 뜻으로 정리되어 있음

### `translation_cache.json`
- 번역 또는 의미 가공 과정에서 재사용 가능한 캐시 데이터 저장

### `source_data.csv`
- 외부 참고 사이트에서 수집한 출처 데이터 저장

### `raw_vocab/`
- 가공 이전 원본 단어 CSV 보관
- vocab CSV 확장의 기준이 되는 원천 데이터

## `output/`
### `output/videos/`
- 단어별 개별 쇼츠 mp4 저장
- 파일명 규칙: `{romaji}.mp4`

### `output/day_videos/`
- 하루치 단어/문법 영상을 이어 붙인 DAY 영상 저장
- 파일명 규칙: `{LEVEL}_DAY_{NNN}.mp4`

### `output/compilations/`
- 여러 DAY를 합친 레벨별 풀영상 저장
- 파일명 규칙: `{LEVEL}_DAY_{START}_{END}_FULL.mp4`

### `output/thumbnails/`
- DAY 썸네일 저장
- 하위 `level/` 폴더에는 풀영상 썸네일 저장

## `src/data/`
### `day_manager.py`
- 레벨별 DAY 상태 조회 및 증가 처리

### `word_manager.py`
- `words.json` 로드, 저장, 초기화, 중복 검사 담당

### `jlpt_word_provider.py`
- 레벨별 CSV에서 미사용 단어/문법을 골라 하루치 학습 세트를 구성
- 현재 설정 기준 단어 5개, 문법 2개를 선택

### `meaning_cleaner.py`
- 단어 CSV의 뜻 텍스트를 정리하고 표기 노이즈를 제거

### `source_collector.py`
- 외부 참고 사이트에서 단어/문법 출처 후보를 수집해 CSV로 저장

### `grammar_data_builder.py`
- 레벨별 문법 CSV를 생성하거나 갱신하는 데이터 구축 보조 모듈

### 그 외 데이터 유틸
- `csv_validator.py`, `frequency_score_builder.py`, `vocab_meaning_translator.py` 등 데이터 검증과 가공용 모듈 포함

## `src/image/`
### `image_generator.py`
- `words.json` 기반 카드 이미지 생성
- 일본어 표기, 히라가나, 한국어 뜻, 레벨 텍스트를 세로형 레이아웃으로 출력

### `thumbnail_generator.py`
- DAY 영상용 YouTube 썸네일 생성

### `level_thumbnail_generator.py`
- 풀영상용 썸네일 생성

### `prompt_generator.py`
- 단어/문법 의미에 맞는 AI 이미지 프롬프트 생성

### `background_generator.py`
- OpenAI 이미지 API를 사용해 배경 이미지를 생성하는 보조 모듈

## `src/tts/`
### `tts_generator.py`
- Edge TTS를 사용해 일본어/한국어 음성을 생성
- `words.json`의 각 항목을 순회하며 mp3 생성

## `src/video/`
### `video_generator.py`
- 카드 이미지와 일본어/한국어 TTS를 결합해 단어별 쇼츠 영상 생성

### `video_batch_generator.py`
- `words.json` 전체 항목에 대해 단어별 영상을 일괄 생성

### `day_video_generator.py`
- 단어별 mp4를 이어 붙여 DAY 영상을 생성

### `level_compilation_generator.py`
- DAY 영상 여러 개를 이어 붙여 레벨별 풀영상을 생성

## `src/youtube/`
### `youtube_uploader.py`
- YouTube OAuth 로그인
- 영상 업로드
- 썸네일 등록
- 예약 공개 시간 계산
- 레벨별 재생목록 자동 등록

### `upload_log.py`
- `uploaded_log.json` 읽기/쓰기 담당
- 중복 업로드 방지에 사용

### `compilation_uploader.py`
- 풀영상 업로드 전용 모듈

## `src/tiktok/`
### `tiktok_uploader.py`
- Playwright 기반 TikTok 업로드 자동화
- 로그인 세션을 브라우저 프로필 디렉터리에 유지하는 방식

## 구조적 특징 요약
- 실행 파이프라인과 데이터 관리 모듈이 분리되어 있다.
- 입력 데이터, 생성 자산, 배포 결과가 폴더 기준으로 명확히 구분된다.
- 쇼츠와 풀영상이 같은 원천 데이터에서 파생되도록 설계되어 재사용성이 높다.
