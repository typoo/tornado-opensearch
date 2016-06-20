# coding: utf-8


class Error(Exception):
    pass


class APIError(Error):
    pass


class AccessRestricted(APIError):
    pass


class InvalidSignature(APIError):
    pass
