import threading, queue, time, os, json, datetime, fcntl
from urllib.request import urlopen
from bs4 import BeautifulSoup
import warnings
warnings.filterwarnings('ignore')


urlQueue = queue.Queue()
updateQueue = queue.Queue()

def updateNewsViewList(urlQueue):

    while True:
        try:
            # 不阻塞的讀取佇列資料
            url = urlQueue.get_nowait()
            i = urlQueue.qsize()
        except Exception as e:
            break
        #print('Current Thread Name %s, Url: %s ' % (threading.currentThread().name,

        print("正在處理: ", url)

        news_response = urlopen(url)
        news_html = BeautifulSoup(news_response)

        news_create_time = datetime.datetime.strptime(news_html.find("span", class_="info_time").text, '%Y-%m-%d %H:%M')
        now = datetime.datetime.now()
        delta = news_create_time - now

        if not delta.days < -3:
            updateQueue.put(url)


if __name__ == "__main__":
# 開啟要爬的新聞網址檔案
    while True:
        if os.path.exists("update_for_view.txt"):
            with open("update_for_view.txt", "r", encoding="utf-8") as f:
                url_list = f.read().split("\n")
            break
        else:
            time.sleep(120)

    for url in url_list:
        if url == "":
            break
        else:
            urlQueue.put(url)

    threads = []
    # 可以調節執行緒數，進而控制抓取速度
    threadNum = 2
    for i in range(0, threadNum):
        t = threading.Thread(target=updateNewsViewList, args=(urlQueue,))
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        # 多執行緒多join的情況下，依次執行各執行緒的join方法，這樣可以確保主執行緒最後退出，且各個執行緒間沒有阻塞
        t.join()

    update_view_url_list = []
    while not updateQueue.empty():
        update_view_url_list.append(updateQueue.get())

    with open("update_for_view.txt", "w", encoding="utf-8") as f:
        while True:
            try:
                # 得到file lock
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                for url in update_view_url_list:
                    f.write(str(url) + "\n")
                    # 釋放file lock
                fcntl.flock(f, fcntl.LOCK_UN)
                break
            except OSError:
                print("update_for_view.txt locked!")
            finally:
                # 釋放file lock
                fcntl.flock(f, fcntl.LOCK_UN)
