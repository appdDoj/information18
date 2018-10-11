from flask import Blueprint, redirect
#1.创建蓝图对象
admin_bp = Blueprint("admin", __name__, url_prefix='/admin')

#3.导入views文件
from .views import *


@admin_bp.before_request
def before_request():
    """是否是管理员的判断"""

    #http://127.0.0.1:5000/admin/login
    # 如果访问的链接是上面的地址，就不应该走下面的逻辑判断，不应该拦截，直接让他访问视图函数接口
    print(request.url)
    if request.url.endswith("/admin/login"):
        pass
    else:
        # http://127.0.0.1:5000/admin/index
        # 访问的url不是http://127.0.0.1:5000/admin/login才需要拦截重定向
        # 获取用户id
        user_id = session.get("user_id")
        # 获取是否有管理员权限
        is_admin = session.get("is_admin", False)

        """
        1.用户未登录 --> 引导到新闻首页进行登录
        2.或者登录的用户不是管理员 ——>不应该访问/admin/login  -->引导到首页 /login
        """
        if not user_id or not is_admin:
            # 引导到新闻首页
            return redirect("/")