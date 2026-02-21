"""Simple two-language (ko/en) translation helper."""

_STRINGS: dict[str, dict[str, str]] = {
    "page_title": {
        "ko": "그날 밤하늘",
        "en": "ThatNightSky",
    },
    "label_place": {
        "ko": "장소",
        "en": "Location",
    },
    "label_date": {
        "ko": "날짜",
        "en": "Date",
    },
    "label_time": {
        "ko": "시각",
        "en": "Time",
    },
    "label_theme": {
        "ko": "이 날의 의미",
        "en": "Occasion",
    },
    "btn_view_sky": {
        "ko": "✦ 밤하늘보기",
        "en": "✦ View Sky",
    },
    "btn_edit": {
        "ko": "다시 입력하기",
        "en": "Edit",
    },
    "btn_save": {
        "ko": "저장하기",
        "en": "Save",
    },
    "btn_confirm": {
        "ko": "확인",
        "en": "Confirm",
    },
    "placeholder": {
        "ko": "장소와 날짜를 입력하고 밤하늘을 불러오세요",
        "en": "Enter a location and date to see the night sky",
    },
    "loading_compute": {
        "ko": "✦ 밤하늘을 계산하는 중",
        "en": "✦ Computing the night sky",
    },
    "loading_narrative": {
        "ko": "✦ 그날 밤하늘을 기억하는 중",
        "en": "✦ Remembering that night",
    },
    "error_address": {
        "ko": "주소를 찾을 수 없어요. 띄어쓰기를 포함해서 입력해보세요. ({error})",
        "en": "Address not found. Try a more specific address. ({error})",
    },
    "narrative_limit": {
        "ko": "이 세션에서 최대 3회 이야기를 생성했어요. 새 탭에서 다시 시작할 수 있습니다.",
        "en": "You've reached the 3-narrative limit for this session. Open a new tab to continue.",
    },
    "narrative_fallback": {
        "ko": "그날, 밤, 하늘입니다.",
        "en": "That night. The sky.",
    },
    "privacy_title": {
        "ko": "개인정보 처리 고지",
        "en": "Privacy Notice",
    },
    "privacy_body": {
        "ko": "입력한 정보는 서비스 제공을 위해 Anthropic에 전송되며,<br>별도로 저장되지 않습니다.<br>서버 운영 로그는 7일 후 자동 삭제됩니다.",
        "en": "Your input is sent to Anthropic solely to generate the narrative.<br>No personal data is stored.<br>Server access logs are automatically deleted after 7 days.",
    },
    "privacy_link": {
        "ko": "Anthropic의 데이터 처리 정책",
        "en": "Anthropic's Privacy Policy",
    },
    "svg_btn_reset": {
        "ko": "↺ 초기화",
        "en": "↺ Reset",
    },
    "svg_btn_save": {
        "ko": "↓ 저장",
        "en": "↓ Save",
    },
    "svg_filename": {
        "ko": "그날밤하늘.png",
        "en": "that-night-sky.png",
    },
}


def t(key: str, lang: str) -> str:
    """Return the translated string for key in lang.

    Falls back to 'en', then to the key itself if not found.
    """
    entry = _STRINGS.get(key)
    if entry is None:
        return key
    return entry.get(lang) or entry.get("en") or key
