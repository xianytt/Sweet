from django.shortcuts import render
from django.views.generic import View
from apps.mixin import LoginMixin
from user.models import Address
from goods.models import GoodsSKU
from django_redis import get_redis_connection
from django.http import JsonResponse
from .models import *
import datetime
from alipay import AliPay
from django.db import transaction
import os
from django.conf import settings
import time
# Create your views here.

#接收购物车发送过来的数据，返回订单提交页面
class Order(LoginMixin,View):

    def post(self,request):

        #获取用户对象
        user = request.user
        #通过用户对象，查询出所有的地址信息
        addrs=Address.objects.filter(user=user)

        #获取购物车页面提交过来的商品id，根据id去购物车里查询商品的数据。
        sku_ids = request.POST.getlist('sku_id')
        #连接到redis
        con = get_redis_connection('default')
        #构造redis中用户对应的键
        cart_key = 'cart_{}'.format(user.id)
        #定义一个列表，用来储存遍历的商品
        goods_list = []
        #sum_price,储存总价格
        sum_price=0
        #sum_count,储存总的商品数量
        sum_count=0
        for sku_id in sku_ids:
            #获取购物车中该商品的数量
            count = con.hget(cart_key,sku_id)

            #查询数据库中对应的商品信息
            if count != None:
                print('-----------------------')
                try:
                    #通过模型类查询到商品对象
                    goods= GoodsSKU.objects.get(id=sku_id)
                    #把数量绑定在该商品的count属性上面
                    goods.count = count

                    #价格小计
                    amount =int(count)*goods.price
                    goods.amount = amount
                    #计算总价格
                    sum_price+=amount
                    #计算商品总件数
                    sum_count+=int(count.decode())
                    #将商品添加到goods_list这个列表中
                    goods_list.append(goods)
                    print(goods_list)
                except:
                    continue
        #运费
        fr =10

        #实付款
        amount_goods_price = sum_price+fr

        context = {
            'addrs':addrs,
            'goods_list':goods_list,
            'fr':fr,
            'sum_price':sum_price,
            'sum_count':sum_count,
            'amount_goods_price':amount_goods_price,
            'sku_ids':sku_ids

        }

        return render(request,'order/place_order.html',context)

#创建订单
class OrderCommit(View):

    @transaction.atomic
    def post(self,request):
        #获取请求用户对象
        user = request.user
        #判断是否登陆
        if not user.is_authenticated():
            return JsonResponse({'status':0,'msg':'用户没有登陆'})

        #获取请求数据
        addr_id = request.POST.get('addr_id')
        pay__method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')
        print(pay__method)
        #验证数据的有效性
        if not all([addr_id,pay__method,sku_ids]):
            return JsonResponse({'status': 0, 'msg': '请求的数据不完整'})


        #验证地址是否有效
        try:
            addr=Address.objects.get(id=addr_id)
        except:
            return JsonResponse({'status': 0, 'msg': '收货地址有误'})

        #验证付款方式：
        li = [item[0] for item in OrderInfo.PAY_METHOD_CHOICES]
        if int(pay__method) not in li:
            return JsonResponse({'status': 0, 'msg': '付款方式有误'})

        #设置运费
        transit_price = 10
        #设置订单编号
        order_id = datetime.datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)
        #设置支付编号
        trade_no = str(user.id)+datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        # 设置事务保存点
        save_id = transaction.savepoint()
        try:
            #创建订单，往订单表中添加一条数据。
            order_obj= OrderInfo.objects.create(
                order_id=order_id,
                user=user,
                addr=addr,
                pay_method=pay__method ,
                total_count =1 ,
                total_price=1,
                transit_price=transit_price,
                order_status=1,
                trade_no=trade_no
            )

            #建立购物车连接
            conn = get_redis_connection('default')

            #构造用户再购物车对应的键
            cart_key = 'cart_{}'.format(user.id)

            #sum_price,储存总价格
            sum_price=0

            #sum_count,储存总的商品数量
            sum_count=0

            for sku_id in sku_ids:
                #获取购物车中该商品的数量
                count = conn.hget(cart_key,sku_id)
                #查询数据库中对应的商品信息
                if count != None:
                    try:
                        #通过模型类查询到商品对象
                        goods= GoodsSKU.objects.get(id=sku_id)
                        #价格小计
                        amount =int(count)*goods.price
                        #计算总价格
                        sum_price+=amount
                        #计算商品总件数
                        sum_count+=int(count.decode())
                        print('--------------')
                        print(int(count))
                        print(goods.stock)

                        #判断商品库存够不够
                        if goods.stock>=int(count):
                            #往订单商品表中插入一条数据
                            print('11111111111')
                            order_goods= OrderGoods.objects.create(
                                order=order_obj,
                                sku = goods,
                                count = count,
                                price = goods.price,
                                comment = ' ',
                            )
                            #保存到数据库
                            order_goods.save()
                            #更改销量和库存的值
                            goods.stock -= int(count)
                            goods.sales += int(count)
                            goods.save()
                        else:
                            transaction.savepoint_rollback(save_id)
                            return JsonResponse({'status': 0, 'msg': '订单创建失败'})

                    except:
                        # 事务回滚
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse({'status': 0, 'msg': '订单创建失败11111'})

            #重新设置商品总价和数量
            order_obj.total_count = sum_count
            order_obj.total_price = sum_price

            #保存到数据库
            order_obj.save()
            # 提交事务
            transaction.savepoint_commit(save_id)
            conn.hdel(cart_key,*sku_ids)
            return JsonResponse({'status': 1, 'msg': '订单创建成功'})
        except:
            # 事务回滚
            transaction.savepoint_rollback(save_id)
            return JsonResponse({'status': 0, 'msg': '订单创建失败'})

