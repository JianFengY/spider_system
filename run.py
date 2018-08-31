"""
Created on 2018/8/20
@Author: Jeff Yang
"""

from flask import Flask, render_template

from views.cjol import cjol
from views.job51 import job51
from views.lagou import lagou

app = Flask(__name__)
app.register_blueprint(cjol, url_prefix='/cjol')
app.register_blueprint(job51, url_prefix='/job51')
app.register_blueprint(lagou, url_prefix='/lagou')


# 本文件放在app目录下时在命令行运行会报错ModuleNotFoundError: No module named 'app'
@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


if __name__ == '__main__':
    app.debug = True
    app.run()
