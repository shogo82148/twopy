#!/usr/bin/env python
#-*- coding:utf-8 -*-

import re
import datetime
import xml.sax.saxutils
import unicodedata


class Comment:
    """
    スレッド上のコメントを管理するクラスです.
    """

    __delete_tag = re.compile(r"<.+?>")
    __date_and_id = re.compile(r"(?P<date>.*) ID:(?P<id>\S*)")
    __be = re.compile(r"BE:(?P<be>.*)")
    __datetime = re.compile((r"(?P<year>\d{4})/(?P<month>\d{2})/"
                             r"(?P<day>\d{2})\(.*\) "
                             r"(?P<hour>\d{2}):(?P<min>\d{2}):"
                             r"(?P<sec>\d{2})(\.(?P<csec>\d+)|)"))
    __datetime2 = re.compile((r"(?P<year>\d{2})/(?P<month>\d{2})/"
                              r"(?P<day>\d{2})\(.*\) "
                              r"(?P<hour>\d{2}):(?P<min>\d{2}):"
                              r"(?P<sec>\d{2})(\.(?P<csec>\d+)|)"))
    __urls = re.compile(r"(ttps?:\/\/[-_.!~*'()a-zA-Z0-9;/?:@&=+$,%#]+)")
    __response = re.compile((r"(>>\d{1,4}|＞＞[０-９]{1,4})"
                             r"(-\d{1,4}|−[０-９]{1,4}|)"))

    def __init__(self, thread, line, number):
        """
        オブジェクトのコンストラクタです.

        thread : コメントが保存されている親スレッドのインスタンス
        line   : 初期化に用いられる、datファイルの一行.
                 この引数はunicode型でなければなりません.
        number : スレッドからの、コメント位置.
        """
        self.thread = thread
        self.number = number
        self.line = line
        self.__datetime_cache = None
        self.__urls_cache = None
        if type(line) == str:
            columns = line.split("<>")
        elif type(line) == str:
            columns = str(line, "MS932", "replace").split("<>")
        else:
            raise TypeError("the type of the argument 'line' is not unicode or str.")
        if len(columns) < 5:
            raise TypeError
        self.__name = Comment.__delete_tag.sub("", columns[0])
        self.__mailaddr = columns[1]
        raw_body = Comment.__delete_tag.sub("", columns[3].replace(" <br> ", "\n"))
        self.__body = xml.sax.saxutils.unescape(raw_body)[1:-1]  # 余分なスペースの削除

        self.__date = ""
        self.__id = ""
        di_result = Comment.__date_and_id.search(columns[2])
        if di_result:
            self.__date = di_result.group("date") or ""
            self.__id = di_result.group("id") or ""
        else:
            self.__date = columns[2]
        be_result = Comment.__be.search(columns[2])
        self.__be = None
        if be_result:
            self.__be = be_result.group("be")
        self.__responses_cache = None

    def getName(self):
        return self.__name
    name = property(getName)

    def getMailAddr(self):
        return self.__mailaddr
    mailaddr = property(getMailAddr)

    def getDate(self):
        return self.__date
    date = property(getDate)

    def getBody(self):
        return self.__body
    body = property(getBody)

    def getDatetime(self):
        if self.__datetime_cache:
            return self.__datetime_cache

        result = Comment.__datetime.search(self.__date)
        if result:
            year = int(result.group("year"))
            month = int(result.group("month"))
            day = int(result.group("day"))
            hour = int(result.group("hour"))
            m = int(result.group("min"))
            sec = int(result.group("sec"))
            c = result.group("csec")
            csec = int(c) if c else 0
            if day>=32: #エイプリルフール対策
                day = 1
                month += 1

            d = datetime.datetime(year, month, day, hour, m, sec, csec * 10000)
            self.__datetime_cache = d
            return d

        result = Comment.__datetime2.search(self.__date)
        if result:
            year = int(result.group("year")) + 2000
            month = int(result.group("month"))
            day = int(result.group("day"))
            hour = int(result.group("hour"))
            m = int(result.group("min"))
            sec = int(result.group("sec"))
            c = result.group("csec")
            csec = int(c) if c else 0
            if day>=32: #エイプリルフール対策
                day = 1
                month += 1

            d = datetime.datetime(year, month, day, hour, m, sec, csec * 10000)
            self.__datetime_cache = d
            return d

        return None
    datetime = property(getDatetime)

    def getID(self):
        return self.__id
    ID = property(getID)

    def getBe(self):
        return self.__be
    be = property(getBe)

    def extractUrls(self):
        """
        コメントの内容から、URLの一覧を抽出して返します.
        """
        if self.__urls_cache:
            return self.__urls_cache
        result = Comment.__urls.finditer(self.body)
        l = ["".join(("h", r.group(0))) for r in result]
        self.__urls_cache = l
        return l
    urls = property(extractUrls)

    def __extractResponses(self):
        if self.__responses_cache == None:
            result = Comment.__response.finditer(self.body)
            l = [(r.group(1), r.group(2)) for r in result]
            self.__responses_cache = l
            return l
        else:
            return self.__responses_cache

    def extractResponses(self):
        """
        コメントの内容からレスポンスの一覧を抽出し、文字列として返します.
        """
        l = self.__extractResponses()
        if returnType == "str":
            return ["".join(i) for i in l]
        elif returnType == "int":
            return self.__makeIntegerLists(l)
        elif returnType == "comment":
            rl = self.__makeIntegerLists(l)
            rl2 = []
            for i in rl:
                if type(i) == int:
                    if 0 < i <= self.thread.res:
                        rl2.append(self.thread[i])
                else:
                    rl2.append([self.thread[j] for j in i if 0 < j <= self.thread.res])
            return rl2
        else:
            raise TypeError
    res = property(extractResponses)
    responses = property(extractResponses)

    def extractResponsesAsInteger(self):
        """
        コメントの内容からレスポンスの一覧を抽出し、整数のリストとして返します.
        """
        l = self.__extractResponses()
        rl = []
        for i in l:
            start = int(unicodedata.normalize("NFKC", i[0][2:]))
            if i[1] == "":
                rl.append(start)
            else:
                end = int(unicodedata.normalize("NFKC", i[1][1:]))
                rl.append(list(range(start, end + 1)))
        return rl
    
    def extractResponsesAsComment(self):
        """
        コメントの内容からレスポンスの一覧を抽出し、コメントのリストとして返します.
        """
        rl = self.extractResponsesAsInteger()
        rl2 = []
        for i in rl:
            if type(i) == int:
                if 0 < i <= self.thread.res:
                    rl2.append(self.thread[i])
                else:
                    rl2.append([self.thread[j] for j in i if 0 < j <= self.thread.res])
                return rl2
            else:
                raise TypeError

    def render(self):
        """
        取得したコメントから、整形された文章を返します.
        """
        if self.be:
            header = "%i 名前:%s [%s]: %s ID:%s BE:%s" % \
                (self.number, self.name, self.mailaddr, self.date, self.ID, self.be)
        else:
            header = "%i 名前:%s [%s]: %s ID:%s" % \
                (self.number, self.name, self.mailaddr, self.date, self.ID)
        return "%s\n%s\n" % (header, self.body)

    def __unicode__(self):
        return self.render()
