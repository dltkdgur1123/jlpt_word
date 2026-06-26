import os
import re
import unicodedata


INVALID_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|()\[\]{}~～`\'“”‘’\s]+')
NON_SAFE_CHARS = re.compile(r"[^0-9A-Za-z._-]+")
UNDERSCORE_RUN = re.compile(r"_+")


def normalize_romaji_filename(romaji, default="item"):
    """
    romaji 값을 파일명으로 안전하게 바꿉니다.

    원본 romaji 데이터는 유지하고, 파일명을 만들 때만 정규화합니다.
    """

    if romaji is None:
        return default

    filename = unicodedata.normalize("NFKC", str(romaji)).strip().lower()

    if not filename:
        return default

    filename = INVALID_FILENAME_CHARS.sub("_", filename)
    filename = NON_SAFE_CHARS.sub("_", filename)
    filename = UNDERSCORE_RUN.sub("_", filename)
    filename = filename.strip("._- ")

    return filename or default


def resolve_romaji_file_path(folder, romaji, extension):
    """
    정규화된 파일명을 우선 찾고, 기존 느슨한 파일명도 뒤이어 찾습니다.
    """

    candidates = []

    raw_text = "" if romaji is None else str(romaji).strip()
    raw_nfkc_text = unicodedata.normalize("NFKC", raw_text).strip()

    normalized = normalize_romaji_filename(raw_text)
    legacy_space_underscored = raw_nfkc_text.replace(" ", "_").lower()
    legacy_space_removed = raw_nfkc_text.replace(" ", "").lower()
    legacy_tilde_fullwidth = raw_nfkc_text.replace("~", "～").replace(" ", "").lower()
    legacy_tilde_ascii = raw_nfkc_text.replace("～", "~").replace(" ", "").lower()
    legacy_raw = raw_text
    legacy_nfkc = raw_nfkc_text.lower()
    legacy_raw_space_removed = raw_text.replace(" ", "")

    for base_name in (
        normalized,
        legacy_space_underscored,
        legacy_space_removed,
        legacy_tilde_fullwidth,
        legacy_tilde_ascii,
        legacy_raw,
        legacy_nfkc,
        legacy_raw_space_removed,
    ):
        if base_name and base_name not in candidates:
            candidates.append(base_name)

    for base_name in candidates:
        candidate_path = os.path.join(folder, base_name + extension)

        if os.path.exists(candidate_path):
            return candidate_path

    if candidates:
        return os.path.join(folder, candidates[0] + extension)

    return os.path.join(folder, "item" + extension)
