import os
import sys
import argparse
import configparser
from pathlib import Path

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.To_MD.converter import DocumentConverter
from src.To_JSON.ai_agent import QuizGenerator

class MistParser:
    """Mist_Parser 主程序类"""
    
    def __init__(self):
        self.config = self._load_config()
        self.args = self._parse_args()
        self._merge_config()
    
    def _load_config(self):
        """加载配置文件"""
        config = configparser.ConfigParser()
        config_file = Path(__file__).parent.parent.parent / 'config.ini'
        
        if config_file.exists():
            config.read(config_file, encoding='utf-8')
        else:
            # 默认配置
            config['DEFAULT'] = {
                'input_dir': 'data/input',
                'intermediate_dir': 'data/intermediate',
                'output_dir': 'data/output',
                'answers_dirs': 'data/input,data/answers'
            }
        
        return config
    
    def _parse_args(self):
        """解析命令行参数"""
        parser = argparse.ArgumentParser(
            description='Mist_Parser 文档解析工具 - 将文档转换为结构化题目',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog='''
示例用法：
  python main.py                      # 使用默认配置运行
  python main.py --input data/docs    # 指定输入目录
  python main.py --skip-ai            # 仅执行文档转换，跳过AI处理
  python main.py --only-ai            # 仅执行AI处理，跳过文档转换
            '''
        )
        
        parser.add_argument('--input', '-i', 
                          help='输入文件目录')
        parser.add_argument('--intermediate', '-m', 
                          help='中间文件（Markdown）输出目录')
        parser.add_argument('--output', '-o', 
                          help='最终输出（JSON）目录')
        parser.add_argument('--answers-dirs', 
                          help='答案文件搜索目录，多个目录用逗号分隔')
        parser.add_argument('--skip-ai', action='store_true', 
                          help='仅执行文档转换，跳过AI处理')
        parser.add_argument('--only-ai', action='store_true', 
                          help='仅执行AI处理，跳过文档转换')
        parser.add_argument('--version', action='version', 
                          version='Mist_Parser v1.0')
        
        return parser.parse_args()
    
    def _merge_config(self):
        """合并配置文件和命令行参数"""
        # 优先级：命令行参数 > 配置文件 > 默认值
        self.input_dir = self.args.input or self.config['DEFAULT'].get('input_dir', 'data/input')
        self.intermediate_dir = self.args.intermediate or self.config['DEFAULT'].get('intermediate_dir', 'data/intermediate')
        self.output_dir = self.args.output or self.config['DEFAULT'].get('output_dir', 'data/output')
        
        # 处理答案目录
        if self.args.answers_dirs:
            self.answers_dirs = [d.strip() for d in self.args.answers_dirs.split(',')]
        else:
            answers_dirs_str = self.config['DEFAULT'].get('answers_dirs', 'data/input,data/answers')
            self.answers_dirs = [d.strip() for d in answers_dirs_str.split(',')]
    
    def _print_banner(self):
        """打印程序横幅"""
        banner = """=============================================
Mist_Parser 文档解析工具 v1.0
============================================="""
        print(banner)
    
    def _print_config(self):
        """打印当前配置"""
        print("\n当前配置:")
        print(f"   输入目录: {self.input_dir}")
        print(f"   中间目录: {self.intermediate_dir}")
        print(f"   输出目录: {self.output_dir}")
        print(f"   答案搜索目录: {', '.join(self.answers_dirs)}")
        print("   -----------------------------------------")
    
    def run_document_conversion(self):
        """执行文档转换"""
        print("\nStep 1/2: 文档转换...")
        print("   -----------------------------------------")
        
        converter = DocumentConverter(
            input_dir=self.input_dir,
            output_dir=self.intermediate_dir
        )
        
        if not converter.convert_all():
            print("   ❌ 文档转换失败，无法继续执行")
            return False
        
        return True
    
    def run_ai_processing(self):
        """执行AI处理"""
        print("\nStep 2/2: AI处理...")
        print("   -----------------------------------------")
        
        ai_agent = QuizGenerator(
            input_dir=self.intermediate_dir,
            output_dir=self.output_dir,
            answers_dirs=self.answers_dirs
        )
        
        if not ai_agent.process_all():
            print("   ❌ AI处理失败")
            return False
        
        return True
    
    def run(self):
        """主运行方法"""
        self._print_banner()
        
        try:
            self._print_config()
            
            # 执行流程
            success = True
            
            if not self.args.only_ai:
                # 执行文档转换
                if not self.run_document_conversion():
                    success = False
            
            if success and not self.args.skip_ai:
                # 执行AI处理
                if not self.run_ai_processing():
                    success = False
            
            if success:
                print("\n=============================================")
                print("✅ 所有处理流程完成！")
                print("=============================================")
                return True
            else:
                print("\n=============================================")
                print("❌ 处理流程部分或全部失败！")
                print("=============================================")
                return False
                
        except KeyboardInterrupt:
            print("\n   ⚠️ 用户中断操作")
            print("\n=============================================")
            print("❌ 操作已取消")
            print("=============================================")
            return False
        
        except Exception as e:
            print(f"\n   ❌ 执行过程中发生错误: {str(e)}")
            print(f"   ❌ 错误类型: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            print("\n=============================================")
            print("❌ 操作失败")
            print("=============================================")
            return False

def main():
    """主程序入口"""
    parser = MistParser()
    return parser.run()

if __name__ == "__main__":
    main()
