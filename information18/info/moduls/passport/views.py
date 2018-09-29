# 登录注册业务逻辑
from . import passport_bp
from flask import request, abort, current_app, make_response, jsonify
from info.utits.captcha.captcha import captcha
from info import redis_store, constants
from info.utits.response_code import RET
from info.models import User
import json
import re
import random
from info.lib.yuntongxun.sms import CCP

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
        return jsonify(errno=RET.PARAMERR, errmsg="图片验证码填写错误")

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
        ccp.send_template_sms("18520340803", [sms_code, constants.SMS_CODE_REDIS_EXPIRES / 60], 1)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="云通讯发送短信验证码失败")

    #3.3 将生成6位的短信验证码值 存储到redis数据库
    try:
        redis_store.setex("SMS_CODE_%s" %mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存短信验证码到数据库异常")

    #4.返回值
    return jsonify(errno=RET.OK, errmsg="发送短信验证码成功")







