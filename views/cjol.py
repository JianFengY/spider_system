"""
Created on 2018/8/20
@Author: Jeff Yang
"""

import pymongo
# import threading
from flask import Blueprint, render_template, request, jsonify

from spider.settings import *
from spider.cjol_spider.crawl import CjolSpider

cjol = Blueprint('cjol', __name__)


@cjol.route('/')
def main():
    """cjol爬虫"""
    return render_template('cjol.html')


@cjol.route('/get_spiders')
def get_spiders():
    """查询系统已有的爬虫"""
    page = int(request.args.get('page'))
    limit = int(request.args.get('limit'))
    print("page:", page, "\nlimit:", limit)
    client = pymongo.MongoClient(
        'mongodb://{}:{}@{}:{}/{}?authMechanism=SCRAM-SHA-1'.format(MONGO_USER, MONGO_PWD, MONGO_URL, MONGO_PORT,
                                                                    MONGO_DB))
    db = client[MONGO_DB]
    result = {}
    list = db[SPIDERS_TABLE].find({"spider_type": "cjol_resume"}).limit(limit).skip((page - 1) * limit)
    if list.count():
        result["code"] = 0
        result["msg"] = "Get spiders successfully!"
        result["count"] = list.count()
        result["data"] = []
        for item in list:
            # item.pop('_id')  # 解决TypeError: Object of type 'ObjectId' is not JSON serializable
            result["data"].append(item)
    return jsonify(result)


@cjol.route('/cjol_spider_result')
def cjol_spider_result():
    """cjol爬虫结果页面"""
    return render_template('cjol_spider_result.html')


@cjol.route("/get_resumes", methods=['POST'])
def get_resumes():
    """根据爬虫ID查询结果"""
    page = int(request.form.get('page'))
    limit = int(request.form.get('limit'))
    spider_id = request.form.get('spider_id')
    myquery = {}
    work_experiences_keyword = request.form.get('work_experiences_keyword')
    education = request.form.get('education')
    graduate_institution = request.form.get('graduate_institution')
    gender = request.form.get('gender')
    age_min = request.form.get('age_min')
    age_max = request.form.get('age_max')
    if education is not '':
        myquery['education'] = education
    if graduate_institution is not '':
        myquery['graduate_institution'] = {"$regex": ".*?" + graduate_institution + ".*?"}
    if gender is not '':
        myquery['gender'] = gender
    if age_min is not '' and age_max is not '':
        myquery['age'] = {"$gte": age_min, "$lte": age_max}
    elif age_min is not '':
        myquery['age'] = {"$gte": age_min}
    elif age_max is not '':
        myquery['age'] = {"$lte": age_max}
    if work_experiences_keyword is not '':
        # 查找文档里work_experiences数组中至少有一个嵌入文档的work_experience_describe包含关键字work_experiences_search的文档
        myquery['work_experiences.work_experience_describe'] = {"$regex": ".*?" + work_experiences_keyword + ".*?"}
    print("page:", page, "\nlimit:", limit, "\nspider_id:", spider_id)
    print("myquery", myquery)
    client = pymongo.MongoClient(MONGO_URL)
    db = client[MONGO_DB]
    result = {}
    list = db['cjol_resume_' + spider_id].find(myquery).limit(limit).skip((page - 1) * limit)
    if list.count():
        result["code"] = 0
        result["msg"] = "Get resume successfully!"
        result["count"] = list.count()
        result["data"] = []
        for item in list:
            # item.pop('_id')  # 解决TypeError: Object of type 'ObjectId' is not JSON serializable
            result["data"].append(item)
    else:
        result["code"] = 1
        result["msg"] = "系统暂无爬虫数据!"
    return jsonify(result)


@cjol.route('/work_experiences')
def work_experiences():
    """工作经历页面"""
    return render_template('work_experiences.html')


@cjol.route("/get_work_experiences")
def get_work_experiences():
    """根据爬虫ID及简历ID查询工作经历"""
    page = int(request.args.get('page'))
    limit = int(request.args.get('limit'))
    spider_id = request.args.get('spider_id')
    resume_id = request.args.get('resume_id')
    print("page:", page, "\nlimit:", limit, "\nspider_id:", spider_id, "\nresume_id:", resume_id)
    client = pymongo.MongoClient(MONGO_URL)
    db = client[MONGO_DB]
    result = {}
    # list = db['cjol_resume_' + spider_id].find_one({ "resume_id": resume_id }).limit(limit).skip((page - 1) * limit)
    resume = db['cjol_resume_' + spider_id].find_one({"resume_id": resume_id})
    if resume:
        result["code"] = 0
        result["msg"] = "Get resume successfully!"
        result["count"] = resume['work_experiences']
        result["data"] = []
        for item in resume['work_experiences']:
            result["data"].append(item)
    else:
        result["code"] = 1
        result["msg"] = "系统暂无数据!"
    return jsonify(result)


