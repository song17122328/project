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
    num_bands = image.shape[0]
    blue, green, red = image[0], image[1], image[2]
    nir = image[3] if num_bands >= 4 else None

    marked_image = np.zeros((red.shape[0], red.shape[1], 3), dtype=np.uint8)
    max_value = max(red.max(), green.max(), blue.max())
    if max_value > 0:
        marked_image[..., 0] = (red / max_value * 255).astype(np.uint8)
        marked_image[..., 1] = (green / max_value * 255).astype(np.uint8)
        marked_image[..., 2] = (blue / max_value * 255).astype(np.uint8)

    # 绿地判断（如果无NIR则仅用RGB）
    green_mask = (green > green_threshold) & (green > red)
    if nir is not None:
        green_mask &= (nir > green)  # 如果有NIR波段，增加条件
    marked_image[green_mask] = [0, 255, 0]

    # 湿地判断
    wet_mask = (blue > wet_threshold) & (blue > red)
    if nir is not None:
        wet_mask &= (nir < blue)  # 如果有NIR波段，增加条件
    marked_image[wet_mask] = [0, 0, 255]

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


if __name__ == "__main__":
    main()
