from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from info import create_app, db
from flask import current_app, jsonify
import logging

from info.models import User
from info.utits.response_code import RET

"""
从单一职责的角度思考：manage.py文件专门用来做项目的启动文件即可，其他配置放到别的文件
"""
# app = create_app("production")

# 开发环境的app对象
app = create_app("development")

# 6.创建管理对象
manager = Manager(app)

# 7.创建迁移对象
Migrate(app, db)

# 8.添加迁移命令
manager.add_command("db", MigrateCommand)

"""
使用方法：
python3 manage.py createsuperuser -n "账号名称" -p "密码"
python3 manage.py createsuperuser --name "账号名称" --password "密码"

"""


@manager.option('-n', '--name', dest="name")
@manager.option('-p', '--password', dest="password")
def createsuperuser(name, password):
    """创建管理员用户接口"""
    if not all([name, password]):
        return "参数不足"

    # 创建用户对象
    user = User()
    # 昵称
    user.nick_name = name
    # 账号
    user.mobile = name
    user.password = password
    # 设置为管理员
    user.is_admin = True

    # 保存回数据库
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存管理员用户异常")

    return "创建管理员用户成功"


if __name__ == '__main__':
    # 使用管理对象开启flask
    manager.run()
