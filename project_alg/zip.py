import os
import zipfile
import tarfile
import gzip
import shutil
from pathlib import Path


def extract_archive(archive_path, output_dir="./resource/data"):
    """
    解压压缩包（支持 ZIP/TAR/GZ 格式）

    :param archive_path: 压缩包路径（如 /path/to/archive.zip）
    :param output_dir: 解压目录（默认解压到压缩包所在目录）
    :return: 解压后的文件列表
    """
    if not os.path.exists(archive_path):
        raise FileNotFoundError(f"压缩包不存在: {archive_path}")

    if output_dir is None:
        output_dir = os.path.dirname(archive_path)
    os.makedirs(output_dir, exist_ok=True)

    extracted_files = []

    try:
        # 处理 ZIP 文件
        if zipfile.is_zipfile(archive_path):
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(output_dir)
                extracted_files = zip_ref.namelist()
                print(f"解压 ZIP 文件成功，共 {len(extracted_files)} 个文件")

        # 处理 TAR/TAR.GZ 文件
        elif archive_path.endswith(('.tar', '.tar.gz', '.tgz')):
            mode = 'r:gz' if archive_path.endswith('.gz') else 'r'
            with tarfile.open(archive_path, mode) as tar_ref:
                tar_ref.extractall(output_dir)
                extracted_files = tar_ref.getnames()
                print(f"解压 TAR 文件成功，共 {len(extracted_files)} 个文件")

        # 处理 GZ 文件（单文件压缩）
        elif archive_path.endswith('.gz'):
            output_file = os.path.join(output_dir, os.path.basename(archive_path[:-3]))
            with gzip.open(archive_path, 'rb') as gz_ref:
                with open(output_file, 'wb') as out_ref:
                    shutil.copyfileobj(gz_ref, out_ref)
            extracted_files = [output_file]
            print(f"解压 GZ 文件成功: {output_file}")

        else:
            raise ValueError("不支持的压缩格式（仅支持 ZIP/TAR/GZ）")

        return [os.path.join(output_dir, f) for f in extracted_files]

    except Exception as e:
        shutil.rmtree(output_dir, ignore_errors=True)  # 失败时清理残留文件
        raise RuntimeError(f"解压失败: {e}")


# 示例用法
if __name__ == "__main__":
    # 替换为你的压缩包路径
    archive_path = "/path/to/your/archive.zip"
    output_dir = "./extracted_files"  # 解压目录（可选）

    try:
        files = extract_archive(archive_path, output_dir)
        print("解压后的文件列表:")
        for file in files:
            print(f" - {file}")
    except Exception as e:
        print(f"错误: {e}")