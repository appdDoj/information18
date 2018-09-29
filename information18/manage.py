from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from info import create_app, db
from flask import current_app
import logging



"""
从单一职责的角度思考：manage.py文件专门用来做项目的启动文件即可，其他配置放到别的文件
"""
# app = create_app("production")

# 开发环境的app对象
app = create_app("development")

#6.创建管理对象
manager = Manager(app)

#7.创建迁移对象
Migrate(app, db)

#8.添加迁移命令
manager.add_command("db", MigrateCommand)



if __name__ == '__main__':
    # 使用管理对象开启flask
    manager.run()
