"""
MCP Server Interface
Provides snapshot query functionality through Model Context Protocol
"""

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Try importing MCP SDK, support multiple possible import paths
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    try:
        # Try alternative import path
        from mcp import Server
        from mcp.server.stdio import stdio_server
        from mcp.types import Tool, TextContent
    except ImportError:
        # If MCP SDK is not installed, provide friendly error message
        print("Error: MCP SDK is required. Run: pip install mcp", file=sys.stderr)
        print("Or: pip install @modelcontextprotocol/server-sdk-python", file=sys.stderr)
        sys.exit(1)

from .query import SnapshotQuery
from .models import SnapshotElement
from typing import Union


# 创建 MCP 服务器实例
server = Server("snapshot-query")


@server.list_tools()
async def list_tools() -> List[Tool]:
    """List all available tools"""
    return [
        Tool(
            name="find_by_name",
            description="Find elements by name (fuzzy matching)",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to snapshot log file"
                    },
                    "name": {
                        "type": "string",
                        "description": "Element name to search for"
                    },
                    "exact": {
                        "type": "boolean",
                        "description": "Whether to use exact matching, default is false (fuzzy matching)",
                        "default": False
                    }
                },
                "required": ["file_path", "name"]
            }
        ),
        Tool(
            name="find_by_name_bm25",
            description="Find elements by name using BM25 algorithm (ranked by relevance)",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to snapshot log file"
                    },
                    "name": {
                        "type": "string",
                        "description": "Element name to search for"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Return top k most relevant results, return all if not provided",
                        "minimum": 1
                    }
                },
                "required": ["file_path", "name"]
            }
        ),
        Tool(
            name="find_by_role",
            description="Find elements by role type (e.g., button, link, textbox, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to snapshot log file"
                    },
                    "role": {
                        "type": "string",
                        "description": "Element role (button, link, textbox, checkbox, etc.)"
                    }
                },
                "required": ["file_path", "role"]
            }
        ),
        Tool(
            name="find_by_ref",
            description="Find element by reference identifier",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to snapshot log file"
                    },
                    "ref": {
                        "type": "string",
                        "description": "Element reference identifier (e.g., ref-xxxxx)"
                    }
                },
                "required": ["file_path", "ref"]
            }
        ),
        Tool(
            name="find_by_text",
            description="Find elements containing specified text",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to snapshot log file"
                    },
                    "text": {
                        "type": "string",
                        "description": "Text content to search for"
                    },
                    "case_sensitive": {
                        "type": "boolean",
                        "description": "Whether to be case sensitive, default is false",
                        "default": False
                    }
                },
                "required": ["file_path", "text"]
            }
        ),
        Tool(
            name="find_by_regex",
            description="Find elements using regular expressions (grep syntax)",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to snapshot log file"
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Regular expression pattern (supports grep syntax)"
                    },
                    "field": {
                        "type": "string",
                        "description": "Field to search: 'name' (default), 'role', or 'ref'",
                        "enum": ["name", "role", "ref"],
                        "default": "name"
                    },
                    "case_sensitive": {
                        "type": "boolean",
                        "description": "Whether to be case sensitive, default is false",
                        "default": False
                    }
                },
                "required": ["file_path", "pattern"]
            }
        ),
        Tool(
            name="find_by_selector",
            description="Find elements using CSS/jQuery selector syntax",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to snapshot log file"
                    },
                    "selector": {
                        "type": "string",
                        "description": "CSS/jQuery selector (e.g., button, #ref-xxx, button[name='search'])"
                    }
                },
                "required": ["file_path", "selector"]
            }
        ),
        Tool(
            name="find_interactive_elements",
            description="Find all interactive elements (buttons, links, input boxes, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to snapshot log file"
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="count_elements",
            description="Count elements by type",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to snapshot log file"
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="get_element_path",
            description="Get element path in tree",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to snapshot log file"
                    },
                    "ref": {
                        "type": "string",
                        "description": "Element reference identifier"
                    }
                },
                "required": ["file_path", "ref"]
            }
        ),
        Tool(
            name="extract_all_refs",
            description="Extract all reference identifiers from snapshot file",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to snapshot log file"
                    }
                },
                "required": ["file_path"]
            }
        )
    ]


