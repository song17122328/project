import os
import math
import random
import numpy as np
import rasterio
from rasterio.windows import Window
from skimage.transform import resize
from tqdm import tqdm
from osgeo import gdal
from rasterio.transform import Affine
from rasterio.crs import CRS

def get_valid_geoinfo(path):
    """
    尝试从嵌入或 RPC(.rpb)中恢复真实 transform 和 CRS
    """
    with rasterio.open(path) as src:
        crs = src.crs
        transform = src.transform
        if transform != Affine.identity and crs is not None:
            print(f" {os.path.basename(path)} 已嵌入地理信息。")
            return crs, transform

    print(f"[!] {os.path.basename(path)} 无嵌入地理信息，尝试从 RPC/.rpb 文件恢复...")

    # === 利用 GDAL 临时重投影为 GeoTIFF，强制生成 GeoTransform ===
    temp_path = "/tmp/_rpc_temp.tif"
    gdal_ds = gdal.Open(path, gdal.GA_ReadOnly)

    # 检查是否有 RPC 元数据
    rpc = gdal_ds.GetMetadata('RPC')
    if not rpc:
        print(" 未检测到 RPC 信息，无法恢复")
        return None, None

    # GDAL Warp 创建具有 GeoTransform 的影像
    warp_options = gdal.WarpOptions(
        format='GTiff',
        dstSRS='EPSG:4326',  # 常用于卫星影像的 RPC
        rpc=True,
        geoloc=False
    )

    gdal.Warp(destNameOrDestDS=temp_path, srcDSOrSrcDSTab=gdal_ds, options=warp_options)
    gdal_ds = None  # 释放原始数据集

    # 读取临时文件获取真实 Transform 和 CRS
    with rasterio.open(temp_path) as temp_src:
        transform = temp_src.transform
        crs = temp_src.crs

    print(" 成功从 RPC + GDAL Warp 获取有效地理信息")
    return crs, transform



