import streamlit as st
import json
import pathlib
import asyncio
import html
from datetime import datetime
from main_app import process_narrative_message, get_rag_system
from config import Config
from memory_manager import MemoryManager
from story_summarizer import StorySummarizer

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

# 初始化记忆系统
if "memory_manager" not in st.session_state:
    st.session_state.memory_manager = MemoryManager(Config.MEMORY_DIR)

if "story_summarizer" not in st.session_state:
    st.session_state.story_summarizer = StorySummarizer(st.session_state.memory_manager)

if "memory_processing" not in st.session_state:
    st.session_state.memory_processing = False

if "show_complete_story" not in st.session_state:
    st.session_state.show_complete_story = False

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
    
    # 显示聊天统计和记忆状态
    st.markdown("### 📖 叙事统计")
    st.markdown(f"**当前会话消息数**: {len(st.session_state.narrative_messages)}")
    
    # 显示记忆统计
    try:
        memory_stats = st.session_state.story_summarizer.get_memory_stats()
        st.markdown("### 🧠 记忆统计")
        st.markdown(f"**当前会话ID**: {memory_stats['current_session_id']}")
        st.markdown(f"**当前会话梗概**: {memory_stats['current_session_summaries']} 个")
        st.markdown(f"**总计梗概**: {memory_stats['total_summaries']} 个")
        st.markdown(f"**总计故事**: {memory_stats['total_stories']} 个")
        st.markdown(f"**距离下次总结**: {memory_stats['messages_until_next_summary']} 条消息")
        
        if memory_stats['last_summary_time']:
            last_summary_time = datetime.fromisoformat(memory_stats['last_summary_time']).strftime("%m-%d %H:%M")
            st.markdown(f"**最近总结时间**: {last_summary_time}")
    except Exception as e:
        st.error(f"记忆统计错误: {e}")
    
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
    
    # 会话管理按钮
    st.markdown("### 🗂️ 会话管理")
    
    col_sess1, col_sess2 = st.columns([1, 1])
    with col_sess1:
        clear_ui_btn = st.button("🗑️ 清空UI显示", help="只清空界面显示，不影响记忆", use_container_width=True)
    with col_sess2:
        new_session_btn = st.button("🆕 开始新会话", help="结束当前会话，开始新的独立会话", use_container_width=True)
    
    # 重置设定按钮
    if st.button("🔄 重置所有设定", help="清空所有设定但保留记忆"):
        st.session_state.narrative_messages = []
        st.session_state.script_summary = ""
        st.session_state.current_stage = ""
        st.rerun()
    
    # 记忆管理按钮
    st.markdown("### 🧠 记忆管理")
    
    col_mem1, col_mem2 = st.columns([1, 1])
    with col_mem1:
        manual_summary_btn = st.button("📝 手动总结", help="立即总结最近的对话", use_container_width=True)
    with col_mem2:
        current_story_btn = st.button("📖 当前会话故事", help="生成当前会话的完整故事", use_container_width=True)
    
    generate_story_btn = st.button("📚 生成所有故事", help="将所有会话的梗概合成完整故事", use_container_width=True)
    
    # 危险操作区域
    st.markdown("### ⚠️ 危险操作")
    if st.button("🗑️ 清空所有记忆", help="删除所有聊天记录、梗概和故事", type="secondary"):
        if st.session_state.get("confirm_clear_memory", False):
            st.session_state.story_summarizer.clear_all_memories()
            st.session_state.narrative_messages = []
            st.session_state.script_summary = ""
            st.session_state.current_stage = ""
            st.session_state.confirm_clear_memory = False
            st.success("✅ 所有记忆已清空")
            st.rerun()
        else:
            st.session_state.confirm_clear_memory = True
            st.warning("⚠️ 再次点击确认清空所有记忆")
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
    
    **🧠 长期记忆功能：**
    - **自动总结**：每15次对话自动生成剧情梗概
    - **手动总结**：随时点击"手动总结"生成当前阶段梗概
    - **当前会话故事**：点击"当前会话故事"生成本次会话的完整故事
    - **所有故事**：点击"生成所有故事"将所有会话梗概合成完整故事
    - **语言风格**：根据剧本时代背景自动调整语言风格
    - **会话隔离**：每个会话的记忆独立管理，互不影响
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
    st.markdown('<div class="section-title">📚 剧本概要（全局背景）</div>', unsafe_allow_html=True)
    script_summary_input = st.text_area(
        "剧本概要输入",
        placeholder="例如：一个发生在1920年代阿卡姆镇的恐怖故事，调查员们需要调查一系列神秘失踪案件...",
        value=st.session_state.script_summary,
        height=200,
        key="script_summary_input",
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🎬 当前剧情阶段（场景信息）</div>', unsafe_allow_html=True)
    current_stage_input = st.text_area(
        "当前阶段输入",
        placeholder="例如：调查员们来到废弃的威尔逊庄园。这里曾经是失踪者最后出现的地方。夜色深沉，月光透过破败的窗户洒入大厅...",
        value=st.session_state.current_stage,
        height=200,
        key="current_stage_input",
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
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

# 右列 - 对话历史/完整故事
with col2:
    # 切换显示模式的选项卡
    tab1, tab2 = st.tabs(["💬 叙事对话历史", "📚 完整故事"])
    
    with tab1:
        # 显示消息统计
        if st.session_state.narrative_messages:
            total_messages = len(st.session_state.narrative_messages)
            kp_messages = len([m for m in st.session_state.narrative_messages if m["role"] == "kp"])
            ai_messages = len([m for m in st.session_state.narrative_messages if m["role"] == "ai"])
            
            st.markdown(f"""
            <div style="margin-bottom: 10px; padding: 8px; background-color: #f8f9fa; border-radius: 5px; font-size: 0.9em; color: #6c757d;">
                📊 总消息: {total_messages} | 🎪 KP: {kp_messages} | 🎭 AI: {ai_messages}
            </div>
            """, unsafe_allow_html=True)
        
        # 显示聊天历史 - 使用固定高度的滚动容器
        if st.session_state.narrative_messages:
            # 使用Streamlit内置的height参数创建固定高度容器
            with st.container(height=1000):
                # 显示所有消息
                for i, message in enumerate(st.session_state.narrative_messages):
                    if message["role"] == "kp":
                        st.markdown("🎪 **KP输入:**")
                        st.info(message["content"])
                    else:
                        st.markdown("🎭 **AI叙事:**")
                        st.success(message["content"])
                    
                    # 添加分隔线（最后一条消息不加）
                    if i < len(st.session_state.narrative_messages) - 1:
                        st.markdown("---")
        else:
            # 空状态也使用相同高度的容器保持布局一致
            with st.container(height=1000):
                st.info("📝 还没有叙事记录，开始你的第一个场景吧...")
    
    with tab2:
        # 显示完整故事
        if st.session_state.get("latest_complete_story"):
            st.markdown("### 📖 最新完整故事")
            story_data = st.session_state.latest_complete_story
            
            # 显示故事信息
            story_time = datetime.fromisoformat(story_data["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
            st.markdown(f"**生成时间**: {story_time}")
            st.markdown(f"**基于梗概数**: {story_data['summaries_count']} 个")
            if story_data.get("story_type"):
                st.markdown(f"**故事类型**: {story_data['story_type']}")
            
            # 显示故事内容
            st.markdown("---")
            st.markdown(story_data["story"])
        else:
            st.markdown("*还没有生成完整故事，先积累一些剧情后点击'生成完整故事'按钮...*")

# 处理会话管理按钮
if clear_ui_btn:
    st.session_state.narrative_messages = []
    st.success("✅ UI显示已清空，记忆系统不受影响")
    st.rerun()

if new_session_btn:
    # 开始新会话
    try:
        new_session_id = st.session_state.memory_manager.end_current_session_and_start_new(
            st.session_state.script_summary,
            st.session_state.current_stage
        )
        # 清空UI显示
        st.session_state.narrative_messages = []
        st.success(f"✅ 已开始新会话: {new_session_id}")
        st.rerun()
    except Exception as e:
        st.error(f"开始新会话时出错: {e}")

# 处理记忆管理按钮
if manual_summary_btn and not st.session_state.memory_processing:
    if not embedding_api_key:
        st.error("⚠️ 请先输入API密钥！")
    else:
        st.session_state.memory_processing = True
        with st.spinner("正在生成记忆总结..."):
            try:
                # 使用异步运行
                async def run_memory_summary():
                    success, result = await st.session_state.story_summarizer.trigger_memory_summary(embedding_api_key, force=True)
                    return success, result
                
                # 在同步环境中运行异步函数
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                success, result = loop.run_until_complete(run_memory_summary())
                
                if success:
                    st.success(f"✅ 记忆总结完成！\n\n{result[:200]}...")
                else:
                    st.error(f"❌ 记忆总结失败：{result}")
                
                st.session_state.memory_processing = False
                st.rerun()
                
            except Exception as e:
                st.session_state.memory_processing = False
                st.error(f"处理记忆总结时出错: {e}")
                st.rerun()

if current_story_btn and not st.session_state.memory_processing:
    if not embedding_api_key:
        st.error("⚠️ 请先输入API密钥！")
    else:
        st.session_state.memory_processing = True
        with st.spinner("正在生成当前会话故事..."):
            try:
                # 使用异步运行
                async def run_current_session_story():
                    success, result = await st.session_state.story_summarizer.generate_current_session_story(embedding_api_key)
                    return success, result
                
                # 在同步环境中运行异步函数
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                success, result = loop.run_until_complete(run_current_session_story())
                
                if success:
                    # 保存最新故事到session_state以便显示
                    latest_story = st.session_state.story_summarizer.get_latest_story()
                    if latest_story:
                        st.session_state.latest_complete_story = latest_story
                        
                        # 调试信息
                        st.write(f"**调试**: 故事已生成，长度: {len(result) if result else 0} 字符")
                        st.write(f"**调试**: latest_story数据: 已获取")
                        st.write(f"**调试**: 故事预览: {latest_story['story'][:200]}...")
                        
                        st.success("✅ 当前会话故事生成成功！请查看'完整故事'选项卡")
                    else:
                        st.error("❌ 故事生成成功但无法获取故事数据")
                        st.write(f"**调试**: 生成结果: {result[:200] if result else '空'}...")
                else:
                    st.error(f"❌ 当前会话故事生成失败：{result}")
                
                st.session_state.memory_processing = False
                st.rerun()
                
            except Exception as e:
                st.session_state.memory_processing = False
                st.error(f"生成当前会话故事时出错: {e}")
                st.rerun()

if generate_story_btn and not st.session_state.memory_processing:
    if not embedding_api_key:
        st.error("⚠️ 请先输入API密钥！")
    else:
        st.session_state.memory_processing = True
        with st.spinner("正在生成完整故事...这可能需要一些时间..."):
            try:
                # 使用异步运行
                async def run_story_generation():
                    success, result = await st.session_state.story_summarizer.generate_complete_story(embedding_api_key)
                    return success, result
                
                # 在同步环境中运行异步函数
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                success, result = loop.run_until_complete(run_story_generation())
                
                if success:
                    # 保存最新故事到session_state以便显示
                    latest_story = st.session_state.story_summarizer.get_latest_story()
                    if latest_story:
                        st.session_state.latest_complete_story = latest_story
                        
                        # 调试信息
                        st.write(f"**调试**: 完整故事已生成，长度: {len(result) if result else 0} 字符")
                        st.write(f"**调试**: latest_story数据: 已获取")
                        st.write(f"**调试**: 故事预览: {latest_story['story'][:200]}...")
                        
                        st.success("✅ 完整故事生成成功！请查看'完整故事'选项卡")
                    else:
                        st.error("❌ 故事生成成功但无法获取故事数据")
                        st.write(f"**调试**: 生成结果: {result[:200] if result else '空'}...")
                else:
                    st.error(f"❌ 故事生成失败：{result}")
                
                st.session_state.memory_processing = False
                st.rerun()
                
            except Exception as e:
                st.session_state.memory_processing = False
                st.error(f"生成完整故事时出错: {e}")
                st.rerun()

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
        
        # 添加KP消息到UI显示
        kp_message = f"玩家行动: {narrative_data['player_action']}"
        st.session_state.narrative_messages.append({"role": "kp", "content": kp_message})
        
        # 添加KP消息到记忆系统
        need_summary = st.session_state.memory_manager.add_message(
            "kp", 
            narrative_data['player_action'],
            narrative_data['script_summary'],
            narrative_data['current_stage']
        )
        
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
                    # 添加AI消息到UI显示
                    st.session_state.narrative_messages.append({"role": "ai", "content": ai_narrative})
                    
                    # 添加AI消息到记忆系统
                    need_summary_ai = st.session_state.memory_manager.add_message(
                        "ai", 
                        ai_narrative,
                        narrative_data['script_summary'],
                        narrative_data['current_stage']
                    )
                    
                    # 检查是否需要自动总结（任一消息触发15次阈值）
                    if need_summary or need_summary_ai:
                        st.info("🧠 达到15次对话，正在自动生成记忆总结...")
                        try:
                            # 异步运行自动总结
                            async def run_auto_summary():
                                success, result = await st.session_state.story_summarizer.trigger_memory_summary(narrative_data['embedding_api_key'])
                                return success, result
                            
                            # 在同步环境中运行异步函数
                            try:
                                loop = asyncio.get_event_loop()
                            except RuntimeError:
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                            
                            success, summary_result = loop.run_until_complete(run_auto_summary())
                            
                            if success:
                                st.success(f"✅ 自动记忆总结完成！\n\n{summary_result[:150]}...")
                            else:
                                st.warning(f"⚠️ 自动总结失败，但对话已保存：{summary_result}")
                                
                        except Exception as summary_error:
                            st.warning(f"⚠️ 自动总结遇到问题，但对话已保存：{summary_error}")
                
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
