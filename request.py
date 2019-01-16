import requests
from settings import *
import redis


class Request(object):
    def __init__(self, log):
        self.session = requests.Session()
        self.session.proxies = self.get_proxies()
        # self.session.timeout = TIMEOUT_TIME    # 不起作用
        self.session.headers = DEFAULT_HEADERS
        self.log = log
        # self.redis_server = redis.Redis(host=REDIS_HOST, password=REDIS_PASSWORD)

    @staticmethod
    def get_proxies():
        proxyHost = "http-dyn.abuyun.com"
        proxyPort = "9020"

        proxyUser = PROXY_USER
        proxyPass = PROXY_PASS

        proxyMeta = "http://%(user)s:%(pass)s@%(host)s:%(port)s" % {
            "host": proxyHost,
            "port": proxyPort,
            "user": proxyUser,
            "pass": proxyPass,
        }

        proxies = {
            "http": proxyMeta,
            "https": proxyMeta,
        }
        return proxies

    def get(self, url, headers=None, params=None, cookies=None):
        count = RETRY_TIMES
        while count > 0:
            try:
                # ip = self.redis_server.get('proxy:a')
                # proxies = {'http': ip.decode('utf-8'), 'https': ip.decode('utf-8')} if ip else None
                response = self.session.get(url=url, headers=headers, params=params, cookies=cookies, timeout=TIMEOUT_TIME)
                if response.status_code == 200:
                    return response
                else:
                    self.log.logger.error('Crawled ({status_code}) <GET {url}>'.format(status_code=str(response.status_code), url=url))
                    count -= 1
            except:
                self.log.logger.exception('connection exception')
                count -= 1

        if count == 0:
            return None

    def post(self, url, headers=None, data=None, cookies=None):
        count = RETRY_TIMES
        while count > 0:
            try:
                # ip = self.redis_server.get('proxy:a')
                # proxies = {'http': ip.decode('utf-8'), 'https': ip.decode('utf-8')} if ip else None
                response = self.session.post(url=url, headers=headers, data=data, cookies=cookies, timeout=TIMEOUT_TIME)
                if response.status_code == 200:
                    return response
                else:
                    self.log.logger.error('Crawled ({status_code}) <POST {url}>'.format(status_code=str(response.status_code), url=url))
                    count -= 1
            except:
                self.log.logger.exception('connection exception')
                count -= 1

        if count == 0:
            return None
