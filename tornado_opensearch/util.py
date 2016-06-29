# coding: utf-8
import functools
import urllib.parse
import operator


_quote = functools.partial(urllib.parse.quote, safe="-_.~")


def urlquote(value):
    """ URL 编码（注意部分符号是不编码的）"""
    if not isinstance(value, str):
        if hasattr(value, "decode"):
            value = value.decode("utf-8")
        else:
            value = str(value)

    return _quote(value)


def items_key_ascending(dct):
    """按 key 的升序取得字典的 items"""
    return sorted(
        dct.items(),
        key=operator.itemgetter(0)
    )
