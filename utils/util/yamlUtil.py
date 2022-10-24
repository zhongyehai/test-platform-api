# -*- coding: utf-8 -*-
import io

import yaml


def load(file):
    """ 读取yaml """
    with io.open(file, 'r', encoding='utf-8') as fr:
        data = yaml.load(fr, yaml.FullLoader)
    return data
