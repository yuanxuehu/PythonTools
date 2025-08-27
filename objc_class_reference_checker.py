#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Created by TigerHu on 2025/8/27.
# Copyright © 2025 TigerHu. All rights reserved.

"""
Objective-C .m 文件引用检测（支持多路径忽略）
- 新增功能：通过 `--ignore-paths` 参数指定多个路径前缀（空格分隔）
- 保留原有白名单（-w）功能，支持组合使用
用法：
  python3 objc_class_reference_checker.py /path/to/project [-w PREFIX] [--ignore-paths "PATH1 PATH2"]
"""

import os
import re
import sys
import argparse
from pathlib import Path
from typing import List, Set, Optional, Union

CLASS_REGEXES = [
    re.compile(r"@implementation\s+([A-Za-z_][A-Za-z0-9_]*)"),
    re.compile(r"@interface\s+([A-Za-z_][A-Za-z0-9_]*)"),
]

def list_m_files(root: Path, ignore_paths: Optional[List[str]]) -> List[Path]:
    """递归获取所有 .m 文件路径（排除多个指定前缀的路径）"""
    m_files: List[Path] = []
    for dirpath, dirs, _ in os.walk(str(root)):
        # 动态修改dirs列表实现路径忽略[1](@ref)[6](@ref)
        dirs[:] = [
            d for d in dirs
            if not any(
                str(Path(dirpath) / d).startswith(prefix)
                for prefix in (ignore_paths or [])
            )
        ]
        for fn in os.listdir(dirpath):
            if fn.lower().endswith('.m'):
                full_path = Path(dirpath) / fn
                m_files.append(full_path)
    return m_files

def extract_class_names_from_file(path: Path) -> Set[str]:
    """从单个文件中提取类名集合"""
    try:
        text = path.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        try:
            text = path.read_text(encoding='latin-1', errors='ignore')
        except Exception:
            return set()
    names: Set[str] = set()
    for reg in CLASS_REGEXES:
        for m in reg.finditer(text):
            names.add(m.group(1))
    return names

def filter_class_names(names: Set[str], prefix: Optional[str]) -> Set[str]:
    """根据白名单前缀筛选类名集合"""
    if not prefix:
        return names
    return {name for name in names if name.startswith(prefix)}

def parse_ignore_paths(raw_paths: Optional[str]) -> Optional[List[str]]:
    """解析忽略路径字符串（支持空格分隔的多路径）"""
    if not raw_paths:
        return None
    return [p.strip() for p in raw_paths.split() if p.strip()]

def main() -> None:
    parser = argparse.ArgumentParser(
        description='扫描 .m 文件名与类名匹配，支持白名单和多路径忽略',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('project_path', help='项目根目录')
    parser.add_argument('-w', '--whitelist',
                       help='只匹配指定前缀的类名（如 "ABC" 匹配 ABC 开头的类）',
                       metavar='PREFIX',
                       default=None)
    parser.add_argument('--ignore-paths',
                       help='忽略多个路径前缀的文件（用空格分隔，如 "/libs /tests"）',
                       metavar='PATHS',
                       default=None)
    args = parser.parse_args()

    project_root = Path(args.project_path)
    if not project_root.exists():
        print(f"路径不存在: {project_root}")
        sys.exit(1)

    # 解析多路径忽略参数
    ignore_paths = parse_ignore_paths(args.ignore_paths)

    # 1) 枚举所有 .m 文件（应用多路径忽略规则）
    m_files = list_m_files(project_root, ignore_paths)
    if not m_files:
        print('未找到任何 .m 文件')
        sys.exit(0)

    # 2) 收集全局类名集合
    all_class_names: Set[str] = set()
    for p in m_files:
        all_class_names.update(extract_class_names_from_file(p))

    # 3) 应用白名单筛选类名
    filtered_class_names = filter_class_names(all_class_names, args.whitelist)
    
    # 4) 逐文件比对
    referenced: List[Path] = []
    unreferenced: List[Path] = []
    for p in m_files:
        base = p.stem  # 文件名去扩展
        if base in filtered_class_names:
            referenced.append(p)
        else:
            unreferenced.append(p)

    # 5) 报告
    whitelist_note = f"（白名单前缀: '{args.whitelist}'）" if args.whitelist else ""
    ignore_note = f"（忽略路径: {ignore_paths}）" if ignore_paths else ""
    print("\n=========== 统计 ==========")
    print(f"总 .m 文件: {len(m_files)} {ignore_note}")
    print(f"原始类名总数: {len(all_class_names)}")
    print(f"筛选后类名总数{whitelist_note}: {len(filtered_class_names)}")
    print(f"匹配文件数(被认为引用/有效): {len(referenced)}")
    print(f"未匹配文件数(可疑未引用): {len(unreferenced)}")

    print("\n=========== 可疑未引用的 .m 文件（文件名未匹配类名） ==========")
    for i, p in enumerate(sorted(unreferenced), 1):
        print(f"{i:3d}. {p}")

    print("\n=========== 匹配成功的 .m 文件（文件名匹配类名） ==========")
    for i, p in enumerate(sorted(referenced), 1):
        print(f"{i:3d}. {p}")

if __name__ == '__main__':
    main()
