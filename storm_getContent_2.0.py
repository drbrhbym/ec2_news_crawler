# 引用相關套件
from urllib.request import urlopen
from bs4 import BeautifulSoup
import threading, queue, time, os, json, glob, datetime, fcntl
import warnings
warnings.filterwarnings('ignore')
from aws_linenotify import lineNotify


urlQueue = queue.Queue()
newsQueue = queue.Queue()


def getNewsContent(urlQueue):
    while True:
        try:
            # 不阻塞的讀取佇列資料
            news_url = urlQueue.get_nowait()
            i = urlQueue.qsize()
        except Exception as e:
            break
        #print('Current Thread Name %s, Url: %s ' % (threading.currentThread().name, news_url))

        ## 爬蟲程式內容
        # News Tag轉換表
        tag_dict = {"財經": "finance",
                    "房地產": "finance",
                    "國內": "local",
                    "國際": "international",
                    "中港澳": "international",
                    "政治": "politics",
                    "公共政策": "politics",
                    "公民運動": "politics",
                    "風生活": "life",
                    "風攝影": "life",
                    "品味生活": "life",
                    "運動": "sports",
                    "評論": "forum",
                    "軍事": "military",
                    "科技": "technology",
                    "藝文": "arts",
                    "影音": "entertainment",
                    "歷史": "history",
                    "調查": "research"}

        news_response = urlopen(news_url)
        news_html = BeautifulSoup(news_response)
        news_tag = news_html.find("a", class_="tags_link").text
        news_title = news_html.find("h1", id="article_title").text

        artical_number = news_url.split("/")[-1]
        view_response = urlopen("https://service-pvapi.storm.mg/pvapi/get_pv/" + artical_number)
        view_html = BeautifulSoup(view_response)
        news_view = json.loads(view_html.text)["total_count"]

        news_create_time = news_html.find("span", class_="info_time").text

        artical = news_html.find("div", class_="article_content_inner")
        content = []
        for p in artical.find_all("p"):
            content.append(p.text)
        news_content = "".join(content)

        news_keyword = []
        key_word = news_html.find_all("a", class_="tag tags_content")
        for word in key_word:
            news_keyword.append(word.text)

        #print("正在處理:", news_url)

        # 將新聞內容放入佇列
        try:
            newsQueue.put({"id": "storm-" + tag_dict[news_tag] + "-" + artical_number,
                           "news_link": news_url,
                           "news_title": news_title,
                           "news_create_time": news_create_time,
                           "news_content": news_content,
                           "news_keyword": news_keyword,
                           "news_tag": news_tag,
                           "news_view": [{"view": news_view, "time": news_create_time}]})
        except KeyError as e:
            lineNotify("Got KeyError: " + str(e))

        # 爲了突出效果，設定延時
        #time.sleep(1)


