"""
快照日志文件查询工具包
用于高效查询和分析 cursor-ide-browser 生成的快照日志文件
"""

from .query import SnapshotQuery

try:
    from .models import SnapshotElement, SnapshotData
    __all__ = ["SnapshotQuery", "SnapshotElement", "SnapshotData"]
except ImportError:
    __all__ = ["SnapshotQuery"]

__version__ = "0.1.0"
