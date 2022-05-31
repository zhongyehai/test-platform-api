#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : yamlUtil.py
# @Software: PyCharm
import yaml


def load(file):
    """ 读取yaml """
    with open(file, 'r', encoding='utf-8') as fr:
        data = yaml.load(fr, yaml.FullLoader)
    return data
