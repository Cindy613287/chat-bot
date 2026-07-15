import streamlit as st
from openai import OpenAI

# 从 Secrets 读取 API Key（公网部署用）
API_KEY = st.secrets["DEEPSEEK_API_KEY"]
DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-chat"
from datetime import datetime
import os
import json
import hashlib
import re

# ========== 密码工具函数 ==========
def hash_password(password):
    """对密码进行 SHA-256 哈希加密"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    """验证密码是否正确"""
    return hash_password(password) == password_hash

# ========== 知识库读取函数 ==========
def load_knowledge():
    knowledge_dir = "knowledge"
    all_content = ""
    
    if not os.path.exists(knowledge_dir):
        return "（知识库文件夹不存在）"
    
    for filename in os.listdir(knowledge_dir):
        if filename.endswith(".txt"):
            file_path = os.path.join(knowledge_dir, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    all_content += f"\n【文件：{filename}】\n{content}\n"
            except Exception as e:
                all_content += f"\n（读取 {filename} 失败：{e}）\n"
    
    if all_content == "":
        return "（知识库为空，请添加 .txt 文件）"
    
    return all_content

# ========== 多用户记忆管理函数 ==========
def load_all_memory():
    default_data = {}
    try:
        with open("memory.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            if "用户信息" in data or "待办任务" in data:
                new_data = {"默认用户": data}
                save_all_memory(new_data)
                return new_data
            return data
    except FileNotFoundError:
        return default_data
    except:
        return default_data

def save_all_memory(all_data):
    with open("memory.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

def get_user_memory(user_id):
    if user_id == "游客":
        if "tourist_data" not in st.session_state:
            st.session_state.tourist_data = {
                "密码": None,
                "用户信息": {},
                "待办任务": []
            }
        return st.session_state.tourist_data
    
    all_data = load_all_memory()
    if user_id not in all_data:
        all_data[user_id] = {
            "密码": None,
            "用户信息": {},
            "待办任务": []
        }
        save_all_memory(all_data)
    return all_data[user_id]

def save_user_memory(user_id, user_data):
    if user_id == "游客":
        st.session_state.tourist_data = user_data
        return
    all_data = load_all_memory()
    all_data[user_id] = user_data
    save_all_memory(all_data)

def migrate_tourist_data(username, password_hash=None):
    if "tourist_data" in st.session_state and st.session_state.tourist_data:
        tourist_data = st.session_state.tourist_data
        if tourist_data["用户信息"] or tourist_data["待办任务"]:
            user_data = get_user_memory(username)
            if tourist_data["用户信息"]:
                user_data["用户信息"].update(tourist_data["用户信息"])
            if tourist_data["待办任务"]:
                user_data["待办任务"].extend(tourist_data["待办任务"])
            if password_hash:
                user_data["密码"] = password_hash
            save_user_memory(username, user_data)
        st.session_state.tourist_data = {"密码": None, "用户信息": {}, "待办任务": []}

# ========== 页面设置 ==========
st.set_page_config(page_title="我的AI助手", page_icon="🤖")
st.title("🤖 我的AI助手")

# ========== 初始化 Session State ==========
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "tourist_data" not in st.session_state:
    st.session_state.tourist_data = {"密码": None, "用户信息": {}, "待办任务": []}

# ========== 用户身份设置（侧边栏） ==========
with st.sidebar:
    st.header("👤 用户")
    
    if st.session_state.user_id:
        st.success(f"✅ 已登录：**{st.session_state.user_id}**")
        if st.button("🚪 退出登录", use_container_width=True):
            st.session_state.user_id = None
            st.session_state.messages = []
            st.rerun()
    else:
        st.info("👋 当前为游客模式")
        st.caption("💡 登录后可使用待办任务和个人信息功能")
    
    st.divider()
    
    # ===== 登录模块 =====
    st.subheader("🔑 登录 / 注册")
    
    login_name = st.text_input("👤 姓名", placeholder="请输入你的姓名", key="login_name_input")
    login_password = st.text_input("🔒 密码", placeholder="请输入密码", type="password", key="login_password_input")
    
    if login_name and login_password:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ 登录", use_container_width=True, key="login_btn"):
                all_data = load_all_memory()
                user_name = login_name.strip()
                
                if user_name in all_data:
                    stored_hash = all_data[user_name].get("密码")
                    if stored_hash and verify_password(login_password, stored_hash):
                        migrate_tourist_data(user_name)
                        st.session_state.user_id = user_name
                        st.session_state.messages = []
                        st.success(f"✅ 欢迎回来，{user_name}！")
                        st.rerun()
                    else:
                        st.error("❌ 密码错误，请重试")
                else:
                    st.warning(f"👋 {user_name} 是新用户，请点击「注册」按钮设置密码")
        
        with col2:
            if st.button("📝 注册", use_container_width=True, key="register_btn"):
                user_name = login_name.strip()
                password = login_password.strip()
                
                if len(password) < 6:
                    st.error("❌ 密码至少需要6位字符")
                else:
                    all_data = load_all_memory()
                    if user_name in all_data:
                        st.error("❌ 该用户名已被注册，请直接登录")
                    else:
                        password_hash = hash_password(password)
                        all_data[user_name] = {
                            "密码": password_hash,
                            "用户信息": {},
                            "待办任务": []
                        }
                        save_all_memory(all_data)
                        migrate_tourist_data(user_name)
                        st.session_state.user_id = user_name
                        st.session_state.messages = []
                        st.success(f"🎉 注册成功！欢迎 {user_name}！")
                        st.rerun()
    else:
        st.caption("💡 输入姓名和密码后，点击「登录」或「注册」")
    
    st.divider()
    st.caption("📌 不同用户的记忆和任务独立保存")

# ========== 知识库管理 ==========
with st.expander("📚 知识库管理", expanded=False):
    knowledge_dir = "knowledge"
    
    if os.path.exists(knowledge_dir):
        files = [f for f in os.listdir(knowledge_dir) if f.endswith(".txt")]
        st.info(f"当前知识库中有 **{len(files)}** 个文件")
        
        if files:
            st.write("📄 文件列表：")
            for f in files:
                st.write(f"- {f}")
    else:
        st.warning("知识库文件夹不存在，即将自动创建")
        os.makedirs(knowledge_dir, exist_ok=True)
        st.rerun()
    
    st.divider()
    uploaded_file = st.file_uploader(
        "📤 上传知识文件（仅支持 .txt）",
        type=["txt"],
        help="上传的 .txt 文件会自动保存到知识库"
    )
    
    if uploaded_file is not None:
        if not os.path.exists(knowledge_dir):
            os.makedirs(knowledge_dir)
        
        file_path = os.path.join(knowledge_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"✅ 文件 {uploaded_file.name} 上传成功！")
        st.rerun()
    
    st.divider()
    st.write("🗑️ 删除知识库文件：")
    
    if os.path.exists(knowledge_dir):
        files = [f for f in os.listdir(knowledge_dir) if f.endswith(".txt")]
        if files:
            file_to_delete = st.selectbox("选择要删除的文件", files)
            if st.button("删除此文件", type="secondary"):
                os.remove(os.path.join(knowledge_dir, file_to_delete))
                st.success(f"✅ 已删除 {file_to_delete}")
                st.rerun()
        else:
            st.write("（暂无文件）")

# ========== 显示当前时间 ==========
now = datetime.now()
current_time = now.strftime("%Y年%m月%d日 %H:%M")
st.caption(f"🕐 {current_time}")

# ========== 初始化客户端 ==========
client = OpenAI(api_key=API_KEY, base_url=DEFAULT_BASE_URL)

# ========== 初始化聊天历史 ==========
if "messages" not in st.session_state:
    st.session_state.messages = []

# ========== 显示历史消息 ==========
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ========== 输入框 ==========
if prompt := st.chat_input("输入你的问题..."):
    # 检测用户是否在自我介绍（提取姓名），但不再自动登录
    name_match = re.search(r'我叫\s*([^\s，,。.！!？?]+)', prompt)
    if name_match and not st.session_state.user_id:
        user_name = name_match.group(1).strip()
        # 检查用户是否存在
        all_data = load_all_memory()
        if user_name in all_data:
            st.info(f"💡 检测到您想以「{user_name}」身份登录，请在左侧侧边栏输入密码进行登录")
        else:
            st.info(f"💡 检测到新用户「{user_name}」，请在左侧侧边栏输入姓名和密码进行注册")
        # 不再自动登录，直接退出本次输入
        st.stop()
    
    # 添加用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # ===== 获取当前用户的数据 =====
    user_id = st.session_state.user_id if st.session_state.user_id else "游客"
    user_data = get_user_memory(user_id)
    
    # ===== 获取当前时间 =====
    now = datetime.now()
    time_str = now.strftime("%Y年%m月%d日 %H:%M:%S")

    knowledge_content = load_knowledge()
    
    # 格式化用户记忆内容
    memory_text = "【用户信息】\n"
    if user_data["用户信息"]:
        for key, value in user_data["用户信息"].items():
            memory_text += f"{key}：{value}\n"
    else:
        memory_text += "（暂无）\n"
    
    memory_text += "\n【待办任务】\n"
    if user_data["待办任务"]:
        urgent_tasks = []
        normal_tasks = []
        
        for i, task in enumerate(user_data["待办任务"], 1):
            task_str = f"{i}. {task['任务']}（截止：{task.get('截止时间', '无')}，状态：{task.get('状态', '未完成')}）"
            if task.get('状态') == '未完成':
                if '今天' in task.get('截止时间', '') or '明天' in task.get('截止时间', ''):
                    urgent_tasks.append(task_str)
                else:
                    normal_tasks.append(task_str)
            else:
                normal_tasks.append(task_str + " ✅")
        
        if urgent_tasks:
            memory_text += "⚠️ **紧急任务：**\n"
            for task in urgent_tasks:
                memory_text += f"{task}\n"
        if normal_tasks:
            if urgent_tasks:
                memory_text += "\n📋 **其他任务：**\n"
            for task in normal_tasks:
                memory_text += f"{task}\n"
    else:
        memory_text += "（暂无）\n"

    # 根据是否登录，调整系统指令
    if st.session_state.user_id:
        login_instruction = f"当前用户是 {user_id}，所有记忆都归属这个用户。"
    else:
        login_instruction = "当前是游客模式，用户还没有登录。如果用户想登录，请引导去侧边栏输入姓名和密码。"

    prompt_with_time = f"""【当前时间：{time_str}】
