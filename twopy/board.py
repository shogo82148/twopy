#!/usr/bin/env python
#-*- coding:utf-8 -*-

import urllib, urllib2, time, re
import twopy, utility

class Board (object):
  """
  2chの板全般を管理するクラスです。
  """
  
  __tr_re     = re.compile(r"(?P<title>.*) \((?P<res>\d*)\)")
  __server_re = re.compile(r"http://.+?/")
  __name_re = re.compile(r"http://.+?/(.+?)/")
  
  def __init__(self, url, user=None):
    """
    オブジェクトのコンストラクタです。
    
    url  : 対象の2ch板のURL
    user : 通信に用いるtwopy.Userクラスのインスタンス
    """
    u = url.endswith("/") and url or url + "/"
    self.__url  = u
    self.__user = user or twopy.User.anonymouse()
    self.__isRetrieved = False
    
    self.__index = 0
    self.__threads = []
  
  def getUrl(self): return self.__url
  def setUrl(self, url):
    if type(url) == str:
      self.__url = url
    else: raise AttributeError
  url = property(getUrl, setUrl)
  
  def getConfig(self): return self.__conf
  def setConfig(self, conf): self__conf = conf
  config = property(getConfig, setConfig)
  
  def getSubject(self):
    su = self.url.endswith("/") and \
         self.url + "subject.txt" or self.url + "/subject.txt"
    return su
  subject_url = property(getSubject)
  
  def getBBS(self):
    b = self.url.endswith("/") and \
        self.url + "test/bbs.cgi" or self.url + "/test/bbs.cgi"
  
  def get_isRetrieved(self): return self.__isRetrieved
  isRetrieved = property(get_isRetrieved)
  
  def getUser(self): return self.__user
  user = property(getUser)
  
  def getServer(self):
    return Board.__server_re.search(self.url).group(0)
  server = property(getServer)
  
  def getName(self):
    return Board.__name_re.search(self.url).group(1)
  name = property(getName)
  
  def __init_threads(self):
    self.__threads = []
    self.__isRetrieved = False
  
  def retrieve(self):
    """
    対象の板からスレッド一覧を取得します。
    """
    self.__init_threads()
    
    try:
      response = self.user.urlopen(self.subject_url, gzip=False)
    except urllib2.HTTPError, e:
      return e.code
    if response.code == 200:
      rawdata = unicode(response.read(), 'Shift_JIS', 'ignore')
      dat = rawdata.split("\n")
      for thread_str in dat:
        columns = thread_str.split("<>")
        if len(columns) < 2 : continue
        r = Board.__tr_re.search(columns[1])
        title = r.group("title")
        res   = int(r.group("res"))
        th = twopy.Thread(self, columns[0], self.user, title, res)
        self.__threads.append(th)
      self.__isRetrieved = True
    
    return response.code
  
  def createNewThread(self, subject=u"", name=u"", mailaddr=u"", message=u"",
                      submit=u"新規スレッド作成", hidden={}, delay=5):
    """
    新しくスレッドを生成します.
    
    引数:
    subject  : スレッドのタイトル
    name     : 名前
    mailaddr : メールアドレス
    message  : 本文の文章
    submit   : 書き込みボタンのキャプション
    hidden   : hidden属性の値
    delay    : 本来の時間から何秒だけ後戻りさせるか(未来の時間に書き込むのを防ぐ)
    
    返り値:
    レスポンスコードと受信した文章の本文のタプル.
    レスポンスコード:
    twopy.STATUS_TRUE   書き込み成功
    twopy.STATUS_FALSE  書き込み成功&警告
    twopy.STATUS_ERROR  書き込み失敗
    twopy.STATUS_CHECK  書き込み警告
    twopy.STATUS_COOKIE 書き込み確認
    
    ただし、レスポンスコードがtwopy.STATUS_COOKIEの場合、
    返り値はレスポンスコード、受信した文章の本文、input->hidden属性の辞書が返されます.
    """
    referer = self.url
    send_dict = { "bbs" : self.name,
                  "subject" : subject.encode("Shift_JIS"),
                  "time" : int(time.time())-delay,
                  "FROM" : name.encode("Shift_JIS"),
                  "mail" : mailaddr.encode("Shift_JIS"),
                  "MESSAGE" : message.encode("Shift_JIS"),
                  "submit" : submit.encode("Shift_JIS")}
    send_dict.update(hidden)
    params = urllib.urlencode(send_dict)
    
    return utility.bbsPost(self.user, self, params, referer)
  
  def __len__(self):
    if not self.isRetrieved: raise twopy.NotRetrievedError
    return len(self.__threads)
  
  def __iter__(self):
    if not self.isRetrieved: raise twopy.NotRetrievedError
    for thread in self.__threads:
      yield thread
  
  def __getitem__(self, i):
    if not self.isRetrieved: raise twopy.NotRetrievedError
    return self.__threads[i]
