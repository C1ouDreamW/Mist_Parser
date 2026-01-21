import json
import os

"""
各模块功能：
1. check_json_file(): 检查单个JSON文件的格式正确性,包括题目类型、答案格式、有效选项等
2. generate_report(): 生成单个JSON文件的检查报告,包含通过情况和错误详情
3. get_all_json_files(): 递归获取指定目录下的所有JSON文件路径
4. generate_summary_report(): 生成多个JSON文件的汇总检查报告,包含统计信息和各文件结果
5. main(): 主函数，处理命令行参数，根据输入路径类型执行单个文件检查或文件夹遍历检查
"""

def check_json_file(json_path):
    """
    检查JSON文件格式正确性
    :param json_path: JSON文件路径
    :return: 检查结果字典
    """
    # 初始化检查结果
    results = {
        "file_path": json_path,
        "total_questions": 0,
        "passed_questions": 0,
        "failed_questions": 0,
        "errors": [],
        "status": "pass"
    }

    try:
        # 检查文件是否存在
        if not os.path.exists(json_path):
            results["status"] = "fail"
            results["errors"].append({
                "type": "FileError",
                "position": "N/A",
                "description": f"文件不存在: {json_path}"
            })
            return results

        # 读取并解析JSON文件
        with open(json_path, 'r', encoding='utf-8') as f:
            try:
                questions = json.load(f)
            except json.JSONDecodeError as e:
                results["status"] = "fail"
                results["errors"].append({
                    "type": "JSONDecodeError",
                    "position": f"Line {e.lineno}, Column {e.colno}",
                    "description": f"JSON解析错误: {e.msg}"
                })
                return results

        # 检查是否为列表格式
        if not isinstance(questions, list):
            results["status"] = "fail"
            results["errors"].append({
                "type": "FormatError",
                "position": "N/A",
                "description": "JSON文件必须是一个题目列表"
            })
            return results

        results["total_questions"] = len(questions)

        # 遍历每道题目
        for idx, question in enumerate(questions):
            question_position = f"Question {idx + 1}"
            question_valid = True

            # 检查题目基本字段
            if "type" not in question:
                results["errors"].append({
                    "type": "FieldMissing",
                    "position": question_position,
                    "description": "缺少题目类型字段(type)"
                })
                question_valid = False
                continue

            if "content" not in question:
                results["errors"].append({
                    "type": "FieldMissing",
                    "position": question_position,
                    "description": "缺少题目内容字段(content)"
                })
                question_valid = False

            if "options" not in question:
                results["errors"].append({
                    "type": "FieldMissing",
                    "position": question_position,
                    "description": "缺少选项字段(options)"
                })
                question_valid = False

            if "answer" not in question:
                results["errors"].append({
                    "type": "FieldMissing",
                    "position": question_position,
                    "description": "缺少答案字段(answer)"
                })
                question_valid = False

            if not question_valid:
                results["failed_questions"] += 1
                continue

            # 获取题目类型
            question_type = question["type"]
            answer = question["answer"]
            options = question["options"]

            # 生成有效选项字母列表（如A, B, C, D...）
            valid_option_letters = [chr(65 + i) for i in range(len(options))]

            # 单选题检查
            if question_type == "single_choice":
                # 检查答案是否为字符串
                if not isinstance(answer, str):
                    results["errors"].append({
                        "type": "AnswerFormatError",
                        "position": question_position,
                        "description": f"单选题答案必须是字符串类型，当前为: {type(answer).__name__}"
                    })
                    question_valid = False
                else:
                    # 检查答案数量
                    if len(answer) != 1:
                        results["errors"].append({
                            "type": "AnswerCountError",
                            "position": question_position,
                            "description": f"单选题答案数量必须为1个，当前为: {len(answer)}"
                        })
                        question_valid = False
                    # 检查答案是否有效
                    elif answer not in valid_option_letters:
                        results["errors"].append({
                            "type": "InvalidAnswerError",
                            "position": question_position,
                            "description": f"单选题答案无效，有效选项为: {', '.join(valid_option_letters)}，当前为: {answer}"
                        })
                        question_valid = False

            # 多选题检查
            elif question_type == "multiple_choice":
                # 检查答案是否为列表
                if not isinstance(answer, list):
                    results["errors"].append({
                        "type": "AnswerFormatError",
                        "position": question_position,
                        "description": f"多选题答案必须是列表类型，当前为: {type(answer).__name__}"
                    })
                    question_valid = False
                else:
                    # 检查答案数量
                    answer_count = len(answer)
                    if answer_count < 2:
                        results["errors"].append({
                            "type": "AnswerCountError",
                            "position": question_position,
                            "description": f"多选题答案数量必须为2个或以上，当前为: {answer_count}"
                        })
                        question_valid = False
                    else:
                        # 检查每个答案是否有效
                        for ans in answer:
                            if ans not in valid_option_letters:
                                results["errors"].append({
                                    "type": "InvalidAnswerError",
                                    "position": question_position,
                                    "description": f"多选题答案包含无效选项，有效选项为: {', '.join(valid_option_letters)}，当前无效选项: {ans}"
                                })
                                question_valid = False
                                break
            else:
                results["errors"].append({
                    "type": "InvalidTypeError",
                    "position": question_position,
                    "description": f"无效的题目类型: {question_type}，支持的类型为: single_choice, multiple_choice"
                })
                question_valid = False

            # 更新统计信息
            if question_valid:
                results["passed_questions"] += 1
            else:
                results["failed_questions"] += 1

        # 更新整体状态
        if results["failed_questions"] > 0:
            results["status"] = "fail"

        return results

    except Exception as e:
        results["status"] = "fail"
        results["errors"].append({
            "type": "UnexpectedError",
            "position": "N/A",
            "description": f"意外错误: {str(e)}"
        })
        return results


