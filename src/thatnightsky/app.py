"""ThatNightSky — Streamlit app for the night sky on a given date."""

import datetime

from dotenv import load_dotenv

load_dotenv()

import streamlit as st

from thatnightsky.compute import GeocodingError, run
from thatnightsky.models import QueryInput
from thatnightsky.narrative import generate_night_description
from thatnightsky.renderers.plotly_2d import render_plotly_chart

st.set_page_config(
    page_title="그날 밤하늘",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- Dark fullscreen theme CSS ---
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
    /* Remove main block padding + bottom margin for input bar height */
    [data-testid="stMainBlockContainer"] {
        padding-top: 0 !important;
        padding-bottom: 7rem !important;
    }
    /* Input bar: fix stLayoutWrapper (columns wrapper) to bottom — only when text input present */
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
    /* Narrative overlay: full width strip, above chart (z10), below input bar (z100) */
    [data-testid="stElementContainer"]:has(.overlay-box) {
        position: fixed !important;
        bottom: 7rem !important;
        left: 0 !important;
        right: 0 !important;
        z-index: 50 !important;
    }
    [data-testid="stElementContainer"]:has(.overlay-box) .overlay-box {
        border-radius: 0 !important;
        margin-bottom: 0 !important;
        text-align: center !important;
    }
    /* Chart: full viewport width, fixed 30px above input bar */
    [data-testid="stElementContainer"]:has([data-testid="stPlotlyChart"]) {
        position: fixed !important;
        left: 0 !important;
        right: 0 !important;
        bottom: calc(7rem + 30px - 50vw) !important;
        width: 100vw !important;
        height: 100vw !important;
        z-index: 10 !important;
        overflow: visible !important;
    }
    [data-testid="stFullScreenFrame"]:has([data-testid="stPlotlyChart"]),
    [data-testid="stPlotlyChart"] {
        width: 100% !important;
        height: 100% !important;
        overflow: visible !important;
    }
    /* Fill all inner Plotly div layers */
    [data-testid="stPlotlyChart"] > div,
    [data-testid="stPlotlyChart"] .js-plotly-plot,
    [data-testid="stPlotlyChart"] .plotly,
    [data-testid="stPlotlyChart"] .plot-container,
    [data-testid="stPlotlyChart"] .svg-container {
        width: 100% !important;
        height: 100% !important;
        background: #050a1a !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
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

if st.session_state.sky_data is not None:
    fig = render_plotly_chart(st.session_state.sky_data)
    chart_placeholder.plotly_chart(
        fig,
        use_container_width=False,
        config={"scrollZoom": True, "displayModeBar": False},
    )
else:
    chart_placeholder.markdown(
        "<div style='height:100vh; display:flex; align-items:center; justify-content:center;"
        " color:#334466; font-size:1.2rem;'>장소와 날짜를 입력하고 밤하늘을 불러오세요</div>",
        unsafe_allow_html=True,
    )

# --- Bottom input bar (fixed via CSS) ---
col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1.5])
with col1:
    address = st.text_input(
        "장소", placeholder="예: 부산광역시 가야동", label_visibility="visible"
    )
with col2:
    date_val = st.date_input(
        "날짜", value=datetime.date(1995, 1, 15), label_visibility="visible"
    )
with col3:
    time_val = st.time_input(
        "시각", value=datetime.time(0, 0), label_visibility="visible", step=300
    )
with col4:
    theme = st.text_input(
        "이 날의 의미",
        placeholder="예: 생일, 첫 만남, 기일",
        label_visibility="visible",
    )
with col5:
    st.markdown("<div style='height:1.9rem'></div>", unsafe_allow_html=True)
    submitted = st.button("✦ 밤하늘보기", use_container_width=True)

# --- Error message ---
if st.session_state.error_msg:
    st.markdown(
        f"<div class='overlay-box' style='border:1px solid #ff6b6b; color:#ff9999;'>"
        f"{st.session_state.error_msg}</div>",
        unsafe_allow_html=True,
    )

# --- Narrative text ---
if st.session_state.narrative:
    st.markdown(
        f"<div class='overlay-box'><p class='narrative-text'>{st.session_state.narrative}</p></div>",
        unsafe_allow_html=True,
    )

# --- Form submission handler ---
if submitted and address:
    when_str = f"{date_val.strftime('%Y-%m-%d')} {time_val.strftime('%H:%M')}"
    st.session_state.error_msg = None
    st.session_state.narrative = None

    with st.spinner("밤하늘을 계산하는 중..."):
        try:
            sky_data = run(QueryInput(address=address, when=when_str))
            st.session_state.sky_data = sky_data
        except GeocodingError as e:
            st.session_state.error_msg = f"주소를 찾을 수 없어요: {e}"
            st.rerun()

    if st.session_state.sky_data is not None:
        with st.spinner("그날 밤하늘을 기억하는 중..."):
            try:
                narrative = generate_night_description(
                    address=st.session_state.sky_data.context.address_display,
                    when=when_str,
                    visible_constellation_names=st.session_state.sky_data.visible_constellation_names,
                    theme=theme,
                )
                st.session_state.narrative = narrative
            except Exception:
                pass  # Narrative failure should not block chart rendering

    st.rerun()
