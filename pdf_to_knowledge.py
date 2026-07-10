# pdf_to_knowledge.py
"""
PDF转知识库工具 - 一键将PDF转换为知识库txt文件
用法：python pdf_to_knowledge.py
"""

import os
import re
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("⚠️ 请先安装 pdfplumber：pip install pdfplumber")
    exit(1)


def extract_pdf_to_txt(pdf_path, output_dir="knowledge"):
    """
    将PDF完整提取为txt文件，保留表格结构
    """
    # 检查PDF是否存在
    if not os.path.exists(pdf_path):
        print(f"❌ 找不到文件：{pdf_path}")
        return False
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成输出文件名（去掉.pdf后缀）
    pdf_name = Path(pdf_path).stem
    output_path = os.path.join(output_dir, f"{pdf_name}.txt")
    
    print(f"📖 正在读取：{pdf_path}")
    print(f"📝 输出到：{output_path}")
    print("-" * 50)
    
    all_text = []
    total_pages = 0
    total_tables = 0
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            
            for page_num, page in enumerate(pdf.pages, 1):
                print(f"  处理第 {page_num}/{total_pages} 页...")
                
                # 页眉
                all_text.append(f"\n{'='*60}")
                all_text.append(f"第 {page_num} 页")
                all_text.append(f"{'='*60}\n")
                
                # 1. 提取普通文本
                text = page.extract_text()
                if text:
                    all_text.append(text)
                
                # 2. 提取表格
                tables = page.extract_tables()
                
                for table_idx, table in enumerate(tables):
                    if not table or len(table) < 2:
                        continue
                    
                    total_tables += 1
                    all_text.append(f"\n📊 表格 {total_tables}：")
                    
                    # 处理表头
                    header = table[0]
                    if header:
                        header_text = " | ".join([
                            str(cell).strip().replace("\n", " ") if cell else ""
                            for cell in header
                        ])
                        all_text.append(f"【{header_text}】")
                        all_text.append("-" * 60)
                    
                    # 处理数据行
                    for row in table[1:]:
                        row_text = " | ".join([
                            str(cell).strip().replace("\n", " ") if cell else ""
                            for cell in row
                        ])
                        if row_text.strip():
                            all_text.append(row_text)
                    
                    all_text.append("")  # 空行分隔
                
                # 每页结束加个分隔
                all_text.append("\n" + "─" * 60)
            
            # 合并所有内容
            full_text = "\n".join(all_text)
            
            # 清理多余空行
            full_text = re.sub(r'\n{3,}', '\n\n', full_text)
            
            # 保存文件
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(full_text)
            
            print("-" * 50)
            print(f"✅ 提取完成！")
            print(f"   - 总页数：{total_pages}")
            print(f"   - 表格数：{total_tables}")
            print(f"   - 文件大小：{len(full_text)} 字符")
            print(f"   - 保存位置：{output_path}")
            return True
    
    except Exception as e:
        print(f"❌ 提取失败：{e}")
        return False


def batch_convert():
    """
    批量转换：处理当前目录下所有PDF
    """
    pdf_files = list(Path(".").glob("*.pdf"))
    pdf_files += list(Path(".").glob("*.PDF"))
    
    if not pdf_files:
        print("📂 当前目录没有找到PDF文件")
        print("💡 请将PDF文件放在项目根目录，或指定文件路径")
        return
    
    print(f"📂 找到 {len(pdf_files)} 个PDF文件")
    print("-" * 50)
    
    success_count = 0
    for pdf_path in pdf_files:
        print(f"\n处理：{pdf_path.name}")
        if extract_pdf_to_txt(str(pdf_path)):
            success_count += 1
    
    print(f"\n{'='*50}")
    print(f"✅ 完成！成功转换 {success_count}/{len(pdf_files)} 个文件")


def main():
    """
    主程序：支持两种模式
    1. 指定文件：python pdf_to_knowledge.py 文件名.pdf
    2. 批量模式：python pdf_to_knowledge.py （自动处理所有PDF）
    """
    import sys
    
    print("=" * 50)
    print("📄 PDF → 知识库 转换工具")
    print("=" * 50)
    print()
    
    # 检查是否有指定文件
    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]
        extract_pdf_to_txt(pdf_file)
    else:
        # 批量模式
        batch_convert()
    
    print("\n💡 转换后的文件在 knowledge/ 文件夹中")
    print("💡 重启 Streamlit 后，AI 就能读取新知识库了")


if __name__ == "__main__":
    main()