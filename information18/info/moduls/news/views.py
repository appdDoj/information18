from . import news_bp
from flask import render_template


#http://127.0.0.1:5000/news/1
@news_bp.route('/<int:news_id>')
def get_detail_news(news_id):
    """展示新闻详情页面"""
    return render_template("news/detail.html")