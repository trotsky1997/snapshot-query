# 测试文档

本目录包含 snapshot-query 项目的所有测试文件。

## 测试结构

```
tests/
├── __init__.py          # 测试包初始化
├── conftest.py          # pytest 配置和共享 fixtures
├── test_models.py       # 数据模型测试
├── test_query.py        # 查询功能测试
└── test_cli.py          # 命令行接口测试
```

## 运行测试

### 安装测试依赖

```bash
pip install -e ".[dev]"
```

或者使用 uv:

```bash
uv pip install -e ".[dev]"
```

### 运行所有测试

```bash
pytest
```

### 运行特定测试文件

```bash
pytest tests/test_models.py
pytest tests/test_query.py
pytest tests/test_cli.py
```

### 运行特定测试类或函数

```bash
pytest tests/test_query.py::TestSnapshotQuery
pytest tests/test_query.py::TestSnapshotQuery::test_find_by_name_fuzzy
```

### 带覆盖率报告

```bash
pytest --cov=snapshot_query --cov-report=html
```

覆盖率报告会生成在 `htmlcov/index.html`。

### 详细输出

```bash
pytest -v
```

### 只运行失败的测试

```bash
pytest --lf
```

### 运行上次失败的测试并显示输出

```bash
pytest --lf -x
```

## 测试覆盖范围

### test_models.py
- `SnapshotElement` 模型的所有字段和验证
- `SnapshotData` 模型的创建和转换
- 数据验证和类型转换

### test_query.py
- `BM25Index` 类的所有方法
- `SnapshotQuery` 类的所有查询方法
- 边界情况和错误处理

### test_cli.py
- 命令行接口的所有命令
- 参数验证和错误处理
- 输出格式

## Fixtures

测试使用 pytest fixtures 来提供测试数据：

- `sample_snapshot_data`: 基础示例快照数据
- `sample_snapshot_file`: 临时快照文件
- `complex_snapshot_data`: 复杂示例数据（用于边界测试）
- `complex_snapshot_file`: 复杂临时快照文件
- `empty_snapshot_file`: 空快照文件

## 编写新测试

添加新测试时，请遵循以下规范：

1. 测试文件命名：`test_*.py`
2. 测试类命名：`Test*`
3. 测试函数命名：`test_*`
4. 使用描述性的测试名称
5. 每个测试应该独立，不依赖其他测试的执行顺序
6. 使用 fixtures 来提供测试数据
7. 测试应该覆盖正常情况和边界情况

## 示例

```python
def test_find_by_name_fuzzy(self, sample_snapshot_file):
    """测试模糊名称查找"""
    query = SnapshotQuery(sample_snapshot_file)
    results = query.find_by_name("搜索")
    assert len(results) > 0
    names = [r.name for r in results if r.name]
    assert any("搜索" in name for name in names)
```
