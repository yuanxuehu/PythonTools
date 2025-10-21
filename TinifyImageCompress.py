# python3
# Created by TigerHu on 2025/6/6.
# Copyright © 2025 TigerHu. All rights reserved.

# 背景：手动压缩一次性最多压缩20张图片且每日压缩次数受限，该脚本适用于批量压缩图片的需求场景

import os
import tinify
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
import time

# ===== 配置区域 =====
API_KEYS = ["xxxxx", "xxxxx", "xxxxx"]  # 替换为实际API Key
INPUT_FOLDER = "/Users/xxx/OriginalImg"  # 输入图片目录
OUTPUT_FOLDER = "/Users/xxx/NewImg"  # 输出图片目录
MAX_WORKERS = 5  # 最大并发线程数
# ====================

class ImageProcessor:
    def __init__(self):
        self.key_index = 0
        self.key_usage = {key: 0 for key in API_KEYS}
        self.failed_files = []

    def get_next_key(self):
        """轮询获取可用API Key"""
        key = API_KEYS[self.key_index]
        self.key_index = (self.key_index + 1) % len(API_KEYS)
        self.key_usage[key] += 1
        return key

    def compress_with_tinify(self, input_path, output_path):
        """使用TinyPNG API压缩图片"""
        key = self.get_next_key()
        try:
            tinify.key = key
            source = tinify.from_file(input_path)
            source.to_file(output_path)
            print(f"✓ 成功压缩: {os.path.basename(input_path)} (使用Key: {key[:6]}...)")
            return True
        except tinify.AccountError:
            print(f"⚠️ Key已超限: {key[:6]}... 自动切换")
            API_KEYS.remove(key)  # 移除无效Key
            if not API_KEYS:
                raise RuntimeError("所有API Key均已耗尽")
            return self.compress_with_tinify(input_path, output_path)  # 重试
        except Exception as e:
            print(f"❌ 压缩失败 [{os.path.basename(input_path)}]: {str(e)}")
            self.failed_files.append(input_path)
            return False

    def process_single_image(self, input_path, output_path):
        """处理单张图片"""
        if not os.path.exists(output_path):
            try:
                return self.compress_with_tinify(input_path, output_path)
            except RuntimeError as e:
                print(f"⛔ 严重错误: {str(e)}")
                return False
        return True

def batch_process():
    """批量处理主函数"""
    processor = ImageProcessor()
    
    # 创建输出目录
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    # 获取图片文件列表
    image_files = [
        f for f in os.listdir(INPUT_FOLDER)
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))
    ]
    
    print(f"🔍 发现 {len(image_files)} 张待处理图片")
    print(f"🔄 使用 {len(API_KEYS)} 个API Key进行轮询")

    # 多线程处理
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for filename in image_files:
            input_path = os.path.join(INPUT_FOLDER, filename)
            output_path = os.path.join(OUTPUT_FOLDER, filename)
            futures.append(executor.submit(
                processor.process_single_image,
                input_path,
                output_path
            ))
        
        # 等待所有任务完成
        for future in futures:
            future.result()

    # 生成报告
    print("\n" + "="*50)
    print(f"✅ 完成处理: {len(image_files) - len(processor.failed_files)}/{len(image_files)}")
    print(f"❌ 失败文件: {len(processor.failed_files)}")
    print("🔑 Key使用统计:")
    for key, count in processor.key_usage.items():
        print(f"  • {key[:8]}...: {count}次")
    
    if processor.failed_files:
        print("\n失败文件列表:")
        for f in processor.failed_files:
            print(f"  - {os.path.basename(f)}")

if __name__ == "__main__":
    start_time = time.time()
    batch_process()
    print(f"\n⏱️ 总耗时: {time.time() - start_time:.2f}秒")
