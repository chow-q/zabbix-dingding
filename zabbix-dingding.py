#!/usr/bin/python3.6
# -*- coding: utf-8 -*-
import requests, time
import json, sys, re, os, logging

from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client

now_time = time.strftime("%Y-%m-%d_%H:%M")

user = ''  # 定义zabbix用户名
password = ''  # 定义zabbix用户密码
zabbixserver_url = 'http://*/zabbix/index.php'
# 定义远端的web服务器地址，将图片复制到远端的web目录下，让zabbix主机可以访问这个图片
pname_path = 'http://localhost/dingding_pic/'
# 定义获取的图片地址
graph_url = "http://*/zabbix/chart.php"
host = 'zabbixhost'


def get_itemid():
  itemid = re.search(r'ITEMID:(\d+)', sys.argv[3]).group(1)
  #  print(itemid)
  return itemid


def get_picture(itemid, pname):
  session = requests.Session()  # 创建一个session会话
  try:
    loginHeaders = {
      "Host": host,
      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"
    }
    # 构建登录所需的信息
    playLoad = {
      "name": user,
      "password": password,
      "autologin": "1",
      "enter": "Sign in",
    }

    #获取登陆后session信息
    update_cookie = session.post(url=zabbixserver_url, headers=loginHeaders, data=playLoad)

    #将获取到的cookie信息，赋值给cookie_dict
    cookie_dict = requests.utils.dict_from_cookiejar(update_cookie.cookies)

    #将获取到的zabbix的cookie更新session.cookie,用于后续的请求
    session.cookies = requests.utils.cookiejar_from_dict(cookie_dict)


    playLoad = {
      "from": "now-720m",
      "to": "now",
      "itemids[0]": itemid,
      "width": "1820",
      "height":"600",
#      "width": "700",
    }
    # 定义获取图片的参数
    graph_req = session.get(url=graph_url, params=playLoad)

    IMAGEPATH = os.path.join('/tmp/zabbix-alert-picture/', pname)
    # 将获取到的图片数据写入到文件中去
    with open(IMAGEPATH, 'wb') as f:
      f.write(graph_req.content)
    pname_url = pname_path + pname
    return pname_url
  except Exception as e:
    print(e)
    return False


# 将图片存储到cos
def upload_picture(file_path, pname):
  logging.basicConfig(level=logging.INFO, stream=sys.stdout)

  secret_id = ''  # 替换为用户的 SecretId，请登录访问管理控制台进行查看和管理，https://console.cloud.tencent.com/cam/capi
  secret_key = ''  # 替换为用户的 SecretKey，请登录访问管理控制台进行查看和管理，https://console.cloud.tencent.com/cam/capi
  region = ''  # 替换为用户的 region，已创建桶归属的region可以在控制台查看，https://console.cloud.tencent.com/cos5/bucket
  # COS支持的所有region列表参见https://cloud.tencent.com/document/product/436/6224
  token = None  # 如果使用永久密钥不需要填入token，如果使用临时密钥需要填入，临时密钥生成和使用指引参见https://cloud.tencent.com/document/product/436/14048

  config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Token=token)
  client = CosS3Client(config)

  response = client.put_object_from_local_file(
    Bucket='',
    Key=pname,
    LocalFilePath=file_path
  )


# 构造发送消息的请求
def send_msg(cos_picture,result_message):
  headers = {'Content-Type': 'application/json;charset=utf-8'}
#  print(result_message)
  data = {
    "msgtype": "markdown",
    "markdown": {
      "title": "告警",
      "text": result_message + "![screenshot](%s)" % (cos_picture)

    },
    "at": {
      "atMobiles": reminders,
      "isAtAll": False,
    },
  }
  r = requests.post(url=webhook_url, json=data, headers=headers)
#  print(r.text)
  return r

# 对报警信息进行格式化
def info_text(message):
  new_text = ""
  x = message.split('\n')
  for i in x:
    if re.search('ITEM ID', str(i)):
      pass
    else:
      new_text += "- " + str(i) + ('\n')
  print(type(new_text))
  return new_text


if __name__ == '__main__':
  # 将报警信息写入日志
  # pname = str(int(time.time())) + '.png'
  #  tupian_name = re.search(r'告警主机:(.*)', sys.argv[3]).group(1)
  pname = str(int(time.time())) + '.png'

  # title = str(sys.argv[2])
  message = str(sys.argv[3])
  result_message = info_text(message)

  # with open('/tmp/syslog.md','a') as f:
  #   f.write(title)
  #   f.write(message)
  #   f.close()
  reminders = []
  webhook_url = ""  # 钉钉机器人
  itemid = get_itemid()
  pname_url = get_picture(itemid, pname)

  with open(r'/tmp/zabbix.llllog','w') as f:
    f.write(str(pname_url))
    f.close()

  # 发送图片到cos
  file_path = r"/tmp/zabbix-alert-picture/" + pname
  upload_picture(file_path, pname)

  #腾讯云cos全路径，用于传给钉钉获取图片
  cos_picture = 'https://*.*.*.*/' + pname

 #将信息通过钉钉发送
  send_msg(cos_picture,result_message)
