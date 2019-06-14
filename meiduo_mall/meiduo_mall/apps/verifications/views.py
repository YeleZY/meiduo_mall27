from random import randint

from PIL.Image import logger
from django import http
from django.shortcuts import render

# Create your views here.
from django.views import View
from django_redis import get_redis_connection

from meiduo_mall.libs.captcha.captcha import captcha
from meiduo_mall.utils.response_code import RETCODE
from verifications import constants
from verifications.constants import IMAGE_CODE_REDIS_EXPIRES
from celery_tasks.sms.tasks import send_sms_code


class ImageCodeView(View):
    #图片验证码
    def get(self, request, uuid):
        #使用captcha扩展包生成图片验证码
        name, image_code_text, image_bytes = captcha.generate_captcha()
        #指定保存的数据库路径
        redis_conn = get_redis_connection('verify_code')
        #用uuid为唯一标识保存到redis数据库
        redis_conn.setex(uuid, IMAGE_CODE_REDIS_EXPIRES, image_code_text)
        #返回响应图片验证码bytes类型指定格式为'image/png'
        return http.HttpResponse(image_bytes, content_type='image/png')


class SmsCodeView(View):
    #发送短信验证码
    def get(self, request, mobile):
        #创建reids数据库对象
        redis_conn = get_redis_connection('verify_code')
        #尝试获取数据库里面手机是否有发短信的标记
        redis_flag = redis_conn.get('redis_flag_%s' % mobile)
        #如果有返回
        if redis_flag:
            return http.JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '获取手机短信过于频繁'})
        #接受客户端数据
        image_code_client = request.GET.get('image_code')
        uuid = request.GET.get('uuid')
        #数据校验

        if all([image_code_client, uuid])is False:
            return http.HttpResponseForbidden('缺少参数')

        #获取redis中的图片验证码
        image_code_server = redis_conn.get(uuid)
        #删除redis中的图片验证码
        redis_conn.delete(uuid)
        #判断验证码是否过期
        if image_code_server is None:
            return http.HttpResponseForbidden('图片验证码过期')

        #没过期再进行数据格式转换
        image_code_server = image_code_server.decode()
        #进行图片验证码比对
        if image_code_client.lower() != image_code_server.lower():
            return http.HttpResponseForbidden('图片验证码输入错误')

        #随机生成一个6位数的数字作为短信验证码
        sms_code = '%06d' % randint(0, 999999)
        logger.info(sms_code)

        #redis管道技术
        pl = redis_conn.pipeline()
        #保存短信验证码到redis数据库，方便后期注册时校验
        pl.setex('sms_%s' %mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        #设置60s时间不能发短信验证码
        pl.setex('send_flag_%s' %mobile, 60, 1)
        #执行管道
        pl.execute()

        #给当前手机发送短信验证码
        send_sms_code.delay(mobile, sms_code)
        #响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '发送短信验证码成功'})