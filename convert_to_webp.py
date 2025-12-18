#!/usr/bin/env python3
"""
将所有 JPG 图片转换为 WebP 格式，进一步减小文件大小
WebP 格式通常比 JPG 小 25-35%，同时保持相同的视觉质量
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

def convert_jpg_to_webp(jpg_path, webp_path, quality=85, max_size=(1200, 2000)):
    """将 JPG 转换为 WebP"""
    try:
        with Image.open(jpg_path) as img:
            # 确保是 RGB 模式
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 如果图片太大，按比例缩小
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # 保存为 WebP
            # quality: 0-100，85 是很好的平衡点（质量高，文件小）
            # method: 0-6，6 是最慢但压缩最好的
            img.save(webp_path, 'WEBP', quality=quality, method=6)
            
            original_size = jpg_path.stat().st_size
            compressed_size = webp_path.stat().st_size
            reduction = (1 - compressed_size / original_size) * 100
            
            return True, original_size, compressed_size, reduction, None
    except Exception as e:
        return False, 0, 0, 0, str(e)

def main():
    cards_dir = Path('cards')
    backup_dir = cards_dir / 'backup_jpg'
    backup_dir.mkdir(exist_ok=True)
    
    if not cards_dir.exists():
        print("错误: cards 目录不存在")
        return
    
    # 获取所有 JPG 文件
    jpg_files = list(cards_dir.glob('*.jpg'))
    
    if not jpg_files:
        print("cards 目录中没有 JPG 文件")
        return
    
    print(f"找到 {len(jpg_files)} 个 JPG 文件")
    print("开始转换为 WebP 格式...")
    print("=" * 60)
    
    converted = 0
    failed = 0
    total_original = 0
    total_compressed = 0
    
    for jpg_file in sorted(jpg_files):
        webp_file = jpg_file.with_suffix('.webp')
        
        print(f"处理: {jpg_file.name}...", end=' ')
        
        success, orig_size, comp_size, reduction, error = convert_jpg_to_webp(
            jpg_file, webp_file, quality=85, max_size=(1200, 2000)
        )
        
        if success and comp_size < orig_size:
            # 转换成功且文件更小，备份原 JPG 并删除
            backup_path = backup_dir / jpg_file.name
            if not backup_path.exists():
                shutil.copy2(jpg_file, backup_path)
            jpg_file.unlink()
            print(f"✓ 转换成功: {orig_size/1024/1024:.2f}MB → {comp_size/1024/1024:.2f}MB (-{reduction:.1f}%)")
            converted += 1
            total_original += orig_size
            total_compressed += comp_size
        elif success:
            # 转换成功但文件更大，保留 JPG
            webp_file.unlink()
            print(f"○ 已转换（但 JPG 更小，保留 JPG）")
            converted += 1
        else:
            print(f"✗ 失败: {error}")
            failed += 1
    
    print("=" * 60)
    print(f"完成！转换了 {converted} 个文件，失败 {failed} 个")
    if total_original > 0:
        total_reduction = (1 - total_compressed / total_original) * 100
        print(f"总大小: {total_original/1024/1024:.2f}MB → {total_compressed/1024/1024:.2f}MB (-{total_reduction:.1f}%)")
    print(f"\n原 JPG 文件已备份到: {backup_dir}")
    
    # 检查最终文件数量
    webp_count = len(list(cards_dir.glob('*.webp')))
    jpg_count = len(list(cards_dir.glob('*.jpg')))
    total = webp_count + jpg_count
    print(f"\n最终文件数: {total} (WebP: {webp_count}, JPG: {jpg_count})")
    print(f"应该有的文件数: 78")

if __name__ == '__main__':
    main()