【用户状态：{"已登录" if st.session_state.user_id else "游客模式"}】
{login_instruction}

【你记得的关于用户的信息】
{memory_text}

【知识库内容（仅供参考）】
{knowledge_content}

【重要指令】
1. 你是一个自然的对话助手，回答问题时要自然、亲切，像朋友聊天一样
2. 知识库里的内容是你的背景知识，你可以参考它来回答问题
3. 【记忆】部分是你之前记住的关于当前用户的信息和待办任务，要优先使用
4. 回答时**绝对不要说**"根据文件内容""根据知识库""根据你提供的信息"这类话
5. 如果用户告诉了你新的个人信息（比如名字、年龄、喜好），要在回答中自然地记住它
6. 如果知识库里有相关信息，就自然地告诉用户；如果没有，就诚实地说你不知道
7. 如果有待办任务，在回答中自然地提醒用户（不要生硬地列出，要融入对话）

【用户问题】
{prompt}"""

    messages_for_api = st.session_state.messages.copy()
    messages_for_api[-1] = {"role": "user", "content": prompt_with_time}

    # ---------- 1. 提取个人信息 ----------
    memory_extraction_prompt = f"""请分析用户的消息，提取出值得记住的个人信息。

用户消息：{prompt}
当前用户：{user_id}

