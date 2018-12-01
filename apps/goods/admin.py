from django.contrib import admin

# Register your models here.
from .models import *
from apps.tasks import generate_static_index_html
from django.core.cache import cache

class BaseAdminModel1(admin.ModelAdmin):
    '''定义通用的管理模型类'''
    def save_model(self, request, obj, form, change):
        #再数据发生改变的时候自动调用
        super().save_model(request, obj, form, change)
        #发起celery任务，重新生成首页静态页面
        generate_static_index_html.delay()
        # 清除首页的缓存数据
        cache.delete('index_con')


    def delete_model(self, request, obj):
        # 再数据发生删除操作的时候自动调用
        super().delete_model(request, obj)
        #发起celery任务，重新生成首页静态页面
        generate_static_index_html.delay()
        # 清除首页的缓存数据
        cache.delete('index_con')




admin.site.register(GoodsType,BaseAdminModel1)
admin.site.register(IndexGoodsBanner,BaseAdminModel1)
admin.site.register(GoodsSKU,BaseAdminModel1)
admin.site.register(IndexPromotionBanner,BaseAdminModel1)
admin.site.register(IndexTypeGoodsBanner,BaseAdminModel1)
admin.site.register(Goods,BaseAdminModel1)




