"""
Created on 2018/8/20
@Author: Jeff Yang
"""

import pymongo
from flask import Flask, render_template, request, jsonify

from app.views.cjol import cjol
from app.views.job51 import job51
from app.views.lagou import lagou

app = Flask(__name__)
app.register_blueprint(cjol, url_prefix='/cjol')
app.register_blueprint(job51, url_prefix='/job51')
app.register_blueprint(lagou, url_prefix='/lagou')


@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


if __name__ == '__main__':
    app.run()
