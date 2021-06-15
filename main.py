import time
import requests
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common import credential
import json
import secret


def main(num):
    # print("这个程序的目的是降低文本相似度")
    # print("调用了腾讯云的NLP相关接口")
    # print("采用了 重复翻译 文本摘要 近义词替换 的方式降重")
    # print("顺便还涉及用了爬虫request库的方法来爬取网页的“文本相似度查重”结果")
    # print("示例是用了鲁迅的《祝福》片段")
    # input("按任意键进行翻译")

    f2 = open("ord.txt", "r", encoding='utf-8')
    print(f2.read())
    f2.close()
    translate(num)
    f = open("sentence.txt", "r+", encoding="utf-8")
    f3 = open("rate.txt", "a", encoding='utf-8')
    f2 = open("ord.txt", "r", encoding='utf-8')
    fs = f.read()
    f2s = f2.read()
    f3.write(str(duibi(fs, f2s)))
    # print(fs)
    f.write(f2.read())
    f.close()
    f2.close()
    f3.close()


def duibi(sentence, ordinary):
    # 通过post提交表单获取网页信息，检测两个文本的相似度
    url = 'http://life.chacuo.net/convertsimilar'
    data = {'data': sentence+"^^^"+ordinary,
            'type': 'similar',
            'arg': '',
            'beforeSend': 'undefined'
            }

    re = requests.post(url, data=data)
    content = json.loads(re.text)

    print(content['data'][0])
    return content['data'][0]


def head():  # 为了简化代码写的函数，该函数包括了nlp接口调用代码的重合部分
    from tencentcloud.nlp.v20190408 import nlp_client, models
    cred = credential.Credential(secret.SecretId, secret.SecretKey)
    httpProfile = HttpProfile()
    httpProfile.endpoint = "nlp.tencentcloudapi.com"

    clientProfile = ClientProfile()
    clientProfile.httpProfile = httpProfile
    client = nlp_client.NlpClient(cred, "ap-guangzhou", clientProfile)
    return client


def replace(sentence):
    # 通过近义词替换降重
    from tencentcloud.nlp.v20190408 import nlp_client, models
    try:
        client = head()
        req = models.SimilarWordsRequest()
        params = {
            "Text": sentence
        }
        req.from_json_string(json.dumps(params))

        resp = client.SimilarWords(req)
        re = eval(resp.to_json_string())
        print(resp.to_json_string())
        return re["SimilarWords"][0]
    except TencentCloudSDKException as err:
        print(err)


def divide(sentence):
    # 分词并检测词性
    from tencentcloud.nlp.v20190408 import nlp_client, models
    try:
        null = None
        client = head()
        req = models.LexicalAnalysisRequest()
        params = {
            "Text": sentence
        }
        req.from_json_string(json.dumps(params))

        resp = client.LexicalAnalysis(req)
        # print(resp.to_json_string())
        re = eval(resp.to_json_string())
        for str in re['PosTokens']:
            if str['Pos'] == '' or str['Pos'] == 'd':  # 替换形容词
                # print(str['Word'])
                str['Word'] = replace(str['Word'])
        s = ""
        for str in re['PosTokens']:
            s += str['Word']

        # print(s)
        return s
    except TencentCloudSDKException as err:
        print(err)


# divide("举个例子，如果目标文件的编码格式为 GBK 编码，而我们在使用 open() 函数并以文本模式打开该文件时，手动指定 encoding 参数为 UTF-8。这种情况下，由于编码格式不匹配，当我们使用 read() 函数读取目标文件中的数据时，Python 解释器就会提示UnicodeDecodeError异常。")


def summary(sentence, length):
    # 概括文本，实际上是压缩内容
    from tencentcloud.nlp.v20190408 import nlp_client, models
    try:

        client = head()

        req = models.AutoSummarizationRequest()
        params = {
            "Text": sentence,
            "Length": length
        }
        req.from_json_string(json.dumps(params))

        resp = client.AutoSummarization(req)
        re = resp.__dict__
        # print(re['Summary'])
        return re['Summary']
    except TencentCloudSDKException as err:
        print(err)


def translate(num):
    from tencentcloud.tmt.v20180321 import tmt_client, models
    cred = credential.Credential(
        secret.SecretId, secret.SecretKey)
    httpProfile = HttpProfile()
    httpProfile.endpoint = "tmt.tencentcloudapi.com"
    clientProfile = ClientProfile()
    clientProfile.httpProfile = httpProfile
    client = tmt_client.TmtClient(cred, "ap-guangzhou", clientProfile)

    req = models.TextTranslateRequest()

    try:
        # 多次循环翻译：简中->日文->简中
        # 或 简中->英文->日文->简中
        for i in range(1, num*3+1):
            f = open("sentence.txt", "r", encoding="utf-8")
            source = ""
            # if i != 1:
            source = f.read()
            if i == 1:
                print("要翻译的原文：")
                print(source)
                while True:
                    line = f.readline()
                    if not line:
                        break
                    else:
                        source += divide(line)  # 先分词再近义词替换
            if i == 1:
                source = summary(source, len(str(source))//50*49)  # 进行文本总结
            f.close()
            if i % 4 == 0:  # 防止访问频率过高，先停止2s
                time.sleep(2)
            if i % 3 == 1:
                params = {
                    "SourceText": source,
                    "Source": "zh",
                    "Target": "en",
                    "ProjectId": 0
                }

            if i % 3 == 2:
                params = {
                    "SourceText": source,
                    "Source": "en",
                    "Target": "ja",
                    "ProjectId": 0
                }
            if i % 3 == 0:
                params = {
                    "SourceText": source,
                    "Source": "ja",
                    "Target": "zh",
                    "ProjectId": 0
                }
            req.from_json_string(json.dumps(params))
            resp = client.TextTranslate(req)
            source = resp.TargetText

            f = open("sentence.txt", "w", encoding="utf-8")
            f.write(source)
            f.close()
            print("本次翻译结果：")
            print(source)

    except TencentCloudSDKException as err:
        print(err)


for i in range(2, 11, 2):
    main(2)
