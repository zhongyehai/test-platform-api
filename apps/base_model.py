# -*- coding: utf-8 -*-
import copy
import os
import time
from datetime import datetime
from contextlib import contextmanager
from typing import Union

import requests
from flask import g, request
from flask_sqlalchemy import SQLAlchemy as _SQLAlchemy
from flask_sqlalchemy.query import Query as BaseQuery
from sqlalchemy import MetaData, or_, text, Integer, String, DateTime, JSON, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from apps.enums import DataStatusEnum, ApiCaseSuiteTypeEnum, CaseStatusEnum, SendReportTypeEnum, ReceiveTypeEnum, \
    TriggerTypeEnum, ApiBodyTypeEnum
from config import _main_server_host, ui_suite_list, api_suite_list, _job_server_host
from utils.make_data.make_xmind import get_xmind_first_sheet_data
from utils.util.file_util import TEMP_FILE_ADDRESS
from utils.util.json_util import JsonUtil
from utils.parse.parse import parse_list_to_dict, update_dict_to_list, parse_dict_to_list


class SQLAlchemy(_SQLAlchemy):
    """ 自定义SQLAlchemy并继承SQLAlchemy """

    @contextmanager
    def auto_commit(self):
        """ 自定义上下文处理数据提交和异常回滚 """
        try:
            yield
            self.session.commit()
        except Exception as error:
            self.session.rollback()
            raise error
        finally:
            self.session.rollback()

    def execute_query_sql(self, sql, to_dict=True):
        """ 执行原生查询sql，并返回字典 """
        res = self.session.execute(text(sql)).fetchall()
        if to_dict:
            return dict(res) if res else {}
        else:
            return res


class Query(BaseQuery):
    """ 重写query方法，使其默认加上status=0 """

    def filter_by(self, **kwargs):
        """ 如果传过来的参数中不含is_delete，则默认加一个is_delete参数，状态为0 查询有效的数据"""
        # kwargs.setdefault("is_delete", 0)
        return super(Query, self).filter_by(**kwargs)

    def update(self, values, synchronize_session="evaluate", update_args=None):
        try:
            values["update_user"] = g.user_id  # 自动加上更新者id, 如果是执行测试，不在上下文，所以拿不到
        except:
            pass
        return super(Query, self).update(values, synchronize_session=synchronize_session, update_args=update_args)


# 由于数据库迁移的时候，不兼容约束关系的迁移，下面是百度出的解决方案
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
db = SQLAlchemy(
    query_class=Query,  # 指定使用修改过后的Qeury
    metadata=MetaData(naming_convention=naming_convention)
)


