from django.shortcuts import render
from django.views.generic import View
from django_redis import get_redis_connection
from apps.mixin import LoginMixin
from goods.models import GoodsSKU
from django.http import JsonResponse


# Create your views here.

class Cart(LoginMixin,View):

    def get(self,request):

        user = request.user
        #链接到redis中 获取缓存中购物车里的数据
        conn = get_redis_connection('default')

        #构造用户对应的键名
        cart_ket = 'cart_{}'.format(user.id)

        #读取缓存中购物车的数据
        cart_dict= conn.hgetall(cart_ket)


        #分别获取商品id和数量
        cont =[]  #定义个列表用来存储商品
        sum_price=0 #存储购物车总价
        for sku_id,num in cart_dict.items():
            #查询对应的商品
            goods= GoodsSKU.objects.get(id=sku_id)
            print(goods)
            #将数量添加goods的属性中
            goods.cart_num = num
            #计算小计
            goods.amount = goods.price * int(num)
            #计算总价
            sum_price += goods.price * int(num)
            cont.append(goods)

        # 商品名  图片  价格  单位

        context = {
            'goods_list':cont,
            'num':len(cont),
            'sum_price':sum_price
        }
        #  hash    cart_userid   商品名为属性    数量为属性对应值

        return render(request,'cart/cart.html',context)


#往购物车加入商品
class AddCart(View):
    # {status:0,msg:'--处理信息--'}
    def post(self,request):
        #获取发送请求的用户
        user =request.user

        #判断用户是否登陆
        if not user.is_authenticated():
            return JsonResponse({'status':0,'msg':'请先登陆'})

        #data{'sku_id','num'}
        sku_id= request.POST.get('sku_id')
        num = request.POST.get('num')
        #验证数据的完整性
        if not all([sku_id,num]):
            return JsonResponse({'status':0,'msg':'请求数据不完整'})

        #验证数量是否合法
        try:
            num =int(num)
        except:
            return JsonResponse({'status':0,'msg':'请求的数据类型有误'})

        #验证商品是否存在
        try:
            GoodsSKU.objects.get(id=sku_id)
        except:
            return JsonResponse({'status':0,'msg':'该商品不存在'})

        #连接到redis，获取缓存中的数据

        conn = get_redis_connection('default')

        #构造用户对应的键名
        cart_ket = 'cart_{}'.format(user.id)
        # 判断购物车里是否有该商品
        count= conn.hget(cart_ket,sku_id)
        print(count)
        if count:
            #获取该商品在购物车原有的数量
            num = int(count)+num
            #重新设置改商品在购物车中的数量
            conn.hset(cart_ket,sku_id,num)
        else:
            #购物车原来没有该商品，直接添加
            conn.hset(cart_ket, sku_id, num)


        goods_list= conn.hgetall(cart_ket)

        #返回购物车商品总数
        count = len(goods_list.keys())

        return JsonResponse({'status':1,'cart_num':count,'msg':'添加成功'})





class Update(View):
    '''修改购物车中的数据'''
    def post(self,request):

        user = request.user

        if not user.is_authenticated:
            return JsonResponse({'status':0,'msg':'请先登陆'})

        sku_id = request.POST.get('sku_id')
        num = request.POST.get('num')

        # 验证数据的完整性
        if not all([sku_id, num]):
            return JsonResponse({'status': 0, 'msg': '请求数据不完整'})

        # 验证数量是否合法
        try:
            num = int(num)
        except:
            return JsonResponse({'status': 0, 'msg': '请求的数据类型有误'})

        # 验证商品是否存在
        try:
            GoodsSKU.objects.get(id=sku_id)
        except:
            return JsonResponse({'status': 0, 'msg': '该商品不存在'})

        #连接到redis，获取缓存中的数据

        conn = get_redis_connection('default')

        #构造用户对应的键名
        cart_ket = 'cart_{}'.format(user.id)
        # 判断购物车里是否有该商品
        count= conn.hget(cart_ket,sku_id)

        if num >0:
            #重新设定购物车中的数据
            conn.hset(cart_ket,sku_id,num)

            return JsonResponse({'status': 1, 'msg': '数据更改成功'})
        else:
            return JsonResponse({'status': 0, 'msg': '请求的数据有误'})


class Delete(View):
    '''删除购物车中 的数据'''
    def post(self,request):
        user = request.user
        #判断是否登陆
        if not user.is_authenticated:
            return JsonResponse({'status':0,'msg':'请先登陆'})

        sku_id = request.POST.get('sku_id')

        # 验证商品是否存在
        try:
            GoodsSKU.objects.get(id=sku_id)
        except:
            return JsonResponse({'status': 0, 'msg': '该商品不存在'})

        #连接到redis，获取缓存中的数据
        conn = get_redis_connection('default')

        #构造用户对应的键名
        cart_ket = 'cart_{}'.format(user.id)

        # 判断购物车里是否有该商品
        count= conn.hget(cart_ket,sku_id)
        if count:
            #删除购物车的该商品
            conn.hdel(cart_ket,sku_id)
            return JsonResponse({'status': 1, 'msg': '删除成功'})
        else:
            return JsonResponse({'status': 0, 'msg': '购物车中没有该数据'})












