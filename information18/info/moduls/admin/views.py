import time
from datetime import datetime, timedelta
from flask import current_app, jsonify, abort
from flask import g
from flask import request, redirect, url_for
from flask import session
from info import db
from info.models import User, News, Category
from info.utits.pic_storage import pic_storage
from info.utits.response_code import RET
from . import admin_bp
from flask import render_template
from info.utits.common import user_login_data
from info import constants


@admin_bp.route('/news_edit_detail', methods=['POST', 'GET'])
def news_edit_detail():
    """新闻编辑详情页面接口"""

    if request.method == "GET":
        """
        返回新闻详情页面

        url: /admin/news_edit_detail?news_id=1

        """
        # 获取新闻id
        news_id = request.args.get("news_id")

        if not news_id:
            return Exception("参数不足")
        # 查询新闻
        try:
            news = News.query.get(news_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="")
        # 新闻不存在
        if not news:
            return abort(404)

        # 新闻对象转成新闻字典
        news_dict = news.to_dict() if news else None

        # 查询所有分类
        try:
            categories = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="")

        # 对象列表转字典列表
        category_dict_list = []
        for category in categories if categories else []:
            category_dict = category.to_dict()
            # 默认分类id没有选中
            category_dict["is_selected"] = False
            # 当前新闻的分类id和遍历出来的某一个id相等，就选中
            if category.id == news.category_id:
                category_dict["is_selected"] = True
            category_dict_list.append(category_dict)

        # 组织数据
        data = {
            "news": news_dict,
            "categories": category_dict_list
        }

        return render_template("admin/news_edit_detail.html", data=data)

    # POST请求：新闻编辑
    """
    1.获取参数
        1.1 title:新闻标题，category_id:新闻分类id，digest:新闻摘要
            index_image:新闻主图片， content:新闻内容
    2.校验参数
        2.1 非空判断
    3.逻辑处理
        3.0 将图片上传到七牛云保存
        3.1 创建新闻对象，给各个属性赋值
        3.2 保存回数据库
    4.返回值
    """
    # 1.1 title:新闻标题，category_id:新闻分类id，digest:新闻摘要 index_image:新闻主图片， content:新闻内容，user:登录用户
    title = request.form.get("title")
    category_id = request.form.get("category_id")
    digest = request.form.get("digest")
    index_image = request.files.get("index_image")
    content = request.form.get("content")
    # 获取新闻id
    news_id = request.form.get("news_id")

    # 2.1 非空判断
    if not all([title, category_id, digest, content, news_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")

    # 如果图片有数据
    pic_name = None
    if index_image:
        try:
            index_image_data = index_image.read()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg="读取图片数据异常")

        # 3.0 将图片上传到七牛云保存
        try:
            pic_name = pic_storage(index_image_data)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.THIRDERR, errmsg="上传到七牛云失败")

    # 查询新闻对象
    news = None
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询新闻异常")
    if not news:
        return jsonify(errno=RET.NODATA, errmsg="新闻不存在")

    # 3.1 创建新闻对象，给各个属性赋值
    news.title = title
    news.category_id = category_id
    news.digest = digest
    news.content = content
    if pic_name:
        news.index_image_url = constants.QINIU_DOMIN_PREFIX + pic_name

    # 保存到数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存新闻数据异常")

    # 4.返回值
    return jsonify(errno=RET.OK, errmsg="发布新闻成功")


# /admin/news_edit?p=页码
@admin_bp.route('/news_edit')
def news_edit():
    """新闻编辑页面展示"""
    # 1.获取参数
    p = request.args.get("p", 1)
    # 2.校验参数
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        p = 1

    # 获取查询关键字
    keyswords = request.args.get("keyswords")
    filters = []
    if keyswords:
        filters.append(News.title.contains(keyswords))

    news_list = []
    current_page = 1
    total_page = 1
    try:
        paginate = News.query.filter(*filters). \
                   order_by(News.create_time.desc()). \
                   paginate(p, constants.ADMIN_NEWS_PAGE_MAX_COUNT, False)
        # 当前页码所有数据
        news_list = paginate.items
        # 当前页码
        current_page = paginate.page
        # 总页数
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询新闻列表数据异常")

    # 模型列表转换字典列表
    news_dict_list = []
    for news in news_list if news_list else []:
        news_dict_list.append(news.to_review_dict())

    data = {
        "news_list": news_dict_list,
        "current_page": current_page,
        "total_page": total_page
    }
    return render_template("admin/news_edit.html", data=data)


