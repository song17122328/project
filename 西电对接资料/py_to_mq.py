import pika
import json

def  sendMsgToMq(self):
     #设置RabbitMQ连接参数(账号密码)
    credentials = pika.PlainCredentials('guest', 'guest')
    # 更改为自己的服务器地址
    parameters = pika.ConnectionParameters('192.168.1.3', 5672, '/', credentials)

    # 建立到RabbitMQ的连接
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    # 声明队列，确保它存在
    exchange_name = 'ExchangeSyntheticalA_P'  
    queue_name = 'alg_result_p'  # 队列名字
    channel.queue_declare(queue=queue_name, durable=True, passive=True)

    # 要发送的消息 格式如下 flag--处理状态  msg--处理消息   result--返回结果（包含tif和csv）  algType--算法类型（1，2，3...代表不同的算法） classifyId--任务id（入参会传）
    crawled_data = {"flag":true,"msg":"处理成功","result":{"tif":"\\\\192.168.1.209\\data\\mnt\\algResult\\trqs\\slqs\\dataResult\\2023_slqs\\Uzbekistan_2023_GF6_Water_Erosion_rank.tif","csv":"\\\\192.168.1.209\\data\\mnt\\algResult\\trqs\\slqs\\dataResult\\2023_slqs\\Uzbekistan_2023_GF6_Water_Erosion_rank.csv","png":"\\\\192.168.1.209\\data\\mnt\\algResult\\trqs\\slqs\\dataResult\\2023_slqs\\Uzbekistan_2023_GF6_Water_Erosion_rank.png"},"algType":"11","classifyId":"16"}

    # 将字典转换为JSON字符串
    crawled_data_json = json.dumps(crawled_data)

    # 发布消息到指定队列
    channel.basic_publish(exchange=exchange_name,
                          routing_key=queue_name,
                          body=crawled_data_json.encode("utf-8"),  # 要传字节
                          properties=pika.BasicProperties(
                              delivery_mode=2,  # 使消息持久化
                          ))
    print(crawled_data)

    # 关闭连接
    connection.close()