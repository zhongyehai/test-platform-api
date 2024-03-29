# -*- coding: utf-8 -*-
from datetime import datetime

from sqlalchemy import String, Integer, Text, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from apps.base_model import BaseModel


class WeeklyConfigModel(BaseModel):
    """ 周报配置表 """
    __tablename__ = "test_work_weekly_config"
    __table_args__ = {"comment": "周报配置表"}

    name: Mapped[str] = mapped_column(String(255), nullable=False, comment="名字")
    parent: Mapped[int] = mapped_column(
        Integer(), nullable=True, default=None, comment="上一级的id，有上一级则为项目，否则为产品")
    desc: Mapped[str] = mapped_column(Text(), comment="备注")

    @classmethod
    def get_data_dict(cls):
        """ 获取产品、项目数据
        {
            "id": {
                "total": 0,  # 产品下的项目数
                "name": "产品名",
                "project": {
                    "id": {
                        "total": 0,  # 项目下的版本数
                        "name": "项目名",
                        "version": {
                            "version1": {
                                "total": 0,  # 版本下的日报条数
                                "item": [],  # 版本下的日报数据
                            },
                            "version2": {
                                "total": 0,
                                "item": []
                            }
                        }
                    }
                }
            }
        }
        """
        container, product_list = {}, [data.to_dict() for data in WeeklyConfigModel.get_all()]

        # 获取所有产品
        for index, data in enumerate(product_list):
            if not data["parent"]:
                cls.build_project_product(container, data)
                cls.build_project_container(container[data["id"]], data)

        # 根据产品id获取所有项目
        for product_id, product_data in container.items():
            for index, data in enumerate(product_list):
                if data["parent"] == product_id:
                    cls.build_project_container(product_data, data)

        return container

    @classmethod
    def build_project_product(cls, container, data):
        """ 插入项目 """
        container[data["id"]] = {
            "total": 0,
            "name": data["name"],
            "project": {}
        }

    @classmethod
    def build_project_container(cls, container, data):
        """ 插入项目 """
        container["project"][data["id"]] = {
            "name": data["name"],
            "total": 0,
            "version": {}
        }
        container["total"] += 1


class WeeklyModel(BaseModel):
    """ 周报明细表 """
    __tablename__ = "test_work_weekly"
    __table_args__ = {"comment": "周报明细表"}

    product_id: Mapped[int] = mapped_column(Integer(), nullable=False, index=True, comment="产品id")
    project_id: Mapped[int] = mapped_column(Integer(), nullable=False, index=True, comment="项目id")
    version: Mapped[str] = mapped_column(String(255), comment="版本号")
    task_item: Mapped[list] = mapped_column(JSON, default=[], comment="任务明细和进度")
    start_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="开始时间")
    end_time: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now, comment="结束时间")
    desc: Mapped[str] = mapped_column(Text(), comment="备注")

    @property
    def str_start_time(self):
        return datetime.strftime(self.start_time, "%Y-%m-%d %H:%M:%S")

    @property
    def str_end_time(self):
        return datetime.strftime(self.end_time, "%Y-%m-%d %H:%M:%S")