# /admin/news_review_detail?news_id=1
@admin_bp.route('/news_review_detail', methods=['POST', 'GET'])
@user_login_data
def news_review_detail():
    """新闻审核详情页面接口"""
    if request.method == "GET":

        # 获取新闻id
        news_id = request.args.get("news_id")

        if not news_id:
            return Exception("参数不足")

        # 查询新闻
        try:
            news = News.query.get(news_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询新闻异常")

        if not news:
            abort(404)

        # 对象转字典
        news_dict = news.to_dict() if news else None

        data = {
            "news": news_dict
        }
        # 返回审核页面，同时将新闻数据带回
        return render_template("admin/news_review_detail.html", data=data)

    """
    1.获取参数
        1.1 新闻id：news_id ,action：通过、拒绝
    2.校验参数
        2.1 非空判断
    3.逻辑处理
        3.0 根据新闻id查询新闻
        3.1 通过： news.status=0
        3.2 拒绝：news.status=-1 news.reason = 拒绝原因
    4.返回值

    """
    #1.1 新闻id：news_id ,action：通过、拒绝
    params_dict = request.json
    news_id = params_dict.get("news_id")
    action = params_dict.get("action")
    user = g.user

    #2.1 非空判断
    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")

    #2.2 用户是否登录判断
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    #2.3 action in ["accept", "reject"]
    if action not in ["accept", "reject"]:
        return jsonify(errno=RET.PARAMERR, errmsg="action参数错误")

    #3.0 根据新闻id查询新闻
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询新闻异常")
    if not news:
        return jsonify(errno=RET.NODATA, errmsg="新闻不存在")

    #3.1 通过： news.status=0
    if action == "accept":
        news.status = 0
    # 3.2 拒绝：news.status=-1 news.reason = 拒绝原因
    else:
        reason = request.json.get("reason")
        if reason:
            # 审核未通过
            news.status = -1
            # 拒绝原因
            news.reason = reason
        else:
            return jsonify(errno=RET.PARAMERR, errmsg="请填写拒绝原因")

    # 保存回数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存新闻异常")

    return jsonify(errno=RET.OK, errmsg="OK")


# /admin/news_review?p=页码
@admin_bp.route('/news_review')
def news_review():
    """新闻审核页面展示"""
    # 1.获取参数
    p = request.args.get("p", 1)

    # 2.校验参数
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        p = 1
    # 用户对象列表
    news_list = []
    current_page = 1
    total_page = 1
    # 获取查询关键字
    keywords = request.args.get("keywords")

    # 条件列表 默认条件：查询审核未通过&未审核的新闻
    filters = [News.status != 0]
    # 如果有关键字，将关键字条件添加到列表
    if keywords:
        filters.append(News.title.contains(keywords))
    try:
        paginate = News.query.filter(*filters).order_by(News.create_time.desc()) \
            .paginate(p, constants.ADMIN_NEWS_PAGE_MAX_COUNT, False)
        # 获取当前页码所有数据
        news_list = paginate.items
        # 当前页码
        current_page = paginate.page
        # 总页数
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询分页数据异常")

    # 对象列表转字典列表
    news_dict_list = []
    for news in news_list if news_list else []:
        news_dict_list.append(news.to_review_dict())

    # 组织数据
    data = {
        "news_list": news_dict_list,
        "current_page": current_page,
        "total_page": total_page
    }

    return render_template("admin/news_review.html", data=data)



# /admin/user_list?p=页码
@admin_bp.route('/user_list')
@user_login_data
def user_list():
    """用户列表接口"""
    # 1.获取参数
    p = request.args.get("p", 1)
    # 获取用户对象
    user = g.user
    # 2.校验参数
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        p = 1
    # 用户对象列表
    user_list = []
    current_page = 1
    total_page = 1
    try:
         paginate = User.query.filter(User.is_admin == False).order_by(User.create_time.desc())\
            .paginate(p, constants.ADMIN_USER_PAGE_MAX_COUNT, False)
         # 获取当前页码所有数据
         user_list = paginate.items
         # 当前页码
         current_page = paginate.page
         # 总页数
         total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询分页数据异常")

    # 对象列表转字典列表
    user_dict_list = []
    for user in user_list if user_list else []:
        user_dict_list.append(user.to_admin_dict())

    # 组织数据
    data = {
        "users": user_dict_list,
        "current_page": current_page,
        "total_page": total_page
    }

    return render_template("admin/user_list.html", data=data)




# /admin/user_count
@admin_bp.route('/user_count')
def user_count():
    """用户数据统计接口"""

    #1. 查询总人数
    total_count = 0
    try:
        #User.is_admin == False 统计的是普通用户
        total_count = User.query.filter(User.is_admin == False).count()
    except Exception as e:
        current_app.logger.error(e)

    # 2.查询月新增数
    mon_count = 0
    try:
        # 获取到本地的时间 tm_year：年 tm_mon:月  tm_day: 天
        now = time.localtime()
        # 2018-10-01
        # 2018-11-01
        # 2019-10-01
        # 代表每一个月的第一天（字符串）
        mon_begin = '%d-%02d-01' % (now.tm_year, now.tm_mon)
        # strptime：将时间字符串转换成时间格式
        mon_begin_date = datetime.strptime(mon_begin, '%Y-%m-%d')
        # 查询从本月第一天到今天为止新增的人数--月新增人数
        # User.create_time >= mon_begin_date： 用户创建时间大于月初第一天
        mon_count = User.query.filter(User.is_admin == False, User.create_time >= mon_begin_date).count()
    except Exception as e:
        current_app.logger.error(e)

    # 查询日新增数
    day_count = 0
    try:
        # 2018-10-11 00:00（今天）
        # 2018-10-12 00:00（明天）
        day_begin = '%d-%02d-%02d' % (now.tm_year, now.tm_mon, now.tm_mday)
        # 一天的开始时间 2018-10-11 00:00
        # 一天的结束时间 2018-10-11 23:59
        day_begin_date = datetime.strptime(day_begin, '%Y-%m-%d')
        # User.create_time > day_begin_date 你创建的时间小于一天的结束时间，大于一天的开始时间
        day_count = User.query.filter(User.is_admin == False, User.create_time > day_begin_date).count()
    except Exception as e:
        current_app.logger.error(e)

    # 查询图表信息
    # 获取到当天2018-10-11号 00:00:00时间
    now_date = datetime.strptime(datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d')
    # 定义空数组，保存数据
    # 当前时间往后推一个月
    active_date = []
    # 每一天的活跃人数
    active_count = []

    # 依次添加数据，再反转
    for i in range(0, 31): # 0 1， 2， 3 .. 30
        """
        #当前时间 now_date =   2018-10-12号 00:00:00
        #开始时间 begin_date = 2018-10-12号号 00:00:00
        #结束时间 end_date = 2018-10-12号 23:59:59 + 1天 = 2018-10-10号 24:00:00
        结束时间 = 开始时间 + 1天

        #当前时间 now_date =  2018-10-11号 00:00:00
        #开始时间 begin_date = 2018-10-11号 00:00:00
        #结束时间 end_date = 2018-11-11号 23:59:59 + 1天 = 2018-10-10号 24:00:00



        #当前时间 now_date =  2018-10-11号 00:00:00
        #开始时间 begin_date = 2018-10-10号 00:00:00
        #结束时间 end_date = 2018-10-10号 00:00:00 + 1天 = 2018-10-10号 24:00:00
        """
        begin_date = now_date - timedelta(days=i)
        end_date = begin_date + timedelta(days=1)

        # 添加当前时间
        active_date.append(begin_date.strftime('%Y-%m-%d'))
        count = 0
        try:
            # 当天活跃量： last_login最后一次登录时间 大于一天的开始，小于一天的结束
            count = User.query.filter(User.is_admin == False, User.last_login >= begin_date,
                                      User.last_login < end_date).count()
        except Exception as e:
            current_app.logger.error(e)
        # 添加每一天的活跃量count
        active_count.append(count)

    # 将数据反转
    active_date.reverse()
    active_count.reverse()

    data = {"total_count": total_count, "mon_count": mon_count, "day_count": day_count, "active_date": active_date,
            "active_count": active_count}

    return render_template('admin/user_count.html', data=data)




# 127.0.0.1:5000/admin/
@admin_bp.route('/index', methods=['GET', 'POST'])
@user_login_data
def admin_index():
    """管理员首页"""
    # 获取用户对象
    user = g.user
    data = {
        "user_info": user.to_dict() if user else None
    }
    return render_template("admin/index.html", data=data)


# 127.0.0.1:5000/admin/login
# http://127.0.0.1:5000/admin/login
@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    """管理员用户登录接口"""
    if request.method == 'GET':

        """
        管理员是否登录判断
        """
        user_id = session.get("user_id")
        is_admin = session.get("is_admin", False)

        if user_id and is_admin:
            # 跳转到管理员首页
            return redirect(url_for("admin.admin_index"))
        else:
            # 管理没有登录过
            return render_template("admin/login.html")

    # POST请求：管路员用户登录逻辑
    """
    1.获取参数
        1.1 name:账号，password：未加密密码
    2.校验参数
        2.1 非空判断
    3.逻辑处理
        3.0 根据name账号，查询管理员用户
        3.1 密码比对
        3.2 将管理员用户信息记录到session中
    4.返回值
    """
    #1.1 name:账号，password：未加密密码
    name = request.form.get("username")
    password = request.form.get("password")

    # 2.1 非空判断
    if not all([name, password]):
        return render_template("admin/login.html", errmsg="参数不足")

    # 3.0 根据name账号，查询管理员用户
    admin_user = None # type: User
    try:
        admin_user = User.query.filter(User.mobile == name, User.is_admin == True).first()
    except Exception as e:
        current_app.logger.error(e)
        return render_template("admin/login.html", errmsg="查询管理员用户异常")

    if not admin_user:
        return render_template("admin/login.html", errmsg="管理员用户不存在")

    # 3.1 密码比对
    if not admin_user.check_passowrd(password):
        return render_template("admin/login.html", errmsg="密码填写错误")

    # 将用户对象保存回数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return render_template("admin/login.html", errmsg="保存管理员用户异常")

    # 3.2 将管理员用户信息记录到session中
    session["nick_name"] = name
    session["mobile"] = name
    session["user_id"] = admin_user.id
    session["is_admin"] = True

    # 跳转到管理员首页
    return redirect(url_for("admin.admin_index"))









