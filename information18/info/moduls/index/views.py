import logging
from flask import current_app, render_template, session, jsonify
from info.utits.response_code import RET
from . import index_bp
from info import redis_store
from info.models import User, News, Category
from info import constants


#2. 使用蓝图
@index_bp.route('/')
def hello_world():
    # -------------------用户数据查询------------------
    #1.获取用户id-
    user_id = session.get("user_id")
    # 用户id有值才去查询用户数据
    user = None # type: User
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


    # -----------获取新闻分类数据----------
    categories = Category.query.all()
    # 定义列表保存分类数据
    categories_dicts = []

    for category in categories if categories else []:
        # 拼接内容
        Category_dict = category.to_dict()
        categories_dicts.append(Category_dict)


    data = {
        "user_info": user.to_dict() if user else None,
        "news_rank_list": news_rank_dict_list,
        "categories": categories_dicts
    }
    # 返回模板文件
    return render_template("news/index.html",data=data)


# 浏览器默认会往这个路径发送请求获取网站图片（定时请求）
@index_bp.route('/favicon.ico')
def favicon():
    """返回网站图标"""
    """
    Function used internally to send static files from the static
        folder to the browser
    # 内部发送静态文件函数，将static文件夹下的静态文件发送到浏览器
    """
    return current_app.send_static_file('news/favicon.ico')