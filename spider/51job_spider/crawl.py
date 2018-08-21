"""
Created on 2018/8/13
@Author: Jeff Yang
"""

import requests
import pymongo
import time
from pyquery import PyQuery as pq

from spider.settings import *


class _51JobSpider():
    """51job爬虫类"""

    def __init__(self, keyword, spider_id):
        url = 'https://search.51job.com/list/000000,000000,0000,00,9,99,{},2,1.html'.format(keyword)
        self.keyword = keyword
        self.spider_id = spider_id
        self.page_num = self.get_page_number(url)

    def get_html(self, url):
        """获取页面源码"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36',
        }
        response = requests.get(url)
        if response.status_code == 200:
            response.encoding = 'gbk'
            return response.text
        return

    def get_page_number(self, url):
        """获取总页数"""
        html = self.get_html(url)
        doc = pq(html)
        page_num = doc('.p_in span:nth-child(2)').text()[1:-4]
        return int(page_num)

    def get_job_info(self, html):
        """获取职位信息"""
        doc = pq(html)
        list = doc('.dw_table .el:gt(0)').items()
        job_info = {}
        for item in list:
            # 职位名
            job_info['job_title'] = item('.t1 a').attr('title')
            # 职位说明url
            job_info['job_url'] = item('.t1 a').attr('href')
            # 工作地点
            job_info['work_place'] = item('.t3').text()
            # 薪资（有的是空的）
            job_info['salary'] = item('.t4').text() if item('.t4').text() else ''
            # 发布时间
            job_info['publish_time'] = item('.t5').text()
            # 公司（先放url，然后在公司详情页获取信息）
            job_info['company'] = item('.t2 a').attr('href')
            yield job_info

    def get_company_info(self, html):
        """获取公司信息"""
        doc = pq(html)
        company_info = {}
        # 公司名称
        company_info['name'] = doc('.in h1').attr('title') if doc('.in.img_on h1').attr('title') else ''
        info = doc('.ltype').attr('title')
        if info and len(info.split('|')) is 3:
            info = info.split('|')
            # 公司性质
            company_info['nature'] = ''.join(info[0].split())  # 去除空白字符\xa0
            # 公司规模
            company_info['scale'] = ''.join(info[1].split())
            # 公司业务范围
            company_info['business'] = ''.join(info[2].split())
        else:
            print(company_info['name'], ':', doc('.ltype').attr('title'))
            # 公司性质
            company_info['nature'] = ''
            # 公司规模
            company_info['scale'] = ''
            # 公司业务范围
            company_info['business'] = ''
        # 公司简介
        company_info['profile'] = doc('.con_txt').text()
        return company_info

    def get_complete_info(self, job_info):
        """通过传入职位信息里保存的公司url获取公司信息"""
        html = self.get_html(job_info['company'])
        company_info = self.get_company_info(html)
        job_info['company'] = company_info
        return job_info

    def run(self):
        """运行爬虫"""
        client = pymongo.MongoClient(MONGO_URL)
        db = client[MONGO_DB]
        for page in range(1, self.page_num + 1):
            url = 'https://search.51job.com/list/000000,000000,0000,00,9,99,{},2,{}.html'.format(self.keyword, page)
            html = self.get_html(url)
            for job in self.get_job_info(html):
                t = time.time()
                job_info = self.get_complete_info(job)
                if not job_info['company']['name']:
                    continue
                print('saving:', job_info['job_title'])
                job_info['_id'] = int(round(t * 1000))
                db['51job_' + self.spider_id].insert(job_info)
            print(' === Page', page, 'done! ===')


if __name__ == '__main__':
    client = pymongo.MongoClient(MONGO_URL)
    db = client[MONGO_DB]
    keyword = 'iot'
    spider_id = '1534744083802'
    spider = _51JobSpider(keyword, spider_id)
    spider_data = {
        '_id': spider_id,
        'Keyword': keyword,
        'spider_id': spider_id,
        'spider_type': '51job_job'
    }
    db[SPIDERS_TABLE].insert(spider_data)
    spider.run()
