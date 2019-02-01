# 引用相關套件
from urllib.request import urlopen
from bs4 import BeautifulSoup
import threading, queue, time, os, json, datetime
import warnings
warnings.filterwarnings('ignore')



urlQueue = queue.Queue()
viewQueue = queue.Queue()

def getNewsView(urlQueue):
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

        artical_number = news_url.split("/")[-1]
        view_response = urlopen("https://service-pvapi.storm.mg/pvapi/get_pv/" + artical_number)
        view_html = BeautifulSoup(view_response)
        news_view = json.loads(view_html.text)["total_count"]

        news_tag = news_html.find("a", class_="tags_link").text

        print("正在處理:", news_url)

        # 將新聞觀看數放入佇列
        viewQueue.put({"id": "storm-" + tag_dict[news_tag] + "-" + artical_number,
                       "news_link": news_url,
                       "view": news_view,
                       "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")})


        # 爲了突出效果，設定延時
        time.sleep(1)

if __name__ == "__main__":
    # 開啟要爬的新聞網址檔案
    while True:
        if os.path.exists("storm_news_url.txt"):
            with open("storm_news_url.txt", "r", encoding="utf-8") as f:
                url_list = f.read().split("\n")
                #print(url_list)
            break
        else:
            time.sleep(120)

    # 紀錄爬蟲開始時間
    start_time = time.time()

    for url in url_list:
        if url == "":
            break
        else:
            urlQueue.put(url)
            # print(url)

    threads = []
    # 可以調節執行緒數，進而控制抓取速度
    threadNum = 10
    for i in range(0, threadNum):
        t = threading.Thread(target=getNewsView, args=(urlQueue,))
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        # 多執行緒多join的情況下，依次執行各執行緒的join方法，這樣可以確保主執行緒最後退出，且各個執行緒間沒有阻塞
        t.join()

    view_list = []  # 紀錄爬回來的新聞觀看數
    date_list = []  # 紀錄爬取觀看數的日期
    count = 0  # 紀錄爬了幾筆
    # 將每筆觀看數從佇列拿出並放入List
    while not viewQueue.empty():
        view_list.append(viewQueue.get())

    ## 不紀錄重複的爬取觀看數的日期
    for view in view_list:
        # print(view)
        if not view["time"].split(" ")[0] in date_list:
            date_list.append(view["time"].split(" ")[0])
        count = count + 1

    # 紀錄爬蟲結束時間
    end_time = time.time()
    print('Done, Time cost: %s ' % (end_time - start_time))

    # 紀錄存檔開始時間
    start_time = time.time()

    path = "./viewsfolder"
    if not os.path.exists(path):
        os.makedirs(path)

    ## 將每筆觀看數依照爬取日期分類
    for date in date_list:
        date_view_list = []  # 紀錄分類過的新聞觀看數
        for view in view_list:
            if view["time"].split(" ")[0] == date:
                date_view_list.append(view)
        view_dict = {"date": date, "views": date_view_list}

        ## 如果檔案存在
        if os.path.exists(date + "_storm_news_view.json"):
            # 開啟之前紀錄新聞觀看數的檔案
            with open("./viewsfolder/" + date + "_storm_news_view.json", "r", encoding="utf-8") as f:
                file_content = json.load(f)
            # 將依照爬取日期分類的新聞觀看數存檔
            with open("./viewsfolder/" + date + "_storm_news_view.json", "w", encoding="utf-8") as f:
                # 將每筆新的新聞觀看數加入之前的紀錄
                for view in date_view_list:
                    file_content["views"].append(view)
                json.dump(file_content, f)
        ## 如果檔案不存在
        else:
            # 將依照爬取日期分類的新聞觀看數存檔
            with open("./viewsfolder/" + date + "_storm_news_view.json", "w", encoding="utf-8") as f:
                json.dump(view_dict, f)

    # 紀錄存檔結束時間
    end_time = time.time()
    print('Done, Time cost: %s ' % (end_time - start_time))

    # 檢查用
    # print(len(view_list))
    # print(count)