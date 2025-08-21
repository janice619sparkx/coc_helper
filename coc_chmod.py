
import os
import json
import re
import subprocess
from bs4 import BeautifulSoup
from pathlib import Path

def extract_chm_with_7zip(chm_file, output_dir="chm_output"):
    """使用7zip提取CHM文件并处理"""
    
    chm_path = Path(chm_file)
    if not chm_path.exists():
        print(f"❌ CHM文件不存在: {chm_file}")
        return
    
    # 检查7zip是否安装
    try:
        subprocess.run(['7z'], capture_output=True, check=False)
    except FileNotFoundError:
        print("❌ 请先安装7zip: brew install p7zip")
        return
    
    # 创建临时提取目录
    temp_dir = "temp_chm_extract"
    os.makedirs(temp_dir, exist_ok=True)
    
    print(f"📦 提取CHM文件: {chm_file}")
    
    # 使用7zip提取
    try:
        result = subprocess.run([
            '7z', 'x', str(chm_path), f'-o{temp_dir}', '-y'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ 7zip提取失败: {result.stderr}")
            return
            
    except Exception as e:
        print(f"❌ 提取过程出错: {e}")
        return
    
    print("✅ CHM文件提取成功")
    
    # 处理HTML文件
    documents, text = process_html_files(temp_dir, output_dir)
    
    # 清理临时目录
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)
    
    return documents

def process_html_files(extracted_dir, output_dir):
    """处理提取的HTML文件"""
    
    os.makedirs(output_dir, exist_ok=True)
    documents = []
    check = []
    # 查找HTML文件
    html_files = []
    for ext in ['*.html', '*.htm']:
        html_files.extend(Path(extracted_dir).rglob(ext))
    
    print(f"🔍 找到 {len(html_files)} 个HTML文件")
    
    for i, html_file in enumerate(html_files, 1):
        try:
            # 尝试不同的编码
            content = None
            for encoding in ['utf-8', 'gbk', 'gb2312', 'latin1']:
                try:
                    with open(html_file, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if not content:
                print(f"⚠️ 无法读取文件: {html_file}")
                continue
            
            # 解析HTML
            soup = BeautifulSoup(content, 'html.parser')
            
            # 移除不需要的标签
            for tag in soup(['script', 'style', 'meta', 'link']):
                tag.decompose()
            
            # 提取标题
            title = "\n"
            if soup.title and soup.title.get_text().strip():
                title = soup.title.get_text().strip()
            elif soup.find(['h1', 'h2', 'h3']):
                title = soup.find(['h1', 'h2', 'h3']).get_text().strip()
            
            # 提取文本
            text = soup.get_text()
            # 清理文本，保持段落结构
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            clean_text = '\n'.join(lines)
# 只保存有意义的内容
            doc = {"content": clean_text}
            documents.append(doc)
            check.append(title)
            check.append(clean_text)

            print(f"📄 已处理 {i}/{len(html_files)} 个文件")
        
        except Exception as e:
            print(f"⚠️ 处理文件出错 {html_file}: {e}")
    
    print(f"✅ 成功处理 {len(documents)} 个文档")
    
    # 保存结果
    # save_text_results(documents, output_dir)
    return documents, check

def save_text_results(documents, output_dir):
    """保存纯文本结果"""
    
    output_path = Path(output_dir)
    
    # 1. JSON格式 (保留结构化信息)
    json_file = output_path / "documents.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)
    
    # 2. 单独的文本文件 (便于后续处理)
    texts_dir = output_path / "texts"
    texts_dir.mkdir(exist_ok=True)
    
    for doc in documents:
        # 安全的文件名
        safe_name = re.sub(r'[^\w\-_.]', '_', doc['title'])[:50]
        txt_file = texts_dir / f"{doc['id']}_{safe_name}.txt"
        
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(doc['content'])  # 只写入纯文本，不加额外信息
    
    # 3. 带元数据的文本文件 (如果需要保留来源信息)
    texts_with_meta_dir = output_path / "texts_with_metadata"
    texts_with_meta_dir.mkdir(exist_ok=True)
    
    for doc in documents:
        safe_name = re.sub(r'[^\w\-_.]', '_', doc['title'])[:50]
        txt_file = texts_with_meta_dir / f"{doc['id']}_{safe_name}.txt"
        
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"标题: {doc['title']}\n")
            f.write(f"来源文件: {doc['metadata']['source_file']}\n")
            f.write(f"字数: {doc['metadata']['word_count']}\n")
            f.write(f"行数: {doc['metadata']['line_count']}\n")
            f.write("=" * 60 + "\n\n")
            f.write(doc['content'])
    
    # 4. 所有文本合并 (适合批量处理)
    combined_file = output_path / "all_text_combined.txt"
    with open(combined_file, 'w', encoding='utf-8') as f:
        for i, doc in enumerate(documents, 1):
            if i > 1:  # 文档间添加分隔符
                f.write(f"\n\n{'='*80}\n")
                f.write(f"文档 {i}: {doc['title']}\n")
                f.write(f"来源: {doc['metadata']['source_file']}\n")
                f.write('='*80 + "\n\n")
            else:
                f.write(f"文档 {i}: {doc['title']}\n")
                f.write(f"来源: {doc['metadata']['source_file']}\n")
                f.write('='*80 + "\n\n")
            
            f.write(doc['content'])
    
    # 5. 纯文本合并 (完全干净的文本)
    pure_text_file = output_path / "pure_text_combined.txt"
    with open(pure_text_file, 'w', encoding='utf-8') as f:
        for i, doc in enumerate(documents):
            if i > 0:
                f.write('\n\n')  # 文档间只用空行分隔
            f.write(doc['content'])
    
    # 6. 文档索引 (便于定位)
    index_file = output_path / "document_index.txt"
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write("文档索引\n")
        f.write("="*50 + "\n\n")
        for doc in documents:
            f.write(f"ID: {doc['id']}\n")
            f.write(f"标题: {doc['title']}\n")
            f.write(f"来源: {doc['metadata']['source_file']}\n")
            f.write(f"字数: {doc['metadata']['word_count']:,}\n")
            f.write(f"行数: {doc['metadata']['line_count']}\n")
            f.write("-" * 30 + "\n\n")
    
    # 7. 统计信息
    total_words = sum(doc['metadata']['word_count'] for doc in documents)
    total_chars = sum(doc['metadata']['char_count'] for doc in documents)
    
    stats = {
        "extraction_summary": {
            "total_documents": len(documents),
            "total_words": total_words,
            "total_characters": total_chars,
            "average_words_per_doc": total_words // len(documents) if documents else 0,
            "largest_doc": max(documents, key=lambda x: x['metadata']['word_count']) if documents else None,
            "smallest_doc": min(documents, key=lambda x: x['metadata']['word_count']) if documents else None
        },
        "output_files": {
            "structured_data": "documents.json",
            "individual_texts": "texts/*.txt",
            "texts_with_metadata": "texts_with_metadata/*.txt", 
            "combined_with_headers": "all_text_combined.txt",
            "pure_text_only": "pure_text_combined.txt",
            "document_index": "document_index.txt"
        }
    }
    
    with open(output_path / "extraction_stats.json", 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    # 输出统计信息
    print(f"\n📊 提取统计:")
    print(f"   📄 文档总数: {len(documents)}")
    print(f"   📝 总字数: {total_words:,}")
    print(f"   📏 总字符数: {total_chars:,}")
    print(f"   📈 平均每文档字数: {stats['extraction_summary']['average_words_per_doc']:,}")
    
    print(f"\n📁 生成的文件:")
    print(f"   📋 documents.json - 结构化数据")
    print(f"   📂 texts/ - 纯文本文件 (无元数据)")
    print(f"   📂 texts_with_metadata/ - 带元数据的文本文件")
    print(f"   📄 all_text_combined.txt - 合并文本 (带标题)")
    print(f"   📄 pure_text_combined.txt - 纯文本合并 (无标题)")
    print(f"   📋 document_index.txt - 文档索引")
    print(f"   📊 extraction_stats.json - 提取统计")
    
    print(f"\n💡 使用建议:")
    print(f"   - 用于RAG: 使用 texts/ 目录中的文件")
    print(f"   - 批量处理: 使用 pure_text_combined.txt")
    print(f"   - 保留来源: 使用 texts_with_metadata/ 目录")

# 主函数
if __name__ == "__main__":
    import sys
    
    chm_file = "/Users/janice.xu/Downloads/COC6th玩家整合手册v1.7 Super Extra II.chm" 
    output_dir = f"{Path(chm_file).stem}_extracted"
    
    print("🚀 开始处理CHM文件...")
    documents = extract_chm_with_7zip(chm_file, output_dir)
    
    if documents:
        print(f"\n✅ 处理完成！输出目录: {output_dir}")
        print("\n📁 生成的文件:")
        print(f"   - documents.json (结构化数据)")
        print(f"   - texts/ (单独文本文件)")
        print(f"   - combined_text.txt (合并文本)")
        print(f"   - rag_chunks.json (RAG分块)")
        print(f"   - statistics.json (统计信息)")
    else:
        print("❌ 处理失败")