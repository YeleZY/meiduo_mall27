from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View

class LoginRequiredView(LoginRequiredMixin, View):
    #自定义一个登陆判断类
    pass