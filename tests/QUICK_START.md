# Pytest 快速开始

## 运行测试

```bash
# 运行所有测试
pytest

# 运行特定文件
pytest tests/test_models.py

# 运行特定测试
pytest tests/test_query.py::TestSnapshotQuery::test_find_by_name_fuzzy

# 详细输出
pytest -v

# 显示覆盖率
pytest --cov=snapshot_query --cov-report=html
```

## 测试结构

- `tests/test_models.py` - 数据模型测试（15个测试）
- `tests/test_query.py` - 查询功能测试（47个测试）
- `tests/test_cli.py` - 命令行接口测试（14个测试）

**总计：65个测试，全部通过 ✅**

## 覆盖率

当前测试覆盖率达到 **59%**，核心功能（models.py）达到 **100%** 覆盖率。

## 关键概念

### Fixtures

测试使用 fixtures 提供测试数据：

```python
def test_example(sample_snapshot_file):
    query = SnapshotQuery(sample_snapshot_file)
    # 使用测试数据
```

### 断言

```python
assert len(results) > 0
assert result.role == "button"
with pytest.raises(ValueError):
    # 测试异常
```

### Mock

```python
from unittest.mock import patch

with patch('sys.argv', ['snapshot-query', 'file.log', 'count']):
    main()
```

## 添加新测试

1. 在相应的测试文件中添加测试函数
2. 使用 `test_` 前缀命名
3. 使用 fixtures 提供测试数据
4. 编写清晰的断言
5. 运行测试确保通过
