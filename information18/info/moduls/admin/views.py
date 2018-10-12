import time
from datetime import datetime, timedelta
from flask import current_app
from flask import g
from flask import request, redirect, url_for
from flask import session
from info import db
from info.models import User
from . import admin_bp
from flask import render_template
from info.utits.common import user_login_data


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
    for i in range(0, 31): # 1， 2， 3 .. 31
        """
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









