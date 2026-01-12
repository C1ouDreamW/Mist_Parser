import os
import json
from markitdown import MarkItDown
from openai import OpenAI
from dotenv import load_dotenv

print("=============================================")
print("Mist_Parser 文档解析工具启动中...")
print("=============================================")

# 加载环境变量
print(" # 加载环境变量配置...")
load_dotenv()

# 初始化 OpenAI Client
print(" # 初始化 OpenAI Client...")
api_key = os.getenv("AI_API_KEY")
base_url = os.getenv("AI_BASE_URL", "https://api.deepseek.com/v1")
model_name = os.getenv("AI_MODEL_NAME", "deepseek-chat")

if not api_key:
    raise ValueError("请在 .env 文件中设置 AI_API_KEY")

print(f"   - API 基础 URL: {base_url}")
print(f"   - 模型名称: {model_name}")
print("   - OpenAI Client 初始化完成")

client = OpenAI(
    api_key=api_key,
    base_url=base_url
)

# 确保输入输出目录存在
print(" # 检查输入输出目录...")
INPUT_DIR = "input"
OUTPUT_DIR = "output"
PROCESSED_DIR = "processed"  # 存放已处理文件的目录

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
print(f"   - 输入目录: {INPUT_DIR}")
print(f"   - 输出目录: {OUTPUT_DIR}")
print(f"   - 已处理目录: {PROCESSED_DIR}")
print("   - 目录检查完成")

# 系统提示词，强约束 AI 输出格式
SYSTEM_PROMPT = """
你是一个专业的题目文本解析器，负责将非结构化的题目文本转换为标准化的 JSON 格式。

请严格按照以下 JSON 结构输出：
[
  {
    "type": "single_choice", // 题型：single_choice, multiple_choice, judge, fill, essay
    "content": "题干文本",
    "options": ["A. 选项内容", "B. 选项内容"], // 选择题必填，其他题型为空数组
    "answer": "A", // 多选则有多个答案，如 ["A", "B"]
  }
]

要求：
1. 只输出纯 JSON 字符串，不要包含任何 Markdown 标记（如 ```json）
2. 确保 JSON 格式合法
3. 正确识别题型并提取题干、选项和答案
4. 对于没有明确答案的题目，保持 answer 字段为空字符串
"""

def parse_document(file_path: str) -> str:
    """解析文档并返回 Markdown 文本"""
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
    else:
        # 使用 markitdown 处理其他文档类型
        try:
            print("   - 使用 markitdown 解析...")
            md = MarkItDown()
            result = md.convert(file_path)
            markdown_content = result.text_content
            print(f"   - 解析完成，Markdown 长度: {len(markdown_content)} 字符")
            return markdown_content
        except Exception as e:
            raise Exception(f"文档解析失败: {str(e)}")

def process_file(file_path):
    """处理单个文件"""
    print(f"\n4. 开始处理文件: {os.path.basename(file_path)}")
    print("   -----------------------------------------")
    
    # 读取文件内容
    try:
        print("   - 步骤 1: 解析文档内容...")
        content = parse_document(file_path)
    except Exception as e:
        print(f"   ❌ 处理文件时出错: {file_path}")
        print(f"   ❌ 错误信息: {str(e)}")
        return False

    # 调用 AI API
    try:
        print("   - 步骤 2: 调用大模型 API 处理内容...")
        print("   - 发送请求到 AI 服务...")
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": content}
            ],
            temperature=0.1,
            response_format={"type": "text"}
        )
        
        # 提取 AI 回复
        print("   - 收到 AI 响应...")
        ai_response = response.choices[0].message.content.strip()
        print(f"   - AI 响应长度: {len(ai_response)} 字符")
        
        # 清洗内容，去除可能的 Markdown 代码块标记
        print("   - 步骤 3: 清洗 AI 响应内容...")
        if ai_response.startswith("```json"):
            print("   - 移除 JSON 代码块标记...")
            ai_response = ai_response[7:]
        if ai_response.endswith("```"):
            ai_response = ai_response[:-3]
        ai_response = ai_response.strip()
        print(f"   - 清洗后内容长度: {len(ai_response)} 字符")
        
        # 解析 JSON
        print("   - 步骤 4: 解析 JSON 响应...")
        try:
            json_data = json.loads(ai_response)
            print(f"   - JSON 解析成功，题目数量: {len(json_data)}")
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON 解析失败: {str(e)}")
            print(f"   ❌ 响应内容预览: {ai_response[:200]}...")
            return False
        
        # 保存到输出目录
        print("   - 步骤 5: 保存解析结果...")
        output_filename = os.path.splitext(os.path.basename(file_path))[0] + ".json"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        # 移动已处理的文件到 processed 目录
        print("   - 步骤 6: 移动已处理文件...")
        processed_file_path = os.path.join(PROCESSED_DIR, os.path.basename(file_path))
        os.rename(file_path, processed_file_path)
        print(f"   - 文件已移动到: {processed_file_path}")
        
        print(f"   ✅ 成功保存到: {output_path}")
        print("   -----------------------------------------")
        print(f"   ✅ 文件处理完成: {os.path.basename(file_path)}")
        return True
        
    except Exception as e:
        print(f"   ❌ 处理文件时出错: {file_path}")
        print(f"   ❌ 错误信息: {str(e)}")
        return False

def main():
    """主函数"""
    print("\n # 开始扫描输入目录...")
    files = [f for f in os.listdir(INPUT_DIR) if os.path.isfile(os.path.join(INPUT_DIR, f))]
    
    if not files:
        print("   ❌ 输入目录中没有文件，请将待处理的文档放入 input/ 目录")
        print("=============================================")
        return
    
    print(f"   - 发现 {len(files)} 个文件待处理:")
    for f in files:
        print(f"     * {f}")
    
    print("\n6. 开始批量处理文件...")
    print("   -----------------------------------------")
    
    # 遍历输入目录下的所有文件
    processed_count = 0
    success_count = 0
    
    for filename in files:
        file_path = os.path.join(INPUT_DIR, filename)
        if os.path.isfile(file_path):
            processed_count += 1
            if process_file(file_path):
                success_count += 1
    
    print("\n # 处理完成！")
    print("   -----------------------------------------")
    print(f"   - 总处理文件数: {processed_count}")
    print(f"   - 成功处理数: {success_count}")
    print(f"   - 失败处理数: {processed_count - success_count}")
    print("   -----------------------------------------")
    print("Mist_Parser 文档解析工具执行完毕")
    print("=============================================")

if __name__ == "__main__":
    main()