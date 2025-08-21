import streamlit as st
import json
import pathlib
from datetime import datetime
from main_app import process_message, get_rag_system
from config import Config

# 页面配置
st.set_page_config(
    page_title=Config.APP_TITLE,
    page_icon="🐙",
    layout="wide"
)

# 自定义CSS样式
st.markdown("""
<style>
.chat-message {
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
    border-left: 4px solid;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.user-message {
    background-color: #e8f5e8;
    border-left-color: #4ade80;
    color: #2d5a2d;
}

.ai-message {
    background-color: #fef2f2;
    border-left-color: #dc2626;
    color: #7f1d1d;
}

.horror-title {
    color: #dc2626;
    text-align: center;
    font-family: 'Courier New', monospace;
    text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
}

.stats-box {
    background-color: #f8f9fa;
    padding: 1rem;
    border-radius: 0.5rem;
    border: 1px solid #dee2e6;
}

.warning-box {
    background-color: #fdf2f8;
    padding: 10px;
    border-radius: 5px;
    border-left: 4px solid #dc2626;
    color: #7c2d12;
}
</style>
""", unsafe_allow_html=True)

# 标题
st.markdown(f"<h1 class='horror-title'>🐙 {Config.APP_TITLE} 🐙</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #666;'>在古老的知识中寻找真相，但小心你的理智...</h3>", unsafe_allow_html=True)

# 初始化会话状态
if "messages" not in st.session_state:
    st.session_state.messages = []

if "rag_system_loaded" not in st.session_state:
    st.session_state.rag_system_loaded = False

if "processing" not in st.session_state:
    st.session_state.processing = False

if "message_counter" not in st.session_state:
    st.session_state.message_counter = 0

if "pending_message" not in st.session_state:
    st.session_state.pending_message = None

if "last_api_key" not in st.session_state:
    st.session_state.last_api_key = None

# 侧边栏 - 应用信息和统计
with st.sidebar:
    st.markdown("### 🔑 API配置")
    
    # API密钥输入
    api_key = st.text_input(
        "DashScope API密钥",
        type="password",
        placeholder="请输入您的DashScope API密钥",
        help="用于文本向量化和LLM生成，获取地址：https://dashscope.aliyun.com/"
    )
    
    st.markdown("### 📊 应用状态")
    
    # 检查API密钥
    if not api_key:
        st.warning("⚠️ 请输入API密钥")
        st.session_state.rag_system_loaded = False
        st.session_state.last_api_key = None
    else:
        # 检查API密钥是否改变
        if st.session_state.last_api_key != api_key:
            st.session_state.rag_system_loaded = False
            st.session_state.last_api_key = api_key
        
        # 检查RAG系统状态
        if not st.session_state.rag_system_loaded:
            with st.spinner("正在初始化古老的知识库..."):
                try:
                    get_rag_system(api_key, api_key)
                    st.session_state.rag_system_loaded = True
                    st.success("✅ RAG系统已加载")
                except Exception as e:
                    st.error(f"❌ RAG系统加载失败: {e}")
                    st.session_state.rag_system_loaded = False
        else:
            st.success("✅ RAG系统已加载")
    
    # 显示聊天统计
    st.markdown("### 💬 聊天统计")
    st.markdown(f"**当前会话消息数**: {len(st.session_state.messages)}")
    
    # 显示历史聊天记录统计
    log_file = pathlib.Path("chat_logs.json")
    if log_file.exists():
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            st.markdown(f"**历史消息总数**: {len(logs)}")
        except:
            st.markdown("**历史消息总数**: 无法读取")
    else:
        st.markdown("**历史消息总数**: 0")
    
    # 清空聊天记录按钮
    if st.button("🗑️ 清空当前会话"):
        st.session_state.messages = []
        st.session_state.current_input = ""
        st.rerun()
    
    # 应用说明
    st.markdown("### 📖 使用说明")
    st.markdown("""
    - 询问COC规则相关问题
    - 寻求角色创建建议
    - 了解技能和属性说明
    - 探索克苏鲁神话知识
    - 获得跑团建议
    """)
    
    st.markdown("### ⚠️ 警告")
    st.markdown("""
    <div class='warning-box'>
    深入研究克苏鲁神话可能会影响你的理智值。请谨慎提问，在黑暗的真相面前保持清醒...
    </div>
    """, unsafe_allow_html=True)

