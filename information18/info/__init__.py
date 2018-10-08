import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis
from flask_wtf.csrf import CSRFProtect, generate_csrf
# 帮助我们将flask中的session存储位置进行调整（内存--redis）
from flask_session import Session
from config import config_dict
from info.utits.common import do_index_class

# 没有app对象暂时不初始化，只是声明
db = SQLAlchemy()
# 初始化redis对象（全局对象） 并且声明类型
redis_store = None  # type: StrictRedis


def setup_log(config_name):
    """记录日志函数"""
    # 获取配置类
    config_class = config_dict[config_name]

    # 设置日志的记录等级
    logging.basicConfig(level=config_class.LOG_LEVEL)  # 调试debug级

    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小(100M)、保存的日志文件个数上限
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)

    # 创建日志记录的格式: 日志等级 输入日志信息的文件名 行数 日志信息
    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')

    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)

    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)


# 相当于ofo，传入原材料--小黄
# 传入项目配置名称-返回对应配置的app
# config_name == "development" -- 开发环境的app对象
# config_name == "production"  -- 线上环境的app对象
def create_app(config_name):
    """创建app的函数 （工厂方法）"""

    # 0. 记录日志信息
    setup_log(config_name)
    # 1.创建app对象
    app = Flask(__name__)
    # 将项目配置信息关联到app
    # config_dict["development"] -- DevelopmentConfig配置类
    # 1.1 获取配置类
    config_class = config_dict[config_name]
    # 1.2 将配置类和app关联
    app.config.from_object(config_class)

    # 2.创建数据库对象
    # 懒加载思想 延迟加载
    db.init_app(app)

    # 3.创建redis数据库对象
    # decode_responses 将二进制数据转成字符串
    global redis_store
    redis_store = StrictRedis(host=config_class.REDIS_HOST,
                              port=config_class.REDIS_PORT,
                              db=config_class.REDIS_NUM,
                              decode_responses=True
                              )

    """
    #4.初始化csrf保护机制
    #保护机制帮我们实现csrf_token的获取:
        1.从request的cookies中提取csrf_token
        2.从ajax请求的请求头headers中提起X-CSRFToken字段
    获取到这个两个值然后做比较验证操作
    """
    csrf = CSRFProtect(app)

    # 使用钩子函数统一设置cookie值
    @app.after_request
    def set_csrftoken(response):
        #1.生成csrf_token随机值
        csrf_token = generate_csrf()
        #2.借助response对象设置csrf_token值到cookie中
        response.set_cookie("csrf_token", csrf_token)
        #3.返回响应对象
        return response

    # 添加过滤器
    app.add_template_filter(do_index_class, "do_index_class")

    # 5.初始化拓展Session对象
    Session(app)

    # 注册蓝图对象到app中

    # 注册蓝图的时候在来导入（延迟导入解决循环导入文件）
    from info.moduls.index import index_bp
    # 注册首页的蓝图对象
    app.register_blueprint(index_bp)

    # 注册 登录、注册模块蓝图
    from info.moduls.passport import passport_bp
    app.register_blueprint(passport_bp)

    # 注册新闻详情模块的蓝图
    from info.moduls.news import news_bp
    app.register_blueprint(news_bp)

    # 返回app
    return app