from django.conf.urls import url

from oauth import views

urlpatterns = [
    #获取图形验证码
    url(r'^qq/authorization/$', views.QQAuthUrlView.as_view()),
    url(r'^oauth_callback/$', views.QQAuthUrlView.as_view()),
]