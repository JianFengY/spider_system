"""
Created on 2018/8/20
@Author: Jeff Yang
"""

import pymongo
from flask import Blueprint, render_template, request, jsonify

from spider.settings import *

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
    result = {}
    list = db[SPIDERS_TABLE].find({"spider_type": "lagou_job"}).limit(limit).skip((page - 1) * limit)
    if list.count():
        result["code"] = 0
        result["msg"] = "Get spiders successfully!"
        result["count"] = list.count()
        result["data"] = []
        for item in list:
            result["data"].append(item)
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
    return jsonify(result)
