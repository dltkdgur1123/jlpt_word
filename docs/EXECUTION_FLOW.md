# 실행 흐름

## 1. 파이프라인 진입
`main.py`가 전체 자동화의 시작점이다.

현재 설정 기준으로 다음 순서로 동작한다.
1. 처리할 JLPT 레벨 목록을 순회한다.
2. 각 레벨의 현재 DAY 번호를 조회한다.
3. 데이터 정리, 콘텐츠 생성, 업로드를 순차 실행한다.

## 2. 데이터 준비 흐름
### 2-1. DAY 상태 조회
- `src/data/day_manager.py`
- `data/day_status.json`에서 현재 레벨의 DAY 번호를 읽는다.
- 예: `N4 -> 26`, `N5 -> 26`

### 2-2. 의미 텍스트 정리
- `src/data/meaning_cleaner.py`
- 레벨별 단어 CSV의 `meaning` 컬럼에서 특수문자, 중복 표현, 불필요한 공백을 정리한다.

### 2-3. 하루치 학습 세트 구성
- `src/data/jlpt_word_provider.py`
- 레벨별 단어 CSV와 문법 CSV를 읽는다.
- `used != true` 인 항목만 필터링한다.
- 점수 기준으로 정렬한 뒤 단어 5개, 문법 2개를 선택한다.
- 선택된 항목을 `data/words.json`에 기록한다.
- 동시에 원본 CSV에는 `used=true`, `day=DAY NNN` 상태를 반영한다.
- 문법과 단어의 `meaning`은 학습용 한국어 표현으로 정리된 데이터를 사용한다.

## 3. 콘텐츠 생성 흐름
### 3-1. 카드 이미지 생성
- `src/image/image_generator.py`
- `data/words.json`을 읽어 세로형 카드 이미지를 생성한다.
- 출력 경로: `assets/images/{romaji}.png`

### 3-2. TTS 생성
- `src/tts/tts_generator.py`
- 각 항목에 대해 일본어 읽기와 한국어 뜻 음성을 생성한다.
- 출력 경로:
  - `assets/audio/{romaji}_jp.mp3`
  - `assets/audio/{romaji}_kr.mp3`

### 3-3. 단어별 쇼츠 생성
- `src/video/video_generator.py`
- 카드 이미지 1장과 일본어/한국어 음성을 결합한다.
- 일본어와 한국어 음성을 반복 연결해 학습형 쇼츠를 만든다.
- 출력 경로: `output/videos/{romaji}.mp4`

### 3-4. 일괄 쇼츠 생성
- `src/video/video_batch_generator.py`
- `words.json` 전체를 순회하며 단어별 영상을 한 번에 생성한다.

## 4. DAY 영상 생성 흐름
### 4-1. DAY 영상 합치기
- `src/video/day_video_generator.py`
- `output/videos/`의 단어별 mp4를 순서대로 읽는다.
- 하나의 DAY 영상으로 결합한다.
- 출력 경로: `output/day_videos/{LEVEL}_DAY_{NNN}.mp4`

### 4-2. DAY 썸네일 생성
- `src/image/thumbnail_generator.py`
- 레벨별 배경을 사용해 DAY 썸네일 생성
- 출력 경로: `output/thumbnails/{LEVEL}_DAY_{NNN}.jpg`

## 5. YouTube 자동 업로드 흐름
### 5-1. 업로드 대상 정보 조립
- `src/youtube/youtube_uploader.py`
- DAY 영상 파일 경로, 썸네일 경로, 제목, 설명, 태그를 구성한다.

### 5-2. 업로드 여부 확인
- `src/youtube/upload_log.py`
- `data/uploaded_log.json`을 확인해 같은 DAY가 이미 업로드됐는지 검사한다.

### 5-3. YouTube API 업로드
- OAuth 인증 후 YouTube Data API로 영상 업로드
- 썸네일 자동 등록
- 레벨별 재생목록 자동 등록
- 예약 공개 시간 계산 지원

### 5-4. 업로드 이력 저장
- 업로드 성공 후 `uploaded_log.json`에 `LEVEL_DAY_NNN` 형식으로 기록한다.

## 6. DAY 상태 갱신
- `src/data/day_manager.py`
- 업로드까지 끝나면 현재 레벨의 DAY 번호를 1 증가시킨다.
- 다음 실행 시 다음 학습 세트를 자동 생성할 수 있게 된다.

## 7. 풀영상 생성 구조
### 7-1. DAY 영상 범위 계산
- 메인 파이프라인에는 25일 단위 묶음을 위한 범위 계산 함수가 포함되어 있다.
- 예: 1~25일, 26~50일 단위로 확장 가능

### 7-2. DAY 영상 결합
- `src/video/level_compilation_generator.py`
- 여러 DAY 영상을 이어 붙여 레벨별 긴 복습 영상을 생성한다.
- 출력 경로: `output/compilations/{LEVEL}_DAY_{START}_{END}_FULL.mp4`

### 7-3. 풀영상 썸네일 생성
- `src/image/level_thumbnail_generator.py`
- 풀영상 범위를 포함한 전용 썸네일 생성
- 출력 경로: `output/thumbnails/level/{LEVEL}_DAY_{START}_{END}_FULL.jpg`

### 7-4. 풀영상 업로드
- `src/youtube/compilation_uploader.py`
- 풀영상 mp4와 썸네일을 일반 YouTube 영상으로 업로드한다.

## 8. 데이터 흐름 요약
```text
JLPT CSV
-> used=false 항목 선별
-> words.json 생성
-> 카드 이미지 생성
-> 일본어/한국어 TTS 생성
-> 단어별 쇼츠 mp4 생성
-> DAY 영상 생성
-> DAY 썸네일 생성
-> YouTube 업로드
-> uploaded_log.json 기록
-> day_status.json 증가
```

## 9. 자동화 범위 정리
- 입력 데이터 관리: CSV, JSON
- 생성 자산: 이미지, mp3, mp4, 썸네일
- 배포 채널: YouTube
- 상태 관리: DAY 번호, 업로드 로그
- 확장 구조: DAY 영상에서 풀영상으로 재가공 가능
- 데이터 보강 구조: 원천 vocab와 문법 CSV를 기반으로 지속 확장 가능
