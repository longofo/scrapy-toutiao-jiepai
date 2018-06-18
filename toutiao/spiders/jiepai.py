# -*- coding: utf-8 -*-
import re

import scrapy
import urllib
import json
from ..items import ToutiaoItem
from ..logger import logger

class JiepaiSpider(scrapy.Spider):
    name = 'jiepai'
    # allowed_domains = ['www.toutiao.com']

    start_url = 'https://www.toutiao.com/search_content/'
    query = '?offset={offset}&format=json&keyword={keyword}&autoload=true&count=20&cur_tab=3&from=gallery'



    def __init__(self, keyword,*args,**kwargs):
        super(JiepaiSpider, self).__init__(*args,**kwargs)
        self.keyword = urllib.parse.quote(keyword)
        self.offset = 0

    def start_requests(self):
        url = urllib.parse.urljoin(
                self.start_url, self.query.format(offset=self.offset, keyword=self.keyword))
        yield scrapy.Request(url=url, callback=self.parse_index)

    @classmethod
    def from_crawler(cls, crawler,*args,**kwargs):
        return cls(crawler.settings.get('KEYWORD'),*args,**kwargs)

    def parse_index(self, response):
        result = json.loads(response.text)
        # 判断data是否为空列表
        if result.get('data'):
            for data in result.get('data'):
                item = ToutiaoItem()
                item['title'] = data.get('title')
                item['detail_url'] = data.get('article_url')
                yield scrapy.Request(url=data.get('article_url'), callback=self.parse_detail, meta={'item': item})
        # data不为空列表,才继续获取下一页
        if result.get('data'):
            self.offset += 20
            next = urllib.parse.urljoin(
                    self.start_url, self.query.format(offset=self.offset, keyword=self.keyword))
            yield scrapy.Request(url=next, callback=self.parse_index)

    def parse_detail(self, response):
        # 头条封的时候不是403禁止,而是返回空页面。所以无法根据状态码判断。这里使用img标签判断
        if 'img' not in response.text:
            yield scrapy.Request(url=response.url,callback=self.parse_detail,meta={'use_proxy':True})

        item = response.meta.get('item')
        html = response.text

        # 从网页的js中解析出图片链接
        partten = re.compile(r'gallery: JSON.parse\(\"(.*?)\"\)', re.S)
        result = re.search(partten,html)
        try:
            data = json.loads(result.group(1).replace('\\',''))
            image_lst = []
            for image in data.get('sub_images'):
                image_lst.append(image.get('url'))
            item['image_lst'] = image_lst
            yield item
        except Exception as e:
            logger.exception('exception occured')