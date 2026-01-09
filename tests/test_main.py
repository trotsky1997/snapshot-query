"""
测试 __main__.py 模块入口
"""

import pytest
import sys
from unittest.mock import patch
from snapshot_query.__main__ import main


class TestMainModule:
    """测试 __main__.py 模块"""
    
    def test_main_module_entry_point(self, sample_snapshot_file, capsys):
        """测试通过 python -m snapshot_query 运行"""
        with patch('sys.argv', ['snapshot-query', sample_snapshot_file, 'count']):
            main()
            captured = capsys.readouterr()
            assert "元素统计" in captured.out or len(captured.out) > 0
    
    def test_main_module_without_args(self, capsys):
        """测试不带参数时显示用法"""
        with patch('sys.argv', ['snapshot-query']):
            with pytest.raises(SystemExit):
                main()
            captured = capsys.readouterr()
            assert "用法:" in captured.out
    
    def test_main_module_direct_execution(self, sample_snapshot_file):
        """测试直接执行 __main__.py"""
        # 测试 if __name__ == "__main__" 分支
        import subprocess
        import sys
        result = subprocess.run(
            [sys.executable, '-m', 'snapshot_query', sample_snapshot_file, 'count'],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        assert result.returncode == 0
        assert len(result.stdout) > 0
