# 知行 AI 学习助手

一个基于 Streamlit 与 DeepSeek API 的个人学习工作台，支持资料问答、用户记忆、待办管理和本地知识库。

## 功能

- 结合本地课程与制度资料进行对话
- 自动识别个人信息和待办操作
- 游客模式，以及带独立数据空间的本地账户
- 可视化任务管理与 TXT 知识库管理
- 响应式界面、键盘焦点、降低动态效果等无障碍支持

## 本地运行

建议使用 Python 3.11–3.13。

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
streamlit run chat_ui.py
```

然后在 `.streamlit/secrets.toml` 中填写：

```toml
DEEPSEEK_API_KEY = "你的 API Key"
```

也可以通过环境变量 `DEEPSEEK_API_KEY` 提供密钥。

## 项目结构

```text
app/
  assistant.py   AI 调用、消息分析与任务动作
  config.py      路径和运行配置
  knowledge.py   知识库文件边界与读取
  storage.py     用户数据、密码哈希和原子写入
design-system/
  MASTER.md      UI/UX 设计规范
tests/           核心逻辑测试
chat_ui.py       Streamlit 页面与交互
```

## 数据与安全

- API Key 不应提交到 Git；真实 secrets 文件已在 `.gitignore` 中排除。
- 新密码使用带随机盐的 PBKDF2-SHA256 存储，旧版 SHA-256 数据会在成功登录后自动升级。
- `memory.json` 包含用户资料和任务，默认不会提交到 Git。
- 该账户系统适合个人或可信环境部署；公开多实例部署建议改用正式数据库与认证服务。

## 测试

```bash
python3 -m unittest discover -s tests -v
```

PDF 转换工具仍可独立使用：

```bash
python3 pdf_to_knowledge.py 文件名.pdf
```
