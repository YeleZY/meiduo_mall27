from django.conf import settings
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.views import View
from django import http
import re

from django_redis import get_redis_connection

from users.models import User
from meiduo_mall.utils.response_code import RETCODE

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
        if all([username, password, password2, mobile, sms_code, allow])is False:
            return http.HttpResponseForbidden('缺少必传参数')

        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入5-20个字符的用户名')

        if not re.match(r'^[a-zA-Z0-9]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20个字符的密码')

        if password2 != password:
            return http.HttpResponseForbidden('两次密码不一致')

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('请输入有效的手机号')

        #创建redis连接对象
        redis_conn = get_redis_connection('verify_code')
        #获取redis中的短信验证码
        sms_code_server = redis_conn.get('sms_%s' %mobile)

        #判断验证码是否过期
        if sms_code_server is None:
            return http.HttpResponseForbidden('短信验证码已过期')

        #删除redis中已经被使用的验证码
        redis_conn.delete('sms_%s' %mobile)
        #由bytes类型转换为str类型
        sms_code_server = sms_code_server.decode()

        #判断用户输入的验证码是否正确
        if sms_code != sms_code_server:
            return http.HttpResponseForbidden('验证码输入有误')

        # 业务逻辑
        #用户登陆成功保存账号密码并对密码进行加密
        user = User.objects.create_user(username=username, password=password, mobile=mobile)
        #用户登陆成功保存用户信息到session中
        login(request, user)
        #登陆成功后响应跳转首页
        return redirect('/')

#判断用户名是否重复注册
class UsernameCountView(View):

    def get(self, request, username):
        #使用username查询user表,得到mobile的数量
        count = User.objects.filter(username=username).count()
        content = {'count': count, 'code':RETCODE.OK, 'errmsg': 'OK'}

        return http.JsonResponse(content)

#判断手机是否重复注册
class MobileCountView(View):

    def get(self, request, mobile):
        #使用username查询user表,得到mobile的数量
        count = User.objects.filter(mobile=mobile).count()
        content = {'count': count, 'code':RETCODE.OK, 'errmsg': 'OK'}

        return http.JsonResponse(content)

class LoginView(View):
    #展示登陆界面
    def get(self, request):
        return render(request, 'login.html')

    #接收请求
    def post(self, request):
        #接受登陆数据
        query_dict = request.POST
        username = query_dict.get('username')
        password = query_dict.get('password')
        remembered = query_dict.get('remembered')

        #登陆认证
        user = authenticate(request, username=username, password=password)
        #验证密码
        if user is None:
            return render(request, 'login.html', {'account_errmsg': '账号或密码错误'})

        #状态保持
        login(request,user)
        #判断用户是否勾选了记住登陆
        if remembered is None:
            request.session.set_expiry(0)#session为None是指定过期时间为2周，为0是浏览器关闭删除
            #cookies为None是指定浏览器关闭就删除

        #重定向到首页
        response = redirect(request.GET.get('next', '/'))
        # 保存用户信息到cookies
        response.set_cookie('username', user.username, max_age=(settings.SECCION_COOKIE_AGE if remembered else None))
        return response