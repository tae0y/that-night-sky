"""ThatNightSky — Streamlit app for the night sky on a given date."""

import datetime
import random

from dotenv import load_dotenv

load_dotenv()

import streamlit as st
import streamlit.components.v1 as components

from thatnightsky.compute import GeocodingError, run
from thatnightsky.models import QueryInput
from thatnightsky.narrative import generate_night_description
from thatnightsky.renderers.svg_2d import render_svg_html

st.set_page_config(
    page_title="그날 밤하늘",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- Session state initialization ---
if "sky_data" not in st.session_state:
    st.session_state.sky_data = None
if "narrative" not in st.session_state:
    st.session_state.narrative = None
if "error_msg" not in st.session_state:
    st.session_state.error_msg = None
if "privacy_agreed" not in st.session_state:
    st.session_state.privacy_agreed = False
if "narrative_count" not in st.session_state:
    st.session_state.narrative_count = 0
if "input_open" not in st.session_state:
    st.session_state.input_open = True

_MAX_NARRATIVES_PER_SESSION = 3

_SAMPLE_INPUTS = [
    {
        "address": "서울 종로",
        "date": datetime.date(1900, 1, 1),
        "time": datetime.time(6, 0),
        "theme": "생일",
    },
    {
        "address": "부산 가야동",
        "date": datetime.date(2000, 10, 1),
        "time": datetime.time(20, 0),
        "theme": "첫만남",
    },
    {
        "address": "경기 김포",
        "date": datetime.date(2022, 11, 25),
        "time": datetime.time(5, 0),
        "theme": "아버지기일",
    },
]

if "default_input" not in st.session_state:
    st.session_state.default_input = random.choice(_SAMPLE_INPUTS)

# --- Dark fullscreen theme CSS (static) ---
st.markdown(
    """
    <style>
    /* Full background */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        background-color: #050a1a !important;
    }
    /* Hide header/toolbar */
    [data-testid="stHeader"], [data-testid="stToolbar"] {
        display: none !important;
    }
    /* Sidebar background */
    [data-testid="stSidebar"] {
        background-color: #050a1a !important;
    }
    /* Remove main block padding, allow chart to overflow */
    [data-testid="stMainBlockContainer"] {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        overflow: visible !important;
    }
    [data-testid="stMain"] {
        overflow: visible !important;
    }
    /* Input bar: fix stLayoutWrapper to bottom */
    [data-testid="stLayoutWrapper"]:has([data-testid="stTextInput"]) {
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        z-index: 100 !important;
        background: rgba(5, 10, 26, 0.95) !important;
        padding: 0.8rem 1.6rem 1.2rem !important;
        border-top: 1px solid rgba(255,255,255,0.08) !important;
    }
    /* Desktop: horizontal layout, columns stay in one row */
    @media (min-width: 769px) {
        [data-testid="stLayoutWrapper"]:has([data-testid="stTextInput"]) [data-testid="stHorizontalBlock"] {
            flex-wrap: nowrap !important;
        }
        [data-testid="stLayoutWrapper"]:has([data-testid="stTextInput"]) [data-testid="stColumn"] {
            min-width: 0 !important;
            flex-shrink: 1 !important;
        }
    }
    /* Mobile: vertical stacked layout */
    @media (max-width: 768px) {
        [data-testid="stLayoutWrapper"]:has([data-testid="stTextInput"]) [data-testid="stHorizontalBlock"] {
            flex-direction: column !important;
            gap: 0.2rem !important;
        }
        [data-testid="stLayoutWrapper"]:has([data-testid="stTextInput"]) [data-testid="stColumn"] {
            width: 100% !important;
            min-width: unset !important;
            flex: unset !important;
        }
    }
    /* Bottom overlay common styles */
    .overlay-box {
        background: rgba(0, 0, 0, 0.65);
        border-radius: 12px;
        padding: 1.2rem 1.6rem;
        color: #e8e8e8;
        font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
        margin-bottom: 0.5rem;
    }
    /* Input fields */
    [data-testid="stTextInput"] input,
    [data-testid="stDateInput"] input,
    [data-testid="stTimeInput"] input {
        background-color: #ffffff !important;
        color: #111111 !important;
        border: 1px solid rgba(255,255,255,0.3) !important;
        border-radius: 6px !important;
    }
    /* Button */
    [data-testid="stButton"] button {
        background-color: rgba(126, 200, 227, 0.2) !important;
        color: #7ec8e3 !important;
        border: 1px solid #7ec8e3 !important;
        border-radius: 6px !important;
        font-weight: 600;
    }
    [data-testid="stButton"] button:hover {
        background-color: rgba(126, 200, 227, 0.35) !important;
    }
    /* 밤하늘보기 버튼: 고정 너비 */
    .st-key-submit_btn button {
        width: 9rem !important;
        min-width: unset !important;
        max-width: unset !important;
        white-space: nowrap !important;
    }
    /* Labels */
    label, [data-testid="stWidgetLabel"] p {
        color: #aaaaaa !important;
        font-size: 0.85rem !important;
    }
    /* Divider */
    hr { border-color: rgba(255,255,255,0.1) !important; }
    /* Narrative text */
    .narrative-text {
        color: #d0d8e8;
        font-size: 1.05rem;
        line-height: 1.8;
        font-style: italic;
    }
    /* overlay-box Streamlit wrapper: collapse to zero so it doesn't interfere */
    [data-testid="stElementContainer"]:has(.overlay-box) {
        all: unset !important;
    }
    /* Loading message: fixed center overlay */
    @keyframes dots {
        0%   { content: '.'; }
        33%  { content: '. .'; }
        66%  { content: '. . .'; }
        100% { content: '.'; }
    }
    .loading-overlay {
        position: fixed !important;
        top: 50% !important;
        left: 50% !important;
        transform: translate(-50%, -50%) !important;
        z-index: 9999 !important;
        background: rgba(5,10,26,0.95) !important;
        border-radius: 12px !important;
        padding: 1.6rem 3rem !important;
        color: #e8e8e8 !important;
        font-size: 1rem !important;
        border: none !important;
        min-width: 200px !important;
        text-align: center !important;
        pointer-events: none !important;
    }
    .loading-overlay::after {
        content: '.';
        animation: dots 1.2s steps(1, end) infinite;
    }
    [data-testid="stElementContainer"]:has(.loading-overlay) {
        all: unset !important;
    }
    /* Toggle-open button: fixed to bottom when input is closed */
    .st-key-toggle_open {
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        z-index: 101 !important;
        background: rgba(5, 10, 26, 0.95) !important;
        border-top: 1px solid rgba(255,255,255,0.08) !important;
        padding: 0.5rem 1.6rem 0.8rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --- Privacy notice (shown until agreed) ---
@st.dialog("개인정보 처리 고지")
def _privacy_dialog() -> None:
    st.write(
        "입력한 날짜와 장소는 저장되지 않으며, 별자리 생성 목적으로만 AI(Anthropic Claude) API에 전송됩니다."
    )
    st.write("서버 운영 로그는 7일 후 자동 삭제됩니다.")
    st.markdown(
        "본 서비스는 [Anthropic의 데이터 처리 정책](https://www.anthropic.com/legal/privacy)을 따릅니다."
    )
    if st.button("확인", key="privacy_confirm", use_container_width=True):
        st.session_state.privacy_agreed = True
        st.rerun()


if not st.session_state.privacy_agreed:
    _privacy_dialog()

# --- Chart area ---
chart_placeholder = st.empty()
loading_placeholder = st.empty()

if st.session_state.sky_data is not None:
    svg_html = render_svg_html(st.session_state.sky_data)
    chart_placeholder.empty()
    # height=900: Streamlit이 요구하는 초기 iframe 높이(0이면 숨겨짐).
    # JS가 iframe을 position:fixed + width=h*2로 재조정하여 뷰포트 꽉 채움.
    # SVG는 visibility:hidden으로 시작해 JS 완료 후 visible — 깜빡임 방지.
    components.html(svg_html, height=900, scrolling=False)
else:
    chart_placeholder.markdown(
        "<div style='height:100vh; display:flex; align-items:center; justify-content:center;"
        " color:#334466; font-size:1.2rem;'>장소와 날짜를 입력하고 밤하늘을 불러오세요</div>",
        unsafe_allow_html=True,
    )

# --- Input panel ---
# Mobile closed state: show toggle button only (input form hidden via CSS)
# Mobile open state / Desktop: show full input form
if not st.session_state.input_open:
    if st.button("다시 입력하기", key="toggle_open", use_container_width=True):
        st.session_state.input_open = True
        st.rerun()
else:
    col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1.5])
    with col1:
        address = st.text_input(
            "장소",
            value=st.session_state.default_input["address"],
            label_visibility="visible",
        )
    with col2:
        date_val = st.date_input(
            "날짜",
            value=st.session_state.default_input["date"],
            min_value=datetime.date(1900, 1, 1),
            max_value=datetime.date.today(),
            label_visibility="visible",
        )
    with col3:
        time_val = st.time_input(
            "시각",
            value=st.session_state.default_input["time"],
            label_visibility="visible",
            step=3600,
        )
    with col4:
        theme = st.text_input(
            "이 날의 의미",
            value=st.session_state.default_input["theme"],
            label_visibility="visible",
            max_chars=20,
        )
    with col5:
        st.markdown("<div style='height:1.9rem'></div>", unsafe_allow_html=True)
        submitted = st.button("✦ 밤하늘보기", key="submit_btn")

    # --- Form submission handler ---
    if submitted and address:
        when_str = f"{date_val.strftime('%Y-%m-%d')} {time_val.strftime('%H:%M')}"
        st.session_state.error_msg = None
        st.session_state.narrative = None

        loading_placeholder.markdown(
            "<div class='loading-overlay'>✦ 밤하늘을 계산하는 중</div>",
            unsafe_allow_html=True,
        )
        try:
            sky_data = run(QueryInput(address=address, when=when_str))
            st.session_state.sky_data = sky_data
        except GeocodingError as e:
            loading_placeholder.empty()
            st.session_state.error_msg = (
                f"주소를 찾을 수 없어요. 띄어쓰기를 포함해서 입력해보세요. ({e})"
            )
            st.rerun()

        if st.session_state.sky_data is not None:
            if st.session_state.narrative_count >= _MAX_NARRATIVES_PER_SESSION:
                st.session_state.narrative = "이 세션에서 최대 3회 이야기를 생성했어요. 새 탭에서 다시 시작할 수 있습니다."
            else:
                loading_placeholder.markdown(
                    "<div class='loading-overlay'>✦ 그날 밤하늘을 기억하는 중</div>",
                    unsafe_allow_html=True,
                )
                try:
                    narrative = generate_night_description(
                        address=st.session_state.sky_data.context.address_display,
                        when=when_str,
                        constellation_positions=st.session_state.sky_data.constellation_positions,
                        theme=theme,
                    )
                    st.session_state.narrative = narrative
                    st.session_state.narrative_count += 1
                except Exception:
                    st.session_state.narrative = "그날, 밤, 하늘입니다."

            st.session_state.input_open = False

        st.rerun()

# --- Error message ---
if st.session_state.error_msg:
    st.markdown(
        f"<div class='overlay-box' style='"
        f"position:fixed; bottom:var(--input-h,3rem); left:0; right:0; z-index:51;"
        f"border:1px solid #ff6b6b; color:#ff9999;'>"
        f"{st.session_state.error_msg}</div>",
        unsafe_allow_html=True,
    )

# --- Narrative text ---
if st.session_state.narrative:
    st.markdown(
        f"""<div class='overlay-box' style='
            position: fixed;
            bottom: calc(var(--input-h, 3rem) + 1.9rem);
            left: 0;
            right: 0;
            z-index: 50;
            max-height: calc((1.8em * 4 + 2.4rem) * 1.2);
            overflow-y: auto;
            box-sizing: border-box;
            word-break: keep-all;
            overflow-wrap: break-word;
        '><p class='narrative-text' style='
            width: min(90%, 640px);
            margin: 0 auto;
            text-align: center;
            word-break: keep-all;
            overflow-wrap: break-word;
        '>{st.session_state.narrative}</p></div>""",
        unsafe_allow_html=True,
    )
