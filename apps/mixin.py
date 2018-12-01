#!/usr/bin/env/python
# -*-coding:utf-8 -*-

from django.contrib.auth.decorators import login_required

class LoginMixin(object):
    @classmethod
    def as_view(cls,**initkwargs):
        view = super().as_view(**initkwargs)
        return login_required(view)


