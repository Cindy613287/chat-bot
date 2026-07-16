from __future__ import annotations

import html
import os
from copy import deepcopy
from typing import Any

import streamlit as st

from app.assistant import AssistantService, apply_actions
from app.config import (
    APP_NAME,
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    KNOWLEDGE_DIR,
    MAX_KNOWLEDGE_CHARS,
    MAX_UPLOAD_BYTES,
    MEMORY_FILE,
)
from app.knowledge import KnowledgeBase
from app.storage import UserStore, empty_user


st.set_page_config(
    page_title=APP_NAME,
    layout="wide",
    initial_sidebar_state="auto",
)

store = UserStore(MEMORY_FILE)
knowledge_base = KnowledgeBase(KNOWLEDGE_DIR, max_upload_bytes=MAX_UPLOAD_BYTES)


def inject_styles() -> None:
    st.html(
        """
        <style>
        :root {
            --ink: #172033;
            --muted: #5f6b7a;
            --primary: #4f46e5;
            --primary-dark: #3730a3;
            --primary-soft: #eeedff;
            --success: #0f766e;
            --canvas: #f6f7fb;
            --surface: #ffffff;
            --surface-soft: #fafbff;
            --border: #e3e7ef;
            --border-strong: #cfd5e2;
            --danger: #b42318;
            --radius-sm: 10px;
            --radius-md: 14px;
            --radius-lg: 20px;
            --radius-xl: 28px;
            --shadow-1: 0 1px 2px rgba(23, 32, 51, .04),
                        0 8px 22px rgba(23, 32, 51, .055);
            --shadow-2: 0 2px 5px rgba(23, 32, 51, .05),
                        0 18px 42px rgba(23, 32, 51, .09);
            --shadow-focus: 0 0 0 4px rgba(79, 70, 229, .16);
        }

        html { font-size: 16px; }
        body, [class*="css"] {
            font-family: Inter, "PingFang SC", "Microsoft YaHei", sans-serif;
            color: var(--ink);
        }
        .stApp {
            background:
                radial-gradient(circle at 88% -8%, rgba(99, 102, 241, .1), transparent 30rem),
                radial-gradient(circle at 14% 98%, rgba(20, 184, 166, .055), transparent 26rem),
                var(--canvas);
        }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stAppDeployButton"] { display: none; }
        [data-testid="stMainBlockContainer"] {
            max-width: 1160px;
            padding-top: 2.5rem;
            padding-bottom: 5rem;
        }
        [data-testid="stSidebar"] {
            background: rgba(251, 251, 253, .94);
            backdrop-filter: blur(22px);
            border-right: 1px solid var(--border);
            box-shadow: 12px 0 36px rgba(23, 32, 51, .035);
        }
        [data-testid="stSidebarContent"] { padding-top: 1.55rem; }

        h1, h2, h3 { color: var(--ink); letter-spacing: -0.025em; }
        p, li { line-height: 1.65; }

        .brand {
            display: flex;
            align-items: center;
            gap: .8rem;
            margin: .1rem 0 1.4rem;
        }
        .brand-mark {
            display: grid;
            place-items: center;
            width: 44px;
            height: 44px;
            border: 1px solid rgba(255, 255, 255, .34);
            border-radius: 15px;
            color: #fff;
            background: linear-gradient(145deg, #635bff 0%, var(--primary) 56%, #3f36d8 100%);
            font-weight: 750;
            box-shadow:
                inset 0 1px 0 rgba(255, 255, 255, .28),
                0 9px 22px rgba(79, 70, 229, .24);
        }
        .brand-name { font-size: 1.05rem; font-weight: 700; color: var(--ink); }
        .brand-tagline { font-size: .78rem; color: var(--muted); margin-top: .08rem; }

        .page-heading {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 1.5rem;
            margin-bottom: 1.65rem;
        }
        .eyebrow {
            color: var(--primary);
            font-size: .78rem;
            font-weight: 750;
            letter-spacing: .12em;
            text-transform: uppercase;
            margin-bottom: .45rem;
        }
        .page-title {
            font-size: clamp(2rem, 5vw, 2.7rem);
            line-height: 1.16;
            margin: 0;
            color: var(--ink);
            letter-spacing: -.045em;
        }
        .page-subtitle {
            color: var(--muted);
            margin: .7rem 0 0;
            max-width: 45rem;
            font-size: 1rem;
        }
        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: .5rem;
            min-height: 40px;
            padding: 0 .9rem;
            border: 1px solid #c9e7e2;
            border-radius: 999px;
            color: #0b665f;
            background: rgba(240, 253, 250, .88);
            backdrop-filter: blur(12px);
            font-size: .82rem;
            font-weight: 650;
            white-space: nowrap;
            box-shadow: 0 6px 18px rgba(15, 118, 110, .08);
        }
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #14b8a6;
            box-shadow: 0 0 0 4px rgba(20, 184, 166, .12);
        }
        .status-pill.offline {
            color: #92400e;
            border-color: #f4d6a4;
            background: #fffbeb;
        }
        .status-pill.offline .status-dot {
            background: #d97706;
            box-shadow: 0 0 0 4px rgba(217, 119, 6, .12);
        }

        .hero-card {
            position: relative;
            overflow: hidden;
            isolation: isolate;
            padding: clamp(1.6rem, 4vw, 2.45rem);
            margin: 1.15rem 0 1.45rem;
            border: 1px solid rgba(190, 194, 255, .58);
            border-radius: var(--radius-xl);
            background:
                radial-gradient(circle at 95% 5%, rgba(79,70,229,.16), transparent 38%),
                linear-gradient(135deg, #ffffff 0%, #f7f7ff 100%);
            box-shadow:
                inset 0 1px 0 rgba(255, 255, 255, .9),
                var(--shadow-2);
        }
        .hero-card::before {
            content: "";
            position: absolute;
            z-index: -1;
            width: 210px;
            height: 210px;
            right: -72px;
            top: -90px;
            border: 38px solid rgba(99, 102, 241, .06);
            border-radius: 50%;
        }
        .hero-layout {
            display: grid;
            grid-template-columns: minmax(0, 1fr) 190px;
            align-items: center;
            gap: 2rem;
        }
        .hero-content { min-width: 0; }
        .hero-stack {
            position: relative;
            width: 176px;
            height: 132px;
            justify-self: end;
        }
        .stack-card {
            position: absolute;
            width: 142px;
            height: 98px;
            padding: 14px;
            border: 1px solid rgba(151, 157, 226, .42);
            border-radius: 18px;
            background: rgba(255, 255, 255, .8);
            backdrop-filter: blur(14px);
            box-shadow: 0 14px 30px rgba(52, 55, 110, .12);
        }
        .stack-card.back {
            top: 2px;
            right: 2px;
            transform: rotate(7deg);
            background: rgba(230, 232, 255, .72);
        }
        .stack-card.middle {
            top: 13px;
            right: 17px;
            transform: rotate(-4deg);
            background: rgba(244, 245, 255, .9);
        }
        .stack-card.front {
            top: 25px;
            right: 8px;
            background: rgba(255, 255, 255, .94);
        }
        .stack-label {
            color: var(--primary);
            font-size: .68rem;
            font-weight: 750;
            letter-spacing: .08em;
            text-transform: uppercase;
        }
        .stack-line {
            display: block;
            height: 7px;
            margin-top: 9px;
            border-radius: 999px;
            background: #e7e9f3;
        }
        .stack-line.short { width: 62%; }
        .stack-dot-row { display: flex; gap: 6px; margin-top: 12px; }
        .stack-dot {
            width: 18px;
            height: 18px;
            border-radius: 6px;
            background: var(--primary-soft);
        }
        .stack-dot.active { background: #c9c5ff; }
        .stack-file {
            display: grid;
            place-items: center;
            width: 34px;
            height: 34px;
            margin-top: 10px;
            border-radius: 10px;
            color: var(--primary);
            background: var(--primary-soft);
            font-size: .62rem;
            font-weight: 800;
        }
        .hero-kicker {
            color: var(--primary);
            font-size: .8rem;
            font-weight: 750;
            letter-spacing: .08em;
        }
        .hero-title {
            max-width: 42rem;
            margin: .6rem 0 .7rem;
            font-size: clamp(1.55rem, 4vw, 2.15rem);
            line-height: 1.28;
            letter-spacing: -.035em;
            color: var(--ink);
        }
        .hero-copy { color: var(--muted); max-width: 40rem; margin: 0; }

        .metric-card {
            position: relative;
            overflow: hidden;
            min-height: 116px;
            padding: 1.15rem 1.25rem;
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            background: rgba(255, 255, 255, .9);
            box-shadow: var(--shadow-1);
            transition: border-color 180ms ease, box-shadow 180ms ease;
        }
        .metric-card::after {
            content: "";
            position: absolute;
            width: 72px;
            height: 72px;
            right: -28px;
            bottom: -30px;
            border-radius: 50%;
            background: var(--metric-tint, rgba(79, 70, 229, .08));
        }
        .metric-card:hover {
            border-color: #d1d4f6;
            box-shadow: var(--shadow-2);
        }
        .metric-label { color: var(--muted); font-size: .82rem; }
        .metric-value { color: var(--ink); font-size: 1.7rem; font-weight: 750; margin-top: .2rem; }
        .metric-primary { --metric-tint: rgba(79, 70, 229, .11); }
        .metric-progress { --metric-tint: rgba(217, 119, 6, .12); }
        .metric-success { --metric-tint: rgba(15, 118, 110, .12); }

        .account-card {
            padding: 1rem 1.05rem;
            margin-bottom: .9rem;
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            background: rgba(255, 255, 255, .9);
            box-shadow: var(--shadow-1);
        }
        .account-label { color: var(--muted); font-size: .76rem; }
        .account-name { color: var(--ink); font-weight: 700; margin-top: .18rem; }

        [data-testid="stTabs"] [role="tablist"],
        [data-testid="stTabs"] [data-baseweb="tab-list"] {
            width: fit-content;
            gap: .3rem;
            padding: .3rem;
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            background: rgba(234, 236, 243, .86);
            box-shadow: inset 0 1px 2px rgba(23, 32, 51, .045);
        }
        [data-testid="stTabs"] [data-testid="stTab"],
        [data-testid="stTabs"] [data-baseweb="tab"] {
            min-height: 44px;
            border-radius: var(--radius-sm);
            padding: .5rem 1.05rem;
            color: var(--muted);
            font-weight: 650;
        }
        [data-testid="stTabs"] [data-testid="stTab"][data-selected="true"],
        [data-testid="stTabs"] [aria-selected="true"] {
            background: #fff;
            color: var(--primary);
            box-shadow: 0 1px 2px rgba(23, 32, 51, .06),
                        0 5px 12px rgba(23, 32, 51, .08);
        }
        [data-testid="stTabs"] .react-aria-SelectionIndicator,
        [data-testid="stTabs"] [data-baseweb="tab-highlight"],
        [data-testid="stTabs"] [data-baseweb="tab-border"] { display: none; }
        [data-testid="stSidebar"] [data-testid="stTabs"] [role="tablist"] {
            width: 100%;
            display: grid;
            grid-template-columns: repeat(2, 1fr);
        }
        [data-testid="stSidebar"] [data-testid="stTab"] {
            justify-content: center;
        }

        .stButton > button,
        .stFormSubmitButton > button,
        .stDownloadButton > button,
        [data-testid="stPopoverButton"] > button {
            min-height: 48px;
            padding: .65rem 1.1rem;
            border-radius: var(--radius-md);
            font-weight: 650;
            letter-spacing: -.005em;
            cursor: pointer;
            box-shadow: 0 1px 2px rgba(23, 32, 51, .04);
            transition: transform 160ms ease, border-color 180ms ease,
                        color 180ms ease, background-color 180ms ease,
                        box-shadow 180ms ease;
        }
        .stButton > button[kind="secondary"],
        .stFormSubmitButton > button[kind="secondary"],
        [data-testid="stPopoverButton"] > button {
            color: #303a50;
            border-color: var(--border-strong);
            background: linear-gradient(180deg, #ffffff 0%, #f8f9fc 100%);
        }
        .stButton > button[kind="secondary"]:hover,
        .stFormSubmitButton > button[kind="secondary"]:hover,
        [data-testid="stPopoverButton"] > button:hover {
            color: var(--primary);
            border-color: #b8b3ff;
            background: #fff;
            box-shadow: 0 7px 18px rgba(79, 70, 229, .1);
        }
        .stButton > button:active,
        .stFormSubmitButton > button:active,
        [data-testid="stPopoverButton"] > button:active {
            transform: translateY(1px);
            box-shadow: 0 1px 2px rgba(23, 32, 51, .08);
        }
        .stButton > button:disabled,
        .stFormSubmitButton > button:disabled {
            cursor: not-allowed;
            opacity: .58;
            box-shadow: none;
        }
        .stButton > button:focus-visible,
        .stFormSubmitButton > button:focus-visible,
        input:focus-visible,
        textarea:focus-visible {
            outline: 3px solid rgba(79, 70, 229, .3) !important;
            outline-offset: 2px;
        }
        .stButton > button[kind="primary"],
        .stFormSubmitButton > button[kind="primary"],
        .stFormSubmitButton > button[kind="primaryFormSubmit"] {
            color: #fff;
            border-color: var(--primary);
            background: linear-gradient(180deg, #6259f5 0%, var(--primary) 62%, #443bd7 100%);
            box-shadow:
                inset 0 1px 0 rgba(255, 255, 255, .22),
                0 8px 18px rgba(79, 70, 229, .2);
        }
        .stButton > button[kind="primary"]:hover,
        .stFormSubmitButton > button[kind="primary"]:hover,
        .stFormSubmitButton > button[kind="primaryFormSubmit"]:hover {
            border-color: var(--primary-dark);
            background: linear-gradient(180deg, #554ce5 0%, var(--primary-dark) 100%);
            box-shadow:
                inset 0 1px 0 rgba(255, 255, 255, .18),
                0 10px 22px rgba(55, 48, 163, .24);
        }

        [data-testid="stChatMessage"] {
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            background: rgba(255, 255, 255, .92);
            padding: .5rem .6rem;
            margin-bottom: .8rem;
            box-shadow: var(--shadow-1);
        }
        [data-testid="stChatInput"] {
            padding: .35rem;
            border: 1px solid var(--border-strong);
            border-radius: 18px;
            background: rgba(255, 255, 255, .96);
            box-shadow: 0 12px 34px rgba(23, 32, 51, .1);
        }
        [data-testid="stChatInput"]:focus-within {
            border-color: var(--primary);
            box-shadow: var(--shadow-focus), 0 12px 34px rgba(23, 32, 51, .1);
        }
        [data-baseweb="input"] > div,
        [data-baseweb="textarea"] > div,
        [data-testid="stTextInputRootElement"],
        [data-testid="stTextAreaRootElement"] {
            min-height: 48px;
            border-color: var(--border-strong);
            border-radius: var(--radius-md);
            background: var(--surface-soft);
            transition: border-color 180ms ease, background-color 180ms ease,
                        box-shadow 180ms ease;
        }
        [data-baseweb="input"]:focus-within > div,
        [data-baseweb="textarea"]:focus-within > div,
        [data-testid="stTextInputRootElement"]:focus-within,
        [data-testid="stTextAreaRootElement"]:focus-within {
            border-color: var(--primary);
            background: #fff;
            box-shadow: var(--shadow-focus);
        }
        [data-testid="stFileUploaderDropzone"] {
            min-height: 164px;
            border: 1px dashed #b8bdd0;
            border-radius: var(--radius-lg);
            background:
                radial-gradient(circle at 50% 0%, rgba(79, 70, 229, .06), transparent 55%),
                var(--surface-soft);
        }
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-color: var(--border);
            border-radius: var(--radius-lg);
            background: rgba(255, 255, 255, .92);
            box-shadow: var(--shadow-1);
            transition: border-color 180ms ease, box-shadow 180ms ease;
        }
        [data-testid="stVerticalBlockBorderWrapper"]:hover {
            border-color: #d0d4e2;
            box-shadow: var(--shadow-2);
        }
        [data-testid="stExpander"] {
            overflow: hidden;
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            background: rgba(255, 255, 255, .84);
            box-shadow: var(--shadow-1);
        }
        [data-testid="stForm"] {
            border-color: var(--border);
            border-radius: var(--radius-lg);
            background: rgba(255, 255, 255, .9);
            box-shadow: var(--shadow-1);
        }
        [data-testid="stAlert"] {
            border-radius: var(--radius-md);
            border: 1px solid rgba(148, 163, 184, .22);
        }
        [data-baseweb="popover"] {
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            background: rgba(255, 255, 255, .96);
            box-shadow: 0 20px 55px rgba(23, 32, 51, .18);
            backdrop-filter: blur(18px);
        }
        [data-testid="stPopoverBody"] {
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            background: rgba(255, 255, 255, .96);
            box-shadow: 0 20px 55px rgba(23, 32, 51, .18);
            backdrop-filter: blur(18px);
        }
        [data-testid="stPopoverBody"] .stButton > button {
            color: var(--danger);
            border-color: #efc6c3;
            background: #fffafa;
            box-shadow: none;
        }
        [data-testid="stPopoverBody"] .stButton > button:hover {
            color: #8f1d16;
            border-color: #dcaaa6;
            background: #fff4f3;
            box-shadow: 0 7px 18px rgba(180, 35, 24, .09);
        }
        .task-done { color: var(--muted); text-decoration: line-through; }
        .file-meta { color: var(--muted); font-size: .85rem; }

        @media (max-width: 700px) {
            [data-testid="stMainBlockContainer"] {
                padding-left: 1rem;
                padding-right: 1rem;
                padding-top: 1.2rem;
            }
            .page-heading { display: block; }
            .status-pill { margin-top: 1rem; }
            .hero-card {
                margin-top: 1rem;
                border-radius: var(--radius-lg);
            }
            .hero-layout { display: block; }
            .hero-stack { display: none; }
            [data-testid="stTabs"] [role="tablist"],
            [data-testid="stTabs"] [data-baseweb="tab-list"] {
                width: 100%;
                display: grid;
                grid-template-columns: repeat(3, 1fr);
            }
            [data-testid="stTabs"] [data-testid="stTab"],
            [data-testid="stTabs"] [data-baseweb="tab"] {
                justify-content: center;
                padding-left: .6rem;
                padding-right: .6rem;
            }
            [data-testid="stSidebar"] [data-testid="stTabs"] [role="tablist"] {
                grid-template-columns: repeat(2, 1fr);
            }
            .metric-card {
                min-height: 104px;
                padding: 1rem;
            }
        }
        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after {
                scroll-behavior: auto !important;
                animation-duration: .01ms !important;
                transition-duration: .01ms !important;
            }
        }
        </style>
        """
    )


