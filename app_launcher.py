import streamlit as st
import subprocess
import sys
import os

# 页面配置
st.set_page_config(
    page_title="COC跑团工具集合",
    page_icon="🐙",
    layout="wide"
)

# 自定义CSS样式
st.markdown("""
<style>
.main-title {
    color: #dc2626;
    text-align: center;
    font-family: 'Courier New', monospace;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    font-size: 3rem;
    margin-bottom: 1rem;
}

.subtitle {
    text-align: center;
    color: #666;
    font-size: 1.2rem;
    margin-bottom: 3rem;
}

.tool-card {
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    padding: 2rem;
    border-radius: 1rem;
    border: 2px solid #e2e8f0;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    margin: 1rem 0;
    transition: all 0.3s ease;
    height: 300px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.tool-card:hover {
    border-color: #dc2626;
    box-shadow: 0 8px 25px rgba(220, 38, 38, 0.15);
    transform: translateY(-2px);
}

.tool-icon {
    font-size: 4rem;
    text-align: center;
    margin-bottom: 1rem;
}

.tool-title {
    font-size: 1.5rem;
    font-weight: bold;
    color: #1f2937;
    text-align: center;
    margin-bottom: 1rem;
}

.tool-description {
    color: #6b7280;
    text-align: center;
    line-height: 1.6;
    flex-grow: 1;
}

.tool-features {
    color: #374151;
    font-size: 0.9rem;
    margin-top: 1rem;
}

.cthulhu-quote {
    text-align: center;
    font-style: italic;
    color: #7c2d12;
    font-size: 1rem;
    margin: 2rem 0;
    padding: 1rem;
    background-color: #fef2f2;
    border-left: 4px solid #dc2626;
    border-radius: 0.5rem;
}

.launch-button {
    background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
    color: white;
    border: none;
    padding: 0.75rem 2rem;
    border-radius: 0.5rem;
    font-weight: bold;
    font-size: 1rem;
    cursor: pointer;
    transition: all 0.3s ease;
    width: 100%;
    margin-top: 1rem;
}

.launch-button:hover {
    background: linear-gradient(135deg, #991b1b 0%, #7f1d1d 100%);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3);
}
</style>
""", unsafe_allow_html=True)

# 主标题
st.markdown('<h1 class="main-title">🐙 COC跑团工具集合 🐙</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">克苏鲁的呼唤 - 专业跑团辅助工具</p>', unsafe_allow_html=True)

# 克苏鲁语录
st.markdown("""
<div class="cthulhu-quote">
"我们生活在一个平静的无知之岛上，被漆黑的无尽海洋包围，而我们并不应该航行过远。"<br>
—— H.P. Lovecraft
</div>
""", unsafe_allow_html=True)

# 工具选择
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="tool-card">
        <div class="tool-icon">🔍</div>
        <div class="tool-title">COC规则助手</div>
        <div class="tool-description">
            专业的克苏鲁的呼唤规则查询工具，基于COC第六版规则手册构建的智能助手。
            可以回答各种规则问题，帮助KP和玩家快速理解游戏机制。
        </div>
        <div class="tool-features">
            ✅ 规则查询与解释<br>
            ✅ 技能属性说明<br>
            ✅ 战斗系统指导<br>
            ✅ 理智检定规则<br>
            ✅ COC知识库检索
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🔍 启动COC规则助手", key="rules_assistant", use_container_width=True, type="primary"):
        st.info("正在启动COC规则助手...")
        st.markdown("请在新的终端窗口中运行以下命令：")
        st.code("streamlit run streamlit_app.py", language="bash")
        st.markdown("或者点击下方链接直接访问：")
        st.markdown("[COC规则助手](http://localhost:8501)")

with col2:
    st.markdown("""
    <div class="tool-card">
        <div class="tool-icon">🎭</div>
        <div class="tool-title">KP叙事辅助工具</div>
        <div class="tool-description">
            专为守秘人(KP)设计的AI叙事伙伴，通过四层信息输入结构，
            帮助KP生成高质量、情境相关的游戏描述。
        </div>
        <div class="tool-features">
            ✅ 剧本概要设定<br>
            ✅ 当前阶段管理<br>
            ✅ 玩家行动响应<br>
            ✅ 聊天记录上下文<br>
            ✅ 智能叙事生成
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🎭 启动KP叙事工具", key="narrative_assistant", use_container_width=True, type="primary"):
        st.info("正在启动KP叙事辅助工具...")
        st.markdown("请在新的终端窗口中运行以下命令：")
        st.code("streamlit run kp_narrative_app.py --server.port 8502", language="bash")
        st.markdown("或者点击下方链接直接访问：")
        st.markdown("[KP叙事工具](http://localhost:8502)")

# 使用指南
st.markdown("---")
st.markdown("### 📚 使用指南")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **COC规则助手适用于：**
    - 新手KP和玩家学习规则
    - 游戏中快速查询规则条目
    - 理解复杂的游戏机制
    - 获取COC知识库信息
    - 角色创建指导
    """)

with col2:
    st.markdown("""
    **KP叙事工具适用于：**
    - 经验丰富的KP进行叙事创作
    - 需要快速生成场景描述
    - 保持故事连贯性和氛围
    - 处理玩家意外行动
    - 丰富游戏体验
    """)

# 技术信息
st.markdown("---")
st.markdown("### ⚙️ 技术特性")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    **核心技术**
    - 🤖 大语言模型 (DeepSeek-V3)
    - 🔍 RAG检索增强生成
    - 📊 向量数据库 (FAISS)
    - 🌐 Streamlit界面
    """)

with col2:
    st.markdown("""
    **数据支持**
    - 📖 COC第六版完整规则
    - 🎲 技能属性详细说明
    - ⚔️ 战斗系统规则
    - 🧠 理智系统机制
    """)

with col3:
    st.markdown("""
    **功能特色**
    - 💾 会话状态保持
    - 📝 对话历史记录
    - 🎪 情境感知生成
    - 🔧 灵活配置选项
    """)

# 底部信息
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9em;'>
🐙 COC跑团工具集合 | 让恐怖与乐趣并存 🐙<br>
<em>愿你的理智值永远不会归零，愿你的故事永远引人入胜</em>
</div>
""", unsafe_allow_html=True)

# 版本信息
st.caption("版本: 1.0.0 | 最后更新: 2024年12月")
