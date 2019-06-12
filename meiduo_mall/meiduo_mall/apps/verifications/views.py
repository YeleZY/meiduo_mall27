from django import http
from django.shortcuts import render

# Create your views here.
from django.views import View
from django_redis import get_redis_connection

from meiduo_mall.libs.captcha.captcha import captcha
from verifications.constants import IMAGE_CODE_REDIS_EXPIRES


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
        return http.HttpResponseForbidden(image_bytes, content_type='image/png')
