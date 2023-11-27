# -*- coding: utf-8 -*-
import json
from datetime import datetime

from json import JSONEncoder

from utils.parse.parse import encode_object


class CustomJSONEncoder(JSONEncoder):
    """ 处理返回时间，直接使用 jsonify 会把时间处理成 GMT 时间"""

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()

        return super().default(obj)


class JsonUtil:
    """ 处理json事件，主要是在dumps时处理编码问题 """

    @classmethod
    def dump(cls, obj, fp, *args, **kwargs):
        """ json.dump """
        kwargs.setdefault("ensure_ascii", False)
        # kwargs.setdefault("indent", 4)
        return json.dump(obj, fp, *args, **kwargs)

    @classmethod
    def dumps(cls, obj, *args, **kwargs):
        """ json.dumps """
        kwargs.setdefault("ensure_ascii", False)
        # kwargs.setdefault("indent", 4)
        return json.dumps(obj, default=encode_object, cls=CustomJSONEncoder, *args, **kwargs)

    @classmethod
    def loads(cls, obj, *args, **kwargs):
        """ json.loads """
        return json.loads(obj, *args, **kwargs)

    @classmethod
    def load(cls, fp, *args, **kwargs):
        """ json.load """
        return json.load(fp, *args, **kwargs)

    @classmethod
    def field_to_json(cls, dict_data: dict, *args):
        """ 把字典中已存在的key的值转为json """
        for key in args:
            if key in dict_data:
                dict_data[key] = cls.dumps(dict_data[key])
        return dict_data


if __name__ == "__main__":
    d = {
        "a": {"a1": "b2"},
        "b": {"b1", "b2"}
    }
