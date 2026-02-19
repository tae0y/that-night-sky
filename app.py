"""ThatNightSky — 그날 밤하늘 Streamlit 앱."""

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

# --- 어두운 풀스크린 테마 CSS ---
st.markdown(
    """
    <style>
    /* 전체 배경 */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        background-color: #050a1a !important;
    }
    /* 헤더/툴바 숨김 */
    [data-testid="stHeader"], [data-testid="stToolbar"] {
        display: none !important;
    }
    /* 사이드바 배경 */
    [data-testid="stSidebar"] {
        background-color: #050a1a !important;
    }
    /* 메인 블록 패딩 제거 + 하단 input bar 높이만큼 여백 */
    [data-testid="stMainBlockContainer"] {
        padding-top: 0 !important;
        padding-bottom: 7rem !important;
    }
    /* input bar: stLayoutWrapper(columns 래퍼)를 하단에 고정 */
    [data-testid="stLayoutWrapper"] {
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        z-index: 100 !important;
        background: rgba(5, 10, 26, 0.95) !important;
        padding: 0.8rem 1.6rem 1.2rem !important;
        border-top: 1px solid rgba(255,255,255,0.08) !important;
    }
    /* 하단 오버레이 공통 */
    .overlay-box {
        background: rgba(0, 0, 0, 0.65);
        border-radius: 12px;
        padding: 1.2rem 1.6rem;
        color: #e8e8e8;
        font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
        margin-bottom: 0.5rem;
    }
    /* 입력 필드 */
    [data-testid="stTextInput"] input,
    [data-testid="stDateInput"] input,
    [data-testid="stTimeInput"] input {
        background-color: #ffffff !important;
        color: #111111 !important;
        border: 1px solid rgba(255,255,255,0.3) !important;
        border-radius: 6px !important;
    }
    /* 버튼 */
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
    /* 레이블 */
    label, [data-testid="stWidgetLabel"] p {
        color: #aaaaaa !important;
        font-size: 0.85rem !important;
    }
    /* 구분선 */
    hr { border-color: rgba(255,255,255,0.1) !important; }
    /* 감성 텍스트 */
    .narrative-text {
        color: #d0d8e8;
        font-size: 1.05rem;
        line-height: 1.8;
        font-style: italic;
    }
    /* plotly 차트: input bar 높이(7rem) 제외한 전체 높이 */
    .js-plotly-plot, .plotly, .plot-container {
        background: #050a1a !important;
        height: calc(100vh - 7rem) !important;
    }
    [data-testid="stPlotlyChart"] {
        height: calc(100vh - 7rem) !important;
    }
    [data-testid="stPlotlyChart"] > div {
        height: 100% !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- 세션 상태 초기화 ---
if "sky_data" not in st.session_state:
    st.session_state.sky_data = None
if "narrative" not in st.session_state:
    st.session_state.narrative = None
if "error_msg" not in st.session_state:
    st.session_state.error_msg = None

# --- 차트 영역 ---
chart_placeholder = st.empty()

if st.session_state.sky_data is not None:
    fig = render_plotly_chart(st.session_state.sky_data)
    chart_placeholder.plotly_chart(
        fig,
        use_container_width=True,
        config={"scrollZoom": True, "displayModeBar": False},
    )
else:
    chart_placeholder.markdown(
        "<div style='height:100vh; display:flex; align-items:center; justify-content:center;"
        " color:#334466; font-size:1.2rem;'>장소와 날짜를 입력하고 밤하늘을 불러오세요</div>",
        unsafe_allow_html=True,
    )

# --- 하단 input (CSS로 fixed 처리) ---
col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
with col1:
    address = st.text_input("장소", placeholder="예: 부산광역시 가야동", label_visibility="visible")
with col2:
    import datetime
    date_val = st.date_input("날짜", value=datetime.date(1995, 1, 15), label_visibility="visible")
with col3:
    time_val = st.time_input("시각", value=datetime.time(0, 0), label_visibility="visible", step=300)
with col4:
    st.markdown("<div style='height:1.9rem'></div>", unsafe_allow_html=True)
    submitted = st.button("✦ 밤하늘 보기", use_container_width=True)

# --- 오류 메시지 ---
if st.session_state.error_msg:
    st.markdown(
        f"<div class='overlay-box' style='border:1px solid #ff6b6b; color:#ff9999;'>"
        f"{st.session_state.error_msg}</div>",
        unsafe_allow_html=True,
    )

# --- 감성 텍스트 ---
if st.session_state.narrative:
    st.markdown(
        f"<div class='overlay-box'><p class='narrative-text'>{st.session_state.narrative}</p></div>",
        unsafe_allow_html=True,
    )

# --- 제출 처리 ---
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

    with st.spinner("그날 밤하늘을 기억하는 중..."):
        try:
            narrative = generate_night_description(
                address=sky_data.context.address_display,
                when=when_str,
                visible_constellation_names=sky_data.visible_constellation_names,
            )
            st.session_state.narrative = narrative
        except Exception:
            pass  # 감성 텍스트 실패는 차트 표시를 막지 않음

    st.rerun()