请从用户消息中提取以下类型的信息（如果有）：
- 姓名
- 年级（如：大一、大二、大三、大四、研一）
- 专业
- 性别
- 年龄
- 兴趣爱好
- 居住地
- 职业
- 其他重要信息（如：下半年大二、明年毕业等）

【重要】尽可能提取所有细节，不要漏掉信息。

请以 JSON 格式返回，例如：
{{"姓名": "张三", "年级": "大一", "专业": "计算机", "性别": "女", "兴趣爱好": "篮球", "下半年": "大二"}}

如果没有新信息，只返回：{{}}

注意：
1. 只返回 JSON，不要有其他内容
2. 尽量提取详细信息，不要简化
3. 如果用户说"下半年大二"，要记录"下半年"和"大二"两个信息
"""

    try:
        memory_response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[{"role": "user", "content": memory_extraction_prompt}],
            temperature=0.3,
            stream=False
        )

        memory_text_response = memory_response.choices[0].message.content.strip()

        try:
            new_memory = json.loads(memory_text_response)
            if new_memory:
                user_data = get_user_memory(user_id)
                if "用户信息" not in user_data:
                    user_data["用户信息"] = {}
                user_data["用户信息"].update(new_memory)
                save_user_memory(user_id, user_data)
                print(f"✅ 已保存用户信息：{new_memory}")

            # 如果提取到了姓名，且当前是游客模式，提示去登录
            if "姓名" in new_memory and not st.session_state.user_id:
                user_name = new_memory["姓名"]
                all_data = load_all_memory()
                if user_name in all_data:
                    st.info(f"💡 检测到您想以「{user_name}」身份登录，请在左侧侧边栏输入密码进行登录")
                else:
                    st.info(f"💡 检测到新用户「{user_name}」，请在左侧侧边栏输入姓名和密码进行注册")
        except json.JSONDecodeError:
            print(f"⚠️ 记忆提取失败，AI返回：{memory_text_response}")
    except Exception as e:
        print(f"⚠️ 记忆提取出错：{e}")
    
    # ---------- 2. 提取待办任务 ----------
    task_extraction_prompt = f"""请分析用户的消息，判断是否包含待办任务。

