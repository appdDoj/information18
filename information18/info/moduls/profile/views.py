from flask import current_app
from flask import g, jsonify
from flask import request
from flask import session

from info import db
from info.utits.response_code import RET
from . import profile_bp
from flask import render_template
from info.utits.common import user_login_data


#127.0.0.1:5000/user/base_info
@profile_bp.route('/base_info', methods=['GET', 'POST'])
@user_login_data
def user_base_info():
    """展示用户基本资料页面"""
    # 获取用户对象
    user = g.user

    # get请求返回用户基本资料模板
    if request.method == 'GET':

        # 组织返回数据
        data = {
            "user_info": user.to_dict() if user else None
        }
        return render_template("profile/user_base_info.html", data=data)

    # 修改用户基本资料接口（POST）
    """
    1.获取参数
        1.1 signature:个性签名，nick_name:昵称，gender:性别, user: 用户对象
    2.校验参数
        2.1 非空判断
        2.2 gender in ['MAN', 'WOMAN']
    3.逻辑处理
        3.0 上传的属性赋值到当前user对象中
        3.1 更新session，中nick_name数据
        3.3 保存回数据库
    4.返回值
    """
    #1.1 用户对象 新闻id comment_id评论的id，action:(点赞、取消点赞)
    params_dict = request.json
    signature = params_dict.get("signature")
    nick_name = params_dict.get("nick_name")
    gender = params_dict.get("gender")


    #2.1 非空判断
    if not all([signature, nick_name, gender]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")

    #2.2 用户是否登录判断
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    #2.3 gender in ['MAN', 'WOMAN']
    if gender not in ["MAN", "WOMAN"]:
        return jsonify(errno=RET.PARAMERR, errmsg="action参数错误")

    # 3.0 上传的属性赋值到当前user对象中
    user.signature = signature
    user.nick_name = nick_name
    user.gender = gender

    # 3.1 更新session，中nick_name数据
    session["nick_name"] = nick_name
    # 3.3 保存回数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存数据库异常")

    # 4.返回值
    return jsonify(errno=RET.OK, errmsg="保存用户基本资料成功")


#127.0.0.1:5000/user/info
@profile_bp.route('/info')
@user_login_data
def get_user_info():
    """展示用户个人中心数据"""
    # 获取用户对象
    user = g.user
    # 组织返回数据
    data = {
        "user_info": user.to_dict() if user else None
    }
    return render_template("profile/user.html", data=data)