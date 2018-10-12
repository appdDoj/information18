from flask import abort
from flask import current_app, jsonify
from flask import g
from flask import request
from flask import session
from info import constants, db
from info.models import User, News, Comment, CommentLike
from info.utits.common import user_login_data
from info.utits.response_code import RET
from . import news_bp
from flask import render_template


@news_bp.route('/comment_like', methods=['POST'])
@user_login_data
def comment_like():
    """评论的点赞、取消点赞接口"""
    """
    1.获取参数
        1.1 comment_id:评论id， action:点赞、取消点赞的行为（add,remove）
    2.校验参数
        2.1 非空判断
        2.2 action in ['add', 'remove']
    3.逻辑处理
        3.0 根据comment_id查询该评论
        3.1 action==add表示点赞：查询commentlike模型对象，如果不存在，再创建commentlike
        3.2 action==remove表示取消点赞：查询commentlike模型对象，如果存在，再删除这种点赞关系
    4.返回值
    """
    #1.1 用户对象 新闻id comment_id评论的id，action:(点赞、取消点赞)
    params_dict = request.json
    comment_id = params_dict.get("comment_id")
    action = params_dict.get("action")
    user = g.user

    #2.1 非空判断
    if not all([comment_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")

    #2.2 用户是否登录判断
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    #2.3 action in ["add", "remove"]
    if action not in ["add", "remove"]:
        return jsonify(errno=RET.PARAMERR, errmsg="action参数错误")

    # 3.0 根据comment_id查询该评论
    try:
        comment = Comment.query.get(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询评论对象异常")
    if not comment:
        return jsonify(errno=RET.NODATA, errmsg="评论不存在")

    # 当前用户登录成功
    if user:
        # 3.1 action==add表示点赞：查询commentlike模型对象，如果不存在，再创建commentlike
        if action == "add":
            # 点赞
            try:
                commentlike = CommentLike.query.filter(CommentLike.comment_id == comment_id,
                                                       CommentLike.user_id == user.id).first()
            except Exception as e:
                current_app.logger.error(e)
                return jsonify(errno=RET.DBERR, errmsg="查询点赞评论模型异常")
            # 当前用户没有对当前评论点过赞
            if not commentlike:
                # 创建CommentLike模型对象给其属性赋值
                commentlike_obj = CommentLike()
                commentlike_obj.user_id = user.id
                commentlike_obj.comment_id = comment_id

                # 添加到数据库
                db.session.add(commentlike_obj)
                # 评论的总点赞数量进行累加
                comment.like_count += 1
        # 3.2 action==remove表示取消点赞：查询commentlike模型对象，如果存在，再删除这种点赞关系
        else:
            # 取消点赞
            try:
                commentlike = CommentLike.query.filter(CommentLike.comment_id == comment_id,
                                                       CommentLike.user_id == user.id).first()
            except Exception as e:
                current_app.logger.error(e)
                return jsonify(errno=RET.DBERR, errmsg="查询点赞评论模型异常")
            # 当前用户对当前评论点过赞的情况才能取消点赞
            if commentlike:
                # 从数据库删除第三张表维护的关系，即表示：取消点赞
                db.session.delete(commentlike)
                # 评论的总点赞数量进行减一
                comment.like_count -= 1

    # 将点赞、取消点赞的修改提交回数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        # 回滚
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存评论点赞模型对象异常")

    #4.返回值
    return jsonify(errno=RET.OK, errmsg="OK")


@news_bp.route('/news_comment', methods=['POST'])
@user_login_data
def news_comment():
    """发布评论接口（主评论，子评论）"""
    """
    1.获取参数
        1.1 comment_str:评论内容，news_id:新闻id， parent_id：父评论id（非必传参数）
    2.校验参数
        2.1 非空判断
    3.逻辑处理
        3.0 根据news_id查询新闻是否存在
        3.1 parent_id没有值：发布主评论
        3.2 parent_id有值：发布子评论
    4.返回值
    """
    #1.1 comment_str:评论内容，news_id:新闻id， parent_id：父评论id（非必传参数）
    params_dict = request.json
    comment_str = params_dict.get("comment")
    news_id = params_dict.get("news_id")
    parent_id = params_dict.get("parent_id")
    # 获取用户对象
    user = g.user

    #2.1 非空判断
    if not all([news_id, comment_str]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")

    #2.2 用户是否登录判断
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    # 3.0 根据news_id查询新闻是否存在
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询新闻对象异常")
    if not news:
        return jsonify(errno=RET.NODATA, errmsg="新闻不存在")

    # 3.1 parent_id没有值：发布主评论
    comment_obj = Comment()
    comment_obj.user_id = user.id
    comment_obj.news_id = news_id
    comment_obj.content = comment_str
    # 3.2 parent_id有值：发布子评论
    if parent_id:
        comment_obj.parent_id = parent_id

    # 3.3 保存到数据库
    try:
        db.session.add(comment_obj)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存评论对象异常")

    #4.返回值
    return jsonify(errno=RET.OK, errmsg="评论成功", data=comment_obj.to_dict())


@news_bp.route('/news_collect', methods=['POST'])
@user_login_data
def news_collect():
    """用户点击收藏、取消收藏后端接口实现"""
    """
    1.获取参数
        1.1 news_id：新闻id, action:表示收藏和取消收藏的行为（'collect', 'cancel_collect'）
    2.校验参数
        2.1 非空判断
        2.2 action必须是在['collect', 'cancel_collect']
    3.逻辑处理
        3.0 根据news_id查询该新闻
        3.1 action是collect表示收藏: 将新闻添加到user.collection_news列表中
        3.2 action是cancel_collect表示取消收藏: 将新闻从user.collection_news列表中移除
    4.返回值
    """
    # 获取当前用户
    user = g.user
    # 1.1 news_id：新闻id, action:表示收藏和取消收藏的行为（'collect', 'cancel_collect'）
    param_dict = request.json
    news_id = param_dict.get("news_id")
    action = param_dict.get("action")

    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")
    # 2.1 非空判断
    if not all([action, news_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")
    # 2.2 action必须是在['collect', 'cancel_collect']
    if action not in ['collect', 'cancel_collect']:
        return jsonify(errno=RET.PARAMERR, errmsg="参数内容错误")

    # 3.0 根据news_id查询该新闻
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询新闻数据异常")

    if not news:
        return jsonify(errno=RET.NODATA, errmsg="没有改新闻")

    # 3.1 action是collect表示收藏: 将新闻添加到user.collection_news列表中
    if action == "collect":
        # 收藏
        user.collection_news.append(news)
    # 3.2 action是cancel_collect表示取消收藏: 将新闻从user.collection_news列表中移除
    else:
        # 取消收藏
        user.collection_news.remove(news)

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存新闻数据到收藏列表异常")

    #4.返回值
    return jsonify(errno=RET.OK, errmsg="OK")


#http://127.0.0.1:5000/news/1
@news_bp.route('/<int:news_id>')
@user_login_data
def get_detail_news(news_id):
    """展示新闻详情页面"""
    # -------------------用户数据查询------------------
    # # 1.获取用户id-
    # user_id = session.get("user_id")
    # # 用户id有值才去查询用户数据
    # user = None  # type: User
    # if user_id:
    #     try:
    #         user = User.query.get(user_id)
    #     except Exception as e:
    #         current_app.logger.error(e)
    #         return jsonify(errno=RET.DBERR, errmsg="查询用户对象异常")
    """
        if user:
            # user：对象 --> 字典
            user_info = user.to_dict()

        #数据格式：
        data= {
            "user_info"： {"id": self.id}
        }

        #在模板中获取方法
        data.user_info.nick_name: 获取用户昵称
        """

    # 使用装饰器获取当前用户信息
    user = g.user


    # -------------------点击排行新闻数据查询------------------
    try:
        news_rank_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询点击排行数据异常")

    # news_rank_list = [news对象1,news对象2, ...]
    # news_rank_dict_list = [{新闻字典},{新闻字典}]
    # 字典列表容器
    news_rank_dict_list = []
    for news_obj in news_rank_list if news_rank_list else []:
        # 将新闻对象转换成新闻字典
        news_dict = news_obj.to_dict()
        # 将字典装到一个列表中
        news_rank_dict_list.append(news_dict)

    # -------------------新闻详情数据查询------------------
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询新闻详情异常")

    #如果新闻不存在，抛出异常
    if not news:
        return abort(404)

    # 新闻访问量累加
    news.clicks += 1

    # 新闻对象转字典
    news_dict = news.to_dict()

    # -------------------查询当前用户是否收藏该新闻------------------
    # is_collected = True表示收藏 反之
    is_collected = False
    # 是否关注的标志位
    is_followed = False

    # 用户已经登录
    if user:
        if news in user.collection_news:
            # 表示该用户已经收藏该新闻
            is_collected = True

    # 获取到作者
    author = None
    try:
        author = User.query.filter(User.id == news.user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="")

    # 当前用户存在&作者存在
    if user and author:
        """
        user: 当前用户  author：发布当前新闻的作者

        #1. 当前用户在作者的粉丝列表内，表示当前用户关注过该作者
        user in author.followers
        #2. 当前作者在用户的偶像列表内，表示当前用户关注过该作者
        author in user.followed
        """
        if author in user.followed:
            is_followed = True


    # -------------------查询当前新闻评论列表------------------
    # 获取评论对象列表：[comment对象1,comment对象2,....]
    try:
        comments = Comment.query.filter(Comment.news_id == news_id)\
            .order_by(Comment.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询评论对象异常")

    commentlike_id_list = []
    if user:
        # -------------------查询当前用户在当前新闻的评论里边具体点赞了那几条评论------------------
        # 1. 查询出当前新闻的所有评论，取得所有评论的id —>  comment_id_list: [1,2,3,4,5,6]
        comment_id_list = [comment.id for comment in comments]

        # 2.再通过评论点赞模型(CommentLike)查询当前用户点赞了那几条评论  —>[模型1,模型2...]
        try:
            commentlike_model_list = CommentLike.query.filter(CommentLike.comment_id.in_(comment_id_list),
                                     CommentLike.user_id == user.id).all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询评论点赞模型对象异常")
        # 3. 遍历上一步的评论点赞模型列表，获取所以点赞过的评论id（comment_like.comment_id）
        # commentlike_id_list => [1, 3, 4]
        commentlike_id_list = [commentlike_model.comment_id for commentlike_model in commentlike_model_list]

    # 评论对象列表转字典列表
    comment_dict_list = []
    for comment in comments if comments else []:
        # 评论字典
        comment_dict = comment.to_dict()
        # 借助评论字典携带is_like键值对，表示当前评论的点赞状态
        comment_dict["is_like"] = False
        """
        commentlike_id_list => [1, 3, 4]

        comment.id ==> 1  in [1, 3, 4] ==> comment_dict["is_like"] = True
        comment.id ==> 2  in [1, 3, 4] ==> comment_dict["is_like"] = False
        comment.id ==> 3  in [1, 3, 4] ==> comment_dict["is_like"] = True
        """
        # 遍历每一条评论的id是否在当前用户点过赞的评论id列中
        if comment.id in commentlike_id_list:
            comment_dict["is_like"] = True
        comment_dict_list.append(comment_dict)

    # 组织返回数据
    data = {
        "user_info": user.to_dict() if user else None,
        "news_rank_list": news_rank_dict_list,
        "news": news_dict,
        "is_collected": is_collected,
        "is_followed": is_followed,
        "comments": comment_dict_list
    }

    return render_template("news/detail.html", data=data)