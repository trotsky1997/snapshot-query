"""
测试命令行接口（cli.py）
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from snapshot_query.cli import main


class TestCLI:
    """测试命令行接口"""
    
    def test_main_without_args(self, capsys):
        """测试不带参数时显示用法"""
        with patch('sys.argv', ['snapshot-query']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "用法:" in captured.out
    
    def test_main_find_name(self, sample_snapshot_file, capsys):
        """测试 find-name 命令"""
        with patch('sys.argv', ['snapshot-query', sample_snapshot_file, 'find-name', '搜索']):
            main()
            captured = capsys.readouterr()
            assert "找到" in captured.out or "个匹配的元素" in captured.out
    
    def test_main_find_name_exact(self, sample_snapshot_file, capsys):
        """测试 find-name-exact 命令"""
        with patch('sys.argv', ['snapshot-query', sample_snapshot_file, 'find-name-exact', '搜索按钮']):
            main()
            captured = capsys.readouterr()
            assert "找到" in captured.out or "个精确匹配的元素" in captured.out
    
    def test_main_find_name_bm25(self, sample_snapshot_file, capsys):
        """测试 find-name-bm25 命令"""
        with patch('sys.argv', ['snapshot-query', sample_snapshot_file, 'find-name-bm25', '搜索']):
            main()
            captured = capsys.readouterr()
            assert "找到" in captured.out or "个相关元素" in captured.out
    
    def test_main_find_name_bm25_with_top_k(self, sample_snapshot_file, capsys):
        """测试 find-name-bm25 命令（带数量限制）"""
        with patch('sys.argv', ['snapshot-query', sample_snapshot_file, 'find-name-bm25', '搜索', '5']):
            main()
            captured = capsys.readouterr()
            assert "找到" in captured.out
    
    def test_main_find_name_bm25_invalid_top_k(self, sample_snapshot_file, capsys):
        """测试 find-name-bm25 命令（无效的数量参数）"""
        with patch('sys.argv', ['snapshot-query', sample_snapshot_file, 'find-name-bm25', '搜索', 'invalid']):
            main()
            captured = capsys.readouterr()
            # 应该显示警告但继续执行
            assert "找到" in captured.out or "警告" in captured.err
    
    def test_main_find_role(self, sample_snapshot_file, capsys):
        """测试 find-role 命令"""
        with patch('sys.argv', ['snapshot-query', sample_snapshot_file, 'find-role', 'button']):
            main()
            captured = capsys.readouterr()
            assert "找到" in captured.out or "个 button 元素" in captured.out
    
    def test_main_find_role_missing_arg(self, sample_snapshot_file, capsys):
        """测试 find-role 命令缺少参数"""
        with patch('sys.argv', ['snapshot-query', sample_snapshot_file, 'find-role']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "错误" in captured.out or "需要提供" in captured.out
    
    def test_main_find_text_missing_arg(self, sample_snapshot_file, capsys):
        """测试 find-text 命令缺少参数"""
        with patch('sys.argv', ['snapshot-query', sample_snapshot_file, 'find-text']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "错误" in captured.out or "需要提供" in captured.out
    
    def test_main_find_ref_not_found(self, sample_snapshot_file, capsys):
        """测试 find-ref 命令（元素不存在）"""
        with patch('sys.argv', ['snapshot-query', sample_snapshot_file, 'find-ref', 'ref-nonexistent']):
            main()
            captured = capsys.readouterr()
            assert "未找到匹配的元素" in captured.out
    
    def test_main_find_text_many_results(self, sample_snapshot_file, capsys):
        """测试 find-text 命令（超过10个结果）"""
        import yaml
        import tempfile
        data = [{
            "role": "generic",
            "ref": "ref-root",
            "children": [{"role": "button", "ref": f"ref-btn-{i}", "name": f"搜索按钮{i}"} for i in range(15)]
        }]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False, encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True)
            temp_file = f.name
        
        try:
            with patch('sys.argv', ['snapshot-query', temp_file, 'find-text', '搜索']):
                main()
                captured = capsys.readouterr()
                assert "还有" in captured.out or "个元素未显示" in captured.out
        finally:
            import os
            os.unlink(temp_file)
    
    def test_main_find_selector_exception(self, sample_snapshot_file, capsys):
        """测试 find-selector 命令（异常处理）"""
        # 创建一个会导致异常的选择器（如果可能）
        with patch('sys.argv', ['snapshot-query', sample_snapshot_file, 'find-selector', 'button']):
            # 正常情况下不应该抛出异常
            main()
            captured = capsys.readouterr()
            assert len(captured.out) > 0 or len(captured.err) == 0
    
    def test_main_find_ref(self, sample_snapshot_file, capsys):
        """测试 find-ref 命令"""
        with patch('sys.argv', ['snapshot-query', sample_snapshot_file, 'find-ref', 'ref-btn-1']):
            main()
            captured = capsys.readouterr()
            assert "找到元素" in captured.out or "未找到匹配的元素" in captured.out
    
    def test_main_find_text(self, sample_snapshot_file, capsys):
        """测试 find-text 命令"""
        with patch('sys.argv', ['snapshot-query', sample_snapshot_file, 'find-text', '搜索']):
            main()
            captured = capsys.readouterr()
            assert "找到" in captured.out or "个包含文本的元素" in captured.out
    
    def test_main_count(self, sample_snapshot_file, capsys):
        """测试 count 命令"""
        with patch('sys.argv', ['snapshot-query', sample_snapshot_file, 'count']):
            main()
            captured = capsys.readouterr()
            # count 命令应该输出统计信息
            assert len(captured.out) > 0
    
    def test_main_interactive(self, sample_snapshot_file, capsys):
        """测试 interactive 命令"""
        with patch('sys.argv', ['snapshot-query', sample_snapshot_file, 'interactive']):
            main()
            captured = capsys.readouterr()
            # interactive 命令应该输出可交互元素
            assert len(captured.out) > 0
    
    def test_main_all_refs(self, sample_snapshot_file, capsys):
        """测试 all-refs 命令"""
        with patch('sys.argv', ['snapshot-query', sample_snapshot_file, 'all-refs']):
            main()
            captured = capsys.readouterr()
            # all-refs 命令应该输出所有 ref
            assert len(captured.out) > 0
    
    def test_main_path(self, sample_snapshot_file, capsys):
        """测试 path 命令"""
        with patch('sys.argv', ['snapshot-query', sample_snapshot_file, 'path', 'ref-btn-1']):
            main()
            captured = capsys.readouterr()
            # path 命令应该输出元素路径
            assert len(captured.out) > 0
    
    def test_main_find_name_missing_arg(self, sample_snapshot_file, capsys):
        """测试 find-name 命令缺少参数"""
        with patch('sys.argv', ['snapshot-query', sample_snapshot_file, 'find-name']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "错误" in captured.out or "需要提供" in captured.out
    
    def test_main_invalid_file(self, capsys):
        """测试无效文件路径"""
        with patch('sys.argv', ['snapshot-query', 'nonexistent.log', 'count']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "错误" in captured.err or "文件不存在" in captured.err
    
    def test_main_find_grep(self, sample_snapshot_file, capsys):
        """测试 find-grep 命令"""
        with patch('sys.argv', ['snapshot-query', sample_snapshot_file, 'find-grep', '搜索', 'name']):
            main()
            captured = capsys.readouterr()
            assert "找到" in captured.out or "个匹配正则表达式" in captured.out
    
    def test_main_find_grep_default_field(self, sample_snapshot_file, capsys):
        """测试 find-grep 命令（默认字段）"""
        with patch('sys.argv', ['snapshot-query', sample_snapshot_file, 'find-grep', '搜索']):
            main()
            captured = capsys.readouterr()
            assert "找到" in captured.out or "个匹配正则表达式" in captured.out
    
    def test_main_find_grep_invalid_field(self, sample_snapshot_file, capsys):
        """测试 find-grep 命令（无效字段）"""
        with patch('sys.argv', ['snapshot-query', sample_snapshot_file, 'find-grep', 'test', 'invalid']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "错误" in captured.out or "字段必须是" in captured.out
    
    def test_main_find_grep_missing_arg(self, sample_snapshot_file, capsys):
        """测试 find-grep 命令缺少参数"""
        with patch('sys.argv', ['snapshot-query', sample_snapshot_file, 'find-grep']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "错误" in captured.out or "需要提供" in captured.out
    
    def test_main_find_grep_invalid_regex(self, sample_snapshot_file, capsys):
        """测试 find-grep 命令（无效正则表达式）"""
        with patch('sys.argv', ['snapshot-query', sample_snapshot_file, 'find-grep', '[invalid', 'name']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "错误" in captured.err
    
    def test_main_find_selector(self, sample_snapshot_file, capsys):
        """测试 find-selector 命令"""
        with patch('sys.argv', ['snapshot-query', sample_snapshot_file, 'find-selector', 'button']):
            main()
            captured = capsys.readouterr()
            assert "找到" in captured.out or "个匹配选择器" in captured.out
    
    def test_main_find_selector_missing_arg(self, sample_snapshot_file, capsys):
        """测试 find-selector 命令缺少参数"""
        with patch('sys.argv', ['snapshot-query', sample_snapshot_file, 'find-selector']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "错误" in captured.out or "需要提供" in captured.out
    
    def test_main_find_role_many_results(self, sample_snapshot_file, capsys):
        """测试 find-role 命令（超过10个结果）"""
        # 创建一个包含多个button的快照文件
        import yaml
        import tempfile
        data = [{
            "role": "generic",
            "ref": "ref-root",
            "children": [{"role": "button", "ref": f"ref-btn-{i}", "name": f"按钮{i}"} for i in range(15)]
        }]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False, encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True)
            temp_file = f.name
        
        try:
            with patch('sys.argv', ['snapshot-query', temp_file, 'find-role', 'button']):
                main()
                captured = capsys.readouterr()
                assert "还有" in captured.out or "个元素未显示" in captured.out
        finally:
            import os
            os.unlink(temp_file)
    
    def test_main_find_grep_many_results(self, sample_snapshot_file, capsys):
        """测试 find-grep 命令（超过20个结果）"""
        import yaml
        import tempfile
        data = [{
            "role": "generic",
            "ref": "ref-root",
            "children": [{"role": "button", "ref": f"ref-btn-{i}", "name": f"搜索按钮{i}"} for i in range(25)]
        }]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False, encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True)
            temp_file = f.name
        
        try:
            with patch('sys.argv', ['snapshot-query', temp_file, 'find-grep', '搜索', 'name']):
                main()
                captured = capsys.readouterr()
                assert "还有" in captured.out or "个元素未显示" in captured.out
        finally:
            import os
            os.unlink(temp_file)
    
    def test_main_interactive_many_results(self, sample_snapshot_file, capsys):
        """测试 interactive 命令（超过5个结果）"""
        import yaml
        import tempfile
        data = [{
            "role": "generic",
            "ref": "ref-root",
            "children": [{"role": "button", "ref": f"ref-btn-{i}", "name": f"按钮{i}"} for i in range(10)]
        }]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False, encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True)
            temp_file = f.name
        
        try:
            with patch('sys.argv', ['snapshot-query', temp_file, 'interactive']):
                main()
                captured = capsys.readouterr()
                assert "还有" in captured.out or "个 button 元素" in captured.out
        finally:
            import os
            os.unlink(temp_file)
    
    def test_main_all_refs_many_results(self, sample_snapshot_file, capsys):
        """测试 all-refs 命令（超过50个结果）"""
        import yaml
        import tempfile
        data = [{
            "role": "generic",
            "ref": f"ref-{i}",
        } for i in range(60)]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False, encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True)
            temp_file = f.name
        
        try:
            with patch('sys.argv', ['snapshot-query', temp_file, 'all-refs']):
                main()
                captured = capsys.readouterr()
                assert "还有" in captured.out or "个引用标识符" in captured.out
        finally:
            import os
            os.unlink(temp_file)
    
    def test_main_path_not_found(self, sample_snapshot_file, capsys):
        """测试 path 命令（元素不存在）"""
        with patch('sys.argv', ['snapshot-query', sample_snapshot_file, 'path', 'ref-nonexistent']):
            main()
            captured = capsys.readouterr()
            assert "未找到匹配的元素" in captured.out
    
    def test_main_path_missing_arg(self, sample_snapshot_file, capsys):
        """测试 path 命令缺少参数"""
        with patch('sys.argv', ['snapshot-query', sample_snapshot_file, 'path']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "错误" in captured.out or "需要提供" in captured.out
    
    def test_main_unknown_command(self, sample_snapshot_file, capsys):
        """测试未知命令"""
        with patch('sys.argv', ['snapshot-query', sample_snapshot_file, 'unknown-command']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "未知命令" in captured.out