# def running(form_data):
#     """返回“正在执行”的消息"""
#     result = {
#         'code': 0,
#         'msg': 'running',
#         'data': form_data
#     }
#     return result


@cjol.route("/add_spider", methods=['POST'])
def add_spider():
    """新增爬虫"""
    form_data = {
        'GetListResult': 'GetListResult',
        'PageSize': '20',
        'Sort': 'UpdateTime desc',
        'Keyword': request.form.get('Keyword'),
        'MinEducationText': request.form.get('MinEducationText'),
        'MinEducation': request.form.get('MinEducation'),
        'MinWorkExperience': request.form.get('MinWorkExperience'),
        'ExpectedLocationText': request.form.get('ExpectedLocationText'),
        'ExpectedLocation': request.form.get('ExpectedLocation')
    }
    spider_id = request.form.get('SpiderId')
    print(spider_id)
    # print(form_data)
    client = pymongo.MongoClient(MONGO_URL)
    db = client[MONGO_DB]
    # spider = CjolSpider(form_data, spider_id)
    form_data['_id'] = spider_id
    form_data['spider_id'] = spider_id
    form_data['spider_type'] = 'cjol_resume'
    form_data['spider_status'] = '0'  # 爬虫状态，0为新增未启动，1为已启动
    db[SPIDERS_TABLE].insert(form_data)
    # result = jsonify(running(form_data))
    # t = threading.Thread(target=spider.run(), name='run_spider')
    # t.setDaemon(False)
    # t.start()
    result = {
        'code': 0,
        'msg': 'success',
        'data': form_data
    }
    return jsonify(result)


@cjol.route("/run_spider", methods=['POST'])
def run_spider():
    """运行爬虫"""
    form_data = {
        'GetListResult': 'GetListResult',
        'PageSize': '20',
        'Sort': 'UpdateTime desc',
        'Keyword': request.form.get('Keyword'),
        'MinEducationText': request.form.get('MinEducationText'),
        'MinEducation': request.form.get('MinEducation'),
        'MinWorkExperience': request.form.get('MinWorkExperience'),
        'ExpectedLocationText': request.form.get('ExpectedLocationText'),
        'ExpectedLocation': request.form.get('ExpectedLocation')
    }
    spider_id = request.form.get('SpiderId')
    spider = CjolSpider(form_data, spider_id)
    client = pymongo.MongoClient(MONGO_URL)
    db = client[MONGO_DB]
    # 修改爬虫状态
    db[SPIDERS_TABLE].update_one({'_id': spider_id}, {'$set': {'spider_status': '1'}})
    print('running spider:', spider_id)
    spider.run()
    result = {
        'code': 0,
        'msg': 'running',
        'data': form_data
    }
    return jsonify(result)


@cjol.route("/del_spider", methods=['POST'])
def del_spider():
    """删除爬虫及爬虫结果"""
    spider_id = request.form.get('spider_id')
    print('delete spider:', spider_id)
    client = pymongo.MongoClient(MONGO_URL)
    db = client[MONGO_DB]
    # 删除spiders的该条记录
    db[SPIDERS_TABLE].delete_one({'spider_id': spider_id})
    # 删除集合
    db['cjol_resume_' + spider_id].drop()
    result = {
        'code': 0,
        'msg': 'success',
        'data': ''
    }
    return jsonify(result)


@cjol.route("/del_resume", methods=['POST'])
def del_resume():
    """删除简历"""
    spider_id = request.form.get('spider_id')
    resume_id = request.form.get('resume_id')
    print('delete resume:', resume_id)
    client = pymongo.MongoClient(MONGO_URL)
    db = client[MONGO_DB]
    # 删除文档
    x = db['cjol_resume_' + spider_id].delete_one({'resume_id': resume_id})
    print(x.deleted_count, "个文档已删除")
    result = {
        'code': 0,
        'msg': 'success',
        'data': ''
    }
    return jsonify(result)
