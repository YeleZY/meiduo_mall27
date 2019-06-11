from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.views import View
from django import http
import re
from users.models import User

class RegisterView(View):

    def get(self, request):
        return render(request, 'register.html')
    # 接收用户请求数据
    def post(self, request):
        query_dict = request.POST

        username = query_dict.get('username')
        password = query_dict.get('password')
        password2 = query_dict.get('password2')
        mobile = query_dict.get('mobile')
        sms_code = query_dict.get('sms_code')
        allow = query_dict.get('allow')

        # 数据校验
        if all([username, password, password2, mobile, allow])is False:
            return http.HttpResponseForbidden('缺少必传参数')

        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入5-20个字符的用户名')

        if not re.match(r'^[a-zA-Z0-9]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20个字符的密码')

        if password2 != password:
            return http.HttpResponseForbidden('两次密码不一致')

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('请输入有效的手机号')

        # 业务逻辑
        #用户登陆成功保存账号密码并对密码进行加密
        user = User.objects.create(username=username, password=password, mobile=mobile)
        #用户登陆成功保存用户信息到session中
        login(request, user)
        #登陆成功后响应跳转首页
        return redirect('/')