def gram_schmidt_fusion_with_cloud_mask(
    pan_path,
    ms_path,
    output_path,
    block_size=1024,
    sample_ratio=0.1,
    lower_percent=2,
    upper_percent=98,
    gamma=1.3,
    align_pan_gs1=True,
    cloud_mode='KEEP_MS',
    cloud_percentile=99
):
    # === A) 读取元信息 ===
    with rasterio.open(pan_path) as pan_src:
        pan_width, pan_height = pan_src.width, pan_src.height
        pan_profile = pan_src.profile

    with rasterio.open(ms_path) as ms_src:
        ms_width, ms_height = ms_src.width, ms_src.height

    ratio_x = pan_width / ms_width
    ratio_y = pan_height / ms_height

    # === B) 提取有效地理信息 ===
    crs, transform = get_valid_geoinfo(pan_path)
    if crs is None or transform is None:
        crs, transform = get_valid_geoinfo(ms_path)

    if crs is None or transform is None:
        raise ValueError("无法获取有效地理信息")

    
    # === C) 设置输出 profile ===
    out_profile = pan_profile.copy()
    out_profile.update({
        'count': 3,
        'dtype': 'uint8',
        'driver': 'GTiff',
        'crs': crs,
        'transform': transform
    })
    # ========== B) 抽样统计全局分位点 + 云阈值 ==========

    print("[1] 抽样统计分位点 + 云阈值 ...")
    ms_windows = []
    for row_start in range(0, ms_height, block_size):
        for col_start in range(0, ms_width, block_size):
            w = Window(
                col_off=col_start,
                row_off=row_start,
                width=min(block_size, ms_width - col_start),
                height=min(block_size, ms_height - row_start)
            )
            ms_windows.append(w)
    sample_count_ms = max(1, int(len(ms_windows)*sample_ratio))
    sampled_ms_windows = random.sample(ms_windows, sample_count_ms)

    # 用于 [lower%, upper%] 分位点统计 (R,G,B)
    # 同时还要统计 sum(R,G,B) 用于判断云阈值
    ms_samples = [[], [], []]  # R, G, B
    sum_samples = []
    with rasterio.open(ms_path) as ms_src:
        for w in tqdm(sampled_ms_windows, desc="Sampling MS"):
            data = ms_src.read(indexes=[1,2,3], window=w).astype(np.float32)
            # data.shape = (3, h, w)
            for b in range(3):
                flat = data[b].flatten()
                if len(flat) > 1000:
                    flat = np.random.choice(flat, 1000, replace=False)
                ms_samples[b].extend(flat.tolist())
            # sum(R,G,B)
            sum_rgb = data.sum(axis=0).flatten()
            if len(sum_rgb) > 1000:
                sum_rgb = np.random.choice(sum_rgb, 1000, replace=False)
            sum_samples.extend(sum_rgb.tolist())

    ms_p_low = [0,0,0]
    ms_p_high = [0,0,0]
    for b in range(3):
        arr = np.array(ms_samples[b])
        ms_p_low[b] = np.percentile(arr, lower_percent)
        ms_p_high[b] = np.percentile(arr, upper_percent)

    sum_samples = np.array(sum_samples)
    cloud_threshold = np.percentile(sum_samples, cloud_percentile)

    print(f"MS分位点: R=[{ms_p_low[0]:.2f}, {ms_p_high[0]:.2f}], "
          f"G=[{ms_p_low[1]:.2f}, {ms_p_high[1]:.2f}], "
          f"B=[{ms_p_low[2]:.2f}, {ms_p_high[2]:.2f}]")
    print(f"Cloud threshold (sumRGB) = {cloud_threshold:.2f}")

    # 同样抽样 PAN 分位点
    pan_windows = []
    with rasterio.open(pan_path) as pan_src:
        pan_width, pan_height = pan_src.width, pan_src.height
    for row_start in range(0, pan_height, block_size):
        for col_start in range(0, pan_width, block_size):
            w = Window(
                col_off=col_start,
                row_off=row_start,
                width=min(block_size, pan_width-col_start),
                height=min(block_size, pan_height-row_start)
            )
            pan_windows.append(w)

    sample_count_pan = max(1, int(len(pan_windows)*sample_ratio))
    sampled_pan_windows = random.sample(pan_windows, sample_count_pan)

    pan_samples = []
    with rasterio.open(pan_path) as pan_src:
        for w in tqdm(sampled_pan_windows, desc="Sampling PAN"):
            block = pan_src.read(1, window=w).astype(np.float32)
            flat = block.flatten()
            if len(flat) > 1000:
                flat = np.random.choice(flat, 1000, replace=False)
            pan_samples.extend(flat.tolist())

    pan_samples = np.array(pan_samples)
    pan_p_low = np.percentile(pan_samples, lower_percent)
    pan_p_high = np.percentile(pan_samples, upper_percent)
    print(f"PAN分位点 = [{pan_p_low:.2f}, {pan_p_high:.2f}]")

    # ========== C) 分块融合 (云区保留MS/压亮) + Gram-Schmidt ==========

    print("[2] 分块Gram-Schmidt + 简易云掩膜 处理中 ...")
    with rasterio.open(pan_path) as pan_src, \
         rasterio.open(ms_path) as ms_src, \
         rasterio.open(output_path, 'w', **out_profile) as dst:

        # 枚举所有块
        all_pan_windows = []
        for row_start in range(0, pan_height, block_size):
            for col_start in range(0, pan_width, block_size):
                w = Window(
                    col_off=col_start,
                    row_off=row_start,
                    width=min(block_size, pan_width-col_start),
                    height=min(block_size, pan_height-row_start)
                )
                all_pan_windows.append(w)

        for w in tqdm(all_pan_windows, desc="Fusing blocks"):
            row_size = w.height
            col_size = w.width

            # --- 1) PAN裁剪归一化
            pan_block = pan_src.read(1, window=w).astype(np.float32)
            pan_block = np.clip(pan_block, pan_p_low, pan_p_high)
            pan_block = (pan_block - pan_p_low)/(pan_p_high - pan_p_low + 1e-6)
            pan_block = np.clip(pan_block, 0,1)

            # --- 2) 读取MS(R,G,B)，裁剪/归一化
            ms_row_start = int(math.floor(w.row_off / ratio_y))
            ms_row_end   = int(math.ceil((w.row_off+row_size)/ratio_y))
            ms_col_start = int(math.floor(w.col_off / ratio_x))
            ms_col_end   = int(math.ceil((w.col_off+col_size)/ratio_x))

            ms_row_start = max(ms_row_start, 0)
            ms_row_end   = min(ms_row_end, ms_height)
            ms_col_start = max(ms_col_start, 0)
            ms_col_end   = min(ms_col_end, ms_width)

            ms_data = ms_src.read(
                indexes=[1,2,3],
                window=Window(ms_col_start, ms_row_start,
                              ms_col_end-ms_col_start,
                              ms_row_end-ms_row_start)
            ).astype(np.float32)

            ms_upsampled = np.zeros((3, row_size, col_size), dtype=np.float32)
            for b in range(3):
                band_clip = np.clip(ms_data[b], ms_p_low[b], ms_p_high[b])
                band_norm = (band_clip - ms_p_low[b])/(ms_p_high[b]-ms_p_low[b]+1e-6)
                band_norm = np.clip(band_norm, 0,1)

                ms_upsampled[b] = resize(
                    band_norm,
                    (row_size, col_size),
                    order=1,
                    preserve_range=True
                )

            # --- 3) 简易云掩膜 => sum(R,G,B) > cloud_threshold ?
            sum_rgb_block = ms_upsampled.sum(axis=0)  # shape=(row_size, col_size)
            cloud_mask = (sum_rgb_block > (cloud_threshold/(ms_p_high[0]+ms_p_high[1]+ms_p_high[2]) )) 

            # --- 4) Gram-Schmidt, 仅对非云像素
            # 先做GS变换
            R = ms_upsampled[0]
            G = ms_upsampled[1]
            B = ms_upsampled[2]
            GS1 = (R + G + B)/3.0
            GS2 = R - G
            GS3 = (R + G)/2.0 - B

            # 对pan_block做 mean-std对齐
            if align_pan_gs1:
                m_pan = np.mean(pan_block[~cloud_mask])  # 非云区
                s_pan = np.std(pan_block[~cloud_mask]) + 1e-6
                m_gs1 = np.mean(GS1[~cloud_mask])
                s_gs1 = np.std(GS1[~cloud_mask]) + 1e-6
                pan_adj = (pan_block - m_pan)/s_pan * s_gs1 + m_gs1
                pan_adj = np.clip(pan_adj, 0,1)
                fused_GS1 = pan_adj
            else:
                fused_GS1 = pan_block

            # 构造 R_fused,G_fused,B_fused
            R_fused = fused_GS1 + GS2/2.0 + GS3/3.0
            G_fused = fused_GS1 - GS2/2.0 + GS3/3.0
            B_fused = fused_GS1 - 2.0*GS3/3.0

            # 然后把“云区”像素用cloud_mode处理
            if cloud_mode == 'KEEP_MS':
                # 直接保留 MS 原值(已裁剪+上采样)
                R_fused[cloud_mask] = R[cloud_mask]
                G_fused[cloud_mask] = G[cloud_mask]
                B_fused[cloud_mask] = B[cloud_mask]

            elif cloud_mode == 'COMPRESS':
                # 对云区做亮度压缩
                # 例如让其亮度= 原值^0.8
                R_fused[cloud_mask] = (R[cloud_mask])**0.8
                G_fused[cloud_mask] = (G[cloud_mask])**0.8
                B_fused[cloud_mask] = (B[cloud_mask])**0.8
            else:
                # 也可直接设成灰色、或其他处理
                pass

            fused_rgb = np.stack([R_fused, G_fused, B_fused], axis=0)
            fused_rgb = np.clip(fused_rgb, 0,1)

            # --- 5) gamma校正 (全局)
            if gamma != 1.0:
                fused_rgb = fused_rgb ** (1.0/gamma)
            fused_rgb = np.clip(fused_rgb, 0,1)

            # --- 6) 写出
            fused_uint8 = (fused_rgb*255).astype(np.uint8)
            dst.write(fused_uint8, indexes=[1,2,3], window=w)
    print(f"✔ 融合完成，输出已保留地理信息: {output_path}")
    with rasterio.open(output_path) as src:
        print("  - CRS:", src.crs)
        print("  - Transform:", src.transform)
    print(f"处理完成, 输出到: {output_path}")
    


