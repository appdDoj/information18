# 登录注册业务逻辑
from . import passport_bp
from flask import request, abort, current_app, make_response, jsonify, session
from info.utits.captcha.captcha import captcha
from info import redis_store, constants, db
from info.utits.response_code import RET
from info.models import User
import json
import re
import random
from info.lib.yuntongxun.sms import CCP
from datetime import datetime


# 127.0.0.1：5000/passport/login
@passport_bp.route('/login', methods=['POST'])
def login():
    """用户登录后端接口"""
    """
    1.获取参数
        1.1 mobile手机号码，password未加密密码
    2.校验参数
        2.1 非空判断
        2.2 手机号码正则校验
    3.逻辑处理
        3.0 查询用户是否存在
        3.1 验证密码是否一致
        3.2 不一致： 提示密码填写错误
        3.3 一致：记录用户登录信息
    4.返回值
        登录成功
    """
    # 1.1 mobile手机号码，password未加密密码
    param_dict = request.json
    mobile = param_dict.get("mobile", "")
    password = param_dict.get("password", "")
    #2.1 非空判断
    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")
    #2.2 手机号码正则校验
    if not re.match('1[3578][0-9]{9}', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机格式错误")

    #3.0 查询用户是否存在
    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询用户对象异常")
    # 用户不存在
    if not user:
        return jsonify(errno=RET.NODATA, errmsg="用户不存在")

    #3.1 验证密码是否一致
    if not user.check_passowrd(password):
        # 3.2 不一致： 提示密码填写错误
        return jsonify(errno=RET.DATAERR, errmsg="密码填写错误")

    #3.3 一致：记录用户登录信息
    session["user_id"] = user.id
    session["nick_name"] = user.mobile
    session['mobile'] = user.mobile

    # 更新用户最后一次登录时间
    user.last_login = datetime.now()
    # 修改了用户对象属性，要想更新到数据库必须commit
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()

    #4.登录成功
    return jsonify(errno=RET.OK, errmsg="登录成功")


# 127.0.0.1:5000/passport/register
@passport_bp.route('/register', methods=['POST'])
def register():
    """用户注册后端接口"""
    """
    1.获取参数
        1.1 mobile手机号码，smscode短信验证码，password未加密密码
    2.校验参数
        2.1 非空判断
        2.2 手机号码正则校验
    3.逻辑处理
        3.1 根据SMS_CODE_手机号码key去redis中获取正确的短信验证码值
            3.1.1 有值：删除
            3.1.2 没有值： 过期了
        3.2 拿用户填写的短信验证码值和正确的短信验证码值进行比较
        3.3 不一致：提示短信验证码填写错误
        3.4 一致：使用User模型创建用户对象，并且赋值
        3.5 一般需求：用户注册成功，第一次应该给他登录成功，记录session数据
    4.返回值
        注册成功
    """
    # 1.1 mobile手机号码，smscode短信验证码，password未加密密码
    param_dict = request.json
    mobile = param_dict.get("mobile", "")
    smscode = param_dict.get("smscode", "")
    password = param_dict.get("password", "")

    #2.1 非空判断
    if not all([mobile, smscode, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")
    #2.2 手机号码正则校验
    if not re.match('1[3578][0-9]{9}', mobile):
        # 手机号码格式有问题
        current_app.logger.error("手机号码格式错误")
        return jsonify(errno=RET.PARAMERR, errmsg="手机号码格式错误")

    #3.1 根据SMS_CODE_手机号码key去redis中获取正确的短信验证码值
    try:
        real_smscode = redis_store.get("SMS_CODE_%s" % mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询真实短信验证码值异常")
    #3.1.1 有值：从redis中将短信验证码值删除
    if real_smscode:
        redis_store.delete("SMS_CODE_%s" % mobile)
    # 3.1.2 没有值： 过期了
    else:
        return jsonify(errno=RET.NODATA, errmsg="短信验证码过期")

    #3.2 拿用户填写的短信验证码值和正确的短信验证码值进行比较
    if real_smscode != smscode:
        # 3.3 不一致：提示短信验证码填写错误
        return jsonify(errno=RET.DATAERR, errmsg="短信验证码填写错误")

    #3.4 一致：使用User模型创建用户对象，并且赋值
    user = User()
    user.nick_name = mobile
    # 将手机号码赋值
    user.mobile = mobile
    # 当前时间作为最后一次登录时间
    user.last_login = datetime.now()
    #TODO: 密码加密处理
    # user.make_password_hash(password)
    user.password = password

    # 将用户对象存储到数据库
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        # 数据库回滚
        db.session.rollback()
    #3.5 一般需求：用户注册成功，第一次应该给他登录成功，记录session数据
    session["user_id"] = user.id
    session["nick_name"] = user.mobile
    session["mobile"] = user.mobile

    #4.返回注册成功
    return jsonify(errno=RET.OK, errmsg="注册成功")


#2.使用蓝图
# 127.0.0.1:5000/passport/image_code?code_id=uuid编号  (GET)
@passport_bp.route('/image_code')
def get_image_code():
    """获取验证码图片的接口 (GET)"""
    """
    1.获取参数
        1.1 获取code_id全球唯一的uuid编号
    2.参数校验
        2.1 判断code_id是否有值
    3.逻辑处理
        3.1 生成验证码图片&生成验证码图片上面的真实值
        3.2 以code_id作为key将验证码图片上面的真实值存储到redis中
    4.返回值
        4.1 返回图片给前端展示
    """

    #1.1 获取code_id全球唯一的uuid编号
    code_id = request.args.get('code_id', "")
    #2.1 判断code_id是否有值
    if not code_id:
        # code_id不存在
        abort(404)

    #3.1 生成验证码图片&生成验证码图片上面的真实值
    image_name, real_image_code, image_data = captcha.generate_captcha()

    try:
        # 3.2 以code_id作为key将验证码图片上面的真实值存储到redis中
        redis_store.setex("imageCodeId_%s" % code_id, constants.IMAGE_CODE_REDIS_EXPIRES, real_image_code)
    except Exception as e:
        current_app.logger.error(e)
        # 如果保存数据到redis异常，就报错
        abort(500)

    #4.1 返回图片给前端展示
    #构建响应对象
    response = make_response(image_data)
    #设置响应数据的类型 , Content-Type:返回值类型
    #作用：能够兼容所有浏览器的数据格式
    response.headers["Content-Type"] = 'image/JPEG'
    return response


#127.0.0.1:5000/passport/sms_code
@passport_bp.route('/sms_code', methods=['POST'])
def send_sms_code():
    """点击发送短信验证码后端接口"""
    """
    1.获取参数
        1.1 手机号码mobile，用户填写的图片验证码值image_code，image_code_id全球唯一的UUID编号
    2.校验参数
        2.1 非空判断
        2.2 手机号码格式正则判断
    3.逻辑处理
        3.1 image_code_id编号去redis数据库取出图片验证码的真实值
            3.1.1 有值： 从redis数据库删除真实值（防止拿着相同的值多次验证）
            3.1.2 没有值：图片验证码值在redis中过期
        3.2 比较用户填写的图片验证码值和真实的验证码值是否一致
            TODO: 手机号码有了（用户是否已经注册的判断，用户体验最好），
            根据手机号码去查询用户是否有注册，有注册，不需要再注册，没有注册才去发送短信验证码
            一致：填写正确，生成6位的短信验证码值，发送短信验证码
            不一致：提示图片验证码填写错误
        3.3 将生成6位的短信验证码值 存储到redis数据库
    4.返回值
        4.1 发送短信验证码成功
    """
    #1.1 手机号码mobile，用户填写的图片验证码值image_code，image_code_id全球唯一的UUID编号
    # dict = json.loads(request.data) 能够将json字符串转换成dict
    # 能够获取前端发送过来的json数据，同时能够将json字符串转换成python的对象
    param_dict = request.json
    # 手机号码
    mobile = param_dict.get("mobile", "")
    # 用户填写的图片验证值
    image_code = param_dict.get("image_code", "")
    # uuid编号
    image_code_id = param_dict.get("image_code_id", "")

    #2.1 非空判断
    if not all([mobile, image_code, image_code_id]):
        current_app.logger.error("参数不足")
        # 返回json格式的错误信息
        return jsonify({"errno": RET.PARAMERR, "errmsg": "参数不足"})
    #2.2 手机号码格式正则判断
    if not re.match('1[3578][0-9]{9}', mobile):
        # 手机号码格式有问题
        current_app.logger.error("手机号码格式错误")
        return jsonify(errno=RET.PARAMERR, errmsg="手机号码格式错误")

    real_image_code = None
    try:
        # 3.1 image_code_id编号去redis数据库取出图片验证码的真实值
        real_image_code = redis_store.get("imageCodeId_%s" % image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询图片验证码真实值异常")

    #3.1.1 有值： 从redis数据库删除真实值（防止拿着相同的值多次验证）
    if real_image_code:
        redis_store.delete("imageCodeId_%s" % image_code_id)
    # 3.1.2 没有值：图片验证码值在redis中过期
    else:
        return jsonify(errno=RET.NODATA, errmsg="图片验证码值在redis中过期")

    #3.2 比较用户填写的图片验证码值和真实的验证码值是否一致
    #细节1：全部转成小写
    #细节2：设置redis数据decode操作
    if real_image_code.lower() != image_code.lower():
        return jsonify(errno=RET.DATAERR, errmsg="图片验证码填写错误")

    """
        TODO: 手机号码有了（用户是否已经注册的判断，用户体验最好），
                根据手机号码去查询用户是否有注册，有注册，不需要再注册，没有注册才去发送短信验证码
    """
    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询用户数据异常")

    # 用户存在
    if user:
        return jsonify(errno=RET.DATAEXIST, errmsg="用户已经注册")

    #一致：填写正确，生成6位的短信验证码值，发送短信验证码
    # 生成6位的短信验证码值
    sms_code = random.randint(0, 999999)
    sms_code = "%06d" % sms_code

    try:
        ccp = CCP()
        result = ccp.send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES / 60], 1)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="云通讯发送短信验证码失败")

    # 发送短信验证失败
    if result != 0:
        return jsonify(errno=RET.THIRDERR, errmsg="云通讯发送短信验证码失败")

    #3.3 将生成6位的短信验证码值 存储到redis数据库
    try:
        redis_store.setex("SMS_CODE_%s" %mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存短信验证码到数据库异常")

    #4.返回值
    return jsonify(errno=RET.OK, errmsg="发送短信验证码成功")







