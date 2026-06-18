# ==================================================
# 파일명: prompt_generator.py
# 역할: JLPT 단어에 어울리는 AI 이미지 생성 프롬프트 생성 모듈
# ==================================================


# ==================================================
# 1. 라이브러리 import 섹션
# ==================================================

# 운영체제 환경변수와 파일 경로를 다루는 도구
import os

# .env 파일에 저장된 API 키를 불러오는 도구
from dotenv import load_dotenv

# OpenAI API를 사용하기 위한 도구
from openai import OpenAI


# ==================================================
# 2. 환경변수 및 OpenAI 클라이언트 설정 섹션
# ==================================================

# .env 파일에 있는 환경변수들을 프로그램 안으로 불러온다
load_dotenv()

# OPENAI_API_KEY 값을 가져온다
api_key = os.getenv("OPENAI_API_KEY")

# API 키가 없으면 안내 메시지를 출력한다
if not api_key:
    print("OPENAI_API_KEY가 설정되어 있지 않습니다. .env 파일을 확인해주세요.")

# OpenAI API를 사용할 클라이언트를 만든다
client = OpenAI(
    api_key=api_key
)

IMAGE_HINTS = {
    "根拠": "a lawyer or office worker carefully reviewing evidence documents on a desk",
    "促進": "a realistic team meeting where coworkers are actively pushing a project forward",
    "概念": "a teacher explaining an idea to students in a realistic classroom",
    "妥協": "two East Asian business people calmly negotiating and reaching an agreement at a meeting table, realistic office scene",
    "信頼": "two coworkers shaking hands with mutual trust in a realistic office",
    "配慮": "a person kindly helping an elderly person in daily life",
    "判断": "a manager carefully reviewing reports and making a decision",
    "説得": "a person explaining a proposal to another person in a meeting room",
    "支援": "volunteers helping someone in a realistic community setting",
    "貢献": "people working together for a community project",
    "矛盾": "two people noticing conflicting information in documents during a meeting",
    "措置": "official workers taking practical action after reviewing a situation",
    "推測": "a researcher analyzing clues and documents to infer a conclusion",
    "遂行": "a professional completing an important task step by step",
}

# ==================================================
# 3. 단어 정보 검증 함수 섹션
# ==================================================

# - 단어 데이터에 word, hiragana, meaning 값이 있는지 확인한다.
# - 필요한 값이 부족하면 False를 반환한다.
# - 필요한 값이 모두 있으면 True를 반환한다.


def validate_word_data(current_word):
    word = current_word.get("word", "")
    hiragana = current_word.get("hiragana", "")
    meaning = current_word.get("meaning", "")

    if not word:
        print("word 값이 없습니다.")
        return False

    if not hiragana:
        print("hiragana 값이 없습니다.")
        return False

    if not meaning:
        print("meaning 값이 없습니다.")
        return False

    return True


# ==================================================
# 4. LLM에게 전달할 요청문 생성 함수 섹션
# ==================================================

# - JLPT 단어 데이터를 받는다.
# - word, hiragana, meaning 값을 꺼낸다.
# - 이미지 생성 프롬프트를 만들기 위한 요청문을 만든다.
# - 이미지 안에는 글자나 로고가 들어가지 않도록 요청한다.


