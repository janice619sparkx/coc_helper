"""
故事总结器
负责梗概管理和完整故事生成功能
"""

import json
import pathlib
from datetime import datetime
from typing import List, Dict, Optional
from openai import OpenAI
from memory_manager import MemoryManager

class StorySummarizer:
    def __init__(self, memory_manager: MemoryManager):
        """
        初始化故事总结器
        
        Args:
            memory_manager: 记忆管理器实例
        """
        self.memory_manager = memory_manager
        self.story_archive_file = memory_manager.story_archive_file
    
    async def trigger_memory_summary(self, api_key: str, force: bool = False) -> tuple[bool, str]:
        """
        触发记忆总结（手动或自动调用）
        
        Args:
            api_key: API密钥
            force: 是否强制总结（忽略消息数量限制）
            
        Returns:
            tuple[bool, str]: (成功标志, 生成的总结或错误信息)
        """
        try:
            # 获取最近的消息
            recent_messages = self.memory_manager.get_recent_messages(50)  # 增加获取数量
            
            if not force and len(recent_messages) < 5:  # 至少需要5条消息才值得总结
                return False, "消息数量不足，无需总结"
            
            if len(recent_messages) < 2:  # 绝对最低限制
                return False, "消息数量太少，无法总结"
            
            # 如果强制总结且消息较少，取所有消息
            if force and len(recent_messages) < 15:
                messages_to_summarize = recent_messages
            else:
                messages_to_summarize = recent_messages[-15:]  # 取最近15条
            
            # 生成总结
            summary = await self.memory_manager.generate_summary(api_key, messages_to_summarize)
            
            if summary:
                return True, summary
            else:
                return False, "生成总结失败"
                
        except Exception as e:
            return False, f"触发记忆总结时出错: {e}"
    
    async def generate_complete_story(self, api_key: str) -> tuple[bool, str]:
        """
        生成完整故事
        将所有梗概整合成一个完整的故事
        
        Args:
            api_key: API密钥
            
        Returns:
            tuple[bool, str]: (成功标志, 完整故事或错误信息)
        """
        try:
            # 首先触发一次记忆总结，确保最新对话被总结
            await self.trigger_memory_summary(api_key)
            
            # 获取所有梗概
            all_summaries = self.memory_manager.get_all_summaries()
            
            if not all_summaries:
                return False, "没有找到任何剧情梗概"
            
            # 获取当前会话信息用于上下文
            current_session = self.memory_manager.get_current_session_info()
            script_summary = current_session.get("script_summary", "") if current_session else ""
            
            # 构建完整故事
            complete_story = await self._create_complete_story(api_key, all_summaries, script_summary)
            
            if complete_story:
                # 保存完整故事到档案
                await self._save_complete_story(complete_story, script_summary)
                return True, complete_story
            else:
                return False, "生成完整故事失败"
                
        except Exception as e:
            return False, f"生成完整故事时出错: {e}"
    
    async def _create_complete_story(self, api_key: str, summaries: List[Dict], script_summary: str) -> str:
        """
        根据所有梗概创建完整故事
        
        Args:
            api_key: API密钥
            summaries: 所有梗概列表
            script_summary: 剧本概要
            
        Returns:
            str: 完整故事
        """
        # 按时间排序梗概
        sorted_summaries = sorted(summaries, key=lambda x: x["timestamp"])
        
        # 构建梗概文本
        summaries_text = ""
        
        for i, summary in enumerate(sorted_summaries, 1):
            summaries_text += f"章节 {i}:\n{summary['summary']}\n\n"
        
        # 构建完整故事生成提示词
        story_prompt = f"""
你是一位专业的COC克苏鲁跑团故事编剧。现在需要将以下分散的剧情梗概整合成一个完整、连贯的故事。

剧本背景：
{script_summary}

分章节梗概：
{summaries_text}

请按照以下要求创作完整故事：

1. **语言风格**：严格按照剧本时代背景使用相应的语言风格，例如：
   - 中世纪：古朴典雅，文言色彩
   - 民国时期：半文半白，带有时代特色
   - 现代都市：简洁直白，现代用语
   - 中国乡土：带有方言色彩的朴实语言
   - 西方背景：翻译体的优雅表达

2. **故事结构**：
   - 开头：简要交代背景和主要角色
   - 发展：按照梗概顺序展开剧情
   - 高潮：突出最紧张刺激的情节
   - 结尾：给出当前故事的阶段性结论

3. **叙事要求**：
   - 保持COC恐怖神秘氛围
   - 情节连贯，逻辑合理
   - 突出玩家的勇敢和智慧
   - 字数控制在1500-2500字
   - 使用第三人称全知视角
   - 适当添加环境描写和心理描写

4. **注意事项**：
   - 不要添加梗概中没有的新情节
   - 保持各章节之间的逻辑连接
   - 突出关键线索和转折点
   - 营造悬疑紧张的阅读体验

请开始创作这个完整的COC故事：
"""
        
        try:
            complete_story = self._call_llm_api(api_key, story_prompt)
            return complete_story
        except Exception as e:
            print(f"生成完整故事时调用API出错: {e}")
            return ""
    
    
    def _call_llm_api(self, api_key: str, prompt: str) -> str:
        """调用大模型API生成文本"""
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
                temperature=0.8,
                max_tokens=3000
            )
            return completion.choices[0].message.content
        except Exception as e:
            raise Exception(f"API调用错误：{e}")
    
    async def _save_complete_story(self, story: str, script_summary: str):
        """保存完整故事到档案"""
        data = self.memory_manager._load_json(self.story_archive_file)
        
        story_entry = {
            "timestamp": datetime.now().isoformat(),
            "story": story,
            "script_summary": script_summary,
            "summaries_count": len(self.memory_manager.get_all_summaries()),
            "session_id": self.memory_manager._load_json(self.memory_manager.chat_sessions_file).get("current_session_id")
        }
        
        data["stories"].append(story_entry)
        self.memory_manager._save_json(self.story_archive_file, data)
    
    def get_story_archive(self) -> List[Dict]:
        """获取故事档案"""
        data = self.memory_manager._load_json(self.story_archive_file)
        return data.get("stories", [])
    
    def get_latest_story(self) -> Optional[Dict]:
        """获取最新的完整故事"""
        stories = self.get_story_archive()
        if stories:
            return max(stories, key=lambda x: x["timestamp"])
        return None
    
    def clear_all_memories(self):
        """清空所有记忆（谨慎使用）"""
        # 清空梗概
        self.memory_manager._save_json(self.memory_manager.summaries_file, {"summaries": []})
        
        # 清空故事档案
        self.memory_manager._save_json(self.story_archive_file, {"stories": []})
        
        # 清空当前会话
        self.memory_manager.clear_current_session()
    
    def get_memory_stats(self) -> Dict:
        """获取记忆统计信息"""
        summaries = self.memory_manager.get_all_summaries()
        current_session_summaries = self.memory_manager.get_current_session_summaries()
        stories = self.get_story_archive()
        current_session = self.memory_manager.get_current_session_info()
        
        return {
            "total_summaries": len(summaries),
            "current_session_summaries": len(current_session_summaries),
            "total_stories": len(stories),
            "current_session_messages": current_session.get("message_count", 0) if current_session else 0,
            "messages_until_next_summary": 15 - (current_session.get("message_count", 0) % 15) if current_session else 15,
            "last_summary_time": summaries[-1]["timestamp"] if summaries else None,
            "last_story_time": stories[-1]["timestamp"] if stories else None,
            "current_session_id": current_session.get("session_id", "无") if current_session else "无"
        }
    
    async def generate_current_session_story(self, api_key: str) -> tuple[bool, str]:
        """
        生成当前会话的完整故事（基于当前会话的梗概或聊天记录）
        
        Args:
            api_key: API密钥
            
        Returns:
            tuple[bool, str]: (成功标志, 完整故事或错误信息)
        """
        try:
            # 获取当前会话的梗概
            current_session_summaries = self.memory_manager.get_current_session_summaries()
            current_session = self.memory_manager.get_current_session_info()
            
            if not current_session:
                return False, "没有找到当前会话"
            
            script_summary = current_session.get("script_summary", "")
            
            # 如果没有梗概，检查是否有足够的聊天记录
            if not current_session_summaries:
                recent_messages = self.memory_manager.get_recent_messages(50)  # 获取最近50条消息
                
                if len(recent_messages) < 2:
                    return False, "当前会话没有足够的内容生成故事（至少需要2条消息）"
                
                # 先生成一个临时总结基于现有聊天记录
                temp_summary = await self._create_story_from_messages(api_key, recent_messages, script_summary)
                
                if temp_summary:
                    # 保存为临时故事
                    await self._save_session_story(temp_summary, script_summary, current_session.get("session_id"), story_type="session_story_from_messages")
                    return True, temp_summary
                else:
                    return False, "基于聊天记录生成故事失败"
            else:
                # 如果有梗概，先触发一次记忆总结确保最新对话被总结
                await self.trigger_memory_summary(api_key)
                current_session_summaries = self.memory_manager.get_current_session_summaries()
                
                # 构建当前会话的完整故事
                complete_story = await self._create_complete_story(api_key, current_session_summaries, script_summary)
                
                if complete_story:
                    # 保存完整故事到档案，标记为当前会话故事
                    await self._save_session_story(complete_story, script_summary, current_session.get("session_id"))
                    return True, complete_story
                else:
                    return False, "生成当前会话故事失败"
                
        except Exception as e:
            return False, f"生成当前会话故事时出错: {e}"
    
    async def _create_story_from_messages(self, api_key: str, messages: List[Dict], script_summary: str) -> str:
        """
        基于聊天消息直接生成故事
        
        Args:
            api_key: API密钥
            messages: 聊天消息列表
            script_summary: 剧本概要
            
        Returns:
            str: 生成的故事
        """
        # 构建对话历史文本
        conversation_text = ""
        current_stage = ""
        
        for msg in messages:
            if msg["role"] == "kp":
                conversation_text += f"KP输入: {msg['content']}\n"
            elif msg["role"] == "ai":
                conversation_text += f"AI叙事: {msg['content']}\n"
            
            # 获取最新的阶段信息
            if msg.get("current_stage"):
                current_stage = msg["current_stage"]
        
        # 检测语言风格 - 简化版本
        if "1920" in script_summary or "民国" in script_summary:
            language_style = "民国时期的半文半白风格"
        elif "中世纪" in script_summary or "古代" in script_summary:
            language_style = "古朴典雅的文言风格"
        elif "现代" in script_summary or "当代" in script_summary:
            language_style = "现代简洁直白的语言风格"
        else:
            language_style = "符合COC恐怖氛围的神秘诡异风格"
        
        # 构建故事生成提示词
        story_prompt = f"""
你是专业的COC克苏鲁跑团故事记述者。请将以下对话记录整理成一个完整连贯的故事。

剧本背景：
{script_summary}

当前阶段：
{current_stage}

语言风格要求：{language_style}

对话记录：
{conversation_text}

请按照以下要求创作故事：

1. **语言风格**：严格按照剧本时代背景使用相应的语言风格
2. **故事结构**：
   - 开头：简要交代背景和情境
   - 发展：按照对话顺序展开剧情
   - 当前状态：描述故事进展到的当前状态
3. **叙事要求**：
   - 保持COC神秘氛围
   - 情节连贯，逻辑合理
   - 突出玩家的行动和遭遇
   - 字数控制在800-1500字
   - 使用第三人称全知视角
   - 重点描述已发生的情节

请开始创作这个COC故事：
"""
        
        try:
            story = self._call_llm_api(api_key, story_prompt)
            return story
        except Exception as e:
            print(f"基于消息生成故事时调用API出错: {e}")
            return ""

    async def _save_session_story(self, story: str, script_summary: str, session_id: str, story_type: str = "session_story"):
        """保存会话故事到档案"""
        data = self.memory_manager._load_json(self.story_archive_file)
        
        story_entry = {
            "timestamp": datetime.now().isoformat(),
            "story": story,
            "script_summary": script_summary,
            "summaries_count": len(self.memory_manager.get_current_session_summaries()) if story_type == "session_story" else 0,
            "session_id": session_id,
            "story_type": story_type
        }
        
        data["stories"].append(story_entry)
        self.memory_manager._save_json(self.story_archive_file, data)
