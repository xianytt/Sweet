
from django.conf.urls import url
from .views import *

urlpatterns = [
    url(r'^index$',Index.as_view()),
    url(r'^detail(?P<sku_id>.+)/$',Detail.as_view()),  #商品详情页
    url(r'^list(?P<type_id>.+)/(?P<num>.*)$',GoodsList.as_view())  #商品列表页


]
