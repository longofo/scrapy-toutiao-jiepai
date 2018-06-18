# -*- coding: utf-8 -*-

import logging
import os

logger = logging.getLogger(__name__)

base_dir = os.path.abspath(os.path.dirname(__file__))
if not os.path.exists(os.path.join(base_dir,'log')):
    os.mkdir(os.path.join(base_dir,'log'))

# 记录请求状态日志
handler = logging.FileHandler(
        '{dir}/log/access.log'.format(dir=base_dir), mode='a', encoding='UTF-8', delay=0)
handler.setLevel(logging.INFO)
logging_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(logging_format)
# 错误日志
error_handler = logging.FileHandler(
        '{dir}/log/error.log'.format(dir=base_dir), mode='a', encoding='UTF-8', delay=0)
error_handler.setLevel(logging.ERROR)
logging_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
error_handler.setFormatter(logging_format)

logger.addHandler(handler)
logger.addHandler(error_handler)

if __name__ == '__main__':
    logger.info('test')
    try:
        raise TimeoutError
    except Exception as e:
        logger.exception('error occured')
