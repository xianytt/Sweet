# Sweet


本项目是基于Django开发的B2C生鲜类电商网站，可分为用户模块，商品模块，购物车模块和订单模块。
后台数据使用mysql数据库以及redis数据库来存放session账号缓存。其中用户模块使用celery和redis实现分布式队列处理耗时任务。
商品模块采用FastDFS分布式系统存放大量商品图片以及使用nginx来提高网站访问图片和静态页面的效率。

1、注册模块使用PIL随机生成随机码，使用Django.ceil.mail模块再加上celery技术实现耗时进行邮箱验证，通过authenticate验证账号是否正确，采用md5对用户密码进行加密处理。
2、通过redis数据库实现商品首页缓存，以减少服务器的压力
3、使用login_requried装饰器来进行登录验证，实现购物车验证用户登录，实现商品增删改以及结算。
4、采用haystack+whoosh+jieba全文检索搜索商品关键字。
5、较多商品展示时，使用Paginator分页实现商品。
6、使用Django自带admin后台管理模板，自定义后台管理页面功能，发布商品信息。
