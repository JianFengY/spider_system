"""
Created on 2018/8/20
@Author: Jeff Yang
"""

import pymongo
import threading
from flask import Blueprint, render_template, request, jsonify

from spider.settings import *
from spider.job51_spider.crawl import Job51Spider

job51 = Blueprint('job51', __name__)


@job51.route('/job51')
def main():
    """51job爬虫"""
    return render_template('job51.html')


@job51.route('/job51_spider_result')
def job51_spider_result():
    """51job爬虫结果页面"""
    return render_template('job51_spider_result.html')


@job51.route('/get_spiders')
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
    list = db[SPIDERS_TABLE].find({"spider_type": "51job_job"}).limit(limit).skip((page - 1) * limit)
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


@job51.route("/get_jobs")
def get_jobs():
    """根据爬虫ID查询结果"""
    page = int(request.args.get('page'))
    limit = int(request.args.get('limit'))
    spider_id = request.args.get('spider_id')
    print("page:", page, "\nlimit:", limit, "\nspider_id:", spider_id)
    client = pymongo.MongoClient(
        'mongodb://{}:{}@{}:{}/{}?authMechanism=SCRAM-SHA-1'.format(MONGO_USER, MONGO_PWD, MONGO_URL, MONGO_PORT,
                                                                    MONGO_DB))
    db = client[MONGO_DB]
    result = {}
    list = db['51job_' + spider_id].find().limit(limit).skip((page - 1) * limit)
    if list.count():
        result["code"] = 0
        result["msg"] = "Get resume successfully!"
        result["count"] = list.count()
        result["data"] = []
        for item in list:
            item['company_name'] = item['company']['name']
            item['company_nature'] = item['company']['nature']
            item['company_scale'] = item['company']['scale']
            item['company_business'] = item['company']['business']
            item['company_profile'] = item['company']['profile']
            item.pop('company')
            result["data"].append(item)
    else:
        result["code"] = 1
        result["msg"] = "系统暂无数据!"
    return jsonify(result)


@job51.route("/add_spider", methods=['POST'])
def add_spider():
    """新增爬虫"""
    client = pymongo.MongoClient(
        'mongodb://{}:{}@{}:{}/{}?authMechanism=SCRAM-SHA-1'.format(MONGO_USER, MONGO_PWD, MONGO_URL, MONGO_PORT,
                                                                    MONGO_DB))
    db = client[MONGO_DB]
    keyword = request.form.get('keyword')
    spider_id = request.form.get('spider_id')
    spider_data = {
        '_id': spider_id,
        'Keyword': keyword,
        'spider_id': spider_id,
        'spider_type': '51job_job',
        'spider_status': '0'
    }
    db[SPIDERS_TABLE].insert(spider_data)
    result = {
        'code': 0,
        'msg': 'success',
        'data': spider_data
    }
    return jsonify(result)


@job51.route("/run_spider", methods=['POST'])
def run_spider():
    """运行爬虫"""
    client = pymongo.MongoClient(
        'mongodb://{}:{}@{}:{}/{}?authMechanism=SCRAM-SHA-1'.format(MONGO_USER, MONGO_PWD, MONGO_URL, MONGO_PORT,
                                                                    MONGO_DB))
    db = client[MONGO_DB]
    keyword = request.form.get('keyword')
    spider_id = request.form.get('spider_id')
    # 修改爬虫状态
    db[SPIDERS_TABLE].update_one({'_id': spider_id}, {'$set': {'spider_status': '1'}})
    spider = Job51Spider(keyword, spider_id)
    spider.run()
    result = {
        'code': 0,
        'msg': 'success',
        'data': ''
    }
    return jsonify(result)


@job51.route("/del_spider", methods=['POST'])
def del_spider():
    """删除爬虫及爬虫结果"""
    spider_id = request.form.get('spider_id')
    print('delete spider:', spider_id)
    client = pymongo.MongoClient(
        'mongodb://{}:{}@{}:{}/{}?authMechanism=SCRAM-SHA-1'.format(MONGO_USER, MONGO_PWD, MONGO_URL, MONGO_PORT,
                                                                    MONGO_DB))
    db = client[MONGO_DB]
    # 删除spiders的该条记录
    db[SPIDERS_TABLE].delete_one({'spider_id': spider_id})
    # 删除集合
    db['51job_' + spider_id].drop()
    result = {
        'code': 0,
        'msg': 'success',
        'data': ''
    }
    return jsonify(result)

@job51.route("/del_job", methods=['POST'])
def del_job():
    """删除某岗位"""
    spider_id = request.form.get('spider_id')
    job_id = request.form.get('job_id')
    print('delete job:', job_id)
    client = pymongo.MongoClient(
        'mongodb://{}:{}@{}:{}/{}?authMechanism=SCRAM-SHA-1'.format(MONGO_USER, MONGO_PWD, MONGO_URL, MONGO_PORT,
                                                                    MONGO_DB))
    db = client[MONGO_DB]
    # 删除文档
    x = db['51job_' + spider_id].delete_one({'job_id': job_id})
    print(x.deleted_count, "个文档已删除")
    result = {
        'code': 0,
        'msg': 'success',
        'data': ''
    }
    return jsonify(result)