#  /order/pay
#订单支付
class OederPay(View):
    '''支付宝支付'''
    def post(self,request):
        # 支付宝支付
        order_id = request.POST.get('order_id')
        # 对接支付宝初始化配置
        alipay = AliPay(

            appid='2016092000557568',
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(settings.BASE_DIR,'apps/order/app_private_key.pem'),
            alipay_public_key_path = os.path.join(settings.BASE_DIR,'apps/order/alipay_public_key.pem'),
            sign_type="RSA2",  # RSA 或者 RSA2
            debug = True  # 默认False
        )

        # 如果你是 Python 3的用户，使用默认的字符串即可
        subject = "生鲜测试订单:{}".format(order_id)
        # 电脑网站支付，需要跳转到https://openapi.alipay.com/gateway.do? + order_string
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,      #订单号
            total_amount='0.01',        #订单金额
            subject=subject,          #订单名称

        )
        url = 'https://openapi.alipaydev.com/gateway.do?' + order_string
        return JsonResponse({'res':1,'url':url})


#查询支付结果
class CheckPay(View):
    def post(self,requst):
        # 对接支付宝初始化配置
        alipay = AliPay(
            appid='2016092000557568',
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(settings.BASE_DIR,'apps/order/app_private_key.pem'),
            alipay_public_key_path = os.path.join(settings.BASE_DIR,'apps/order/alipay_public_key.pem'),
            sign_type="RSA2",  # RSA 或者 RSA2
            debug = True  # 默认False
        )

        '''
        #支付宝查询接口返回的数据
        {
        'buyer_user_id': '2088102176818981',    #订单号
        'buyer_pay_amount': '0.00',             #买家实付金额，
        'buyer_logon_id': 'lli***@sandbox.com', #买家支付宝账号
        'out_trade_no': '2018103022282318',   	#商户订单号
        'buyer_user_type': 'PRIVATE',           #买家用户类型
        'send_pay_date': '2018-10-31 14:45:47', #本次交易打款给卖家的时间
        'msg': 'Success',                       #支付状态描述信息
        'point_amount': '0.00',                 #积分支付的金额
        'code': '10000',                        #网关返回码
        'trade_no': '2018103122001418980500363830',  #支付宝的交易号
        'invoice_amount': '0.00',               #交易中用户支付的可开具发票的金额
        'total_amount': '0.01',                 #订单金额
        'receipt_amount': '0.00',               #实收金额
        'trade_status': 'TRADE_SUCCESS'         #交易状态
             }
        '''
        # 获取订单号
        order_id = requst.POST.get('order_id')
        for i in range(30):
            time.sleep(5)
            # result = alipay.api_alipay_trade_query(order_id)
            result = alipay.api_alipay_trade_query(out_trade_no=order_id)
            print(result)
            # 判断订单的状态，
            if result.get('code',0) == '10000' and result.get('trade_status') == 'TRADE_SUCCESS':
                #支付成功更改订单状态
                order = OrderInfo.objects.get(order_id=order_id)
                order.order_status=2
                order.save()
                return JsonResponse({'res':'1','msg':'支付成功'})
            #订单未创建或者，未支付
            elif result.get('code',0) == '20000' or result.get('code',0) == '40004'or (result.get('code',0) == '10000' and result.get('trade_status') == 'WAIT_BUYER_PAY'):
                continue
            else:
                #其他情况下撤销订单，并返回订单支付失败
                alipay.api_alipay_trade_cancel(out_trade_no=order_id)
                return JsonResponse({'res': '0', 'msg': '未支付1'})
        # 其他情况下撤销订单，并返回订单支付失败
        alipay.api_alipay_trade_cancel(out_trade_no=order_id)
        return JsonResponse({'res': '0', 'msg': '未支付2'}


                            )



























































