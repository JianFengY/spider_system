"""
Created on 2018/8/20
@Author: Jeff Yang
"""

import pymongo
from flask import Flask, render_template, request, jsonify

from app.views.cjol import cjol

app = Flask(__name__)
app.register_blueprint(cjol, url_prefix='/cjol')

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


@app.route('/51job')
def _51job():
    """51job爬虫"""
    return render_template('51job.html')


@app.route('/lagou')
def lagou():
    """lagou爬虫"""
    return render_template('lagou.html')


if __name__ == '__main__':
    app.run()
