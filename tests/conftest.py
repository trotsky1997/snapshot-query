"""
pytest 配置和共享 fixtures
"""

import pytest
import tempfile
import yaml
from pathlib import Path


@pytest.fixture
def sample_snapshot_data():
    """创建示例快照数据"""
    return [
        {
            "role": "generic",
            "ref": "ref-root",
            "children": [
                {
                    "role": "button",
                    "ref": "ref-btn-1",
                    "name": "搜索按钮"
                },
                {
                    "role": "link",
                    "ref": "ref-link-1",
                    "name": "Google 首页"
                },
                {
                    "role": "textbox",
                    "ref": "ref-input-1",
                    "name": "搜索框"
                },
                {
                    "role": "generic",
                    "ref": "ref-container",
                    "children": [
                        {
                            "role": "button",
                            "ref": "ref-btn-2",
                            "name": "登录"
                        },
                        {
                            "role": "link",
                            "ref": "ref-link-2",
                            "name": "帮助"
                        }
                    ]
                }
            ]
        }
    ]


@pytest.fixture
def sample_snapshot_file(sample_snapshot_data, tmp_path):
    """创建临时快照文件"""
    snapshot_file = tmp_path / "test-snapshot.log"
    with open(snapshot_file, 'w', encoding='utf-8') as f:
        yaml.dump(sample_snapshot_data, f, allow_unicode=True, default_flow_style=False)
    return str(snapshot_file)


@pytest.fixture
def complex_snapshot_data():
    """创建更复杂的示例快照数据（用于测试边界情况）"""
    return [
        {
            "role": "generic",
            "ref": "ref-complex-root",
            "children": [
                {
                    "role": "button",
                    "ref": "ref-exact-match",
                    "name": "精确匹配测试"
                },
                {
                    "role": "button",
                    "ref": "ref-partial-match",
                    "name": "部分匹配测试按钮"
                },
                {
                    "role": "link",
                    "ref": "ref-no-name",
                    # 没有 name 字段
                },
                {
                    "role": "textbox",
                    "ref": "ref-case-test",
                    "name": "Case Test"
                },
                {
                    "role": "generic",
                    "ref": "ref-nested",
                    "children": [
                        {
                            "role": "button",
                            "ref": "ref-deep-button",
                            "name": "深层按钮"
                        }
                    ]
                }
            ]
        }
    ]


@pytest.fixture
def complex_snapshot_file(complex_snapshot_data, tmp_path):
    """创建复杂的临时快照文件"""
    snapshot_file = tmp_path / "test-complex-snapshot.log"
    with open(snapshot_file, 'w', encoding='utf-8') as f:
        yaml.dump(complex_snapshot_data, f, allow_unicode=True, default_flow_style=False)
    return str(snapshot_file)


@pytest.fixture
def empty_snapshot_file(tmp_path):
    """创建空的快照文件"""
    snapshot_file = tmp_path / "empty-snapshot.log"
    with open(snapshot_file, 'w', encoding='utf-8') as f:
        yaml.dump([], f)
    return str(snapshot_file)
