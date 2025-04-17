import asyncio
from sanic import Sanic
from sanic.response import json
from fusion import run_fusion
from detect_green_wetland import run_detection
from send_mq import send_result_to_mq
import os
import traceback
from datetime import datetime
from zip import extract_archive
from chooseFile import filter_and_copy_files

app = Sanic(name="ZJAMDPAMapp")
app.config.KEEP_ALIVE_TIMEOUT = 30


async def runAgricMeteorolTask(request):
    await run_algorithm_task(request)


async def run_algorithm_task(request):
    data = request.json
    task_type = data.get("taskType")
    inputFile = data.get("inputFile")
    outputDir = data.get("outputDir")

    print(f"接收到任务: taskType={task_type}, inputFile={inputFile}, outputDir={outputDir}")

    # 默认的模拟数据
    DEFAULT_SIMULATED_DATA = {
        "tif": f"{outputDir}/result.tif",
        "png": f"{outputDir}/result.png",
        "csv": f"{outputDir}/result.csv",
        "defaults": "false"
    }
    output_paths = DEFAULT_SIMULATED_DATA  # 初始化为模拟数据

    # if task_type == "3":
    #     output_paths = run_fusion(inputFile)  # 可能抛出异常
    if task_type == "4":
        # output_paths = run_detection(inputFile)  # 可能抛出异常
        file_list = extract_archive(inputFile, "./resource/data")
        dir = file_list[0]
        outdir = "targetMSSTIF"
        # print(dir)
        suffix = "MSS.tif"
        outdir = "./resource/data/" + outdir + "_need"

        matched_files = filter_and_copy_files(dir, outdir, suffix)

        TiffFile = matched_files[0]
        TiffFile = TiffFile.replace("\\", "/")
        print(f"地址是{TiffFile}")
        res = run_detection(TiffFile)
        res['tif'] = TiffFile
        print(f"得到的结果是:{res}")



    else:
        return json({"msg": "无效的 taskType", "code": "400"})

    # 无论成功或失败，都发送到 RabbitMQ
    send_result_to_mq(
        tif_path=output_paths.get("tif"),
        png_path=output_paths.get("png"),
        csv_path=output_paths.get("csv"),
        task_type=task_type,
        isDefault=output_paths.get("defaults"),
    )

    return json({"msg": "处理完成（可能使用了模拟数据）", "code": "200"})


# async def run_algorithm_task(request):
#     try:
#
#         data = request.json
#         task_type = data.get("taskType")
#         inputFile = data.get("inputFile")
#         outputDir = data.get("outputDir")
#
#         print(f"接收到任务: taskType={task_type}, inputFile={inputFile}, outputDir={outputDir}")
#
#         # 默认的模拟数据
#         DEFAULT_SIMULATED_DATA = {
#             "tif": f"{outputDir}/result.tif",
#             "png": f"{outputDir}/result.png",
#             "csv": f"{outputDir}/result.csv",
#             "defaults": "false"
#         }
#         output_paths = DEFAULT_SIMULATED_DATA  # 初始化为模拟数据
#
#         try:
#             # if task_type == "3":
#             #     output_paths = run_fusion(inputFile)  # 可能抛出异常
#             if task_type == "4":
#                 # output_paths = run_detection(inputFile)  # 可能抛出异常
#                 file_list = extract_archive(inputFile, "./resource/data")
#                 dir = file_list[0]
#                 outdir = "targetMSSTIF"
#                 # print(dir)
#                 suffix = "MSS.tif"
#                 outdir = "./resource/data/" + outdir + "_need"
#
#                 matched_files = filter_and_copy_files(dir, outdir, suffix)
#
#                 TiffFile = matched_files[0]
#                 TiffFile=TiffFile.replace("\\", "/")
#                 print(f"地址是{TiffFile}")
#                 res = run_detection(TiffFile)
#                 print(f"得到的结果是:{res}")
#
#
#
#             else:
#                 return json({"msg": "无效的 taskType", "code": "400"})
#         except Exception as e:
#             print(f"任务执行出错，发送默认数据，错误原因: {e},")
#             # 使用模拟数据继续执行
#             output_paths = DEFAULT_SIMULATED_DATA
#             output_paths["defaults"] = "true"
#
#         # 无论成功或失败，都发送到 RabbitMQ
#         send_result_to_mq(
#             tif_path=output_paths.get("tif"),
#             png_path=output_paths.get("png"),
#             csv_path=output_paths.get("csv"),
#             task_type=task_type,
#             isDefault=output_paths.get("defaults"),
#         )
#
#         return json({"msg": "处理完成（可能使用了模拟数据）", "code": "200"})
#
#     except Exception as e:
#         print(f"全局异常捕获: {e}")
#         return json({"msg": "服务器内部错误", "code": "500"})


# async def run_algorithm_task(request):
#     try:
#         data = request.json
#         # print("打印输出请求",request)
#         # print("打印request.json", request.json)
#         task_type = data.get("taskType")
#         task_code = data.get("taskCode")  # 可用于日志或文件命名
#         task_file_path = data.get("taskFilePath")  # 统一输入路径
#         # classify_id = data.get("classifyId", "0000")  # 可选字段
#         # alg_type = data.get("algType", task_type)  # 默认以 task_type 作为 alg_type
#
#         print(f"接收到任务: taskType={task_type}, code={task_code}")
#         print(f"输入路径: {task_file_path}")
#
#         output_paths = {}
#
#         if task_type == "3":
#             print(f"task_type={task_type}")
#             output_paths = run_fusion(task_file_path)
#         elif task_type == "4":
#             print(f"task_type={task_type}")
#             output_paths = run_detection(task_file_path)
#         else:
#             return json({"msg": "无效的 taskType", "code": "400"})
#         print("接受状态码")
#         # 成功后上传结果到 MQ
#         send_result_to_mq(
#             tif_path=output_paths.get("tif"),
#             png_path=output_paths.get("png"),
#             csv_path=output_paths.get("csv"),  # 若没有传 None
#             task_type=task_type
#         )
#
#
#         return json({"msg": "处理成功", "code": "200"})
#
#     except Exception as e:
#         print("处理异常：", str(e))
#         traceback.print_exc()
#         return json({"msg": "处理失败", "code": "500"})

@app.route("/Algorithm/", methods=["POST"])
async def run_api(request):
    # print("接受到参数")
    # res=run_algorithm_task(request)
    request.app.add_task(run_algorithm_task(request))
    return json({"msg": "任务开始执行"})


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8091, workers=1, debug=True)