# 主要聊天界面
st.markdown("### 🎭 与古老的智慧对话")

# 显示聊天历史
if st.session_state.messages:
    st.markdown(f"*当前共有 {len(st.session_state.messages)} 条消息*")
    
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f"""
        <div class="chat-message user-message">
            <strong>🧙‍♂️ 调查员:</strong> {message["content"]}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="chat-message ai-message">
            <strong>🐙 古老的智慧:</strong> {message["content"]}
        </div>
        """, unsafe_allow_html=True)
else:
    st.markdown("*还没有对话记录，开始你的第一个问题吧...*")

# 用户输入
if "current_input" not in st.session_state:
    st.session_state.current_input = ""

user_input = st.text_input(
    "向古老的智慧询问...", 
    placeholder="例如：什么是理智检定？如何创建调查员？",
    value=st.session_state.current_input,
    key="user_input"
)

# 发送消息按钮
col1, col2, col3 = st.columns([1, 1, 4])

with col1:
    send_button = st.button("📤 发送", type="primary")

with col2:
    random_button = st.button("🎲 随机问题")
    
# 处理随机问题按钮
if random_button and not st.session_state.processing:
    if not api_key:
        st.error("⚠️ 请先在侧边栏输入API密钥！")
    else:
        sample_questions = [
            "什么是理智检定？",
            "如何创建一个调查员角色？", 
            "COC中的技能系统是如何运作的？",
            "什么是克苏鲁神话技能？",
            "战斗系统的规则是什么？",
            "如何处理角色的疯狂状态？",
            "什么是伤害奖励？",
            "毒药的规则是怎样的？"
        ]
        import random
        selected_question = random.choice(sample_questions)
        st.session_state.pending_message = selected_question
        st.session_state.message_counter += 1

# 处理发送按钮
if send_button and user_input.strip() and not st.session_state.processing:
    if not api_key:
        st.error("⚠️ 请先在侧边栏输入API密钥！")
    else:
        st.session_state.pending_message = user_input
        st.session_state.message_counter += 1

# 实际处理消息（只处理一次）
if st.session_state.pending_message and not st.session_state.processing:
    if not st.session_state.rag_system_loaded:
        st.error("❌ RAG系统未加载，请等待初始化完成")
        st.session_state.pending_message = None
    else:
        message_to_process = st.session_state.pending_message
        st.session_state.pending_message = None  # 立即清除，防止重复
        st.session_state.processing = True
        
        # 添加用户消息
        st.session_state.messages.append({"role": "user", "content": message_to_process})
        
        # 处理消息
        with st.spinner("古老的存在正在思考你的问题..."):
            try:
                ai_response = process_message(message_to_process, api_key, api_key)
                if ai_response:
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})
                
                # 清空输入框并重置状态
                st.session_state.current_input = ""
                st.session_state.processing = False
                st.rerun()
                
            except Exception as e:
                st.session_state.processing = False
                st.error(f"在黑暗的深渊中遇到了错误: {e}")
                st.rerun()

# 底部信息
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.8em;'>
🐙 基于COC第六版规则的AI助手 | 愿你的理智值永远不会归零 🐙<br>
<em>"我们生活在一个平静的无知之岛上，被漆黑的无尽海洋包围，而我们并不应该航行过远。"</em> - H.P. Lovecraft
</div>
""", unsafe_allow_html=True)

# 显示当前时间
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.caption(f"当前时间: {current_time}")