def format_element(element: Union[SnapshotElement, Dict[str, Any]]) -> str:
    """Format element information as string"""
    lines = []
    
    # 支持 pydantic 模型和字典
    if isinstance(element, SnapshotElement):
        role = element.role
        ref = element.ref
        name = element.name or ''
        has_children = element.children is not None and len(element.children) > 0
        children_count = len(element.children) if element.children else 0
    else:
        role = element.get('role', 'unknown')
        ref = element.get('ref', 'N/A')
        name = element.get('name', '')
        has_children = 'children' in element
        children_count = len(element['children']) if has_children else 0
    
    lines.append(f"role: {role}")
    lines.append(f"ref: {ref}")
    if name:
        lines.append(f"name: {name}")
    if has_children:
        lines.append(f"children: {children_count} items")
    
    return "\n".join(lines)


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls"""
    file_path = arguments.get("file_path")
    
    if not file_path:
        return [TextContent(
            type="text",
            text="Error: file_path parameter is required"
        )]
    
    try:
        query = SnapshotQuery(file_path)
        result_text = ""
        
        if name == "find_by_name":
            name_param = arguments.get("name")
            exact = arguments.get("exact", False)
            if not name_param:
                return [TextContent(type="text", text="Error: name parameter is required")]
            
            results = query.find_by_name(name_param, exact=exact)
            result_text = f"Found {len(results)} matching elements:\n\n"
            for item in results:
                result_text += format_element(item) + "\n\n"
        
        elif name == "find_by_name_bm25":
            name_param = arguments.get("name")
            top_k = arguments.get("top_k")
            if not name_param:
                return [TextContent(type="text", text="Error: name parameter is required")]
            
            results = query.find_by_name_bm25(name_param, top_k=top_k)
            result_text = f"Found {len(results)} relevant elements (ranked by relevance):\n\n"
            for item in results:
                result_text += format_element(item) + "\n\n"
        
        elif name == "find_by_role":
            role = arguments.get("role")
            if not role:
                return [TextContent(type="text", text="Error: role parameter is required")]
            
            results = query.find_by_role(role)
            result_text = f"Found {len(results)} {role} elements:\n\n"
            for item in results[:20]:  # Limit output
                result_text += format_element(item) + "\n\n"
            if len(results) > 20:
                result_text += f"... {len(results) - 20} more elements not shown\n"
        
        elif name == "find_by_ref":
            ref = arguments.get("ref")
            if not ref:
                return [TextContent(type="text", text="Error: ref parameter is required")]
            
            result = query.find_by_ref(ref)
            if result:
                result_text = "Found element:\n\n" + format_element(result)
            else:
                result_text = "No matching element found"
        
        elif name == "find_by_text":
            text = arguments.get("text")
            if not text:
                return [TextContent(type="text", text="Error: text parameter is required")]
            
            case_sensitive = arguments.get("case_sensitive", False)
            results = query.find_elements_with_text(text, case_sensitive=case_sensitive)
            result_text = f"Found {len(results)} elements containing text:\n\n"
            for item in results[:20]:  # Limit output
                result_text += format_element(item) + "\n\n"
            if len(results) > 20:
                result_text += f"... {len(results) - 20} more elements not shown\n"
        
        elif name == "find_by_regex":
            pattern = arguments.get("pattern")
            field = arguments.get("field", "name")
            case_sensitive = arguments.get("case_sensitive", False)
            
            if not pattern:
                return [TextContent(type="text", text="Error: pattern parameter is required")]
            
            if field not in ["name", "role", "ref"]:
                return [TextContent(type="text", text=f"Error: field must be 'name', 'role', or 'ref', got: {field}")]
            
            try:
                results = query.find_by_regex(pattern, field=field, case_sensitive=case_sensitive)
                result_text = f"Found {len(results)} elements matching regex '{pattern}' (field: {field}):\n\n"
                for item in results[:20]:  # Limit output
                    result_text += format_element(item) + "\n\n"
                if len(results) > 20:
                    result_text += f"... {len(results) - 20} more elements not shown\n"
            except ValueError as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "find_by_selector":
            selector = arguments.get("selector")
            
            if not selector:
                return [TextContent(type="text", text="Error: selector parameter is required")]
            
            try:
                results = query.find_by_selector(selector)
                result_text = f"Found {len(results)} elements matching selector '{selector}':\n\n"
                for item in results[:20]:  # Limit output
                    result_text += format_element(item) + "\n\n"
                if len(results) > 20:
                    result_text += f"... {len(results) - 20} more elements not shown\n"
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "find_interactive_elements":
            interactive = query.find_interactive_elements()
            total = sum(len(items) for items in interactive.values())
            result_text = f"Found {total} interactive elements:\n\n"
            for role, items in interactive.items():
                if items:
                    result_text += f"{role}: {len(items)} items\n"
                    for item in items[:5]:  # Show first 5 of each type
                        result_text += "  " + format_element(item).replace("\n", "\n  ") + "\n\n"
                    if len(items) > 5:
                        result_text += f"  ... {len(items) - 5} more {role} elements\n\n"
        
        elif name == "count_elements":
            counts = query.count_elements()
            result_text = "Element statistics:\n"
            for role, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
                result_text += f"  {role}: {count}\n"
        
        elif name == "get_element_path":
            ref = arguments.get("ref")
            if not ref:
                return [TextContent(type="text", text="Error: ref parameter is required")]
            
            path = query.get_element_path(ref)
            if path:
                result_text = "Element path:\n\n"
                for i, element in enumerate(path):
                    result_text += f"Level {i}:\n"
                    result_text += "  " + format_element(element).replace("\n", "\n  ") + "\n\n"
            else:
                result_text = "No matching element found"
        
        elif name == "extract_all_refs":
            refs = query.extract_all_refs()
            result_text = f"Total {len(refs)} reference identifiers:\n"
            for ref in refs[:100]:  # Limit output
                result_text += f"  {ref}\n"
            if len(refs) > 100:
                result_text += f"... {len(refs) - 100} more reference identifiers\n"
        
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
        
        return [TextContent(type="text", text=result_text)]
    
    except FileNotFoundError as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run MCP server"""
    # Run MCP server using stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def run_server():
    """Synchronous wrapper function for command-line entry point"""
    asyncio.run(main())


if __name__ == "__main__":
    run_server()
