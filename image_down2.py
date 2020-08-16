import urllib # 爬虫必备
import requests # 爬虫必备
import os # 系统
import re # 系统
import sys # 系统
import time # 系统
import threading #  线程
from datetime import datetime as dt # 本机时间
from multiprocessing.dummy import Pool # 多线程和进程
from multiprocessing import Queue # 多线程 队列

# 类名与文件名相同
class BaiduImgDownloader(object):


    # 百度URL 解码网址用的映射表
    str_table = {
        '_z2C$q': ':',
        '_z&e3B': '.',
        'AzdH3F': '/'
    }

    char_table = {
        'w': 'a',
        'k': 'b',
        'v': 'c',
        '1': 'd',
        'j': 'e',
        'u': 'f',
        '2': 'g',
        'i': 'h',
        't': 'i',
        '3': 'j',
        'h': 'k',
        's': 'l',
        '4': 'm',
        'g': 'n',
        '5': 'o',
        'r': 'p',
        'q': 'q',
        '6': 'r',
        'f': 's',
        'p': 't',
        '7': 'u',
        'e': 'v',
        'o': 'w',
        '8': '1',
        'd': '2',
        'n': '3',
        '9': '4',
        'c': '5',
        'm': '6',
        '0': '7',
        'b': '8',
        'l': '9',
        'a': '0'
    }

    # 目标对象URL
    re_objURL = re.compile(r'"objURL":"(.*?)".*?"type":"(.*?)"')
    re_downNum = re.compile(r"已下载\s(\d+)\s张图片") # 控制台打印

    # PC浏览器头文件
    # 伪装浏览器
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.71 Safari/537.36",
        "Accept-Encoding": "gzip, deflate, sdch",
    }

    # Python中 __init__ 方法用 self. 初始化对象
    def __init__(self, word, dirpath=None, processNum=30):

        # 查询 不允许有空格字符
        if " " in word:
            raise AttributeError("本脚本仅支持单个关键字")

        # word是用户输入的关键字
        self.word = word
        self.char_table = {ord(key): ord(value)
                           for key, value in BaiduImgDownloader.char_table.items()}

        # 初始化若干文件保存默认路径

        # Python3 中 os.path.join(path1[, path2[, ...]])
        # sys.path[0] 是本文件所在路径
        # dirpath 是图片下载保存路径
        if not dirpath:
            dirpath = r'C:\Users\wangyang\Desktop\pigpick3'
        self.dirpath = dirpath

        # jsonUrlFile 是解析完成的Url文件
        self.jsonUrlFile = os.path.join(sys.path[0], 'jsonUrl.txt')
        self.logFile = os.path.join(sys.path[0], 'logInfo.txt')
        self.errorFile = os.path.join(sys.path[0], 'errorUrl.txt')

        # 如果有错误文件就删除
        if os.path.exists(self.errorFile):
            os.remove(self.errorFile)

        # 如果没有路径就添加
        if not os.path.exists(self.dirpath):
            os.mkdir(self.dirpath)

        # 初始化线程池
        # 线程数量为30
        self.pool = Pool(30)

        # 初始化 session
        # 处理Cookies
        # cookies是某些网站为了辨别用户身份、进行session跟踪而储存在用户本地终端上的数据(通常经过加密)
        # 会话对象requests.Session能够跨请求地保持某些参数，比如cookies
        self.session = requests.Session()

        # 初始化 session.headers 对象，调用自身headers变量
        self.session.headers = BaiduImgDownloader.headers

        # 初始化 队列 对象
        # 多线程编程的 先进先出 的数据结构
        # 若队列空返回Ture 否则False
        self.queue = Queue()

        # 初始化 消息队列 对象
        self.messageQueue = Queue()

        # 初始化 图片编号 对象
        self.index = 0

        # 初始化 下载提示 下载几张图片提示一次
        self.promptNum = 10

        # 初始化 互斥锁 对象
        # 线程 相互独立， 但 进程 中的资源是共享的
        # 互斥锁 使线程同步，保证多个线程安全访问竞争资源
        # 互斥锁 原理：
        #   互斥锁为资源引入一个状态：锁定/非锁定。
        #   某个线程要更改共享数据时，先将其锁定，
        #   此时资源的状态为“锁定”，其他线程不能更改；
        #   直到该线程释放资源，将资源的状态变成“非锁定”，其他的线程才能再次锁定该资源。
        #   互斥锁保证了每次只有一个线程进行写入操作，从而保证了多线程情况下数据的正确性。
        # threading包 中定义了Lock类，可以方便的处理锁定
        self.lock = threading.Lock()

        # 初始化 延迟 对象 网络请求太频繁会被封
        self.delay = 1.5

        # 初始化 队列结束 对象
        self.QUIT = "QUIT"

        # 控制塔输出**字符
        self.printPrefix = "**"

    # 方法一 start方法
    def start(self):

        # 控制台输出线程 Thread类表示在单独的控制线程中运行的活动
        # 传递 回调对象 给对象t
        # class Thread(group=None, target=None, name=None, args=(), kwargs={})
        # 这里的 target 是被 run()方法调用的回调对象
        t = threading.Thread(target=self.__log)

        # 设置为 守护线程
        # Thread.setDaemon(false)设置为用户线程；Thread.setDaemon(true)设置为守护线程
        # 调用b.setDaemaon(True)，则主线程结束时，会把子线程B也杀死
        t.setDaemon(True)

        # 线程开始
        t.start()

        # 消息队列进行打印
        self.messageQueue.put(self.printPrefix + "脚本开始执行")

        # 获取当前时间
        start_time = dt.now()

        # 获取百度图片Urls
        urls = self.__buildUrls()
        self.messageQueue.put(self.printPrefix + "已获取 %s 个Json请求网址" % len(urls))

        # 解析出所有图片网址，该方法会阻塞直到任务完成
        self.pool.map(self.__resolveImgUrl, urls)

        # 当有返回队列则传递图片url
        while self.queue.qsize():

            # Queue.get 是从队列中获取任务，并在队列中移除任务
            imgs = self.queue.get()

            # 进程池的使用有四种方式
            # apply_async、apply、map_async、map
            # apply_async和map_async为异步进程
            # 启动进程函数之后会继续执行后续的代码不用等待进程函数返回
            self.pool.map_async(self.__downImg, imgs)

        # 关闭进程池（pool）
        self.pool.close()

        # 主进程阻塞等待子进程的退出，join方法必须在close或terminate之后使用
        self.pool.join()

        # 消息打印
        self.messageQueue.put(self.printPrefix + "下载完成！已下载 %s 张图片，总用时 %s" %
                              (self.index, dt.now() - start_time))
        self.messageQueue.put(self.printPrefix + "请到 %s 查看结果！" % self.dirpath)
        self.messageQueue.put(self.printPrefix + "错误信息保存在 %s" % self.errorFile)
        self.messageQueue.put(self.QUIT)

    # 方法二 日志读写方法 控制台输出 加锁以免被多线程打乱
    def __log(self):

        # with open ... as ... 方法读文件
        # 打开 self.logFile 文件，读写方式是 "w"， 编码格式是 "utf-8" 传递给对象 f
        with open(self.logFile, "w", encoding = "utf-8") as f:

            # 程序不停 打印停止
            while True:
                message = self.messageQueue.get()
                if message == self.QUIT:
                    break

                # 打印时间
                message = str(dt.now()) + " " + message
                if self.printPrefix  in message:
                    print(message)
                elif "已下载" in message:
                    # 下载N张图片提示一次
                    downNum = self.re_downNum.findall(message)
                    if downNum and int(downNum[0]) % self.promptNum == 0:
                        print(message)

                # 写入logFile
                f.write(message + '\n')

                # 清空缓存，防止内存溢出
                f.flush()

    # 方法三 文件编号
    def __getIndex(self):

        # 获得线程锁
        self.lock.acquire()

        # 返回当前线程的 index 再自增
        try:
            return self.index
        finally:
            self.index += 1

            # 释放线程
            self.lock.release()

    # 方法四 解码图片URL
    def decode(self, url):

        """解码图片URL
        大佬示例：
        解码前：
        ippr_z2C$qAzdH3FAzdH3Ffl_z&e3Bftgwt42_z&e3BvgAzdH3F4omlaAzdH3Faa8W3ZyEpymRmx3Y1p7bb&mla
        解码后：
        http://s9.sinaimg.cn/mw690/001WjZyEty6R6xjYdtu88&690
        """

        # 先替换字符串
        # 使用 str_table 对象解码
        for key, value in self.str_table.items():

            # 使用Python3的替换方法 replace()
            # 把所有key值 替换为 value
            url = url.replace(key, value)

        # 再替换剩下的字符
        # 使用 char_table 对象解码  把url中出现在char_table中的值都替换
        return url.translate(self.char_table)

    # 方法五 发送请求给百度图片并拿到图片url
    def __buildUrls(self):

        """json请求网址生成器"""

        # urllib库中的parse类下的quote方法用于转码特殊字符
        # 主要为 “;” | “/” | “?” | “:” | “@” | “&” | “=” | “+” |”$” | “,”
        word = urllib.parse.quote(self.word)

        # 把 word 塞到下面的URL中
        url = r"http://image.baidu.com/search/acjson?tn=resultjson_com&ipn=rj&ct=201326592&fp=result&queryWord={word}&cl=2&lm=-1&ie=utf-8&oe=utf-8&st=-1&ic=0&word={word}&face=0&istype=2nc=1&pn={pn}&rn=60"

        # 延时模拟人
        time.sleep(self.delay)

        # 拿到utf-8格式的网页数据
        html = self.session.get(url.format(word=word, pn=0), timeout = 15).content.decode('utf-8')

        # re.findall()方法是正则表达式中的常用方法
        # 返回html页面中的匹配值
        results = re.findall(r'"displayNum":(\d+),', html)
        maxNum = int(results[0]) if results else 0
        urls = [url.format(word=word, pn=x)
                for x in range(0, maxNum + 1, 60)]

        # 把jsonUrl写进文件
        with open(self.jsonUrlFile, "w", encoding="utf-8") as f:
            for url in urls:
                f.write(url + "\n")
        return urls

    # 方法六 解析图片URL
    def __resolveImgUrl(self, url):

        """从指定网页中解析出图片URL"""

        time.sleep(self.delay)
        html = self.session.get(url, timeout = 15).content.decode('utf-8')

        # 获取目标的URL，这里的re_objURL是类变量
        datas = self.re_objURL.findall(html)
        imgs = [Image(self.decode(x[0]), x[1]) for x in datas]
        self.messageQueue.put(self.printPrefix + "已解析出 %s 个图片网址" % len(imgs))

        # 把imgs对象插入队列中
        self.queue.put(imgs)

    # 方法七 下载图片
    def __downImg(self, img):

        """下载单张图片，传入的是Image对象"""

        # img是方法参数，这里是拿到img对象的url
        imgUrl = img.url

        # self.messageQueue.put("线程 %s 正在下载 %s " %
        #          (threading.current_thread().name, imgUrl))
        try:
            time.sleep(self.delay)
            res = self.session.get(imgUrl, timeout = 15)
            message = None

            # 如果页面未报错就打印 = =。
            if str(res.status_code)[0] == "4":
                message = "\n%s： %s" % (res.status_code, imgUrl)
            elif "text/html" in res.headers["Content-Type"]:
                message = "\n无法打开图片： %s" % imgUrl
        except Exception as e:
            message = "\n抛出异常： %s\n%s" % (imgUrl, str(e))

        # 输出控制台信息
        finally:
            if message:
                self.messageQueue.put(message)
                self.__saveError(message)
                return

        index = self.__getIndex()
        # index从0开始
        self.messageQueue.put("已下载 %s 张图片：%s" % (index + 1, imgUrl))
        filename = os.path.join(self.dirpath, str(index) + "." + img.type)

        # 这里就是下载图片，把res的内容存入index命名的文件
        with open(filename, "wb") as f:
            f.write(res.content)


    # 方法八 保存错误日志
    def __saveError(self, message):
        self.lock.acquire()
        try:
            with open(self.errorFile, "a", encoding="utf-8") as f:
                f.write(message)
        finally:
            self.lock.release()


# 图片类
class Image(object):

    # 构建图片类的默认对象
    def __init__(self, url, type):
        super(Image, self).__init__()
        self.url = url
        self.type = type

# 主函数
if __name__ == '__main__':


    print("欢迎使用百度图片下载脚本！\n 程序很简单，一定要看懂！\n 仅支持单个关键词。\n 最后更新为2018-05-11")
    print("下载结果保存在：桌面的pigpick3路径下")
    print("=" * 50)

    word = input("请输入你要下载的图片关键词：\n")

    # 转到Baidu.....der类的 __init__ 方法
    down = BaiduImgDownloader(word)

    # 开始程序
    down.start()