from django.conf import settings
from django.contrib.auth import login, authenticate, logout, mixins
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views import View
from django import http
import re, json

from django_redis import get_redis_connection

from meiduo_mall.utils.views import LoginRequiredView
from users.models import User, Address
from meiduo_mall.utils.response_code import RETCODE
from users.utils import genreate_verify_email_url,check_cerify_email_token
from celery_tasks.email.tasks import send_verify_email

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
        response.set_cookie('username', user.username, max_age=(settings.SESSION_COOKIE_AGE if remembered else None))
        return response

class LogoutView(View):
    #退出登陆
    def get(self, request):
        logout(request)
        #重定向到登陆页面
        response = redirect('/login/')
        #删除cookies保存的user信息
        response.delete_cookie('username')

        return response

# class InfoView(View):
#     def get(self, request):
#         #获取用户对象
#         user = request.user
#         #判断用户是否登陆，如果是返回用户中心，如果不是返回登陆界面
#         if user.is_authenticated:
#             return render(request, 'user_center_info.html')
#         else:
#             return redirect('/login/?next=/info/')


# class InfoView(View):
#     #装饰器方法展示用户中心
#     @method_decorator(login_required)
#     def get(self, request):
#         return render(request, 'user_center_info.html')

class InfoView(mixins.LoginRequiredMixin, View):
    #扩展类展示用户中心
    def get(self, request):
        return render(request, 'user_center_info.html')

class EmailView(LoginRequiredView):
    #接收请求体中的email, body {'email':'xxxxx'}
    def put(self, request):
        json_str = request.body.decode()#body返回的是bytes类型数据,所以解码转为json字符串
        json_dict = json.loads(json_str)#将json字符串转为json字典
        email = json_dict.get('email')

        #校验邮箱
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return http.HttpResponseForbidden('邮箱格式错误')

        #获取当前当前登陆用户user对象
        user = request.user
        #给user字段赋值
        user.email = email
        user.save()
        #当设置好邮箱后，应该就对用户邮箱发个邮件
        #生成邮箱激活url
        verify_url = genreate_verify_email_url(user)
        #cerely异步进行发送邮件
        send_verify_email.delay(email,verify_url)
        #响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '添加邮箱成功'})

class EmailVerificationView(View):
    """激活邮箱"""
    def get(self, request):
        #获取到查询参数token
        token = request.GET.get('token')
        if token is None:
            return http.HttpResponseForbidden('缺少token参数')

        # 对token进行解密并查询到要激活邮箱的那个用户
        user = check_cerify_email_token(token)
        # 如果没有查询到user,提前响应
        if user is None:
            return http.HttpResponseForbidden('token无效')
        # 如果查询到user,修改它的email_active字段为True,再save()
        user.email_active = True
        user.save()
        #响应
        return redirect('/info/')

class AddressView(LoginRequiredView):
    """用户收货地址"""

    def get(self, request):
        user = request.user
        # 查询出来当前用户的所有未被逻辑删除的收货地址
        address_qs = Address.objects.filter(user=user, is_deleted=False)

        # 把查询集里面的模型转换成字典,然后再添加到列表中
        addresses_list = []
        for address_model in address_qs:
            addresses_list.append({
                'id': address_model.id,
                'title': address_model.title,
                'receiver': address_model.receiver,
                'province_id': address_model.province_id,
                'province': address_model.province.name,
                'city_id': address_model.city_id,
                'city': address_model.city.name,
                'district_id': address_model.district_id,
                'district': address_model.district.name,
                'place': address_model.place,
                'mobile': address_model.mobile,
                'tel': address_model.tel,
                'email': address_model.email
            })

        # 获取到用户默认收货地址的id
        default_address_id = user.default_address_id

        # 包装要传入模型的渲染数据
        context = {
            'addresses': addresses_list,
            'default_address_id': default_address_id
        }
        return render(request, 'user_center_site.html', context)

