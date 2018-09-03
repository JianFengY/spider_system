"""
Created on 2018/7/17
@Author: Jeff Yang
"""

import re
import time
from io import BytesIO

import pymongo
import pytesseract
import requests
from PIL import Image
from pyquery import PyQuery as pq

from spider.settings import *


class CjolSpider():
    """中国人才热线爬虫类"""

    def __init__(self, form_data, spider_id):
        self.form_data = form_data
        self.spider_id = spider_id

    def get_html(self, url, from_data, session):
        """获取网页源码"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36',
        }
        resume_url = "http://newrms.cjol.com/ResumeBank/ResumeOperation"
        response = session.post(url, data=from_data, headers=headers)
        if response.status_code == 200:
            if url == resume_url:
                return response.json()
            else:
                return response.text
        return

    def identify_captcha(self, key):
        """识别验证码"""
        response = requests.get('http://rms.cjol.com/ValidateCodePicture.aspx?Key=' + key)
        image = Image.open(BytesIO(response.content))
        code = pytesseract.image_to_string(image)
        return code

    def get_cookies(self, key):
        """通过旧版系统模拟登录获取cookies"""
        url = "http://rms.cjol.com/Login.aspx?ReturnUrl=%2fDefault.aspx%3fver%3d7&ver=7"
        code = self.identify_captcha(key)
        print('识别验证码：', code)
        form_data = {
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": "/wEPDwUKLTY3MTc3MjcyOGRk",
            "txtUserName": "******",
            "txtPassword": "******",
            "txtValidateCode": code,
            "hdValidateCodeID": key,
            "ddlLanguage": "CN",
            "btnLogin": "登录",
        }
        session = requests.Session()
        response = session.post(url, data=form_data)
        return session

    def get_page_number(self, html):
        """获取页数"""
        doc = pq(html)
        page_num = doc('#hid_search_page_count').attr('value')
        return page_num

    def get_resume_ids(self, html):
        """获取简历编号"""
        doc = pq(html)
        items = doc('ul .w80 a').items()
        pattern = re.compile('detail-(\d+?)\?Key=')
        for item in items:
            resume_id = re.search(pattern, item.attr('href'))
            yield resume_id[1]

    def get_resume_info(self, html):
        """获取简历上的信息"""
        # 没有匹配到学历等4个基本信息就跳过，用正则程序会卡住
        if any(str not in html for str in ['学历', '性别', '毕业院校', '年龄']):
            return
        resume_info = {}
        doc = pq(html)
        # 简历编号
        resume_id = doc('.resume_info_up').text()[5:]
        # print(resume_id)
        resume_info['resume_id'] = resume_id
        # 简历最后更新时间
        last_update_time = doc('.resume_info_down').text()[7:]
        # print(last_update_time)
        resume_info['last_update_time'] = last_update_time
        pattern = re.compile('.*?学历.*?class="field_right">(.*?)</td>.*?'
                             + '.*?性别.*?class="field_right">(.*?)</td>.*?'
                             + '.*?毕业院校.*?class="field_right">(.*?)</td>.*?'
                             + '.*?年龄.*?class="field_right">(.*?)</td>.*?', re.S)
        result = re.search(pattern, html)
        # # 没有匹配到学历等4个基本信息就跳过
        # if not result:
        #     return
        # 学历
        education = result[1]
        resume_info['education'] = education
        # 性别
        gender = result[2]
        resume_info['gender'] = gender
        # 毕业院校
        graduate_institution = result[3]
        resume_info['graduate_institution'] = graduate_institution
        # 年龄
        age = result[4][:3]
        resume_info['age'] = age
        # print(education)
        # 工作经历
        experiences_list = []
        work_experiences_tr = doc('td:contains("工作经历")').parent().next()
        work_experiences = work_experiences_tr('.work_experience').items()
        # 有些class为work_experience实际不是工作经历而是教育经历之类的
        for work_experience in work_experiences:
            experience_dict = {}
            items = list(work_experience('span').items())
            if not items:
                continue
            # 公司
            company = items[0].text()
            experience_dict['company'] = company
            # 职位
            job_title = items[1].text() if len(items) > 1 else ''
            experience_dict['job_title'] = job_title
            # 在职时间
            date_range = items[2].text() if len(items) > 1 else ''
            experience_dict['date_range'] = date_range
            # 工作简介
            work_experience_describe_tr = work_experience.parent().siblings()[1]
            doc2 = pq(work_experience_describe_tr)
            work_experience_describe = doc2('td').text()
            experience_dict['work_experience_describe'] = work_experience_describe
            experiences_list.append(experience_dict)
            # print(company)
            # print(job_title)
            # print(date_range)
            # print(work_experience_describe)
            # print('======')
        resume_info['work_experiences'] = experiences_list
        return resume_info

    def get_resume_info_by_id(self, resume_id, session):
        """通过简历ID获取某简历信息"""
        url = "http://newrms.cjol.com/ResumeBank/ResumeOperation"
        from_data = {
            "JobSeekerID": resume_id,
            "bankid": "-1",
            "Fn": "resume",
            "Lang": "CN",
        }
        html = self.get_html(url, from_data, session)
        # print(html["OtherData"])

        resume_info = self.get_resume_info(html["OtherData"])
        # print(data)
        if not resume_info:
            return
        return resume_info

    def run(self):
        """运行爬虫"""
        url = "http://newrms.cjol.com/SearchEngine/List?fn=d"
        key = "0d98459a-038b-2c0e-351d-23b69f1fcd1a"
        client = pymongo.MongoClient(MONGO_URL)
        db = client[MONGO_DB]
        db.authenticate(MONGO_USER, MONGO_PWD)
        login_flag = True
        while login_flag:
            session = self.get_cookies(key)
            self.form_data['PageNo'] = 1
            html = self.get_html(url, self.form_data, session)
            if '招聘管理系统登录' in html:
                print('登录失败！')
                continue
            login_flag = False
            pages = int(self.get_page_number(html))
            print("(cjol) 共搜索出", pages, "页")
            for page_num in range(1, pages + 1):
                self.form_data['PageNo'] = page_num
                html = self.get_html(url, self.form_data, session)
                # if '招聘管理系统登录' in html:
                #     print('登录失败！')
                #     return
                for resume_id in self.get_resume_ids(html):
                    t = time.time()
                    print('正在获取简历：', resume_id)
                    resume_info = self.get_resume_info_by_id(resume_id, session)
                    if resume_info:
                        resume_info['_id'] = int(round(t * 1000))
                        db['cjol_resume_' + self.spider_id].insert(resume_info)
                print(' === (cjol) Page', page_num, 'done! ===')
        return


if __name__ == '__main__':
    form_data = {
        "Keyword": "前端 +Vue.js",
        "MinWorkExperience": "3",
        "MinEducationText": "大专",
        "MinEducation": "50",
        "ExpectedLocationText": "深圳",
        "ExpectedLocation": "2008",
        "GetListResult": "GetListResult",
        "PageSize": "20",
        "Sort": "UpdateTime desc",
    }
    spider_id = '1534753856533'
    client = pymongo.MongoClient(MONGO_URL)
    db = client[MONGO_DB]
    spider = CjolSpider(form_data, spider_id)
    form_data['_id'] = spider_id
    form_data['spider_id'] = spider_id
    form_data['spider_type'] = 'cjol_resume'
    db[SPIDERS_TABLE].insert(form_data)
    # while not spider.run():
    #     spider.run()
    spider.run()
