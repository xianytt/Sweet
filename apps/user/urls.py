
from django.conf.urls import url
from .views import *

from django.contrib.auth.decorators import login_required


urlpatterns = [
    url(r'^/register$',Register.as_view()), #使用类视图,注册
    url(r'^/activa(?P<token>.+)$',Activa.as_view()),#激活
    url(r'/login$',Login.as_view()),#登陆
    url(r'^/info$',UserInfo.as_view()),#用户信息页
    url(r'^/site$',UserSite.as_view()),#用户地址页面
    url(r'^/order/$',UserOrder.as_view()),#用户订单页面
    # url(r'^/info$',login_required(UserInfo.as_view())), #用户信息
    # url(r'^/order$',login_required(UserOrder.as_view())),#用户订单
    # url(r'^/site$',login_required(UserSite.as_view())),  #用户地址
    url(r'^/logout$', Logout.as_view()),  # 退出登陆
]




