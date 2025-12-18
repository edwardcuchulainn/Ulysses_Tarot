#!/usr/bin/env python3
"""
压缩塔罗牌图片，保持清晰度的同时减小文件大小
"""
import os
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("正在安装 Pillow 库...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow", "--quiet"])
    from PIL import Image

def compress_image(input_path, output_path, quality=85, max_size=(2000, 3000)):
    """
    压缩图片
    - quality: JPG 质量 (1-100)，PNG 使用 optimize=True
    - max_size: 最大尺寸 (width, height)，保持宽高比
    """
    try:
        with Image.open(input_path) as img:
            # 转换为 RGB（如果是 RGBA 或其他模式）
            if img.mode in ('RGBA', 'LA', 'P'):
                # 对于有透明通道的 PNG，保持透明
                if img.mode == 'RGBA':
                    img = img.convert('RGBA')
                else:
                    img = img.convert('RGB')
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 如果图片太大，按比例缩小
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # 保存压缩后的图片
            if output_path.suffix.lower() == '.png':
                # PNG: 使用 optimize 和 compress_level
                img.save(output_path, 'PNG', optimize=True, compress_level=9)
            else:
                # JPG: 使用 quality
                img.save(output_path, 'JPEG', quality=quality, optimize=True)
            
            # 获取文件大小
            original_size = input_path.stat().st_size
            compressed_size = output_path.stat().st_size
            reduction = (1 - compressed_size / original_size) * 100
            
            return original_size, compressed_size, reduction
    except Exception as e:
        print(f"错误: 压缩 {input_path} 失败: {e}")
        return None, None, None

def main():
    cards_dir = Path('cards')
    if not cards_dir.exists():
        print("错误: cards 目录不存在")
        return
    
    # 创建备份目录
    backup_dir = cards_dir / 'backup_original'
    backup_dir.mkdir(exist_ok=True)
    
    # 支持的图片格式
    image_extensions = {'.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG'}
    
    total_original = 0
    total_compressed = 0
    processed = 0
    failed = 0
    
    print("开始压缩图片...")
    print("=" * 60)
    
    for img_file in cards_dir.iterdir():
        if img_file.suffix not in image_extensions:
            continue
        
        # 跳过备份目录
        if img_file.parent.name == 'backup_original':
            continue
        
        print(f"处理: {img_file.name}...", end=' ')
        
        # 备份原文件
        backup_path = backup_dir / img_file.name
        if not backup_path.exists():
            import shutil
            shutil.copy2(img_file, backup_path)
        
        # 创建临时输出文件
        temp_output = cards_dir / f".temp_{img_file.name}"
        
        # 压缩图片
        original_size, compressed_size, reduction = compress_image(
            img_file, 
            temp_output,
            quality=85,  # JPG 质量
            max_size=(2000, 3000)  # 最大尺寸
        )
        
        if original_size and compressed_size:
            # 如果压缩后更小，替换原文件
            if compressed_size < original_size:
                temp_output.replace(img_file)
                print(f"✓ 压缩成功: {original_size/1024/1024:.2f}MB → {compressed_size/1024/1024:.2f}MB "
                      f"(-{reduction:.1f}%)")
                total_original += original_size
                total_compressed += compressed_size
                processed += 1
            else:
                # 如果压缩后更大，删除临时文件，保留原文件
                temp_output.unlink()
                print(f"○ 已优化（文件大小未减小）")
                processed += 1
        else:
            print(f"✗ 失败")
            if temp_output.exists():
                temp_output.unlink()
            failed += 1
    
    print("=" * 60)
    print(f"完成！处理了 {processed} 个文件，失败 {failed} 个")
    if total_original > 0:
        total_reduction = (1 - total_compressed / total_original) * 100
        print(f"总大小: {total_original/1024/1024:.2f}MB → {total_compressed/1024/1024:.2f}MB "
              f"(-{total_reduction:.1f}%)")
    print(f"\n原文件已备份到: {backup_dir}")

if __name__ == '__main__':
    main()

