from flask import current_app, jsonify
from flask import session

from info import constants
from info.models import User, News
from info.utits.response_code import RET
from . import news_bp
from flask import render_template


#http://127.0.0.1:5000/news/1
@news_bp.route('/<int:news_id>')
def get_detail_news(news_id):
    """展示新闻详情页面"""
    # -------------------用户数据查询------------------
    # 1.获取用户id-
    user_id = session.get("user_id")
    # 用户id有值才去查询用户数据
    user = None  # type: User
    if user_id:
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询用户对象异常")

    """
    if user:
        # user：对象 --> 字典
        user_info = user.to_dict()

    #数据格式：
    data= {
        "user_info"： {"id": self.id}
    }

    #在模板中获取方法
    data.user_info.nick_name: 获取用户昵称
    """
    # -------------------点击排行新闻数据查询------------------
    try:
        news_rank_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询点击排行数据异常")

    # news_rank_list = [news对象1,news对象2, ...]
    # news_rank_dict_list = [{新闻字典},{新闻字典}]
    # 字典列表容器
    news_rank_dict_list = []
    for news_obj in news_rank_list if news_rank_list else []:
        # 将新闻对象转换成新闻字典
        news_dict = news_obj.to_dict()
        # 将字典装到一个列表中
        news_rank_dict_list.append(news_dict)

    # -------------------新闻详情数据查询------------------
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询新闻详情异常")

    # 新闻对象转字典
    news_dict = news.to_dict()

    data = {
        "user_info": user.to_dict() if user else None,
        "news_rank_list": news_rank_dict_list,
        "news": news_dict
    }

    return render_template("news/detail.html", data=data)