用户消息：{prompt}
当前用户：{user_id}

判断标准：
1. 如果用户提到"提醒我""帮我记一下""别忘了""明天要""记得""计划"等词，通常表示有任务
2. 任务需要有明确的内容，可能包含时间信息

如果有任务，请以 JSON 格式返回，格式如下：
{{"任务": "开会", "截止时间": "明天上午10点", "状态": "未完成"}}

如果没有任务，只返回：{{}}

注意：
1. 只返回 JSON，不要有其他内容
2. "截止时间"如果没有明确时间，填"无"
3. 状态固定为"未完成"
"""

    try:
        task_response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[{"role": "user", "content": task_extraction_prompt}],
            temperature=0.1,
            stream=False
        )
        
        task_text_response = task_response.choices[0].message.content.strip()
        
        try:
            new_task = json.loads(task_text_response)
            if new_task and "任务" in new_task:
                user_data = get_user_memory(user_id)
                if "待办任务" not in user_data:
                    user_data["待办任务"] = []
                user_data["待办任务"].append(new_task)
                save_user_memory(user_id, user_data)
                print(f"✅ 已保存任务：{new_task}")
        except json.JSONDecodeError:
            print(f"⚠️ 任务提取失败，AI返回：{task_text_response}")
    except Exception as e:
        print(f"⚠️ 任务提取出错：{e}")

    # ---------- 3. 管理任务（删除已完成的任务） ----------
    task_management_prompt = f"""请分析用户的消息，判断用户是否在说某个任务已经完成了。

用户消息：{prompt}
当前用户：{user_id}

判断标准：
1. 如果用户说"XX完成了""XX做好了""XX已经搞定了""XX做完了""XX好了"等，表示任务已完成
2. 如果用户说"不用提醒了""取消这个任务""删除这个任务"等，表示要删除任务
3. 任务名称应该从用户的描述中提取

如果用户提到了已完成或要删除的任务，请以 JSON 格式返回，格式如下：
{{"操作": "删除", "任务关键词": "还书"}}

如果没有提到已完成的任务，只返回：{{}}

注意：
1. 只返回 JSON，不要有其他内容
2. "操作"固定为"删除"
3. "任务关键词"是任务内容中的关键词，用于匹配要删除的任务
"""

    try:
        management_response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[{"role": "user", "content": task_management_prompt}],
            temperature=0.1,
            stream=False
        )
        
        management_text = management_response.choices[0].message.content.strip()
        
        try:
            management_data = json.loads(management_text)
            if management_data and management_data.get("操作") == "删除":
                keyword = management_data.get("任务关键词", "")
                if keyword:
                    user_data = get_user_memory(user_id)
                    if "待办任务" in user_data and user_data["待办任务"]:
                        original_count = len(user_data["待办任务"])
                        user_data["待办任务"] = [
                            task for task in user_data["待办任务"]
                            if keyword not in task.get("任务", "")
                        ]
                        new_count = len(user_data["待办任务"])
                        
                        if new_count < original_count:
                            save_user_memory(user_id, user_data)
                            print(f"✅ 已删除包含关键词 '{keyword}' 的任务（删除了 {original_count - new_count} 个）")
                        else:
                            print(f"⚠️ 未找到包含关键词 '{keyword}' 的任务")
        except json.JSONDecodeError:
            print(f"⚠️ 任务管理解析失败，AI返回：{management_text}")
    except Exception as e:
        print(f"⚠️ 任务管理出错：{e}")

    # ===== 调用 API（流式） =====
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""

        stream = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=messages_for_api,
            temperature=0.7,
            stream=True
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content
                response_placeholder.markdown(full_response + "▌")

        response_placeholder.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})
