#!/usr/bin/env python
#-*- coding:utf-8 -*-

import re

STATUS_FALSE  = 0
STATUS_TRUE   = 1
STATUS_ERROR  = 2
STATUS_CHECK  = 3
STATUS_COOKIE = 4

__status_false    = re.compile(u"2ch_X:false")
__status_true     = re.compile(u"(2ch_X:true|書きこみました)")
__status_error    = re.compile(u"(2ch_X:error|ＥＲＲＯＲ)")
__status_check    = re.compile(u"2ch_X:check")
__status_cookie = re.compile(u"(2ch_X:cookie|書き込み確認)")

__hidden = re.compile(r'input type=hidden name="(.+?)" value="(.+?)"')


def bbsPost(user, board, params, referer):
    """
    サーバーの/test/bbs.cgiを呼び出して、書き込みやスレッド作成などの処理を行います.
    """
    url = "%stest/bbs.cgi" % (board.server)

    try:
        response = user.urlpost(url, params, referer)
        if response.code == 200:
            body = unicode(response.read(), "Shift_JIS", "ignore")
            code = __detectStatusCode(body)
            if code == STATUS_COOKIE:
                r = __hidden.search(body)
                d = {r.group(1): r.group(2)}
                return (code, body, d)
            else:
                return (code, body)
        else:
            raise TypeError
    except urllib2.HTTPError, e:
        print e.code


def __detectStatusCode(body):
    """
    与えられた引数からステータスコードを返します.
    """
    if __status_false.search(body):
        return STATUS_FALSE
    elif __status_true.search(body):
        return STATUS_TRUE
    elif __status_error.search(body):
        return STATUS_ERROR
    elif __status_check.search(body):
        return STATUS_CHECK
    elif __status_cookie.search(body):
        return STATUS_COOKIE
    else:
        raise TypeError("twopy can't detect the status code.")
