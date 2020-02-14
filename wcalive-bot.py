# coding: UTF-8
from bs4 import BeautifulSoup
import time
import re
import tweepy
import json
import urllib.parse
import requests
import lxml.html

url = "https://live.worldcubeassociation.org/"
key = "XXXXXXXXXX"

payload = {'url':url,'renderType':'HTML','outputAsJson':'true'}
payload = json.dumps(payload) #JSONパース
payload = urllib.parse.quote(payload,safe = '') #URIエンコード
 
phantomJSURL = "https://phantomjscloud.com/api/browser/v2/"+ key + "/?request=" + payload

response = requests.get(phantomJSURL) #GETリクエスト

responseDict = response.json()
htmlAll = lxml.html.fromstring(responseDict["content"]["data"])

htmlList = htmlAll.xpath("//*[@id='root']/div/div/div[.//div/ul/li[text()='Recent records']]/div/ul/div")

if len(htmlList) != 0:
    htmlLXML = lxml.html.tostring(htmlList[0], method='html', encoding='unicode')
    htmlBS = BeautifulSoup(htmlLXML, "html.parser")
    html = htmlBS.select_one("div").decode_contents(formatter="html")

    # WCA Liveから記録の項目を取得しファイルに書き込み
    with open("recordList.txt", mode='w', encoding="utf-8") as f:
        f.write(html)

    # ファイルから読み出し
    htmlOriginal = ""
    with open('recordList.txt', 'r', encoding="utf-8") as f:
        htmlOriginal += f.read()

    beforeHTMLOriginal = ""
    with open('beforeRecordList.txt', 'r', encoding="utf-8") as f:
        beforeHTMLOriginal += f.read()

    # HTMLにパース
    html = BeautifulSoup(htmlOriginal, "html.parser")
    html = html.select("a")
    beforeHTML = BeautifulSoup(beforeHTMLOriginal, "html.parser")
    beforeHTML = beforeHTML.select("a")

    # 追加差分を取得
    difference = []
    for item in html:
        noneFlag = True
        for beforeItem in beforeHTML:
            if item.select_one("div:nth-child(1) > span").text == beforeItem.select_one("div:nth-child(1) > span").text and item.select_one("div:nth-child(2) > span").text == beforeItem.select_one("div:nth-child(2) > span").text and item.select_one("div:nth-child(2) > p").text == beforeItem.select_one("div:nth-child(2) > p").text:
                noneFlag = False
                break
        if noneFlag:
            difference.append(item)

    Consumer_key = "XXXXXXXXXX"
    Consumer_secret = "XXXXXXXXXX"
    Access_token = "XXXXXXXXXX"
    Access_secret = "XXXXXXXXXX"
    auth = tweepy.OAuthHandler(Consumer_key, Consumer_secret)
    auth.set_access_token(Access_token, Access_secret)
    api = tweepy.API(auth)

    # 更新情報を整形してツイート
    if len(difference) != 0:
        for record in difference:
            recordType = record.select_one("div:nth-child(1) > span").text
            recordInfoList = record.select_one("div:nth-child(2) > span").text.split(" of ")
            recordInfo = recordInfoList[0] + " " + recordType + " (" + recordInfoList[1] + ")"
            recordPersonList = record.select_one("div:nth-child(2) > p").text.split(" from ")
            recordPerson = recordPersonList[0] + " (from " + recordPersonList[1] + ")" 

            recordURL = record["href"]
            recordURLList = recordURL.split("/")
            recordCompetitionName = requests.get("https://www.worldcubeassociation.org/api/v0/competitions/" + recordURLList[2] + "/")
            recordCompetitionName = recordCompetitionName.json()
            recordCompetitionName = recordCompetitionName["name"]

            tweetSentence = recordPerson + " just got the " + recordInfo + " at " + recordCompetitionName + " https://live.worldcubeassociation.org" + recordURL
            # print(tweetSentence)
            api.update_status(tweetSentence)

        # 現在の情報をファイルに書き込み
        with open("beforeRecordList.txt", mode='w', encoding="utf-8") as f:
            f.write(htmlOriginal)