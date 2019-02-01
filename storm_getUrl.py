# 引用相關套件
from urllib.request import urlopen
from bs4 import BeautifulSoup
import time, os
import warnings
warnings.filterwarnings('ignore')
from urllib.error import HTTPError


def crab(classID, tag):
    # 紀錄爬蟲開始時間
    start_time = time.time()

    update_url_list = [] # 紀錄爬回來的各篇新聞網址
    count = 0 # 紀錄爬了幾筆
    page = 1 # 從蘋果即時新聞第一頁開始
    ## 開始爬蟲
    while True:
        url = "https://www.storm.mg/category/" + str(classID) + "/" + str(page)
        print("處理頁面：", url)
        try:
            page_response = urlopen(url)
        except HTTPError:
            print("tag:", tag, "Completed")
            break
        page_html = BeautifulSoup(page_response)

        for page_news in page_html.find_all("div", class_="category_card"):
            news_url = page_news.find("a", class_="card_link")["href"]
            print(news_url)
            if not news_url in update_url_list:
                update_url_list.append(news_url)
            count = count + 1
        page = page + 1
        if page == 2:
            print("tag:", tag, "completed!!!")
            break

    # 紀錄爬蟲結束時間
    #print(update_url_list)
    end_time = time.time()
    print('Done, Time cost: %s ' % (end_time - start_time))

    # 紀錄存檔開始時間
    start_time = time.time()

    old_url_list = []  # 紀錄之前爬過的新聞網址
    # 開啟紀錄全部新聞網址的檔案
    if os.path.exists("./urlfolder/storm_" + tag + "_news_url_tmp.txt"):
        with open("./urlfolder/storm_" + tag + "_news_url_tmp.txt", "r", encoding="utf-8") as f:
            old_url_list = f.read().split("\n")
            old_url_list.remove("")

    url_list = []  # 紀錄更新的新聞網址
    # 不記錄重複的新聞網址
    for url in update_url_list:
        if not url in old_url_list:
            url_list.append(url)
    # print(len(url_list))

    if not url_list == []:
        print(tag, "update = ", len(url_list))
        ## 如果檔案存在
        if os.path.exists("./tmpfolder/update_storm_" + tag + "_news_url_tmp.txt"):
            old_update_url_list = []  # 紀錄之前更新但還沒爬新聞內容的新聞網址
            new_update_url_list = []  # 紀錄此次更新的新聞網址
            new_update_url_list = url_list.copy()
            # 開啟之前紀錄更新的新聞網址的檔案
            with open("./tmpfolder/update_storm_"+ tag + "_news_url_tmp.txt", "r", encoding="utf-8") as f:
                old_update_url_list = f.read().split("\n")
            old_update_url_list.remove("")
            # 將此次更新的新聞網址跟之前更新但還沒爬新聞內容的新聞網址合併
            new_update_url_list.extend(old_update_url_list)
            # 將更新的新聞網址存檔
            with open("./tmpfolder/update_storm_" + tag + "_news_url_tmp.txt", "w", encoding="utf-8") as f:
                for url in new_update_url_list:
                    f.write(str(url + "\n"))

        ## 如果檔案不存在
        else:
            # 將更新的新聞網址存檔
            with open("./tmpfolder/update_storm_" + tag + "_news_url_tmp.txt", "w", encoding="utf-8") as f:
                for url in url_list:
                    f.write(str(url + "\n"))


        # 將更新的新聞網址跟之前紀錄的新聞網址合併
        url_list.extend(old_url_list)
        # 將全部新聞網址存檔
        with open("./urlfolder/storm_" + tag + "_news_url_tmp.txt", "w", encoding="utf-8") as f:
            for url in url_list:
                f.write(str(url + "\n"))


        # 紀錄存檔結束時間
        end_time = time.time()
        print('Done, Time cost: %s ' % (end_time - start_time))

        # 檢查用
        print(len(update_url_list))
        print(len(old_url_list))
        print(len(url_list))
        print(count)


if __name__ == "__main__":

    path = "./tmpfolder"
    if not os.path.exists(path):
        os.makedirs(path)

    path = "./urlfolder/"
    if not os.path.exists(path):
        os.makedirs(path)

    crab(118, "politic")
    crab(117, "world")
    crab(23083, "finance")
    crab(24667, "research")
    crab(26644, "military")
    crab(118606, "sports")
    crab(84984, "arts")
    crab(121, "china")
    crab(965, "civic")


    #將全部url list 合併
    filenames = ["storm_politic_news_url_tmp.txt", "storm_world_news_url_tmp.txt", "storm_finance_news_url_tmp.txt",
                 "storm_research_news_url_tmp.txt", "storm_military_news_url_tmp.txt", "storm_sports_news_url_tmp.txt",
                 "storm_arts_news_url_tmp.txt", "storm_china_news_url_tmp.txt", "storm_civic_news_url_tmp.txt"]
    with open("storm_news_url.txt", 'w', encoding="utf-8") as outfile:
        for fname in filenames:
            try:
                with open("./urlfolder/" + fname) as infile:
                    for line in infile:
                        outfile.write(line)
                #os.remove("./tmpfolder/" + fname)
            except FileNotFoundError:
                break

    #將update list 合併
    filenames = ["update_storm_politic_news_url_tmp.txt", "update_storm_world_news_url_tmp.txt", "update_storm_finance_news_url_tmp.txt",
                 "update_storm_research_news_url_tmp.txt", "update_storm_military_news_url_tmp.txt", "update_storm_sports_news_url_tmp.txt",
                 "update_storm_arts_news_url_tmp.txt", "update_storm_china_news_url_tmp.txt", "update_storm_civic_news_url_tmp.txt"]
    with open("update_storm_news_url.txt", 'w', encoding="utf-8") as outfile:
        for fname in filenames:
            try:
                with open("./tmpfolder/" + fname) as infile:
                    for line in infile:
                        outfile.write(line)
                #os.remove("./tmpfolder/" + fname)
            except FileNotFoundError:
                break