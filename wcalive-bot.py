# coding: UTF-8

import urllib.request
import json
import math
import tweepy

Consumer_key = "XXXXXXXXXX"
Consumer_secret = "XXXXXXXXXX"
Access_token = "XXXXXXXXXX"
Access_secret = "XXXXXXXXXX"
auth = tweepy.OAuthHandler(Consumer_key, Consumer_secret)
auth.set_access_token(Access_token, Access_secret)
api = tweepy.API(auth)

# MBLDのattemptResultを必要な値に変換
def decodeMbldAttempt(value):
    solved = 0
    attempted = 0
    centiseconds = value
    if value <= 0:
        return solved, attempted, centiseconds
    missed = value % 100
    seconds = math.floor(value / 100) % 1e5
    points = 99 - (math.floor(value / 1e7) % 100)
    solved = points + missed
    attempted = solved + missed
    centiseconds = None if seconds == 99999 else seconds * 100
    return solved, attempted, centiseconds

# センチ秒をMBLDの記録タイムに変換
def centisecondsToMBLDTimeFormat(value):
    minutes = int(value / 6000)
    seconds = int((value % 6000) / 100)
    secondsStr = str(seconds) if seconds >= 10 else "0" + str(seconds)
    return "%d:%s" % (minutes, secondsStr)

# MBLD用の記録文字列にフォーマット
def formatMbldAttempt(attempt):
    solved, attempted, centiseconds = decodeMbldAttempt(attempt)
    clockFormat = centisecondsToMBLDTimeFormat(centiseconds)
    return "%d/%d %s" % (solved, attempted, clockFormat)

# MBLDとFMC以外の競技のattemptResult(センチ秒)を記録タイムに変換
def centisecondsToTimeFormat(value):
    minutes = int(value / 6000)
    minutesStr = "" if minutes == 0 else str(minutes) + ":"
    seconds = int((value % 6000) / 100)
    secondsStr = str(seconds) if minutes == 0 or seconds >= 10 else "0" + str(seconds)
    centiseconds = int(value % 100)
    centisecondsStr = str(centiseconds) if centiseconds >= 10 else "0" + str(centiseconds)
    return "%s%s.%s" % (minutesStr, secondsStr, centisecondsStr)

# 競技ごとの記録文字列にフォーマット
def formatAttemptResult(attemptResult, eventId, isAverage=False):
    if eventId == "333fm":
        return str('{:.2f}'.format(attemptResult / 100)) if isAverage else str(attemptResult)
    if eventId == "333mbf":
        return formatMbldAttempt(attemptResult)
    return centisecondsToTimeFormat(attemptResult)

url = 'https://live.worldcubeassociation.org/api'
req_header = {
    'Content-Type': 'application/json',
}
req_data = '{ "query": "{ recentRecords { competition { id name } event { id name } round { id } type recordTag attemptResult result { person { name country { name } } } } }" }'

# WCA LiveのGraqlQL APIでRecent RecordsをJSON形式で取得
req = urllib.request.Request(url, data=req_data.encode(), method='POST', headers=req_header)

# String型のJSON dataを辞書型に変換
recordList = {}
with urllib.request.urlopen(req) as response:
    recordList = json.loads(response.read())

if len(recordList['data']['recentRecords']) != 0:
    # 前回取得した記録リストを読み込み
    beforeRecordListString = ""
    # with open('beforeRecordList.txt', 'r', encoding="utf-8") as f:
    with open('/home/shuto/WCALivebot/beforeRecordList.txt', 'r', encoding="utf-8") as f:
        beforeRecordListString += f.read()
    beforeRecordList = json.loads(beforeRecordListString)

    # 前回との差分を取得
    difference = []
    for item in recordList['data']['recentRecords']:
        noneFlag = True
        for beforeItem in beforeRecordList['data']['recentRecords']:
            if item['competition']['id'] == beforeItem['competition']['id'] \
                and item['event']['name'] == beforeItem['event']['name'] \
                and item['round']['id'] == beforeItem['round']['id'] \
                and item['type'] == beforeItem['type'] \
                and item['recordTag'] == beforeItem['recordTag'] \
                and item['attemptResult'] == beforeItem['attemptResult'] \
                and item['result']['person']['name'] == beforeItem['result']['person']['name']:
                noneFlag = False
                break
        if noneFlag:
            difference.append(item)
    
    # 更新情報を整形してツイート
    if len(difference) != 0:
        for record in difference:
            person = record['result']['person']['name']
            country = record['result']['person']['country']['name']
            event = record['event']['name']
            recordType = record['type']
            recordTag = record['recordTag']
            isAverage = True if record['type'] == "average" else False
            result = formatAttemptResult(record['attemptResult'], record['event']['id'], isAverage)
            competition = record['competition']['name']
            url = "/competitions/" + record['competition']['id'] + "/rounds/" + record['round']['id']

            tweetSentence = person + " (from " + country + ") just got the " + event + " " + recordType + " " \
                + recordTag + " (" + result + ") at " + competition + " https://live.worldcubeassociation.org" + url
            # print(tweetSentence)
            api.update_status(tweetSentence)

        # 現在の情報をファイルに書き込み
        # with open("beforeRecordList.txt", mode='w', encoding="utf-8") as f:
        with open("/home/shuto/WCALivebot/beforeRecordList.txt", mode='w', encoding="utf-8") as f:
            f.write(json.dumps(recordList))