class CreateAddressView(LoginRequiredView):
    """新增收货地址"""

    def post(self, request):

        # 判断用户当前收货地址的数量,不能超过20
        count = Address.objects.filter(user=request.user, is_deleted=False).count()
        # count = request.user.addresses.filter(is_deleted=False).count()
        if count >= 20:
            return http.JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '收货地址数量超过上限'})

        # 接收请求体 body数据
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 校验
        if all([title, receiver, province_id, city_id, district_id, place, mobile]) is False:
            return http.HttpResponseForbidden('缺少必传参数')

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseForbidden('参数email有误')
        # 新增收货地址
        address_model = Address.objects.create(
            user=request.user,
            title=title,
            receiver=receiver,
            province_id=province_id,
            city_id=city_id,
            district_id=district_id,
            place=place,
            mobile=mobile,
            tel=tel,
            email=email
        )
        # 如果当前用户还没有默认收货地址,就把当前新增的收货地址直接设置为它的默认地址
        if request.user.default_address is None:
            request.user.default_address = address_model
            request.user.save()

        # 把新增的收货地址再转换成字典响应回去
        address_dict = {
            'id': address_model.id,
            'title': address_model.title,
            'receiver': address_model.receiver,
            'province_id': address_model.province_id,
            'province': address_model.province.name,
            'city_id': address_model.city_id,
            'city': address_model.city.name,
            'district_id': address_model.district_id,
            'district': address_model.district.name,
            'place': address_model.place,
            'mobile': address_model.mobile,
            'tel': address_model.tel,
            'email': address_model.email
        }

        # 响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '添加收货地址成功', 'address': address_dict})

class UpdateDestroyAddressView(LoginRequiredView):
    """收货地址修改和删除"""

    def put(self, request, address_id):

        # 接收请求体 body数据
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 校验
        if all([title, receiver, province_id, city_id, district_id, place, mobile]) is False:
            return http.HttpResponseForbidden('缺少必传参数')

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseForbidden('参数email有误')

        # 查询出要修改的模型对象
        try:
            address_model = Address.objects.get(id=address_id, user=request.user, is_deleted=False)
        except Address.DoesNotExist:
            return http.HttpResponseForbidden('address_id无效')

        # Address.objects.filter(id=address_id).update(
        address_model.title = title
        address_model.receiver = receiver
        address_model.province_id = province_id
        address_model.city_id = city_id
        address_model.district_id = district_id
        address_model.place = place
        address_model.mobile = mobile
        address_model.tel = tel
        address_model.email = email
        address_model.save()
        # )
        # 如果使用update去修改数据时,auto_now 不会重新赋值
        # 如果是调用save做的修改数据,才会对auto_now 进行重新赋值

        # 把修改后的的收货地址再转换成字典响应回去
        address_dict = {
            'id': address_model.id,
            'title': address_model.title,
            'receiver': address_model.receiver,
            'province_id': address_model.province_id,
            'province': address_model.province.name,
            'city_id': address_model.city_id,
            'city': address_model.city.name,
            'district_id': address_model.district_id,
            'district': address_model.district.name,
            'place': address_model.place,
            'mobile': address_model.mobile,
            'tel': address_model.tel,
            'email': address_model.email
        }

        # 响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '修改收货地址成功', 'address': address_dict})

    def delete(self, request, address_id):
        """删除收货地址"""
        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return http.HttpResponseForbidden('address_id无效')

        # 逻辑删除
        address.is_deleted = True
        address.save()

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '删除地址成功'})

class UpdateAddressTitleView(LoginRequiredView):
    """修改收货地址标题"""

    def put(self, request, address_id):

        # 接收前端传入的新标题
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')

        # 查询指定id的收货地址,并校验
        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return http.HttpResponseForbidden('address_id无效')

        # 重新给收货地址模型的title属性赋值
        address.title = title
        address.save()

        # 响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})

class DefaultAddressView(LoginRequiredView):
    """设置用户默认收货地址"""

    def put(self, request, address_id):

        # 查询指定id的收货地址,并校验
        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return http.HttpResponseForbidden('address_id无效')
        # 获取当前user模型对象
        user = request.user
        # 给user的default_address 重写赋值
        user.default_address = address
        user.save()

        # 响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})

class ChangePasswordView(LoginRequiredView):
    """修改用户密码"""

    def get(self, request):
        return render(request, 'user_center_pass.html')

    def post(self, request):
        """修改密码逻辑"""
        # 接收请求中的表单数据
        query_dict = request.POST
        old_pwd = query_dict.get('old_pwd')
        new_pwd = query_dict.get('new_pwd')
        new_cpwd = query_dict.get('new_cpwd')

        # 校验
        if all([old_pwd, new_pwd, new_cpwd]) is False:
            return http.HttpResponseForbidden('缺少必传参数')

        user = request.user
        if user.check_password(old_pwd) is False:
            return render(request, 'user_center_pass.html', {'origin_pwd_errmsg': '原始密码错误'})

        if not re.match(r'^[0-9A-Za-z]{8,20}$', new_pwd):
            return http.HttpResponseForbidden('密码最少8位，最长20位')
        if new_pwd != new_cpwd:
            return http.HttpResponseForbidden('两次输入的密码不一致')

        # 修改用户密码
        user.set_password(new_pwd)
        user.save()

        return redirect('/logout/')