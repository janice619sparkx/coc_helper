import os
import pathlib
import re
import json
import logging
import numpy as np
import faiss
import pickle
from typing import List, Dict, Any
from filelock import FileLock
from openai import OpenAI
from config import Config

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DashScopeEmbedding:
    def __init__(self, api_key, model="text-embedding-v4", dimensions=1024):
        if not api_key:
            raise ValueError("需要提供DashScope API密钥")
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        self.model = model
        self.dimensions = dimensions
    
    def embed_texts(self, texts):
        """对多个文本进行向量化"""
        embeddings = []
        for text in texts:
            response = self.client.embeddings.create(
                model=self.model,
                input=text,
                dimensions=self.dimensions,
                encoding_format="float"
            )
            embeddings.append(response.data[0].embedding)
        return np.array(embeddings, dtype=np.float32)
    
    def embed_text(self, text):
        """对单个文本进行向量化"""
        response = self.client.embeddings.create(
            model=self.model,
            input=text,
            dimensions=self.dimensions,
            encoding_format="float"
        )
        return np.array(response.data[0].embedding, dtype=np.float32)

class FAISSStore:
    def __init__(self, embedding_model, index_path="faiss_index"):
        self.embedding_model = embedding_model
        self.index_path = pathlib.Path(index_path)
        self.index = None
        self.documents = []
        self.metadata = []
    
    def add_documents(self, texts, metadatas):
        """添加文档到索引"""
        # 获取向量
        embeddings = self.embedding_model.embed_texts(texts)
        
        # 创建 FAISS 索引
        if self.index is None:
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dimension)  # 使用内积相似度
        
        # 添加到索引
        self.index.add(embeddings)
        self.documents.extend(texts)
        self.metadata.extend(metadatas)
    
    def save_index(self, filename):
        """保存索引和元数据"""
        index_file = self.index_path / f"{filename}.faiss"
        metadata_file = self.index_path / f"{filename}.pkl"
        
        # 确保目录存在
        self.index_path.mkdir(exist_ok=True)
        
        # 保存 FAISS 索引
        faiss.write_index(self.index, str(index_file))
        
        # 保存元数据和文档
        with open(metadata_file, 'wb') as f:
            pickle.dump({
                'documents': self.documents,
                'metadata': self.metadata
            }, f)
    
    def load_index(self, filename):
        """加载索引和元数据"""
        index_file = self.index_path / f"{filename}.faiss"
        metadata_file = self.index_path / f"{filename}.pkl"
        
        if not index_file.exists() or not metadata_file.exists():
            return False
        
        try:
            # 加载 FAISS 索引
            self.index = faiss.read_index(str(index_file))
            
            # 加载元数据和文档
            with open(metadata_file, 'rb') as f:
                data = pickle.load(f)
                
                # 处理不同的数据格式
                if isinstance(data, dict):
                    # 新格式：字典
                    self.documents = data['documents']
                    self.metadata = data['metadata']
                elif isinstance(data, (list, tuple)) and len(data) == 2:
                    # 可能的旧格式：元组或列表
                    self.documents = data[0]
                    self.metadata = data[1]
                else:
                    logger.error(f"未知的数据格式: {type(data)}")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"加载索引失败: {e}")
            return False
    
    def similarity_search_with_score(self, query, k=4):
        """相似度搜索，返回结果和分数"""
        if self.index is None:
            return []
        
        # 对查询进行向量化
        query_embedding = self.embedding_model.embed_text(query).reshape(1, -1)
        
        # 搜索
        scores, indices = self.index.search(query_embedding, k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx != -1:  # -1 表示没有找到足够的结果
                results.append({
                    'document': self.documents[idx],
                    'metadata': self.metadata[idx],
                    'score': float(score)
                })
        
        return results

class COCRAGSystem:
    def __init__(self, embedding_api_key=None, llm_api_key=None):
        self.config = Config()
        
        # 使用传入的API密钥或配置中的密钥
        self.embedding_api_key = embedding_api_key or self.config.EMBEDDING_API_KEY
        self.llm_api_key = llm_api_key or self.config.LLM_API_KEY
        
        self.embedding_model = None
        self.faiss_store = None
        
        # 初始化RAG
        self.init_rag_system()
    
    def init_rag_system(self):
        """初始化RAG系统"""
        try:
            self._init_embedding_model()
            self._build_rag_documents()
            self._load_faiss_index()
            logger.info("RAG系统初始化成功")
        except Exception as e:
            logger.error(f"RAG系统初始化失败: {e}")
            raise
    
    def _init_embedding_model(self):
        """初始化嵌入模型"""
        if not self.embedding_api_key:
            raise ValueError("需要提供DashScope API密钥来初始化嵌入模型")
        self.embedding_model = DashScopeEmbedding(
            api_key=self.embedding_api_key,
            model="text-embedding-v4",
            dimensions=1024
        )
    
    def _build_rag_documents(self):
        """构建RAG文档"""
        lock_path = pathlib.Path("rag_build.lock")
        index_path = pathlib.Path(f"{self.config.FAISS_INDEX_PATH}/{self.config.FAISS_INDEX_NAME}.faiss")
        
        if index_path.exists():
            logger.info("向量索引已存在，跳过构建")
            return
        
        logger.info("开始构建RAG文档...")
        
        # 读取RAG文档
        rag_file_path = pathlib.Path("rag_documents.txt")
        if not rag_file_path.exists():
            raise FileNotFoundError("rag_documents.txt 文件不存在")
        
        with open(rag_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 按照换行符分割文档
        chunks = self._split_document_by_newlines(content)
        
        # 准备文档和元数据
        texts = []
        metadatas = []
        for i, chunk in enumerate(chunks):
            if chunk.strip():  # 忽略空白行
                texts.append(chunk)
                metadatas.append({
                    "chunk_id": i,
                    "source": "COC规则手册",
                    "length": len(chunk)
                })
        
        logger.info(f"创建了 {len(texts)} 个文档块")
        
        with FileLock(lock_path):
            if not index_path.exists():
                # 创建FAISS存储
                self.faiss_store = FAISSStore(self.embedding_model)
                self.faiss_store.add_documents(texts, metadatas)
                self.faiss_store.save_index(self.config.FAISS_INDEX_NAME)
                logger.info("向量索引构建并保存成功")
    
    def _split_document_by_newlines(self, content: str) -> List[str]:
        """按照换行符分割文档，每个段落作为一个块"""
        # 先按照多个换行符分割大段落
        paragraphs = re.split(r'\n\s*\n', content)
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            # 如果当前块加上新段落超过了块大小限制，则保存当前块
            if len(current_chunk) + len(paragraph) > self.config.CHUNK_SIZE and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = paragraph
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # 添加最后一个块
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _load_faiss_index(self):
        """加载FAISS索引"""
        try:
            if self.faiss_store is None:
                self.faiss_store = FAISSStore(self.embedding_model)
            
            if not self.faiss_store.load_index(self.config.FAISS_INDEX_NAME):
                logger.warning("FAISS索引加载失败，尝试重新构建...")
                self._cleanup_old_index(self.config.FAISS_INDEX_NAME)
                self._build_rag_documents()  # 强制重新构建
                if not self.faiss_store.load_index(self.config.FAISS_INDEX_NAME):
                    raise RuntimeError("无法加载FAISS索引")
            
            logger.info("FAISS索引加载成功")
        except Exception as e:
            logger.error(f"FAISS索引加载失败: {e}")
            raise
    
    def _cleanup_old_index(self, filename):
        """清理旧的索引文件"""
        index_path = pathlib.Path(self.config.FAISS_INDEX_PATH)
        index_file = index_path / f"{filename}.faiss"
        metadata_file = index_path / f"{filename}.pkl"
        
        try:
            if index_file.exists():
                index_file.unlink()
                logger.info(f"删除旧索引文件: {index_file}")
            if metadata_file.exists():
                metadata_file.unlink()
                logger.info(f"删除旧元数据文件: {metadata_file}")
        except Exception as e:
            logger.error(f"清理文件时出错: {e}")
    
    def get_relevant_documents(self, query: str) -> List[str]:
        """获取相关文档"""
        try:
            results = self.faiss_store.similarity_search_with_score(query, k=self.config.TOP_K)
            
            relevant_docs = []
            for result in results:
                logger.info(f"检索到文档 (相似度: {result['score']:.3f}): {result['document'][:100]}...")
                relevant_docs.append(result['document'])
            
            return relevant_docs
        except Exception as e:
            logger.error(f"文档检索失败: {e}")
            return []
    def get_completion(self, system_prompt, user_prompt, api_key, base_url, model):
        try:
            client = OpenAI(
                api_key=api_key,
                base_url=base_url
            )

            completion = client.chat.completions.create(
                model=model,  # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                    ]
            )
            return completion.choices[0].message.content, completion
        except Exception as e:
            return f"错误信息：{e}", {}


    def generate_response(self, user_message: str) -> str:
        """生成LLM响应"""
        try:
            logger.info(f"=== 开始生成响应 ===")
            
            # 获取相关文档
            logger.info("1. 开始检索相关文档...")
            relevant_docs = self.get_relevant_documents(user_message)
            logger.info(f"检索完成，获得 {len(relevant_docs)} 个文档")
            
            # 构建提示词 - 将所有检索内容合并
            context = "\n\n".join(relevant_docs) if relevant_docs else "暂无相关资料"
            
            user_prompt = f"""
参考资料：
{context}

用户问题：{user_message}

请基于以上参考资料回答用户问题。如果参考资料中没有相关信息，请诚实地告知用户，并尽量提供一般性的COC游戏建议。
"""
            
            logger.info("2. 开始调用LLM...")
            # 单次调用LLM，处理所有合并后的内容
            if not self.llm_api_key:
                raise ValueError("需要提供LLM API密钥来生成响应")
            response, _ = self.get_completion(
                self.config.SYSTEM_PROMPT, 
                user_prompt, 
                self.llm_api_key, 
                "https://dashscope.aliyuncs.com/compatible-mode/v1", 
                'deepseek-v3'
            )
            
            logger.info(f"3. LLM调用完成，响应长度: {len(response)}")
            logger.info(f"=== 响应生成完成 ===")
            return response
            
        except Exception as e:
            logger.error(f"LLM响应生成失败: {e}")
            return f"抱歉，在黑暗的虚空中遇到了未知的错误...请稍后再试。错误信息: {str(e)}"
    
    def generate_narrative_response(self, script_summary: str, current_stage: str, player_action: str, chat_history: list) -> str:
        """生成KP叙事响应"""
        try:
            logger.info(f"=== 开始生成叙事响应 ===")
            
            # 获取与玩家行动相关的知识库文档
            logger.info("1. 开始检索相关规则文档...")
            relevant_docs = self.get_relevant_documents(player_action)
            logger.info(f"检索完成，获得 {len(relevant_docs)} 个相关文档")
            
            # 构建聊天历史上下文
            chat_context = ""
            if chat_history:
                recent_messages = chat_history[-5:]  # 只取最近5条消息
                for msg in recent_messages:
                    if msg["role"] == "kp":
                        chat_context += f"KP: {msg['content']}\n"
                    else:
                        chat_context += f"AI: {msg['content']}\n"
            
            # 构建知识库上下文
            knowledge_context = "\n\n".join(relevant_docs) if relevant_docs else "暂无相关规则资料"
            
            # 构建完整的提示词
            user_prompt = f"""
你是一个专业的克苏鲁的呼唤(Call of Cthulhu)跑团守秘人(KP)的AI叙事助手。

**剧本概要**：
{script_summary if script_summary else "暂无设定"}

**当前剧情阶段**：
{current_stage if current_stage else "暂无设定"}

**玩家选择/行动**：
{player_action}

**最近对话历史**：
{chat_context if chat_context else "暂无历史"}

**相关规则知识**：
{knowledge_context}

你可以考虑的常用词，以下词仅作风格参考，并不是必须使用：
隐晦、怪诞、不可解释、肆无忌惮、狭长、不可名状、繁缛无用、延伸、哀嚎、逗留、吹奏、吟诵、亘古浩远、鬼祟、鬼魅、祭坛、神翕、风化、源头

请基于以上信息生成一段生动的叙事描述，要求：
1. 忠于剧本设定和当前阶段的氛围
2. 对玩家行动给出合理的结果描述
3. 如果涉及规则检定，结合知识库信息给出准确说明
4. 保持克苏鲁神话的神秘氛围
5. 描述要具体生动，有画面感
6. 字数控制在150-300字之间
7. 如果需要进行技能检定或属性检定，请明确说明

请现在开始叙事：
"""
            
            logger.info("2. 开始调用LLM生成叙事...")
            # 调用LLM生成叙事
            if not self.llm_api_key:
                raise ValueError("需要提供LLM API密钥来生成叙事")
            response, _ = self.get_completion(
                Config.NARRATIVE_SYSTEM_PROMPT, 
                user_prompt, 
                self.llm_api_key, 
                "https://dashscope.aliyuncs.com/compatible-mode/v1", 
                'deepseek-v3'
            )
            
            logger.info(f"3. 叙事生成完成，响应长度: {len(response)}")
            logger.info(f"=== 叙事响应生成完成 ===")
            return response
            
        except Exception as e:
            logger.error(f"叙事响应生成失败: {e}")
            return f"在编织恐怖故事的过程中遇到了未知的阻碍...请稍后再试。错误信息: {str(e)}"

    def save_chat_log(self, user_message: str, ai_response: str):
        """保存聊天记录"""
        try:
            import time
            log_entry = {
                "timestamp": time.time(),  # 当前时间戳
                "user": user_message,
                "ai": ai_response
            }
            
            # 读取现有日志
            log_file = pathlib.Path("chat_logs.json")
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            # 添加新日志
            logs.append(log_entry)
            
            # 保存日志
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"保存聊天记录失败: {e}")
    
    def save_narrative_log(self, script_summary: str, current_stage: str, player_action: str, ai_narrative: str):
        """保存叙事记录"""
        try:
            import time
            log_entry = {
                "timestamp": time.time(),
                "type": "narrative",
                "script_summary": script_summary,
                "current_stage": current_stage,
                "player_action": player_action,
                "ai_narrative": ai_narrative
            }
            
            # 读取现有日志
            log_file = pathlib.Path("narrative_logs.json")
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            # 添加新日志
            logs.append(log_entry)
            
            # 保存日志
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"保存叙事记录失败: {e}")

