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


class BrokenError (Exception):
    """
    スレッドが壊れているときに送出されるエラーです.
    """
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return "BrokenError: %s" % (self.value)


class Message:
    __title_re = re.compile("<title>(?P<title>.*?)</title>")
    __body_re = re.compile("<body>(?P<body>.*?)</body>")

    def __init__(self, dat):
        if type(dat) == str or type(dat) == str:
            self.__title = Message.__title_re.search(dat).group("title")
            self.__body = Message.__body_re.search(dat).group("body")
        elif type(dat) == tuple or type(dat) == list:
            self.__title = dat[0]
            self.__body = dat[1]
        elif type(dat) == dict:
            self.__title = dat["title"]
            self.__body = dat["body"]
        else:
            self.__title = ""
            self.__body = ""

    def getTitle(self):
        return self.__title
    title = property(getTitle)

    def getBody(self):
        return self.__body
    body = property(getBody)
