import streamlit as st
import json
import pathlib
from datetime import datetime
from main_app import process_narrative_message, get_rag_system
from config import Config

# 页面配置
st.set_page_config(
    page_title="COC KP叙事辅助工具",
    page_icon="🎭",
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

.kp-message {
    background-color: #e8f5e8;
    border-left-color: #4ade80;
    color: #2d5a2d;
}

.ai-narrative {
    background-color: #f3e8ff;
    border-left-color: #8b5cf6;
    color: #4c1d95;
}

.horror-title {
    color: #7c2d12;
    text-align: center;
    font-family: 'Courier New', monospace;
    text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
}

.input-section {
    background-color: #f8fafc;
    padding: 1rem;
    border-radius: 0.5rem;
    border: 1px solid #e2e8f0;
    margin: 1rem 0;
}

.section-title {
    color: #475569;
    font-weight: bold;
    margin-bottom: 0.5rem;
}

.warning-box {
    background-color: #fdf2f8;
    padding: 10px;
    border-radius: 5px;
    border-left: 4px solid #dc2626;
    color: #7c2d12;
}

.context-info {
    background-color: #eff6ff;
    padding: 10px;
    border-radius: 5px;
    border-left: 4px solid #3b82f6;
    color: #1e40af;
    font-size: 0.9em;
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)

# 标题
st.markdown(f"<h1 class='horror-title'>🎭 COC KP叙事辅助工具 🎭</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #666;'>为守秘人量身打造的AI叙事伙伴</h3>", unsafe_allow_html=True)

# 初始化会话状态
if "narrative_messages" not in st.session_state:
    st.session_state.narrative_messages = []

if "script_summary" not in st.session_state:
    st.session_state.script_summary = ""

if "current_stage" not in st.session_state:
    st.session_state.current_stage = ""

if "rag_system_loaded" not in st.session_state:
    st.session_state.rag_system_loaded = False

if "processing" not in st.session_state:
    st.session_state.processing = False

if "message_counter" not in st.session_state:
    st.session_state.message_counter = 0

if "pending_narrative" not in st.session_state:
    st.session_state.pending_narrative = None

if "last_api_key" not in st.session_state:
    st.session_state.last_api_key = None

# 侧边栏 - 应用信息和统计
with st.sidebar:
    st.markdown("### 🔑 API配置")
    
    # API密钥输入
    embedding_api_key = st.text_input(
        "DashScope API密钥",
        type="password",
        placeholder="请输入您的DashScope API密钥",
        help="用于文本向量化和LLM生成，获取地址：https://dashscope.aliyun.com/"
    )
    
    st.markdown("### 📊 应用状态")
    
    # 检查API密钥
    if not embedding_api_key:
        st.warning("⚠️ 请输入API密钥")
        st.session_state.rag_system_loaded = False
        st.session_state.last_api_key = None
    else:
        # 检查API密钥是否改变
        if st.session_state.last_api_key != embedding_api_key:
            st.session_state.rag_system_loaded = False
            st.session_state.last_api_key = embedding_api_key
        
        # 检查RAG系统状态
        if not st.session_state.rag_system_loaded:
            with st.spinner("正在初始化古老的知识库..."):
                try:
                    get_rag_system(embedding_api_key, embedding_api_key)
                    st.session_state.rag_system_loaded = True
                    st.success("✅ RAG系统已加载")
                except Exception as e:
                    st.error(f"❌ RAG系统加载失败: {e}")
                    st.session_state.rag_system_loaded = False
        else:
            st.success("✅ RAG系统已加载")
    
    # 显示聊天统计
    st.markdown("### 📖 叙事统计")
    st.markdown(f"**当前会话消息数**: {len(st.session_state.narrative_messages)}")
    
    # 显示当前设定状态
    st.markdown("### 🎪 当前设定状态")
    if st.session_state.script_summary:
        st.markdown("✅ **剧本概要**: 已设定")
    else:
        st.markdown("❌ **剧本概要**: 未设定")
    
    if st.session_state.current_stage:
        st.markdown("✅ **当前阶段**: 已设定")
    else:
        st.markdown("❌ **当前阶段**: 未设定")
    
    # 清空聊天记录按钮
    if st.button("🗑️ 清空当前会话"):
        st.session_state.narrative_messages = []
        st.rerun()
    
    # 重置设定按钮
    if st.button("🔄 重置所有设定"):
        st.session_state.narrative_messages = []
        st.session_state.script_summary = ""
        st.session_state.current_stage = ""
        st.rerun()
    
    # 应用说明
    st.markdown("### 📖 使用说明")
    st.markdown("""
    **四层信息输入结构：**
    1. **剧本概要** - 设定全局背景
    2. **当前阶段** - 场景静态信息
    3. **玩家选择** - 即时动态触发器
    4. **聊天记录** - 提供上下文连贯性
    
    **使用流程：**
    - 首次使用时设定剧本概要
    - 场景切换时更新当前阶段
    - 每次输入玩家行动获取叙事
    - AI会结合知识库生成描述
    """)
    
    st.markdown("### ⚠️ 提示")
    st.markdown("""
    <div class='warning-box'>
    剧本概要和当前阶段可以留空，系统会沿用上次设定。必须输入玩家选择才能生成叙事。
    </div>
    """, unsafe_allow_html=True)

# 主要内容区域
col1, col2 = st.columns([1, 1])

# 左列 - 输入区域
with col1:
    st.markdown("### 🎪 场景设定")
    
    # 剧本概要输入
    st.markdown('<div class="input-section">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📚 剧本概要（全局背景）</div>', unsafe_allow_html=True)
    script_summary_input = st.text_area(
        "剧本概要输入",
        placeholder="例如：一个发生在1920年代阿卡姆镇的恐怖故事，调查员们需要调查一系列神秘失踪案件...",
        value=st.session_state.script_summary,
        height=120,
        key="script_summary_input",
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 当前阶段输入
    st.markdown('<div class="input-section">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🎬 当前剧情阶段（场景信息）</div>', unsafe_allow_html=True)
    current_stage_input = st.text_area(
        "当前阶段输入",
        placeholder="例如：调查员们来到废弃的威尔逊庄园。这里曾经是失踪者最后出现的地方。夜色深沉，月光透过破败的窗户洒入大厅...",
        value=st.session_state.current_stage,
        height=120,
        key="current_stage_input",
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 玩家选择输入
    st.markdown('<div class="input-section">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🎯 玩家选择（必填）</div>', unsafe_allow_html=True)
    player_action = st.text_area(
        "玩家选择输入",
        placeholder="例如：玩家决定仔细搜查大厅，寻找任何线索...",
        height=100,
        key="player_action_input",
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 显示当前上下文信息
    if st.session_state.script_summary or st.session_state.current_stage:
        st.markdown("""
        <div class='context-info'>
        <strong>📝 当前上下文：</strong><br>
        """, unsafe_allow_html=True)
        if st.session_state.script_summary:
            st.markdown(f"**剧本概要**: {st.session_state.script_summary[:100]}{'...' if len(st.session_state.script_summary) > 100 else ''}")
        if st.session_state.current_stage:
            st.markdown(f"**当前阶段**: {st.session_state.current_stage[:100]}{'...' if len(st.session_state.current_stage) > 100 else ''}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 发送按钮
    col_btn1, col_btn2 = st.columns([1, 1])
    with col_btn1:
        generate_button = st.button("🎭 生成叙事", type="primary", use_container_width=True)
    with col_btn2:
        example_button = st.button("💡 示例场景", use_container_width=True)

# 右列 - 对话历史
with col2:
    st.markdown("### 💬 叙事对话历史")
    
    # 显示聊天历史
    if st.session_state.narrative_messages:
        for message in st.session_state.narrative_messages:
            if message["role"] == "kp":
                st.markdown(f"""
                <div class="chat-message kp-message">
                    <strong>🎪 输入:</strong> {message["content"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message ai-narrative">
                    <strong>🎭 叙事:</strong> {message["content"]}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown("*还没有叙事记录，开始你的第一个场景吧...*")

# 处理示例按钮
if example_button and not st.session_state.processing:
    st.session_state.script_summary = """
一个发生在1920年代阿卡姆镇的恐怖故事。当地连续发生了三起神秘失踪案件，失踪者都是在夜间独自外出后再也没有回来。最后的目击地点都指向镇外的一座废弃庄园。当地警方束手无策，一群经验丰富的调查员决定亲自前往调查真相。
"""
    st.session_state.current_stage = """
调查员们在月黑风高的夜晚来到了威尔逊庄园的大门前。这座维多利亚风格的建筑已经废弃了十多年，藤蔓爬满了外墙，窗户多数破碎。庄园被高大的铁栅栏围绕，生锈的大门半开着，发出令人不安的吱嘎声。远处偶尔传来夜枭的啼叫，让这个地方显得更加阴森恐怖。
"""
    st.rerun()

# 处理生成叙事按钮
if generate_button and player_action.strip() and not st.session_state.processing:
    if not embedding_api_key:
        st.error("⚠️ 请先在侧边栏输入API密钥！")
    else:
        # 更新设定状态
        if script_summary_input.strip():
            st.session_state.script_summary = script_summary_input.strip()
        if current_stage_input.strip():
            st.session_state.current_stage = current_stage_input.strip()
        
        # 设置待处理消息
        st.session_state.pending_narrative = {
            "script_summary": st.session_state.script_summary,
            "current_stage": st.session_state.current_stage,
            "player_action": player_action.strip(),
            "embedding_api_key": embedding_api_key,
            "llm_api_key": embedding_api_key
        }
        st.session_state.message_counter += 1

# 实际处理叙事生成（只处理一次）
if st.session_state.pending_narrative and not st.session_state.processing:
    if not st.session_state.rag_system_loaded:
        st.error("❌ RAG系统未加载，请等待初始化完成")
        st.session_state.pending_narrative = None
    else:
        narrative_data = st.session_state.pending_narrative
        st.session_state.pending_narrative = None  # 立即清除，防止重复
        st.session_state.processing = True
        
        # 添加KP消息
        kp_message = f"玩家行动: {narrative_data['player_action']}"
        st.session_state.narrative_messages.append({"role": "kp", "content": kp_message})
        
        # 处理叙事生成
        with st.spinner("助手正在编织你的故事..."):
            try:
                ai_narrative = process_narrative_message(
                    narrative_data['script_summary'],
                    narrative_data['current_stage'],
                    narrative_data['player_action'],
                    st.session_state.narrative_messages[-10:],  # 获取最近10条消息作为上下文
                    narrative_data['embedding_api_key'],
                    narrative_data['llm_api_key']
                )
                if ai_narrative:
                    st.session_state.narrative_messages.append({"role": "ai", "content": ai_narrative})
                
                # 重置状态
                st.session_state.processing = False
                st.rerun()
                
            except Exception as e:
                st.session_state.processing = False
                st.error(f"在黑暗的深渊中遇到了错误: {e}")
                st.rerun()

elif generate_button and not player_action.strip():
    st.error("⚠️ 请输入玩家选择！")

# 底部信息
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.8em;'>
🎭 COC KP叙事辅助工具 | 让AI成为你的创作伙伴 🎭<br>
<em>"在恐怖与未知之间，编织最扣人心弦的故事..."</em>
</div>
""", unsafe_allow_html=True)

# 显示当前时间
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.caption(f"当前时间: {current_time}")