# 全局实例
rag_system = None

def get_rag_system(embedding_api_key=None, llm_api_key=None):
    """获取RAG系统实例"""
    global rag_system
    if rag_system is None or (embedding_api_key and llm_api_key):
        rag_system = COCRAGSystem(embedding_api_key, llm_api_key)
    return rag_system

def process_message(user_message: str, embedding_api_key=None, llm_api_key=None) -> str:
    """处理用户消息的主函数"""
    try:
        logger.info(f"开始处理消息: {user_message[:50]}...")
        system = get_rag_system(embedding_api_key, llm_api_key)
        response = system.generate_response(user_message)
        system.save_chat_log(user_message, response)
        logger.info(f"消息处理完成，响应长度: {len(response)}")
        return response
    except Exception as e:
        logger.error(f"消息处理失败: {e}")
        return f"在古老的卷轴中搜寻答案时遇到了异常...错误: {str(e)}"

def process_narrative_message(script_summary: str, current_stage: str, player_action: str, chat_history: list, embedding_api_key=None, llm_api_key=None) -> str:
    """处理KP叙事消息的主函数"""
    try:
        logger.info(f"开始处理叙事消息: {player_action[:50]}...")
        system = get_rag_system(embedding_api_key, llm_api_key)
        response = system.generate_narrative_response(script_summary, current_stage, player_action, chat_history)
        system.save_narrative_log(script_summary, current_stage, player_action, response)
        logger.info(f"叙事处理完成，响应长度: {len(response)}")
        return response
    except Exception as e:
        logger.error(f"叙事处理失败: {e}")
        return f"在编织黑暗故事的过程中遇到了神秘的阻碍...错误: {str(e)}"

if __name__ == "__main__":
    # 测试
    test_message = "什么是理智检定？"
    response = process_message(test_message)
    print(f"用户: {test_message}")
    print(f"AI: {response}")
