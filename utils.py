""" utils tools"""
import os
import logging
import configparser

def load_config():
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))
    return config

# 创建一个 init logger，日志按文件大小切割日志，最多保存5个日志文件，日志级别为 DEBUG
def init_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(lineno)d - %(funcName)s - %(message)s')

    # 创建一个 FileHandler，用于输出到文件
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    if not os.path.exists(log_dir): # 如果日志文件夹不存在，则创建
        os.makedirs(log_dir)
    log_file = os.path.join(log_dir, 'midjourney.log')
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger
