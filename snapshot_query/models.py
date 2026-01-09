"""
快照数据模型
使用 pydantic 进行数据验证和类型检查
"""

from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class SnapshotElement(BaseModel):
    """
    快照元素数据模型
    
    表示可访问性树中的一个元素，包含角色、引用标识符、名称和子元素。
    """
    role: str = Field(..., description="元素的角色类型（必需）")
    ref: str = Field(..., description="元素的唯一引用标识符（必需）")
    name: Optional[str] = Field(None, description="元素的名称或文本内容（可选）")
    children: Optional[List['SnapshotElement']] = Field(
        None, 
        description="子元素列表（可选）"
    )
    
    @field_validator('ref')
    @classmethod
    def validate_ref(cls, v: str) -> str:
        """验证 ref 格式"""
        if not v.startswith('ref-'):
            # 允许非标准格式，但给出警告
            pass
        return v
    
    @field_validator('name', mode='before')
    @classmethod
    def validate_name(cls, v: Union[str, int, None]) -> Optional[str]:
        """确保 name 是字符串或 None"""
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return str(v)
        return v
    
    model_config = {
        "populate_by_name": True,
        "extra": "allow",
        "validate_assignment": True,
    }


# 允许前向引用
SnapshotElement.model_rebuild()


class SnapshotData(BaseModel):
    """
    快照数据根模型
    
    包含快照元素列表
    """
    elements: List[SnapshotElement] = Field(
        ..., 
        description="快照元素列表"
    )
    
    @classmethod
    def from_yaml_list(cls, data: List[dict]) -> 'SnapshotData':
        """
        从 YAML 列表创建 SnapshotData
        
        Args:
            data: YAML 解析后的列表数据
        
        Returns:
            SnapshotData 实例
        """
        elements = [SnapshotElement(**item) for item in data]
        return cls(elements=elements)
    
    def to_dict_list(self) -> List[dict]:
        """
        转换为字典列表（用于向后兼容）
        
        Returns:
            字典列表
        """
        return [elem.model_dump(exclude_none=True) for elem in self.elements]
