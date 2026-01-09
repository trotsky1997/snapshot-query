"""
测试数据模型（models.py）
"""

import pytest
from pydantic import ValidationError
from snapshot_query.models import SnapshotElement, SnapshotData


class TestSnapshotElement:
    """测试 SnapshotElement 模型"""
    
    def test_create_element_with_required_fields(self):
        """测试创建包含必需字段的元素"""
        element = SnapshotElement(
            role="button",
            ref="ref-test-123"
        )
        assert element.role == "button"
        assert element.ref == "ref-test-123"
        assert element.name is None
        assert element.children is None
    
    def test_create_element_with_all_fields(self):
        """测试创建包含所有字段的元素"""
        element = SnapshotElement(
            role="button",
            ref="ref-test-123",
            name="测试按钮",
            children=[]
        )
        assert element.role == "button"
        assert element.ref == "ref-test-123"
        assert element.name == "测试按钮"
        assert element.children == []
    
    def test_create_element_with_nested_children(self):
        """测试创建包含嵌套子元素的元素"""
        child = SnapshotElement(
            role="link",
            ref="ref-child-1",
            name="子链接"
        )
        parent = SnapshotElement(
            role="generic",
            ref="ref-parent-1",
            children=[child]
        )
        assert len(parent.children) == 1
        assert parent.children[0].role == "link"
        assert parent.children[0].name == "子链接"
    
    def test_ref_validation(self):
        """测试 ref 字段验证（允许非标准格式）"""
        # 标准格式
        element1 = SnapshotElement(role="button", ref="ref-standard")
        assert element1.ref == "ref-standard"
        
        # 非标准格式（应该允许）
        element2 = SnapshotElement(role="button", ref="non-standard-ref")
        assert element2.ref == "non-standard-ref"
    
    def test_name_validation_string(self):
        """测试 name 字段验证（字符串）"""
        element = SnapshotElement(
            role="button",
            ref="ref-1",
            name="测试名称"
        )
        assert element.name == "测试名称"
        assert isinstance(element.name, str)
    
    def test_name_validation_int_conversion(self):
        """测试 name 字段验证（整数转换为字符串）"""
        element = SnapshotElement(
            role="button",
            ref="ref-1",
            name=123
        )
        assert element.name == "123"
        assert isinstance(element.name, str)
    
    def test_name_validation_float_conversion(self):
        """测试 name 字段验证（浮点数转换为字符串）"""
        element = SnapshotElement(
            role="button",
            ref="ref-1",
            name=123.45
        )
        assert element.name == "123.45"
        assert isinstance(element.name, str)
    
    def test_name_validation_none(self):
        """测试 name 字段验证（None）"""
        element = SnapshotElement(
            role="button",
            ref="ref-1",
            name=None
        )
        assert element.name is None
    
    def test_missing_required_fields(self):
        """测试缺少必需字段时抛出验证错误"""
        with pytest.raises(ValidationError):
            SnapshotElement(role="button")
            # 缺少 ref
        
        with pytest.raises(ValidationError):
            SnapshotElement(ref="ref-1")
            # 缺少 role


class TestSnapshotData:
    """测试 SnapshotData 模型"""
    
    def test_create_from_yaml_list(self):
        """测试从 YAML 列表创建 SnapshotData"""
        yaml_data = [
            {
                "role": "button",
                "ref": "ref-1",
                "name": "按钮1"
            },
            {
                "role": "link",
                "ref": "ref-2",
                "name": "链接1"
            }
        ]
        
        snapshot_data = SnapshotData.from_yaml_list(yaml_data)
        assert len(snapshot_data.elements) == 2
        assert snapshot_data.elements[0].role == "button"
        assert snapshot_data.elements[1].role == "link"
    
    def test_create_from_yaml_list_with_children(self):
        """测试从包含子元素的 YAML 列表创建 SnapshotData"""
        yaml_data = [
            {
                "role": "generic",
                "ref": "ref-parent",
                "children": [
                    {
                        "role": "button",
                        "ref": "ref-child",
                        "name": "子按钮"
                    }
                ]
            }
        ]
        
        snapshot_data = SnapshotData.from_yaml_list(yaml_data)
        assert len(snapshot_data.elements) == 1
        assert snapshot_data.elements[0].role == "generic"
        assert len(snapshot_data.elements[0].children) == 1
        assert snapshot_data.elements[0].children[0].name == "子按钮"
    
    def test_to_dict_list(self):
        """测试转换为字典列表"""
        element1 = SnapshotElement(role="button", ref="ref-1", name="按钮")
        element2 = SnapshotElement(role="link", ref="ref-2")
        snapshot_data = SnapshotData(elements=[element1, element2])
        
        dict_list = snapshot_data.to_dict_list()
        assert len(dict_list) == 2
        assert dict_list[0]["role"] == "button"
        assert dict_list[0]["name"] == "按钮"
        assert dict_list[1]["role"] == "link"
        # None 值应该被排除
        assert "name" not in dict_list[1] or dict_list[1].get("name") is None
    
    def test_empty_elements_list(self):
        """测试空元素列表"""
        snapshot_data = SnapshotData(elements=[])
        assert len(snapshot_data.elements) == 0
        assert snapshot_data.to_dict_list() == []
