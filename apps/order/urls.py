
from django.conf.urls import url
from .views import *

urlpatterns = [
    url(r'^/order/',Order.as_view()),  #返回订单提交页面

    url(r'^/commit/',OrderCommit.as_view()),

    url(r'^/pay',OederPay.as_view()),  #订单支付宝支付
    url(r'^/check',CheckPay.as_view())    #订单支付结果查询

]
