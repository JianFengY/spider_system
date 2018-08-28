"""
Created on 2018/8/13
@Author: Jeff Yang
"""

import requests
import time
import uuid
import pymongo

from spider.settings import *


class LagouSpider():
    """拉勾网爬虫类"""

    def __init__(self, keyword, page, spider_id):
        self.keyword = keyword
        self.page = page
        self.spider_id = spider_id

    def get_json(self, url, form_data):
        """获取页面源码"""
        cookie = "JSESSIONID=" + str(uuid.uuid4()) + ";user_trace_token=" + str(uuid.uuid4()) + "; LGUID=" + str(
            uuid.uuid4()) + "; index_location_city=%E6%88%90%E9%83%BD;SEARCH_ID=" + str(
            uuid.uuid4()) + '; _gid=GA1.2.717841549.1514043316;_ga=GA1.2.952298646.1514043316;LGSID=' + str(
            uuid.uuid4()) + ";LGRID=" + str(uuid.uuid4()) + "; "
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'AlexaToolbar-ALX_NS_PH': 'AlexaToolbar/alx-4.0.3',
            'Connection': 'keep-alive',
            'Content-Length': '23',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Cookie': cookie,
            'Host': 'www.lagou.com',
            'Origin': 'https://www.lagou.com',
            'Referer': 'https://www.lagou.com/jobs/list_iot?city=%E5%85%A8%E5%9B%BD&cl=false&fromSearch=true&labelWords=&suginput=',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36',
            'X-Anit-Forge-Code': '0',
            'X-Anit-Forge-Token': 'None',
            'X-Requested-With': 'XMLHttpRequest',
        }
        response = requests.post(url, data=form_data, headers=headers)
        if response.status_code == 200:
            return response.json()
        return

    def get_info(self, data):
        """获取职位及公司信息"""
        items = data['content']['positionResult']['result']
        result = {}
        for item in items:
            # 职位名称
            result['position_name'] = item['positionName']
            # 薪资
            result['salary'] = item['salary']
            # 城市
            result['city'] = item['city']
            # 发布时间
            result['create_time'] = item['createTime']
            # 公司名称
            result['company_name'] = item['companyFullName']
            # 公司性质
            result['finance_stage'] = item['financeStage']
            # 公司规模
            result['company_size'] = item['companySize']
            # 公司业务范围
            result['industry_field'] = item['industryField']
            yield result

    def run(self):
        """运行爬虫"""
        url = 'https://www.lagou.com/jobs/positionAjax.json?needAddtionalResult=false'
        client = pymongo.MongoClient(MONGO_URL)
        db = client[MONGO_DB]
        for page in range(1, self.page):
            form_data = {
                'first': 'false',
                'pn': page,
                'kd': self.keyword
            }
            data = self.get_json(url, form_data)
            for item in self.get_info(data):
                t = time.time()
                print('saving:', item['company_name'])
                item['_id'] = int(round(t * 1000))
                db['lagou_' + self.spider_id].insert(item)
                time.sleep(0.1)
            print(' === Page', page, 'done! ===')


if __name__ == '__main__':
    client = pymongo.MongoClient(MONGO_URL)
    db = client[MONGO_DB]
    keyword = 'iot'
    page_num = 50
    spider_id = '1534752311040'
    spider = LagouSpider(keyword, page_num, spider_id)
    spider_data = {
        '_id': spider_id,
        'Keyword': keyword,
        'spider_id': spider_id,
        'spider_type': 'lagou_job'
    }
    db[SPIDERS_TABLE].insert(spider_data)
    spider.run()
