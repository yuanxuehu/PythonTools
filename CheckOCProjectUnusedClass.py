# python3
# Created by TigerHu on 2025/8/25.
# Copyright © 2025 TigerHu. All rights reserved.

# 执行命令行 python3 /Users/TigerHu/Downloads/PythonTools/CheckOCProjectUnusedClass.py --project_path /Users/TigerHu/XcodeProjects/YourCompanyName/YourProjectName/ --macho_path /Users/TigerHu/Library/Developer/Xcode/DerivedData/xxx-fofkvptgsedrxmcavcsqvgzpbjyi/Build/Products/Debug-iphoneos/YourApp.app/YourApp --linkmap_path /Users/TigerHu/Library/Developer/Xcode/DerivedData/xxx-fofkvptgsedrxmcavcsqvgzpbjyi/Build/Intermediates.noindex/xxx.build/Debug-iphoneos/YourApp.build/YourApp-LinkMap-normal-arm64.txt

#打印
#Mach-O分析发现0个未使用类
#代码扫描发现1166个未使用类
#
#[安全建议]
#1. 以下类未被直接引用，但需人工确认：
#   - 通过NSClassFromString动态调用的类
#   - 被Category扩展的系统类（如NSString+Utils）
#2. 使用Xcode全局搜索确认类名是否在字符串中出现
#
#[未使用类清单]
#- AFCompoundResponseSerializer
#- AFHTTPRequestSerializer
#- AFHTTPResponseSerializer
#...

import os
import re
import subprocess
import argparse
from collections import defaultdict

# 配置参数
parser = argparse.ArgumentParser(description='iOS OC工程未使用类检测工具')
parser.add_argument('--project_path', type=str, required=True, help='项目根目录路径')
parser.add_argument('--macho_path', type=str, help='Mach-O文件路径（Release包需配合Linkmap）')
parser.add_argument('--linkmap_path', type=str, help='Linkmap文件路径（Release包解析用）')
parser.add_argument('--ignore_prefix', type=str, default='NS,UI', help='忽略的系统类前缀（逗号分隔）')
args = parser.parse_args()

# 系统类前缀过滤
IGNORE_PREFIXES = tuple(p.strip() for p in args.ignore_prefix.split(','))

def parse_macho_classes():
    """解析Mach-O获取类引用关系[3](@ref)[4](@ref)"""
    class_refs = set()   # 被引用的类
    class_all = set()    # 所有定义的类

    # 1. 获取所有类列表（__objc_classlist段）
    cmd_all = f"otool -v -s __DATA __objc_classlist {args.macho_path}"
    output = subprocess.check_output(cmd_all, shell=True).decode()
    for line in output.splitlines():
        if '0x' in line and '_OBJC_CLASS_$_' in line:
            class_name = line.split('_OBJC_CLASS_$_')[-1].strip()
            if not class_name.startswith(IGNORE_PREFIXES):
                class_all.add(class_name)

    # 2. 获取被引用类列表（__objc_classrefs段）
    cmd_refs = f"otool -v -s __DATA __objc_classrefs {args.macho_path}"
    output = subprocess.check_output(cmd_refs, shell=True).decode()
    for line in output.splitlines():
        if '0x' in line and '_OBJC_CLASS_$_' in line:
            class_name = line.split('_OBJC_CLASS_$_')[-1].strip()
            class_refs.add(class_name)

    # 3. 处理父类未显式引用问题[3](@ref)
    cmd_hierarchy = f"otool -oV {args.macho_path}"
    output = subprocess.check_output(cmd_hierarchy, shell=True).decode()
    super_classes = set()
    for line in output.split('superclass 0x')[1:]:
        addr = line.split()
        # 通过地址反查父类名（需Linkmap支持）
        if args.linkmap_path:
            with open(args.linkmap_path, 'r') as f:
                linkmap = f.read()
                if f'0x{addr} ' in linkmap:
                    cls_line = linkmap.split(f'0x{addr} ')[1].split('\n')
                    super_classes.add(cls_line.split('] ')[-1])

    # 合并直接引用和父类引用
    class_refs |= super_classes
    return class_all - class_refs

def scan_code_references():
    """代码扫描辅助检测[4](@ref)[12](@ref)"""
    used_classes = set()
    class_files = {}

    # 遍历.h/.m文件
    for root, _, files in os.walk(args.project_path):
        if "Pods" in root:  # 排除CocoaPods目录
            continue
        for file in files:
            if not file.endswith(('.h', '.m')):
                continue
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

                # 记录定义的类
                if file.endswith('.h'):
                    matches = re.findall(r'@interface\s+(\w+)', content)
                    for cls in matches:
                        class_files[cls] = path

                # 收集被引用的类
                ref_matches = re.findall(
                    r'#import\s+"(\w+\.h)"|\b\[(\w+)\s+',
                    content
                )
                for imp, cls in ref_matches:
                    used_class = imp.split('.')[0] if imp else cls
                    if not used_class.startswith(IGNORE_PREFIXES):
                        used_classes.add(used_class)

    return set(class_files.keys()) - used_classes

def main():
    unused_classes = set()

    # 优先使用Mach-O分析（更准确）
    if args.macho_path:
        macho_unused = parse_macho_classes()
        unused_classes.update(macho_unused)
        print(f"Mach-O分析发现{len(macho_unused)}个未使用类")

    # 补充代码扫描（覆盖Mach-O无法处理的情况）
    code_unused = scan_code_references()
    unused_classes.update(code_unused)
    print(f"代码扫描发现{len(code_unused)}个未使用类")

    # 输出结果
    print("\n[安全建议]")
    print("1. 以下类未被直接引用，但需人工确认：")
    print("   - 通过NSClassFromString动态调用的类")
    print("   - 被Category扩展的系统类（如NSString+Utils）")
    print("2. 使用Xcode全局搜索确认类名是否在字符串中出现\n")

    print("[未使用类清单]")
    for cls in sorted(unused_classes):
        print(f"- {cls}")

if __name__ == "__main__":
    main()
