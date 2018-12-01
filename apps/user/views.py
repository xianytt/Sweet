from django.shortcuts import render,redirect
from django.http import HttpResponse
from .models import User,Address
from django.conf import settings
from apps.tasks import *
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import re
from django.views.generic import View
from apps.mixin import LoginMixin
from django.db.models import Q

from django.core.paginator import Paginator
from order.models import OrderInfo,OrderGoods
from django_redis import get_redis_connection
from goods.models import GoodsSKU
from django.contrib.auth import authenticate,login,logout

# Create your views here.



# def register(request):
#     if request.method == 'GET':
#         #返回注册页面
#         return render(request,'user/register.html')
#     else:
#         username = request.POST.get('user_name')
#         password = request.POST.get('pwd')
#         email = request.POST.get('email')
#         allow = request.POST.get('allow')
#         print(username,password,email)
#
#         if not all([username,password,email]):
#             #判断提交的数据是否完整
#             return render(request, 'user/register.html', {'merror': '请把数据填写完整'})
#         if not re.findall(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
#             # 判断提交的邮箱地址是否规范
#             return render(request, 'user/register.html', {'merror': '请把填写正确的邮箱地址'})
#         if allow!='on':
#             # 判断提交的数据有没有勾选用户协议
#             return render(request, 'user/register.html', {'merror': '请勾选用户协议'})
#         try:
#             #判断用户名是否以及被注册
#             User.objects.get(username=username)
#         except:
#             # 进行用户的注册
#             user = User.objects.create_user(username,email,password)
#             user.is_active=0  #表示账户未激活
#             user.save()
#
#             # 发送邮件给用户进行激活验证。
#             send_register_active_email.delay(email,user.username)
#
#             return HttpResponse('注册成功')
#         else:
#             return render(request, 'user/register.html', {'merror': '该用户名已被注册'})
#


#
# def active(request,token):
#     '''处理用户的激活请求'''
#     ser = Serializer(settings.SECRET_KEY, 3600)
#     #获取用户名
#     username = ser.loads(token)['confirm']
#
#     try:
#         user = User.objects.get(username=username)
#     except:
#         print('该用户已被系统注销')
#     else:
#         #激活用户
#         user.is_active=1
#         user.save()
#     return HttpResponse('已激活')


