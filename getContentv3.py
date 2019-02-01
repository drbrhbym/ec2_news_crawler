# 引用相關套件
from urllib.request import urlopen
from bs4 import BeautifulSoup
import threading, queue, time, os, json, subprocess, fcntl

# <!-- For MAC電腦
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
# -->

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

        ## 開始爬蟲
        try:
            news_response = urlopen(news_url)
            responseCode = news_response.getcode()
        except Exception as e:
            continue
        if responseCode == 200:
            ## 爬蟲程式內容
            # News Tag轉換表
            tag_dict = {"焦點": "recommend",
                        "熱門": "hot",
                        "微視蘋": "micromovie",
                        "娛樂": "entertainment",
                        "時尚": "entertainment",
                        "財經": "finance",
                        "地產": "finance",
                        "社會": "local",
                        "國際": "international",
                        "政治": "politics",
                        "生活": "life",
                        "3C": "gadget",
                        "車市": "gadget",
                        "吃喝玩樂": "lifestyle",
                        "副刊": "lifestyle",
                        "體育": "sports",
                        "辣蘋道": "girl",
                        "論壇": "forum",
                        "壹週刊": "nextmag"}

            news_html = BeautifulSoup(news_response, features="html5lib") # features="html5lib" for Windows
            news = news_html.find("article", class_="ndArticle_leftColumn")
            news_title = news.find("h1").text
            news_view = news.find("div", class_="ndArticle_view")
            # 沒有觀看數就設定為0
            if news_view == None:
                news_view = None
            else:
                news_view = news_view.text
            news_create_time = news.find("div", class_="ndArticle_creat").text.split("：")[1].replace("/", "-")
            news_content = news.find("article", class_="ndArticle_content").find("p").text
            news_keyword = news.find("div", class_="ndgKeyword")
            keyword_list = [] # 紀錄此新聞的關鍵字
            if not news_keyword == None:
                news_keyword = news_keyword.find_all("a")
                for keyword in news_keyword:
                    keyword_list.append(keyword.text)
            news_tag = news.find("div", class_="ndArticle_moreNewlist").find("h2").text.replace("《", "").replace("》",
                                                                                                                 "")
            # 將新聞內容放入佇列
            newsQueue.put({"id": "apple-" + tag_dict[news_tag] + "-" + news_url.split("/")[-2],
                           "news_link": news_url,
                           "news_title": news_title,
                           "news_create_time": news_create_time,
                           "news_content": news_content,
                           "news_keyword": keyword_list,
                           "news_tag": news_tag,
                           "news_view": [{"view": news_view, "time": news_create_time}]})

            # 爲了突出效果，設定延時
            time.sleep(1)

if __name__ == "__main__":
    # 開啟要爬的新聞網址檔案
    while True:
        if os.path.exists("update_apple_news_url.txt"):
            with open("update_apple_news_url.txt", "r", encoding="utf-8") as f:
                while True:
                    try:
                        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        url_list = f.read().split("\n")
                        fcntl.flock(f, fcntl.LOCK_UN)
                        break
                    except OSError:
                        print("update_apple_news_url.txt locked!")
                    finally:
                        fcntl.flock(f, fcntl.LOCK_UN)
            break
        else:
            time.sleep(30)

    # 使用系統指令更改檔案名字
    subprocess.run(["mv", "update_apple_news_url.txt", "update_apple_news_url.txt.bak"])

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
    threadNum = 10
    for i in range(0, threadNum):
        t = threading.Thread(target=getNewsContent, args=(urlQueue, ))
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        # 多執行緒多join的情況下，依次執行各執行緒的join方法，這樣可以確保主執行緒最後退出，且各個執行緒間沒有阻塞
        t.join()

    news_list = [] # 紀錄爬回來的新聞內容
    date_list = [] # 紀錄新聞發布日期
    count = 0 # 紀錄爬了幾筆
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

    ## 將每筆新聞依照發布日期分類
    for date in date_list:
        date_news_list = [] # 紀錄分類過的新聞內容
        for news in news_list:
            if news["news_create_time"].split(" ")[0] == date:
                date_news_list.append(news)
        news_dict = {"date": date, "news": date_news_list}

        ## 如果檔案存在
        if os.path.exists(date + "_apple_news.json"):
            # 開啟之前紀錄新聞內容的檔案
            with open(date + "_apple_news.json", "r", encoding="utf-8") as f:
                file_content = json.load(f)
            # 將依照發布日期分類的新聞內容存檔
            with open(date + "_apple_news.json", "w", encoding="utf-8") as f:
                # 將每筆新的新聞內容加入之前的紀錄
                for news in date_news_list:
                    file_content["news"].append(news)
                json.dump(file_content, f)
        ## 如果檔案不存在
        else:
            # 將依照發布日期分類的新聞內容存檔
            with open(date + "_apple_news.json", "w", encoding="utf-8") as f:
                json.dump(news_dict, f)

    # 紀錄存檔結束時間
    end_time = time.time()
    print('Done, Time cost: %s ' % (end_time - start_time))

    # 檢查用
    #print(len(news_list))
    #print(count)

    # 紀錄刪除檔案開始時間
    start_time = time.time()

    # 使用系統指令刪除檔案
    subprocess.run(["rm", "update_apple_news_url.txt.bak"])

    # 紀錄刪除檔案結束時間
    end_time = time.time()
    print('Done, Time cost: %s ' % (end_time - start_time))
