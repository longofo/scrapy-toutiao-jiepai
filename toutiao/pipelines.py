# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import os
import queue
import pymongo
import requests
import threading
from .logger import logger


class MongoPipeline(object):
    collection_name = 'jiepai_items'

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
                mongo_uri=crawler.settings.get('MONGO_URI'),
                mongo_db=crawler.settings.get('MONGO_DATABASE', 'items')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        self.db[self.collection_name].insert_one(dict(item))
        return item


class DownloadPicturePipeline(object):
    def __init__(self, proxies_pool_url):
        self.proxies_pool_url = proxies_pool_url

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
                proxies_pool_url=crawler.settings.get('PROXIES_POOL_URL')
        )

    def open_spider(self, spider):
        self.queue = queue.Queue()
        self.base_dir = os.path.abspath(os.path.dirname(__file__))
        self.wait_time = 30
        self.threads = []

        # 创建存储图片文件夹
        store_images = os.path.join(self.base_dir, 'images')
        if not os.path.exists(store_images):
            os.mkdir(store_images)
        self.base_dir = store_images

        # 开启多线程等待下载图片
        for i in range(4):
            t = threading.Thread(target=self.download_pictures)
            self.threads.append(t)
        for t in self.threads:
            t.start()

    def close_spider(self, spider):
        for t in self.threads:
            t.join()

    def process_item(self, item, spider):
        self.queue.put((item.get('title'), item.get('image_lst')))
        return item

    def download_pictures(self):
        while True:
            try:
                dir_name, img_lst = self.queue.get(timeout=self.wait_time)
                logger.info('download picture group:{0}'.format(dir_name))
                store_path = os.path.join(self.base_dir, dir_name)
                if not os.path.exists(store_path):
                    os.mkdir(store_path)
                for url in img_lst:
                    self.download(url, store_path=store_path)
            except queue.Empty:
                break

    def download(self, url, store_path):
        try:
            res = requests.get(url)
            if res.status_code == 200:
                pic_name = url.split('/')[-1] + '.png'
                store_path = os.path.join(store_path, pic_name)
                with open(store_path, 'wb') as f:
                    f.write(res.content)
            info = 'download picture:{url},status:{status}'
            logger.info(info.format(url=url, status=res.status_code))
        except Exception as e:
            info = 'download picture except:{url},error info:{error}'
            logger.error(info.format(url=url, error=str(e.args)))