import logging
from flask import current_app, render_template, session, jsonify
from flask import request

from info.utits.response_code import RET
from . import index_bp
from info import redis_store
from info.models import User, News, Category
from info import constants


@index_bp.route('/news_list')
def get_news_list():
    """获取新闻列表数据"""
    """
    1.获取参数
        1.1 分类id: cid,当前页码：page（默认值：第一页）, 每一页多少条数据：per_page（默认值：10条）
    2.校验参数
        2.1 非空判断
        2.2 整型强制类型转换
    3.逻辑处理
        3.1 分页查询
        3.2 对象列表转字典列表
    4.返回值
    """
    # 1.1 分类id: cid,当前页码：page（默认值：第一页）, 每一页多少条数据：per_page（默认值：10条）
    param_dict = request.args
    cid = param_dict.get('cid', "1")
    page = param_dict.get('page', "1")
    per_page = param_dict.get('per_page', "10")

    # 2.1 非空判断
    if not cid:
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")
    #2.2 整型强制类型转换
    try:
        cid = int(cid)
        page = int(page)
        per_page = int(per_page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数格式错误")

    """
        if cid == 1:
            # 只需要根据新闻创建时间的降序排序
            paginate = News.query.order_by(News.create_time.desc()).paginate(page, per_page, False)
        else:
            # 需要根据新闻创建时间的降序排序和分类id
            paginate = News.query.filter(News.category_id == cid).order_by(News.create_time.desc()).paginate(page, per_page, False)
    """
    # 条件列表
    filters = []
    if cid != 1: # 2 3 4 5
        # == 符号被sqlalchemy底层给重写了__eq__返回的是一个查询条件，而不是Bool值
        filters.append(News.category_id == cid)
    # 3.1 分页查询
    # *filters 解包
    try:
        paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page, per_page, False)
        # 当前页码所有数据
        items = paginate.items
        # 当前页码
        current_page = paginate.page
        # 总页码
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询新闻列表数据异常")

    # 3.2 对象列表转字典列表
    news_dict_list = []
    for news in items if items else []:
        news_dict_list.append(news.to_dict())

    # 3.3 组织返回数据
    data = {
        "news_list": news_dict_list,
        "current_page": current_page,
        "total_page": total_page
    }
    return jsonify(errno=RET.OK, errmsg="查询新闻列表数据成功", data=data)


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

    # -------------------新闻分类数据查询------------------
    try:
        categories = Category.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询分类数据异常")

    # 分类的对象列表转换成字典列表
    category_dict_list = []
    for category in categories if categories else []:
        # 将分类对象转换成字典
        category_dict_list.append(category.to_dict())

    data = {
        "user_info": user.to_dict() if user else None,
        "news_rank_list": news_rank_dict_list,
        "categories": category_dict_list
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