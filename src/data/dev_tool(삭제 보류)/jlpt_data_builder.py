# ==================================================
# 파일명: jlpt_data_builder.py
# 역할: JLPT N1~N5 단어/문법 CSV 생성기를 한 번에 실행하는 통합 모듈
# ==================================================


# ==================================================
# 1. 라이브러리 import 섹션
# ==================================================

from src.data.vocab_data_builder import build_all_vocab_csv
from src.data.grammar_data_builder import build_all_grammar_csv


# ==================================================
# 2. 전체 JLPT 데이터 생성 함수 섹션
# ==================================================

def build_all_jlpt_data():
    print("JLPT 단어 CSV 생성을 시작합니다.")
    build_all_vocab_csv()
    print("JLPT 단어 CSV 생성 완료")

    print("JLPT 문법 CSV 생성을 시작합니다.")
    build_all_grammar_csv()
    print("JLPT 문법 CSV 생성 완료")

    print("전체 JLPT 데이터 생성 완료")


# ==================================================
# 3. 테스트 실행 섹션
# ==================================================

if __name__ == "__main__":
    build_all_jlpt_data()