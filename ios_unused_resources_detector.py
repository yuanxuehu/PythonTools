#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Created by TigerHu on 2025/10/21.
# Copyright © 2025 TigerHu. All rights reserved.

"""
示例：
python3 /Users/yxh/ios_unused_resources_detector.py /MainProject --images-root /MainResource --code-exts .m
"""

"""
极简版 iOS 无用资源检测脚本
- 资源仅在 --images-root 指定的目录中扫描（默认支持 .png/.svga/.mp3/.mp4，可用 --res-exts 覆盖）
- 代码仅扫描 .m 文件（可用 --code-exts 扩展，例如 .m,.mm）
- 匹配规则：只要资源“基名”在任意代码文件中出现一次，即判定为已使用；命中后对该资源短路，后续不再继续匹配
- 扫描过程中每约 1 秒输出一次扫描进度（已处理文件、百分比、剩余未命中数量、用时）
- PNG 资源名自动归一化（去除 @2x/@3x/~iphone/~ipad 后缀），避免重复统计
"""

import os
import re
import sys
import argparse
from pathlib import Path
from typing import Set, Dict


NORMALIZE_SUFFIX_RE = re.compile(r'(@[23]x|~iphone|~ipad)$', re.IGNORECASE)


def normalize_base_name(stem: str, ext: str) -> str:
	# 仅对 PNG 去除尺寸/平台后缀
	if ext.lower() == '.png':
		return NORMALIZE_SUFFIX_RE.sub('', stem)
	return stem


def collect_resource_names(images_root: Path, res_exts: Set[str]) -> Dict[str, Set[str]]:
	"""返回：扩展名 -> 该类型资源基名集合"""
	if not images_root.exists():
		raise FileNotFoundError(f"images_root not found: {images_root}")
	by_ext: Dict[str, Set[str]] = {}
	res_exts_lower = {e.lower() for e in res_exts}
	for root, dirs, files in os.walk(str(images_root)):
		# 不再跳过任何目录
		for filename in files:
			ext = os.path.splitext(filename)[1].lower()
			if ext not in res_exts_lower:
				continue
			stem, _ = os.path.splitext(filename)
			base = normalize_base_name(stem, ext)
			by_ext.setdefault(ext, set()).add(base)
	return by_ext


def read_text(path: Path) -> str:
	try:
		return path.read_text(encoding='utf-8', errors='ignore')
	except Exception:
		try:
			return path.read_text(encoding='latin-1', errors='ignore')
		except Exception:
			return ''


def find_used_resources(project_root: Path, active_names: Set[str], code_exts: Set[str]) -> Set[str]:
	used: Set[str] = set()
	if not active_names:
		return used
	code_exts_lower = {ext.lower() for ext in code_exts}
	# 预收集待扫描的代码文件，便于进度统计
	code_files = []
	for root, dirs, files in os.walk(str(project_root)):
		# 不再跳过任何目录
		for filename in files:
			suffix = os.path.splitext(filename)[1].lower()
			if suffix in code_exts_lower:
				code_files.append(Path(root) / filename)
	total = len(code_files)
	processed = 0
	last_print = 0.0
	start_ts = __import__('time').time()
	for path in code_files:
		if not active_names:
			break
		content = read_text(path)
		if content:
			newly_found: Set[str] = set()
			for name in active_names:
				if name and name in content:
					newly_found.add(name)
			if newly_found:
				used.update(newly_found)
				active_names.difference_update(newly_found)
		processed += 1
		# 每约 1 秒打印一次进度
		now = __import__('time').time()
		if now - last_print >= 1.0:
			percent = (processed / total * 100.0) if total else 100.0
			remaining = len(active_names)
			elapsed = now - start_ts
			print(f"进度: {processed}/{total} ({percent:.1f}%) | 剩余未命中: {remaining} | 用时: {elapsed:.1f}s")
			last_print = now
	return used


