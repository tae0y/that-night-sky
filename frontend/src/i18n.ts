import type { Lang } from './types'

const STRINGS: Record<string, Record<Lang, string>> = {
  page_title:        { ko: '그날 밤하늘', en: 'ThatNightSky' },
  label_place:       { ko: '장소', en: 'Location' },
  label_date:        { ko: '날짜 및 시각 (YYYY-MM-DD HH:MM)', en: 'Date & Time (YYYY-MM-DD HH:MM)' },
  label_theme:       { ko: '이 날의 의미', en: 'Occasion' },
  btn_view_sky:      { ko: '✦ 밤하늘보기', en: '✦ View Sky' },
  btn_narrative:     { ko: '✦ 이야기 생성', en: '✦ Generate Story' },
  btn_edit:          { ko: '다시 입력하기', en: 'Edit' },
  btn_save:          { ko: '↓ 저장', en: '↓ Save' },
  btn_reset:         { ko: '↺ 초기화', en: '↺ Reset' },
  btn_confirm:       { ko: '확인', en: 'Confirm' },
  placeholder_place: { ko: '예) 서울특별시 종로구', en: 'e.g. Seoul, Korea' },
  placeholder_date:  { ko: '예) 1999-12-31 23:00', en: 'e.g. 1999-12-31 23:00' },
  placeholder_theme: { ko: '예) 생일, 졸업, 첫만남', en: 'e.g. birthday, graduation' },
  loading_compute:   { ko: '밤하늘을 계산하고 있어요…', en: 'Computing the night sky…' },
  loading_narrative: { ko: '이야기를 쓰고 있어요…', en: 'Crafting your story…' },
  error_address:     { ko: '주소를 찾을 수 없어요. 다시 입력해 주세요.', en: 'Address not found. Please try again.' },
  narrative_limit:   { ko: '이야기는 세션당 3회까지만 생성할 수 있어요.', en: 'Story generation is limited to 3 times per session.' },
  privacy_title:     { ko: '개인정보 처리방침', en: 'Privacy Notice' },
  privacy_body:      {
    ko: '입력하신 주소는 좌표 변환 목적으로만 사용되며, 별도로 저장되지 않습니다.',
    en: 'Your address is used only to resolve coordinates and is not stored.',
  },
  filename:          { ko: '그날밤하늘.png', en: 'that-night-sky.png' },
}

const SAMPLES: Record<Lang, { address: string; when: string; theme: string }[]> = {
  ko: [
    { address: '서울특별시 종로구 창경궁로 185', when: '1999-12-31 23:00', theme: '새천년의 전날 밤' },
    { address: '부산광역시 해운대구 중동', when: '2010-06-01 21:00', theme: '첫사랑' },
    { address: '제주특별자치도 서귀포시', when: '2024-08-15 22:00', theme: '여름휴가' },
  ],
  en: [
    { address: 'New York, USA', when: '1999-12-31 23:00', theme: 'New Year Eve' },
    { address: 'London, UK', when: '2012-07-27 21:00', theme: 'Olympics opening' },
    { address: 'Sydney, Australia', when: '2000-09-15 20:00', theme: 'Olympics 2000' },
  ],
}

export function t(key: string, lang: Lang): string {
  return STRINGS[key]?.[lang] ?? STRINGS[key]?.en ?? key
}

export function randomSample(lang: Lang) {
  const list = SAMPLES[lang]
  return list[Math.floor(Math.random() * list.length)]
}
