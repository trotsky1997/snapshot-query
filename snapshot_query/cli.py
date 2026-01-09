"""
命令行接口
"""

import sys
from .query import SnapshotQuery


def main():
    """命令行工具主函数"""
    if len(sys.argv) < 3:
        print("用法:")
        print("  snapshot-query <文件路径> <命令> [参数]")
        print("\n命令:")
        print("  find-name <文本>          - 根据名称查找元素（模糊匹配）")
        print("  find-name-exact <文本>     - 根据名称查找元素（精确匹配）")
        print("  find-name-bm25 <文本> [数量] - 使用 BM25 算法查找元素（按相关性排序）")
        print("  find-role <角色>          - 根据角色查找元素")
        print("  find-ref <ref>            - 根据引用标识符查找元素")
        print("  find-text <文本>          - 查找包含指定文本的元素")
        print("  find-grep <模式> [字段]   - 使用正则表达式查找元素（支持 grep 语法）")
        print("  find-selector <选择器>    - 使用 CSS/jQuery 选择器语法查找元素")
        print("  interactive               - 列出所有可交互元素")
        print("  count                     - 统计各类型元素数量")
        print("  path <ref>                - 显示元素在树中的路径")
        print("  all-refs                  - 列出所有引用标识符")
        sys.exit(1)
    
    file_path = sys.argv[1]
    command = sys.argv[2]
    
    try:
        query = SnapshotQuery(file_path)
        
        if command == "find-name":
            if len(sys.argv) < 4:
                print("错误: 需要提供搜索文本")
                sys.exit(1)
            results = query.find_by_name(sys.argv[3])
            print(f"找到 {len(results)} 个匹配的元素:")
            for item in results:
                query.print_element(item)
                print()
        
        elif command == "find-name-exact":
            if len(sys.argv) < 4:
                print("错误: 需要提供搜索文本")
                sys.exit(1)
            results = query.find_by_name(sys.argv[3], exact=True)
            print(f"找到 {len(results)} 个精确匹配的元素:")
            for item in results:
                query.print_element(item)
                print()
        
        elif command == "find-name-bm25":
            if len(sys.argv) < 4:
                print("错误: 需要提供搜索文本")
                sys.exit(1)
            top_k = None
            if len(sys.argv) >= 5:
                try:
                    top_k = int(sys.argv[4])
                except ValueError:
                    print("警告: 数量参数无效，将返回所有结果", file=sys.stderr)
            results = query.find_by_name_bm25(sys.argv[3], top_k=top_k)
            print(f"找到 {len(results)} 个相关元素（按相关性排序）:")
            for item in results:
                query.print_element(item)
                print()
        
        elif command == "find-role":
            if len(sys.argv) < 4:
                print("错误: 需要提供角色类型")
                sys.exit(1)
            results = query.find_by_role(sys.argv[3])
            print(f"找到 {len(results)} 个 {sys.argv[3]} 元素:")
            for item in results[:10]:  # 只显示前10个
                query.print_element(item)
                print()
            if len(results) > 10:
                print(f"... 还有 {len(results) - 10} 个元素未显示")
        
        elif command == "find-ref":
            if len(sys.argv) < 4:
                print("错误: 需要提供引用标识符")
                sys.exit(1)
            result = query.find_by_ref(sys.argv[3])
            if result:
                print("找到元素:")
                query.print_element(result)
            else:
                print("未找到匹配的元素")
        
        elif command == "find-text":
            if len(sys.argv) < 4:
                print("错误: 需要提供搜索文本")
                sys.exit(1)
            results = query.find_elements_with_text(sys.argv[3])
            print(f"找到 {len(results)} 个包含文本的元素:")
            for item in results[:10]:  # 只显示前10个
                query.print_element(item)
                print()
            if len(results) > 10:
                print(f"... 还有 {len(results) - 10} 个元素未显示")
        
        elif command == "find-grep":
            if len(sys.argv) < 4:
                print("错误: 需要提供正则表达式模式")
                sys.exit(1)
            pattern = sys.argv[3]
            field = sys.argv[4] if len(sys.argv) >= 5 else 'name'
            
            if field not in ['name', 'role', 'ref']:
                print(f"错误: 字段必须是 'name', 'role' 或 'ref'，当前为: {field}")
                sys.exit(1)
            
            try:
                results = query.find_by_regex(pattern, field=field)
                print(f"找到 {len(results)} 个匹配正则表达式 '{pattern}' 的元素 (字段: {field}):")
                for item in results[:20]:  # 只显示前20个
                    query.print_element(item)
                    print()
                if len(results) > 20:
                    print(f"... 还有 {len(results) - 20} 个元素未显示")
            except ValueError as e:
                print(f"错误: {e}", file=sys.stderr)
                sys.exit(1)
        
        elif command == "find-selector":
            if len(sys.argv) < 4:
                print("错误: 需要提供选择器")
                sys.exit(1)
            selector = sys.argv[3]
            
            try:
                results = query.find_by_selector(selector)
                print(f"找到 {len(results)} 个匹配选择器 '{selector}' 的元素:")
                for item in results[:20]:  # 只显示前20个
                    query.print_element(item)
                    print()
                if len(results) > 20:
                    print(f"... 还有 {len(results) - 20} 个元素未显示")
            except Exception as e:
                print(f"错误: {e}", file=sys.stderr)
                sys.exit(1)
        
        elif command == "interactive":
            interactive = query.find_interactive_elements()
            total = sum(len(items) for items in interactive.values())
            print(f"找到 {total} 个可交互元素:\n")
            for role, items in interactive.items():
                if items:
                    print(f"{role}: {len(items)} 个")
                    for item in items[:5]:  # 每个类型只显示前5个
                        query.print_element(item, indent=1)
                        print()
                    if len(items) > 5:
                        print(f"  ... 还有 {len(items) - 5} 个 {role} 元素\n")
        
        elif command == "count":
            counts = query.count_elements()
            print("元素统计:")
            for role, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  {role}: {count}")
        
        elif command == "path":
            if len(sys.argv) < 4:
                print("错误: 需要提供引用标识符")
                sys.exit(1)
            path = query.get_element_path(sys.argv[3])
            if path:
                print("元素路径:")
                for i, element in enumerate(path):
                    print(f"\n层级 {i}:")
                    query.print_element(element, indent=1)
            else:
                print("未找到匹配的元素")
        
        elif command == "all-refs":
            refs = query.extract_all_refs()
            print(f"共 {len(refs)} 个引用标识符:")
            for ref in refs[:50]:  # 只显示前50个
                print(f"  {ref}")
            if len(refs) > 50:
                print(f"... 还有 {len(refs) - 50} 个引用标识符")
        
        else:
            print(f"未知命令: {command}")
            sys.exit(1)
    
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