class BaseModel(db.Model, JsonUtil):
    """ 基类模型 """
    __abstract__ = True
    db = db  # 方便直接使用，不用每次都导入

    id: Mapped[int] = mapped_column(Integer(), primary_key=True, comment="主键，自增")
    create_time: Mapped[datetime] = mapped_column(DateTime, nullable=True, default=datetime.now, comment="创建时间")
    update_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=True, default=datetime.now, onupdate=datetime.now, comment="修改时间")
    create_user: Mapped[int] = mapped_column(Integer(), nullable=True, default=None, comment="创建数据的用户id")
    update_user: Mapped[int] = mapped_column(Integer(), nullable=True, default=None, comment="修改数据的用户id")

    @classmethod
    def get_table_column_name_list(cls):
        """ 获取当前表的所有字段 """
        return [column.name for column in cls.__table__.columns]

    @classmethod
    def get_id_list(cls, **kwargs):
        return [data[0] for data in cls.query.with_entities(cls.id).filter_by(**kwargs).all()]

    @classmethod
    def format_create_data(cls, data_dict):
        if "id" in data_dict:
            data_dict.pop("id")

        try:  # 执行初始化脚本、执行测试时，不在上下文中，不能使用g对象
            if hasattr(g, 'user_id') and g.user_id:
                current_user = g.user_id  # 真实用户
            else:
                current_user = g.common_user_id  # 预设的用户id
        except:
            current_user = None
        data_dict["create_user"] = data_dict["update_user"] = current_user
        data_dict["create_time"] = data_dict["update_time"] = None

    @classmethod
    def model_create(cls, data_dict: dict):
        """ 创建数据 """
        column_name_list = cls.get_table_column_name_list()
        if "num" in column_name_list:  # 如果有num字段，自动获取最大的num，并赋值
            data_dict["num"] = cls.get_insert_num()

        cls.format_create_data(data_dict)
        insert_dict = {key: value for key, value in data_dict.items() if key in column_name_list}

        with db.auto_commit():
            db.session.add(cls(**insert_dict))

    @classmethod
    def model_create_and_get(cls, data_dict: dict):
        """ 创建并返回数据，会多一次查询 """
        cls.model_create(data_dict)
        query_filter = {}
        if "name" in data_dict:
            query_filter["name"] = data_dict["name"]
        if "sso_user_id" in data_dict:
            query_filter["sso_user_id"] = data_dict["sso_user_id"]
        if "module_id" in data_dict:
            query_filter["module_id"] = data_dict["module_id"]
        if "parent" in data_dict:
            query_filter["parent"] = data_dict["parent"]
        if "project_id" in data_dict:
            query_filter["project_id"] = data_dict["project_id"]
        if "batch_id" in data_dict:
            query_filter["batch_id"] = data_dict["batch_id"]
        if "report_id" in data_dict:
            query_filter["report_id"] = data_dict["report_id"]
        if "report_case_id" in data_dict:
            query_filter["report_case_id"] = data_dict["report_case_id"]
        if "url" in data_dict:
            query_filter["url"] = data_dict["url"]
        if "method" in data_dict:
            query_filter["method"] = data_dict["method"]
        if "project" in data_dict:
            query_filter["project"] = data_dict["project"]
        return cls.query.filter_by(**query_filter).order_by(cls.id.desc()).first()

    @classmethod
    def model_batch_create(cls, data_list: list):
        """ 批量插入 """
        with db.auto_commit():
            obj_list = []
            for data_dict in data_list:
                cls.format_create_data(data_dict)
                obj_list.append(cls(**data_dict))
            db.session.add_all(obj_list)

    def model_update(self, data_dict: dict):
        """ 更新数据 """
        if "num" in data_dict: data_dict.pop("num")
        if "id" in data_dict: data_dict.pop("id")
        try:
            data_dict["update_user"] = g.user_id if hasattr(g, "user_id") else None
        except:
            pass
        with db.auto_commit():
            for key, value in data_dict.items():
                if hasattr(self, key):
                    setattr(self, key, value)

    @classmethod
    def batch_update(cls, data_list):
        """ 批量更新 """
        for data in data_list:
            if "id" not in data:
                raise "batch_update 方法必须有id字段"
            data["update_user"] = g.user_id if hasattr(g, "user_id") else None
        cls.db.session.bulk_update_mappings(cls, data_list)

    def delete(self):
        """ 删除单条数据 """
        with db.auto_commit():
            db.session.delete(self)

    @classmethod
    def delete_by_id(cls, data_id):
        """ 根据id删除数据 """
        if isinstance(data_id, int):
            cls.query.filter(cls.id == data_id).delete()
        elif isinstance(data_id, list):
            cls.query.filter(cls.id.in_(data_id)).delete()

    @classmethod
    def get_simple_filed_list(cls):
        return [cls.id, cls.name]

    def enable(self):
        """ 启用数据 """
        with db.auto_commit():
            self.status = DataStatusEnum.ENABLE.value

    def disable(self):
        """ 禁用数据 """
        with db.auto_commit():
            self.status = DataStatusEnum.DISABLE.value

    def is_enable(self):
        """ 判断数据是否为启用状态 """
        return self.status == DataStatusEnum.ENABLE.value

    def is_disable(self):
        """ 判断数据是否为禁用状态 """
        return self.status == DataStatusEnum.DISABLE.value

    @classmethod
    def format_with_entities_query_list(cls, query_list):
        """ 格式化查询集 [(1,), (2,)] -> [1, 2] """
        return [res[0] for res in query_list]

    def current_is_create_user(self):
        """ 判断当前传进来的id为数据创建者 """
        return self.create_user == g.user_id

    def copy(self):
        """ 复制本身对象 """
        data = self.to_dict()
        data["name"] = data.get("name") + "_copy" if data.get("name") else "_copy"
        if data.get("status"): data["status"] = 0
        return self.__class__.model_create(data)

    @classmethod
    def get_from_path(cls, data_id):
        """ 获取模块/用例集的归属 """
        from_name = []

        def get_from(current_data_id):
            parent_name, parent_parent = cls.query.with_entities(
                cls.name, cls.parent).filter(cls.id == current_data_id).first()  # (qwe, 1)
            from_name.insert(0, parent_name)

            if parent_parent:
                get_from(parent_parent)

        get_from(data_id)
        return '/'.join(from_name)

    @classmethod
    def change_sort(cls, id_list, page_num, page_size):
        """ 批量修改排序 """
        id_list_query = cls.query.with_entities(cls.id).filter(cls.id.in_(id_list)).all()
        db_id_list, update_data_list = [id_query[0] for id_query in id_list_query], []
        if id_list:
            for index, data_id in enumerate(id_list):
                if data_id in db_id_list:
                    update_data_list.append({"id": data_id, "num": (page_num - 1) * page_size + index})
            cls.db.session.bulk_update_mappings(cls, update_data_list)

    @classmethod
    def get_max_num(cls, **kwargs):
        """ 返回 model 表中**kwargs筛选条件下的已存在编号num的最大值 """
        max_num_data = cls.query.filter_by(**kwargs).order_by(cls.num.desc()).first()
        return max_num_data.num if max_num_data and max_num_data.num else 0

    @classmethod
    def get_insert_num(cls, **kwargs):
        """ 返回 model 表中**kwargs筛选条件下的已存在编号num的最大值 + 1 """
        return cls.get_max_num(**kwargs) + 1

    @classmethod
    def get_current_business_list(cls):
        """ 管理员权限 """
        return g.business_list

    @classmethod
    def get_current_api_permissions(cls):
        """ 管理员权限 """
        return g.api_permissions

    @classmethod
    def is_admin(cls):
        """ 管理员权限 """
        return 'admin' in cls.get_current_api_permissions()

    @classmethod
    def is_not_admin(cls):
        """ 非管理员权限 """
        return not cls.is_admin()

    @classmethod
    def get_first(cls, **kwargs):
        """ 获取第一条数据 """
        return cls.query.filter_by(**kwargs).first()

    @classmethod
    def get_all(cls, **kwargs):
        """ 获取全部数据 """
        return cls.query.filter_by(**kwargs).all()

    def to_dict(self, pop_list: list = [], filter_list: list = []):
        """ 自定义序列化器
        pop_list: 序列化时忽略的字段
        filter_list: 仅要序列化的字段
        当 pop_list 与 filter_list 同时包含同一个字段时，以 filter_list 为准
        """
        if pop_list or filter_list:
            dict_data = {}
            for column_name in self.get_table_column_name_list():
                if filter_list:
                    if column_name in filter_list:
                        dict_data[column_name] = getattr(self, column_name)
                else:
                    if column_name not in pop_list:
                        dict_data[column_name] = getattr(self, column_name)  # self.get_column_data(column_name)
            return dict_data
        return {column.name: getattr(self, column.name, None) for column in self.__table__.columns}

    @classmethod
    def make_pagination(cls, form, get_filed: list = [], order_by=None, **kwargs):
        """ 执行分页查询 """
        # 排序
        if order_by is None:
            # 有num就用num升序，否则用id降序
            order_by = cls.num.asc() if "num" in cls.get_table_column_name_list() else cls.id.desc()

        get_filed = get_filed or cls.__table__.columns  # 如果没传指定字段，则默认查全部字段
        col_name_list = [column.name for column in get_filed]  # 字段名

        if form.page_num and form.page_size:
            query_obj = cls.db.session.query(*get_filed).filter(*form.get_query_filter(**kwargs)).order_by(order_by)
            query_result = query_obj.paginate(page=form.page_num, per_page=form.page_size, error_out=False)
            return {
                "total": query_result.total,
                "data": [dict(zip(col_name_list, item)) for item in query_result.items]
            }

        all_data = cls.db.session.query(*get_filed).filter(*form.get_query_filter(**kwargs)).order_by(order_by).all()
        return {
            "total": len(all_data),
            "data": [dict(zip(col_name_list, item)) for item in all_data]
        }


class StatusFiled(BaseModel):
    __abstract__ = True
    status: Mapped[int] = mapped_column(
        Integer(), nullable=True, default=DataStatusEnum.ENABLE.value, comment="数据状态，0/1")


class NumFiled(BaseModel):
    __abstract__ = True
    num: Mapped[int] = mapped_column(Integer(), default=0, nullable=True, comment="数据序号")


class ScriptListFiled(BaseModel):
    __abstract__ = True
    script_list: Mapped[list] = mapped_column(JSON, nullable=True, default=[], comment="引用的脚本文件")


class VariablesFiled(BaseModel):
    __abstract__ = True
    variables: Mapped[list] = mapped_column(
        JSON, default=[{"key": None, "value": None, "remark": None, "data_type": None}], comment="公共参数")


class HeadersFiled(BaseModel):
    __abstract__ = True
    headers: Mapped[list] = mapped_column(
        JSON, default=[{"key": None, "remark": None, "value": None}], comment="头部信息")


class ParamsFiled(BaseModel):
    __abstract__ = True
    params: Mapped[list] = mapped_column(JSON, default=[{"key": None, "value": None}], comment="url参数")


class BodyTypeFiled(BaseModel):
    __abstract__ = True
    body_type: Mapped[ApiBodyTypeEnum] = mapped_column(
        default=ApiBodyTypeEnum.json.value, comment="请求体数据类型，json/form/text/urlencoded")


class DataFormFiled(BaseModel):
    __abstract__ = True
    data_form: Mapped[list] = mapped_column(
        JSON, default=[{"data_type": None, "key": None, "remark": None, "value": None}], comment="form-data参数")


class DataUrlencodedFiled(BaseModel):
    __abstract__ = True
    data_urlencoded: Mapped[dict] = mapped_column(JSON, default={}, comment="form_urlencoded参数")


class DataJsonFiled(BaseModel):
    __abstract__ = True
    data_json: Mapped[dict] = mapped_column(JSON, default={}, comment="json参数")


