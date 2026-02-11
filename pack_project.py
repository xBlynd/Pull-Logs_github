#!/usr/bin/env python3
"""
WRAITH - Project Source Exporter
==================================

Part of the WRAITH toolkit for Git & GitHub documentation.

Exports entire project source code into dual formats:
- Human-readable with navigation and organization
- AI-optimized with flat, parseable structure

GitHub: https://github.com/xBlynd/wraith
Author: Ian Martin (@xBlynd) - xsvStudio, LLC
License: MIT

Usage:
    python pack_project.py

Outputs:
    - PROJECT_HUMAN_READABLE.md
    - PROJECT_AI_OPTIMIZED.md
"""

import os
import ast
import time
from pathlib import Path


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
OUTPUT_HUMAN = "PROJECT_HUMAN_READABLE.md"
OUTPUT_AI = "PROJECT_AI_OPTIMIZED.md"
IGNORE_DIRS = {'.git', '__pycache__', 'venv', 'env', '.idea', '.vscode', 'dist', 'build', 'node_modules', 'loot'}
IGNORE_FILES = {'.DS_Store', 'Thumbs.db', 'package-lock.json', OUTPUT_HUMAN, OUTPUT_AI, os.path.basename(__file__)}
ALLOWED_EXTENSIONS = {'.py', '.md', '.json', '.bat', '.sh', '.txt', '.yml', '.yaml', '.ini', '.cfg', '.toml'}

def is_allowed(filename):
    return any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS)

