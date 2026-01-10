#!/usr/bin/env python3
"""
快照日志文件查询工具
用于高效查询和分析 cursor-ide-browser 生成的快照日志文件
"""

import yaml
import sys
import re
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
from collections import defaultdict

from snapshot_query.models import SnapshotElement, SnapshotData


class BM25Index:
    """BM25 检索索引"""
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        初始化 BM25 索引
        
        Args:
            k1: 词频饱和度参数，默认 1.5
            b: 长度归一化参数，默认 0.75
        """
        self.k1 = k1
        self.b = b
        self.documents: List[str] = []
        self.doc_freqs: List[Dict[str, int]] = []
        self.idf: Dict[str, float] = {}
        self.avg_doc_len: float = 0.0
        self._built = False
    
    def _tokenize(self, text: str) -> List[str]:
        """简单的分词，支持中英文"""
        # 确保 text 是字符串
        if not isinstance(text, str):
            text = str(text)
        # 移除标点符号，保留中文字符、英文字母和数字
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text.lower())
        # 分割成词（中文按字符，英文按单词）
        tokens = []
        for word in text.split():
            # 如果是中文字符，按字符分割
            if re.match(r'[\u4e00-\u9fff]+', word):
                tokens.extend(list(word))
            else:
                tokens.append(word)
        return [t for t in tokens if t.strip()]
    
    def add_document(self, text: str):
        """添加文档到索引"""
        tokens = self._tokenize(text)
        self.documents.append(text)
        self.doc_freqs.append(defaultdict(int))
        for token in tokens:
            self.doc_freqs[-1][token] += 1
        self._built = False
    
    def build(self):
        """构建索引"""
        if self._built:
            return
        
        if not self.documents:
            self._built = True
            return
        
        # 计算平均文档长度
        total_len = sum(sum(freqs.values()) for freqs in self.doc_freqs)
        self.avg_doc_len = total_len / len(self.documents) if self.documents else 0
        
        # 计算 IDF（逆文档频率）
        doc_count = len(self.documents)
        term_doc_count = defaultdict(int)
        
        for freqs in self.doc_freqs:
            for term in freqs:
                term_doc_count[term] += 1
        
        self.idf = {
            term: math.log((doc_count - term_doc_count[term] + 0.5) / (term_doc_count[term] + 0.5) + 1.0)
            for term in term_doc_count
        }
        
        self._built = True
    
    def score(self, query: str, doc_idx: int) -> float:
        """计算查询与文档的相关性分数"""
        if not self._built:
            self.build()
        
        if doc_idx >= len(self.documents):
            return 0.0
        
        query_tokens = self._tokenize(query)
        doc_freqs = self.doc_freqs[doc_idx]
        doc_len = sum(doc_freqs.values())
        
        score = 0.0
        for term in query_tokens:
            if term not in self.idf:
                continue
            
            term_freq = doc_freqs.get(term, 0)
            if term_freq == 0:
                continue
            
            # BM25 公式
            idf = self.idf[term]
            numerator = idf * term_freq * (self.k1 + 1)
            denominator = term_freq + self.k1 * (1 - self.b + self.b * (doc_len / self.avg_doc_len))
            score += numerator / denominator
        
        return score
    
    def search(self, query: str, top_k: Optional[int] = None) -> List[Tuple[int, float]]:
        """搜索并返回排序后的结果"""
        if not self._built:
            self.build()
        
        scores = [(i, self.score(query, i)) for i in range(len(self.documents))]
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # 过滤掉分数为 0 的结果
        scores = [(idx, score) for idx, score in scores if score > 0]
        
        if top_k is not None:
            scores = scores[:top_k]
        
        return scores


class SnapshotQuery:
    """快照日志查询工具类"""
    
    def __init__(self, file_path: str):
        """
        初始化，加载快照文件
        
        Args:
            file_path: 快照文件路径
        """
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        with open(self.file_path, 'r', encoding='utf-8') as f:
            raw_data = yaml.safe_load(f)
        
        # 使用 pydantic 验证和加载数据
        self.snapshot_data = SnapshotData.from_yaml_list(raw_data)
        self.data = self.snapshot_data.elements  # 直接使用 pydantic 模型列表
        
        # BM25 索引（延迟构建）
        self._bm25_index: Optional[BM25Index] = None
        self._elements_with_names: List[SnapshotElement] = []
    
    def _build_bm25_index(self):
        """构建 BM25 索引（延迟初始化）"""
        if self._bm25_index is not None:
            return
        
        self._bm25_index = BM25Index()
        self._elements_with_names = []
        
        def collect_elements(items: List[SnapshotElement]):
            for item in items:
                if item.name:
                    self._elements_with_names.append(item)
                    self._bm25_index.add_document(item.name)
                
                if item.children:
                    collect_elements(item.children)
        
        collect_elements(self.data)
        self._bm25_index.build()
    
    def find_by_name_bm25(self, name: str, top_k: Optional[int] = None) -> List[SnapshotElement]:
        """
        使用 BM25 算法根据元素名称查找元素（按相关性排序）
        
        Args:
            name: 要搜索的元素名称
            top_k: 返回前 k 个最相关的结果，None 表示返回所有结果
        
        Returns:
            按相关性分数排序的元素列表
        """
        self._build_bm25_index()
        
        if not self._elements_with_names:
            return []
        
        # 使用 BM25 搜索
        results = self._bm25_index.search(name, top_k=top_k)
        
        # 返回对应的元素（按分数排序）
        return [self._elements_with_names[idx] for idx, _ in results]
    
    def find_by_name(self, name: str, exact: bool = False) -> List[Dict]:
        """根据元素名称查找元素"""
        results = []
        
        def search_recursive(items):
            for item in items:
                if 'name' in item:
                    item_name = item['name']
                    # 确保 item_name 是字符串
                    if not isinstance(item_name, str):
                        item_name = str(item_name)
                    
                    if exact:
                        if item_name == name:
                            results.append(item)
                    else:
                        if name in item_name:
                            results.append(item)
                
                if 'children' in item:
                    search_recursive(item['children'])
        
        search_recursive(self.data)
        return results
    
    def find_by_role(self, role: str) -> List[SnapshotElement]:
        """根据角色类型查找元素"""
        results = []
        
        def search_recursive(items: List[SnapshotElement]):
            for item in items:
                if item.role == role:
                    results.append(item)
                
                if item.children:
                    search_recursive(item.children)
        
        search_recursive(self.data)
        return results
    
    def find_by_ref(self, ref: str) -> Optional[SnapshotElement]:
        """根据引用标识符查找元素"""
        def search_recursive(items: List[SnapshotElement]):
            for item in items:
                if item.ref == ref:
                    return item
                
                if item.children:
                    result = search_recursive(item.children)
                    if result:
                        return result
            
            return None
        
        return search_recursive(self.data)
    
    def find_interactive_elements(self) -> Dict[str, List[SnapshotElement]]:
        """查找所有可交互元素（按钮、链接、输入框等）"""
        interactive_roles = ['button', 'link', 'textbox', 'checkbox', 'radio', 'combobox', 'slider']
        results = {}
        
        for role in interactive_roles:
            results[role] = self.find_by_role(role)
        
        return results
    
    def get_element_path(self, ref: str) -> List[SnapshotElement]:
        """获取元素在树中的路径"""
        def search_recursive(items: List[SnapshotElement], current_path: List[SnapshotElement]):
            for item in items:
                new_path = current_path + [item]
                
                if item.ref == ref:
                    return new_path
                
                if item.children:
                    result = search_recursive(item.children, new_path)
                    if result:
                        return result
            
            return None
        
        result = search_recursive(self.data, [])
        return result if result else []
    
    def count_elements(self) -> Dict[str, int]:
        """统计各类型元素的数量"""
        counts = {}
        
        def count_recursive(items: List[SnapshotElement]):
            for item in items:
                role = item.role
                counts[role] = counts.get(role, 0) + 1
                
                if item.children:
                    count_recursive(item.children)
        
        count_recursive(self.data)
        return counts
    
    def extract_all_refs(self) -> List[str]:
        """提取所有引用标识符"""
        refs = []
        
        def extract_recursive(items: List[SnapshotElement]):
            for item in items:
                refs.append(item.ref)
                
                if item.children:
                    extract_recursive(item.children)
        
        extract_recursive(self.data)
        return refs
    
    def find_elements_with_text(self, text: str, case_sensitive: bool = False) -> List[Dict]:
        """查找包含指定文本的元素"""
        results = []
        search_text = text if case_sensitive else text.lower()
        
        def search_recursive(items):
            for item in items:
                if 'name' in item:
                    item_text = item['name'] if case_sensitive else item['name'].lower()
                    if search_text in item_text:
                        results.append(item)
                
                if 'children' in item:
                    search_recursive(item['children'])
        
        search_recursive(self.data)
        return results
    
    def find_by_regex(self, pattern: str, field: str = 'name', case_sensitive: bool = False) -> List[Dict]:
        """
        使用正则表达式查找元素
        
        Args:
            pattern: 正则表达式模式
            field: 要搜索的字段，默认为 'name'，也可以是 'role' 或 'ref'
            case_sensitive: 是否区分大小写，默认为 False
        
        Returns:
            匹配的元素列表
        """
        results = []
        flags = 0 if case_sensitive else re.IGNORECASE
        
        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            raise ValueError(f"无效的正则表达式: {e}")
        
        def search_recursive(items):
            for item in items:
                if field in item:
                    field_value = item[field]
                    # 确保 field_value 是字符串
                    if not isinstance(field_value, str):
                        field_value = str(field_value)
                    
                    if regex.search(field_value):
                        results.append(item)
                
                if 'children' in item:
                    search_recursive(item['children'])
        
        search_recursive(self.data)
        return results
    
    def find_by_selector(self, selector: str) -> List[Dict]:
        """
        使用 CSS/jQuery 选择器语法查找元素
        
        支持的选择器：
        - 标签选择器：button, link, textbox（对应 role）
        - ID 选择器：#ref-xxx（对应 ref）
        - 属性选择器：[name="xxx"], [role="button"], [ref="ref-xxx"]
        - 组合选择器：button[name="搜索"]
        - 后代选择器：parent child（空格分隔）
        - 直接子元素：parent > child
        
        Args:
            selector: CSS/jQuery 选择器字符串
        
        Returns:
            匹配的元素列表
        """
        # 解析选择器
        parts = self._parse_selector(selector)
        if not parts:
            return []
        
        results = []
        
        def match_element(item: Dict, selectors: List[Dict]) -> bool:
            """检查元素是否匹配选择器"""
            if not selectors:
                return True
            
            sel = selectors[0]
            matched = True
            
            # 检查标签选择器（role）
            if 'tag' in sel:
                if item.get('role') != sel['tag']:
                    matched = False
            
            # 检查 ID 选择器（ref）
            if 'id' in sel:
                if item.get('ref') != sel['id']:
                    matched = False
            
            # 检查属性选择器
            if 'attrs' in sel:
                for attr_name, attr_value in sel['attrs'].items():
                    item_value = item.get(attr_name)
                    if not isinstance(item_value, str):
                        item_value = str(item_value) if item_value is not None else ''
                    
                    # 支持精确匹配和包含匹配
                    if attr_value.startswith('*') and attr_value.endswith('*'):
                        pattern = attr_value[1:-1]
                        if pattern not in item_value:
                            matched = False
                    elif attr_value.startswith('^'):
                        pattern = attr_value[1:]
                        if not item_value.startswith(pattern):
                            matched = False
                    elif attr_value.endswith('$'):
                        pattern = attr_value[:-1]
                        if not item_value.endswith(pattern):
                            matched = False
                    else:
                        if item_value != attr_value:
                            matched = False
            
            if not matched:
                return False
            
            if len(selectors) == 1:
                return True
            
            if 'combinator' in sel:
                if sel['combinator'] == ' ':
                    if 'children' in item:
                        for child in item['children']:
                            if self._match_descendant(child, selectors[1:]):
                                return True
                    return False
                elif sel['combinator'] == '>':
                    if 'children' in item:
                        for child in item['children']:
                            if match_element(child, selectors[1:]):
                                return True
                    return False
            
            return False
        
        def search_recursive(items):
            for item in items:
                if match_element(item, parts):
                    results.append(item)
                
                if 'children' in item:
                    search_recursive(item['children'])
        
        search_recursive(self.data)
        return results
    
    def _match_descendant(self, item: Dict, selectors: List[Dict]) -> bool:
        """在后代元素中查找匹配（辅助方法）"""
        def match_element(item: Dict, selectors: List[Dict]) -> bool:
            """检查元素是否匹配选择器"""
            if not selectors:
                return True
            
            sel = selectors[0]
            matched = True
            
            if 'tag' in sel:
                if item.get('role') != sel['tag']:
                    matched = False
            
            if 'id' in sel:
                if item.get('ref') != sel['id']:
                    matched = False
            
            if 'attrs' in sel:
                for attr_name, attr_value in sel['attrs'].items():
                    item_value = item.get(attr_name)
                    if not isinstance(item_value, str):
                        item_value = str(item_value) if item_value is not None else ''
                    
                    if attr_value.startswith('*') and attr_value.endswith('*'):
                        pattern = attr_value[1:-1]
                        if pattern not in item_value:
                            matched = False
                    elif attr_value.startswith('^'):
                        pattern = attr_value[1:]
                        if not item_value.startswith(pattern):
                            matched = False
                    elif attr_value.endswith('$'):
                        pattern = attr_value[:-1]
                        if not item_value.endswith(pattern):
                            matched = False
                    else:
                        if item_value != attr_value:
                            matched = False
            
            if not matched:
                return False
            
            if len(selectors) == 1:
                return True
            
            if 'combinator' in sel:
                if sel['combinator'] == '>':
                    if 'children' in item:
                        for child in item['children']:
                            if match_element(child, selectors[1:]):
                                return True
                    return False
            
            return False
        
        if match_element(item, selectors):
            return True
        
        if 'children' in item:
            for child in item['children']:
                if self._match_descendant(child, selectors):
                    return True
        
        return False
    
    def _parse_selector(self, selector: str) -> List[Dict]:
        """解析 CSS 选择器字符串"""
        if not selector or not selector.strip():
            return []
        
        selector = selector.strip()
        parts = []
        
        pattern = r'([^\s>]+|\s+|\s*>\s*)'
        matches = re.findall(pattern, selector)
        
        i = 0
        while i < len(matches):
            token = matches[i].strip()
            if not token:
                i += 1
                continue
            
            if token == '>':
                if parts:
                    parts[-1]['combinator'] = '>'
                i += 1
                continue
            elif i > 0 and matches[i-1].strip() == '' and parts:
                parts[-1]['combinator'] = ' '
            
            part = {}
            
            combined_match = re.match(r'^([a-z][a-z0-9]*)(\[.+\])$', token, re.IGNORECASE)
            if combined_match:
                part['tag'] = combined_match.group(1)
                attr_str = combined_match.group(2)[1:-1]
                self._parse_attributes(part, attr_str)
            elif token.startswith('#'):
                part['id'] = token[1:]
            elif token.startswith('[') and token.endswith(']'):
                attr_str = token[1:-1]
                self._parse_attributes(part, attr_str)
            elif re.match(r'^[a-z][a-z0-9]*$', token, re.IGNORECASE):
                part['tag'] = token
            
            if part:
                parts.append(part)
            
            i += 1
        
        return parts
    
    def _parse_attributes(self, part: Dict, attr_str: str):
        """解析属性选择器字符串"""
        match = re.match(r'^(\w+)([*^$]?)=["\']?([^"\']*)["\']?$', attr_str)
        if match:
            attr_name = match.group(1)
            operator = match.group(2) or ''
            attr_value = match.group(3)
            
            if 'attrs' not in part:
                part['attrs'] = {}
            
            if operator == '*':
                part['attrs'][attr_name] = f'*{attr_value}*'
            elif operator == '^':
                part['attrs'][attr_name] = f'^{attr_value}'
            elif operator == '$':
                part['attrs'][attr_name] = f'{attr_value}$'
            else:
                part['attrs'][attr_name] = attr_value
    
    def print_element(self, element: Union[SnapshotElement, Dict], indent: int = 0):
        """格式化打印元素信息"""
        prefix = "  " * indent
        
        # 支持 pydantic 模型和字典（向后兼容）
        if isinstance(element, SnapshotElement):
            role = element.role
            ref = element.ref
            name = element.name or ''
            has_children = element.children is not None and len(element.children) > 0
            children_count = len(element.children) if element.children else 0
        else:
            # 字典格式（向后兼容）
            role = element.get('role', 'unknown')
            ref = element.get('ref', 'N/A')
            name = element.get('name', '')
            has_children = 'children' in element
            children_count = len(element['children']) if has_children else 0
        
        print(f"{prefix}role: {role}")
        print(f"{prefix}ref: {ref}")
        if name:
            print(f"{prefix}name: {name}")
        if has_children:
            print(f"{prefix}children: {children_count} items")
    
    def to_markdown(self, output_file: Optional[str] = None, include_ref: bool = True, max_depth: Optional[int] = None) -> str:
        """
        Convert snapshot data to Markdown format (coherent document)
        
        Args:
            output_file: Optional output file path. If provided, saves to file.
            include_ref: Whether to include ref identifiers in output
            max_depth: Maximum depth to render (None = no limit)
        
        Returns:
            Markdown string representation of the snapshot as a coherent document
        """
        from datetime import datetime
        
        lines = []
        
        # Document header
        lines.append("# Accessibility Snapshot Documentation")
        lines.append("")
        lines.append(f"**Source File:** `{self.file_path.name}`")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Document introduction
        lines.append("## Overview")
        lines.append("")
        stats = self.count_elements()
        total = sum(stats.values())
        lines.append(f"This document contains the accessibility tree structure from the snapshot file. ")
        lines.append(f"The snapshot contains **{total}** accessibility elements organized in a hierarchical tree structure.")
        lines.append("")
        
        # Statistics section
        lines.append("## Statistics")
        lines.append("")
        lines.append("### Element Count by Role")
        lines.append("")
        lines.append("| Role | Count | Percentage |")
        lines.append("|------|-------|------------|")
        for role, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total * 100) if total > 0 else 0
            lines.append(f"| `{role}` | {count} | {percentage:.1f}% |")
        lines.append("")
        lines.append(f"**Total Elements:** {total}")
        lines.append("")
        
        # Interactive elements summary
        interactive = self.find_interactive_elements()
        interactive_total = sum(len(items) for items in interactive.values())
        if interactive_total > 0:
            lines.append("### Interactive Elements")
            lines.append("")
            lines.append(f"The snapshot contains **{interactive_total}** interactive elements:")
            lines.append("")
            for role, items in sorted(interactive.items(), key=lambda x: len(x[1]), reverse=True):
                if items:
                    lines.append(f"- **{role}**: {len(items)} elements")
            lines.append("")
        
        lines.append("---")
        lines.append("")
        
        # Accessibility tree section - collect all elements with names
        lines.append("## Accessibility Tree Structure")
        lines.append("")
        lines.append("The following section lists all elements with names from the accessibility tree. ")
        lines.append("Links are formatted using Markdown link syntax.")
        lines.append("")
        
        # Helper function to extract name from element (including from children)
        def get_element_display_name(elem: SnapshotElement) -> Optional[str]:
            """Get display name from element or its children"""
            if elem.name:
                return elem.name
            
            # For listitem and tab, try to get name from first child link or button
            if elem.role in ('listitem', 'tab') and elem.children:
                for child in elem.children:
                    if child.name and child.role in ('link', 'button', 'heading'):
                        return child.name
                    # Recursively check nested children
                    if child.children:
                        for nested in child.children:
                            if nested.name and nested.role in ('link', 'button', 'heading'):
                                return nested.name
            
            return None
        
        # Helper function to get link info from listitem/tab
        def get_link_from_element(elem: SnapshotElement) -> Tuple[Optional[str], Optional[str]]:
            """Get link ref and name from element or its children"""
            if elem.role in ('listitem', 'tab') and elem.children:
                for child in elem.children:
                    if child.role == 'link' and child.name:
                        return (child.ref, child.name)
                    # Recursively check nested children
                    if child.children:
                        for nested in child.children:
                            if nested.role == 'link' and nested.name:
                                return (nested.ref, nested.name)
            return (None, None)
        
        # Collect all elements with names (including listitem/tab that get names from children)
        elements_with_names = []
        # Track listitem/tab children to skip them (avoid duplicate rendering)
        listitem_tab_refs = set()
        
        def collect_elements_with_names(element: SnapshotElement, depth: int = 0, parent_is_listitem_tab: bool = False):
            """Recursively collect all elements that have names or can derive names"""
            if max_depth is not None and depth > max_depth:
                return
            
            # For listitem and tab, check if they have name or can get name from children
            if element.role in ('listitem', 'tab'):
                display_name = get_element_display_name(element)
                if display_name:
                    elements_with_names.append((element, depth))
                    # Mark all children of this listitem/tab to skip them
                    if element.children:
                        for child in element.children:
                            listitem_tab_refs.add(child.ref)
                            # Also mark nested children
                            if child.children:
                                for nested in child.children:
                                    listitem_tab_refs.add(nested.ref)
                # Don't process children for listitem/tab to avoid duplicates
                return
            
            # For list elements, only collect if they have their own name
            if element.role == 'list':
                if element.name:
                    elements_with_names.append((element, depth))
                # Process children to collect listitems
                if element.children and (max_depth is None or depth < max_depth):
                    for child in element.children:
                        collect_elements_with_names(child, depth + 1, parent_is_listitem_tab)
                return
            
            # Skip elements that are children of listitem/tab (to avoid duplicates)
            if element.ref in listitem_tab_refs:
                # Still process children in case they are not duplicates
                if element.children and (max_depth is None or depth < max_depth):
                    for child in element.children:
                        collect_elements_with_names(child, depth + 1, parent_is_listitem_tab)
                return
            
            # For other elements, collect if they have names
            if element.name:
                elements_with_names.append((element, depth))
            
            # Recursively process children
            if element.children and (max_depth is None or depth < max_depth):
                for child in element.children:
                    collect_elements_with_names(child, depth + 1, parent_is_listitem_tab)
        
        # Collect all elements with names from the tree
        for element in self.data:
            collect_elements_with_names(element, 0, False)
        
        # Render elements with names
        if elements_with_names:
            for element, depth in elements_with_names:
                # Skip elements that are children of listitem/tab (already rendered as part of listitem/tab)
                if element.ref in listitem_tab_refs:
                    continue
                
                if element.role == 'listitem':
                    # For listitem, check if it contains a link
                    link_ref, link_name = get_link_from_element(element)
                    if link_ref and link_name:
                        # Use Markdown link syntax in list item
                        lines.append(f"- [{link_name}]({link_ref})")
                    else:
                        # Use listitem's own name (or name from children)
                        display_name = get_element_display_name(element)
                        if display_name:
                            if include_ref:
                                lines.append(f"- {display_name} (`{element.ref}`)")
                            else:
                                lines.append(f"- {display_name}")
                    lines.append("")
                elif element.role == 'tab':
                    # For tab, check if it contains a link
                    link_ref, link_name = get_link_from_element(element)
                    if link_ref and link_name:
                        # Use Markdown link syntax in list item
                        lines.append(f"- [{link_name}]({link_ref})")
                    else:
                        # Use tab's own name
                        display_name = get_element_display_name(element)
                        if display_name:
                            if include_ref:
                                lines.append(f"- {display_name} (`{element.ref}`)")
                            else:
                                lines.append(f"- {display_name}")
                    lines.append("")
                elif element.role == 'link':
                    # Use Markdown link syntax for links
                    if include_ref:
                        lines.append(f"[{element.name}]({element.ref})")
                    else:
                        lines.append(element.name)
                    lines.append("")
                elif element.role == 'heading':
                    # Use heading syntax for headings
                    heading_level = min(depth + 3, 6)  # Start from ###
                    lines.append(f"{'#' * heading_level} {element.name}")
                    lines.append("")
                elif element.role == 'button':
                    # Format buttons
                    if include_ref:
                        lines.append(f"**{element.name}** `{element.ref}`")
                    else:
                        lines.append(f"**{element.name}**")
                    lines.append("")
                elif element.role == 'list':
                    # For list elements, just show the name as text (if any)
                    # The actual list items will be rendered separately
                    if include_ref:
                        lines.append(f"{element.name} (`{element.ref}`)")
                    else:
                        lines.append(element.name)
                    lines.append("")
                else:
                    # Format other elements
                    display_name = get_element_display_name(element) if not element.name else element.name
                    if display_name:
                        if include_ref:
                            lines.append(f"{display_name} (`{element.ref}`)")
                        else:
                            lines.append(display_name)
                        lines.append("")
        else:
            lines.append("*No elements with names found in the accessibility tree.*")
            lines.append("")
        
        # Interactive elements reference section
        if interactive_total > 0:
            lines.append("")
            lines.append("---")
            lines.append("")
            lines.append("## Interactive Elements Reference")
            lines.append("")
            lines.append("This section lists all interactive elements for quick reference. ")
            lines.append("These elements can be interacted with using browser automation tools.")
            lines.append("")
            
            # Helper function to pluralize role names
            def pluralize_role(role: str) -> str:
                """Convert role name to plural form"""
                # Common roles that need special handling
                if role.endswith('box'):
                    return role + 'es'  # textbox -> textboxes, combobox -> comboboxes
                elif role.endswith('x') or role.endswith('ch') or role.endswith('sh'):
                    return role + 'es'  # mix -> mixes, batch -> batches, brush -> brushes
                elif role.endswith('y') and role[-2] not in 'aeiou':
                    return role[:-1] + 'ies'  # city -> cities (but not day -> days)
                elif role.endswith('f'):
                    return role[:-1] + 'ves'  # leaf -> leaves
                elif role.endswith('fe'):
                    return role[:-2] + 'ves'  # knife -> knives
                else:
                    return role + 's'  # button -> buttons, link -> links
            
            for role, items in sorted(interactive.items(), key=lambda x: len(x[1]), reverse=True):
                if items:
                    role_plural = pluralize_role(role)
                    role_display = role_plural.replace('_', ' ').title()
                    lines.append(f"### {role_display} ({len(items)})")
                    lines.append("")
                    lines.append("| Name | Reference |")
                    lines.append("|------|-----------|")
                    for item in items[:50]:  # Limit to first 50 to avoid huge tables
                        name = item.name if item.name else "*No name*"
                        ref = item.ref if include_ref else "*N/A*"
                        # Escape pipe characters in table cells
                        name = name.replace('|', '\\|')
                        lines.append(f"| {name} | `{ref}` |")
                    if len(items) > 50:
                        lines.append(f"| ... {len(items) - 50} more {role_plural.replace('_', ' ')} | |")
                    lines.append("")
        
        # Footer
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Notes")
        lines.append("")
        lines.append("- This document was automatically generated from an accessibility snapshot.")
        lines.append("- Reference identifiers (`ref-*`) are unique identifiers for each element.")
        lines.append("- Interactive elements can be targeted using their reference identifiers in browser automation.")
        if max_depth is not None:
            lines.append(f"- Tree depth is limited to {max_depth} levels for readability.")
        if not include_ref:
            lines.append("- Reference identifiers are excluded from this document.")
        lines.append("")
        
        markdown_content = "\n".join(lines)
        
        # Save to file if specified
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
        
        return markdown_content


def main():
    """命令行工具主函数"""
    if len(sys.argv) < 3:
        print("用法:")
        print("  python query_snapshot.py <文件路径> <命令> [参数]")
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
        print("  convert-to-markdown [输出文件] - 将快照转换为 Markdown 格式")
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
        
        elif command == "convert-to-markdown":
            output_file = sys.argv[3] if len(sys.argv) >= 4 else None
            include_ref = True
            max_depth = None
            
            # Parse optional arguments
            i = 4
            while i < len(sys.argv):
                arg = sys.argv[i]
                if arg == "--no-ref":
                    include_ref = False
                elif arg == "--max-depth" and i + 1 < len(sys.argv):
                    try:
                        max_depth = int(sys.argv[i + 1])
                        i += 1
                    except ValueError:
                        print("警告: --max-depth 参数无效，将忽略", file=sys.stderr)
                i += 1
            
            markdown = query.to_markdown(output_file=output_file, include_ref=include_ref, max_depth=max_depth)
            
            if output_file:
                print(f"已转换为 Markdown 并保存到: {output_file}")
            else:
                print(markdown)
        
        else:
            print(f"未知命令: {command}")
            sys.exit(1)
    
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