def get_api_key() -> str:
    try:
        secret = st.secrets.get("DEEPSEEK_API_KEY", "")
    except Exception:
        secret = ""
    return secret or os.getenv("DEEPSEEK_API_KEY", "")


def initialize_state() -> None:
    defaults = {
        "user_id": None,
        "messages": [],
        "tourist_data": empty_user(),
        "pending_prompt": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = deepcopy(value)


def current_user_name() -> str:
    return st.session_state.user_id or "游客"


def current_user_data() -> dict[str, Any]:
    if st.session_state.user_id:
        return store.get(st.session_state.user_id, create=True)
    return deepcopy(st.session_state.tourist_data)


def save_current_user(user_data: dict[str, Any]) -> None:
    if st.session_state.user_id:
        store.save(st.session_state.user_id, user_data)
    else:
        st.session_state.tourist_data = deepcopy(user_data)


def migrate_tourist_data(username: str) -> None:
    tourist = st.session_state.tourist_data
    if not tourist.get("用户信息") and not tourist.get("待办任务"):
        return
    user_data = store.get(username, create=True)
    user_data["用户信息"].update(tourist.get("用户信息", {}))
    user_data["待办任务"].extend(tourist.get("待办任务", []))
    store.save(username, user_data)
    st.session_state.tourist_data = empty_user()


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="brand">
              <div class="brand-mark" aria-hidden="true">知</div>
              <div>
                <div class="brand-name">知行</div>
                <div class="brand-tagline">AI 学习工作台</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.session_state.user_id:
            safe_user_name = html.escape(st.session_state.user_id)
            st.markdown(
                f"""
                <div class="account-card">
                  <div class="account-label">当前账户</div>
                  <div class="account-name">{safe_user_name}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(
                "退出登录",
                icon=":material/logout:",
                use_container_width=True,
            ):
                st.session_state.user_id = None
                st.session_state.messages = []
                st.rerun()
            st.caption("个人资料和任务仅保存在当前部署环境。")
            return

        st.info("当前为游客模式。登录后，资料和任务可以长期保存。")
        login_tab, register_tab = st.tabs(["登录", "注册"])

        with login_tab:
            with st.form("login_form"):
                login_name = st.text_input("用户名", placeholder="输入用户名")
                login_password = st.text_input(
                    "密码",
                    type="password",
                    placeholder="输入密码",
                )
                submitted = st.form_submit_button(
                    "登录",
                    type="primary",
                    icon=":material/login:",
                    use_container_width=True,
                )
            if submitted:
                try:
                    if store.authenticate(login_name, login_password):
                        migrate_tourist_data(login_name.strip())
                        st.session_state.user_id = login_name.strip()
                        st.session_state.messages = []
                        st.rerun()
                    st.error("用户名或密码不正确")
                except ValueError as error:
                    st.error(str(error))

        with register_tab:
            with st.form("register_form"):
                register_name = st.text_input("用户名", placeholder="1–32 个字符")
                register_password = st.text_input(
                    "密码",
                    type="password",
                    placeholder="至少 8 位字符",
                )
                registered = st.form_submit_button(
                    "创建账户",
                    type="primary",
                    icon=":material/person_add:",
                    use_container_width=True,
                )
            if registered:
                try:
                    created, message = store.register(register_name, register_password)
                    if created:
                        migrate_tourist_data(register_name.strip())
                        st.session_state.user_id = register_name.strip()
                        st.session_state.messages = []
                        st.rerun()
                    st.error(message)
                except ValueError as error:
                    st.error(str(error))


def render_heading(api_ready: bool) -> None:
    state_class = "" if api_ready else " offline"
    state_text = "AI 服务已连接" if api_ready else "等待 API 配置"
    st.markdown(
        f"""
        <header class="page-heading">
          <div>
            <div class="eyebrow">Your learning desk</div>
            <h1 class="page-title">今天，想弄懂什么？</h1>
            <p class="page-subtitle">
              把问题、校内资料和待办放在一个安静的工作台里，让每次学习都有下一步。
            </p>
          </div>
          <div class="status-pill{state_class}" role="status">
            <span class="status-dot" aria-hidden="true"></span>
            {state_text}
          </div>
        </header>
        """,
        unsafe_allow_html=True,
    )


def submit_quick_prompt(prompt: str) -> None:
    st.session_state.pending_prompt = prompt
    st.rerun()


def render_chat(api_key: str) -> None:
    if not st.session_state.messages:
        st.markdown(
            """
            <section class="hero-card">
              <div class="hero-layout">
                <div class="hero-content">
                  <div class="hero-kicker">从一个具体问题开始</div>
                  <h2 class="hero-title">课程规划、奖学金规则或今天的学习安排，都可以一起梳理。</h2>
                  <p class="hero-copy">
                    我会结合已上传的资料和你的个人进度回答，并把明确的待办自动整理到任务页。
                  </p>
                </div>
                <div class="hero-stack" aria-hidden="true">
                  <div class="stack-card back"></div>
                  <div class="stack-card middle"></div>
                  <div class="stack-card front">
                    <div class="stack-label">Study plan</div>
                    <span class="stack-line"></span>
                    <span class="stack-line short"></span>
                    <div class="stack-dot-row">
                      <span class="stack-dot active"></span>
                      <span class="stack-dot"></span>
                      <span class="stack-dot"></span>
                    </div>
                  </div>
                </div>
              </div>
            </section>
            """,
            unsafe_allow_html=True,
        )
        quick_prompts = [
            (
                "梳理本周计划",
                "根据我的待办，帮我安排本周学习计划。",
                ":material/calendar_view_week:",
            ),
            (
                "查询奖学金规则",
                "请帮我梳理奖学金评定的关键条件。",
                ":material/workspace_premium:",
            ),
            (
                "查看今日课程",
                "我今天有哪些课程？请按时间排序。",
                ":material/calendar_today:",
            ),
        ]
        columns = st.columns(3)
        for column, (label, prompt, icon) in zip(columns, quick_prompts):
            with column:
                if st.button(
                    label,
                    icon=icon,
                    use_container_width=True,
                    disabled=not api_key,
                    key=f"quick-{label}",
                ):
                    submit_quick_prompt(prompt)

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if not api_key:
        st.warning(
            "尚未配置 DEEPSEEK_API_KEY。请在环境变量或 .streamlit/secrets.toml 中添加后再开始对话。"
        )

    typed_prompt = st.chat_input(
        "输入问题，或直接说“提醒我周五交作业”",
        disabled=not api_key,
    )
    prompt = st.session_state.pop("pending_prompt", None) or typed_prompt
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    service = AssistantService(api_key, DEFAULT_BASE_URL, DEFAULT_MODEL)
    user_data = current_user_data()

    try:
        with st.spinner("正在整理问题与个人进度…"):
            actions = service.analyze_message(prompt)
            updated_user_data = apply_actions(user_data, actions)
            save_current_user(updated_user_data)
    except Exception:
        updated_user_data = user_data

    history = st.session_state.messages
    knowledge = knowledge_base.load_content(max_chars=MAX_KNOWLEDGE_CHARS)
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        try:
            for content in service.stream_reply(
                prompt=prompt,
                history=history,
                user_name=current_user_name(),
                user_data=updated_user_data,
                knowledge=knowledge,
            ):
                full_response += content
                placeholder.markdown(f"{full_response}▌")
            placeholder.markdown(full_response)
        except Exception as error:
            full_response = ""
            placeholder.error("暂时无法连接 AI 服务，请稍后重试。")
            st.caption(f"错误类型：{type(error).__name__}")

    if full_response:
        st.session_state.messages.append(
            {"role": "assistant", "content": full_response}
        )


def render_tasks() -> None:
    user_data = current_user_data()
    tasks = user_data.get("待办任务", [])
    pending_count = sum(task.get("状态", "未完成") != "已完成" for task in tasks)
    completed_count = len(tasks) - pending_count

    metric_columns = st.columns(3)
    metrics = [
        ("全部任务", len(tasks), "metric-primary"),
        ("进行中", pending_count, "metric-progress"),
        ("已完成", completed_count, "metric-success"),
    ]
    for column, (label, value, metric_class) in zip(metric_columns, metrics):
        with column:
            st.markdown(
                f"""
                <div class="metric-card {metric_class}">
                  <div class="metric-label">{label}</div>
                  <div class="metric-value">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with st.expander("添加一项任务", expanded=not tasks):
        with st.form("add_task_form", clear_on_submit=True):
            title = st.text_input("任务内容", placeholder="例如：完成数据结构作业")
            deadline = st.text_input("截止时间", placeholder="例如：本周五 18:00")
            add_task = st.form_submit_button(
                "添加任务",
                type="primary",
                icon=":material/add_task:",
            )
        if add_task:
            if not title.strip():
                st.error("请填写任务内容")
            else:
                tasks.append(
                    {
                        "任务": title.strip()[:200],
                        "截止时间": deadline.strip()[:100] or "无",
                        "状态": "未完成",
                    }
                )
                user_data["待办任务"] = tasks
                save_current_user(user_data)
                st.rerun()

    if not tasks:
        st.info("还没有任务。你可以手动添加，也可以在对话中直接说“提醒我……”。")
        return

    st.subheader("任务清单")
    for index, task in enumerate(tasks):
        completed = task.get("状态") == "已完成"
        safe_title = html.escape(str(task.get("任务", "未命名任务")))
        safe_deadline = html.escape(str(task.get("截止时间", "无")))
        with st.container(border=True):
            content_column, action_column, delete_column = st.columns([6, 1.25, 1])
            with content_column:
                title_class = "task-done" if completed else ""
                st.markdown(
                    f"<div class='{title_class}'><strong>{safe_title}</strong></div>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<div class='file-meta'>截止：{safe_deadline} · "
                    f"{'已完成' if completed else '进行中'}</div>",
                    unsafe_allow_html=True,
                )
            with action_column:
                action_label = "恢复" if completed else "完成"
                if st.button(
                    action_label,
                    icon=":material/undo:" if completed else ":material/check:",
                    key=f"task-state-{index}",
                    use_container_width=True,
                ):
                    tasks[index]["状态"] = "未完成" if completed else "已完成"
                    user_data["待办任务"] = tasks
                    save_current_user(user_data)
                    st.rerun()
            with delete_column:
                with st.popover(
                    "更多",
                    icon=":material/more_horiz:",
                    use_container_width=True,
                ):
                    st.caption("删除后无法恢复。")
                    if st.button(
                        "删除任务",
                        icon=":material/delete:",
                        key=f"task-delete-{index}",
                        use_container_width=True,
                    ):
                        tasks.pop(index)
                        user_data["待办任务"] = tasks
                        save_current_user(user_data)
                        st.rerun()

    if not st.session_state.user_id:
        st.caption("游客任务只在当前浏览会话中保留；登录后可持久保存。")


def format_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def render_knowledge() -> None:
    files = knowledge_base.list_files()
    total_size = sum(item["size"] for item in files)

    st.markdown(
        """
        <section class="hero-card">
          <div class="hero-layout">
            <div class="hero-content">
              <div class="hero-kicker">Knowledge library</div>
              <h2 class="hero-title">让回答建立在你信任的资料上。</h2>
              <p class="hero-copy">
                上传 UTF-8 编码的 TXT 文件。适合课程表、培养方案、评奖规则和个人学习笔记。
              </p>
            </div>
            <div class="hero-stack" aria-hidden="true">
              <div class="stack-card back"></div>
              <div class="stack-card middle"></div>
              <div class="stack-card front">
                <div class="stack-label">Library</div>
                <div class="stack-file">TXT</div>
                <span class="stack-line short"></span>
              </div>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    summary_columns = st.columns(2)
    with summary_columns[0]:
        st.markdown(
            f"""
            <div class="metric-card metric-primary">
              <div class="metric-label">资料数量</div>
              <div class="metric-value">{len(files)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with summary_columns[1]:
        st.markdown(
            f"""
            <div class="metric-card metric-success">
              <div class="metric-label">占用空间</div>
              <div class="metric-value">{format_size(total_size)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    uploads = st.file_uploader(
        "上传资料",
        type=["txt"],
        accept_multiple_files=True,
        help="单个文件不超过 2 MB，需使用 UTF-8 编码。",
    )
    if uploads and st.button(
        "保存所选文件",
        type="primary",
        icon=":material/save:",
    ):
        saved = 0
        for upload in uploads:
            try:
                knowledge_base.save_upload(upload.name, upload.getvalue())
                saved += 1
            except ValueError as error:
                st.error(f"{upload.name}：{error}")
        if saved:
            st.success(f"已保存 {saved} 个文件")
            st.rerun()

    st.subheader("已收录资料")
    if not files:
        st.info("知识库还是空的。上传第一份资料后，AI 会在相关问题中优先参考它。")
        return

    for index, item in enumerate(files):
        safe_file_name = html.escape(item["name"])
        with st.container(border=True):
            name_column, action_column = st.columns([7, 1])
            with name_column:
                st.markdown(f"<strong>{safe_file_name}</strong>", unsafe_allow_html=True)
                st.markdown(
                    f"<div class='file-meta'>{format_size(item['size'])} · TXT 文档</div>",
                    unsafe_allow_html=True,
                )
            with action_column:
                with st.popover(
                    "更多",
                    icon=":material/more_horiz:",
                    use_container_width=True,
                ):
                    st.caption("该文件将从知识库中移除。")
                    if st.button(
                        "删除文件",
                        icon=":material/delete:",
                        key=f"knowledge-delete-{index}",
                        use_container_width=True,
                    ):
                        knowledge_base.delete(item["name"])
                        st.rerun()


inject_styles()
initialize_state()
render_sidebar()

api_key = get_api_key()
render_heading(bool(api_key))

chat_tab, task_tab, knowledge_tab = st.tabs(["对话", "任务", "知识库"])
with chat_tab:
    render_chat(api_key)
with task_tab:
    render_tasks()
with knowledge_tab:
    render_knowledge()