def get_file_info(filepath):
    """Extract metadata and symbols from files."""
    info = {
        'size': os.path.getsize(filepath),
        'lines': 0,
        'symbols': []
    }
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            info['lines'] = len(content.splitlines())
            
            # Extract Python symbols
            if filepath.endswith('.py'):
                try:
                    tree = ast.parse(content, filename=filepath)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            methods = [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
                            info['symbols'].append({
                                'type': 'class',
                                'name': node.name,
                                'methods': methods,
                                'line': node.lineno
                            })
                        elif isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                            info['symbols'].append({
                                'type': 'function',
                                'name': node.name,
                                'line': node.lineno
                            })
                except:
                    pass
    except:
        pass
    
    return info

def generate_human_readable(startpath):
    """Generate a human-friendly navigation document."""
    output = []
    project_name = os.path.basename(os.path.abspath(startpath))
    
    # Header with metadata
    output.append(f"# 📦 {project_name} - Project Documentation")
    output.append(f"\n**Generated:** {time.strftime('%B %d, %Y at %I:%M %p')}")
    output.append(f"**Location:** `{os.path.abspath(startpath)}`\n")
    output.append("---\n")
    
    # Table of Contents
    output.append("## 📑 Table of Contents\n")
    output.append("1. [Project Structure](#project-structure)")
    output.append("2. [Python Modules](#python-modules)")
    output.append("3. [Configuration Files](#configuration-files)")
    output.append("4. [Documentation Files](#documentation-files)")
    output.append("5. [Complete Source Code](#complete-source-code)\n")
    output.append("---\n")
    
    # Organize files by type
    python_files = []
    config_files = []
    doc_files = []
    other_files = []
    
    for root, dirs, files in os.walk(startpath):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for f in files:
            if f in IGNORE_FILES or not is_allowed(f):
                continue
            
            filepath = os.path.join(root, f)
            relpath = os.path.relpath(filepath, startpath).replace("\\", "/")
            info = get_file_info(filepath)
            
            file_data = {'path': relpath, 'info': info, 'fullpath': filepath}
            
            if f.endswith('.py'):
                python_files.append(file_data)
            elif f.endswith(('.json', '.yml', '.yaml', '.ini', '.cfg', '.toml')):
                config_files.append(file_data)
            elif f.endswith('.md'):
                doc_files.append(file_data)
            else:
                other_files.append(file_data)
    
    # 1. PROJECT STRUCTURE (Visual Tree)
    output.append("## 🗂️ Project Structure\n")
    output.append("```")
    for root, dirs, files in os.walk(startpath):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        level = root.replace(startpath, '').count(os.sep)
        indent = '│   ' * level
        folder_name = os.path.basename(root) if level > 0 else project_name
        output.append(f"{indent}├── 📁 {folder_name}/")
        
        subindent = '│   ' * (level + 1)
        for f in sorted(files):
            if f in IGNORE_FILES or not is_allowed(f):
                continue
            output.append(f"{subindent}├── 📄 {f}")
    
    output.append("```\n")
    
    # 2. PYTHON MODULES (with symbols)
    if python_files:
        output.append("## 🐍 Python Modules\n")
        for file_data in sorted(python_files, key=lambda x: x['path']):
            output.append(f"### `{file_data['path']}`")
            output.append(f"- **Lines:** {file_data['info']['lines']}")
            output.append(f"- **Size:** {file_data['info']['size']:,} bytes\n")
            
            if file_data['info']['symbols']:
                output.append("**Symbols:**\n")
                for symbol in file_data['info']['symbols']:
                    if symbol['type'] == 'class':
                        output.append(f"- 🔷 **Class** `{symbol['name']}` (line {symbol['line']})")
                        if symbol['methods']:
                            for method in symbol['methods'][:5]:  # Limit to first 5 methods
                                output.append(f"  - `{method}()`")
                            if len(symbol['methods']) > 5:
                                output.append(f"  - *...and {len(symbol['methods']) - 5} more methods*")
                    else:
                        output.append(f"- 🔹 **Function** `{symbol['name']}()` (line {symbol['line']})")
                output.append("")
    
    # 3. CONFIGURATION FILES
    if config_files:
        output.append("## ⚙️ Configuration Files\n")
        for file_data in sorted(config_files, key=lambda x: x['path']):
            output.append(f"- `{file_data['path']}` ({file_data['info']['lines']} lines)")
        output.append("")
    
    # 4. DOCUMENTATION FILES
    if doc_files:
        output.append("## 📖 Documentation Files\n")
        for file_data in sorted(doc_files, key=lambda x: x['path']):
            output.append(f"- `{file_data['path']}` ({file_data['info']['lines']} lines)")
        output.append("")
    
    output.append("---\n")
    
    # 5. COMPLETE SOURCE CODE
    output.append("## 📝 Complete Source Code\n")
    
    all_files = python_files + config_files + doc_files + other_files
    
    for file_data in sorted(all_files, key=lambda x: x['path']):
        output.append(f"\n### 📄 {file_data['path']}")
        output.append(f"**Location:** `{file_data['path']}`  |  **Lines:** {file_data['info']['lines']}  |  **Size:** {file_data['info']['size']:,} bytes\n")
        
        ext = file_data['path'].split('.')[-1]
        output.append(f"```{ext}")
        
        try:
            with open(file_data['fullpath'], 'r', encoding='utf-8', errors='ignore') as f:
                output.append(f.read())
        except Exception as e:
            output.append(f"ERROR READING FILE: {e}")
        
        output.append("```\n")
        output.append("---\n")
    
    return "\n".join(output)

def generate_ai_optimized(startpath):
    """Generate AI-optimized flat structure with clear delimiters."""
    output = []
    project_name = os.path.basename(os.path.abspath(startpath))
    
    # Structured header for AI parsing
    output.append("# AI_OPTIMIZED_PROJECT_DUMP")
    output.append(f"PROJECT_NAME: {project_name}")
    output.append(f"GENERATION_TIMESTAMP: {time.strftime('%Y-%m-%d_%H:%M:%S')}")
    output.append(f"ROOT_PATH: {os.path.abspath(startpath)}")
    output.append("")
    
    # File inventory (for quick reference)
    output.append("FILE_INVENTORY_START")
    file_list = []
    
    for root, dirs, files in os.walk(startpath):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for f in files:
            if f in IGNORE_FILES or not is_allowed(f):
                continue
            
            filepath = os.path.join(root, f)
            relpath = os.path.relpath(filepath, startpath).replace("\\", "/")
            info = get_file_info(filepath)
            
            file_list.append({
                'path': relpath,
                'info': info,
                'fullpath': filepath
            })
            
            # Compact file listing
            output.append(f"FILE|{relpath}|{info['lines']}|{info['size']}")
    
    output.append("FILE_INVENTORY_END")
    output.append("")
    
    # Python symbol index (flat list for AI)
    output.append("SYMBOL_INDEX_START")
    for file_data in file_list:
        if file_data['path'].endswith('.py') and file_data['info']['symbols']:
            for symbol in file_data['info']['symbols']:
                if symbol['type'] == 'class':
                    output.append(f"CLASS|{file_data['path']}|{symbol['name']}|line_{symbol['line']}")
                    for method in symbol.get('methods', []):
                        output.append(f"METHOD|{file_data['path']}|{symbol['name']}.{method}")
                else:
                    output.append(f"FUNCTION|{file_data['path']}|{symbol['name']}|line_{symbol['line']}")
    output.append("SYMBOL_INDEX_END")
    output.append("")
    
    # Full content dump with clear boundaries
    output.append("CONTENT_SECTION_START")
    output.append("")
    
    for file_data in sorted(file_list, key=lambda x: x['path']):
        # AI-friendly delimiter
        output.append(f"FILE_START|{file_data['path']}")
        output.append(f"METADATA|lines:{file_data['info']['lines']}|bytes:{file_data['info']['size']}")
        
        ext = file_data['path'].split('.')[-1]
        output.append(f"LANGUAGE|{ext}")
        output.append("CONTENT_START")
        
        try:
            with open(file_data['fullpath'], 'r', encoding='utf-8', errors='ignore') as f:
                output.append(f.read())
        except Exception as e:
            output.append(f"ERROR_READING_FILE: {e}")
        
        output.append("CONTENT_END")
        output.append(f"FILE_END|{file_data['path']}")
        output.append("")
    
    output.append("CONTENT_SECTION_END")
    
    return "\n".join(output)

if __name__ == "__main__":
    print("🔨 Generating dual-format project documentation...")
    cwd = os.getcwd()
    
    # Generate human-readable version
    print("📘 Creating human-readable version...")
    human_content = generate_human_readable(cwd)
    with open(OUTPUT_HUMAN, 'w', encoding='utf-8') as f:
        f.write(human_content)
    print(f"   ✅ Saved: {OUTPUT_HUMAN}")
    
    # Generate AI-optimized version
    print("🤖 Creating AI-optimized version...")
    ai_content = generate_ai_optimized(cwd)
    with open(OUTPUT_AI, 'w', encoding='utf-8') as f:
        f.write(ai_content)
    print(f"   ✅ Saved: {OUTPUT_AI}")
    
    print("\n✨ Done! Two versions created:")
    print(f"   • {OUTPUT_HUMAN} - Browse and navigate")
    print(f"   • {OUTPUT_AI} - Upload to Gemini/AI tools")
