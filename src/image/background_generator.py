# ==================================================
# 파일명: background_generator.py
# 역할: 이미지 프롬프트를 이용해 AI 배경 이미지를 생성하고 저장하는 모듈
# ==================================================


# ==================================================
# 1. 라이브러리 import 섹션
# ==================================================

import os
import base64

from dotenv import load_dotenv
from openai import OpenAI

from src.image.prompt_generator import generate_image_prompt
from src.utils.filename_utils import normalize_romaji_filename

# ==================================================
# 2. OpenAI 설정 섹션
# ==================================================

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)


# ==================================================
# 3. 배경 이미지 저장 폴더 설정 섹션
# ==================================================

background_folder = "assets/backgrounds"


if not os.path.exists(background_folder):
    os.makedirs(background_folder)
    
    
# ==================================================
# 4. 배경 이미지 생성 함수 섹션
# ==================================================

# - 이미지 프롬프트를 받는다.
# - 저장할 경로를 받는다.
# - 이미지 프롬프트가 없으면 중단한다.
# - OpenAI 이미지 생성 API에 요청한다.
# - 생성된 이미지 URL을 꺼낸다.
# - URL에서 이미지를 다운로드한다.
# - 다운로드한 이미지 데이터를 저장경로에 저장한다.
# - 저장경로를 반환한다.


def generate_background_image(image_prompt, save_path):

    if not image_prompt:
        print("이미지 프롬프트가 없습니다.")

        return ""

    try:
        response = client.images.generate(
            model="gpt-image-1",
            prompt=image_prompt,
            size="1024x1536",
            n=1
        )

        image_base64 = response.data[0].b64_json

        image_bytes = base64.b64decode(image_base64)

        with open(save_path, "wb") as file:
            file.write(image_bytes)

        print("배경 이미지 저장 완료:", save_path)

        return save_path


    except Exception as error:
        print("배경 이미지 생성 중 오류가 발생했습니다.")
        print(error)

        return ""


# ==================================================
# 5. 테스트 실행 섹션
# ==================================================

# - 이 파일을 직접 실행했을 때만 테스트한다.
# - 테스트용 이미지 프롬프트를 만든다.
# - 테스트용 저장 경로를 만든다.
# - 배경 이미지 생성 함수를 실행한다.


if __name__ == "__main__":

    current_word = {
        "word": "学校",
        "hiragana": "がっこう",
        "meaning": "학교",
        "romaji": "gakkou"
    }
    prompt = generate_image_prompt(current_word)
    save_path = os.path.join(
        background_folder,
        normalize_romaji_filename(current_word["romaji"]) + ".png"
    )

    generate_background_image(prompt, save_path)
