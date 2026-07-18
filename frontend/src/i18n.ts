export type Lang = "ko" | "en";

const STRINGS: Record<string, Record<Lang, string>> = {
  page_title: { ko: "그날 밤하늘", en: "ThatNightSky" },
  label_place: { ko: "장소", en: "Location" },
  label_date: { ko: "날짜", en: "Date" },
  label_time: { ko: "시각", en: "Time" },
  label_theme: { ko: "이 날의 의미", en: "Occasion" },
  btn_view_sky: { ko: "✦ 밤하늘보기", en: "✦ View Sky" },
  btn_edit: { ko: "다시 입력하기", en: "Edit" },
  btn_confirm: { ko: "확인", en: "Confirm" },
  placeholder: {
    ko: "장소와 날짜를 입력하고 밤하늘을 불러오세요",
    en: "Enter a location and date to see the night sky",
  },
  loading_compute: { ko: "✦ 밤하늘을 계산하는 중", en: "✦ Computing the night sky" },
  loading_narrative: { ko: "✦ 그날 밤하늘을 기억하는 중", en: "✦ Remembering that night" },
  error_address: {
    ko: "주소를 찾을 수 없어요. 띄어쓰기를 포함해서 입력해보세요. ({error})",
    en: "Address not found. Try a more specific address. ({error})",
  },
  narrative_limit: {
    ko: "이 세션에서 최대 3회 이야기를 생성했어요. 24시간 후 다시 시도해주세요.",
    en: "You've reached the 3-narrative limit for this session. Please try again in 24 hours.",
  },
  narrative_error: {
    ko: "이야기를 불러오지 못했어요. 잠시 후 다시 시도해주세요.",
    en: "Couldn't load the narrative. Please try again later.",
  },
  privacy_title: { ko: "개인정보 처리 고지", en: "Privacy Notice" },
  privacy_body: {
    ko: "입력한 정보는 서비스 제공을 위해 Anthropic에 전송되며,<br>별도로 저장되지 않습니다.<br>서버 운영 로그는 7일 후 자동 삭제됩니다.",
    en: "Your input is sent to Anthropic solely to generate the narrative.<br>No personal data is stored.<br>Server access logs are automatically deleted after 7 days.",
  },
  privacy_link: { ko: "Anthropic의 데이터 처리 정책", en: "Anthropic's Privacy Policy" },
  btn_save_menu: { ko: "저장하기", en: "Save" },
  btn_download_chart: { ko: "별자리만 저장하기", en: "Save chart only" },
  btn_download_card: { ko: "별자리노트와 함께 저장하기", en: "Save with narrative" },
  btn_share: { ko: "공유하기", en: "Share" },
  btn_copy_link: { ko: "링크 복사", en: "Copy link" },
  share_copied: { ko: "링크가 복사됐어요", en: "Link copied" },
};

export function t(key: string, lang: Lang): string {
  const entry = STRINGS[key];
  if (!entry) return key;
  return entry[lang] ?? entry.en ?? key;
}

export function detectLang(): Lang {
  const nav = typeof navigator !== "undefined" ? navigator.language : "en";
  return nav.toLowerCase().startsWith("ko") ? "ko" : "en";
}
