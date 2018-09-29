# 登录注册业务逻辑
from . import passport_bp
from flask import request, abort, current_app, make_response
from info.utits.captcha.captcha import captcha
from info import redis_store, constants


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











