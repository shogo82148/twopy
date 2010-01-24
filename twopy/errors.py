#!/usr/bin/env python
#-*- coding:utf-8 -*-

import re

class DatoutError (Exception):
  """
  対象のURLがdat落ちとなった場合に送出されるエラーです.
  """
  def __init__(self, value):
    self.value = value
  
  def __str__(self):
    return "DatoutError: %s" % (self.value)

class NotRetrievedError (Exception):
  """
  対象のオブジェクトがまだ取得されていない場合に送出されるエラーです.
  """
  def __init__(self, value="an object is not retrieved."):
    self.value = value
  
  def __str__(self):
    return "NotRetrievedError: %s" % (self.value)

class Message (object):
  
  __title_re = re.compile("<title>(?P<title>.*?)</title>")
  __body_re  = re.compile("<body>(?P<body>.*?)</body>")
  
  def __init__(self, dat):
    self.__title = Message.__title_re.search(dat).group("title")
    self.__body = Message.__body_re.search(dat).group("body")
  
  def getTitle(self): return self.__title
  title = property(getTitle)
  
  def getBody(self): return self.__body
  body = property(getBody)
