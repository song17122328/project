import pika
import json
import datetime


def send_result_to_mq(tif_path, png_path, csv_path, task_type, isDefault):
    if isDefault == "true":
        print("程序解析失败，使用默认数据发送至RabbitMQ")

    credentials = pika.PlainCredentials('guest', 'guest')
    parameters = pika.ConnectionParameters('localhost', 5672, '/', credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    # 声明 Exchange 和 Queue
    channel.exchange_declare(
        exchange='ExchangeSyntheticalA_P',
        exchange_type='direct',
        durable=True
    )
    channel.queue_declare(queue='alg_result_p', durable=True)
    channel.queue_bind(
        queue='alg_result_p',
        exchange='ExchangeSyntheticalA_P',
        routing_key='alg_result_p'
    )

    # 构造消息
    payload = {
        "taskType": str(task_type),
        "csvFilePath": csv_path or "",
        "tifFilePath": tif_path or "",
        "pngFilePath": png_path or "",
        "dataTime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # 发送消息
    channel.basic_publish(
        exchange='ExchangeSyntheticalA_P',
        routing_key='alg_result_p',
        body=json.dumps(payload).encode("utf-8"),
        properties=pika.BasicProperties(delivery_mode=2)  # 持久化消息
    )

    print("已推送消息至 MQ:", payload)
    connection.close()


# 测试调用
send_result_to_mq("test.tif", "test.png", "data.csv", "test_task", "false")