def build_prompt_request(current_word):
    item_type = current_word.get("type", "vocab")
    word = current_word.get("word", "")
    hiragana = current_word.get("hiragana", "")
    meaning = current_word.get("meaning", "")
    image_hint = IMAGE_HINTS.get(word, "")

    if item_type == "grammar":
        prompt_request = f"""
Create one English image generation prompt for a JLPT N1 grammar short-form video.

Grammar pattern: {word}
Reading: {hiragana}
Korean meaning: {meaning}

Rules:
- Output only one English image prompt.
- Do not explain anything.
- Do not include markdown.
- The image must NOT contain any text, letters, Japanese characters, Korean characters, captions, signs, logos, or watermarks.
- Do not write the grammar pattern inside the image.
- The image should visually symbolize the meaning or usage of the grammar pattern.
- If the grammar is abstract, represent it as a clear symbolic situation.
- Use scenes such as paths, steps, choices, comparison, evidence, rules, documents, progress, relationships, cause and effect, or sequence when appropriate.
- The image must work as a soft background behind large vocabulary text.
- Keep the center area clean and uncluttered for text overlay.
- Use a clean, minimal, educational, calm Japanese study atmosphere.
- Use soft cinematic lighting.
- Use vertical 9:16 composition.
- Avoid overly complex details.
- Avoid scary, violent, political, religious, or copyrighted imagery.
Image hint: {image_hint}

Important visual style rules:
- Create ultra realistic photography only.
- Use real people, real places, real objects, and realistic human actions.
- Do not create illustrations, anime, cartoons, 3D renders, CGI, fantasy art, surreal art, abstract art, symbolic sculptures, icons, diagrams, or impossible objects.
- If the grammar pattern is abstract, represent it through a realistic human situation or action.
- The scene must look like something that could exist in real life.

People and location rules:
- Use East Asian people only, preferably Japanese or Korean people.
- Do not use Western people.
- Use realistic Japanese or Korean environments.
- Use modern Japanese classrooms, offices, homes, libraries, streets, or meeting rooms.

"""

    else:
        prompt_request = f"""
Create one English image generation prompt for a JLPT N1 vocabulary short-form video.

Japanese word: {word}
Reading: {hiragana}
Korean meaning: {meaning}

Rules:
- Output only one English image prompt.
- Do not explain anything.
- Do not include markdown.
- The image must NOT contain any text, letters, Japanese characters, Korean characters, captions, signs, logos, or watermarks.
- Do not write the word itself inside the image.
- The image must visually represent the meaning of the word.
- If the word is concrete, show a clear object, place, person, or action.
- If the word is abstract, do NOT try to draw the word literally.
- For abstract words,create a realistic human situation that represents the meaning.

Show people interacting, working,
studying, helping, discussing,
teaching, deciding, or cooperating.

Never use symbolic objects,
abstract sculptures,
floating geometric shapes,
or conceptual artwork.
- Examples:
  - promotion / facilitation: a small plant growing, an upward path, progress arrows without text
  - basis / evidence: documents, research papers, a desk with evidence materials, a magnifying glass
  - compromise: two people calmly shaking hands across a table
  - concept: a notebook with abstract shapes, a person organizing ideas, soft lightbulb-like inspiration without text
  - contradiction: two opposite paths, conflicting puzzle pieces, balanced opposing ideas
- The image must work as a soft background behind large vocabulary text.
- Keep the center area clean and uncluttered for text overlay.
- Use a clean, minimal, educational, calm Japanese study atmosphere.
- Use soft cinematic lighting.
- Use vertical 9:16 composition.
- Avoid overly complex details.
- Avoid scary, violent, political, religious, or copyrighted imagery.
-Image hint: {image_hint}

Important visual style rules:
- Create ultra realistic photography only.
- Use real people, real places, real objects, and realistic human actions.
- Do not create illustrations, anime, cartoons, 3D renders, CGI, fantasy art, surreal art, abstract art, symbolic sculptures, icons, diagrams, or impossible objects.
- If the word is abstract, represent it through a realistic human situation or action.
- The scene must look like something that could exist in real life.
- Prefer realistic Japanese classrooms, offices, homes, streets, libraries, meeting rooms, or daily life situations.

People and location rules:
- Use East Asian people only, preferably Japanese or Korean people.
- Do not use Western people.
- Use realistic Japanese or Korean environments.
- Use modern Japanese classrooms, offices, homes, libraries, streets, or meeting rooms.

"""

    return prompt_request


# ==================================================
# 5. 이미지 프롬프트 정리 함수 섹션
# ==================================================

# - LLM이 만든 결과물의 앞뒤 공백을 제거한다.
# - 혹시 따옴표로 감싸져 있으면 제거한다.
# - 줄바꿈이 많으면 한 줄 문장처럼 정리한다.


def clean_image_prompt(image_prompt):
    cleaned_prompt = image_prompt.strip()

    cleaned_prompt = cleaned_prompt.replace("\n", " ")

    cleaned_prompt = cleaned_prompt.replace("  ", " ")

    if cleaned_prompt.startswith('"') and cleaned_prompt.endswith('"'):
        cleaned_prompt = cleaned_prompt[1:-1]

    if cleaned_prompt.startswith("'") and cleaned_prompt.endswith("'"):
        cleaned_prompt = cleaned_prompt[1:-1]

    return cleaned_prompt


# ==================================================
# 6. 이미지 프롬프트 생성 함수 섹션
# ==================================================

# - 단어 데이터 1개를 받는다.
# - 단어 데이터가 올바른지 확인한다.
# - LLM에게 전달할 요청문을 만든다.
# - OpenAI API로 이미지 프롬프트 생성을 요청한다.
# - 생성된 프롬프트를 정리해서 반환한다.


def generate_image_prompt(current_word):
    is_valid = validate_word_data(current_word)

    if not is_valid:
        return ""

    prompt_request = build_prompt_request(current_word)

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {
                    "role": "system",
                    "content": """
You are an expert prompt writer for AI image generation.
You create concise, visual, high-quality English prompts.
Your output must be only one prompt sentence or one compact prompt paragraph.
Do not include markdown.
Do not include explanations.
Do not include quotation marks.
"""
                },
                {
                    "role": "user",
                    "content": prompt_request
                }
            ]
        )

        image_prompt = response.choices[0].message.content

        cleaned_prompt = clean_image_prompt(image_prompt)

        return cleaned_prompt

    except Exception as error:
        print("이미지 프롬프트 생성 중 오류가 발생했습니다.")
        print(error)

        return ""


# ==================================================
# 7. 단독 테스트 실행 섹션
# ==================================================

# - 이 파일을 직접 실행했을 때만 테스트한다.
# - 단어를 넣어서 이미지 프롬프트가 생성되는지 확인한다.


if __name__ == "__main__":
    test_word = {
        "type": "vocab",
        "word": "根拠",
        "hiragana": "こんきょ",
        "meaning": "근거",
        "romaji": "konkyo"
    }

    image_prompt = generate_image_prompt(test_word)

    print("생성된 이미지 프롬프트:")
    print(image_prompt)