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
	def initWithUrl(cls, url, user=None):
		"""
		スレッドを示すURLから、対象のThreadクラスを生成します.
	
		url  : 対象となるURL
		user : 通信に用いるtwopy.Userクラスのインスタンス
		"""
		rs = Thread.__url.search(url)
		if rs == None: raise TypeError
		
		server     = rs.group(1)
		board_name = rs.group(2)
		dat_number = rs.group(3)
		
		board_url = "http://%s/%s/" % (server, board_name)
		u = user or twopy.User.anonymouse()
		b = twopy.Board(board_url, u)
		filename = "%s.dat" % dat_number 
		return Thread(b, filename, u)
	
	def __init__(self, board, filename, user=None, title="", res=0):
		"""
		オブジェクトのコンストラクタです.
	
		board    : 対象となる板のインスタンス
		filename : datファイル名
		user     : 通信に用いるtwopy.Userクラスのインスタンス
		title    : スレッドのタイトルが判明している場合は別途指定.
			         retrieve()が呼び出された場合は、取得したスレッド名で上書きされる.
		res      : スレッドのレス数が判明している場合は別途指定.
			         retrieve()が呼び出された場合は、取得したレス数で上書きされる.
		"""
		self.__board = board
		self.__filename = filename
		self.__user = user or twopy.User.anonymouse()
		self.__title = title
		self.__res = res
		self.__rawdat = ""
		self.__comments = []
		
		self.__isRetrieved = False
		self.__isBroken   = False
		self.__last_modified = None
		self.__etag  = None
	
	def __init_thread(self):
		self.__rawdat = ""
		self.__comments = []
		self.__isRetrieved = False
	
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
	
	def getResponse(self): return self.__res
	response = property(getResponse)
	res      = property(getResponse)
	
	def getDatNumber(self):
		return int(self.filename[:-4])
	dat_number = property(getDatNumber)
	
	def get_isRetrieved(self): return self.__isRetrieved
	isRetrieved = property(get_isRetrieved)
	
	def get_isBroken(self): return self.__isBroken
	isBroken = property(get_isBroken)
	
	def getUrl(self):
		u = "%sdat/%s" % (self.board.url, self.filename)
		return u
	url = property(getUrl)
	
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
			self.__appendComments(unicode(self.__rawdat, "Shift_JIS", "replace"))
			self.__isRetrieved = True
			self.__isBroken   = False
			self.__res = len(self.__comments)
	
	def __appendComments(self, dat):
		no_tag = re.compile("<.*?>")
		nt = re.compile("(?P<name>.*)</b>(?P<trip>.*)<b>")
		di = re.compile("(?P<date>.*) ID:(?P<id>.*)")
		
		for (i, line) in enumerate(dat.split("\n")):
			if len(self.__comments) == 0 :
				columns = line.split("<>")
				self.__title = columns[4]
			if line != "":
				self.__comments.append( twopy.Comment(self, line, i+1) )

	def update(self):
		"""
		スレッドの内容を更新します.
		
		返り値: HTTPステータスコード
		"""
		if len(self.__comments) == 0: # 未取得だった場合
			self.retrieve()
			return
		
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
				self.__appendComments(newdat)
				self.__res = len(self.__comments)
			elif response.code == 416:
				# datが壊れている場合
				self.__isBroken = True
			else: raise TypeError
			
			return response.code
		
		except urllib2.HTTPError, e:
			if e.code == 304:
				# datが更新されていない場合
				pass
			return e.code
	
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
		if not self.isRetrieved: raise NotRetrievedError
		for comment in self.__comments:
			yield comment
	
	def __len__(self):
		if not self.isRetrieved: raise NotRetrievedError
		return len(self.__comments)
	
	def __getitem__(self, i):
		if not self.isRetrieved: raise NotRetrievedError
		return self.__comments[i-1]
