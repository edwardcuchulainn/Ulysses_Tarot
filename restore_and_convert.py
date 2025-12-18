#!/usr/bin/env python3
"""
从备份恢复所有图片并转换为 JPG
"""
import sys
from pathlib import Path
import shutil

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
        if img.mode == 'RGBA':
            alpha = img.split()[3]
            return any(pixel < 255 for pixel in alpha.getdata())
        else:
            return True
    return False

def convert_png_to_jpg(png_path, jpg_path, quality=90, max_size=(1200, 2000)):
    """将 PNG 转换为 JPG"""
    try:
        with Image.open(png_path) as img:
            has_alpha = has_transparency(img)
            
            # 如果有透明通道，保持 PNG
            if has_alpha:
                return False, "有透明通道，保持 PNG"
            
            # 转换为 RGB
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 如果图片太大，按比例缩小
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # 保存为 JPG
            img.save(jpg_path, 'JPEG', quality=quality, optimize=True)
            
            original_size = png_path.stat().st_size
            compressed_size = jpg_path.stat().st_size
            reduction = (1 - compressed_size / original_size) * 100
            
            return True, f"转换成功: {original_size/1024/1024:.2f}MB → {compressed_size/1024/1024:.2f}MB (-{reduction:.1f}%)"
    except Exception as e:
        return False, f"错误: {e}"

def main():
    backup_dir = Path('cards/backup_original')
    cards_dir = Path('cards')
    
    if not backup_dir.exists():
        print("错误: 备份目录不存在")
        return
    
    # 获取所有备份的 PNG 文件
    png_files = list(backup_dir.glob('*.png'))
    
    if not png_files:
        print("备份目录中没有 PNG 文件")
        return
    
    print(f"找到 {len(png_files)} 个 PNG 文件")
    print("开始转换...")
    print("=" * 60)
    
    converted = 0
    kept_png = 0
    failed = 0
    
    for png_file in sorted(png_files):
        # 跳过临时文件
        if png_file.name.startswith('.temp_'):
            continue
        
        jpg_file = cards_dir / png_file.name.replace('.png', '.jpg')
        png_output = cards_dir / png_file.name
        
        print(f"处理: {png_file.name}...", end=' ')
        
        success, message = convert_png_to_jpg(png_file, jpg_file, quality=90, max_size=(1200, 2000))
        
        if success:
            # 转换成功，删除原 PNG（如果存在）
            if png_output.exists():
                png_output.unlink()
            print(f"✓ {message}")
            converted += 1
        elif "透明通道" in message:
            # 有透明通道，复制 PNG 文件
            shutil.copy2(png_file, png_output)
            print(f"○ {message}")
            kept_png += 1
        else:
            # 转换失败，至少复制 PNG 文件
            shutil.copy2(png_file, png_output)
            print(f"✗ {message} (已复制 PNG)")
            failed += 1
    
    print("=" * 60)
    print(f"完成！转换了 {converted} 个文件为 JPG，保留了 {kept_png} 个 PNG（有透明通道），失败 {failed} 个")
    
    # 检查最终文件数量
    jpg_count = len(list(cards_dir.glob('*.jpg')))
    png_count = len(list(cards_dir.glob('*.png')))
    total = jpg_count + png_count
    print(f"\n最终文件数: {total} (JPG: {jpg_count}, PNG: {png_count})")
    print(f"应该有的文件数: 78")
    
    if total < 78:
        print(f"⚠️  警告: 文件数量不足，可能还有文件缺失")

if __name__ == '__main__':
    main()

