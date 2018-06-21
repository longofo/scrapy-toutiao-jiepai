# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals,Request
from scrapy.exceptions import IgnoreRequest
from .logger import logger
import requests
import re
import time
from .exceptions import NeedProxyError


class ToutiaoSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class ToutiaoDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class ProxiesMiddleware(object):
    def __init__(self, proxies_pool_url):
        self.proxies_pool_url = proxies_pool_url

    def _get_ramdom_proxies(self, max_try=0):
        try:
            res = requests.get(self.proxies_pool_url, timeout=3)
            if res.status_code == 200 and re.match(r'\d+.\d+.\d+.\d+:\d+', res.text):
                return res.text
            else:
                logger.warning('waiting proxies...')
                time.sleep(2)
                if max_try > 10:
                    return None
                self._get_ramdom_proxies(max_try=max_try + 1)
        except Exception as e:
            logger.exception('connect error')
            return None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            proxies_pool_url=crawler.settings.get('PROXIES_POOL_URL')
        )

    def process_request(self, request, spider):
        if request.meta.get('use_proxy'):
            raise NeedProxyError('need proxies')

    def process_response(self, request, response, spider):

        info = '{url},proxies {proxies},status {status}'
        logger.info(info.format(url=response.url,proxies=request.meta.get('proxy'), status=response.status))
        if response.status == 403:
            meta = request.meta
            meta['use_proxy'] = True
            return Request(url=response.url,callback=request.callback,meta=meta,dont_filter=True)
        if re.search(r'(4|5)\d+', str(response.status)):
            raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain

        # if not request.meta.get('use_proxy'):
        #     return None
        proxies = self._get_ramdom_proxies()
        meta = request.meta
        if proxies:
            logger.warning('use proxies:{proxies} for {url}'.format(proxies=proxies,url=request.url))
            meta['proxy'] = 'http://' + proxies
            meta['has_proxy'] = True
            meta['download_timeout'] = 5
        else:
            logger.warning('No valid proxies or exception')
        return Request(url=request.url,callback=request.callback,meta=meta,dont_filter=True)