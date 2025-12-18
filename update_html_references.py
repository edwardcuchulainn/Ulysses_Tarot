#!/usr/bin/env python3
"""
更新 HTML 文件中的图片引用，将已转换为 JPG 的 PNG 引用更新为 JPG
"""
from pathlib import Path
import re

def update_html_references():
    html_file = Path('index.html')
    cards_dir = Path('cards')
    
    if not html_file.exists():
        print("错误: index.html 不存在")
        return
    
    if not cards_dir.exists():
        print("错误: cards 目录不存在")
        return
    
    # 读取 HTML 内容
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查哪些 PNG 文件已经转换为 JPG
    png_to_jpg = {}
    for png_file in cards_dir.glob('*.png'):
        jpg_file = png_file.with_suffix('.jpg')
        if jpg_file.exists():
            png_to_jpg[png_file.name] = jpg_file.name
            print(f"发现转换: {png_file.name} → {jpg_file.name}")
    
    if not png_to_jpg:
        print("没有找到需要更新的引用")
        return
    
    # 更新 HTML 中的引用
    updated_count = 0
    for png_name, jpg_name in png_to_jpg.items():
        # 替换所有 PNG 引用为 JPG
        pattern = re.compile(re.escape(png_name), re.IGNORECASE)
        if pattern.search(content):
            content = pattern.sub(jpg_name, content)
            updated_count += 1
            print(f"更新引用: {png_name} → {jpg_name}")
    
    # 保存更新后的 HTML
    if updated_count > 0:
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"\n完成！更新了 {updated_count} 个图片引用")
    else:
        print("没有需要更新的引用")

if __name__ == '__main__':
    update_html_references()

