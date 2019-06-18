import re

from django.contrib.auth.backends import ModelBackend

from users.models import User
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer,BadData
from django.conf import settings


def get_user_account(account):
    #通过传入的账户获取user
    try:
        if re.match(r'^1[3-9]\d{9}$', account):
            user_model = User.objects.get(mobile=account)
        else:
            user_model = User.objects.get(username=account)
    except User.DoesNotExist:
        return None
    return user_model


class UsernameMobileBackend(ModelBackend):
    #自定义认证后端
    def authenticate(self, request, username=None, password=None, **kwargs):
        #查询user，可以动态通过手机或用户名
        user = get_user_account(username)
        #判断user的密码对不对
        if user and user.check_password(password):
            return user

def genreate_verify_email_url(user):
    """拼接用户邮箱激活url"""
    # 创建加密对象
    serializer = Serializer(settings.SECRET_KEY, 60*60*24)
    # 包装要加密的字典数据
    data = {'user_id': user.id, 'user_email': user.email}
    #对字典进行加密
    token = serializer.dumps(data).decode()
    # 拼接用户激活邮箱url
    verify_url = settings.EMAIL_VERIFY_URL + '?token=' + token
    #返回响应
    return verify_url

def check_cerify_email_token(token):
    """对token进行解密并返回user或None"""
    # 创建加密对象
    serializer = Serializer(settings.SECRET_KEY, 60*60*24)
    try:
        data = serializer.loads(token)  # 解密
        user_id = data.get('user_id')  # 解密没有问题后取出里面数据
        email = data.get('user_email')
        try:
            user = User.objects.get(id=user_id, email=email)  # 查询唯一用户
            return user  # 查询到直接返回
        except User.DoesNotExist:
            return None

    except BadData:
        return None

