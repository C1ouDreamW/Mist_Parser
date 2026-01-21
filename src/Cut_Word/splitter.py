import os
import re
from markitdown import MarkItDown
import pypandoc

print("=============================================")
print("Mist_Parser 文档切分工具启动中...")
print("=============================================")

# 目录设置
INPUT_LARGE_DIR = "data/input_large"
OUTPUT_DIR = "data/input"

CHUNK_SIZE = 2500  # 每个切分片段的目标字符数
LOOKAHEAD_RANGE = 500  # 向前查找题号的范围

# 匹配：\n1. 或 \n10、 或 \n 2. 或 \n一、 等格式
QUESTION_PATTERN = r'\n\s*(\d+|[一二三四五六七八九十]+)[\.、．\s]'

# 确保目录存在
os.makedirs(INPUT_LARGE_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"1. 检查目录结构...")
print(f"   - 原始大文件目录: {INPUT_LARGE_DIR}")
print(f"   - 切分后输出目录: {OUTPUT_DIR}")
print(f"   - 切分目标大小: {CHUNK_SIZE} 字符/片段")
print(f"   - 向前查找范围: {LOOKAHEAD_RANGE} 字符")
print("   - 目录检查完成")

def parse_document(file_path: str) -> str:
    """解析文档并返回文本内容"""
    file_ext = os.path.splitext(file_path)[1].lower()
    print(f"   - 解析文件: {os.path.basename(file_path)}")
    print(f"   - 文件类型: {file_ext}")
    
    if file_ext == ".txt":
        # 直接读取 txt 文件
        print("   - 使用文本读取方式解析...")
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        print(f"   - 解析完成，文本长度: {len(content)} 字符")
        return content
    elif file_ext == ".doc":
        raise Exception("不支持的文件格式: .doc (旧版 Word 文档)。请将文件另存为 .docx 格式后重试。")
    elif file_ext == ".docx":
        print("   - 检测到 .docx，使用 Pandoc 转换以保留公式...")
        try:
            # 使用 Pandoc 将 docx 转为 markdown
            output = pypandoc.convert_file(
                file_path, 
                'markdown', 
                format='docx', 
                extra_args=['--wrap=none']
            )
            print(f"   - 解析完成，文本长度: {len(output)} 字符")
            return output
        except Exception as e:
            print(f"   ⚠️ Pandoc 转换失败，尝试降级使用 MarkItDown: {e}")
            print("   - 降级使用 markitdown 解析...")
            md = MarkItDown()
            result = md.convert(file_path)
            markdown_content = result.text_content
            print(f"   - 解析完成，文本长度: {len(markdown_content)} 字符")
            return markdown_content

    else:
        # 使用 markitdown 处理其他文档类型
        print(f"   - 检测到未被支持的类型 {file_ext}，是否强制使用 markitdown 解析？(y/n)")
        user_input = input().strip().lower()
        if user_input != 'y':
            raise Exception(f"不支持的文件格式: {file_ext}。请将文件转换为 .txt, .docx 格式后重试。")
        
        try:
            print("   - 使用 markitdown 解析...")
            md = MarkItDown()
            result = md.convert(file_path)
            markdown_content = result.text_content
            print(f"   - 解析完成，文本长度: {len(markdown_content)} 字符")
            return markdown_content
        except Exception as e:
            # 捕获 markitdown 解析错误
            error_msg = str(e)
            if ".doc" in error_msg or "XLRDError" in error_msg:
                raise Exception("不支持的文件格式: .doc (旧版 Word 文档)。请将文件另存为 .docx 格式后重试。")
            else:
                raise Exception(f"文档解析失败: {str(e)}")

def find_next_question_start(content: str, start_pos: int, end_pos: int) -> int:
    """
    在指定范围内查找下一个题目的开始位置
    
    Args:
        content: 文本内容
        start_pos: 开始查找的位置
        end_pos: 结束查找的位置
        
    Returns:
        找到的题号位置，如果没找到返回 -1
    """
    # 确保 end_pos 不超过文本长度
    end_pos = min(end_pos, len(content))
    
    # 提取查找范围的文本
    search_text = content[start_pos:end_pos]
    
    # 查找匹配的题号
    match = re.search(QUESTION_PATTERN, search_text)
    
    if match:
        # 返回在原始文本中的位置
        return start_pos + match.start()
    else:
        return -1

