import os
import sys
import glob
import warnings
from dotenv import load_dotenv
import pdf2image
from dashscope import MultiModalConversation

load_dotenv()
warnings.filterwarnings("ignore")

class VisionConverter:
    def __init__(self):
        # 读取 API Key
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("环境变量 DASHSCOPE_API_KEY 未设置")

        
        # 指定模型
        self.model_name = "qwen-vl-max" 
        
        print(f" # VisionConverter 初始化成功 (使用模型: {self.model_name})")

    def convert_pdf(self, pdf_path):
        try:
            print(f"   - 正在调用 Poppler 将 PDF 转为图片: {os.path.basename(pdf_path)}")
            
            images = pdf2image.convert_from_path(pdf_path, dpi=200)
            
            all_markdown = ""
            total_pages = len(images)
            print(f"   - PDF 共 {total_pages} 页，开始识别...")
            
            # 创建临时目录存放图片
            temp_dir = "temp/temp_images"
            os.makedirs(temp_dir, exist_ok=True)
            
            for i, image in enumerate(images):
                print(f"     > 正在处理第 {i+1}/{total_pages} 页...")
                
                # 保存临时图片文件
                temp_img_path = os.path.join(temp_dir, f"temp_page_{i}.png")
                image.save(temp_img_path)
                abs_img_path = os.path.abspath(temp_img_path)

                prompt_text = """
                你是一个专业的试题提取助手。请识别这张图片中的内容，并【仅提取选择题部分】。
                
                【核心指令】：
                1. **内容筛选**：只提取“选择题”（包括单选和多选）。**绝对忽略**填空题、判断题、计算题、简答题以及页眉页脚等无关内容。
                2. **公式规范**：数学和物理公式必须使用标准 LaTeX 格式（例如 $E=mc^2$ 或 $$\\frac{a}{b}$$），严禁使用图片或乱码替代。
                3. **格式要求**：
                   - 保持原始题号（如 1, 2, 3...）。
                   - 每个选项（A, B, C, D）必须单独占一行，不要挤在同一行。
                4. **输出示例**：
                   1. 这是一个问题的内容 ($x^2$)?
                   A. 选项A的内容
                   B. 选项B的内容
                   C. 选项C的内容
                   D. 选项D的内容
                5. **输出限制**：直接输出题目内容，不要包含任何“好的”、“提取结果如下”等废话。如果当前图片中没有选择题，请输出“【无选择题】”。
                """

                try:
                    messages = [
                        {
                            "role": "user",
                            "content": [
                                {"image": f"file://{abs_img_path}"},
                                {"text": prompt_text}
                            ]
                        }
                    ]
                    
                    response = MultiModalConversation.call(
                        model=self.model_name,
                        messages=messages,
                        api_key=self.api_key
                    )
                    
                    if response.status_code == 200:
                        content = response.output.choices[0].message.content[0]['text']
                        all_markdown += content
                        all_markdown += "\n\n"
                        print(f"       ✅ 第 {i+1} 页识别成功")
                    else:
                        print(f"       ❌ 第 {i+1} 页识别失败: {response.code} - {response.message}")

                except Exception as e:
                    print(f"       ❌ 第 {i+1} 页发生错误: {e}")
                    continue
                finally:
                    # 清理临时文件
                    if os.path.exists(temp_img_path):
                        os.remove(temp_img_path)
            
            # 清理临时目录
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
                
            return all_markdown.strip()
            
        except pdf2image.exceptions.PDFInfoNotInstalledError:
            print("\n❌ 错误：未找到 Poppler 依赖！")
            raise
        except Exception as e:
            print(f"❌ 转换过程中发生错误：{str(e)}")
            raise

if __name__ == "__main__":
    input_dir = "data/input"
    output_dir = "data/intermediate"
    os.makedirs(output_dir, exist_ok=True)
    
    pdf_files = glob.glob(os.path.join(input_dir, "*.pdf"))
    
    if not pdf_files:
        print(f"⚠️  错误：在 {input_dir} 目录下未找到 PDF 文件")
        sys.exit(1)
    
    try:
        converter = VisionConverter()
        for pdf_path in pdf_files:
            filename = os.path.basename(pdf_path)
            output_path = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}.md")
            
            print(f"\n📄 正在转换：{filename}")
            result = converter.convert_pdf(pdf_path)
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(result)
            
    except Exception as e:
        print(f"\n❌ 程序运行出错：{e}")