#!/usr/bin/env python3
"""
COC跑团工具启动脚本
"""

import subprocess
import sys
import time
import threading
import webbrowser
from pathlib import Path

def print_banner():
    """打印启动横幅"""
    print("""
🐙════════════════════════════════════════════════════════════════🐙
                    COC跑团工具集合启动器
                克苏鲁的呼唤 - 专业跑团辅助工具
🐙════════════════════════════════════════════════════════════════🐙
""")

def start_app(app_name, port, description):
    """启动应用"""
    print(f"\n🚀 正在启动 {description}...")
    print(f"📍 端口: {port}")
    print(f"🌐 访问地址: http://localhost:{port}")
    
    try:
        # 启动Streamlit应用
        process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", app_name,
            "--server.port", str(port),
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 等待应用启动
        time.sleep(3)
        
        # 检查进程是否还在运行
        if process.poll() is None:
            print(f"✅ {description} 启动成功！")
            return process
        else:
            print(f"❌ {description} 启动失败！")
            return None
            
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return None

def open_browser(url, delay=2):
    """延迟打开浏览器"""
    time.sleep(delay)
    try:
        webbrowser.open(url)
        print(f"🌐 已打开浏览器: {url}")
    except:
        print(f"⚠️ 无法自动打开浏览器，请手动访问: {url}")

def main():
    """主函数"""
    print_banner()
    
    # 检查必要文件是否存在
    required_files = [
        "streamlit_app.py",
        "kp_narrative_app.py", 
        "app_launcher.py",
        "main_app.py",
        "config.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ 缺少必要文件: {', '.join(missing_files)}")
        return
    
    print("选择要启动的工具：")
    print("1. 应用选择器 (推荐)")
    print("2. COC规则助手")
    print("3. KP叙事辅助工具")
    print("4. 同时启动所有工具")
    print("5. 退出")
    
    while True:
        try:
            choice = input("\n请输入选择 (1-5): ").strip()
            
            if choice == "1":
                print("\n🚀 启动应用选择器...")
                process = start_app("app_launcher.py", 8500, "应用选择器")
                if process:
                    threading.Thread(target=open_browser, args=("http://localhost:8500",)).start()
                    input("\n按 Enter 键停止应用选择器...")
                    process.terminate()
                break
                
            elif choice == "2":
                print("\n🚀 启动COC规则助手...")
                process = start_app("streamlit_app.py", 8501, "COC规则助手")
                if process:
                    threading.Thread(target=open_browser, args=("http://localhost:8501",)).start()
                    input("\n按 Enter 键停止COC规则助手...")
                    process.terminate()
                break
                
            elif choice == "3":
                print("\n🚀 启动KP叙事辅助工具...")
                process = start_app("kp_narrative_app.py", 8502, "KP叙事辅助工具")
                if process:
                    threading.Thread(target=open_browser, args=("http://localhost:8502",)).start()
                    input("\n按 Enter 键停止KP叙事辅助工具...")
                    process.terminate()
                break
                
            elif choice == "4":
                print("\n🚀 同时启动所有工具...")
                processes = []
                
                # 启动应用选择器
                p1 = start_app("app_launcher.py", 8500, "应用选择器")
                if p1: processes.append(p1)
                
                # 启动COC规则助手
                p2 = start_app("streamlit_app.py", 8501, "COC规则助手")
                if p2: processes.append(p2)
                
                # 启动KP叙事工具
                p3 = start_app("kp_narrative_app.py", 8502, "KP叙事辅助工具")
                if p3: processes.append(p3)
                
                if processes:
                    print(f"\n✅ 已启动 {len(processes)} 个应用！")
                    print("\n📍 访问地址：")
                    print("   应用选择器: http://localhost:8500")
                    print("   COC规则助手: http://localhost:8501")
                    print("   KP叙事工具: http://localhost:8502")
                    
                    # 打开应用选择器
                    threading.Thread(target=open_browser, args=("http://localhost:8500",)).start()
                    
                    input("\n按 Enter 键停止所有应用...")
                    
                    # 停止所有进程
                    for process in processes:
                        process.terminate()
                break
                
            elif choice == "5":
                print("\n👋 再见！愿你的理智值永远不会归零...")
                break
                
            else:
                print("⚠️ 请输入有效选择 (1-5)")
                
        except KeyboardInterrupt:
            print("\n\n👋 用户中断，再见！")
            break
        except Exception as e:
            print(f"❌ 发生错误: {e}")

if __name__ == "__main__":
    main()
