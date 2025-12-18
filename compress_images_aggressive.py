#!/usr/bin/env python3
"""
更激进的图片压缩：将 PNG 转换为高质量 JPG 或 WebP
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

def has_transparency(img):
    """检查图片是否有透明通道"""
    if img.mode in ('RGBA', 'LA'):
        # 检查 alpha 通道
        if img.mode == 'RGBA':
            alpha = img.split()[3]
            # 如果 alpha 通道有任何非 255 的值，说明有透明
            return any(pixel < 255 for pixel in alpha.getdata())
        else:
            return True
    return False

def compress_image(input_path, output_path, jpg_quality=90, max_size=(1200, 2000), use_webp=False):
    """
    更激进的压缩
    - jpg_quality: JPG 质量 (85-95 保持高质量)
    - max_size: 最大尺寸，稍微缩小以减小文件大小
    - use_webp: 是否使用 WebP 格式（需要浏览器支持）
    """
    try:
        with Image.open(input_path) as img:
            original_mode = img.mode
            original_size_tuple = img.size
            
            # 检查是否有透明通道
            has_alpha = has_transparency(img)
            
            # 如果图片太大，按比例缩小（保持清晰度）
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # 决定输出格式
            if use_webp and has_alpha:
                # 有透明通道，使用 WebP
                img.save(output_path, 'WEBP', quality=85, method=6)
            elif input_path.suffix.lower() == '.png' and not has_alpha:
                # PNG 但没有透明通道，转换为高质量 JPG
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                output_path = output_path.with_suffix('.jpg')
                img.save(output_path, 'JPEG', quality=jpg_quality, optimize=True)
            elif input_path.suffix.lower() == '.png':
                # 有透明通道的 PNG，使用 WebP 或保持 PNG（优化）
                if use_webp:
                    img.save(output_path, 'WEBP', quality=85, method=6)
                else:
                    # 优化 PNG
                    img.save(output_path, 'PNG', optimize=True, compress_level=9)
            else:
                # JPG 文件，直接压缩
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img.save(output_path, 'JPEG', quality=jpg_quality, optimize=True)
            
            # 获取文件大小
            original_size = input_path.stat().st_size
            compressed_size = output_path.stat().st_size
            reduction = (1 - compressed_size / original_size) * 100
            
            return original_size, compressed_size, reduction, output_path
    except Exception as e:
        print(f"错误: 压缩 {input_path} 失败: {e}")
        return None, None, None, None

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
    converted_to_jpg = 0
    
    print("开始更激进的图片压缩...")
    print("策略: PNG(无透明) → JPG, PNG(有透明) → 优化PNG, JPG → 压缩JPG")
    print("=" * 60)
    
    for img_file in cards_dir.iterdir():
        if img_file.suffix not in image_extensions:
            continue
        
        # 跳过备份目录
        if img_file.parent.name == 'backup_original':
            continue
        
        # 跳过临时文件
        if img_file.name.startswith('.temp_'):
            continue
        
        print(f"处理: {img_file.name}...", end=' ')
        
        # 备份原文件（如果还没备份）
        backup_path = backup_dir / img_file.name
        if not backup_path.exists():
            import shutil
            shutil.copy2(img_file, backup_path)
        
        # 创建临时输出文件
        temp_output = cards_dir / f".temp_{img_file.name}"
        
        # 压缩图片（不使用 WebP，因为需要更新 HTML 中的引用）
        original_size, compressed_size, reduction, final_output = compress_image(
            img_file, 
            temp_output,
            jpg_quality=90,  # 高质量 JPG
            max_size=(1200, 2000),  # 稍微缩小尺寸
            use_webp=False  # 不使用 WebP，避免需要修改 HTML
        )
        
        if original_size and compressed_size:
            # 如果压缩后更小，替换原文件
            if compressed_size < original_size:
                # 如果格式改变了（PNG → JPG），需要删除原 PNG 文件
                if final_output.suffix != img_file.suffix:
                    img_file.unlink()
                    converted_to_jpg += 1
                    print(f"✓ 转换并压缩: {img_file.suffix} → {final_output.suffix}, "
                          f"{original_size/1024/1024:.2f}MB → {compressed_size/1024/1024:.2f}MB "
                          f"(-{reduction:.1f}%)")
                else:
                    temp_output.replace(img_file)
                    print(f"✓ 压缩成功: {original_size/1024/1024:.2f}MB → {compressed_size/1024/1024:.2f}MB "
                          f"(-{reduction:.1f}%)")
                total_original += original_size
                total_compressed += compressed_size
                processed += 1
            else:
                # 如果压缩后更大，删除临时文件，保留原文件
                if temp_output.exists():
                    temp_output.unlink()
                if final_output and final_output != temp_output and final_output.exists():
                    final_output.unlink()
                print(f"○ 已优化（文件大小未减小）")
                processed += 1
        else:
            print(f"✗ 失败")
            if temp_output.exists():
                temp_output.unlink()
            failed += 1
    
    print("=" * 60)
    print(f"完成！处理了 {processed} 个文件，失败 {failed} 个")
    if converted_to_jpg > 0:
        print(f"已将 {converted_to_jpg} 个 PNG 文件转换为 JPG（无透明通道）")
    if total_original > 0:
        total_reduction = (1 - total_compressed / total_original) * 100
        print(f"总大小: {total_original/1024/1024:.2f}MB → {total_compressed/1024/1024:.2f}MB "
              f"(-{total_reduction:.1f}%)")
    print(f"\n原文件已备份到: {backup_dir}")
    if converted_to_jpg > 0:
        print("\n⚠️  注意: 部分 PNG 文件已转换为 JPG，需要更新 HTML 中的图片引用！")

if __name__ == '__main__':
    main()

