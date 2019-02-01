# 引用相關套件
from urllib.request import urlopen
from bs4 import BeautifulSoup
import time, os, fcntl

# <!-- For MAC電腦
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
# -->

if __name__ == "__main__":
    # 紀錄爬蟲開始時間
    start_time = time.time()

    update_url_list = [] # 紀錄爬回來的各篇新聞網址
    count = 0 # 紀錄爬了幾筆
    page = 1 # 從蘋果即時新聞第一頁開始
    ## 開始爬蟲
    while True:
        url = "https://tw.appledaily.com/new/realtime/" + str(page)
        #print("處理頁面：", url)
        page_response = urlopen(url)
        page_html = BeautifulSoup(page_response, features="html5lib") # features="html5lib" for Windows
        # 結束爬蟲
        if page_html.find("script").text == 'alert("網址不存在 !");location.href="/";':
            break

        for page_news in page_html.find_all("li", class_="rtddt"):
            news_url = page_news.find("a")["href"]
            # 不紀錄重複的新聞網址
            if not news_url in update_url_list:
                update_url_list.append(news_url)
            count = count + 1
        page = page + 1

    # 紀錄爬蟲結束時間
    end_time = time.time()
    print('Get url done, Time cost: %s ' % (end_time - start_time))

    # 紀錄存檔開始時間
    start_time = time.time()

    old_url_list = [] # 紀錄之前爬過的新聞網址
    # 開啟紀錄全部新聞網址的檔案
    if os.path.exists("apple_news_url.txt"):
        with open("apple_news_url.txt", "r", encoding="utf-8") as f:
            old_url_list = f.read().split("\n")
        old_url_list.remove("")

    url_list = [] # 紀錄更新的新聞網址
    # 不記錄重複的新聞網址
    for url in update_url_list:
        if not url in old_url_list:
            url_list.append(url)
    #print("url_list =", url_list)
    #print(len(url_list))

    if not url_list == []:
        ## 如果檔案存在
        if os.path.exists("update_apple_news_url.txt"):
            old_update_url_list = [] # 紀錄之前更新但還沒爬新聞內容的新聞網址
            new_update_url_list = [] # 紀錄此次更新的新聞網址
            new_update_url_list = url_list.copy()
            # 開啟之前紀錄更新的新聞網址的檔案
            with open("update_apple_news_url.txt", "r", encoding="utf-8") as f:
                old_update_url_list = f.read().split("\n")
            old_update_url_list.remove("")
            #print(len(old_update_url_list))
            # 將此次更新的新聞網址跟之前更新但還沒爬新聞內容的新聞網址合併
            new_update_url_list.extend(old_update_url_list)
            # 將更新的新聞網址存檔
            with open("update_apple_news_url.txt", "w", encoding="utf-8") as f:
                while True:
                    try:
                        # 得到file lock
                        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        for url in new_update_url_list:
                            f.write(str(url + "\n"))
                        # 釋放file lock
                        fcntl.flock(f, fcntl.LOCK_UN)
                        break
                    except OSError:
                        print("update_apple_news_url.txt locked!")
                    finally:
                        # 釋放file lock
                        fcntl.flock(f, fcntl.LOCK_UN)
        ## 如果檔案不存在
        else:
            # 將更新的新聞網址存檔
            with open("update_apple_news_url.txt", "w", encoding="utf-8") as f:
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
                        print("update_apple_news_url.txt locked!")
                    finally:
                        # 釋放file lock
                        fcntl.flock(f, fcntl.LOCK_UN)

        # 將更新的新聞網址跟之前紀錄的新聞網址合併
        url_list.extend(old_url_list)
        # 將全部新聞網址存檔
        with open("apple_news_url.txt", "w", encoding="utf-8") as f:
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
                    print("update_apple_news_url.txt locked!")
                finally:
                    # 釋放file lock
                    fcntl.flock(f, fcntl.LOCK_UN)

    # 紀錄存檔結束時間
    end_time = time.time()
    print('Save url file done, Time cost: %s ' % (end_time - start_time))

    # 檢查用
    #print(len(update_url_list))
    #print(len(old_url_list))
    #print(len(url_list))
    #print(count)
