#!/usr/bin/env python
#-*- coding:utf-8 -*-

import urllib, urllib2, gzip, StringIO, re, time, datetime
import twopy, utility

class Thread (object):
  """
  2chのスレッドを管理するクラスです.
  """
  
  __url  = re.compile(r"http://(.+?)/test/read.cgi/(.+?)/(\d+)")
  __etag = re.compile(r'".*"')
  __hidden = re.compile(r'input type=hidden name="(.+?)" value="(.+?)"')
  
  @classmethod
  def initWithURL(cls, url, board=None, user=None):
    """
    スレッドを示すURLから、対象のThreadクラスを生成します.
  
    url   : 対象となるURL
    board : Boardインスタンスが既にある場合は指定
    user  : 通信に用いるtwopy.Userクラスのインスタンス
    """
    server, board_name, dat_number = Thread.parseURLToProperties(url)
    
    u = user or twopy.User.anonymouse()
    if board: b = board
    else:
      board_url = "http://%s/%s/" % (server, board_name)
      b = twopy.Board(board_url, u)
    filename = "%s.dat" % dat_number 
    return Thread(b, filename, u)
  
  @classmethod
  def initWithDat(cls, dat, url, user=None):
    """
    datからThreadクラスを生成します。
    
    dat : スレッドのdatが格納されている文字列
    url : スレッドを指し示すURL
    """
    thread = Thread.initWithURL(url)
    thread._Thread__rawdat = dat
    thread.reload()
    return thread
    
  @classmethod
  def parseURLToProperties(cls, url):
    """
    スレッドを示すURLから
    (サーバードメイン, 板の名前, スレッド番号)
    からなる文字列のタプルを返します。
    """
    rs = Thread.__url.search(url)
    assert rs, Exception("this url is not valid.")
    
    server     = rs.group(1)
    board_name = rs.group(2)
    dat_number = rs.group(3)
    
    return (server, board_name, dat_number)
  
  def __init__(self, board, filename, user=None, title="", initialRes=0):
    """
    オブジェクトのコンストラクタです.
  
    board      : 対象となる板のインスタンス
    filename   : datファイル名
    user       : 通信に用いるtwopy.Userクラスのインスタンス
    title      : スレッドのタイトルが判明している場合は別途指定.
                 retrieve()が呼び出された場合は、取得したスレッド名で上書きされる.
    initialRes : スレッドのレス数が判明している場合は別途指定.
    """
    self.__board = board
    self.__filename = filename
    self.__user = user or twopy.User.anonymouse()
    self.__title = title
    self.__initialResNumber = initialRes
    self.__rawdat = ""
    self.__comments = []
    
    self.__isBroken   = False
    self.__last_modified = None
    self.__etag  = None
  
  def __init_thread(self):
    self.__rawdat = ""
    self.__comments = []
  
  def getBoard(self): return self.__board
  board = property(getBoard)
  
  def getFilename(self): return self.__filename
  filename = property(getFilename)
  
  def getUser(self): return self.__user
  user = property(getUser)
  
  def getConfig(self): return self.__conf
  def setConfig(self, conf): self__conf = conf
  config = property(getConfig, setConfig)
  
  def getTitle(self): return self.__title
  title = property(getTitle)
  
  def getInitialResponse(self): return self.__initialResNumber
  initialRes = property(getInitialResponse)
  
  def getResponse(self):
    if self.isRetrieved: return len(self.__comments)
    else: return self.__initialResNumber
  response = property(getResponse)
  res      = property(getResponse)
  
  def getPosition(self): return len(self.__comments)
  position = property(getPosition)
  
  def getDat(self): return self.__rawdat
  dat = property(getDat)
  
  def getDatNumber(self):
    return int(self.filename[:-4])
  dat_number = property(getDatNumber)
  
  def get_isRetrieved(self):
    if len(self.__comments) > 0: return True
    else: return False
  isRetrieved = property(get_isRetrieved)
  
  def get_isBroken(self): return self.__isBroken
  isBroken = property(get_isBroken)
  
  def getUrl(self):
    u = "%sdat/%s" % (self.board.url, self.filename)
    return u
  url = property(getUrl)
  
  def getCGIUrl(self):
    u = "%stest/read.cgi/%s/%s/" % (self.board.url, self.board.name, self.filename[:-4])
    return u
  cgi_url = property(getCGIUrl)
  
  def getSince(self):
    return datetime.datetime.fromtimestamp(self.dat_number)
  since = property(getSince)
  
  def getVelocity(self, t=None):
    tp = t or time.time()
    now = int(tp)
    delta = now - self.dat_number
    return self.response / float(delta)*3600
  velocity = property(getVelocity)
  
  def retrieve(self):
    """
    スレッドからdatファイルを読み込み、その内容を取得します.
    
    返り値: HTTPステータスコードと、取得したコメントが格納されている配列のタプル
    """
    self.__init_thread()
    response = self.user.urlopen(self.url, gzip=True)
    
    if response.code == 200:
      headers = response.info()
      self.__last_modified = headers["Last-Modified"]
      self.__etag = Thread.__etag.search(headers["ETag"]).group(0)
      gzip_str = StringIO.StringIO(response.read())
      self.__rawdat = gzip.GzipFile(fileobj=gzip_str).read()
      if self.__rawdat.startswith("<html>"):
        # Dat落ちと判断
        raise twopy.DatoutError, twopy.Message(self.__rawdat)
      self.__parseDatToComments(unicode(self.__rawdat, "Shift_JIS", "replace"))
      self.__isBroken   = False
      self.__res = len(self.__comments)
    elif response.code == 203:
      # Dat落ちと判断(10/01/24現在のanydat.soモジュールの仕様より)
      raise twopy.DatoutError, twopy.Message([u"203 Non-Authoritative Information", u"203レスポンスヘッダが返されました。このスレッドはDat落ちになったものと考えられます。"])
    elif response.code == 404:
      raise twopy.DatoutError, twopy.Message([u"404 File Not Found", u"404レスポンスヘッダが返されました。このスレッドはDat落ちになったものと考えられます。"])
    
    return (response.code, self.__comments)
  
  def __parseDatToComments(self, dat):
    comments = []
    for line in dat.split("\n"):
      if len(self.__comments) == 0 :
        columns = line.split("<>")
        self.__title = columns[4]
      if line != "":
        tmp = twopy.Comment(self, line, self.position+1)
        comments.append(tmp)
        self.__comments.append(tmp)
    return comments

  def update(self):
    """
    スレッドの内容を更新します.
    
    返り値: HTTPステータスコードと、取得したコメントが格納されている配列のタプル
    """
    assert not self.isBroken, twopy.BrokenError("this thread is broken. not updated.")
    if not self.isRetrieved: # 未取得だった場合
      return self.retrieve()

    updatedComments = []
    try:
      response = self.user.urlopen(self.url, gzip=False, bytes=len(self.__rawdat),
                                   if_modified_since=self.__last_modified,
                                   if_none_match=self.__etag)
      if response.code == 206:
        # datが更新されていた場合
        headers = response.info()
        self.__last_modified = headers["Last-Modified"]
        self.__etag = Thread.__etag.search(headers["ETag"]).group(0)
        newdat = response.read()
        self.__rawdat += newdat
        updatedComments = self.__parseDatToComments(newdat)
      elif response.code == 416:
        # datが壊れている場合
        self.__isBroken = True
      elif response.code == 203:
        # dat落ちと判断
        raise twopy.DatoutError, twopy.Message( (u"203 Non-Authoritative Information", u"203レスポンスヘッダが返されました。このスレッドはDat落ちになったものと考えられます。") )
      elif response.code == 404:
        # dat落ちと判断
        raise twopy.DatoutError, twopy.Message( (u"404 File Not Found", u"404レスポンスヘッダが返されました。このスレッドはDat落ちになったものと考えられます。") )
      else: raise TypeError
      
      return (response.code, updatedComments)
    
    except urllib2.HTTPError, e:
      if e.code == 304:
        # datが更新されていない場合
        pass
      return (e.code, updatedComments)
  
  def reload(self):
    """
    現在保管しているdatデータを再読み込みします。
    """
    self.__comments = self.__parseDatToComments(self.__rawdat)
    self.__isBroken = False 
  
  def reloadWithDat(self, dat):
    """
    DATデータからThreadクラスを再読み込みします。
    """
    self.__rawdat = dat
    self.__comments = self.__parseDatToComments(dat)
    self.__isBroken = False
  
  def autopost(self, name=u"", mailaddr=u"", message=u"",
               submit=u"書き込む", delay=5):
    """
    書き込みの確認をすべてスキップして書き込みます.
    """
    r1 = self.post(name, mailaddr, message, submit, delay=delay)
    if r1[0] == twopy.STATUS_COOKIE:
      r2 = self.post(name, mailaddr, message, submit, hidden=r1[2], delay=delay)
      return r2
    else:
      return r1
  
  def post(self, name=u"", mailaddr=u"", message=u"",
           submit=u"書き込む", hidden={}, delay=5):
    """
    コメントの書き込みを試みます.
    
    引数:
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
    referer = "%stest/read.cgi/%s/%i/" % (self.board.server, self.board.name, self.dat_number)
    send_dict = { "bbs"  : self.board.name,
                  "key"  : self.dat_number,
                  "time" : int(time.time())-delay,
                  "FROM" : name.encode("Shift_JIS"),
                  "mail" : mailaddr.encode("Shift_JIS"),
                  "MESSAGE" : message.encode("Shift_JIS"),
                  "submit"  : submit.encode("Shift_JIS")}
    send_dict.update(hidden)
    params = urllib.urlencode(send_dict)
    
    return utility.bbsPost(self.user, self.board, params, referer)
  
  def __iter__(self):
    if not self.isRetrieved: raise twopy.NotRetrievedError
    for comment in self.__comments:
      yield comment
  
  def __len__(self):
    if not self.isRetrieved: raise twopy.NotRetrievedError
    return len(self.__comments)
  
  def __getitem__(self, i):
    if not self.isRetrieved: raise twopy.NotRetrievedError
    return self.__comments[i-1]
