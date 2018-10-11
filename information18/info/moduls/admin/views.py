
from flask import current_app
from flask import request, redirect, url_for
from flask import session
from info import db
from info.models import User
from . import admin_bp
from flask import render_template


@admin_bp.route('/', methods=['GET', 'POST'])
def admin_index():
    """管理员首页"""
    return render_template("admin/index.html")


# 127.0.0.1:5000/admin/login
@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    """管理员用户登录接口"""
    if request.method == 'GET':
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









