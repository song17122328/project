import numpy as np
import rasterio
from rasterio.plot import show
import matplotlib.pyplot as plt
from PIL import Image
import argparse

# 读取TIFF文件
def read_tiff(file_path):
    with rasterio.open(file_path) as src:
        image = src.read()  # 读取所有波段
        profile = src.profile  # 获取图像元信息
    return image, profile

# 标记绿地和湿地
def mark_areas(image, profile, green_threshold, wet_threshold):
    """
    参数：
    image: TIFF图像数据，格式为(波段数, 高度, 宽度)
    profile: TIFF图像元信息
    green_threshold: 判断绿地的条件(波段值范围)
    wet_threshold: 判断湿地的条件(波段值范围)
    """
    # 假设波段顺序为(Band 1, Band 2, Band 3, Band 4)对应(R, G, B, NIR)
    blue, green, red, nir = image[0], image[1], image[2], image[3]  # GF2, GF6

    # 创建输出图像 (RGB格式)
    marked_image = np.zeros((red.shape[0], red.shape[1], 3), dtype=np.uint8)
    max_value = max(red.max(), green.max(), blue.max())
    if max_value > 0:
        marked_image[..., 0] = (red / max_value * 255).astype(np.uint8)  # 归一化并转换为8位深度
        marked_image[..., 1] = (green / max_value * 255).astype(np.uint8)  # 归一化并转换为8位深度
        marked_image[..., 2] = (blue / max_value * 255).astype(np.uint8)  # 归一化并转换为8位深度

    # 标记绿地 (示例条件: G值大于某阈值，且G大于R和B)
    green_mask = (green > green_threshold) & (green > red) & (nir > green)
    # green_mask = (((nir - red) / (nir + red + 1)) > green_threshold) & (((nir - red) / (nir + red + 1)) < 0.5)

    marked_image[green_mask] = [0, 255, 0]  # 绿色标记

    # 标记湿地 (示例条件: B值大于某阈值，且B大于R和G)
    wet_mask = (blue > wet_threshold)  & (blue > red) & (green > red) & (nir < blue) & (nir < green)
    # wet_mask = (((green - nir) / (green + nir + 1)) > wet_threshold) & (((green - nir) / (green + nir + 1)) < 0.01)

    marked_image[wet_mask] = [0, 0, 255]  # 蓝色标记

    return marked_image

# 保存PNG文件
def save_as_png(image, output_path):
    Image.fromarray(image).save(output_path)

# 主函数
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tiff', type=str, required=True)
    parser.add_argument('--output', type=str, required=True)
    args = parser.parse_args()

    image, profile = read_tiff(args.tiff)
    green_threshold = 200
    wet_threshold = 600
    marked_image = mark_areas(image, profile, green_threshold, wet_threshold)
    save_as_png(marked_image, args.output)
    print(f"标记完成：{args.output}")

# 下面是我的程序，我出现了这样的错误
#   File "D:\project\project_alg\detect_green_wetland.py", line 15, in run_detection
#     marked_image = mark_areas(image, profile, green_threshold, wet_threshold)
#   File "D:\project\project_alg\main.py", line 25, in mark_areas
#     blue, green, red, nir = image[0], image[1], image[2], image[3]  # GF2, GF6
# IndexError: index 3 is out of bounds for axis 0 with size 3
# [2025-04-14 21:09:23 +0800] [10544] [DEBUG] KeepAlive Timeout. Closing connection.