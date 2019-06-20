from django.conf.urls import url
from django.contrib import admin
from . import views
urlpatterns = [
    url(r'^register/$', views.RegisterView.as_view()),
    url(r'^usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/$', views.UsernameCountView.as_view()),
    url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view()),
    url(r'^login/$', views.LoginView.as_view()),
    url(r'^logout/$', views.LogoutView.as_view()),
    url(r'^info/$', views.InfoView.as_view()),
    url(r'^emails/$', views.EmailView.as_view()),
    url(r'^emails/verification/$', views.EmailVerificationView.as_view()),
    url(r'^addresses/$', views.AddressView.as_view()),
    # 新增收货地址
    url(r'^addresses/create/$', views.CreateAddressView.as_view()),
    # 修改和删除收货地址
    url(r'^addresses/(?P<address_id>\d+)/$', views.UpdateDestroyAddressView.as_view()),
    # 修改收货地址标题
    url(r'^addresses/(?P<address_id>\d+)/title/$', views.UpdateAddressTitleView.as_view()),
    # 设置默认收货地址
    url(r'^addresses/(?P<address_id>\d+)/default/$', views.DefaultAddressView.as_view()),
    # 修改用户密码
    url(r'^password/$', views.ChangePasswordView.as_view()),
]
