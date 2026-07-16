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
            --success: #0f766e;
            --canvas: #f6f7fb;
            --surface: #ffffff;
            --border: #e3e7ef;
            --danger: #b42318;
        }

        html { font-size: 16px; }
        body, [class*="css"] {
            font-family: Inter, "PingFang SC", "Microsoft YaHei", sans-serif;
            color: var(--ink);
        }
        .stApp { background: var(--canvas); }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stAppDeployButton"] { display: none; }
        [data-testid="stMainBlockContainer"] {
            max-width: 1160px;
            padding-top: 2.2rem;
            padding-bottom: 4rem;
        }
        [data-testid="stSidebar"] {
            background: #fbfbfd;
            border-right: 1px solid var(--border);
        }
        [data-testid="stSidebarContent"] { padding-top: 1.4rem; }

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
            width: 42px;
            height: 42px;
            border-radius: 13px;
            color: #fff;
            background: var(--primary);
            font-weight: 750;
            box-shadow: 0 8px 20px rgba(79, 70, 229, .2);
        }
        .brand-name { font-size: 1.05rem; font-weight: 700; color: var(--ink); }
        .brand-tagline { font-size: .78rem; color: var(--muted); margin-top: .08rem; }

        .page-heading {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 1.5rem;
            margin-bottom: 1.4rem;
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
            min-height: 36px;
            padding: 0 .8rem;
            border: 1px solid #c9e7e2;
            border-radius: 999px;
            color: #0b665f;
            background: #f0fdfa;
            font-size: .82rem;
            font-weight: 650;
            white-space: nowrap;
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
            padding: clamp(1.45rem, 4vw, 2.35rem);
            margin: .9rem 0 1.3rem;
            border: 1px solid #dfe2ff;
            border-radius: 20px;
            background:
                radial-gradient(circle at 95% 5%, rgba(79,70,229,.14), transparent 36%),
                linear-gradient(135deg, #ffffff 0%, #f7f7ff 100%);
            box-shadow: 0 18px 50px rgba(35, 42, 73, .07);
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
            min-height: 112px;
            padding: 1rem 1.1rem;
            border: 1px solid var(--border);
            border-radius: 16px;
            background: var(--surface);
        }
        .metric-label { color: var(--muted); font-size: .82rem; }
        .metric-value { color: var(--ink); font-size: 1.7rem; font-weight: 750; margin-top: .2rem; }

        .account-card {
            padding: .9rem 1rem;
            margin-bottom: .8rem;
            border: 1px solid var(--border);
            border-radius: 14px;
            background: #fff;
        }
        .account-label { color: var(--muted); font-size: .76rem; }
        .account-name { color: var(--ink); font-weight: 700; margin-top: .18rem; }

        [data-testid="stTabs"] [data-baseweb="tab-list"] {
            gap: .35rem;
            padding: .28rem;
            border: 1px solid var(--border);
            border-radius: 13px;
            background: #eef0f5;
        }
        [data-testid="stTabs"] [data-baseweb="tab"] {
            min-height: 42px;
            border-radius: 9px;
            padding: .5rem 1rem;
        }
        [data-testid="stTabs"] [aria-selected="true"] {
            background: #fff;
            box-shadow: 0 2px 8px rgba(23, 32, 51, .08);
        }

        .stButton > button,
        .stFormSubmitButton > button,
        .stDownloadButton > button {
            min-height: 44px;
            border-radius: 11px;
            font-weight: 650;
            cursor: pointer;
            transition: border-color 180ms ease, color 180ms ease,
                        background-color 180ms ease, box-shadow 180ms ease;
        }
        .stButton > button:focus-visible,
        .stFormSubmitButton > button:focus-visible,
        input:focus-visible,
        textarea:focus-visible {
            outline: 3px solid rgba(79, 70, 229, .3) !important;
            outline-offset: 2px;
        }
        .stButton > button[kind="primary"],
        .stFormSubmitButton > button[kind="primary"] {
            background: var(--primary);
            border-color: var(--primary);
        }
        .stButton > button[kind="primary"]:hover,
        .stFormSubmitButton > button[kind="primary"]:hover {
            background: var(--primary-dark);
            border-color: var(--primary-dark);
        }

        [data-testid="stChatMessage"] {
            border: 1px solid var(--border);
            border-radius: 16px;
            background: #fff;
            padding: .35rem .45rem;
            margin-bottom: .7rem;
        }
        [data-testid="stChatInput"] {
            border-color: #cfd4df;
            border-radius: 14px;
            background: #fff;
        }
        [data-testid="stFileUploaderDropzone"] {
            min-height: 150px;
            border-radius: 16px;
            border-color: #cfd4df;
            background: #fafbff;
        }
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-color: var(--border);
            border-radius: 16px;
            background: #fff;
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
            .hero-card { border-radius: 17px; }
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
            if st.button("退出登录", use_container_width=True):
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
              <div class="hero-kicker">从一个具体问题开始</div>
              <h2 class="hero-title">课程规划、奖学金规则或今天的学习安排，都可以一起梳理。</h2>
              <p class="hero-copy">
                我会结合已上传的资料和你的个人进度回答，并把明确的待办自动整理到任务页。
              </p>
            </section>
            """,
            unsafe_allow_html=True,
        )
        quick_prompts = [
            ("梳理本周计划", "根据我的待办，帮我安排本周学习计划。"),
            ("查询奖学金规则", "请帮我梳理奖学金评定的关键条件。"),
            ("查看今日课程", "我今天有哪些课程？请按时间排序。"),
        ]
        columns = st.columns(3)
        for column, (label, prompt) in zip(columns, quick_prompts):
            with column:
                if st.button(
                    label,
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
        ("全部任务", len(tasks)),
        ("进行中", pending_count),
        ("已完成", completed_count),
    ]
    for column, (label, value) in zip(metric_columns, metrics):
        with column:
            st.markdown(
                f"""
                <div class="metric-card">
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
            add_task = st.form_submit_button("添加任务", type="primary")
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
                    key=f"task-state-{index}",
                    use_container_width=True,
                ):
                    tasks[index]["状态"] = "未完成" if completed else "已完成"
                    user_data["待办任务"] = tasks
                    save_current_user(user_data)
                    st.rerun()
            with delete_column:
                if st.button(
                    "删除",
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
          <div class="hero-kicker">Knowledge library</div>
          <h2 class="hero-title">让回答建立在你信任的资料上。</h2>
          <p class="hero-copy">
            上传 UTF-8 编码的 TXT 文件。适合课程表、培养方案、评奖规则和个人学习笔记。
          </p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    summary_columns = st.columns(2)
    with summary_columns[0]:
        st.markdown(
            f"""
            <div class="metric-card">
              <div class="metric-label">资料数量</div>
              <div class="metric-value">{len(files)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with summary_columns[1]:
        st.markdown(
            f"""
            <div class="metric-card">
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
    if uploads and st.button("保存所选文件", type="primary"):
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
                if st.button(
                    "删除",
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
