from django.shortcuts import render,redirect
from .models import *
from django.core.cache import cache
from django_redis import get_redis_connection
from django.views.generic import View
from django.core.paginator import Paginator

from order.models import OrderGoods
# Create your views here.

class Index(View):
    def get(self,request):
        #判断缓存中是否有数据
        context = cache.get('index_con')
        if context is None:
            #获取所有的商品分类
            goodstypes= GoodsType.objects.all()
            #获取首页轮播商品图
            goodsbanner= IndexGoodsBanner.objects.all().order_by('index')
            #获取首页活动的数据
            promotion= IndexPromotionBanner.objects.all().order_by('index')

            for type in goodstypes:
                # 获取分类数据图片展示的数据
                image_type_info = IndexTypeGoodsBanner.objects.filter(type=type,display_type=1).order_by('index')
                #获取以文字展示的分类数据
                title_type_info = IndexTypeGoodsBanner.objects.filter(type=type,display_type=0).order_by('index')

                type.image_type_info = image_type_info
                type.title_type_info = title_type_info

            context={
                'types':goodstypes,
                'banner':goodsbanner,
                'promotion':promotion,
            }
            #缓存查询查来的数据
            cache.set('index_con',context,3600)

        # 获取购物车里的数据,先判断用户是否登陆
        if request.user.is_authenticated():
            # 购物车数据存在缓存中
            con = get_redis_connection("default")
            # 用户对应再数据库里的键
            # 获取用户id
            user_id = request.user.id

            cart_key = 'cart_{}'.format(user_id)

            cart_num = con.hlen(cart_key)
            print(cart_num)
        else:
            cart_num = '0'
        context['cart_num']=cart_num

        return render(request,'goods/index.html',context)

#url设计：127.0.0.1/detail商品id
class Detail(View):
    '''商品详情页视图'''

    def get(self,request,sku_id):
        try:
            sku_id= int(sku_id)
            # 根据商品查询对应的商品数据
            goods = GoodsSKU.objects.get(id=sku_id)
        except:
            return redirect('/index')

        #查询所有商品的分类
        types = GoodsType.objects.all()

        #查询当前分类的新品推荐
        new_goods = GoodsSKU.objects.filter(type=goods.type).order_by('-create_time')[0:2]

        #查询评论
        commits= OrderGoods.objects.filter(sku=goods)

        #查询购物车当前商品数
        # 获取购物车里的数据,先判断用户是否登陆
        if request.user.is_authenticated():
            # 假设用本机的redis数据库里编号为9数据库来存储购物车数据

            con = get_redis_connection("default")
            # 用户对应再数据库里的键
            # 获取用户id
            user_id = request.user.id
            cart_key = 'cart_{}'.format(user_id)
            #获取购物车商品的数量
            cart_num = con.hlen(cart_key)

            #构造一个存储商品浏览记录的键
            histor_key = 'histor{}'.format(user_id)

            #为了防止出现重复的数据，添加之前要删除当前列表中的该数据值
            con.lrem(histor_key, 0, goods.id)
            #把商品的id存入缓存中
            con.lpush(histor_key,goods.id)

            #对浏览记录进行长度处理
            con.ltrim(histor_key,0,5)

        else:
            cart_num = '0'

        context = {
            'goods':goods,
            'types':types,
            'new_goods':new_goods,
            'commits':commits,
            'cart_num':cart_num,
        }
        return render(request,'goods/detail.html',context)


class GoodsList(View):
    '''商品列表页的视图'''
    def get(self,request,type_id,num):
        try:
            type_id = int(type_id)
            #查询当前分类
            type = GoodsType.objects.get(id=type_id)
        except:
            return redirect('/index')

        #根据分类查询当前分类所有的商品信息
        goods_suk= GoodsSKU.objects.filter(type = type)

        # 获取当前分类新品推荐数据
        new_goods = goods_suk.order_by('-create_time')[0:2]

        #按规则排序
        index_num = request.GET.get('num_index')
        print(index_num)
        # print(type(index_num))
        if index_num=='1':
            goods_suk=goods_suk.order_by('price')

        elif index_num=='2':
            goods_suk = goods_suk.order_by('sales')

        else:
            goods_suk = goods_suk.order_by('id')
            index_num ='0'


        #查询出来的商品进行分页，每页一个商品
        pages =Paginator(goods_suk,2)
        #获取页码总数
        page_sum =pages.num_pages

        #获取第一页的内容
        try:
            num = int(num)
        except:
            num=1
        if num > pages.num_pages or num<=0:
            num=1
        page = pages.page(num)

        #判断页码总数是否大于3
        if page_sum > 3:
            #判断当前页码是不是第一页
            if num ==1:
                page_list = [i for i in range(1,3+1)]
            # 判断当前页码是不是第最后一页
            elif num ==page_sum:
                page_list = [i for i in range(num+1-3,num+1)]
            else:
                page_list = [i for i in range(num-3//2, num+3//2+1)]

        else:
            page_list=pages.page_range





        #获取所有的分类信息
        types = GoodsType.objects.all()

        # 获取购物车里的数据,先判断用户是否登陆
        if request.user.is_authenticated():
            # 购物车数据存在缓存中
            con = get_redis_connection("default")
            # 用户对应再数据库里的键
            # 获取用户id
            user_id = request.user.id

            cart_key = 'cart_{}'.format(user_id)

            cart_num = con.hlen(cart_key)
        else:
            cart_num = '0'


        context = {
            'type':type,
            'page_list':page_list,
            'goods_list':page,
            'new_goods':new_goods,
            'types':types,
            'cart_num':cart_num,
            'index_num':index_num
        }

        return render(request,'goods/list.html',context)