def build_number_suffix_groups(by_ext: Dict[str, Set[str]]):
	"""构建以 _<数字> 结尾的同基名分组：
	返回 (group_base_to_members, member_to_base)
	- 若某个基名下成员数 >=2，则使用该基名作为匹配Key
	"""
	group_base_to_members: Dict[str, Set[str]] = {}
	member_to_base: Dict[str, str] = {}
	pat = re.compile(r'^(.*)_\d+$')
	for ext, names in by_ext.items():
		base_map: Dict[str, Set[str]] = {}
		for n in names:
			m = pat.match(n)
			if m:
				base = m.group(1)
				base_map.setdefault(base, set()).add(n)
		for base, members in base_map.items():
			if len(members) >= 2:
				group_base_to_members.setdefault(base, set()).update(members)
				for mem in members:
					member_to_base[mem] = base
	return group_base_to_members, member_to_base


def main() -> None:
	parser = argparse.ArgumentParser(description='极简 iOS 无用资源检测（按名称匹配）')
	parser.add_argument('project_path', help='项目根目录（用于扫描代码文件）')
	parser.add_argument('--images-root', required=True, help='资源根目录（仅在此目录下收集资源）')
	parser.add_argument('--code-exts', default='.m', help='代码文件扩展名（逗号分隔，默认 .m，例如 .m,.mm）')
	parser.add_argument('--res-exts', default='.png,.svga,.mp3,.mp4', help='资源文件扩展名（逗号分隔，默认 .png,.svga,.mp3,.mp4）')
	args = parser.parse_args()

	project_root = Path(args.project_path)
	images_root = Path(args.images_root)
	code_exts = set(ext.strip().lower() if ext.strip().startswith('.') else f".{ext.strip().lower()}" for ext in args.code_exts.split(','))
	res_exts = set(ext.strip().lower() if ext.strip().startswith('.') else f".{ext.strip().lower()}" for ext in args.res_exts.split(','))

	# 1) 收集资源（按扩展名聚合）
	by_ext = collect_resource_names(images_root, res_exts)
	all_names: Set[str] = set().union(*by_ext.values()) if by_ext else set()
	print(f"在 {images_root} 下发现 {sum(len(v) for v in by_ext.values())} 个资源基名")
	if not all_names:
		print('未发现任何资源，任务结束。')
		sys.exit(0)

	# 1.1) 针对形如 <base>_数字 的资源做分组，若同基名成员数>=2，则以 <base> 作为匹配Key
	group_base_to_members, member_to_base = build_number_suffix_groups(by_ext)
	# 构造用于扫描匹配的名称集合：将需要按基名匹配的成员替换为基名Key
	match_keys: Set[str] = set(all_names)
	if group_base_to_members:
		match_keys.difference_update(member_to_base.keys())
		match_keys.update(group_base_to_members.keys())

	# 2) 扫描代码并按名称命中（命中即短路）
	active_names = set(match_keys)
	used_match_keys = find_used_resources(project_root, active_names, code_exts)
	# 将命中的基名Key展开为其全部成员
	used_names: Set[str] = set()
	for key in used_match_keys:
		if key in group_base_to_members:
			used_names.update(group_base_to_members[key])
		else:
			used_names.add(key)
	unused_names = all_names - used_names

	# 3) 扫描前后对比（按类型汇总）
	print("\n================ 各类型统计（扫描前后对比） ================")
	for ext in sorted(by_ext.keys()):
		total = len(by_ext[ext])
		used_cnt = len(by_ext[ext] & used_names)
		unused_cnt = total - used_cnt
		print(f"{ext:6s} | 总数: {total:5d} | 已用: {used_cnt:5d} | 未用: {unused_cnt:5d}")

	# 4) 未使用清单（按类型分别列举）
	print("\n================ 未使用资源（按类型） ================")
	for ext in sorted(by_ext.keys()):
		unused_list = sorted((by_ext[ext] - used_names))
		print(f"\n-- {ext} 未使用（{len(unused_list)}） --")
		for i, name in enumerate(unused_list, 1):
			print(f"{i:3d}. {name}")

	# 5) 未使用清单（总体）
	print("\n================ 未使用资源基名（总体） ================")
	print(f"Total: {len(all_names)} | Used: {len(used_names)} | Unused: {len(unused_names)}")
	for i, name in enumerate(sorted(unused_names), 1):
		print(f"{i:3d}. {name}")

if __name__ == '__main__':
	main()