class ExtractsFiled(BaseModel):
    __abstract__ = True
    extracts: Mapped[list] = mapped_column(
        JSON,
        comment="提取信息",
        default=[{
            "status": 0, "key": None, "data_source": None, "value": None, "remark": None, "update_to_header": None
        }])


class ValidatesFiled(BaseModel):
    __abstract__ = True
    validates: Mapped[list] = mapped_column(
        JSON, comment="断言信息",
        default=[{
            "status": 0,
            "key": None,
            "value": None,
            "remark": None,
            "data_type": None,
            "data_source": None,
            "validate_method": None,
            "validate_type": "data"
        }])


class SkipIfFiled(BaseModel):
    __abstract__ = True
    skip_if: Mapped[list] = mapped_column(
        JSON, comment="是否跳过的判断条件",
        default=[{
            "expect": None,
            "data_type": None,
            "skip_type": None,
            "comparator": None,
            "data_source": None,
            "check_value": None,
        }])


class UpFuncFiled(BaseModel):
    __abstract__ = True
    up_func: Mapped[list] = mapped_column(JSON, default=[], comment="执行前置的函数")


class DownFuncFiled(BaseModel):
    __abstract__ = True
    down_func: Mapped[list] = mapped_column(JSON, default=[], comment="执行后置的函数")


class BaseProject(ScriptListFiled, NumFiled):
    """ 服务基类表 """
    __abstract__ = True

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, comment="服务名称")
    manager: Mapped[int] = mapped_column(Integer(), nullable=False, comment="服务/项目/app管理员")
    business_id: Mapped[int] = mapped_column(Integer(), nullable=False, index=True, comment="所属业务线")

    @classmethod
    def add_project(cls, form, project_env_model, run_env_model, suite_model):
        project = cls.model_create_and_get(form.model_dump())
        project_env_model.create_env(cls, run_env_model, project.id)  # 新增服务的时候，一并把环境设置齐全
        suite_model.create_suite_by_project(project.id)  # 新增服务的时候，一并把用例集设置齐全

    @classmethod
    def clear_env(cls, project_env_model):
        project_id_list = cls.get_id_list()
        project_env_model.query.filter(project_env_model.project_id.notin_(project_id_list)).delete()

    @classmethod
    def is_can_delete(cls, project_id):
        """ 判断是否有权限删除（或）：1.当前用户为系统管理员/2.当前用户为当前数据的创建者/3.当前用户为当前服务的负责人 """
        if cls.is_not_admin():
            return cls.query.with_entities(cls.id).filter(
                cls.id == project_id, or_(cls.manager == g.user_id, cls.create_user == g.user_id)).first()
        return True


class BaseProjectEnv(VariablesFiled):
    """ 服务环境基类表 """
    __abstract__ = True

    host: Mapped[str] = mapped_column(String(255), default=_main_server_host, comment="服务地址")
    env_id: Mapped[int] = mapped_column(Integer(), index=True, nullable=False, comment="对应环境id")
    project_id: Mapped[int] = mapped_column(Integer(), index=True, nullable=False, comment="所属的服务id")

    @classmethod
    def create_env(cls, project_env_model=None, run_env_model=None, project_id=None, env_list=None):
        """
        当环境配置更新时，自动给项目/环境增加环境信息
        如果指定了项目id，则只更新该项目的id，否则更新所有项目的id
        如果已有当前项目的信息，则用该信息创建到指定的环境
        """
        if not project_id and not env_list:
            return

        env_id_list = env_list or run_env_model.get_id_list()

        if project_id:
            current_project_env = cls.get_first(project_id=project_id)
            data = current_project_env.to_dict() if current_project_env else {"project_id": project_id}

            new_env_data_list = []
            for env_id in env_id_list:
                data["env_id"] = env_id
                new_env_data_list.append(copy.deepcopy(data))
            cls.model_batch_create(new_env_data_list)

        else:
            for project_query_id in project_env_model.get_id_list():
                cls.create_env(project_env_model, run_env_model, project_query_id, env_id_list)

    @classmethod
    def change_env(cls, form):
        form.project_env.model_update(form.model_dump())
        # 更新环境的时候，把环境的头部信息、变量的key一并同步到其他环境
        env_id_list_query = cls.db.session.query(cls.env_id).filter(
            cls.project_id == form.project_id, cls.env_id != form.project_env.env_id).all()
        cls.synchronization(form.project_env, [int(env_id[0]) for env_id in env_id_list_query])

    @classmethod
    def synchronization(cls, from_env, to_env_id_list: list):
        """ 把当前环境同步到其他环境
        from_env: 从哪个环境
        to_env_list: 同步到哪些环境
        """
        is_update_headers = hasattr(cls, "headers")
        filed_list = ["variables", "headers"] if is_update_headers else ["variables"]

        # 同步数据来源解析
        from_env_dict = {}
        for filed in filed_list:
            from_env_dict[filed] = parse_list_to_dict(getattr(from_env, filed))

        # 同步至指定环境
        new_env_list = []
        to_env_list = cls.db.session.query(cls.id, *[getattr(cls, filed) for filed in filed_list]).filter(
            cls.project_id == from_env.project_id, cls.env_id.in_(to_env_id_list)).all()

        for to_env_data in to_env_list:
            new_env_data = {
                "id": to_env_data[0],
                "variables": update_dict_to_list(from_env_dict["variables"], to_env_data[1])
            }
            if is_update_headers:
                new_env_data["headers"] = update_dict_to_list(from_env_dict["headers"], to_env_data[2])
            new_env_list.append(new_env_data)
        cls.batch_update(new_env_list)

    @classmethod
    def add_env(cls, env_id, project_model):
        """ 新增运行环境时，批量给服务/项目/APP加上 """
        data_list = []
        for project_id in project_model.get_id_list():
            if not cls.db.session.query(cls.id).filter_by(project_id=project_id, env_id=env_id).first():
                data_list.append({"env_id": env_id, "project_id": project_id})
        cls.model_batch_create(data_list)


class BaseModule(NumFiled):
    """ 模块基类表 """
    __abstract__ = True

    name: Mapped[str] = mapped_column(String(255), nullable=False, comment="模块名")
    parent: Mapped[int] = mapped_column(Integer(), nullable=True, default=None, comment="上一级模块id")
    project_id: Mapped[int] = mapped_column(Integer(), index=False, comment="所属的服务id")

    @classmethod
    def add_module(cls, form_dict):
        new_model = cls.model_create_and_get(form_dict)
        setattr(new_model, "children", [])
        return new_model


class BaseApi(StatusFiled, NumFiled):
    """ 页面表 """
    __abstract__ = True

    name: Mapped[str] = mapped_column(String(255), nullable=False, comment="名称")
    desc: Mapped[str] = mapped_column(Text(), default="", nullable=True, comment="描述")
    project_id: Mapped[int] = mapped_column(Integer(), index=True, nullable=False, comment="所属的服务id")
    module_id: Mapped[int] = mapped_column(Integer(), index=True, nullable=False, comment="所属的模块id")