def generate_report(results):
    """
    生成检查报告
    :param results: 检查结果字典
    :return: 报告字符串
    """
    report = []
    report.append("=" * 60)
    report.append("JSON文件格式检查报告")
    report.append("=" * 60)
    report.append(f"文件路径: {results['file_path']}")
    report.append(f"总题目数: {results['total_questions']}")
    report.append(f"通过题目数: {results['passed_questions']}")
    report.append(f"失败题目数: {results['failed_questions']}")
    report.append(f"整体状态: {'✅ 通过' if results['status'] == 'pass' else '❌ 失败'}")
    report.append("=" * 60)

    if results['errors']:
        report.append("\n错误详情:")
        report.append("-" * 60)
        for i, error in enumerate(results['errors'], 1):
            report.append(f"{i}. [{error['type']}] {error['position']}: {error['description']}")
    else:
        report.append("\n🎉 未发现任何错误！")

    report.append("=" * 60)
    return "\n".join(report)


def get_all_json_files(directory):
    """
    获取目录下所有JSON文件
    :param directory: 目录路径
    :return: JSON文件路径列表
    """
    json_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.json'):
                json_files.append(os.path.join(root, file))
    return json_files


def generate_summary_report(all_results):
    """
    生成汇总报告
    :param all_results: 所有文件的检查结果列表
    :return: 汇总报告字符串
    """
    report = []
    report.append("=" * 60)
    report.append("JSON文件格式检查汇总报告")
    report.append("=" * 60)
    
    total_files = len(all_results)
    passed_files = sum(1 for r in all_results if r['status'] == 'pass')
    failed_files = total_files - passed_files
    
    total_questions = sum(r['total_questions'] for r in all_results)
    passed_questions = sum(r['passed_questions'] for r in all_results)
    failed_questions = sum(r['failed_questions'] for r in all_results)
    
    report.append(f"检查文件总数: {total_files}")
    report.append(f"通过文件数: {passed_files}")
    report.append(f"失败文件数: {failed_files}")
    report.append(f"总题目数: {total_questions}")
    report.append(f"通过题目数: {passed_questions}")
    report.append(f"失败题目数: {failed_questions}")
    report.append(f"整体状态: {'✅ 通过' if failed_files == 0 else '❌ 失败'}")
    report.append("=" * 60)
    
    # 按文件显示结果
    report.append("\n各文件检查结果:")
    report.append("-" * 60)
    for i, result in enumerate(all_results, 1):
        status = "✅ 通过" if result['status'] == 'pass' else "❌ 失败"
        report.append(f"{i}. {result['file_path']} - {status}")
        if result['failed_questions'] > 0:
            report.append(f"   题目总数: {result['total_questions']}, 通过: {result['passed_questions']}, 失败: {result['failed_questions']}")
    
    return "\n".join(report)


def main():
    """
    主函数
    """
    import sys
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
    else:
        # 默认测试文件夹
        input_path = "c:\\Users\\11502\\Desktop\\C1ouD\\Mist_Parser\\tests"

    all_results = []
    
    # 检查输入路径是文件还是文件夹
    if os.path.isfile(input_path):
        # 单个文件检查
        if input_path.endswith('.json'):
            results = check_json_file(input_path)
            all_results.append(results)
            report = generate_report(results)
            print(report)
        else:
            print("错误: 输入文件不是JSON文件")
            return 1
    elif os.path.isdir(input_path):
        # 文件夹遍历检查
        json_files = get_all_json_files(input_path)
        if not json_files:
            print(f"错误: 文件夹 {input_path} 中没有找到JSON文件")
            return 1
        
        print(f"开始检查文件夹: {input_path}")
        print(f"共找到 {len(json_files)} 个JSON文件")
        print("=" * 60)
        
        for json_file in json_files:
            print(f"\n正在检查: {json_file}")
            results = check_json_file(json_file)
            all_results.append(results)
            
            # 生成并打印单个文件报告
            report = generate_report(results)
            print(report)
        
        # 生成汇总报告
        summary_report = generate_summary_report(all_results)
        print(f"\n{'=' * 60}")
        print(summary_report)
    else:
        print(f"错误: 路径不存在: {input_path}")
        return 1
    
    # 返回状态码
    return 0 if all(r['status'] == 'pass' for r in all_results) else 1


if __name__ == "__main__":
    exit(main())
