from redis import StrictRedis
import logging


class Config(object):
    """项目配置 (父类)"""
    DEBUG = True

    # MYSQL数据库的配置信息
    # 数据库链接配置
    SQLALCHEMY_DATABASE_URI = "mysql://root:root@127.0.0.1:3306/information18"
    # 关闭数据库修改后跟踪
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # 取代db.session.commit()方法
    # 在数据库会话对象结束的时候自动帮助提交信息到数据库
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True

    #redis数据库配置信息
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379
    # 选择第9个数据库进行存储
    REDIS_NUM = 8

    #设置加密字符串
    SECRET_KEY = "ASLKDJALKSJDALSDJALKSDJASLKDJ98ADU9"
    #利用flask-session拓展包，将flask中的session存储位置从内存调整到redis的配置信息
    # 存储到那种数据库的类型：redis
    SESSION_TYPE = 'redis'
    # 初始化一个redis实例对象给他赋值
    SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_NUM)
    # 开启session数据的加密操作
    SESSION_USE_SIGNER = True
    # 取消永久存储
    SESSION_PERMANENT = False
    # 设置默认有效时长(24小时)
    PERMANENT_SESSION_LIFETIME = 86400


class DevelopmentConfig(Config):
    """开发环境的项目配置"""
    DEBUG = True
    # 设置开发环境的日志级别为：DEBUG
    LOG_LEVEL = logging.DEBUG


class ProductionConfig(Config):
    """生成环境的项目配置"""
    DEBUG = False
    # 设置线上环境的日志级别为：WARNING
    LOG_LEVEL = logging.WARNING

# 提一个接口暴露给外界调用
# 使用方法: config_dict["development"] --> DevelopmentConfig
config_dict = {
    "development": DevelopmentConfig,
    "production": ProductionConfig
}