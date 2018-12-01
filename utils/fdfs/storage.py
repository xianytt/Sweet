#!/usr/bin/env/python
# -*-coding:utf-8 -*-

from django.core.files.storage import Storage
from django.conf import settings
from fdfs_client.client import Fdfs_client


class FdfsStorage(Storage):
    '''自定义文件存储的类'''

    def __init__(self,client_conf=None,base_url=None):
        #判断有没有传入conf文件的路径
        if client_conf ==None:
            client_conf = settings.FDFS_CLIENT_CONF
        self.client_conf=client_conf
        #判断有没有传入Nginx服务器的地址
        if base_url==None:
            base_url=settings.FDFS_URL
        self.base_url=base_url



    def _open(self,name,mode='rb'):
        pass



    def _save(self,name,content):
        '''实现文件存储的方法'''

        #创建一个fastDFS链接对象
        client = Fdfs_client(self.client_conf)
        '''
        前一天错误代码
        res = client.upload_by_filename(content.read())
        if res.Status !='Upload successed.':
        修改如下
        '''
        #把文件上传到fastDFS服务器
        res = client.upload_by_buffer(content.read())
        #判断文件是否上传成功
        if res.get('Status') !='Upload successed.':
            #上传失败，抛出异常
            raise Exception('文件上传到fastDFS失败')
        #获取返回的文件ID
        filename = res.get('Remote file_id')

        return filename


    def exists(self, name):
        '''Django判断文件名是否可用'''
        return False


    def url(self, name):
        '''返回访问文件的url路径'''
        #nginx服务器的地址：127.0.0.1:8888
        return self.base_url+name






