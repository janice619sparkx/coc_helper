# COC跑团AI助手部署说明

## 基本信息
- 应用名称：COC克苏鲁跑团AI助手
- 主要功能：为KP（守秘人）提供叙事辅助和规则查询
- 技术栈：Streamlit + DashScope + FAISS

## 新增功能 🆕
### 长期记忆系统
- **自动总结**：每15次对话自动生成300-500字剧情梗概
- **手动总结**：支持随时手动触发记忆总结
- **完整故事生成**：将所有梗概整合成连贯的完整故事
- **智能语言风格**：根据剧本时代背景自动调整叙事风格
- **数据持久化**：所有记忆数据本地存储，支持跨会话保持

## Streamlit Cloud 部署步骤

### 1. 推送代码到GitHub
- 确保所有文件都已提交到GitHub仓库
- 包含最新的requirements.txt和runtime.txt
- 新增memory_manager.py和story_summarizer.py文件

### 2. Streamlit Cloud配置
- 访问 [Streamlit Cloud](https://share.streamlit.io/)
- 连接你的GitHub仓库
- 选择主文件：`kp_narrative_app.py` 或 `streamlit_app.py`
- 设置分支：`main`

### 3. 环境要求
- Python 3.11 (通过runtime.txt指定)
- 所有依赖通过requirements.txt自动安装

## 本地部署步骤

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置API密钥
在Streamlit界面中输入DashScope API密钥，或在config.py中配置默认值

### 3. 启动应用
```bash
# KP叙事工具（推荐）
streamlit run kp_narrative_app.py

# 或COC规则助手
streamlit run streamlit_app.py

# 或应用选择器
streamlit run app_launcher.py
```

## 配置说明
- `config.py`：包含系统提示词和各种配置参数
- `faiss_index/`：向量数据库文件存储目录
- `rag_documents.txt`：知识库文档源文件
- `memory_data/`：长期记忆数据存储目录（自动创建）

## 功能模块
1. **主应用**（main_app.py）：核心问答功能
2. **KP叙事助手**（kp_narrative_app.py）：叙事辅助工具
3. **应用启动器**（app_launcher.py）：多应用切换界面
4. **记忆管理器**（memory_manager.py）：🆕 聊天记录存储和自动总结
5. **故事总结器**（story_summarizer.py）：🆕 梗概管理和完整故事生成

## 记忆系统数据结构
```
memory_data/
├── chat_sessions.json    # 完整聊天记录和会话信息
├── summaries.json       # 每15次对话的梗概总结
└── story_archive.json   # 完整故事存档
```

## 长期记忆功能使用指南

### 自动总结功能
- 系统会在每15次对话后自动触发记忆总结
- 总结内容包含重要发现、线索和剧情转折
- 保持COC恐怖氛围的语调风格

### 手动总结功能
- 在侧边栏点击"📝 手动总结"按钮
- 适用于想要在重要剧情节点手动保存记忆的情况
- 至少需要5条消息才能进行总结

### 完整故事生成
- 点击"📚 生成完整故事"按钮
- 系统会将所有已保存的梗概整合成连贯的完整故事
- 根据剧本背景自动调整语言风格：
  - 民国时期：半文半白风格
  - 中世纪：古朴典雅风格
  - 现代：简洁直白风格
  - 西方背景：优雅翻译体风格

### 记忆管理
- 支持清空当前会话（保留历史梗概）
- 支持完全清空所有记忆（需二次确认）
- 所有数据本地存储，支持跨会话保持

## 依赖说明

### 关键更新
- 移除了pandas依赖（未实际使用）
- 更新numpy到兼容版本(>=1.26.0)
- 使用范围版本号而非固定版本

### 核心依赖
- `streamlit`: Web界面框架
- `openai`: AI模型API客户端
- `faiss-cpu`: 向量数据库
- `numpy`: 数值计算库
- `httpx`: HTTP请求库
- `filelock`: 文件锁机制

## 故障排除

### 常见问题
1. **依赖冲突**: 确保requirements.txt使用兼容版本
2. **Python版本**: 确保runtime.txt指定支持的Python版本
3. **API密钥**: 部署后需要在应用界面输入DashScope API密钥
4. **记忆功能错误**: 检查memory_data目录权限和磁盘空间

### 部署验证
- 检查应用是否成功启动
- 验证API密钥输入功能
- 测试基本的问答功能
- 验证记忆系统是否正常工作

## 应用配置

### 文件结构
```
├── kp_narrative_app.py     # KP叙事工具主文件
├── streamlit_app.py        # COC规则助手主文件
├── main_app.py            # 核心业务逻辑
├── config.py              # 配置文件
├── memory_manager.py      # 🆕 记忆管理器
├── story_summarizer.py    # 🆕 故事总结器
├── requirements.txt       # Python依赖
├── runtime.txt           # Python版本
├── .streamlit/           # Streamlit配置
├── faiss_index/          # 向量索引（自动生成）
└── memory_data/          # 🆕 记忆数据（自动生成）
```

### 启动文件选择
- **KP叙事工具（推荐）**: 选择 `kp_narrative_app.py`
- **COC规则助手**: 选择 `streamlit_app.py`
- **应用选择器**: 选择 `app_launcher.py`

## 性能优化

### 冷启动优化
- FAISS索引会在首次使用时自动构建
- 建议预先上传构建好的索引文件
- 记忆系统数据文件会自动创建

### 内存使用
- 向量数据库会占用一定内存
- 记忆系统数据相对较小
- 建议监控应用内存使用情况

## 使用注意事项
- 确保API密钥有效且有足够额度
- 首次使用需要一些时间来加载向量数据库
- 建议在稳定的网络环境下使用
- 长期记忆功能需要额外的API调用，建议合理使用
- 记忆数据存储在本地，请定期备份重要数据
- 在Streamlit Cloud部署时，记忆数据可能在应用重启后丢失，建议导出重要故事