if __name__ == "__main__":

    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    lineNotify("Content of news started updating " + now)

    # 開啟要爬的新聞網址檔案
    while True:
        if os.path.exists("update_storm_news_url.txt"):
            with open("update_storm_news_url.txt", "r", encoding="utf-8") as f:
                url_list = f.read().split("\n")
            break
        else:
            time.sleep(120)

    if os.path.exists("update_for_view.txt"):
        view_update_url_list = url_list.copy()
        with open("update_for_view.txt", "r", encoding="utf-8") as f:
            old_view_list = f.read().split("\n")
        old_view_list.remove("")
        view_update_url_list.extend(old_view_list)
        view_update_url_list.remove("")
        with open("update_for_view.txt", "w", encoding="utf-8") as f:
            while True:
                try:
                    # 得到file lock
                    fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    for url in view_update_url_list:
                        f.write(str(url + "\n"))
                    # 釋放file lock
                    fcntl.flock(f, fcntl.LOCK_UN)
                    break
                except OSError:
                    print("update_for_view.txt locked!")
                finally:
                    # 釋放file lock
                    fcntl.flock(f, fcntl.LOCK_UN)
    else:
        with open("update_for_view.txt", "w", encoding="utf-8") as f:
            while True:
                try:
                    # 得到file lock
                    fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    for url in url_list:
                        f.write(str(url + "\n"))
                    # 釋放file lock
                    fcntl.flock(f, fcntl.LOCK_UN)
                    break
                except OSError:
                    print("update_for_view.txt locked!")
                finally:
                    # 釋放file lock
                    fcntl.flock(f, fcntl.LOCK_UN)

    # 更改檔案名字
    os.rename("update_storm_news_url.txt", "update_storm_news_url.txt.bak")
    path = './tmpfolder/*'
    r = glob.glob(path)
    for i in r:
        os.remove(i)

    # 紀錄爬蟲開始時間
    start_time = time.time()

    for url in url_list:
        if url == "":
            break
        else:
            # 將每筆新聞網址放入佇列
            urlQueue.put(url)
            #print(url)

    threads = []
    # 可以調節執行緒數，進而控制抓取速度
    threadNum = 2
    for i in range(0, threadNum):
        t = threading.Thread(target=getNewsContent, args=(urlQueue,))
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        # 多執行緒多join的情況下，依次執行各執行緒的join方法，這樣可以確保主執行緒最後退出，且各個執行緒間沒有阻塞
        t.join()


    news_list = []  # 紀錄爬回來的新聞內容
    date_list = []  # 紀錄新聞發布日期
    count = 0  # 紀錄爬了幾筆
    # 將每筆新聞從佇列拿出並放入List
    while not newsQueue.empty():
        news_list.append(newsQueue.get())

    ## 不紀錄重複的新聞發布日期
    for news in news_list:
        #print(news)
        if not news["news_create_time"].split(" ")[0] in date_list:
            date_list.append(news["news_create_time"].split(" ")[0])
        count = count + 1

    # 紀錄爬蟲結束時間
    end_time = time.time()
    print('Done, Time cost: %s ' % (end_time - start_time))

    # 紀錄存檔開始時間
    start_time = time.time()

    path = "./newsfolder"
    if not os.path.exists(path):
        os.makedirs(path)

    ## 將每筆新聞依照發布日期分類
    for date in date_list:
        date_news_list = []  # 紀錄分類過的新聞內容
        for news in news_list:
            if news["news_create_time"].split(" ")[0] == date:
                date_news_list.append(news)
        news_dict = {"date": date, "news": date_news_list}

        ## 如果檔案存在
        if os.path.exists("./newsfolder/" + date + "_storm_news.json"):
            # 開啟之前紀錄新聞內容的檔案
            with open("./newsfolder/" + date + "_storm_news.json", "r", encoding="utf-8") as f:
                file_content = json.load(f)
            # 將依照發布日期分類的新聞內容存檔
            with open("./newsfolder/" + date + "_storm_news.json", "w", encoding="utf-8") as f:
                # 將每筆新的新聞內容加入之前的紀錄
                for news in date_news_list:
                    file_content["news"].append(news)
                json.dump(file_content, f)
        ## 如果檔案不存在
        else:
            # 將依照發布日期分類的新聞內容存檔
            with open("./newsfolder/" + date + "_storm_news.json", "w", encoding="utf-8") as f:
                json.dump(news_dict, f)

    # 紀錄存檔結束時間
    end_time = time.time()
    print('Done, Time cost: %s ' % (end_time - start_time))

    # 檢查用
    # print(len(news_list))
    # print(count)

    # 紀錄刪除檔案開始時間
    start_time = time.time()

    # 使用系統指令刪除檔案
    os.remove("update_storm_news_url.txt.bak")

    # 紀錄刪除檔案結束時間
    end_time = time.time()
    print('Done, Time cost: %s ' % (end_time - start_time))

    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    lineNotify("Content of news updated completely " + now)
