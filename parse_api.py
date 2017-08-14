#! /usr/bin/env python
# -*- coding: utf-8 -*-

# *************************************************************
#       Filename @  parse_api.py
#         Author @  Fengchi
#    Create date @  2017-08-13 21:16:24
#  Last Modified @  2017-08-14 10:09:40
#    Description @  
# *************************************************************


import json
import datetime
import sys

DATE_FORMAT = "%Y-%m-%d"

APP_KEY = ''
APP_SECRET = ''
CALLBACK_URL = 'https://api.weibo.com/oauth2/default.html'


from weibo import APIClient
import webbrowser 
import pdb

client = APIClient(app_key=APP_KEY, app_secret=APP_SECRET, redirect_uri=CALLBACK_URL)
url = client.get_authorize_url()
# TODO: redirect to url
print url
webbrowser.open_new(url) 

#获取code=后面的内容
print '输入url中code后面的内容后按回车键：'
code = raw_input()
#code = your.web.framework.request.get('code')
#client = APIClient(app_key=APP_KEY, app_secret=APP_SECRET, redirect_uri=CALLBACK_URL)
r = client.request_access_token(code)
access_token = r.access_token # 新浪返回的token，类似abc123xyz456
expires_in = r.expires_in

# 设置得到的access_token
client.set_access_token(access_token, expires_in)

#可以打印下看看里面都有什么东西
statuses = client.statuses__home_timeline(count = 100)['statuses'] #获取当前登录用户以及所关注用户（已授权）的微博</span>
pdb.set_trace()

length = len(statuses)
print length
#输出了部分信息
for i in range(0,length):
    print u'昵称：'+statuses[i]['user']['screen_name']
    print u'简介：'+statuses[i]['user']['description']
    print u'位置：'+statuses[i]['user']['location']
    print u'微博：'+statuses[i]['text']


