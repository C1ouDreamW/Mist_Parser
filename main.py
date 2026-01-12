import os
import json
from markitdown import MarkItDown
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 初始化 OpenAI Client
api_key = os.getenv("AI_API_KEY")
base_url = os.getenv("AI_BASE_URL", "https://api.deepseek.com/v1")
model_name = os.getenv("AI_MODEL_NAME", "deepseek-chat")

if not api_key:
    raise ValueError("请在 .env 文件中设置 AI_API_KEY")

client = OpenAI(
    api_key=api_key,
    base_url=base_url
)

# 确保输入输出目录存在
INPUT_DIR = "input"
OUTPUT_DIR = "output"

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

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
    
    if file_ext == ".txt":
        # 直接读取 txt 文件
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    else:
        # 使用 markitdown 处理其他文档类型
        try:
            md = MarkItDown()
            result = md.convert(file_path)
            return result.text_content
        except Exception as e:
            raise Exception(f"文档解析失败: {str(e)}")

def process_file(file_path):
    """处理单个文件"""
    # 读取文件内容
    try:
        content = parse_document(file_path)
    except Exception as e:
        print(f"处理文件时出错: {file_path}")
        print(f"错误信息: {str(e)}")
        return False

    # 调用 AI API
    try:
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
        ai_response = response.choices[0].message.content.strip()
        
        # 清洗内容，去除可能的 Markdown 代码块标记
        if ai_response.startswith("```json"):
            ai_response = ai_response[7:]
        if ai_response.endswith("```"):
            ai_response = ai_response[:-3]
        ai_response = ai_response.strip()
        
        # 解析 JSON
        json_data = json.loads(ai_response)
        
        # 保存到输出目录
        output_filename = os.path.splitext(os.path.basename(file_path))[0] + ".json"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        print(f"成功处理文件: {file_path} -> {output_path}")
        return True
        
    except Exception as e:
        print(f"处理文件时出错: {file_path}")
        print(f"错误信息: {str(e)}")
        return False

def main():
    """主函数"""
    # 遍历输入目录下的所有文件
    for filename in os.listdir(INPUT_DIR):
        file_path = os.path.join(INPUT_DIR, filename)
        if os.path.isfile(file_path):
            process_file(file_path)

if __name__ == "__main__":
    main()