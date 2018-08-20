"""
Created on 2018/8/20
@Author: Jeff Yang
"""

import pymongo
from flask import Blueprint, render_template, request, jsonify

from spider.settings import *

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
    client = pymongo.MongoClient(MONGO_URL)
    db = client[MONGO_DB]
    result = {}
    list = db[SPIDERS_TABLE].find({ "spider_type": "cjol_resume" }).limit(limit).skip((page - 1) * limit)
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


@cjol.route("/get_resumes")
def get_resumes():
    """根据爬虫ID查询结果"""
    page = int(request.args.get('page'))
    limit = int(request.args.get('limit'))
    spider_id = request.args.get('spider_id')
    print("page:", page, "\nlimit:", limit, "\nspider_id:", spider_id)
    client = pymongo.MongoClient(MONGO_URL)
    db = client[MONGO_DB]
    result = {}
    list = db['cjol_resume_' + spider_id].find().limit(limit).skip((page - 1) * limit)
    if list.count():
        result["code"] = 0
        result["msg"] = "Get resume successfully!"
        result["count"] = list.count()
        result["data"] = []
        for item in list:
            # item.pop('_id')  # 解决TypeError: Object of type 'ObjectId' is not JSON serializable
            result["data"].append(item)
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
    return jsonify(result)
