#! /usr/bin/env python
# -*- coding: utf-8 -*-

# *************************************************************
#       Filename @  user_login.py
#         Author @  Fengchi
#    Create date @  2017-08-14 10:15:44
#  Last Modified @  2017-08-15 09:59:33
#    Description @  
# *************************************************************


import requests
import base64
import re
import urllib
import urllib.parse
import rsa
import json
import binascii
import pdb
import time
from bs4 import BeautifulSoup

class UserLogin(object):
    def __init__(self, username, password, parse_self = False):
        self.username = username
        self.password = password
        self.parse_self = parse_self
        self.user_login()

    def user_login(self):
        session = requests.Session()
        url_prelogin = 'https://login.sina.com.cn/sso/prelogin.php?entry=weibo&callback=sinaSSOController.preloginCallBack&su=&rsakt=mod&client=ssologin.js(v1.4.19)&_=1502694346166'
        url_login    = 'http://login.sina.com.cn/sso/login.php?client=ssologin.js(1.4.19)'

        resp = session.get(url_prelogin)
        json_data = re.findall(r'(?<=\().*(?=\))', resp.text)[0]
        data      = json.loads(json_data)

        servertime = data['servertime']
        nonce      = data['nonce']
        pubkey     = data['pubkey']
        rsakv      = data['rsakv']

        print(urllib.parse.quote(self.username))
        su = base64.b64encode(self.username.encode(encoding='utf8'))

        rsaPublickey = int(pubkey, 16)
        key = rsa.PublicKey(rsaPublickey, 65537)
        message = str(servertime) + '\t' + str(nonce) + '\n' + str(self.password)
        sp = binascii.b2a_hex(rsa.encrypt(message.encode(encoding='utf8'), key))

        postdata = {
            'entry': 'weibo',
            'gateway': '1',
            'from': '',
            'savestate': '7',
            'userticket': '1',
            'ssosimplelogin': '1',
            'vsnf': '1',
            'vsnval': '',
            'su': su,
            'service': 'miniblog',
            'servertime': servertime,
            'nonce': nonce,
            'pwencode': 'rsa2',
            'sp': sp,
            'encoding': 'UTF-8',
            'url': 'http://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.sinaSSOController.feedBackUrlCallBack',
            'returntype': 'META',
            'rsakv': rsakv,
        }

        resp = session.post(url_login, data = postdata)
        # print(resp.headers)
        # print()
        # print(resp.content)
        login_url = re.findall(r'http://weibo.*&retcode=0', resp.text)
        # print(login_url)

        respo = session.get(login_url[0])
        # print(respo.text)
        self.uid = re.findall('"uniqueid":"(\d+)",', respo.text)[0]
        # # url = "http://weibo.com/u/" + uid
        # url = "http://weibo.com/zhengfu?is_all=1"
        # respo = session.get(url)

        # #print(respo.text)
        # bs_res = BeautifulSoup(respo.text)
        # print(bs_res)

        self.session = session

    def _parse_weibo_content_from_html(self, html):
        # url = "http://weibo.com/p/aj/v6/mblog/mbloglist?ajwvr=6&domain=100106&is_search=0&visible=0&is_all=1&is_tag=0&profile_ftype=1&page=3&pagebar=0&pl_name=Pl_Official_MyProfileFeed__24&id=1001065000609535&script_uri=/zhengfu&feed_type=0&pre_page=3&domain_op=100106&__rnd=1502698639017"
        # url = "http://weibo.com/p/aj/v6/mblog/mbloglist?ajwvr=6&domain=100505&rightmod=1&wvr=6&mod=personnumber&is_all=1&pagebar=0&pl_name=Pl_Official_MyProfileFeed__21&id=1005055788421658&script_uri=/5788421658/profile&feed_type=0&page=1&pre_page=1&domain_op=100505&__rnd=1502700584262"
        # resp = self.session.get(url)

        # wb_html = resp.json()['data']
        wb_bs   = BeautifulSoup(html)

        wb_details = wb_bs.select('div[action-type="feed_list_item"]')
        print("this page has %d weibos" % len(wb_details))
        for detail in wb_details:
            wb_time    = detail.select("a[date]")[0]['title']
            wb_content = detail.select("div.WB_text")[0].text.replace('\u200b','').strip()
            wb_likes = detail.select('span[node-type="like_status"]')[0].text[1:]
            if wb_likes == "赞":
                wb_likes = '0'
            wb_forward = detail.select('span[node-type="forward_btn_text"]')[0].text[1:]
            if wb_forward == "转发":
                wb_forward = '0'

            res = [wb_time, wb_content, wb_forward, wb_likes]
            if self.parse_self:
                # pdb.set_trace()
                wb_read = detail.select("i[title^='此条微博']")[0]['title']
                
                wb_read = re.findall("\d+", wb_read)[0]
                res.append(wb_read)
            self.fw.write(','.join(res) + '\n')
            # pdb.set_trace()

    def get_url_main_page(self, pagenum):
        pagenum = str(pagenum)
        if self.parse_self:
            url_main_page = "http://weibo.com/p/1001065000609535/home?is_search=0&visible=0&is_all=1&is_tag=0&profile_ftype=1&page=%s" % pagenum
        else:
            url_main_page = "http://weibo.com/zhengfu?is_search=0&visible=0&is_all=1&is_tag=0&profile_ftype=1&page=%s" % pagenum

        print(url_main_page)
        resp = self.session.get(url_main_page)
        main_page_soup = BeautifulSoup(resp.text)

        try:
            html = main_page_soup.select('script')[35].text[8:-1]
            html = json.loads(html)['html']
        except:
            html = main_page_soup.select('script')[31].text[8:-1]
            html = json.loads(html)['html']

        return html


    def get_xhr_html(self, pagenum, pagebar):
        if self.parse_self:
            url = "http://weibo.com/p/aj/v6/mblog/mbloglist?ajwvr=6&domain=100106&from=page_100106&mod=TAB&is_all=1&pagebar=%s&pl_name=Pl_Official_MyProfileFeed__24&id=1001065000609535&script_uri=/p/1001065000609535/home&feed_type=0&page=%s&pre_page=%s&domain_op=100106&__rnd=1502761646185" % (pagebar, pagenum, pagenum)
        else:
            url = "http://weibo.com/p/aj/v6/mblog/mbloglist?ajwvr=6&domain=100106&is_search=0&visible=0&is_all=1&is_tag=0&profile_ftype=1&page=%s&pagebar=%s&pl_name=Pl_Official_MyProfileFeed__24&id=1001065000609535&script_uri=/zhengfu&feed_type=0&pre_page=%s&domain_op=100106&__rnd=1502698639017" % (pagenum, pagebar, pagenum)

        print(url)
        resp = self.session.get(url)

        wb_html = resp.json()['data']

        return wb_html


    def main_parse(self, from_date = None, to_date=None):
        self.fw = open("res.csv", 'w')
        headers = ['time', 'content', 'forward_num', 'like_num']
        if self.parse_self:
            headers.append('read_num')
        self.fw.write(",".join(headers) + '\n')
        for pagenum in range(1,4):
            main_page_data = self.get_url_main_page(pagenum)
            self._parse_weibo_content_from_html(main_page_data)
            time.sleep(1)
            print("main page %s finished!" % pagenum)
            for pagebar in range(2):
                xhr_data = self.get_xhr_html(pagenum, pagebar)
                self._parse_weibo_content_from_html(xhr_data)
                time.sleep(1)
                print("main page %s xhr pagebar %s finished!" % (pagenum, pagebar))

            print("=" * 30)

        self.fw.close()



if __name__ == '__main__':
    user_login = UserLogin("", "", parse_self = True)
    # main_page_data = user_login.get_url_main_page(3)
    # user_login._parse_weibo_content_from_html(main_page_data)
    # user_login.get_url_main_page(pagenum=2)
    user_login.main_parse()
