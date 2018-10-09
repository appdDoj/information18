from flask import g
from . import profile_bp
from flask import render_template
from info.utits.common import user_login_data


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