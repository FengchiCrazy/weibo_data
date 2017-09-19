#! /usr/bin/env python
# -*- coding: utf-8 -*-

# *************************************************************
#       Filename @  user_login.py
#         Author @  Fengchi
#    Create date @  2017-08-14 10:15:44
#  Last Modified @  2017-09-04 11:57:19
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
import time
import numpy as np
import pandas as pd
import pdb

from bs4 import BeautifulSoup




class UserLogin(object):
    def __init__(self, username = None, password = None, parse_self = False):
        if username is None or password is None:
            self.parse_username_and_password()
        else:
            self.username = username
            self.password = password

        self.parse_self = parse_self
        self.data = []

        self.headers = ['日期', '时间', '标题', '内容', '转发', '点赞']
        if self.parse_self:
            self.headers.append('阅读/万')

        self.user_login()

    def parse_username_and_password(self, data_file = "zhanghao.csv"):
        with open(data_file) as data:
            self.username, self.password = data.readline().strip().split(' ')
            self.mailusr, self.mailpw = data.readline().strip().split(' ')

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
        wb_bs   = BeautifulSoup(html)

        wb_details = wb_bs.select('div[action-type="feed_list_item"]')
        print("this page has %d weibos" % len(wb_details))
        for detail in wb_details:
            wb_t       = detail.select("a[date]")[0]['title'].split(' ')
            wb_date    = wb_t[0]
            wb_time    = wb_t[1]
            wb_content = detail.select("div.WB_text")[0].text.replace('\u200b', '').strip()
            wb_title   = re.findall(r"(?<=[【]).*(?=[】])", wb_content)
            if wb_title:
                wb_title = wb_title[0]
            else:
                wb_title = ''

            wb_likes = detail.select('span[node-type="like_status"]')[0].text[1:]
            if wb_likes == "赞":
                wb_likes = '0'
            wb_forward = detail.select('span[node-type="forward_btn_text"]')[0].text[1:]
            if wb_forward == "转发":
                wb_forward = '0'

            res = [wb_date, wb_time, wb_title, wb_content, wb_forward, wb_likes]
            if self.parse_self:
                # pdb.set_trace()
                wb_read = detail.select("i[title^='此条微博']")[0]['title']

                wb_read = re.findall("\d+", wb_read)[0]
                wb_read = str(round(int(wb_read) / 10000, 1))
                res.append(wb_read)

            self.data.append(res)

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
        except Exception:
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

    def main(self, type = "xlsx", from_date = None, to_date = None):
        pagenum = 1
        # self.flag indicate whether we should go on parsing
        # while self.flag:
        while pagenum < 2:
            main_page_data = self.get_url_main_page(pagenum)
            self._parse_weibo_content_from_html(main_page_data)
            print("main page %s finished!" % pagenum)
            time.sleep(1)
            for pagebar in range(2):
                xhr_data = self.get_xhr_html(pagenum, pagebar)
                self._parse_weibo_content_from_html(xhr_data)
                print("main page %s xhr pagebar %s finished!" % (pagenum, pagebar))
                time.sleep(1)

            print("=" * 30)
            pagenum += 1

        df_res = pd.DataFrame(self.data, columns = self.headers)
        # pdb.set_trace()
        # df_res = self.parse_date(df_res, from_date, to_date)
        if type == "csv":
            self.out_csv(df_res)
        elif type == "xls" or type == "xlsx":
            self.out_xlsx(df_res)
        else:
            raise ValueError("Wrong Type in main")

        # TODO: send email
        # self.send_email()

    def parse_df_and_clean(self, df_res, from_date, to_date):
        """
        made dataframe good looking. include:
        - make date range write
        - adjust the width of the column
        - adjust the type of numbers from sting to int

        :param df_res:
        :param from_date:
        :param to_date:
        :return:
        """
        pass

    def out_csv(self, df_res, from_date = None, to_date = None):
        df_res.to_csv("res.csv", index = False)

    def out_xlsx(self, df_res):
        from openpyxl.utils.dataframe import dataframe_to_rows
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active

        for r in dataframe_to_rows(df_res, index = False, header = True):
            ws.append(r)

        wb.save("res.xlsx")

    def send_email(self, attach = "res.xlsx", to_addr = ""):
        from email import encoders
        from email.header import Header
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.base import MIMEBase
        from email.utils import parseaddr, formataddr

        import smtplib

        def _format_addr(s):
            name, addr = parseaddr(s)
            return formataddr((Header(name, 'utf-8').encode(), addr))

        from_addr = ""
        password  = ""
        smtp_server = "smtp.163.com"

        msg = MIMEMultipart()
        msg['From'] = _format_addr('Python爱好者 <%s>' % from_addr)
        msg['To'] = _format_addr('管理员 <%s>' % to_addr)
        msg['Subject'] = Header('', 'utf-8').encode()
        msg.attach(MIMEText('hello, send by Python...', 'plain', 'utf-8'))

        part = MIMEBase('application', "octet-stream")
        part.set_payload(open(attach, "rb").read())
        encoders.encode_base64(part)
        print('attachment; filename="%s"' % attach)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % attach)
        msg.attach(part)

        server = smtplib.SMTP(smtp_server, '25')  # SMTP协议默认端口是25
        server.set_debuglevel(1)
        server.login(from_addr, password)
        server.sendmail(from_addr, [to_addr], msg.as_string())
        server.quit()




if __name__ == '__main__':
    # user_login = UserLogin(None, None, parse_self = True)
    # main_page_data = user_login.get_url_main_page(3)
    # user_login._parse_weibo_content_from_html(main_page_data)
    # user_login.get_url_main_page(pagenum=2)
    # user_login.main(type = "xlsx")
    send_email()