class BaseElement(BaseApi):
    """ 页面元素表 """
    __abstract__ = True

    by: Mapped[str] = mapped_column(String(255), nullable=False, comment="定位方式")
    element: Mapped[str] = mapped_column(Text(), default="", nullable=True, comment="元素值")
    wait_time_out: Mapped[int] = mapped_column(
        Integer(), default=3, nullable=True, comment="等待元素出现的时间，默认3秒")
    page_id: Mapped[int] = mapped_column(Integer(), nullable=False, comment="所属的页面id")

    @classmethod
    def copy_element(cls, old_page_id, new_page_id):
        element_list = []
        for index, element in enumerate(cls.get_all(page_id=old_page_id)):
            element_dict = element.to_dict()
            element_dict["page_id"] = new_page_id
            element_list.append(element_dict)
        cls.model_batch_create(element_list)


class BaseCaseSuite(NumFiled):
    """ 用例集基类表 """
    __abstract__ = True

    name: Mapped[str] = mapped_column(String(255), nullable=False, comment="用例集名称")
    suite_type: Mapped[ApiCaseSuiteTypeEnum] = mapped_column(
        default=ApiCaseSuiteTypeEnum.base.value,
        comment="用例集类型，base: 基础用例集，api: 单接口用例集，process: 流程用例集，make_data: 造数据用例集")
    parent: Mapped[int] = mapped_column(Integer(), nullable=True, default=None, comment="上一级用例集id")
    project_id: Mapped[int] = mapped_column(Integer(), nullable=False, index=True, comment="所属的服务id")

    @classmethod
    def upload_case_suite(cls, project_id, file_obj, case_model):
        file_path = os.path.join(TEMP_FILE_ADDRESS, file_obj.filename)
        file_obj.save(file_path)
        xmind_data = get_xmind_first_sheet_data(file_path)
        return cls.upload(project_id, xmind_data, case_model)

    @classmethod
    def upload(cls, project_id, data_tree, case_model):
        """ 上传用例集 """
        suite_pass, suite_fail, case_pass, case_fail = [], [], [], []
        topic_list = data_tree.get("topic", {}).get("topics", [])

        def insert_data(topic_data, parent=None):
            title = topic_data.get("title", "")

            if title.startswith('tc'):  # 用例
                case_name = title.split(':', 1)[1] if ':' in title else title.split('：', 1)[1]  # 支持中英文的冒号
                case_id = case_model.db.session.query(case_model.id).filter_by(name=case_name, suite_id=parent).first()
                if case_id is None:  # 没有才导入
                    desc = topic_data.get("topics", [{}])[0].get("title", case_name)
                    try:
                        case_model.model_create({"name": case_name, "desc": desc, "suite_id": parent})
                        case_pass.append(case_name)
                    except:
                        case_fail.append(case_name)
            else:  # 用例集
                suite_id_query = cls.db.session.query(
                    cls.id).filter_by(parent=parent, name=title, project_id=project_id).first()
                if suite_id_query is None:  # 有就插入下级
                    try:
                        cls.model_create({
                            "name": title, "project_id": project_id, "parent": parent,
                            "suite_type": ApiCaseSuiteTypeEnum.process.value
                        })
                        suite_id_query = cls.db.session.query(
                            cls.id).filter_by(parent=parent, name=title, project_id=project_id).first()
                        suite_pass.append(title)
                    except:
                        suite_fail.append(title)
                        return

                for child in topic_data.get("topics", []):
                    insert_data(child, suite_id_query[0])

        for topic_data in topic_list:
            insert_data(topic_data)

        return {
            "suite": {
                "pass": {
                    "total": len(suite_pass),
                    "data": suite_pass
                },
                "fail": {
                    "total": len(suite_fail),
                    "data": suite_fail
                },
            },
            "case": {
                "pass": {
                    "total": len(case_pass),
                    "data": case_pass
                },
                "fail": {
                    "total": len(case_fail),
                    "data": case_fail
                },
            }
        }

    def update_children_suite_type(self):
        """ 递归更新子用例集的类型 """
        model = self.__class__

        def change_child_suite_type(parent_id):
            child_query_list = model.query.with_entities(model.id).filter_by(parent=parent_id).all()
            child_id_list = [query_list[0] for query_list in child_query_list]
            if child_id_list:
                model.query.filter(model.id.in_(child_id_list)).update({"suite_type": self.suite_type})
                for child_id in child_id_list:
                    change_child_suite_type(child_id)

        change_child_suite_type(self.id)

    @classmethod
    def create_suite_by_project(cls, project_id):
        """ 根据项目id，创建用例集 """
        suite_type_list = api_suite_list if "Api" in cls.__name__ else ui_suite_list
        data_list = []
        for index, suite_type in enumerate(suite_type_list):
            data_list.append({
                "num": index, "project_id": project_id, "name": suite_type["value"], "suite_type": suite_type["key"]
            })
        cls.model_batch_create(data_list)

    def get_run_case_id(self, case_model, business_id=None):
        """ 获取用例集下，状态为要运行的用例id """
        query = {"suite_id": self.id, "status": 1}
        if business_id:
            query["business_id"] = business_id
        case_id_list = [
            query_res[0] for query_res in
            case_model.query.with_entities(case_model.id).filter_by(**query).order_by(case_model.num.asc()).all()
        ]
        return case_id_list

    @classmethod
    def get_case_id(cls, case_model, project_id: int, suite_id: list, case_id: list):
        """
        获取要执行的用例的id
            1、即没选择用例，也没选择用例集
            2、只选择了用例
            3、只选了用例集
            4、选定了用例和用例集
        """
        # 1、只选择了用例，则直接返回用例
        if len(case_id) != 0 and len(suite_id) == 0:
            return case_id

        # 2、没有选择用例集和用例，则视为选择了所有用例集
        elif len(suite_id) == 0 and len(case_id) == 0:
            suite_id_query = cls.db.session.query(cls.id).filter(
                cls.project_id == project_id, cls.suite_type.in_(['api', 'process'])).order_by(cls.num.asc()).all()
            suite_id = [id_query[0] for id_query in suite_id_query]

        # 解析已选中的用例集，并继承已选中的用例列表，再根据用例id去重
        case_id_query = case_model.db.session.query(case_model.id).filter(
            case_model.suite_id.in_(suite_id), case_model.status == CaseStatusEnum.DEBUG_PASS_AND_RUN.value
        ).order_by(case_model.num.asc()).all()
        case_id_list = [id_query[0] for id_query in case_id_query]

        case_id_list.extend(case_id)
        return list(set(case_id_list))


