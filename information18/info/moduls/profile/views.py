from flask import current_app
from flask import g, jsonify
from flask import request
from flask import session
from info.utits.pic_storage import pic_storage
from info import db
from info.utits.response_code import RET
from . import profile_bp
from flask import render_template
from info.utits.common import user_login_data
from info import constants
from info.models import User, Category


@profile_bp.route('/news_release', methods=['GET', 'POST'])
@user_login_data
def news_release():
    """新闻发布页面展示&发布新闻后端接口"""
    # 获取用户对象
    user = g.user
    if request.method == "GET":
        # 查询分类数据
        try:
            categories = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询分类数据异常")
        # 对象列表转字典列表
        category_dict_list = []
        for category in categories if categories else []:
            category_dict_list.append(category.to_dict())
        # 移除最新分类
        category_dict_list.pop(0)
        # 组织数据
        data = {
            "categories": category_dict_list
        }
        return render_template("profile/user_news_release.html", data=data)




# /user/collection?p=2
@profile_bp.route('/collection', methods=['GET', 'POST'])
@user_login_data
def user_collection_news():
    """获取用户收藏的新闻列表数据"""
    """
    1.获取参数
        1.1 p: 当前页码
    2.校验参数
        2.1 能否转成int类型
    3.逻辑处理
        3.0 对象user.collection_news进行分页查询
    4.返回值
    """
    # 1.1 p: 当前页码
    p = request.args.get("p", 1)
    # 获取用户对象
    user = g.user # type: User
    # 2.1 能否转成int类型
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数内容格式错误")

    collections = []
    current_page = 1
    total_page = 1
    #3.0 对象user.collection_news进行分页查询,
    # 真正使用collection_news的时候是一个列表，如果是去查询，就是一个查询对象
    try:

        paginate = user.collection_news.paginate(p, constants.USER_COLLECTION_MAX_NEWS, False)
        # 当前页码的所有数据
        collections = paginate.items
        # 当前页码
        current_page = paginate.page
        # 总页数
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询用户收藏分页数据异常")

    # 对象列表转字典列表
    collection_dict_list = []
    for news in collections if collections else []:
        collection_dict_list.append(news.to_basic_dict())

    # 组织数据
    data = {
        "collections": collection_dict_list,
        "current_page": current_page,
        "total_page": total_page
    }
    # 前后端不分离
    return render_template("profile/user_collection.html", data=data)


@profile_bp.route('/pass_info', methods=['GET', 'POST'])
@user_login_data
def pass_info():
    """修改用户密码的页面展示&业务逻辑"""
    # 获取用户对象
    user = g.user
    if request.method == 'GET':
        return render_template("profile/user_pass_info.html")

    # POST请求：修改密码
    """
    1.获取参数
        1.1 old_password:旧密码， new_password:新密码
    2.校验参数
        2.1 非空判断
    3.逻辑处理
        3.0 先校验旧密码是否填写正确
        3.1 将新的密码赋值到user对象属性中
        3.2 保存回数据库
    4.返回值
    """
    # 1.1 old_password:旧密码， new_password:新密码
    old_password = request.json.get('old_password')
    new_password = request.json.get('new_password')

    # 2.1 非空判断
    if not all([old_password, new_password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")

    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    # 3.0 先校验旧密码是否填写正确
    if not user.check_passowrd(old_password):
        # 旧密码填写错误
        return jsonify(errno=RET.DATAERR, errmsg="旧密码填写错误")
    # 3.1 将新的密码赋值到user对象属性中
    user.password = new_password

    # 3.2 保存回数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="修改密码异常")

    #4.返回值
    return jsonify(errno=RET.OK, errmsg="修改密码成功")


@profile_bp.route('/pic_info', methods=['GET', 'POST'])
@user_login_data
def pic_info():
    """修改用户头像接口"""

    # 获取用户对象
    user = g.user
    # GET请求：渲染修改用户图像页面
    if request.method == 'GET':
        return render_template("profile/user_pic_info.html")

    # POST请求，获取用户上传的图片，保存到七牛云
    try:
        pic_data = request.files.get('avatar').read()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="读取图片数据异常")

    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    # 调用封装好的工具类上传图片
    try:
        pic_name = pic_storage(pic_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="上传图片到七牛云异常")
    """
    方法1： avatar_url = 域名 + 图片名称
    方法2： avatar_url = 图片名称  （采用这种，方便后期修改域名）
    """
    # 保存图片名称到用户对象
    user.avatar_url = pic_name

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存用户头像数据异常")

    # 完整的图片url
    full_url = constants.QINIU_DOMIN_PREFIX + pic_name
    # 组织数据
    data = {
        "avatar_url": full_url
    }
    # 返回值
    return jsonify(errno=RET.OK, errmsg="修改用户头像成功", data=data)




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