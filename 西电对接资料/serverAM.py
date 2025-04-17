import asyncio
import os
import sys

from sanic import Sanic
from sanic.response import json

defdir = os.path.dirname(__file__)
sys.path.append(os.path.join(defdir[:defdir.find('Python')], 'Python'))

from ZJ_AMDP.API.mainAgricMeteorol import runAgricMeteorol

app = Sanic(name="ZJAMDPAMapp")


async def runAgricMeteorolTask(request):
    loop = asyncio.get_event_loop()
    fut = loop.run_in_executor(None, runAgricMeteorol, request)
    resp = await fut


@app.route('/AgricMeteorol/', methods=['POST'])
async def runAM(request):
    request.app.add_task(runAgricMeteorolTask(request))
    return json({'msg': 'Agricmeteorol task runs success!'})



if __name__ == '__main__':
    # app.run(host='10.135.29.244', port=8090, workers=4, debug=False)
    app.run(host='10.135.29.244', port=8091, workers=4, debug=False)


