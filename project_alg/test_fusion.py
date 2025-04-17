import requests

url = 'http://127.0.0.1:8091/Algorithm/'

payload = {
    "taskType": "3",
    "taskCode": "testcode01",
    "taskFilePath": {
        "panPath": "/data/hanxueyuan/fuse_pan_mss/GF2_PMS1_E66.9_N41.0_20211211_L1A0006129384/GF2_PMS1_E66.9_N41.0_20211211_L1A0006129384-PAN1.tiff",
        "msPath": "/data/hanxueyuan/fuse_pan_mss/GF2_PMS1_E66.9_N41.0_20211211_L1A0006129384/GF2_PMS1_E66.9_N41.0_20211211_L1A0006129384-MSS1.tiff",
        "outputPath": "/data/hanxueyuan/fuse_pan_mss/project/fused_result.tiff"
    }
}

response = requests.post(url, json=payload)
print(response.json())