class BaseCase(ScriptListFiled, VariablesFiled, SkipIfFiled, NumFiled):
    """ 用例基类表 """

    __abstract__ = True

    name: Mapped[str] = mapped_column(String(255), nullable=False, comment="用例名称")
    desc: Mapped[str] = mapped_column(Text(), nullable=False, comment="用例描述")
    status: Mapped[int] = mapped_column(
        Integer(), default=CaseStatusEnum.NOT_DEBUG_AND_NOT_RUN.value,
        comment="用例调试状态，0未调试-不执行，1调试通过-要执行，2调试通过-不执行，3调试不通过-不执行，默认未调试-不执行")
    run_times: Mapped[int] = mapped_column(Integer(), default=1, comment="执行次数，默认执行1次")
    output: Mapped[list] = mapped_column(JSON, default=[], comment="用例出参（步骤提取的数据）")
    suite_id: Mapped[int] = mapped_column(Integer(), nullable=False, index=True, comment="所属的用例集id")

    @classmethod
    def batch_delete_step(cls, step_model):
        """ 清理测试用例不存在的步骤 """
        case_id_list = cls.get_id_list()
        step_model.query.filter(step_model.case_id.notin_(case_id_list)).delete()

    def copy_case(self, step_model):
        old_case = self.to_dict()
        old_case["name"], old_case["status"] = old_case["name"] + "_copy", CaseStatusEnum.NOT_DEBUG_AND_NOT_RUN.value
        new_case = self.model_create_and_get(old_case)

        # 复制步骤
        new_step_list = []
        old_step_list = step_model.query.filter_by(case_id=self.id).order_by(step_model.num.asc()).all()
        for index, old_step in enumerate(old_step_list):
            new_step = old_step.to_dict()
            new_step["num"], new_step["case_id"] = index, new_case.id
            new_step_list.append(new_step)
        step_model.model_batch_create(new_step_list)
        return {"case": new_case.to_dict()}

    @classmethod
    def copy_case_all_step_to_current_case(cls, form, step_model):
        """ 复制指定用例的步骤到当前用例下 """
        step_list, num_start = [], step_model.get_max_num(case_id=form.to_case)
        from_step_list = step_model.query.filter_by(case_id=form.from_case).order_by(step_model.num.asc()).all()

        for index, from_step in enumerate(from_step_list):
            step_dict = from_step.to_dict()
            step_dict["case_id"], step_dict["num"] = form.to_case, num_start + index + 1
            step_model.model_create(step_dict)
            step_list.append(step_dict)
        cls.merge_output(form.to_case, step_list)  # 合并出参

    @classmethod
    def merge_variables(cls, from_case_id, to_case_id):
        """ 当用例引用的时候，自动将被引用用例的自定义变量合并到发起引用的用例上 """
        if from_case_id:
            db_from_case_variables = cls.db.session.query(cls.variables).filter(cls.id == from_case_id).first()
            db_to_case_variables = cls.db.session.query(cls.variables).filter(cls.id == to_case_id).first()
            from_case_variables = {variable["key"]: variable for variable in db_from_case_variables[0]}
            to_case_variables = {variable["key"]: variable for variable in db_to_case_variables[0]}

            for from_variable_key, from_case_variable in from_case_variables.items():
                to_case_variables.setdefault(from_variable_key, from_case_variable)

            cls.query.filter(
                cls.id == to_case_id).update({"variables": [value for key, value in to_case_variables.items() if key]})

    @classmethod
    def merge_output(cls, case_id, source_list=[]):
        """ 把步骤的数据提取加到用例的output字段下 """
        output_dict = {}
        for source in source_list:
            if isinstance(source, int):  # 用例id
                source = cls.get_first(id=source).to_dict()
            elif isinstance(source, dict) is False:  # 对象（步骤或用例）
                source = source.to_dict()

            if source.get("quote_case") or source.get("suite_id"):  # 更新源是用例（引用用例和复制用例下的所有步骤）
                source_case = cls.get_first(id=source["id"] if source.get("suite_id") else source["quote_case"])
                source_case_output = parse_list_to_dict(source_case.output)
                output_dict.update(source_case_output)
            else:  # 更新源为步骤（添加步骤和复制其他用例的步骤）
                output_dict.update(parse_list_to_dict(source["extracts"]))

        to_case = cls.get_first(id=case_id)
        output_dict.update(parse_list_to_dict(to_case.output))
        to_case.model_update({"output": parse_dict_to_list(output_dict, False)})

    def get_quote_case_from(self, project_model, suite_model):
        """ 获取用例的归属 """
        suite_path_name = suite_model.get_from_path(self.suite_id)
        project_name = suite_model.db.session.query(project_model.name).filter(
            suite_model.id == self.suite_id, suite_model.project_id == project_model.id).first()  # ('测试平台',)
        return f'{project_name[0]}/{suite_path_name}/{self.name}'


class BaseStep(StatusFiled, SkipIfFiled, UpFuncFiled, DownFuncFiled, NumFiled):
    """ 测试步骤基类表 """

    __abstract__ = True

    run_times: Mapped[int] = mapped_column(Integer(), default=1, comment="执行次数，默认执行1次")
    name = db.Column(db.String(255), nullable=False, comment="步骤名称")
    skip_on_fail: Mapped[int] = mapped_column(
        Integer(), default=1, nullable=True,
        comment="当用例有失败的步骤时，是否跳过此步骤，1跳过，0不跳过，默认跳过")
    data_driver: Mapped[list] = mapped_column(JSON, default=[], comment="数据驱动，若此字段有值，则走数据驱动的解析")
    quote_case: Mapped[int] = mapped_column(Integer(), nullable=True, default=None, comment="引用用例的id")
    case_id: Mapped[int] = mapped_column(Integer(), nullable=False, index=True, comment="步骤所在的用例的id")

    @classmethod
    def copy_step(cls, step_id, case_id, case_model):
        """ 复制步骤，如果没有指定用例id，则默认复制到当前用例下 """
        old = cls.get_first(id=step_id).to_dict()
        old["name"] = f'{old["name"]}_copy'
        if case_id:
            old["case_id"] = case_id
        step = cls.model_create_and_get(old)
        case_model.merge_output(step.case_id, [step])  # 合并出参
        return step

    @classmethod
    def add_step(cls, data_dict, case_model):
        """ 新增步骤 """
        step = cls.model_create_and_get(data_dict)
        case_model.merge_variables(step.quote_case, step.case_id)
        case_model.merge_output(step.case_id, [int(step.quote_case) if step.quote_case else step])  # 合并出参
        return step

    @classmethod
    def set_has_step_for_step(cls, step_list, case_model):
        """ 增加步骤下是否有步骤的标识（是否为引用用例，为引用用例的话，该用例下是否有步骤）"""
        data_list = []
        for step in step_list:
            if isinstance(step, dict) is False:
                step = step.to_dict()

            if step["quote_case"]:  # 若果是引用用例，把对应用例的入参出参、用例来源一起返回
                case_data = case_model.get_first(id=step["quote_case"])
                if case_data:  # 如果手动从数据库删过数据，可能没有
                    step["children"] = []
                    case = case_data.to_dict()
                    step["desc"] = case["desc"]
                    step["skip_if"] = case.get("skip_if")
                    step["variables"] = case.get("variables")
                    step["output"] = case.get("output")

            data_list.append(step)
        return data_list

    @classmethod
    def set_has_step_for_case(cls, case_list):
        """ 增加是否有步骤的标识 """
        data_list = []
        for case in case_list:
            if isinstance(case, dict) is False:
                case = case.to_dict()
            case["hasStep"] = cls.get_first(case_id=case["id"]) is not None
            case["children"] = []
            data_list.append(case)
        return data_list


