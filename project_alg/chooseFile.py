import os
import shutil
from pathlib import Path


def filter_and_copy_files(source_dir, target_dir, suffix="MSS.tif"):
    """
    筛选指定后缀的文件并复制到新文件夹

    :param source_dir: 解压后的源文件夹路径
    :param target_dir: 目标文件夹路径（存放筛选后的文件）
    :param suffix: 需要匹配的文件后缀（如 "MSS.tif"）
    :return: 匹配的文件列表
    """
    # 如果文件夹存在，删除它（包括所有子文件和子目录）
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)
    os.makedirs(target_dir)

    matched_files = []

    # 遍历源文件夹
    for root, _, files in os.walk(source_dir):
        for file in files:
            if file.endswith(suffix):
                src_path = os.path.join(root, file)
                dst_path = os.path.join(target_dir, file)

                # 避免文件名冲突（如果目标文件夹已存在同名文件）
                counter = 1
                while os.path.exists(dst_path):
                    base, ext = os.path.splitext(file)
                    dst_path = os.path.join(target_dir, f"{base}_{counter}{ext}")
                    counter += 1

                # 复制文件
                shutil.copy2(src_path, dst_path)
                matched_files.append(dst_path)
                print(f"已复制: {src_path} -> {dst_path}")

    print(f"共找到 {len(matched_files)} 个匹配文件")
    return matched_files


# 示例用法
if __name__ == "__main__":
    # 替换为你的实际路径
    extracted_dir = "./extracted_files"  # 解压后的文件夹
    output_dir = "./filtered_MSS_files"  # 存放筛选后的文件

    try:
        matched_files = filter_and_copy_files(extracted_dir, output_dir, suffix="_MSS.tif")
        print("\n筛选后的文件列表:")
        for file in matched_files:
            print(f" - {file}")
    except Exception as e:
        print(f"错误: {e}")