#!/usr/bin/env python
#-*- coding:utf-8 -*-

import urllib2, cookielib, re

class User (object):
	"""
	クッキーの管理や、ユーザーエージェントなどのヘッダ全般を管理するクラスです.
	"""
	@classmethod
	def anonymouse(cls):
		return User()
	
	def __init__(self,
	             user_agent = "Monazilla 1.00",
	             language   = "ja",
	             keep_alive = 300):
		self.user_agent = user_agent
		self.language   = language
		self.keep_alive = keep_alive
		
		cj = cookielib.CookieJar()
		self.__cookie = cj
		self.__opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
	
	def getOpener(self): return self.__opener
	opener = property(getOpener)
	
	def getCookie(self): return self.__cookie
	cookie = property(getCookie)
	
	def getRequest(self, url, gzip=False, bytes=0,
	               if_modified_since=None, if_none_match=None):
		headers = {
			"User-Agent" : self.user_agent,
			"Accept-Language" : self.language,
			"Keep-Alive" : str(self.keep_alive),
			"Connection" : "close",
		}
		if gzip: headers["Accept-Encoding"] = "gzip"
		if bytes > 0 :
			headers["If-Modified-Since"] = if_modified_since
			headers["If-None-Match"]     = if_none_match
			headers["Range"]             = "bytes= %i-" % bytes
		req = urllib2.Request(url, None, headers)
		return req
	
	def urlopen(self, url, gzip=False, bytes=0,
	            if_modified_since=None, if_none_match=None):
		req = self.getRequest(url, gzip, bytes, if_modified_since, if_none_match)
		return self.opener.open(req)
	
	def urlpost(self, url, param, referer):
		headers = {
			"User-Agent" : self.user_agent,
			"Accept" : "*/*",
			"Accept-Language" : self.language,
			"Keep-Alive" : str(self.keep_alive),
			"Referer" : referer,
			"Connection" : "close",
		}
		req = urllib2.Request(url, None, headers)
		self.__cookie.add_cookie_header(req)
		return self.opener.open(req, param)
