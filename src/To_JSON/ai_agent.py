import os
import json
from openai import OpenAI
from dotenv import load_dotenv

class QuizGenerator:
    def __init__(self, input_dir="data/intermediate", output_dir="data/output", answers_dirs=["data/input", "data/answers"]):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.answers_dirs = answers_dirs
        self.client = None
        self.model_name = None
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 加载环境变量
        load_dotenv()
        
        # 初始化OpenAI客户端
        self._init_openai_client()
        
        # 读取全局答案
        self.global_answers_content = self._read_global_answers()
        
        # 系统提示词
        self.SYSTEM_PROMPT = """
你是一个专业的题目文本解析器，负责将非结构化的题目文本转换为标准化的JSON格式。

请严格按照以下JSON结构输出：
[
  {
    "type": "single_choice", // 题型：single_choice, multiple_choice, judge, fill, essay
    "content": "题干文本", // 题干文本，不包含题目序号
    "options": ["选项内容", "选项内容"], // 选择题必填，其他题型为空数组，选项前不加A/B/C/D
    "answer": "A", // 多选则有多个答案，如 ["A", "B"]
  }
]

要求：
0.对于LaTeX公式中的反斜杠，必须使用双反斜杠转义（例如输出"\\pi"而不是"\pi"），否则JSON解析会失败。
1. 只输出纯JSON字符串，不要包含任何Markdown标记（如```json）
2. 确保JSON格式合法
3. 正确识别题型并提取题干、选项和答案
4. 对于没有明确答案的题目，保持answer字段为空字符串
5. 确保题干前没有题目序号，例如"1. 这是一个单选题？"应解析为"这是一个单选题？"
"""
    
    def _init_openai_client(self):
        """初始化OpenAI客户端"""
        print(" # 初始化 OpenAI Client...")
        api_key = os.getenv("AI_API_KEY")
        base_url = os.getenv("AI_BASE_URL", "https://api.deepseek.com/v1")
        self.model_name = os.getenv("AI_MODEL_NAME", "deepseek-chat")
        
        if not api_key:
            raise ValueError("请在.env文件中设置AI_API_KEY")
        
        print(f"   - API基础URL: {base_url}")
        print(f"   - 模型名称: {self.model_name}")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        print("   - OpenAI Client初始化完成")
    
    def _read_global_answers(self):
        """读取全局答案文件"""
        print(" # 检查答案文件...")
        global_answers_content = ""
        answer_files = ["answers.txt", "answer_key.txt"]
        answer_file_found = None
        
        for check_dir in self.answers_dirs:
            for answer_file in answer_files:
                answer_path = os.path.join(check_dir, answer_file)
                if os.path.exists(answer_path) and os.path.isfile(answer_path):
                    with open(answer_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read().strip()
                        if content:
                            global_answers_content = content
                            answer_file_found = answer_file
                            print(f"   ✅ 找到答案文件: {os.path.join(check_dir, answer_file)}")
                            print(f"   - 答案文件长度: {len(global_answers_content)}字符")
                            break
            if answer_file_found:
                break
        
        if not answer_file_found:
            print("   - 未找到有效的答案文件，将使用题目中的答案（如果有）")
            print("   - 提示：请将答案文件命名为answers.txt或answer_key.txt，并放在input/或answers/目录中")
        
        return global_answers_content
    
    def _process_file(self, file_path):
        """处理单个Markdown文件"""
        file_name = os.path.basename(file_path)
        print(f"   - 处理文件: {file_name}")
        
        # 读取文件内容
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"   ❌ 读取文件失败: {str(e)}")
            return False
        
        # 调用AI API
        try:
            print("   - 调用大模型API处理内容...")
            
            # 构建用户内容，如果有全局答案则添加
            user_content = content
            if self.global_answers_content:
                print("   - 检测到全局答案，将注入到AI输入中...")
                user_content += "\n\n========== 参考答案区 ==========\n以下是整套试卷的参考答案，请根据题号，将上述题目中缺失的答案补充完整：\n"
                user_content += self.global_answers_content
                user_content += "\n============================="
            
            print("   - 发送请求到AI服务...")
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.1,
                response_format={"type": "text"}
            )
            
            # 提取AI回复
            print("   - 收到AI响应...")
            ai_response = response.choices[0].message.content.strip()
            print(f"   - AI响应长度: {len(ai_response)}字符")
            
            # 清洗内容，去除可能的Markdown代码块标记
            print("   - 清洗AI响应内容...")
            if ai_response.startswith("```json"):
                print("   - 移除JSON代码块标记...")
                ai_response = ai_response[7:]
            if ai_response.endswith("```"):
                ai_response = ai_response[:-3]
            ai_response = ai_response.strip()
            print(f"   - 清洗后内容长度: {len(ai_response)}字符")
            
            # 解析JSON
            print("   - 解析JSON响应...")
            try:
                json_data = json.loads(ai_response)
                print(f"   - JSON解析成功，题目数量: {len(json_data)}")
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON解析失败: {str(e)}")
                print(f"   ❌ 响应内容预览: {ai_response[:200]}...")
                return False
            
            # 保存到输出目录
            print("   - 保存解析结果...")
            output_filename = os.path.splitext(file_name)[0] + ".json"
            output_path = os.path.join(self.output_dir, output_filename)
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            print(f"   ✅ 成功保存到: {output_path}")
            return True
            
        except Exception as e:
            print(f"   ❌ 调用AI API时出错: {str(e)}")
            return False
    
    def process_all(self):
        """处理intermediate目录下的所有Markdown文件"""
        print(f"\n # 开始处理所有Markdown文件...")
        print(f"   - 输入目录: {self.input_dir}")
        print(f"   - 输出目录: {self.output_dir}")
        
        # 获取输入目录下的所有Markdown文件
        files = [f for f in os.listdir(self.input_dir) if os.path.isfile(os.path.join(self.input_dir, f)) and f.endswith(".md")]
        
        if not files:
            print("   ❌ 中间目录中没有Markdown文件，请先运行转换器模块")
            return False
        
        print(f"   - 发现 {len(files)} 个Markdown文件待处理:")
        for f in files:
            print(f"     * {f}")
        
        # 确认是否继续
        print("   - 确认是否继续...")
        print("   - 提示：发送请求将消耗API token，请确认内容无误后继续")
        confirm = input("   - 是否继续处理？(Y/N): ").strip().upper()
        
        if confirm not in ('Y', 'y'):
            print("   - 用户取消处理，退出")
            return False
        
        # 处理所有文件
        success_count = 0
        for filename in files:
            file_path = os.path.join(self.input_dir, filename)
            if os.path.isfile(file_path):
                if self._process_file(file_path):
                    success_count += 1
        
        print(f"\n # 处理完成！")
        print(f"   - 总处理文件数: {len(files)}")
        print(f"   - 成功处理数: {success_count}")
        print(f"   - 失败处理数: {len(files) - success_count}")
        return success_count > 0

if __name__ == "__main__":
    """独立运行入口，用于测试AI处理功能"""
    print("=============================================")
    print("QuizGenerator 独立测试模式")
    print("=============================================")
    
    generator = QuizGenerator()
    generator.process_all()
    
    print("=============================================")
    print("测试完成")
    print("=============================================")
