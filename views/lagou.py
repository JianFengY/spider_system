"""
Created on 2018/8/20
@Author: Jeff Yang
"""

import pymongo
from flask import Blueprint, render_template, request, jsonify

from spider.settings import *
from spider.lagou_spider.crawl import LagouSpider

lagou = Blueprint('lagou', __name__)


@lagou.route('/lagou')
def main():
    """拉勾网爬虫"""
    return render_template('lagou.html')


@lagou.route('/lagou_spider_result')
def lagou_spider_result():
    """拉勾网爬虫结果页面"""
    return render_template('lagou_spider_result.html')


@lagou.route('/get_spiders')
def get_spiders():
    """查询系统已有的爬虫"""
    page = int(request.args.get('page'))
    limit = int(request.args.get('limit'))
    print("page:", page, "\nlimit:", limit)
    client = pymongo.MongoClient(MONGO_URL)
    db = client[MONGO_DB]
    db.authenticate(MONGO_USER, MONGO_PWD)
    result = {}
    list = db[SPIDERS_TABLE].find({"spider_type": "lagou_job"}).limit(limit).skip((page - 1) * limit)
    if list.count():
        result["code"] = 0
        result["msg"] = "Get spiders successfully!"
        result["count"] = list.count()
        result["data"] = []
        for item in list:
            result["data"].append(item)
    else:
        result["code"] = 1
        result["msg"] = "系统暂无爬虫数据!"
    return jsonify(result)


@lagou.route("/get_jobs")
def get_jobs():
    """根据爬虫ID查询结果"""
    page = int(request.args.get('page'))
    limit = int(request.args.get('limit'))
    spider_id = request.args.get('spider_id')
    print("page:", page, "\nlimit:", limit, "\nspider_id:", spider_id)
    client = pymongo.MongoClient(MONGO_URL)
    db = client[MONGO_DB]
    result = {}
    list = db['lagou_' + spider_id].find().limit(limit).skip((page - 1) * limit)
    if list.count():
        result["code"] = 0
        result["msg"] = "Get resume successfully!"
        result["count"] = list.count()
        result["data"] = []
        for item in list:
            result["data"].append(item)
    else:
        result["code"] = 1
        result["msg"] = "系统暂无数据!"
    return jsonify(result)


@lagou.route("/add_spider", methods=['POST'])
def add_spider():
    """新增爬虫"""
    client = pymongo.MongoClient(MONGO_URL)
    db = client[MONGO_DB]
    keyword = request.form.get('keyword')
    spider_id = request.form.get('spider_id')
    spider_data = {
        '_id': spider_id,
        'Keyword': keyword,
        'spider_id': spider_id,
        'spider_type': 'lagou_job',
        'spider_status': '0'
    }
    db[SPIDERS_TABLE].insert(spider_data)
    result = {
        'code': 0,
        'msg': 'success',
        'data': spider_data
    }
    return jsonify(result)


@lagou.route("/run_spider", methods=['POST'])
def run_spider():
    """运行爬虫"""
    client = pymongo.MongoClient(MONGO_URL)
    db = client[MONGO_DB]
    keyword = request.form.get('keyword')
    spider_id = request.form.get('spider_id')
    # 修改爬虫状态
    db[SPIDERS_TABLE].update_one({'_id': spider_id}, {'$set': {'spider_status': '1'}})
    page_num = 30
    spider = LagouSpider(keyword, page_num, spider_id)
    spider.run()
    result = {
        'code': 0,
        'msg': 'success',
        'data': ''
    }
    return jsonify(result)


@lagou.route("/del_spider", methods=['POST'])
def del_spider():
    """删除爬虫及爬虫结果"""
    spider_id = request.form.get('spider_id')
    print('delete spider:', spider_id)
    client = pymongo.MongoClient(MONGO_URL)
    db = client[MONGO_DB]
    # 删除spiders的该条记录
    db[SPIDERS_TABLE].delete_one({'spider_id': spider_id})
    # 删除集合
    db['lagou_' + spider_id].drop()
    result = {
        'code': 0,
        'msg': 'success',
        'data': ''
    }
    return jsonify(result)


@lagou.route("/del_job", methods=['POST'])
def del_job():
    """删除某岗位"""
    spider_id = request.form.get('spider_id')
    job_id = request.form.get('job_id')
    print('delete job:', job_id)
    client = pymongo.MongoClient(MONGO_URL)
    db = client[MONGO_DB]
    # 删除文档
    x = db['lagou_' + spider_id].delete_one({'job_id': job_id})
    print(x.deleted_count, "个文档已删除")
    result = {
        'code': 0,
        'msg': 'success',
        'data': ''
    }
    return jsonify(result)