def find_previous_double_newline(content: str, start_pos: int, end_pos: int) -> int:
    """
    在指定范围内查找前一个双换行符的位置（兜底策略）
    
    Args:
        content: 文本内容
        start_pos: 开始查找的位置
        end_pos: 结束查找的位置
        
    Returns:
        找到的双换行符位置，如果没找到返回 -1
    """
    # 确保 start_pos 不小于 0
    start_pos = max(0, start_pos)
    
    # 提取查找范围的文本
    search_text = content[start_pos:end_pos]
    
    # 查找最后一个双换行符
    split_pos = search_text.rfind('\n\n')
    
    if split_pos != -1:
        # 返回在原始文本中的位置
        return start_pos + split_pos
    else:
        # 如果没找到双换行符，查找单换行符
        split_pos = search_text.rfind('\n')
        if split_pos != -1:
            return start_pos + split_pos
        else:
            return -1

def smart_chunking(content: str, chunk_size: int) -> list:
    """
    基于题号锚点的智能切分文本内容
    
    Args:
        content: 要切分的文本内容
        chunk_size: 每个切分片段的目标大小
        
    Returns:
        切分后的文本片段列表
    """
    chunks = []
    current_pos = 0
    content_length = len(content)
    
    print(f"   - 开始智能切分，总长度: {content_length} 字符")
    print(f"   - 使用题号锚点切分算法")
    
    while current_pos < content_length:
        # 计算当前切分点
        target_end = current_pos + chunk_size
        
        # 如果接近文本末尾，直接取剩余部分
        if target_end >= content_length:
            chunks.append(content[current_pos:].strip())
            break
        
        # 向前查找下一个题号的开始位置
        question_start = find_next_question_start(content, target_end, target_end + LOOKAHEAD_RANGE)
        
        if question_start != -1:
            # 找到了题号，在题号前面切分
            print(f"   - 在位置 {question_start} 处找到题号，执行切分...")
            chunk = content[current_pos:question_start].strip()
            if chunk:  # 确保片段不为空
                chunks.append(chunk)
            # 更新当前位置到题号开始处
            current_pos = question_start
        else:
            # 没找到题号，使用兜底策略：查找双换行符
            print(f"   - 未找到题号，使用兜底策略查找双换行符...")
            split_pos = find_previous_double_newline(content, current_pos, target_end)
            
            if split_pos != -1:
                # 找到了双换行符，在双换行符后面切分
                print(f"   - 在位置 {split_pos} 处找到双换行符，执行切分...")
                chunk = content[current_pos:split_pos].strip()
                if chunk:  # 确保片段不为空
                    chunks.append(chunk)
                # 更新当前位置到双换行符后面
                current_pos = split_pos
            else:
                # 连双换行符都没找到，直接在目标位置切分
                print(f"   - 未找到合适切分点，直接在目标位置切分...")
                chunk = content[current_pos:target_end].strip()
                if chunk:  # 确保片段不为空
                    chunks.append(chunk)
                # 更新当前位置
                current_pos = target_end
    
    print(f"   - 切分完成，共生成 {len(chunks)} 个片段")
    return chunks

def process_file(file_path: str):
    """处理单个文件"""
    print(f"\n2. 开始处理文件: {os.path.basename(file_path)}")
    print("   -----------------------------------------")
    
    try:
        # 解析文档内容
        content = parse_document(file_path)
        
        # 执行智能切分
        chunks = smart_chunking(content, CHUNK_SIZE)
        
        # 保存切分后的文件
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        
        for i, chunk in enumerate(chunks, 1):
            output_filename = f"{base_name}_part{i}.txt"
            output_path = os.path.join(OUTPUT_DIR, output_filename)
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(chunk)
            
            print(f"   - 保存片段 {i}/{len(chunks)}: {output_filename}")
        
        print("   -----------------------------------------")
        print(f"   ✅ 处理完成: {os.path.basename(file_path)}")
        print(f"   ✅ 共切分为 {len(chunks)} 个部分 -> 保存至 {OUTPUT_DIR}/ 目录")
        
    except Exception as e:
        print(f"   ❌ 处理文件时出错: {file_path}")
        print(f"   ❌ 错误信息: {str(e)}")

def main():
    """主函数"""
    print(f"\n3. 开始扫描 {INPUT_LARGE_DIR}/ 目录...")
    
    # 获取 input_large 目录中的文件
    files = [f for f in os.listdir(INPUT_LARGE_DIR) if os.path.isfile(os.path.join(INPUT_LARGE_DIR, f))]
    
    if not files:
        print(f"   ❌ {INPUT_LARGE_DIR}/ 目录中没有文件，请将待处理的大文件放入该目录")
        print("=============================================")
        return
    
    print(f"   - 发现 {len(files)} 个文件待处理:")
    for f in files:
        print(f"     * {f}")
    
    print("\n4. 开始批量处理文件...")
    print("   -----------------------------------------")
    
    # 遍历处理每个文件
    for filename in files:
        file_path = os.path.join(INPUT_LARGE_DIR, filename)
        if os.path.isfile(file_path):
            process_file(file_path)
    
    print("\n5. 所有文件处理完成！")
    print("=============================================")

if __name__ == "__main__":
    main()