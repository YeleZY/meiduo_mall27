from django.shortcuts import render
from django.views import View
from django import http
import re

class RegisterView(View):

    def get(self, request):
        return render(request, 'register.html')
    # 接收用户请求数据
    def post(self, request):
        query_dict = request.POST

        username = query_dict.get('username')
        passworld = query_dict.get('passworld')
        passworld2 = query_dict.get('passworld2')
        mobile = query_dict.get('mobile')
        sms_code = query_dict.get('sms_code')
        allow = query_dict.get('allow')

        # 数据校验
        if all([username, passworld, passworld2, mobile, allow])is False:
            return http.HttpResponseForbidden('缺少必传参数')

        if not re.match(r'^[a-zA-Z0-9_-]{5, 20}$', username):
            return http.HttpResponseForbidden('请输入5-20个字符的用户名')

        if not re.match(r'^[a-zA-Z0-9]{8,20}$', passworld):
            return http.HttpResponseForbidden('请输入8-20个字符的密码')

        if passworld2 != passworld:
            return http.HttpResponseForbidden('两次密码不一致')

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('请输入有效的手机号')


