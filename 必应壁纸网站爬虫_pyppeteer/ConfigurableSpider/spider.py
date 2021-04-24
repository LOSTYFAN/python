# Author:YFAN
from configparser import RawConfigParser
import asyncio
from pyppeteer import launch
import os
import requests
import uuid

# 爬虫配置
spiderConfig = {'configItem': '0000'}
# 请求头
headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"
}

"""
    继承RawConfigParser
    重写optionxform方法
    解决获取int配置文件options自动为小写问题
"""


class MyConfigparser(RawConfigParser):
    def optionxform(self, optionstr):
        return optionstr


"""
    初始化配置信息
"""


def initConfig():
    # print(os.getcwd())
    # configparser.ConfigParser()
    config = MyConfigparser()
    # 获取当前目录下的config.ini文件
    config.read(os.getcwd() + "\config.ini", 'utf8')
    # 获取config配置项信息
    configProperties = config.options('config')
    for configKey in configProperties:
        # 存储config配置项信息
        spiderConfig[configKey] = config.get('config', configKey)
    # 获取配置项配置信息
    for section in config.sections():
        if (section == spiderConfig['configItem']):
            configItemConfig = config.options(section)
            # 遍历目标配置项配置信息
            for configKey in configItemConfig:
                # 存储配置项信息
                spiderConfig[configKey] = config.get(spiderConfig['configItem'], configKey)
        else:
            continue
    print("------------配置文件初始化成功----------")
    for key in spiderConfig:
        print(key + ':' + spiderConfig[key])
    print("------------配置文件初始化成功----------")


"""
    初始化爬虫
    返回launcher
"""


async def initSpider():
    # headless为True浏览器隐藏
    headless = False
    if spiderConfig['isOpenBrowser'] == 'false':
        headless = True
    option = {
        'headless': headless,
        # 'args': ['--no-sandbox'],
        'dumpio': True,
        'ignoreDefaultArgs': ['--enable-automation'],
        'userDataDir': spiderConfig['tempPath']
    }
    browser = await launch(option)

    return browser


"""
    浏览器创建标签
"""


async def createPage(browser):
    # 创建新标签
    page = await browser.newPage()
    await page.setUserAgent(headers['user-agent'])
    # 设置浏览器窗口大小
    await page.setViewport({'width': 1200, 'height': 800})
    await page.goto(spiderConfig['targetUrl'], headers)
    return page


"""
    休眠N秒
"""


async def sleepNumSenconds(num, flag):
    if flag == None or flag == '':
        await asyncio.sleep(num)
    elif flag == 'DOWNLOAD':
        await asyncio.sleep(num)


"""
    按照页面遍历规则
    遍历页面
"""


async def foreachPage(page, isHomePage):
    # isHomePage为False，非首页需要进入下一页
    if (isHomePage == False):
        # 休眠n秒
        await sleepNumSenconds(2, None)
        # 获取下一页的element如果为None说明没有下一页，执行结束
        pageRuleElement = await page.querySelector(spiderConfig['pageRule'])
        if pageRuleElement == None:
            return
        # 点击进入下一页
        await page.click(spiderConfig['pageRule'])
        # 休眠n秒
        await sleepNumSenconds(2, None)
        # 等待页面加载
        # await page.waitForNavigation({'waitUntil': 'load'});
    # 获取DOM容器目标值
    list = await containerTargetList(page)
    containerTarget1 = list[0]
    containerTarget2 = list[1]
    print(page.url)
    for i in range(len(containerTarget2)):
        containerTarget1Element = None
        if i < len(containerTarget1):
            containerTarget1Element = containerTarget1[i]
        containerTarget2Element = containerTarget2[i]
        # 获取属性值
        name = await buildFileName(str(uuid.uuid4()))
        if containerTarget1Element != None:
            name = await getElementgetProperty(containerTarget1Element, 'containerTarget1Propertie')
        url = await getElementgetProperty(containerTarget2Element, 'containerTarget2Propertie')
        # 输出
        print(" \t" + str(i + 1) + " : " + name)
        print(" \t" + str(i + 1) + " : " + url)
        # 下载
        await download(name, url)
    # 继续遍历
    await foreachPage(page, False)


