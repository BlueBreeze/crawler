#!/usr/bin/env python
# coding=utf-8
# 数据来源：凤凰--健康提示 http://fashion.ifeng.com/listpage/5574/1/list.shtml

import sys
reload(sys)
sys.setdefaultencoding('utf-8')


import time
import urllib
import urllib2
from BeautifulSoup import BeautifulSoup
from conf import *
from mydb import *
from public import *
import random
import re

    
my_db = MyDb()

def findComments(detail_url, NewId):
    prex = 'http://comment.ifeng.com/view.php?docUrl='
    detail_url = "%s%s" %(prex, detail_url)
    print detail_url

    page = urllib2.Request(url=detail_url)
    result = urllib2.urlopen(page)
    html = result.read()
    soup3 = BeautifulSoup(html,fromEncoding="gb18030")

    c2 = soup3.find('div',attrs={"id" : "comment2"})
    zuir = c2.find('div', attrs={"class" : "zuir"})
    if not zuir: return

    zuir = zuir.find('div', attrs={"class" : "conBox"}).findAll('div', attrs={"class" : "textCon clearfix"})

    length = len(zuir)
    length = 10 if length > 10 else length
    print 'length:', length


    #删除已有评论
    sql = "select count(1) from PNComment pnc where pnc.PNId=%s;" %NewId
    rs = my_db.myexce(sql,1)
    if rs[0] > 0:
        sql = 'delete from PNComment where PNId=%s;' %NewId
        print 'sql:==>' , sql
        my_db.myexce(sql, 0)
        

    #插入评论
    for i in range(0, length):
        print '----------------------------------'
        tmp = zuir[i]

        txtDet = tmp.find('div', attrs={"class" : "textDet"})
        u = txtDet.find("div", attrs={"class" : "user"})
        pt = u.find('span').text

        t = pt.replace('发表日期：', '')
        t = time.mktime(time.strptime(t,'%Y/%m/%d %H:%M'))
        print t 

        uname = u.text[len(pt):].encode('utf8')
        uname = uname[uname.index('：')+3 :].replace('客户端用户','火星网友').replace('手机用户','火星网友') if uname.find('：') != -1 else uname
        print uname

        pcomment = txtDet.findAll('p')
        pcomment = [b.text.encode('utf8') for b in pcomment]
        pcomment = '\r\n--------\r\n'.join(pcomment)
        print pcomment
        if len(pcomment) < 1 : continue

        sql = "insert into PNComment(PNId, PNComment, PCNickName, PNType, PublishTime) values('%s', '%s', '%s', '%s', '%s');" %(NewId, pcomment, uname, '1', t)
        print sql
        my_db.myexce(sql, 0)

    soup3.decompose()



def nextPageContent(url):
    result = urllib2.urlopen(url)
    html = result.read()
    soup2 = BeautifulSoup(html,fromEncoding="gb18030")
 
    ##body
    body = soup2.find('div', attrs={"id" : "main_content"}).findAll('p')
    neirong = ''; 
    length = len(body)
    for i in range(0,length):
        tmp = body[i]
        if not tmp.text:continue
        if tmp.has_key('class') and ( tmp['class'] == 'picIntro' ) : continue
        neirong += tmp.text.encode('utf8')
        neirong += '\r\n'

    soup2.decompose()
    return neirong



