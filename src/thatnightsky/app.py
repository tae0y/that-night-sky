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
if "show_placeholder" not in st.session_state:
    st.session_state.show_placeholder = True
if "save_triggered" not in st.session_state:
    st.session_state.save_triggered = False
if "save_seq" not in st.session_state:
    st.session_state.save_seq = 0
if "theme" not in st.session_state:
    st.session_state.theme = ""
if "when_str" not in st.session_state:
    st.session_state.when_str = ""

_MAX_NARRATIVES_PER_SESSION = 3

_SAMPLE_INPUTS = [
    {
        "address": "부산 가야동",
        "date": datetime.date(1995, 1, 15),
        "time": datetime.time(6, 0),
        "theme": "생일",
    }
]

if "default_input" not in st.session_state:
    st.session_state.default_input = random.choice(_SAMPLE_INPUTS)

# --- Dark fullscreen theme CSS (static) ---
st.markdown(
    """
    <style>
    /* Custom font */
    @font-face {
        font-family: 'NostalgicPoliceHumanRights';
        src: url('https://cdn.jsdelivr.net/gh/projectnoonnu/2601-6@1.0/Griun_PolHumanrights-Rg.woff2') format('woff2');
        font-weight: normal;
        font-display: swap;
    }
    html, body, * {
        font-family: 'NostalgicPoliceHumanRights', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif !important;
    }
    /* Full background */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        background-color: #0d1b35 !important;
    }
    /* Hide header/toolbar */
    [data-testid="stHeader"], [data-testid="stToolbar"] {
        display: none !important;
    }
    /* Sidebar background */
    [data-testid="stSidebar"] {
        background-color: #0d1b35 !important;
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
        background: rgba(13, 27, 53, 0.97) !important;
        padding: 0.8rem 1.6rem 1.2rem !important;
        border-top: 1px solid rgba(201,169,110,0.15) !important;
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
        background: transparent;
        border-top: 1px solid rgba(201,169,110,0.18);
        border-radius: 0;
        padding: 1.2rem 1.6rem;
        color: #e8d5a3;
        font-family: 'NostalgicPoliceHumanRights', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
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
        color: #e8d5a3;
        font-size: 1.05rem;
        line-height: 1.8;
        font-style: italic;
        letter-spacing: 0.01em;
    }
    /* overlay-box Streamlit wrapper: collapse to zero so it doesn't interfere */
    [data-testid="stElementContainer"]:has(.overlay-box) {
        all: unset !important;
    }
    /* Loading overlay: full-screen breathe animation */
    @keyframes dots {
        0%   { content: '.'; }
        33%  { content: '. .'; }
        66%  { content: '. . .'; }
        100% { content: '.'; }
    }
    @keyframes breathe {
        0%, 100% { background-color: #0d1b35; }
        50%       { background-color: #1a2f55; }
    }
    .loading-overlay {
        position: fixed !important;
        inset: 0 !important;
        z-index: 9999 !important;
        animation: breathe 5s ease-in-out infinite;
        color: #e8e8e8 !important;
        font-size: 1rem !important;
        border: none !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        pointer-events: all !important;
    }
    .loading-overlay::after {
        content: '.';
        animation: dots 1.2s steps(1, end) infinite;
    }
    [data-testid="stElementContainer"]:has(.loading-overlay) {
        all: unset !important;
    }
    /* Fade-out curtain injected by MutationObserver when overlay is removed */
    #tns-fadeout {
        position: fixed;
        inset: 0;
        z-index: 9998;
        background-color: #0d1b35;
        opacity: 1;
        pointer-events: none;
        transition: opacity 0.6s ease-out;
    }
    </style>
    <script>
    function tnsWatchOverlay() {
        var ob = new MutationObserver(function(ms) {
            for (var i = 0; i < ms.length; i++) {
                var removed = ms[i].removedNodes;
                for (var j = 0; j < removed.length; j++) {
                    var n = removed[j];
                    if ((n.classList && n.classList.contains('loading-overlay')) ||
                        (n.querySelector && n.querySelector('.loading-overlay'))) {
                        ob.disconnect();
                        if (document.querySelector('.loading-overlay')) return;
                        var d = document.getElementById('tns-fadeout');
                        if (!d) {
                            d = document.createElement('div');
                            d.id = 'tns-fadeout';
                        }
                        d.style.opacity = '1';
                        document.body.appendChild(d);
                        requestAnimationFrame(function() {
                            requestAnimationFrame(function() {
                                d.style.opacity = '0';
                                setTimeout(function() {
                                    if (d.parentNode) d.parentNode.removeChild(d);
                                }, 700);
                            });
                        });
                        return;
                    }
                }
            }
        });
        ob.observe(document.body, { childList: true, subtree: true });
    }
    </script>
    <style>
    /* Bottom bar when input is closed: [다시 입력하기] + [저장하기] */
    .st-key-bottom_bar {
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        z-index: 101 !important;
        background: rgba(13, 27, 53, 0.97) !important;
        border-top: 1px solid rgba(201,169,110,0.15) !important;
        padding: 0.5rem 1.6rem 0.8rem !important;
    }
    /* Alchemical decoration layer */
    #alchemical-deco {
        position: fixed;
        top: 0; left: 0;
        width: 100vw; height: 100vh;
        pointer-events: none;
        z-index: 1;
        mix-blend-mode: screen;
        opacity: 0.13;
    }
    [data-testid="stElementContainer"]:has(#alchemical-deco) {
        all: unset !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Alchemical decoration SVG layer ---
# Centre point (500, 600) = horizon centre, matching the star chart's rotation origin.
# All decorative elements radiate from or are concentric with this point.
# Wavy radial lines use cubic bezier curves to mimic the flame/wave strokes in the reference.
st.markdown(
    """
    <svg id="alchemical-deco" xmlns="http://www.w3.org/2000/svg"
         viewBox="0 0 1000 600" preserveAspectRatio="xMidYMid slice">
      <defs>
        <!-- Gold gradient for star glints -->
        <radialGradient id="star-glow" cx="50%" cy="50%" r="50%">
          <stop offset="0%"   stop-color="#f5e6b8" stop-opacity="1"/>
          <stop offset="100%" stop-color="#c9a96e" stop-opacity="0"/>
        </radialGradient>
      </defs>

      <!-- ── Concentric orbital rings centred at (500, 600) ── -->
      <!-- 5 rings at r=160,260,360,460,540: thin gold, slight dash variation -->
      <circle cx="500" cy="600" r="160" fill="none" stroke="#c9a96e" stroke-width="0.5"
              stroke-dasharray="6 10" opacity="0.55"/>
      <circle cx="500" cy="600" r="260" fill="none" stroke="#c9a96e" stroke-width="0.45"
              stroke-dasharray="4 12" opacity="0.45"/>
      <circle cx="500" cy="600" r="360" fill="none" stroke="#c9a96e" stroke-width="0.4"
              stroke-dasharray="5 14" opacity="0.38"/>
      <circle cx="500" cy="600" r="460" fill="none" stroke="#c9a96e" stroke-width="0.35"
              stroke-dasharray="3 16" opacity="0.3"/>
      <circle cx="500" cy="600" r="540" fill="none" stroke="#c9a96e" stroke-width="0.3"
              stroke-dasharray="2 18" opacity="0.22"/>

      <!-- ── Wavy radial lines from (500, 600) ── -->
      <!-- Each ray: cubic bezier with lateral oscillation giving a flame/wave feel.
           Control points offset perpendicular to the ray direction.
           14 rays spread across the upper semicircle (approx every 12-13°). -->
      <g fill="none" stroke="#c9a96e" stroke-width="0.55" opacity="0.5">
        <!-- straight up -->
        <path d="M500,600 C480,480 520,360 500,100"/>
        <!-- 15° left -->
        <path d="M500,600 C465,478 448,355 430,100"/>
        <!-- 30° left -->
        <path d="M500,600 C452,475 398,348 350,105"/>
        <!-- 45° left -->
        <path d="M500,600 C438,474 365,342 270,120"/>
        <!-- 60° left -->
        <path d="M500,600 C425,472 330,340 190,150"/>
        <!-- 75° left -->
        <path d="M500,600 C414,474 298,348 120,190"/>
        <!-- 85° left (near horizon) -->
        <path d="M500,600 C408,522 280,440 60,360"/>
        <!-- 15° right -->
        <path d="M500,600 C535,478 552,355 570,100"/>
        <!-- 30° right -->
        <path d="M500,600 C548,475 602,348 650,105"/>
        <!-- 45° right -->
        <path d="M500,600 C562,474 635,342 730,120"/>
        <!-- 60° right -->
        <path d="M500,600 C575,472 670,340 810,150"/>
        <!-- 75° right -->
        <path d="M500,600 C586,474 702,348 880,190"/>
        <!-- 85° right (near horizon) -->
        <path d="M500,600 C592,522 720,440 940,360"/>
      </g>

      <!-- ── Tick marks on outermost ring (r=540, every 15°, upper semicircle) ── -->
      <!-- Computed: point on ring + outward extension 14px along radius direction -->
      <g fill="none" stroke="#c9a96e" stroke-width="0.8" opacity="0.55">
        <!-- 90° (top) -->
        <line x1="500" y1="60"  x2="500" y2="46"/>
        <!-- 75° left -->
        <line x1="361" y1="100" x2="354" y2="87"/>
        <!-- 60° left -->
        <line x1="233" y1="212" x2="221" y2="202"/>
        <!-- 45° left -->
        <line x1="119" y1="370" x2="106" y2="364"/>
        <!-- 75° right -->
        <line x1="639" y1="100" x2="646" y2="87"/>
        <!-- 60° right -->
        <line x1="767" y1="212" x2="779" y2="202"/>
        <!-- 45° right -->
        <line x1="881" y1="370" x2="894" y2="364"/>
      </g>

      <!-- ── Gold 4-pointed star glints (varying size) ── -->
      <!-- Path: thin diamond cross — two overlapping thin rhombuses -->
      <g fill="#e8d5a3" opacity="0.75">
        <!-- large centre-top -->
        <path d="M500,22 L503,30 L512,33 L503,36 L500,44 L497,36 L488,33 L497,30 Z"/>
        <!-- medium scattered -->
        <path d="M130,72  L132,77  L137,79  L132,81  L130,86  L128,81  L123,79  L128,77 Z"/>
        <path d="M870,68  L872,73  L877,75  L872,77  L870,82  L868,77  L863,75  L868,73 Z"/>
        <path d="M310,45  L311,49  L315,50  L311,52  L310,56  L309,52  L305,50  L309,49 Z"/>
        <path d="M680,50  L681,54  L685,56  L681,58  L680,62  L679,58  L675,56  L679,54 Z"/>
        <path d="M60,240  L61,244  L65,246  L61,248  L60,252  L59,248  L55,246  L59,244 Z"/>
        <path d="M940,230 L941,234 L945,236 L941,238 L940,242 L939,238 L935,236 L939,234 Z"/>
        <path d="M200,140 L201,143 L204,145 L201,147 L200,150 L199,147 L196,145 L199,143 Z"/>
        <path d="M800,135 L801,138 L804,140 L801,142 L800,145 L799,142 L796,140 L799,138 Z"/>
        <!-- small dots scattered -->
        <path d="M380,105 L381,108 L384,110 L381,112 L380,115 L379,112 L376,110 L379,108 Z"/>
        <path d="M620,98  L621,101 L624,102 L621,104 L620,107 L619,104 L616,102 L619,101 Z"/>
        <path d="M155,310 L156,312 L158,314 L156,316 L155,318 L154,316 L152,314 L154,312 Z"/>
        <path d="M845,305 L846,307 L848,309 L846,311 L845,313 L844,311 L842,309 L844,307 Z"/>
        <path d="M75,430  L76,432  L78,434  L76,436  L75,438  L74,436  L72,434  L74,432 Z"/>
        <path d="M925,420 L926,422 L928,424 L926,426 L925,428 L924,426 L922,424 L924,422 Z"/>
        <path d="M450,28  L451,31  L454,32  L451,34  L450,37  L449,34  L446,32  L449,31 Z"/>
        <path d="M550,32  L551,35  L554,36  L551,38  L550,41  L549,38  L546,36  L549,35 Z"/>
      </g>
    </svg>
    """,
    unsafe_allow_html=True,
)


# --- Privacy notice (blocks until agreed) ---
if not st.session_state.privacy_agreed:
    st.markdown("<div style='height: 25vh'></div>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown(
            """
            <style>
            .privacy-notice h3 { color: #ffffff; margin-bottom: 1rem; }
            .privacy-notice p  { color: #cccccc; line-height: 1.7; margin-bottom: 0.6rem; font-size: 0.95rem; }
            .privacy-notice small { color: #999999; font-size: 0.85rem; }
            .privacy-notice a { color: #7ec8e3; }
            </style>
            <div class="privacy-notice">
                <h3>개인정보 처리 고지</h3>
                <p>입력한 정보는 서비스 제공을 위해 Anthropic에 전송되며,<br>별도로 저장되지 않습니다.</p>
                <p>서버 운영 로그는 7일 후 자동 삭제됩니다.</p>
                <small>본 서비스는 <a href="https://www.anthropic.com/legal/privacy" target="_blank">Anthropic의 데이터 처리 정책</a>을 따릅니다.</small>
            </div>
            <div style="height: 0.8rem"></div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("확인", key="privacy_confirm", use_container_width=True):
            st.session_state.privacy_agreed = True
            st.rerun()
    st.stop()

# --- Chart area ---
chart_placeholder = st.empty()
loading_placeholder = st.empty()

if st.session_state.sky_data is not None:
    _when = st.session_state.when_str  # "YYYY-MM-DD HH:MM"
    _date_part = _when[:10]  # YYYY-MM-DD
    _hh_part = _when[11:13]  # HH
    _place_part = st.session_state.sky_data.context.address_display.replace(" ", "_")
    _theme_part = st.session_state.theme.replace(" ", "_") if st.session_state.theme else ""
    _name_parts = [p for p in [_date_part, _hh_part, _place_part, _theme_part] if p]
    png_filename = "_".join(_name_parts) + ".png"
    svg_html = render_svg_html(
        st.session_state.sky_data,
        filename=png_filename,
        narrative=st.session_state.narrative or "",
    )
    chart_placeholder.empty()
    # height=900: Streamlit이 요구하는 초기 iframe 높이(0이면 숨겨짐).
    # JS가 iframe을 position:fixed + width=h*2로 재조정하여 뷰포트 꽉 채움.
    # SVG는 visibility:hidden으로 시작해 JS 완료 후 visible — 깜빡임 방지.
    components.html(svg_html, height=900, scrolling=False)

# Save trigger: chart iframe watches parent DOM for attribute changes on this marker.
# Always rendered when sky_data exists so the node persists across reruns.
# data-seq increments on each save click; iframe JS watches for attribute mutations.
if st.session_state.sky_data is not None:
    if st.session_state.save_triggered:
        st.session_state.save_seq += 1
        st.session_state.save_triggered = False
    st.markdown(
        f'<div id="tns-save-trigger" data-seq="{st.session_state.save_seq}" style="display:none"></div>',
        unsafe_allow_html=True,
    )

if st.session_state.show_placeholder and st.session_state.sky_data is None:
    chart_placeholder.markdown(
        "<div style='height:100vh; display:flex; align-items:center; justify-content:center;"
        " color:#334466; font-size:1.2rem;'>장소와 날짜를 입력하고 밤하늘을 불러오세요</div>",
        unsafe_allow_html=True,
    )

# --- Input panel ---
# Mobile closed state: show toggle button only (input form hidden via CSS)
# Mobile open state / Desktop: show full input form
if not st.session_state.input_open:
    with st.container(key="bottom_bar"):
        has_sky = st.session_state.sky_data is not None
        bcol1, bcol2 = st.columns(2) if has_sky else (st.columns(1)[0], None)
        with bcol1:
            if st.button("다시 입력하기", key="toggle_open", use_container_width=True):
                st.session_state.input_open = True
                st.rerun()
        if bcol2 is not None:
            with bcol2:
                if st.button("저장하기", key="save_btn", use_container_width=True):
                    st.session_state.save_triggered = True
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
        st.session_state.show_placeholder = False
        st.session_state.theme = theme
        st.session_state.when_str = when_str

        loading_placeholder.markdown(
            "<div class='loading-overlay'>✦ 밤하늘을 계산하는 중"
            "<script>tnsWatchOverlay();</script>"
            "</div>",
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
                    "<div class='loading-overlay'>✦ 그날 밤하늘을 기억하는 중"
                    "<script>tnsWatchOverlay();</script>"
                    "</div>",
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
        f"<div class='overlay-box' style='background:rgba(10,16,32,0.95);"
        f"position:fixed;bottom:var(--input-h,3rem);left:0;right:0;z-index:51;"
        f"border:1px solid #ff6b6b;color:#ff9999;'>"
        f"{st.session_state.error_msg}</div>",
        unsafe_allow_html=True,
    )

# --- Narrative text ---
if st.session_state.narrative:
    st.markdown(
        f"<div class='overlay-box' style='position:fixed;bottom:calc(var(--input-h,3rem) + 1.9rem);left:0;right:0;z-index:50;max-height:calc((1.8em * 4 + 2.4rem) * 1.2);overflow-y:auto;box-sizing:border-box;word-break:keep-all;overflow-wrap:break-word;"
        f"background:linear-gradient(to bottom,rgba(8,16,36,0) 0%,rgba(10,20,45,0.72) 18%,rgba(12,24,52,0.88) 45%,rgba(13,27,55,0.96) 100%);"
        f"border-top:1px solid rgba(201,169,110,0.12);'>"
        f"<p class='narrative-text' style='width:min(90%,640px);margin:0 auto;text-align:center;word-break:keep-all;overflow-wrap:break-word;'>"
        f"{st.session_state.narrative}</p></div>",
        unsafe_allow_html=True,
    )