"""
    获取ElementHandle的属性值
    返回str
"""


async def getElementgetProperty(element, spiderConfigKey):
    return await (await element.getProperty(spiderConfig[spiderConfigKey])).jsonValue()


"""
    处理DOM容器目标值
    返回一个列表
"""


async def containerTargetList(page):
    list = []
    containerTargetSize = int(spiderConfig['containerTargetSize'])
    if containerTargetSize == 1:
        containerTarget2 = await page.querySelectorAll(spiderConfig['containerTarget2'])
        list.append(containerTarget2)
        list.append(containerTarget2)
    elif containerTargetSize == 2:
        containerTarget1 = await page.querySelectorAll(spiderConfig['containerTarget1'])
        containerTarget2 = await page.querySelectorAll(spiderConfig['containerTarget2'])
        list.append(containerTarget1)
        list.append(containerTarget2)
    else:
        list.append([])
        list.append([])
    return list


"""
    处理文件名
"""


async def buildFileName(name):
    # 使用uuid
    if 'fileNameRandom' in spiderConfig and spiderConfig['fileNameRandom'] == 'uuid':
        uid = str(uuid.uuid4())
        suid = ''.join(uid.split('-'))
        return suid
    # 数字序号
    elif 'fileNameRandom' in spiderConfig and spiderConfig['fileNameRandom'] == 'num':
        fileCount = 1
        filePath = await fileNamePathPublic(fileCount)
        while os.path.isfile(filePath):
            fileCount = fileCount + 1
            filePath = await fileNamePathPublic(fileCount)
        return str(fileCount)
    # 自定义文件名
    elif 'fileNameRandom' not in spiderConfig or spiderConfig['fileNameRandom'] == '0000':
        NAME = ""
        for i in range(len(name)):
            if name[i] not in '/\*:"?<>|':
                NAME += name[i]
        return NAME
    # 默认使用uuid
    else:
        uid = str(uuid.uuid4())
        suid = ''.join(uid.split('-'))
        return suid


"""
    组织文件路径
"""


async def fileNamePathPublic(param):
    fileNamePath = spiderConfig['fileDownloadPath'] + '\\' + str(param) + "." + spiderConfig['fileType']
    return fileNamePath


"""
    下载
   
"""


async def download(name, url):
    response = requests.get(url, headers=headers)  # 反爬虫，模拟浏览器提交
    # 休眠
    await sleepNumSenconds(2, 'DOWNLOAD')
    # 构建文件名
    NAME = await buildFileName(name)
    # 文件
    filename = await fileNamePathPublic(NAME)
    # 是否下载文件 判断文件是否存在下载路径目录中
    downOrNot = await recognizeFile(response, filename)
    if downOrNot:
        return
    with open(filename, "wb") as f:
        f.write(response.content)
        f.close()


"""
    下载前进行判断是否有该文件
    通过文件名和字节大小来判断
    返回False下载文件
"""


async def recognizeFile(response, filePath):
    responseFileSize = 0
    # 获取字节数
    if 'Content-Length' in response.headers:
        responseFileSize = int(response.headers['Content-Length'])
    else:
        responseFileSize = len(response.content)
    # 判断是否有该文件
    if os.path.isfile(filePath):
        fileSize = int(os.path.getsize(filePath))
        print('responseFileSize')
        print(responseFileSize)
        print('fileSize')
        print(fileSize)
        # 判断字节数是否相等
        if fileSize == responseFileSize:
            return True
    return False

"""
    退出提示函数
"""
async def exitTips(num):
    while num > 0:
        print("----------"+str(num) + '秒后退出----------')
        await sleepNumSenconds(1, None)
        num -= 1
    else:
        print('----------正在退出----------')


""" 
    程序入口
"""


async def main():
    # 初始化
    browser = await initSpider()
    # 创建浏览器标签
    page = await createPage(browser)
    # 开始遍历页面
    await foreachPage(page, True)
    # 退出提示
    await exitTips(5)
    # 关闭浏览器
    await browser.close()


if __name__ == '__main__':
    initConfig()
    if 'configItem' in spiderConfig and spiderConfig['configItem'] != None and spiderConfig['configItem'] != '0000':
        asyncio.get_event_loop().run_until_complete(main())
