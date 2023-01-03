# -*- coding: utf-8 -*-
from datetime import datetime

from app.baseModel import BaseModel, db


class WeeklyConfigModel(BaseModel):
    """ 周报配置表 """
    __tablename__ = "test_work_weekly_config"

    name = db.Column(db.Text(), comment="名字")
    parent = db.Column(db.Integer(), nullable=True, default=None, comment="上一级的id，有上一级则为项目，否则为产品")
    desc = db.Column(db.Text(), comment="备注")

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

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.name.data:
            filters.append(WeeklyConfigModel.name == form.name.data)
        if form.parent.data and form.parent.data != "all":
            data = None if form.parent.data == "null" else form.parent.data
            filters.append(WeeklyConfigModel.parent == data)
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.created_time.desc()
        )


class WeeklyModel(BaseModel):
    """ 周报明细表 """
    __tablename__ = "test_work_weekly"

    product_id = db.Column(db.String(5), comment="产品id")
    project_id = db.Column(db.String(5), comment="项目id")
    version = db.Column(db.String(255), comment="版本号")
    task_item = db.Column(db.Text(), comment="任务明细和进度")
    start_time = db.Column(db.DateTime, default=datetime.now, comment="开始时间")
    end_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment="结束时间")
    desc = db.Column(db.Text(), comment="备注")

    @property
    def str_start_time(self):
        return datetime.strftime(self.start_time, "%Y-%m-%d %H:%M:%S")

    @property
    def str_end_time(self):
        return datetime.strftime(self.end_time, "%Y-%m-%d %H:%M:%S")

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.product_id.data:
            filters.append(WeeklyModel.product_id == form.product_id.data)
        if form.project_id.data:
            filters.append(WeeklyModel.project_id == form.project_id.data)
        if form.version.data:
            filters.append(WeeklyModel.version == form.version.data)
        if form.task_item.data:
            filters.append(WeeklyModel.task_item.like(f"%{form.task_item.data}%"))
        if form.start_time.data:
            filters.append(WeeklyModel.start_time >= form.start_time.data)
        if form.end_time.data:
            filters.append(WeeklyModel.end_time <= form.end_time.data)
        if form.create_user.data:
            filters.append(WeeklyModel.create_user == int(form.create_user.data))
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.created_time.desc()
        )

