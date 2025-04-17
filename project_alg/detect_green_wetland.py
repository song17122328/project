import os
from main import read_tiff, mark_areas, save_as_png
# from new_main import read_tiff, mark_areas, save_as_png


def run_detection(tiff_path):
    print("进入函数 run_detection,参数是", tiff_path)
    # tiff_path = params["tiffPath"]
    output_path = tiff_path.replace(".tif", "_marked.png")
    output_path = output_path.replace("/", "\\")

    image, profile = read_tiff(tiff_path) # 第一次调用函数

    green_threshold = 50
    wet_threshold = 50

    marked_image = mark_areas(image, profile, green_threshold, wet_threshold)
    save_as_png(marked_image, output_path)
    print(output_path)
    return {
        "tif": None,
        "png": output_path
    }
