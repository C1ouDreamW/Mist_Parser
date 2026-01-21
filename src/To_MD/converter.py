import os
import pypandoc
from markitdown import MarkItDown

class DocumentConverter:
    def __init__(self, input_dir="data/input", output_dir="data/intermediate"):
        self.input_dir = input_dir
        self.output_dir = output_dir
        
        os.makedirs(self.output_dir, exist_ok=True)
    
    def _convert_file(self, file_path):
        """转换单个文件为Markdown"""
        file_ext = os.path.splitext(file_path)[1].lower()
        file_name = os.path.basename(file_path)
        print(f"   - 转换文件: {file_name}")
        print(f"   - 文件类型: {file_ext}")
        
        if file_ext == ".txt":
            # 直接读取txt文件
            print("   - 使用文本读取方式解析...")
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            print(f"   - 解析完成，文本长度: {len(content)} 字符")
            return content
        
        elif file_ext == ".docx":
            # 使用pypandoc解析docx文件，保留公式为LaTeX
            print("   - 检测到.docx，使用Pandoc转换以保留公式...")
            try:
                output = pypandoc.convert_file(
                    file_path, 
                    'markdown', 
                    format='docx', 
                    extra_args=['--wrap=none']
                )
                print(f"   - 解析完成，Markdown长度: {len(output)} 字符")
                return output
            except Exception as e:
                print(f"   ⚠️ Pandoc转换失败，尝试降级使用MarkItDown: {e}")
                # 失败则使用markitdown兜底
                print("   - 降级使用markitdown解析...")
                md = MarkItDown()
                result = md.convert(file_path)
                markdown_content = result.text_content
                print(f"   - 解析完成，Markdown长度: {len(markdown_content)} 字符")
                return markdown_content
        
        else:
            print(f"检测到暂不支持的文件类型：{file_ext}，请问是否要进行强制转换？(y/n)")
            choice = input().strip().lower()
            if choice != 'y':
                print("   - 用户选择了不强制转换，跳过该文件")
                return None
            try:
                print("   - 使用markitdown解析...")
                md = MarkItDown()
                result = md.convert(file_path)
                markdown_content = result.text_content
                print(f"   - 解析完成，Markdown长度: {len(markdown_content)} 字符")
                return markdown_content
            except Exception as e:
                raise Exception(f"文档解析失败: {str(e)}")
    
    def convert_all(self):
        """转换input目录下的所有文件为Markdown"""
        print(f"\n # 开始转换所有文档...")
        print(f"   - 输入目录: {self.input_dir}")
        print(f"   - 输出目录: {self.output_dir}")
        
        # 获取输入目录下的所有文件
        files = [f for f in os.listdir(self.input_dir) if os.path.isfile(os.path.join(self.input_dir, f))]
        
        if not files:
            print("   ❌ 输入目录中没有文件，请将待处理的文档放入input/目录")
            return
        
        print(f"   - 发现 {len(files)} 个文件待转换:")
        for f in files:
            print(f"     * {f}")
        
        # 转换所有文件
        success_count = 0
        for filename in files:
            file_path = os.path.join(self.input_dir, filename)
            try:
                # 转换文件
                markdown_content = self._convert_file(file_path)
                
                # 保存转换后的Markdown文件
                output_filename = os.path.splitext(filename)[0] + ".md"
                output_path = os.path.join(self.output_dir, output_filename)
                
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(markdown_content)
                
                print(f"   ✅ 转换成功，已保存到: {output_path}")
                success_count += 1
            except Exception as e:
                print(f"   ❌ 转换失败: {filename}")
                print(f"   ❌ 错误信息: {str(e)}")
        
        print(f"\n # 转换完成！")
        print(f"   - 总处理文件数: {len(files)}")
        print(f"   - 成功转换数: {success_count}")
        print(f"   - 失败转换数: {len(files) - success_count}")
        return success_count > 0

if __name__ == "__main__":
    """独立运行入口，用于测试文档转换功能"""
    print("=============================================")
    print("DocumentConverter 独立测试模式")
    print("=============================================")
    
    converter = DocumentConverter()
    converter.convert_all()
    
    print("=============================================")
    print("测试完成")
    print("=============================================")