if __name__=="__main__":
    # pan_img = "./GF2_PMS1_E67.5_N40.8_20210228_L1A0005507949/GF2_PMS1_E67.5_N40.8_20210228_L1A0005507949-PAN1.tiff"
    # ms_img =  "./GF2_PMS1_E67.5_N40.8_20210228_L1A0005507949/GF2_PMS1_E67.5_N40.8_20210228_L1A0005507949-MSS1.tiff"
    # out_img = "./fused_1/fused_large_result_1.tiff"

    pan_img = "./GF2_PMS1_E66.9_N41.0_20211211_L1A0006129384/GF2_PMS1_E66.9_N41.0_20211211_L1A0006129384-PAN1.tiff"
    ms_img = "./GF2_PMS1_E66.9_N41.0_20211211_L1A0006129384/GF2_PMS1_E66.9_N41.0_20211211_L1A0006129384-MSS1.tiff"
    out_img = "./fused_2/fused_large_result_2.tiff"

    # pan_img = "./GF2_PMS1_E67.7_N40.6_20230601_L1A0007312900\GF2_PMS1_E67.7_N40.6_20230601_L1A0007312900-PAN1.tiff"
    # ms_img = "./GF2_PMS1_E67.7_N40.6_20230601_L1A0007312900\GF2_PMS1_E67.7_N40.6_20230601_L1A0007312900-MSS1.tiff"
    # out_img = "./fused_large_result_3.tiff"

    # pan_img = "./GF6_PMS_E59.0_N44.6_20231127_L1A1420379774\GF6_PMS_E59.0_N44.6_20231127_L1A1420379774-PAN.tiff"
    # ms_img = "./GF6_PMS_E59.0_N44.6_20231127_L1A1420379774\GF6_PMS_E59.0_N44.6_20231127_L1A1420379774-MUX.tiff"
    # out_img = "./fused_large_result_4.tiff" 
 
    gram_schmidt_fusion_with_cloud_mask(
        pan_path=pan_img,
        ms_path=ms_img,
        output_path=out_img,
        block_size=1024,
        sample_ratio=0.1,
        lower_percent=2,
        upper_percent=98,
        gamma=1.3,
        align_pan_gs1=True,
        cloud_mode='KEEP_MS',
        cloud_percentile=99
    )


    


