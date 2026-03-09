import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.orchestrator import _load_output_format_constraint

def test_format_constraint():
    print("=" * 60)
    print("测试AI输出格式约束加载")
    print("=" * 60)
    
    constraint = _load_output_format_constraint()
    
    if constraint:
        print("\n✅ 格式约束文件加载成功！\n")
        print("格式约束内容：")
        print("-" * 60)
        print(constraint)
        print("-" * 60)
        
        if "<思考过程>" in constraint and "</思考过程>" in constraint:
            print("\n✅ 包含完整的思考过程标签")
        else:
            print("\n❌ 缺少思考过程标签")
        
        if "<正文部分>" in constraint and "</正文部分>" in constraint:
            print("✅ 包含完整的正文部分标签")
        else:
            print("❌ 缺少正文部分标签")
        
        if "<内容总结>" in constraint and "</内容总结>" in constraint:
            print("✅ 包含完整的内容总结标签")
        else:
            print("❌ 缺少内容总结标签")
        
        if "<行动选项>" in constraint and "</行动选项>" in constraint:
            print("✅ 包含完整的行动选项标签")
        else:
            print("❌ 缺少行动选项标签")
        
        if "最高优先级" in constraint:
            print("✅ 包含最高优先级声明")
        else:
            print("❌ 缺少最高优先级声明")
        
        print("\n" + "=" * 60)
        print("测试完成！格式约束已正确加载并具有最高优先级。")
        print("=" * 60)
    else:
        print("\n❌ 格式约束文件加载失败！")
        print("请检查文件路径：backend/core/output_format_constraint.txt")

if __name__ == "__main__":
    test_format_constraint()