class BaseTask(StatusFiled, NumFiled):
    """ 定时任务基类表 """
    __abstract__ = True

    name: Mapped[str] = mapped_column(String(255), nullable=False, comment="任务名称")
    env_list: Mapped[list] = mapped_column(JSON, default=[], comment="运行环境")
    case_ids: Mapped[list] = mapped_column(JSON, default=[], comment="用例id")
    task_type: Mapped[str] = mapped_column(String(255), default="cron", comment="定时类型")
    cron: Mapped[str] = mapped_column(String(255), nullable=False, comment="cron表达式")
    is_send: Mapped[SendReportTypeEnum] = mapped_column(
        default=SendReportTypeEnum.not_send, comment="是否发送通知，1.不发送、2.始终发送、3.仅用例不通过时发送")
    merge_notify: Mapped[int] = mapped_column(
        Integer(), default=0, nullable=True, comment="多个环境时，是否合并通知（只通知一次），默认不合并，0不合并、1合并")
    receive_type: Mapped[ReceiveTypeEnum] = mapped_column(
        default=ReceiveTypeEnum.ding_ding, nullable=True, comment="接收测试报告类型: ding_ding、we_chat、email")
    webhook_list: Mapped[list] = mapped_column(JSON, default=[], comment="机器人地址")
    email_server: Mapped[str] = mapped_column(String(255), nullable=True, comment="发件邮箱服务器")
    email_from: Mapped[str] = mapped_column(String(255), nullable=True, comment="发件人邮箱")
    email_pwd: Mapped[str] = mapped_column(String(255), nullable=True, comment="发件人邮箱密码")
    email_to: Mapped[list] = mapped_column(JSON, default=[], comment="收件人邮箱")
    skip_holiday: Mapped[int] = mapped_column(Integer(), default=1, nullable=True, comment="是否跳过节假日、调休日")
    is_async: Mapped[int] = mapped_column(Integer(), default=1, comment="任务的运行机制，0：串行，1：并行，默认0")
    suite_ids: Mapped[list] = mapped_column(JSON, default=[], comment="用例集id")
    call_back: Mapped[list] = mapped_column(JSON, default=[], comment="回调给流水线")
    project_id: Mapped[int] = mapped_column(Integer(), nullable=False, index=True, comment="所属的服务id")
    conf: Mapped[dict] = mapped_column(
        JSON, nullable=True,
        default={"browser": "chrome", "server_id": "", "phone_id": "", "no_reset": ""},
        comment="运行配置，ui存浏览器，app存运行服务器、手机、是否重置APP")

    def enable_task(self):
        try:
            task_class_name = self.__class__.__name__
            task_type = "api" if "Api" in task_class_name else "app" if "App" in task_class_name else "ui"
            task = self.to_dict()
            task.pop("create_time")
            task.pop("update_time")
            res = requests.post(
                url=_job_server_host,
                headers=request.headers,
                json={"task_id": g.user_id, "task": task, "type": task_type}
            ).json()
            if res.get("status") == 200:
                self.enable()
                return {"status": 1, "data": res}
            else:
                return {"status": 0, "data": res}
        except Exception as error:
            return {"status": 0, "data": error}

    def disable_task(self):
        try:
            task_class_name = self.__class__.__name__
            task_type = "api" if "Api" in task_class_name else "app" if "App" in task_class_name else "ui"
            res = requests.delete(
                url=_job_server_host,
                headers=request.headers,
                json={"task_id": self.id, "type": task_type}
            ).json()
            if res.get("status") == 200:
                self.disable()
                return {"status": 1, "data": res}
            else:
                return {"status": 0, "data": res}
        except Exception as error:
            return {"status": 0, "data": error}

    def update_task_to_memory(self):
        """ 更新任务时，同步更新内存中的任务 """
        if getattr(self, 'update_to_memory') is True:
            try:
                self.disable_task()
                self.enable_task()
            except Exception as error:
                pass

    def delete_task_to_memory(self):
        """ 删除任务时，同步删除内存中的任务 """
        if getattr(self, 'delete_to_memory') is True:
            try:
                self.disable_task()
            except Exception as error:
                pass


class BaseReport(BaseModel):
    """ 测试报告基类表 """
    __abstract__ = True

    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="测试报告名称")
    is_passed: Mapped[int] = mapped_column(Integer(), default=1, comment="是否全部通过，1全部通过，0有报错")
    run_type: Mapped[str] = mapped_column(
        String(255), default="task", nullable=True, comment="报告类型，task/suite/case/api")
    status: Mapped[int] = mapped_column(Integer(), default=1, comment="当前节点是否执行完毕，1执行中，2执行完毕")
    retry_count: Mapped[int] = mapped_column(Integer(), default=0, comment="已经执行重试的次数")
    env: Mapped[str] = mapped_column(String(255), default="test", comment="运行环境")
    temp_variables: Mapped[dict] = mapped_column(JSON, default={}, nullable=True, comment="临时参数")
    process: Mapped[int] = mapped_column(Integer(), default=1, comment="进度节点, 1: 解析数据、2: 执行测试、3: 写入报告")
    trigger_type: Mapped[TriggerTypeEnum] = mapped_column(
        default=TriggerTypeEnum.page, comment="触发类型，pipeline:流水线、page:页面、cron:定时任务")
    batch_id: Mapped[str] = mapped_column(String(128), index=True, comment="运行批次id，用于查询报告")
    trigger_id: Mapped[Union[int, list, str]] = mapped_column(JSON, comment="运行id，用于触发重跑")
    project_id: Mapped[int] = mapped_column(Integer(), nullable=False, index=True, comment="所属的服务id")
    summary: Mapped[dict] = mapped_column(JSON, default={}, comment="报告的统计")

    @classmethod
    def batch_delete_report(cls, report_id_list):
        """ 批量删除报告 """
        cls.query.filter(cls.id.in_(report_id_list)).delete()

    @classmethod
    def batch_delete_report_detail_data(cls, report_case_mode, report_step_mode):
        """ 批量删除报告下的数据 """
        report_list = cls.format_with_entities_query_list(cls.query.with_entities(cls.id).all())
        report_case_mode.query.filter(report_case_mode.report_id.notin_(report_list)).delete()
        report_step_mode.query.filter(report_step_mode.report_id.notin_(report_list)).delete()

    @staticmethod
    def get_summary_template():
        return {
            "result": "success",
            "stat": {
                "test_case": {  # 用例维度
                    "total": 1,  # 初始化的时候给个1，方便用户查看运行中的报告，后续会在流程中更新为实际的total
                    "success": 0,
                    "fail": 0,
                    "error": 0,
                    "skip": 0
                },
                "test_step": {  # 步骤维度
                    "total": 0,
                    "success": 0,
                    "fail": 0,
                    "error": 0,
                    "skip": 0
                },
                "count": {  # 此次运行有多少接口/元素
                    "api": 1,
                    "step": 1,
                    "element": 0
                }
            },
            "time": {  # 时间维度
                "start_at": "",
                "end_at": "",
                "step_duration": 0,  # 所有步骤的执行耗时，只统计请求耗时
                "case_duration": 0,  # 所有用例下所有步骤执行耗时，只统计请求耗时
                "all_duration": 0  # 开始执行 - 执行结束 整个过程的耗时，包含测试过程中的数据解析、等待...
            },
            "env": {  # 环境
                "code": "",
                "name": "",
            }
        }

    @classmethod
    def get_batch_id(cls):
        """ 生成运行id """
        return f'{g.user_id}_{int(time.time() * 1000000)}'

    @classmethod
    def get_new_report(cls, **kwargs):
        """ 生成一个测试报告 """
        if "summary" not in kwargs:
            kwargs["summary"] = cls.get_summary_template()
        return cls.model_create_and_get(kwargs)

    def merge_test_result(self, case_summary_list):
        """ 汇总测试数据和结果
        Args:
            case_summary_list (list): list of (testcase, result)
        """
        case_result = []
        total_case = len(case_summary_list)
        self.summary["stat"]["test_case"]["total"] = total_case
        self.summary["time"]["start_at"] = case_summary_list[0]["time"][
            "start_at"] if total_case > 0 else datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        for case_summary in case_summary_list:
            case_result.append(case_summary["result"])
            self.summary["stat"]["test_case"][case_summary["result"]] += 1
            self.summary["stat"]["test_step"]["total"] += case_summary["stat"]["total"]
            self.summary["stat"]["test_step"]["fail"] += case_summary["stat"]["fail"]
            self.summary["stat"]["test_step"]["error"] += case_summary["stat"]["error"]
            self.summary["stat"]["test_step"]["skip"] += case_summary["stat"]["skip"]
            self.summary["stat"]["test_step"]["success"] += case_summary["stat"]["success"]
            self.summary["time"]["step_duration"] += case_summary["time"]["step_duration"]
            self.summary["time"]["case_duration"] += case_summary["time"]["case_duration"]

        self.summary["result"] = "error" if "error" in case_result else "fail" if "fail" in case_result else "success"
        return self.summary

    def update_report_process(self, **kwargs):
        """ 更新执行进度 """
        self.__class__.query.filter_by(id=self.id).update(kwargs)

    def parse_data_start(self):
        """ 开始解析数据 """
        self.update_report_process(process=1, status=1)

    def parse_data_finish(self):
        """ 数据解析完毕 """
        self.update_report_process(process=1, status=2)

    def run_case_start(self):
        """ 开始运行测试 """
        self.update_report_process(process=2, status=1)

    def run_case_finish(self):
        """ 测试运行完毕 """
        self.update_report_process(process=2, status=2)

    def save_report_start(self):
        """ 开始保存报告 """
        self.update_report_process(process=3, status=1)

    def save_report_finish(self):
        """ 保存报告完毕 """
        self.update_report_process(process=3, status=2)

    def update_report_result(self, run_result, status=2, summary=None):
        """ 测试运行结束后，更新状态和结果 """
        update_dict = {"is_passed": 1 if run_result == "success" else 0, "status": status}
        if summary:
            update_dict["summary"] = self.loads(self.dumps(summary))
        self.__class__.query.filter_by(id=self.id).update(update_dict)

    @classmethod
    def select_is_all_status_by_batch_id(cls, batch_id, process_and_status=[1, 1]):
        """ 查询一个运行批次下离初始化状态最近的报告 """
        status_list = [[1, 1], [1, 2], [2, 1], [2, 2], [3, 1], [3, 2]]
        index = status_list.index(process_and_status)
        for process, status in status_list[index:]:  # 只查传入状态之后的状态
            data = cls.db.session.query(cls.id).filter(
                cls.batch_id == batch_id, cls.process == process, cls.status == status).first()
            if data:
                return {"process": process, "status": status}

    @classmethod
    def select_is_all_done_by_batch_id(cls, batch_id):
        """ 报告是否全部生成 """
        return cls.query.filter(cls.batch_id == batch_id, cls.process != 3, cls.status != 2).first() is None

    @classmethod
    def select_show_report_id(cls, batch_id):
        """ 获取一个运行批次要展示的报告 """
        # 全部通过
        run_fail_report = cls.db.session.query(cls.id).filter_by(batch_id=batch_id, is_passed=0).first()
        if run_fail_report:
            return run_fail_report[0]
        else:
            return cls.db.session.query(cls.id).filter_by(batch_id=batch_id).first()[0]


