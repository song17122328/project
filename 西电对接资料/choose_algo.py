import asyncio
import os
import sys
from sanic import Sanic
from sanic.response import json

defdir = os.path.dirname(__file__)
sys.path.append(os.path.join(defdir[:defdir.find('Python')], 'Python'))

app = Sanic(name="ZJAMDPAMapp")

async def runAgricMeteorolTask(request):
    loop = asyncio.get_event_loop()
    #fut = loop.run_in_executor(None, runAlgorithmTask, request)
    print("123456")
    runAlgorithmTask(request);
def runAlgorithmTask(request):
    """"""
    par_dict = request.json
    taskType = par_dict["taskType"]
    taskCode = par_dict["taskCode"]

#根据taskType的值调用不同的算法方法
    try:
        if taskType == "3":
            print("3")
            # mainGridClassifyStatistic(**par_dict)

        elif taskType == "2":
            # gridStat(**par_dict)
            print("2")

        elif taskType == "1":

            print("1")
        elif taskType == "4":
            print("4")
        else:
            print("error")

    except  Exception as error:
        print("error-1")

@app.route('/Algorithm/', methods=['POST'])
async def runAM(request):
    request.app.add_task(runAgricMeteorolTask(request))
    return json({'msg': 'Algorithm task runs success!'})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8091, workers=4, debug=False)