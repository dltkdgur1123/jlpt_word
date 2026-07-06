# JLPT 생성봇 Telegram 연결

이 문서는 `bot_server.py`를 사용해 현재 JLPT 쇼츠 자동화 파이프라인을 Telegram 봇으로 실행하는 방법입니다.

## 1. 사용자가 해야 하는 일

1. Telegram에서 `@BotFather`를 엽니다.
2. `/newbot`으로 새 봇을 만듭니다.
3. 봇 이름은 예를 들어 `JLPT생성봇`으로 지정합니다.
4. BotFather가 발급한 Bot Token을 복사합니다.
5. 새 봇을 사용할 그룹방에 초대합니다.

## 2. `.env`에 추가할 값

프로젝트 루트의 `.env`에 아래 값을 추가합니다.

```env
JLPT_BOT_TOKEN=BotFather에서_받은_토큰
JLPT_BOT_ALLOWED_CHAT_ID=
JLPT_BOT_POLL_TIMEOUT=30
```

`JLPT_BOT_ALLOWED_CHAT_ID`는 비워두면 모든 채팅에서 반응합니다.  
특정 그룹에서만 쓰려면 해당 그룹의 chat id를 넣으면 됩니다.

## 3. 실행 방법

```bat
run_jlpt_bot.bat
```

또는 직접 실행:

```bash
python bot_server.py
```

## 4. 지원 명령어

- `/menu` 또는 `/start`  
  버튼 메뉴를 엽니다.

  메뉴 흐름:
  1. `N1~N5 전체 생성`
  2. `BUSINESS 생성`
  3. `특정 레벨 선택 생성` → `N1`~`N5` 중 선택
  4. `최신본 예약 업로드` → `N1~N5 전체 최신본` 또는 `BUSINESS 최신본` 선택 → `오전 8시` 또는 `오후 6시` 선택

  예약 업로드 날짜는 `data/uploaded_log.json`의 최신 `publish_at` 기준으로 자동 계산됩니다.  
  예: 최신 예약이 오전이면 다음 오후 후보, 최신 예약이 오후면 다음 날 오전 후보가 표시됩니다.

- `/1`  
  N1~N5 전체를 순서대로 생성합니다.

- `/2 2026-07-01`  
  N1~N5 최신 생성 DAY를 해당 날짜 오전 8시(KST)에 전체 예약 업로드합니다.

- `/3 2026-07-01`  
  N1~N5 최신 생성 DAY를 해당 날짜 오후 6시(KST)에 전체 예약 업로드합니다.

- `/status`  
  현재 N1~N5, BUSINESS의 DAY 상태를 확인합니다.

- `/make N5`  
  해당 JLPT 레벨의 DAY 쇼츠를 생성하고 Telegram으로 영상 전송을 시도합니다.

- `/business`  
  BUSINESS DAY 쇼츠를 생성하고 Telegram으로 영상 전송을 시도합니다.

- `/make all_level`  
  N1~N5 전체를 순서대로 생성합니다.

- `/make_all`  
  기존 호환용 명령어입니다. `/make all_level`과 같습니다.

- `/upload all_level`  
  N1~N5의 최신 생성 DAY를 순서대로 업로드합니다.

- `/upload N5 045`  
  이미 생성된 특정 DAY 영상을 YouTube에 업로드합니다.

- `/upload_at BUSINESS 018 2026-07-01 18:00`  
  한국시간 기준으로 원하는 날짜/시간에 예약 업로드합니다.

- `/upload_at all_level 2026-07-01 18:00`  
  N1~N5 최신 생성 DAY를 한국시간 기준 원하는 날짜/시간에 전체 예약 업로드합니다.

- `/upload_morning BUSINESS 018 2026-07-01`  
  한국시간 기준 오전 8시에 예약 업로드합니다.

- `/upload_evening BUSINESS 018 2026-07-01`  
  한국시간 기준 오후 6시에 예약 업로드합니다.

- `/upload_morning all_level 2026-07-01`  
  N1~N5 최신 생성 DAY를 한국시간 기준 오전 8시에 전체 예약 업로드합니다.

- `/upload_evening all_level 2026-07-01`  
  N1~N5 최신 생성 DAY를 한국시간 기준 오후 6시에 전체 예약 업로드합니다.

- `/finalize N5 045`  
  업로드 완료된 DAY 산출물을 Google Drive에 백업하고 로컬 중간 산출물을 정리합니다.

## 5. 주의사항

- 생성/업로드 작업은 동시에 하나만 실행됩니다.
- `.env`, `token.json`, `drive_token.json`, `client_secret.json`은 외부에 공유하면 안 됩니다.
- `/make`는 생성만 수행합니다. YouTube 업로드까지 하려면 `/upload`, `/upload_at`, `/upload_morning`, `/upload_evening`을 별도로 실행합니다.
- Telegram 전송 제한 때문에 영상이 너무 크면 전송이 실패할 수 있습니다. 이 경우 로컬 output 폴더에서 확인하면 됩니다.
