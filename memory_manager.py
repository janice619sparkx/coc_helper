"""
长期记忆管理器
负责聊天记录的存储、检索和自动总结功能
"""

import json
import os
import pathlib
from datetime import datetime
from typing import List, Dict, Optional, Any
from openai import OpenAI
from config import Config

class MemoryManager:
    def __init__(self, memory_dir: str = "memory_data"):
        """
        初始化记忆管理器
        
        Args:
            memory_dir: 记忆数据存储目录
        """
        self.memory_dir = pathlib.Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        
        # 数据文件路径
        self.chat_sessions_file = self.memory_dir / "chat_sessions.json"
        self.summaries_file = self.memory_dir / "summaries.json"
        self.story_archive_file = self.memory_dir / "story_archive.json"
        
        # 确保文件存在
        self._ensure_files_exist()
    
    def _ensure_files_exist(self):
        """确保所有数据文件存在"""
        if not self.chat_sessions_file.exists():
            self._save_json(self.chat_sessions_file, {"sessions": [], "current_session_id": None})
        
        if not self.summaries_file.exists():
            self._save_json(self.summaries_file, {"summaries": []})
        
        if not self.story_archive_file.exists():
            self._save_json(self.story_archive_file, {"stories": []})
    
    def _load_json(self, file_path: pathlib.Path) -> Dict:
        """加载JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_json(self, file_path: pathlib.Path, data: Dict):
        """保存JSON文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def start_new_session(self, script_summary: str = "", current_stage: str = "") -> str:
        """
        开始新的聊天会话
        
        Args:
            script_summary: 剧本概要
            current_stage: 当前阶段
            
        Returns:
            session_id: 新会话的ID
        """
        data = self._load_json(self.chat_sessions_file)
        
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_session = {
            "session_id": session_id,
            "start_time": datetime.now().isoformat(),
            "script_summary": script_summary,
            "current_stage": current_stage,
            "messages": [],
            "message_count": 0
        }
        
        data["sessions"].append(new_session)
        data["current_session_id"] = session_id
        
        self._save_json(self.chat_sessions_file, data)
        return session_id
    
    def add_message(self, role: str, content: str, script_summary: str = "", current_stage: str = "") -> bool:
        """
        添加消息到当前会话
        
        Args:
            role: 角色（kp/ai）
            content: 消息内容
            script_summary: 剧本概要（如果有更新）
            current_stage: 当前阶段（如果有更新）
            
        Returns:
            bool: 是否需要触发总结（达到15条消息）
        """
        data = self._load_json(self.chat_sessions_file)
        
        # 如果没有当前会话，创建一个
        if not data.get("current_session_id"):
            self.start_new_session(script_summary, current_stage)
            data = self._load_json(self.chat_sessions_file)
        
        # 找到当前会话
        current_session = None
        for session in data["sessions"]:
            if session["session_id"] == data["current_session_id"]:
                current_session = session
                break
        
        if not current_session:
            # 如果找不到当前会话，创建新会话
            self.start_new_session(script_summary, current_stage)
            data = self._load_json(self.chat_sessions_file)
            current_session = data["sessions"][-1]
        
        # 添加消息
        message = {
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content,
            "script_summary": script_summary,
            "current_stage": current_stage
        }
        
        current_session["messages"].append(message)
        current_session["message_count"] += 1
        
        # 更新会话信息
        if script_summary:
            current_session["script_summary"] = script_summary
        if current_stage:
            current_session["current_stage"] = current_stage
        
        self._save_json(self.chat_sessions_file, data)
        
        # 检查是否需要总结（每15条消息）
        return current_session["message_count"] % 15 == 0
    
    def get_recent_messages(self, count: int = 15) -> List[Dict]:
        """
        获取最近的消息
        
        Args:
            count: 获取消息数量
            
        Returns:
            List[Dict]: 最近的消息列表
        """
        data = self._load_json(self.chat_sessions_file)
        
        if not data.get("current_session_id"):
            return []
        
        # 找到当前会话
        current_session = None
        for session in data["sessions"]:
            if session["session_id"] == data["current_session_id"]:
                current_session = session
                break
        
        if not current_session:
            return []
        
        # 返回最近的消息
        return current_session["messages"][-count:]
    
    def get_current_session_info(self) -> Optional[Dict]:
        """获取当前会话信息"""
        data = self._load_json(self.chat_sessions_file)
        
        if not data.get("current_session_id"):
            return None
        
        for session in data["sessions"]:
            if session["session_id"] == data["current_session_id"]:
                return {
                    "session_id": session["session_id"],
                    "start_time": session["start_time"],
                    "script_summary": session.get("script_summary", ""),
                    "current_stage": session.get("current_stage", ""),
                    "message_count": session["message_count"]
                }
        
        return None
    
    async def generate_summary(self, api_key: str, recent_messages: List[Dict] = None) -> str:
        """
        生成最近15次对话的总结
        
        Args:
            api_key: API密钥
            recent_messages: 要总结的消息列表，如果为None则自动获取最近15条
            
        Returns:
            str: 生成的总结
        """
        if recent_messages is None:
            recent_messages = self.get_recent_messages(15)
        
        if not recent_messages:
            return ""
        
        # 构建对话历史文本
        conversation_text = ""
        current_script = ""
        current_stage = ""
        
        for msg in recent_messages:
            if msg["role"] == "kp":
                conversation_text += f"KP输入: {msg['content']}\n"
            elif msg["role"] == "ai":
                conversation_text += f"AI叙事: {msg['content']}\n"
            
            # 获取最新的剧本信息
            if msg.get("script_summary"):
                current_script = msg["script_summary"]
            if msg.get("current_stage"):
                current_stage = msg["current_stage"]
        
        # 构建总结提示词
        summary_prompt = f"""
请将以下COC跑团游戏的对话记录总结成一个300-500字的剧情梗概。

剧本背景：{current_script}
当前阶段：{current_stage}

对话记录：
{conversation_text}

请按照以下要求总结：
1. 用故事化的语言描述玩家的行动和遭遇
2. 突出重要的发现、线索和剧情转折
3. 保持COC恐怖氛围的语调
4. 控制在300-500字之间
5. 以第三人称描述，像是在记录一段历险经历

总结：
"""
        
        try:
            # 调用大模型API生成总结
            summary = self._call_llm_api(api_key, summary_prompt)
            
            # 保存总结
            await self.save_summary(summary, current_script, current_stage)
            
            return summary
        except Exception as e:
            print(f"生成总结时出错: {e}")
            return ""
    
    def _call_llm_api(self, api_key: str, prompt: str) -> str:
        """调用大模型API"""
        try:
            client = OpenAI(
                api_key=api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            )

            completion = client.chat.completions.create(
                model="deepseek-v3",
                messages=[
                    {'role': 'user', 'content': prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            return completion.choices[0].message.content
        except Exception as e:
            raise Exception(f"API调用错误：{e}")
    
    async def save_summary(self, summary: str, script_summary: str = "", current_stage: str = ""):
        """保存总结到文件"""
        data = self._load_json(self.summaries_file)
        
        summary_entry = {
            "timestamp": datetime.now().isoformat(),
            "summary": summary,
            "script_summary": script_summary,
            "current_stage": current_stage,
            "session_id": self._load_json(self.chat_sessions_file).get("current_session_id")
        }
        
        data["summaries"].append(summary_entry)
        self._save_json(self.summaries_file, data)
    
    def get_all_summaries(self) -> List[Dict]:
        """获取所有总结"""
        data = self._load_json(self.summaries_file)
        return data.get("summaries", [])
    
    def clear_current_session(self):
        """清空当前会话，将当前会话ID设为None"""
        data = self._load_json(self.chat_sessions_file)
        data["current_session_id"] = None
        self._save_json(self.chat_sessions_file, data)
    
    def end_current_session_and_start_new(self, script_summary: str = "", current_stage: str = "") -> str:
        """
        结束当前会话并开始新会话
        这样可以确保会话之间的记忆完全隔离
        
        Args:
            script_summary: 新会话的剧本概要
            current_stage: 新会话的当前阶段
            
        Returns:
            str: 新会话的ID
        """
        # 结束当前会话
        self.clear_current_session()
        
        # 开始新会话
        return self.start_new_session(script_summary, current_stage)
    
    def get_total_message_count(self) -> int:
        """获取当前会话的总消息数"""
        data = self._load_json(self.chat_sessions_file)
        
        if not data.get("current_session_id"):
            return 0
        
        for session in data["sessions"]:
            if session["session_id"] == data["current_session_id"]:
                return session.get("message_count", 0)
        
        return 0
    
    def get_current_session_summaries(self) -> List[Dict]:
        """获取当前会话相关的梗概"""
        current_session_info = self.get_current_session_info()
        if not current_session_info:
            return []
        
        current_session_id = current_session_info["session_id"]
        all_summaries = self.get_all_summaries()
        
        # 筛选出当前会话的梗概
        session_summaries = [
            summary for summary in all_summaries 
            if summary.get("session_id") == current_session_id
        ]
        
        return session_summaries
    
    def get_all_sessions_info(self) -> List[Dict]:
        """获取所有会话的基本信息"""
        data = self._load_json(self.chat_sessions_file)
        sessions_info = []
        
        for session in data.get("sessions", []):
            sessions_info.append({
                "session_id": session["session_id"],
                "start_time": session["start_time"], 
                "script_summary": session.get("script_summary", "")[:100] + "..." if len(session.get("script_summary", "")) > 100 else session.get("script_summary", ""),
                "message_count": session.get("message_count", 0),
                "is_current": session["session_id"] == data.get("current_session_id")
            })
        
        return sorted(sessions_info, key=lambda x: x["start_time"], reverse=True)
