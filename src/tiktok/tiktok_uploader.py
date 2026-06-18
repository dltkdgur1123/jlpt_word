# ==================================================
# 파일명: tiktok_uploader.py
# 역할: output/day_videos 폴더에 있는 DAY 영상을 TikTok에 업로드하는 모듈
# 방식: Playwright 브라우저 자동화
# ==================================================

import os
import time

from playwright.sync_api import sync_playwright

VIDEO_FOLDER = "output/day_videos"
TIKTOK_UPLOAD_URL = "https://www.tiktok.com/upload"
USER_DATA_DIR = "tiktok_browser_profile"


def build_tiktok_caption(level, day):
    caption = (
        f"JLPT {level} 일본어 단어 + 문법 | DAY {day}\n"
        f"#JLPT #{level} #일본어 #일본어공부 #일본어단어 #일본어문법"
    )
    return caption


def build_video_path(level, day):
    filename = f"{level}_DAY_{day}.mp4"
    return os.path.join(VIDEO_FOLDER, filename)


def upload_to_tiktok(video_file, caption):
    if not os.path.exists(video_file):
        print("영상 파일을 찾을 수 없습니다:", video_file)
        return False

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=False
        )

        page = browser.new_page()

        print("TikTok 업로드 페이지로 이동합니다.")
        page.goto(TIKTOK_UPLOAD_URL)

        print("처음 실행이라면 브라우저에서 TikTok 로그인을 완료하세요.")
        print("로그인 후 업로드 화면이 보이면 자동으로 계속 진행됩니다.")

        page.wait_for_timeout(5000)

        try:
            file_input = page.locator("input[type='file']")
            file_input.set_input_files(video_file)
            print("영상 파일 선택 완료:", video_file)

        except Exception as error:
            print("영상 파일 선택 실패")
            print(error)
            browser.close()
            return False

        print("영상 업로드 처리를 기다립니다.")
        page.wait_for_timeout(15000)

        try:
            caption_box = page.locator("[contenteditable='true']").first
            caption_box.click()
            page.keyboard.press("Control+A")
            page.keyboard.type(caption)
            print("캡션 입력 완료")

        except Exception as error:
            print("캡션 입력 실패")
            print(error)

        print("게시 버튼은 TikTok 화면 구조에 따라 자동 클릭이 실패할 수 있습니다.")
        print("화면에서 내용 확인 후 직접 게시 버튼을 눌러도 됩니다.")

        try:
            post_button = page.get_by_text("Post").last
            post_button.click()
            print("게시 버튼 클릭 완료")

        except Exception:
            try:
                post_button = page.get_by_text("게시").last
                post_button.click()
                print("게시 버튼 클릭 완료")
            except Exception as error:
                print("게시 버튼 자동 클릭 실패")
                print("브라우저에서 직접 게시 버튼을 눌러주세요.")
                print(error)

        time.sleep(10)
        browser.close()

    return True


def upload_tiktok_by_level_day(level, day):
    day = str(day).zfill(3)

    video_file = build_video_path(
        level=level,
        day=day
    )

    caption = build_tiktok_caption(
        level=level,
        day=day
    )

    return upload_to_tiktok(
        video_file=video_file,
        caption=caption
    )


if __name__ == "__main__":
    upload_tiktok_by_level_day(
        level="N1",
        day="006"
    )
