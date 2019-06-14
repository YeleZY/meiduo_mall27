import re

from django.contrib.auth.backends import ModelBackend

from users.models import User


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

