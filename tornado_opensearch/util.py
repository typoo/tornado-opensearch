# coding: utf8
import functools
import urllib.parse


_quote = functools.partial(urllib.parse.quote, safe="-_.~")


def urlquote(value):
    """ URL 编码（注意部分符号是不编码的）"""
    if not isinstance(value, str):
        if hasattr(value, "decode"):
            value = value.decode("utf8")
        else:
            value = str(value)

    return _quote(value)
