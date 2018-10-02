from celery import current_app
from flask import abort,g
from flask import render_template

from info.models import User, News, Category
from info.moduls.news import news_blu
from info import constants
from info.utits.common import user_login_data


@news_blu.route('/<int:news_id>')
@user_login_data
def news_detail(news_id):
    global news
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        abort(404)

    if not news:
        # 返回数据未找到的页面
        abort(404)

    news.clicks += 1

    # 获取点击排行数据
    news_list = None
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS).all()
    except Exception as e:
        current_app.logger.error(e)

    click_news_list = []
    for news in news_list if news_list else []:
        click_news_list.append(news.to_basic_dict())

    data = {
        "news": news.to_dict(),
        "click_news_list": click_news_list,
        "user_info": g.user.to_dict() if g.user else None,
    }
    return render_template('news/detail.html',data = data)