class BaseReportCase(BaseModel):
    """ 用例执行记录基类表 """
    __abstract__ = True

    name: Mapped[str] = mapped_column(String(128), nullable=True, comment="测试用例名称")
    case_id: Mapped[int] = mapped_column(Integer(), nullable=True, index=True, comment="执行记录对应的用例id")
    report_id: Mapped[int] = mapped_column(Integer(), index=True, comment="测试报告id")
    result: Mapped[str] = mapped_column(
        String(128), default='waite',
        comment="步骤测试结果，waite：等待执行、running：执行中、fail：执行不通过、success：执行通过、skip：跳过、error：报错")
    case_data: Mapped[dict] = mapped_column(JSON, default={}, comment="用例的数据")
    summary: Mapped[dict] = mapped_column(JSON, default={}, comment="用例的报告统计")
    error_msg: Mapped[str] = mapped_column(Text(), default='', comment="用例错误信息")

    @staticmethod
    def get_summary_template():
        return {
            "result": "skip",
            "stat": {
                'total': 1,  # 初始化的时候给个1，方便用户查看运行中的报告，后续会在流程中更新为实际的total
                'fail': 0,
                'error': 0,
                'skip': 0,
                'success': 0
            },
            "time": {
                "start_at": "",
                "end_at": "",
                "step_duration": 0,  # 当前用例的步骤执行耗时，只统计请求耗时
                "case_duration": 0,  # 当前用例下所有步骤执行耗时，只统计请求耗时
                "all_duration": 0  # 用例开始执行 - 执行结束 整个过程的耗时，包含测试过程中的数据解析、等待...
            }
        }

    def save_case_result_and_summary(self):
        """ 保存测试用例的结果和数据 """
        # 耗时
        self.summary["time"]["case_duration"] = round(self.summary["time"]["step_duration"] / 1000, 4)  # 毫秒转秒
        self.summary["time"]["all_duration"] = (
                self.summary["time"]["end_at"] - self.summary["time"]["start_at"]).total_seconds()
        self.summary["time"]["start_at"] = self.summary["time"]["start_at"].strftime("%Y-%m-%d %H:%M:%S.%f")
        self.summary["time"]["end_at"] = self.summary["time"]["end_at"].strftime("%Y-%m-%d %H:%M:%S.%f")

        # 状态
        if self.summary["stat"]["fail"] or self.summary["stat"]["error"]:  # 步骤里面有不通过或者错误，则把用例的结果置为不通过
            self.summary["result"] = "fail"
            self.test_is_fail(summary=self.summary)
        else:
            self.summary["result"] = "success"
            self.test_is_success(summary=self.summary)

    @classmethod
    def get_resport_case_list(cls, report_id, get_detail):
        """ 根据报告id，获取用例列表，性能考虑，只查关键字段 """
        field_title = ["id", "case_id", "name", "result", "summary", "case_data", "error_msg"]
        query_fields = [cls.id, cls.case_id, cls.name, cls.result]
        if get_detail is True:
            query_fields.extend([cls.summary, cls.case_data, cls.error_msg])

        # [(1, '用例1', 'running')]
        query_data = cls.query.filter(cls.report_id == report_id).with_entities(*query_fields).all()

        # [{ 'id': 1, 'name': '用例1', 'result': 'running' }]
        return [dict(zip(field_title, d)) for d in query_data]

    def update_report_case_data(self, case_data, summary=None):
        """ 更新测试数据 """
        update_dict = {"case_data": case_data}
        if summary:
            update_dict["summary"] = self.loads(self.dumps(summary))
        self.__class__.query.filter_by(id=self.id).update(update_dict)

    def update_report_case_result(self, result, case_data, summary, error_msg):
        """ 更新测试状态 """
        update_dict = {"result": result}
        if case_data:
            update_dict["case_data"] = self.loads(self.dumps(case_data))
        if summary:
            update_dict["summary"] = self.loads(self.dumps(summary))
        if error_msg:
            update_dict["error_msg"] = error_msg
        self.__class__.query.filter_by(id=self.id).update(update_dict)

    def test_is_running(self, case_data=None, summary=None):
        self.update_report_case_result("running", case_data, summary, error_msg=None)

    def test_is_fail(self, case_data=None, summary=None):
        self.update_report_case_result("fail", case_data, summary, error_msg=None)

    def test_is_success(self, case_data=None, summary=None):
        self.update_report_case_result("success", case_data, summary, error_msg=None)

    def test_is_skip(self, case_data=None, summary=None):
        self.update_report_case_result("skip", case_data, summary, error_msg=None)

    def test_is_error(self, case_data=None, summary=None, error_msg=None):
        self.update_report_case_result("error", case_data, summary, error_msg)


