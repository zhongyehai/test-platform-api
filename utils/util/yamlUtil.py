# -*- coding: utf-8 -*-

import yaml


def load(file):
    """ 读取yaml """
    with open(file, 'r', encoding='utf-8') as fr:
        data = yaml.load(fr, yaml.FullLoader)
    return data