class Register(View):
    # 类视图
    def get(self, request):
        # 返回注册页面
        return render(request, 'user/register.html')

    def post(self, request):
        # 处理提交的注册信息
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        print(username, password, email)

        if not all([username, password, email]):
            # 判断提交的数据是否完整
            return render(request, 'user/register.html', {'merror': '请把数据填写完整'})
        if not re.findall(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            # 判断提交的邮箱地址是否规范
            return render(request, 'user/register.html', {'merror': '请把填写正确的邮箱地址'})
        if allow != 'on':
            # 判断提交的数据有没有勾选用户协议
            return render(request, 'user/register.html', {'merror': '请勾选用户协议'})
        try:
            # 判断用户名是否以及被注册
            User.objects.get(username=username)
        except:
            # 进行用户的注册
            user = User.objects.create_user(username, email, password)
            user.is_active = 0  # 表示账户未激活
            user.save()

            # 发送邮件给用户进行激活验证。
            send_register_active_email.delay(email, user.username)

            return HttpResponse('注册成功')
        else:
            return render(request, 'user/register.html', {'merror': '该用户名已被注册'})


class Activa(View):
    def get(self,request,token):
        '''处理用户的激活请求'''
        ser = Serializer(settings.SECRET_KEY, 3600)
        # 获取用户名
        username = ser.loads(token)['confirm']

        try:
            user = User.objects.get(username=username)
        except:
            print('该用户已被系统注销')
        else:
            # 激活用户
            user.is_active = 1
            user.save()
        return HttpResponse('已激活')

class Login(View):
    '''用户登陆'''

    def get(self,request):
        print(request.user.is_authenticated())
        if request.user.is_authenticated():
            return redirect('/index')

        cookie = request.COOKIES.get('username')
        if cookie==None:
            username =''
        else:
            username=cookie
        # 返回登陆页面
        return render(request,'user/login.html',{'username':username})

    def post(self,request):
        #进行登陆验证
        #获取登陆请求的用户信息
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        btn = request.POST.get('btn')
        if not all([username,password]):
        #判读请求数据是否完整
            return render(request, 'user/login.html', {'msg': '请把账号和密码填写完整'})

        #进行校验账号密码
        user= authenticate(username=username,password=password)
        if user==None:
            return render(request,'user/login.html',{'msg':'您输入的账户或密码信息有误'})

        # 获取登陆后跳转的地址
        login(request, user)  # 通过session记住用户登陆状态
        next_url = request.GET.get('next', '/index')
        print(next_url)
        if btn=='on':
        #判读是否有记住账号
            response = redirect(next_url)
            response.set_cookie('username',username)  # 通过cookie记住用户名

        else:
            response  = redirect(next_url)
            response.delete_cookie('username')

        return response



class UserInfo(LoginMixin,View):
    '''用户信息页面'''
    def get(self,request):
        user = request.user


        con = get_redis_connection('default')
        histor_key = 'histor{}'.format(user.id)
        # 获取用户最新浏览的5个商品的id
        sku_ids = con.lrange(histor_key, 0, 4)  # [2,3,1]
        # 遍历获取用户浏览的商品信息
        goods_li = []
        for id in sku_ids:
            goods = GoodsSKU.objects.get(id=id)
            goods_li.append(goods)



        try:
            #查询默认收货地址，获取电话和地址进行显示
            address = Address.objects.filter(Q(user=user) & Q(is_default=True))[0]
        except:
            context = {
                'page':'A',
                'phone':'',
                'addr':'',
                'goods_li':goods_li
            }
        else:
            context={
                'page': 'A',
                'phone': address.phone,
                'addr': address.addr,
                'goods_li': goods_li

            }
        return render(request,'user/user_center_info.html',context)



class UserOrder(LoginMixin,View):

    def get(self,request):
        #获取用户
        user=request.user
        #根据用户查找用户所有的订单
        orders= OrderInfo.objects.filter(user=user).order_by('-order_id')

        #遍历订单
        for order in orders:
            #根据订单查找订单中的商品
            order_skus= OrderGoods.objects.filter(order=order)

            sum_peice =0
            for order_sku in order_skus:
                #获取商品的价格
                price = order_sku.price
                #获取商品的数量
                count = order_sku.count
                #计算小计价格
                order_sku.amount = price*count
            #获取订单状态的名字
            order.status_name = OrderInfo.ORDER_STATUS_CHOICES[order.order_status-1]
            # print(order.status_name)

            #把商品列表加到订单的order_suks属性上
            order.order_skus=order_skus

        context = {
            'orders':orders,
            'page':'B'

        }

        return render(request,'user/user_center_order.html',context)

                









    # '''用户订单面'''
    # def get1(self, request):
    #     '''用户中心-订单页'''
    #     # 获取用户的订单信息
    #     user = request.user
    #     orders = OrderInfo.objects.filter(user=user).order_by('-create_time')
    #
    #     # 遍历获取订单商品的信息
    #     for order in orders:
    #     # 根据order_id查询订单商品信息
    #         order_skus = OrderGoods.objects.filter(order_id=order.order_id)
    #
    #         # 遍历order_skus计算商品的小计
    #         for order_sku in order_skus:
    #             # 计算小计
    #             amount = order_sku.count * order_sku.price
    #             # 动态给order_sku增加属性amount,保存订单商品的小计
    #             order_sku.amount = amount
    #
    #         # 动态给order增加属性，保存订单状态标题
    #         order.status_name = OrderInfo.ORDER_STATUS_CHOICES[order.order_status-1]
    #         # 动态给order增加属性，保存订单商品的信息
    #         order.order_skus = order_skus
    #
    #
    #     # 组织上下文
    #     context = {'orders': orders,
    #                'page':'B'
    #                }
    #     # 使用模板
        # return render(request, 'user/user_center_order.html',context)


class UserSite(LoginMixin,View):
    '''用户收货地址页面'''
    def get(self, request):
        user = request.user

        try:
            address= Address.objects.filter(Q(user=user)&Q(is_default=True))[0]
        except:
            context = {
                'page': 'C',
                'addr':'还没有收货地址，请再下面添加',
                }
        else:
            context = {
                'page': 'C',
                'addr':address.addr,
                'name':address.receiver,
                'phone':address.phone,
                }

        return render(request, 'user/user_center_site.html',context)

    def post(self,request):
        #获取提交过来的数据
        name = request.POST.get('name')
        addr = request.POST.get('addr')
        code = request.POST.get('code')
        phone = request.POST.get('phone')
        #获取user对象
        user= request.user

        addr= Address.objects.create(user=user,receiver=name,addr=addr,zip_code=code,phone=phone)
        if Address.objects.filter(Q(user=user)&Q(is_default=True)):
            pass
        else:
            addr.is_default=True
            addr.save()


        address= Address.objects.filter(Q(user=user)&Q(is_default=True))[0]
        context = {
            'page': 'C',
            'addr':address.addr,
            'name':address.receiver,
            'phone':address.phone,
            }
        return render(request, 'user/user_center_site.html',context)



class Logout(View):
    # 退出登陆
    def get(self,request):
        logout(request)
        return redirect('/index')















