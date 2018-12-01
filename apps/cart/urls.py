
from django.conf.urls import url
from .views import *


urlpatterns = [
    url(r'^/cart/',Cart.as_view()),  #显示购物车页面
    url(r'^/add/',AddCart.as_view()),  #添加数据
    url(r'^/update/',Update.as_view()),  #修改数据
    url(r'^/delete/',Delete.as_view()),  #删除数据

]