class BaseReportStep(BaseModel):
    """ 步骤执行记录基类表 """
    __abstract__ = True

    name: Mapped[str] = mapped_column(String(128), nullable=True, comment="测试步骤名称")
    case_id: Mapped[int] = mapped_column(Integer(), nullable=True, default=None, comment="步骤所在的用例id")
    step_id: Mapped[int] = mapped_column(Integer(), nullable=True, index=True, default=None, comment="步骤id")
    element_id: Mapped[int] = mapped_column(Integer(), comment="步骤对应的元素/接口id")
    report_case_id: Mapped[int] = mapped_column(Integer(), index=True, nullable=True, default=None,
                                                comment="用例数据id")
    report_id: Mapped[int] = mapped_column(Integer(), index=True, comment="测试报告id")
    process: Mapped[str] = mapped_column(
        String(128), default='waite',
        comment="步骤执行进度，waite：等待解析、parse: 解析数据、before：前置条件、after：后置条件、run：执行测试、extract：数据提取、validate：断言")
    result: Mapped[str] = mapped_column(
        String(128), default='waite',
        comment="步骤测试结果，waite：等待执行、running：执行中、fail：执行不通过、success：执行通过、skip：跳过、error：报错")
    step_data: Mapped[dict] = mapped_column(JSON, default={}, comment="步骤的数据")
    summary: Mapped[dict] = mapped_column(
        JSON, comment="步骤的统计",
        default={"response_time_ms": 0, "elapsed_ms": 0, "content_size": 0, "request_at": "", "response_at": ""})

    @staticmethod
    def get_summary_template():
        return {
            "start_at": "",
            "end_at": "",
            "step_duration": 0,  # 当前步骤执行耗时，只统计请求耗时
            "all_duration": 0  # 当前步骤开始执行 - 执行结束 整个过程的耗时，包含测试过程中的数据解析、等待...
        }

    @classmethod
    def get_resport_step_list(cls, report_case_id, get_detail):
        """ 获取步骤列表，性能考虑，只查关键字段 """
        field_title = ["id", "case_id", "name", "process", "result", "summary"]
        query_fields = [cls.id, cls.case_id, cls.name, cls.process, cls.result]

        if get_detail is True:
            query_fields.append(cls.summary)

        # [(1, '步骤1', 'before', 'running')]
        query_data = cls.query.filter(cls.report_case_id == report_case_id).with_entities(*query_fields).all()

        # [{ 'id': 1, 'name': '步骤1', 'process': 'before', 'result': 'success' }]
        return [dict(zip(field_title, d)) for d in query_data]

    def save_step_result_and_summary(self, step_runner, step_error_traceback=None):
        """ 保存测试步骤的结果和数据 """
        data = step_runner.get_test_step_data()
        step_data = self.loads(self.dumps(data))  # 可能有 datetime 格式的数据
        step_meta_data = step_runner.client_session.meta_data
        step_data["attachment"] = step_error_traceback
        # 保存测试步骤的结果和数据
        self.update_report_step_data(
            step_data=step_data, result=step_meta_data["result"], summary=step_meta_data["stat"])

    @classmethod
    def add_run_step_result_count(cls, case_summary, step_meta_data):
        """ 记录步骤执行结果数量 """
        if step_meta_data["result"] == "success":
            case_summary["stat"]["success"] += 1
            case_summary["time"]["step_duration"] += step_meta_data["stat"]["elapsed_ms"]
        elif step_meta_data["result"] == "fail":
            case_summary["stat"]["fail"] += 1
            case_summary["time"]["step_duration"] += step_meta_data["stat"]["elapsed_ms"]
        elif step_meta_data["result"] == "error":
            case_summary["stat"]["error"] += 1
        elif step_meta_data["result"] == "skip":
            case_summary["stat"]["skip"] += 1

    def update_report_step_data(self, **kwargs):
        """ 更新测试数据 """
        self.__class__.query.filter_by(id=self.id).update(kwargs)

    def update_test_result(self, result, step_data):
        """ 更新测试状态 """
        update_dict = {"result": result}
        if step_data:
            update_dict["step_data"] = self.loads(self.dumps(step_data))
        self.__class__.query.filter_by(id=self.id).update(update_dict)

    def test_is_running(self, step_data=None):
        self.update_test_result("running", step_data)

    def test_is_fail(self, step_data=None):
        self.update_test_result("fail", step_data)

    def test_is_success(self, step_data=None):
        self.update_test_result("success", step_data)

    def test_is_skip(self, step_data=None):
        self.update_test_result("skip", step_data)

    def test_is_error(self, step_data=None):
        self.update_test_result("error", step_data)

    def update_step_process(self, process, step_data):
        """ 更新数据和执行进度 """
        update_dict = {"process": process}
        if step_data:
            update_dict["step_data"] = self.loads(self.dumps(step_data))
        self.__class__.query.filter_by(id=self.id).update(update_dict)

    def test_is_start_parse(self, step_data=None):
        self.update_step_process("parse", step_data)

    def test_is_start_before(self, step_data=None):
        self.update_step_process("before", step_data)

    def test_is_start_running(self, step_data=None):
        self.update_step_process("run", step_data)

    def test_is_start_extract(self, step_data=None):
        self.update_step_process("extract", step_data)

    def test_is_start_after(self, step_data=None):
        self.update_step_process("after", step_data)

    def test_is_start_validate(self, step_data=None):
        self.update_step_process("validate", step_data)


class FuncErrorRecord(BaseModel):
    """ 自定义函数执行错误记录表 """
    __tablename__ = "func_error_record"
    __table_args__ = {"comment": "自定义函数执行错误记录表"}

    name: Mapped[str] = mapped_column(String(255), nullable=False, comment="错误title")
    detail: Mapped[str] = mapped_column(Text(), default="", comment="错误详情")


class SaveRequestLog(BaseModel):
    """ 记录请求表 """
    __abstract__ = True

    ip: Mapped[str] = mapped_column(String(256), nullable=True, comment="访问来源ip")
    url: Mapped[str] = mapped_column(String(256), nullable=True, comment="请求地址")
    method: Mapped[str] = mapped_column(String(10), nullable=True, comment="请求方法")
    headers: Mapped[dict] = mapped_column(JSON, nullable=True, default={}, comment="头部参数")
    params: Mapped[dict] = mapped_column(JSON, nullable=True, default={}, comment="查询字符串参数")
    data_form: Mapped[dict] = mapped_column(JSON, nullable=True, default={}, comment="form_data参数")
    data_json: Mapped[dict] = mapped_column(JSON, nullable=True, default={}, comment="json参数")