def findDetailNews(list_url,detail_url,NewId):
    page = urllib2.Request(url=detail_url)
    result = urllib2.urlopen(page)
    #result = urllib2.urlopen(detail_url)
    html = result.read()
    soup1 = BeautifulSoup(html,fromEncoding="gb18030")

    content = soup1.find('div',attrs={"id" : "artical"})
    #print 'content====>', content
    if not content: 
        del_news(NewId)
        return

    ##image
    img = content.find('p', attrs={"class" : "detailPic"})
    #print 'img:==>' , img
    if not img:
        del_news(NewId)
        return 

    img_str = img.find('img')
    if not img_str: 
        del_news(NewId)
        return 

    icon_big_url = img_str['src']
    if not icon_big_url: 
        del_news(NewId)
        return

    #print "image:",icon_big_url
    get_image(icon_big_url,NewId,1)
    get_image(icon_big_url,NewId,2)

    ##src_desc
    src = content.find('span', attrs={"itemprop" : "publisher"})
    src = src.find('span', attrs={"itemprop" : "name"}) 
    src_desc = src.text.encode('utf8')
    print 'src_desc:', src_desc

    ##summary
    s = soup1.find('meta', attrs={"name" : "description"})
    summary = s["content"].encode('utf8') 
    #print 'summary:', summary


    ##body
    body = content.find('div', attrs={"id" : "main_content"}).findAll('p')
    neirong = ''; 
    length = len(body)
    for i in range(0,length):
        tmp = body[i]
        if not tmp.text:continue
        if tmp.has_key('class') and ( tmp['class'] == 'picIntro' ) : continue
        neirong += tmp.text.encode('utf8')
        neirong += '\r\n'
    if not neirong:
        sql = "delete from News where NewsId = %d" % NewId;  my_db.myexce(sql,0)
    neirong = trim(neirong).encode('utf8')
    #print 'neirong:', neirong

    #nextpage deal
    next_pages = soup1.find('div', attrs={"class" : re.compile("^pageNum ss_none")})
    if next_pages:
        pages = next_pages.findAll('a')
        length = len(pages)
        result = ''
        for i in range(0, length):
            tmp = pages[i]
            url = tmp['href']
            result += nextPageContent(url)

        #print 'result: ', result

        neirong += trim(result.encode('utf8'))
        #print 'neirong:' , neirong

    sql = "update News set icon='images/%d.jpg', content='%s', icon_big='images/%d_big.jpg', summary='%s', src_desc='%s' where NewsId=%d" % (NewId, neirong, NewId, summary, src_desc, NewId)
    #print 'sqlb1:', sql

    my_db.myexce(sql,0)

    #getcomments
    findComments(detail_url,NewId)


    soup1.decompose()


def fh_jk(list_url):
    page = urllib2.Request(url=list_url)
    result = urllib2.urlopen(page)

    html = result.read()
    soup = BeautifulSoup(html, fromEncoding="gb18030")

    nl = soup.findAll('div', attrs={"class" : "newsList"})[0].findAll('li')
    length = len(nl); 
    logfile('length:%s' %length)

    continue_counter = 0

    for i in range(0,length):
        temp = nl[i].find('a')
        detail_url = temp['href'].encode('utf8'); #print detail_url
        logfile(detail_url)
        title = temp.contents[0].encode('utf8'); 
        print 'title:', title

        sql = "select * from News where url='%s'" % detail_url; 
        #print 'sql0:', sql

        rs = my_db.myexce(sql,1)
        #print 'rs:----->', rs
        if rs: 
            continue_counter += 1
            #if continue_counter > 5: return
            continue

        content = ''
        time_n = int(time.time()); nType = random.randint(1,5)
        sql = "insert into News(url,title,content,nType,ts) values('%s','%s','%s',%d,%d)" % (
                detail_url,title,content,nType,time_n); my_db.myexce(sql,0)
        #print 'sql1:', sql

        sql = "select NewsId from News where url = '%s'" % detail_url; rs = my_db.myexce(sql,1)
        findDetailNews(list_url,detail_url,rs[0])
        logfile(title)

        #time.sleep(10)
    soup.decompose()


fh_jk('http://fashion.ifeng.com/listpage/5574/1/list.shtml')
#findDetailNews('','http://fashion.ifeng.com/a/20141028/40053543_0.shtml',235)


#detail_url = 'http://fashion.ifeng.com/a/20140901/40039185_0.shtml'
#NewId = 734 
#findComments(detail_url,NewId)



