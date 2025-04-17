from send_mq import send_result_to_mq

if __name__ == "__main__":
    send_result_to_mq(
        tif_path="/data/hanxueyuan/fuse_pan_mss/GF2_PMS1_E66.9_N41.0_20211211_L1A0006129384/fused_result.tiff",
        png_path=None,
        csv_path=None,
        task_type="3"
    )
