# Author:YFAN
from configparser import RawConfigParser
import asyncio
from pyppeteer import launch
import os
import requests
import sys

# 爬虫配置
spiderConfig = {'configItem': '0000'}
# 请求头
headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"
    # ",referer": "https://www.mzitu.com/tag/ugirls/"
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
    按照页面遍历规则
    遍历页面
"""


async def foreachPage(page, isHomePage):
    if (isHomePage == False):
        # nextPageUrl = await page.xpath(spiderConfig['pageRule'])[0].getProperty("textContent").jsonValue()
        # print(nextPageUrl)
        # page.goto(nextPageUrl)
        # body > div.page > a:nth-child(3)
        await asyncio.sleep(2)
        await page.click('body > div.page > a:nth-child(3)')
        # 休眠n秒
        await asyncio.sleep(2)
        # 等待页面加载
        # await page.waitForNavigation({'waitUntil': 'load'});
    # TODO
    containerTarget1 = await page.querySelectorAll(spiderConfig['containerTarget1'])
    containerTarget2 = await page.querySelectorAll(spiderConfig['containerTarget2'])
    isEndForeach = False
    for i in range(len(containerTarget2)):
        containerTarget1Element = containerTarget1[i]
        containerTarget2Element = containerTarget2[i]
        # 获取
        name = await (await containerTarget1Element.getProperty(spiderConfig['containerTarget1Propertie'])).jsonValue()
        url = await (await containerTarget2Element.getProperty(spiderConfig['containerTarget2Propertie'])).jsonValue()
        print(name)
        print(url)
        await download(name, url)
    await foreachPage(page, False)


async def download(name,url):
    response = requests.get(url, headers=headers)  # 反爬虫，模拟浏览器提交
    # 休眠
    await asyncio.sleep(2)
    name = name.split(' ')[0]
    NAME=""
    for i in range(len(name)):
        if name not in '/\*:"?<>|':
            NAME+=name[i]
    filename = spiderConfig['fileDownloadPath'] +'\\'+ NAME + "." + spiderConfig['fileType']
    with open(filename, "wb") as f:
        f.write(response.content)
        f.close()

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
    # 关闭浏览器
    # await browser.close()


if __name__ == '__main__':
    initConfig()
    asyncio.get_event_loop().run_until_complete(main())
