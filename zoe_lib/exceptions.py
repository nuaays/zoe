class ZoeException(Exception):
    """
    A generic exception.
    """
    def __init__(self, message='Something happened'):
        self.message = message

    def __str__(self):
        return self.message


class ZoeAPIException(Exception):
    """
    An exception generated by the API (client-side).
    """
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


class InvalidApplicationDescription(ZoeAPIException):
    """
    An exception thrown while parsing an application description.
    """
    def __init__(self, msg):
        self.message = "Error: " + msg
