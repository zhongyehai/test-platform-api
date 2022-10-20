# -*- coding: utf-8 -*-
from app.baseModel import ConfigType, Config as _Config, db


class Config(_Config):

    @classmethod
    def get_new_env_list(cls, form):
        new_env_list = []
        new_env_keys, old_env_keys = cls.loads(form.value.data).keys(), cls.get_run_test_env().keys()
        # 获取需要进行同步的环境项
        for env in new_env_keys:
            if env not in old_env_keys:
                new_env_list.append(env)
        return new_env_list
