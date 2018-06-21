
class NeedProxyError(Exception):
    def __init__(self,message):
        super(NeedProxyError,self).__init__(message)
        self.message = message


if __name__ == '__main__':
    try:
        raise NeedProxyError('need proxy')
    except NeedProxyError:
        print('need proxy')