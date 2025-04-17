from batch_fusion import gram_schmidt_fusion_with_cloud_mask
import os
import shutil

def run_fusion(params):
    print("进入函数 run_fusion,参数是",params)
    pan_path = params["panPath"]
    ms_path = params["msPath"]
    output_dir = os.path.dirname(ms_path)
    output_path = os.path.join(output_dir, "fused_result.tiff")

    # 调用融合算法
    gram_schmidt_fusion_with_cloud_mask(
        pan_path=pan_path,
        ms_path=ms_path,
        output_path=output_path
    )

    # 复制 RPC 文件（如果存在）
    rpb_path = pan_path.replace(".tiff", ".rpb")
    if os.path.exists(rpb_path):
        fused_rpb = output_path.replace(".tiff", ".rpb")
        shutil.copyfile(rpb_path, fused_rpb)

    return {
        "tif": output_path.replace("/", "\\"),
        "png": None
    }
