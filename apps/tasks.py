#!/usr/bin/env/python
# -*-coding:utf-8 -*-


from django.core.mail import send_mail
from celery import task
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from django.conf import settings
from django.template import loader
from goods.models import *
import os



@task
def send_register_active_email(email,username):

    ser= Serializer(settings.SECRET_KEY,3600)

    token = ser.dumps({'confirm':username}).decode()

    msg='欢迎【{}】注册天天生鲜网上商城点击下面地址进行账户激活：------<a href="http://127.0.0.1:8000/user/activa{}">点击激活"http://127.0.0.1:8000/activation{}</a>------'.format(username,token,token)
    send_mail('天天生鲜账户激活','',settings.EMAIL_FROM,
              [email],
              html_message=msg)
import time

@task
def generate_static_index_html():
    '''生成首页的静态页面'''
    # 获取所有的商品分类
    time.sleep(2)
    goodstypes = GoodsType.objects.all()
    # 获取首页轮播商品图
    goodsbanner = IndexGoodsBanner.objects.all().order_by('index')
    # 获取首页活动的数据
    promotion = IndexPromotionBanner.objects.all().order_by('index')

    for type in goodstypes:
        # 获取分类数据图片展示的数据
        image_type_info = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')
        # 获取以文字展示的分类数据
        title_type_info = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')

        type.image_type_info = image_type_info
        type.title_type_info = title_type_info

    # 获取购物车里的数据,先判断用户是否登陆

    cart_num = '0'

    context = {
        'types': goodstypes,
        'banner': goodsbanner,
        'promotion': promotion,
        'cart_num': cart_num
    }
    #获取首页的模板文件
    temp = loader.get_template('goods/index.html')
    #渲染htlm页面
    html= temp.render(context)

    #打开文件写入html内容
    #拼接路径
    file_path = os.path.join(settings.BASE_DIR,'static','index.html')

    # /home/sxt/Desktop/DEME1/fresh_store/static/index.html
    #html页面写入
    with(open(file_path,'w')) as f:
        f.write(html)






