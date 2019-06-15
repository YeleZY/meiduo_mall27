from django import http
from django.conf import settings
from django.shortcuts import render
from QQLoginTool.QQtool import OAuthQQ
from django.views import View
import logging

from meiduo_mall.utils.response_code import RETCODE

logger = logging.getLogger('django')
class QQAuthUrlView(View):
    #提供qq登陆url
    def get(self, request):
        #获取查询参数 next
        next = request.GET.get('next', '/')
        #创建oauthqq对象，并赋予属性
        auth_qq = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                          client_secret=settings.QQ_CLIENT_SECRET,
                          redirect_uri=settings.QQ_REDIRECT_URI,
                          state=next)

        #调用里面的方法获取拼接好的url
        login_url = auth_qq.get_qq_url()
        #响应json
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'login_url': login_url})

class QQAuthView(View):
    #OAuth2.0认证过程
    #qq登陆成功后的回调处理
    def get(self, request):
        #获取code
        code = request.GET.get('code')
        #判断code是否为空
        if code is None:
            return http.HttpResponseForbidden('缺少code')
        #创建qq登陆sdk对象
        auth_qq = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                          client_secret=settings.QQ_CLIENT_SECRET,
                          redirect_uri=settings.QQ_REDIRECT_URI,)
        try:
            #使用sdk中的get_access_token方法传入code获取token
            access_token = auth_qq.get_access_token(code)
            # 使用sdk中的get_access_openid方法传入token获取openid
            openid = auth_qq.get_open_id(access_token)
        except Exception as e:
            logger.error(e)
            return http.HttpResponseServerError('OAuth2.0认证失败')
