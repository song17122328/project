import os
import datetime

import copy
from ZJ_AMDP.AgricMeteorol.MainFunction.main_grid_classiscify_statistic import mainGridClassifyStatistic
from ZJ_AMDP.AgricMeteorol.MainFunction.main_interpolation_zonestat_xyz import gridStat
from ZJ_AMDP.AgricMeteorol.Algorithm.BasicTool.config.message import msg
from ZJ_AMDP.AgricMeteorol.MainFunction.main_numerical_correction import mainNumericalCorrection
from ZJ_AMDP.RabbitMQ.ProducerSendMsg import sendMessage
from ZJ_AMDP.AgricMeteorol.MainFunction.main_index import runStation, runGrid



def runAgricMeteorol(request):
    """"""
    par_dict = request.json
    taskType = par_dict["taskType"]
    taskCode = par_dict["taskCode"]
    msg_ = msg()

    try:
        if taskType == "3":
            mainGridClassifyStatistic(**par_dict)

        elif taskType == "2":
            gridStat(**par_dict)

        elif taskType == "1":
            runGrid(**par_dict)
            runStation(**par_dict)

        elif taskType == "4":
            mainNumericalCorrection(**par_dict)

        else:
            # 发送错误消息
            msg_["taskCode"] = par_dict["taskCode"]
            msg_["indexCode"] = par_dict["indexCode"]
            msg_["taskType"] = par_dict["taskType"]
            msg_["msg"] = "Unsupported Task Type! TaskType: {}, TaskCode: {}.".format(taskType, taskCode)
            sendMessage(msg_)

    except  Exception as error:
        msg_["taskCode"] = par_dict["taskCode"]
        msg_["indexCode"] = par_dict["indexCode"]
        msg_["taskType"] = par_dict["taskType"]
        msg_["msg"] = str(error)
        sendMessage(msg_)
























