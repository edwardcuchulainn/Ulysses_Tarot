#!/usr/bin/env python3
"""
更激进的 WebP 压缩：降低质量和尺寸以进一步减小文件大小
目标：在保持可接受质量的前提下，最大化压缩率
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

def compress_webp_aggressive(webp_path, output_path, quality=75, max_size=(1000, 1667)):
    """
    更激进的压缩
    - quality: 75 是很好的平衡点（质量仍然很好，但文件更小）
    - max_size: 进一步缩小尺寸（原尺寸约 1086x1810，缩小到 1000x1667）
    """
    try:
        with Image.open(webp_path) as img:
            # 确保是 RGB 模式
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 如果图片太大，按比例缩小
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # 保存为 WebP，使用更激进的设置
            # quality: 75（从 85 降低）
            # method: 6（最慢但压缩最好）
            img.save(output_path, 'WEBP', quality=quality, method=6)
            
            original_size = webp_path.stat().st_size
            compressed_size = output_path.stat().st_size
            reduction = (1 - compressed_size / original_size) * 100
            
            return True, original_size, compressed_size, reduction, None
    except Exception as e:
        return False, 0, 0, 0, str(e)

def main():
    cards_dir = Path('cards')
    backup_dir = cards_dir / 'backup_webp_original'
    backup_dir.mkdir(exist_ok=True)
    
    if not cards_dir.exists():
        print("错误: cards 目录不存在")
        return
    
    # 获取所有 WebP 文件
    webp_files = list(cards_dir.glob('*.webp'))
    
    if not webp_files:
        print("cards 目录中没有 WebP 文件")
        return
    
    print(f"找到 {len(webp_files)} 个 WebP 文件")
    print("开始更激进的压缩...")
    print("设置: 质量 75, 最大尺寸 1000x1667")
    print("=" * 60)
    
    converted = 0
    failed = 0
    total_original = 0
    total_compressed = 0
    
    for webp_file in sorted(webp_files):
        # 创建临时输出文件
        temp_output = cards_dir / f".temp_{webp_file.name}"
        
        print(f"处理: {webp_file.name}...", end=' ')
        
        # 备份原文件（如果还没备份）
        backup_path = backup_dir / webp_file.name
        if not backup_path.exists():
            shutil.copy2(webp_file, backup_path)
        
        success, orig_size, comp_size, reduction, error = compress_webp_aggressive(
            webp_file, temp_output, quality=75, max_size=(1000, 1667)
        )
        
        if success and comp_size < orig_size:
            # 压缩成功且文件更小，替换原文件
            temp_output.replace(webp_file)
            print(f"✓ 压缩成功: {orig_size/1024:.1f}KB → {comp_size/1024:.1f}KB (-{reduction:.1f}%)")
            converted += 1
            total_original += orig_size
            total_compressed += comp_size
        elif success:
            # 压缩成功但文件更大，保留原文件
            temp_output.unlink()
            print(f"○ 已优化（文件大小未减小）")
            converted += 1
        else:
            print(f"✗ 失败: {error}")
            if temp_output.exists():
                temp_output.unlink()
            failed += 1
    
    print("=" * 60)
    print(f"完成！处理了 {converted} 个文件，失败 {failed} 个")
    if total_original > 0:
        total_reduction = (1 - total_compressed / total_original) * 100
        print(f"总大小: {total_original/1024/1024:.2f}MB → {total_compressed/1024/1024:.2f}MB (-{total_reduction:.1f}%)")
    print(f"\n原 WebP 文件已备份到: {backup_dir}")
    
    # 检查最终文件大小
    total_size = sum(f.stat().st_size for f in cards_dir.glob('*.webp'))
    print(f"\n最终总大小: {total_size/1024/1024:.2f}MB")

if __name__ == '__main__':
    main()

