# -*- coding: utf-8 -*-
import time
from datetime import datetime
from werkzeug.exceptions import abort

from flask import g, current_app as app
from flask_sqlalchemy import SQLAlchemy as _SQLAlchemy, BaseQuery, Pagination
from sqlalchemy import MetaData
from contextlib import contextmanager
from sqlalchemy.dialects.mysql import LONGTEXT

from utils.util.jsonUtil import JsonUtil
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
        res = self.session.execute(sql).fetchall()
        if to_dict:
            return dict(res) if res else {}
        else:
            return res


class Qeury(BaseQuery):
    """ 重写query方法，使其默认加上status=0 """

    def filter_by(self, **kwargs):
        """ 如果传过来的参数中不含is_delete，则默认加一个is_delete参数，状态为0 查询有效的数据"""
        # kwargs.setdefault("is_delete", 0)
        return super(Qeury, self).filter_by(**kwargs)

    def paginate(self, page=1, per_page=20, error_out=True, max_per_page=None):
        """ 重写分页器，把页码和页数强制转成int，解决服务器吧int识别为str导致分页报错的问题"""
        page, per_page = int(page) or app.config["page_num"], int(per_page) or app.config["page_size"]
        if max_per_page is not None:
            per_page = min(per_page, max_per_page)
        items = self.limit(per_page).offset((page - 1) * per_page).all()
        if not items and page != 1 and error_out:
            abort(404)
        total = self.order_by(None).count()
        return Pagination(self, page, per_page, total, items)


# 由于数据库迁移的时候，不兼容约束关系的迁移，下面是百度出的解决方案
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
db = SQLAlchemy(
    query_class=Qeury,  # 指定使用修改过后的Qeury
    metadata=MetaData(naming_convention=naming_convention),
    use_native_unicode="utf8"
)


class BaseModel(db.Model, JsonUtil):
    """ 基类模型 """
    __abstract__ = True

    # is_delete = db.Column(db.SmallInteger, default=0, comment="通过更改状态来判断记录是否被删除, 0数据有效, 1数据已删除")
    id = db.Column(db.Integer(), primary_key=True, comment="主键，自增")
    created_time = db.Column(db.DateTime, default=datetime.now, comment="创建时间")
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment="修改时间")
    create_user = db.Column(db.Integer(), nullable=True, default=1, comment="创建数据的用户id")
    update_user = db.Column(db.Integer(), nullable=True, default=1, comment="修改数据的用户id")

    # 需要做序列化和反序列化的字段
    serialization_file_list = [
        "extend_role",
        "headers", "variables", "script_list", "pop_header_filed", "output",
        "params", "data_form", "data_json", "data_urlencoded", "extracts", "validates", "data_driver", "skip_if",
        "call_back", "suite_ids", "case_ids", "conf", "env_list", "webhook_list", "email_to", "temp_variables",
        "kym", "task_item", 'business_list', 'run_id', 'extends', 'case_data', 'step_data', 'summary'
    ]

    def set_attr(self, column_list, value=None):
        """ 插入属性，如果是执行初始化脚本，获取不到g，try一下 """
        for column in column_list:
            try:
                if column in ["create_user", "update_user"]:
                    a = g
                    value = g.user_id if hasattr(g, "user_id") else None
                setattr(self, column, value)
            except Exception as error:
                pass

    @property
    def str_created_time(self):
        try:
            return datetime.strftime(self.created_time, "%Y-%m-%d %H:%M:%S")
        except:
            return self.created_time

    @property
    def str_update_time(self):
        try:
            return datetime.strftime(self.update_time, "%Y-%m-%d %H:%M:%S")
        except:
            return self.created_time

    def create(self, attrs_dict: dict, *args):
        """ 插入数据，若指定了字段，则把该字段的值转为json """
        if not args:
            args = self.serialization_file_list

        with db.auto_commit():
            for key, value in attrs_dict.items():
                if hasattr(self, key) and key not in ["id", "created_time", "update_time"]:
                    if key in args:
                        try:
                            setattr(self, key, self.dumps(value))
                        except:
                            setattr(self, key, value)
                    else:
                        setattr(self, key, value)

            self.set_attr(["create_user", "update_user"])

            db.session.add(self)
        return self

    def update(self, attrs_dict: dict, *args, is_save_num=False, **kwargs):
        """ 修改数据，若指定了字段，则把该字段的值转为json """
        if not args:
            args = self.serialization_file_list

        ignore_filed = ["id"]
        if is_save_num is False:
            ignore_filed.append("num")

        with db.auto_commit():
            for key, value in attrs_dict.items():
                if hasattr(self, key) and key not in ignore_filed:
                    if key in args:
                        try:
                            setattr(self, key, self.dumps(value))
                        except:
                            setattr(self, key, value)
                    else:
                        setattr(self, key, value)

            self.set_attr(["update_user"])

    def delete(self):
        """ 删除单条数据 """
        with db.auto_commit():
            db.session.delete(self)

    def enable(self):
        """ 启用数据 """
        with db.auto_commit():
            self.status = 1

    def disable(self):
        """ 禁用数据 """
        with db.auto_commit():
            self.status = 0

    def is_enable(self):
        """ 判断数据是否为启用状态 """
        return self.status == 1

    def is_disable(self):
        """ 判断数据是否为禁用状态 """
        return self.status == 0

    def delete_current_and_children(self, child_model, filter_field):
        """ 删除当前数据，并且删除下游数据 """
        with db.auto_commit():
            child_model.query.filter(getattr(child_model, filter_field) == self.id).delete(synchronize_session=False)
            db.session.delete(self)

    # def delete(self):
    #     """ 软删除 """
    #     self.is_delete = 1

    def is_create_user(self, user_id):
        """ 判断当前传进来的id为数据创建者 """
        return self.create_user == user_id

    def copy(self):
        """ 复制本身对象 """
        data = self.to_dict()
        data["name"] = data.get("name") + "_copy" if data.get("name") else "_copy"
        return self.__class__().create(data)

    @classmethod
    def get_first(cls, **kwargs):
        """ 获取第一条数据 """
        with db.auto_commit():
            data = cls.query.filter_by(**kwargs).first()
        return data

    @classmethod
    def get_all(cls, **kwargs):
        """ 获取全部数据 """
        with db.auto_commit():
            data = cls.query.filter_by(**kwargs).all()
        return data

    @classmethod
    def get_filter_by(cls, **kwargs):
        """ 获取filter_by对象 """
        with db.auto_commit():
            data = cls.query.filter_by(**kwargs)
        return data

    @classmethod
    def get_filter(cls, **kwargs):
        """ 获取filter对象 """
        with db.auto_commit():
            data = cls.query.filter(**kwargs)
        return data

    @classmethod
    def get_from_path(cls, data_id):
        """ 获取模块/用例集的归属 """
        from_name = []

        def get_from(m_id):
            parent = cls.get_first(id=m_id)
            from_name.insert(0, parent.name)

            if parent.parent:
                get_from(parent.parent)

        get_from(data_id)
        return '/'.join(from_name)

    @classmethod
    def change_sort(cls, id_list, page_num, page_size):
        """ 批量修改排序 """
        with db.auto_commit():
            for index, data_id in enumerate(id_list):
                data = cls.get_first(id=data_id)
                if data:
                    data.num = (page_num - 1) * page_size + index

    @classmethod
    def get_max_num(cls, **kwargs):
        """ 返回 model 表中**kwargs筛选条件下的已存在编号num的最大值 """
        max_num_data = cls.get_filter_by(**kwargs).order_by(cls.num.desc()).first()
        return max_num_data.num if max_num_data and max_num_data.num else 0

    @classmethod
    def get_insert_num(cls, **kwargs):
        """ 返回 model 表中**kwargs筛选条件下的已存在编号num的最大值 + 1 """
        return cls.get_max_num(**kwargs) + 1

    @classmethod
    def is_admin(cls):
        """ 管理员权限 """
        return 'admin' in g.api_permissions

    @classmethod
    def is_not_admin(cls):
        """ 非管理员权限 """
        return not cls.is_admin()

    def to_dict(self, to_dict: list = [], pop_list: list = [], filter_list: list = []):
        """ 自定义序列化器，把模型的每个字段转为key，方便返回给前端
        to_dict: 要转为字典的字段
        pop_list: 序列化时忽略的字段
        filter_list: 仅要序列化的字段
        当 pop_list 与 filter_list 同时包含同一个字段时，以 filter_list 为准
        """
        if not to_dict:
            to_dict = self.serialization_file_list

        dict_data = {}
        for column in self.__table__.columns:
            if filter_list:
                if column.name in filter_list:
                    dict_data[column.name] = self.serialization_data(column.name, to_dict)
            else:
                if column.name not in pop_list:
                    dict_data[column.name] = self.serialization_data(column.name, to_dict)
        return dict_data

    def serialization_data(self, column_name, to_dict_list):
        if column_name == "created_time":
            return self.str_created_time
        elif column_name == "update_time":
            return self.str_update_time
        elif column_name == "start_time":
            return self.str_start_time
        elif column_name == "end_time":
            return self.str_end_time
        else:
            data = getattr(self, column_name)
            # 字段有值且在要转json的列表里面，就转为json
            if data and column_name in to_dict_list:
                try:
                    return self.loads(data)
                except:
                    return data
            else:
                return data

    def change_status(self, status=None):
        """ 修改状态 """
        if hasattr(self, 'status'):
            if status is not None:
                change_status = status
            else:
                change_status = 1 if self.status == 0 else 0
            self.update({"status": change_status})

    @classmethod
    def pop_field(cls, data: dict, field_list: list = []):
        for field in field_list:
            if field in data:
                data.pop(field)
        return data

    @classmethod
    def pagination(cls, page_num, page_size, filters: list = [], order_by=None, pop_field=[]):
        """ 分页, 如果没有传页码和页数，则根据查询条件获取全部数据
        filters：过滤条件
        page_num：页数
        page_size：页码
        order_by: 排序规则
        pop_field: 返回数据中，指定不返回的字段
        """
        if page_num and page_size:
            query_obj = cls.query.filter(*filters).order_by(order_by) if filters else cls.query.order_by(order_by)
            result = query_obj.paginate(page_num, per_page=page_size, error_out=False)
            return {"total": result.total,
                    "data": [cls.pop_field(model.to_dict(), pop_field) for model in result.items]}
        all_data = cls.query.filter(*filters).order_by(order_by).all()
        return {"total": len(all_data), "data": [cls.pop_field(model.to_dict(), pop_field) for model in all_data]}


class ApschedulerJobs(BaseModel):
    """ apscheduler任务表，防止执行数据库迁移的时候，把定时任务删除了 """
    __tablename__ = "apscheduler_jobs"
    __table_args__ = {"comment": "定时任务执行计划表"}

    id = db.Column(db.String(64), primary_key=True, nullable=False)
    next_run_time = db.Column(db.String(128), comment="任务下一次运行时间")
    job_state = db.Column(db.LargeBinary(length=(2 ** 32) - 1), comment="任务详情")


class BaseProject(BaseModel):
    """ 服务基类表 """
    __abstract__ = True

    name = db.Column(db.String(255), nullable=True, comment="服务名称")
    manager = db.Column(db.Integer(), nullable=True, default=1, comment="服务管理员id，默认为admin")
    script_list = db.Column(db.Text(), nullable=True, default="[]", comment="引用的脚本文件")
    num = db.Column(db.Integer(), nullable=True, comment="当前服务的序号")
    business_id = db.Column(db.Integer(), comment="所属业务线")


    @classmethod
    def is_manager_id(cls, project_id):
        """ 判断当前用户为当前数据的负责人 """
        return cls.get_first(id=project_id).manager == g.user_id

    @classmethod
    def is_can_delete(cls, project_id, obj):
        """
        判断是否有权限删除，
        可删除条件（或）：
        1.当前用户为系统管理员
        2.当前用户为当前数据的创建者
        3.当前用户为当前要删除服务的负责人
        """
        return cls.is_manager_id(project_id) or cls.is_admin() or obj.is_create_user(g.user_id)

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.business_id.data and form.business_id.data in g.business_list:
            filters.append(cls.business_id == form.business_id.data)
        else:
            if cls.is_not_admin():  # 非管理员则校验业务线权限
                filters.append(cls.business_id.in_(g.business_list))
        if form.name.data:
            filters.append(cls.name.like(f'%{form.name.data}%'))
        if form.manager.data:
            filters.append(cls.manager == form.manager.data)
        if form.create_user.data:
            filters.append(cls.create_user == form.create_user.data)
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.num.asc())


class BaseProjectEnv(BaseModel):
    """ 服务环境基类表 """
    __abstract__ = True

    host = db.Column(db.String(255), default="http://localhost:8023", comment="服务地址")
    variables = db.Column(
        db.Text(), default='[{"key": "", "value": "", "remark": "", "data_type": ""}]', comment="服务的公共变量"
    )

    env_id = db.Column(db.Integer(), nullable=True, comment="对应环境id")
    project_id = db.Column(db.Integer(), nullable=True, comment="所属的服务id")

    @classmethod
    def synchronization(cls, from_env, to_env_id_list: list, filed_list: list):
        """ 把当前环境同步到其他环境
        from_env: 从哪个环境
        to_env_list: 同步到哪些环境
        filed_list: 指定要同步的字段列表
        """

        # 同步数据来源解析
        from_env_dict = {}
        for filed in filed_list:
            from_env_dict[filed] = parse_list_to_dict(cls.loads(getattr(from_env, filed)))

        # 已同步数据的容器
        synchronization_result = {}

        # 同步至指定环境
        for to_env in to_env_id_list:
            to_env_data = cls.get_first(project_id=from_env.project_id, env_id=to_env)
            new_env_data = {}
            for filed in filed_list:
                from_data, to_data = from_env_dict[filed], cls.loads(getattr(to_env_data, filed))
                new_env_data[filed] = update_dict_to_list(from_data, to_data)

            to_env_data.update(new_env_data)  # 同步环境
            synchronization_result[to_env] = to_env_data.to_dict()  # 保存已同步的环境数据
        return synchronization_result

    @classmethod
    def delete_by_project_id(cls, project_id):
        """ 根据服务/项目id删除环境 """
        cls.query.filter(cls.project_id == project_id).delete(synchronize_session=False)

    @classmethod
    def add_env(cls, env_id, project_model):
        """ 新增运行环境时，批量给服务/项目/APP加上 """
        for project in project_model.get_all():
            if not cls.get_first(project_id=project.id, env_id=env_id):
                cls().create({"env_id": env_id, "project_id": project.id})


class BaseModule(BaseModel):
    """ 模块基类表 """
    __abstract__ = True

    name = db.Column(db.String(255), nullable=True, comment="模块名")
    num = db.Column(db.Integer(), nullable=True, comment="模块在对应服务下的序号")
    parent = db.Column(db.Integer(), nullable=True, default=None, comment="上一级模块id")
    project_id = db.Column(db.Integer(), comment="所属的服务id")

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.projectId.data:
            filters.append(cls.project_id == form.projectId.data)
        if form.name.data:
            filters.append(cls.name.like(f'%{form.name.data}%'))
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.num.asc()
        )


class BaseApi(BaseModel):
    """ 页面表 """
    __abstract__ = True

    num = db.Column(db.Integer(), nullable=True, comment="序号")
    name = db.Column(db.String(255), nullable=True, comment="名称")
    desc = db.Column(db.Text(), default="", nullable=True, comment="描述")
    project_id = db.Column(db.Integer(), nullable=True, comment="所属的服务id")
    module_id = db.Column(db.Integer(), comment="所属的模块id")


class BaseCaseSuite(BaseModel):
    """ 用例集基类表 """
    __abstract__ = True

    name = db.Column(db.String(255), nullable=True, comment="用例集名称")
    num = db.Column(db.Integer(), nullable=True, comment="用例集在对应服务下的序号")
    suite_type = db.Column(db.String(64), default="base",
                           comment="用例集类型，base: 基础用例集，api: 单接口用例集，process: 流程用例集，assist: 造数据用例集")
    parent = db.Column(db.Integer(), nullable=True, default=None, comment="上一级用例集id")
    project_id = db.Column(db.Integer(), comment="所属的服务id")

    @classmethod
    def upload(cls, project_id, data_tree, case_model):
        """ 上传用例集 """
        suite_pass, suite_fail, case_pass, case_fail = [], [], [], []
        topic_list = data_tree.get("topic", {}).get("topics", [])

        def insert_data(topic_data, parent=None):
            title = topic_data.get("title", "")

            if title.startswith('tc'):  # 用例
                case_name = title.split(':')[1] if ':' in title else title.split('：')[1]  # 支持中英文的冒号
                if case_model.get_first(name=case_name, suite_id=parent) is None:  # 有才导入
                    desc = topic_data.get("topics", [{}])[0].get("title", case_name)
                    num = case_model.get_insert_num(suite_id=parent)
                    try:
                        case_model().create({"name": case_name, "num": num, "desc": desc, "suite_id": parent})
                        case_pass.append(case_name)
                    except:
                        case_fail.append(case_name)
            else:  # 用例集
                suite = cls.get_first(parent=parent, name=title, project_id=project_id)
                if suite is None:  # 有就插入下级
                    num = cls.get_insert_num(project_id=project_id)
                    try:
                        suite = cls().create({
                            "name": title,
                            "num": num,
                            "project_id": project_id,
                            "parent": parent,
                            "suite_type": "process"
                        })
                        suite_pass.append(title)
                    except:
                        suite_fail.append(title)
                        return
                for child in topic_data.get("topics", []):
                    insert_data(child, suite.id)

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

        def change_child_suite_type(parent_id):
            child_list = self.get_all(parent=parent_id)
            for child in child_list:
                print(f'child.name: {child.name}')
                child.update({"suite_type": self.suite_type})
                change_child_suite_type(child.id)

        change_child_suite_type(self.id)

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.project_id.data:
            filters.append(cls.project_id == form.project_id.data)
        if form.name.data:
            filters.append(cls.name == form.name.data)
        if form.suite_type.data:
            filters.append(cls.suite_type.in_(form.suite_type.data))
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.id.asc()
        )

    @classmethod
    def create_suite_by_project(cls, project_id):
        """ 根据项目id，创建用例集 """
        project_type = "api" if "api" in cls.__name__.lower() else "ui"
        for index, suite_type in enumerate(Config.get_suite_type_list(project_type)):
            cls().create({
                "num": index,
                "project_id": project_id,
                "name": suite_type["value"],
                "suite_type": suite_type["key"]
            })

    def get_run_case_id(self, case_model, business_id=None):
        """ 获取用例集下，状态为要运行的用例id """
        query = {"suite_id": self.id, "status": 1}
        if business_id:
            query["business_id"] = business_id
        data = [
            case.id for case in
            case_model.query.filter_by(**query).order_by(case_model.num.asc()).all()
        ]
        return data

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
            suite_id = [
                suite.id for suite in cls.query.filter(
                    cls.project_id == project_id, cls.suite_type.in_(['api', 'process'])
                ).order_by(cls.num.asc()).all()
            ]

        # 解析已选中的用例集，并继承已选中的用例列表，再根据用例id去重
        case_ids = [
            case.id for id in suite_id for case in case_model.query.filter_by(
                suite_id=id,
                status=1
            ).order_by(case_model.num.asc()).all() if case and case.status
        ]
        case_ids.extend(case_id)
        return list(set(case_ids))


class BaseCase(BaseModel):
    """ 用例基类表 """

    __abstract__ = True

    num = db.Column(db.Integer(), nullable=True, comment="用例序号")
    name = db.Column(db.String(255), nullable=True, comment="用例名称")
    desc = db.Column(db.Text(), comment="用例描述")
    status = db.Column(db.Integer(), default=0,
                       comment="用例调试状态，0未调试-不执行，1调试通过-要执行，2调试通过-不执行，3调试不通过-不执行，默认未调试-不执行")
    run_times = db.Column(db.Integer(), default=1, comment="执行次数，默认执行1次")
    script_list = db.Column(db.Text(), default="[]", comment="用例需要引用的脚本list")
    variables = db.Column(
        db.Text(), default='[{"key": "", "value": "", "remark": "", "data_type": ""}]', comment="用例级的公共参数"
    )
    output = db.Column(
        db.Text(), default='[]', comment="用例出参（步骤提取的数据）"
    )
    skip_if = db.Column(
        db.Text(),
        default=BaseModel.dumps([
            {"skip_type": "", "data_source": "", "check_value": "", "comparator": "", "data_type": "", "expect": ""}
        ]),
        comment="是否跳过的判断条件"
    )
    suite_id = db.Column(db.Integer(), comment="所属的用例集id")

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.suiteId.data:
            filters.append(cls.suite_id == form.suiteId.data)
        if form.name.data:
            filters.append(cls.name.like(f"%{form.name.data}%"))
        if form.status.data:
            filters.append(cls.status == form.status.data)
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.num.asc()
        )

    @classmethod
    def get_quote_case_from(cls, case_id, project_model, suite_model, case_model):
        """ 获取用例的归属 """
        case = case_model.get_first(id=case_id)
        suite_path_name = suite_model.get_from_path(case.suite_id)
        suite = suite_model.get_first(id=case.suite_id)
        project = project_model.get_first(id=suite.project_id)
        return f'{project.name}/{suite_path_name}/{case.name}'

    @classmethod
    def merge_variables(cls, from_case_id, to_case_id):
        """ 当用例引用的时候，自动将被引用用例的自定义变量合并到发起引用的用例上 """
        if from_case_id:
            from_case, to_case = cls.get_first(id=from_case_id), cls.get_first(id=to_case_id),
            from_case_variables = {variable["key"]: variable for variable in from_case.to_dict()["variables"]}
            to_case_variables = {variable["key"]: variable for variable in to_case.to_dict()["variables"]}

            for from_variable_key, from_case_variable in from_case_variables.items():
                to_case_variables.setdefault(from_variable_key, from_case_variable)

            to_case.update({"variables": [value for key, value in to_case_variables.items() if key]})

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
                source_case_output = parse_list_to_dict(cls.loads(source_case.output))
                output_dict.update(source_case_output)
            else:  # 更新源为步骤（添加步骤和复制其他用例的步骤）
                output_dict.update(parse_list_to_dict(source["extracts"]))

        to_case = cls.get_first(id=case_id)
        output_dict.update(parse_list_to_dict(cls.loads(to_case.output)))
        to_case.update({"output": parse_dict_to_list(output_dict, False)})


class BaseStep(BaseModel):
    """ 测试步骤基类表 """

    __abstract__ = True

    num = db.Column(db.Integer(), nullable=True, comment="步骤序号，执行顺序按序号来")
    status = db.Column(db.Integer(), default=1, comment="是否执行此步骤，1执行，0不执行，默认执行")
    run_times = db.Column(db.Integer(), default=1, comment="执行次数，默认执行1次")
    name = db.Column(db.String(255), comment="步骤名称")
    up_func = db.Column(db.Text(), default="", comment="步骤执行前的函数")
    down_func = db.Column(db.Text(), default="", comment="步骤执行后的函数")
    skip_if = db.Column(
        db.Text(),
        default=BaseModel.dumps([
            {"skip_type": "", "data_source": "", "check_value": "", "comparator": "", "data_type": "", "expect": ""}
        ]),
        comment="是否跳过的判断条件"
    )
    skip_on_fail = db.Column(db.Integer(), default=1,
                             comment="当用例有失败的步骤时，是否跳过此步骤，1跳过，0不跳过，默认跳过")
    data_driver = db.Column(db.Text(), default="[]", comment="数据驱动，若此字段有值，则走数据驱动的解析")
    quote_case = db.Column(db.String(5), default="", comment="引用用例的id")
    case_id = db.Column(db.Integer(), comment="步骤所在的用例的id")

    @classmethod
    def delete_by_case_id(cls, case_id):
        """ 根据用例id删除步骤 """
        cls.query.filter(cls.case_id == case_id).delete(synchronize_session=False)

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
                    # step["hasStep"] = cls.get_first(case_id=step["quote_case"]) is not None
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


class BaseTask(BaseModel):
    """ 定时任务基类表 """
    __abstract__ = True

    num = db.Column(db.Integer(), comment="任务序号")
    name = db.Column(db.String(255), comment="任务名称")
    env_list = db.Column(db.String(255), default='[]', comment="运行环境")
    case_ids = db.Column(db.Text(), comment="用例id")
    task_type = db.Column(db.String(255), default="cron", comment="定时类型")
    cron = db.Column(db.String(255), nullable=True, comment="cron表达式")
    is_send = db.Column(db.String(10), comment="是否发送报告，1.不发送、2.始终发送、3.仅用例不通过时发送")
    receive_type = db.Column(db.String(255), default="ding_ding", comment="接收测试报告类型: ding_ding、we_chat、email")
    webhook_list = db.Column(db.Text(), comment="机器人地址")
    email_server = db.Column(db.String(255), comment="发件邮箱服务器")
    email_from = db.Column(db.String(255), comment="发件人邮箱")
    email_pwd = db.Column(db.String(255), comment="发件人邮箱密码")
    email_to = db.Column(db.Text(), comment="收件人邮箱")
    status = db.Column(db.Integer(), default=0, comment="任务的运行状态，0：禁用中、1：启用中，默认0")
    is_async = db.Column(db.Integer(), default=1, comment="任务的运行机制，0：单线程，1：多线程，默认1")
    suite_ids = db.Column(db.Text(), comment="用例集id")
    call_back = db.Column(db.Text(), comment="回调给流水线")
    project_id = db.Column(db.Integer(), comment="所属的服务id")
    conf = db.Column(
        db.Text(),
        default='{"browser": "chrome", "server_id": "", "phone_id": "", "no_reset": ""}',
        comment="运行配置，webUi存浏览器，appUi存运行服务器、手机、是否重置APP")

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.projectId.data:
            filters.append(cls.project_id == form.projectId.data)
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.num.asc()
        )


class BaseReport(BaseModel):
    """ 测试报告基类表 """
    __abstract__ = True

    name = db.Column(db.String(128), nullable=True, comment="测试报告名称")
    is_passed = db.Column(db.Integer(), default=1, comment="是否全部通过，1全部通过，0有报错")
    run_type = db.Column(db.String(255), default="task", nullable=True, comment="报告类型，task/suite/case/api")
    status = db.Column(db.Integer(), default=1, comment="当前节点是否执行完毕，1执行中，2执行完毕")
    retry_count = db.Column(db.Integer(), default=0, comment="已经执行重试的次数")
    env = db.Column(db.String(255), default="test", comment="运行环境")
    temp_variables = db.Column(db.Text(), default=None, comment="临时参数")
    process = db.Column(db.Integer(), default=1, comment="进度节点, 1: 解析数据、2: 执行测试、3: 写入报告")
    trigger_type = db.Column(
        db.String(128), nullable=True, default="page", comment="触发类型，pipeline:流水线、page:页面、cron:定时任务")
    batch_id = db.Column(db.String(128), comment="运行批次id，用于查询报告")
    run_id = db.Column(db.String(512), comment="运行id，用于触发重跑")
    project_id = db.Column(db.Integer(), comment="所属的服务id")
    summary = db.Column(db.Text(), default='{}', comment="报告的统计")

    @staticmethod
    def get_summary_template():
        return {
            "success": True,
            "stat": {
                "testcases": {
                    "total": 1,  # 初始化的时候给个1，方便用户查看运行中的报告，后续会在流程中更新为实际的total
                    "success": 0,
                    "fail": 0
                },
                "teststeps": {
                    "total": 0,
                    "failures": 0,
                    "errors": 0,
                    "skipped": 0,
                    "expectedFailures": 0,
                    "unexpectedSuccesses": 0,
                    "successes": 0
                }
            },
            "time": {
                "start_at": "",
                "start_date": "",
                "duration": 0
            },
            "run_type": "case",
            "is_async": 0,
            "run_env": "",
            "env_name": "",
            "count_step": 0,
            "count_api": 0,
            "count_element": 0
        }

    @classmethod
    def batch_delete(cls, report_list, report_case_mode, report_step_mode):
        """ 批量删除报告 """
        for report in report_list:
            with db.auto_commit():
                report_case_mode.query.filter(report_case_mode.report_id == report.id).delete()
                report_step_mode.query.filter(report_step_mode.report_id == report.id).delete()
                cls.query.filter(cls.id == report.id).delete()

    @classmethod
    def get_batch_id(cls):
        """ 生产运行id """
        return f'{g.user_id}_{int(time.time() * 1000000)}'

    def update_status(self, run_result, status=2, summary=None):
        """ 测试运行结束后，更新状态和结果 """
        update_dict = {"is_passed": 1 if run_result else 0, "status": status}
        if summary:
            update_dict["summary"] = summary
        self.update(update_dict)

    def retry_count_increase(self):
        """ 增加重试次数 """
        self.update({"retry_count": self.retry_count + 1})

    @classmethod
    def parse_data_start(cls, report_id):
        """ 开始解析数据 """
        cls.get_first(id=report_id).update({"process": 1, "status": 1})

    @classmethod
    def parse_data_finish(cls, report_id):
        """ 数据解析完毕 """
        cls.get_first(id=report_id).update({"process": 1, "status": 2})

    @classmethod
    def run_case_start(cls, report_id):
        """ 开始运行测试 """
        cls.get_first(id=report_id).update({"process": 2, "status": 1})

    @classmethod
    def run_case_finish(cls, report_id):
        """ 测试运行完毕 """
        cls.get_first(id=report_id).update({"process": 2, "status": 2})

    @classmethod
    def save_report_start(cls, report_id):
        """ 开始保存报告 """
        cls.get_first(id=report_id).update({"process": 3, "status": 1})

    @classmethod
    def save_report_finish(cls, report_id):
        """ 保存报告完毕 """
        cls.get_first(id=report_id).update({"process": 3, "status": 2})

    @classmethod
    def get_new_report(cls, **kwargs):
        kwargs["create_user"] = kwargs["create_user"] or g.user_id
        return cls().create(kwargs)

    @classmethod
    def select_is_all_status_by_batch_id(cls, batch_id, process_and_status=[1, 1]):
        """ 查询一个运行批次下离初始化状态最近的报告 """
        status_list = [[1, 1], [1, 2], [2, 1], [2, 2], [3, 1], [3, 2]]
        index = status_list.index(process_and_status)
        for process, status in status_list[index:]:  # 只查传入状态之后的状态
            if cls.query.filter(cls.batch_id == batch_id, cls.process == process, cls.status == status).first():
                return {"process": process, "status": status}

    @classmethod
    def select_is_all_done_by_batch_id(cls, batch_id):
        """ 报告是否全部生成 """
        return cls.query.filter(cls.batch_id == batch_id, cls.process != 3, cls.status != 2).first() is None

    @classmethod
    def select_show_report_id(cls, batch_id):
        """ 获取一个运行批次要展示的报告 """
        # 全部通过
        run_fail_report = cls.get_first(batch_id=batch_id, is_passed=0)
        if run_fail_report:
            return run_fail_report.id
        else:
            return cls.get_first(batch_id=batch_id).id

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.projectName.data:
            filters.append(cls.name.like(f"%{form.projectName.data}%"))
        if form.createUser.data:
            filters.append(cls.create_user == form.createUser.data)
        if form.trigger_type.data:
            filters.append(cls.trigger_type == form.trigger_type.data)
        if form.run_type.data:
            filters.append(cls.run_type == form.run_type.data)
        if form.is_passed.data:
            filters.append(cls.is_passed == form.is_passed.data)
        if form.env_list.data:
            filters.append(cls.env.in_(form.env_list.data))
        if form.projectId.data:
            filters.append(cls.project_id == form.projectId.data)
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.created_time.desc(),
            pop_field=["summary"]
        )


class BaseReportCase(BaseModel):
    """ 用例执行记录基类表 """
    __abstract__ = True

    name = db.Column(db.String(128), nullable=True, comment="测试用例名称")
    from_id = db.Column(db.Integer(), comment="执行记录对应的用例id")
    report_id = db.Column(db.Integer(), index=True, comment="测试报告id")
    result = db.Column(db.String(128), default='waite',
                       comment="步骤测试结果，waite：等待执行、running：执行中、fail：执行不通过、success：执行通过、skip：跳过、error：报错")
    case_data = db.Column(LONGTEXT, default='{}', comment="用例的数据")
    summary = db.Column(db.Text(), default='{}', comment="用例的报告统计")
    error_msg = db.Column(db.Text(), default='', comment="用例错误信息")

    @staticmethod
    def getsummary_template():
        return {
            "success": 'skip',
            "case_id": None,
            "project_id": None,
            "stat": {
                'total': 1,  # 初始化的时候给个1，方便用户查看运行中的报告，后续会在流程中更新为实际的total
                'failures': 0,
                'errors': 0,
                'skipped': 0,
                'expectedFailures': 0,
                'unexpectedSuccesses': 0,
                'successes': 0
            },
            "time": {
                'start_at': '',
                'start_date': '',
                'duration': 0
            }
        }

    @classmethod
    def get_case_list(cls, report_id, get_summary):
        """ 根据报告id，获取用例列表，性能考虑，只查关键字段 """
        field_title = ["id", "from_id", "name", "result", "summary", "case_data", "error_msg"]
        query_fields = [cls.id, cls.from_id, cls.name, cls.result]
        if get_summary is True:
            query_fields.append(cls.summary)
            query_fields.append(cls.case_data)
            query_fields.append(cls.error_msg)

        # [(1, '用例1', 'running')]
        query_data = cls.query.filter(cls.report_id == report_id).with_entities(*query_fields).all()

        # [{ 'id': 1, 'name': '用例1', 'result': 'running' }]
        return [dict(zip(field_title, d)) for d in query_data]

    @classmethod
    def delete_by_report(cls, report_id):
        """ 根据报告id批量删除 """
        with db.auto_commit():
            cls.query.filter(cls.report_id == report_id).delete()

    def update_test_data(self, case_data, summary=None):
        """ 更新测试数据 """
        update_dict = {"case_data": case_data}
        if summary:
            update_dict["summary"] = summary
        self.update(update_dict)

    def update_test_result(self, result, case_data, summary, error_msg):
        """ 更新测试状态 """
        update_dict = {"result": result}
        if case_data:
            update_dict["case_data"] = case_data
        if summary:
            update_dict["summary"] = summary
        if error_msg:
            update_dict["error_msg"] = error_msg
        self.update(update_dict)

    def test_is_running(self, case_data=None, summary=None):
        self.update_test_result("running", case_data, summary, error_msg=None)

    def test_is_fail(self, case_data=None, summary=None):
        self.update_test_result("fail", case_data, summary, error_msg=None)

    def test_is_success(self, case_data=None, summary=None):
        self.update_test_result("success", case_data, summary, error_msg=None)

    def test_is_skip(self, case_data=None, summary=None):
        self.update_test_result("skip", case_data, summary, error_msg=None)

    def test_is_error(self, case_data=None, summary=None, error_msg=None):
        self.update_test_result("error", case_data, summary, error_msg)


class BaseReportStep(BaseModel):
    """ 步骤执行记录基类表 """
    __abstract__ = True

    name = db.Column(db.String(128), nullable=True, comment="测试步骤名称")
    from_id = db.Column(db.Integer(), comment="步骤对应的元素/接口id")
    case_id = db.Column(db.Integer(), default=None, comment="步骤所在的用例id")
    step_id = db.Column(db.Integer(), default=None, comment="步骤id")
    report_case_id = db.Column(db.Integer(), default=None, comment="用例数据id")
    report_id = db.Column(db.Integer(), index=True, comment="测试报告id")
    process = db.Column(db.String(128), default='waite',
                        comment="步骤执行进度，waite：等待解析、parse: 解析数据、before：前置条件、after：后置条件、run：执行测试、extract：数据提取、validate：断言")
    result = db.Column(db.String(128), default='waite',
                       comment="步骤测试结果，waite：等待执行、running：执行中、fail：执行不通过、success：执行通过、skip：跳过、error：报错")
    step_data = db.Column(LONGTEXT, default='{}', comment="步骤的数据")
    summary = db.Column(db.Text(),
                        default='{"response_time_ms": 0, "elapsed_ms": 0, "content_size": 0, "request_at": "", "response_at": ""}',
                        comment="步骤的统计")

    @classmethod
    def get_step_list(cls, report_case_id, get_summary):
        """ 获取步骤列表，性能考虑，只查关键字段 """
        field_title = ["id", "case_id", "name", "process", "result", "summary"]
        query_fields = [cls.id, cls.case_id, cls.name, cls.process, cls.result]

        if get_summary is True:
            query_fields.append(cls.summary)

        # [(1, '步骤1', 'before', 'running')]
        query_data = cls.query.filter(cls.report_case_id == report_case_id).with_entities(*query_fields).all()

        # [{ 'id': 1, 'name': '步骤1', 'process': 'before', 'result': 'success' }]
        return [dict(zip(field_title, d)) for d in query_data]

    @classmethod
    def delete_by_report(cls, report_id):
        """ 根据报告id批量删除 """
        with db.auto_commit():
            cls.query.filter(cls.report_id == report_id).delete()

    def update_test_data(self, step_data, summary=None):
        """ 更新测试数据 """
        update_dict = {"step_data": step_data}
        if summary:
            update_dict["summary"] = summary
        self.update(update_dict)

    def update_test_result(self, result, step_data):
        """ 更新测试状态 """
        update_dict = {"result": result}
        if step_data:
            update_dict["step_data"] = step_data
        self.update(update_dict)

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

    def update_test_process(self, process, step_data):
        """ 更新数据和执行进度 """
        update_dict = {"process": process}
        if step_data:
            update_dict["step_data"] = step_data
        self.update(update_dict)

    def test_is_start_parse(self, step_data=None):
        self.update_test_process("parse", step_data)

    def test_is_start_before(self, step_data=None):
        self.update_test_process("before", step_data)

    def test_is_start_running(self, step_data=None):
        self.update_test_process("run", step_data)

    def test_is_start_extract(self, step_data=None):
        self.update_test_process("extract", step_data)

    def test_is_start_after(self, step_data=None):
        self.update_test_process("after", step_data)

    def test_is_start_validate(self, step_data=None):
        self.update_test_process("validate", step_data)


class ConfigType(BaseModel):
    """ 配置类型表 """

    __tablename__ = "config_type"
    __table_args__ = {"comment": "配置类型表"}

    name = db.Column(db.String(128), nullable=True, unique=True, comment="字段名")
    desc = db.Column(db.Text(), comment="描述")

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.create_user.data:
            filters.append(cls.create_user == form.create_user.data)
        if form.name.data:
            filters.append(cls.name.like(f'%{form.name.data}%'))

        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.id.desc()
        )


class Config(BaseModel):
    """ 配置表 """

    __tablename__ = "config_config"
    __table_args__ = {"comment": "配置表"}

    name = db.Column(db.String(128), nullable=True, unique=True, comment="字段名")
    value = db.Column(db.Text(), nullable=True, comment="字段值")
    type = db.Column(db.Integer(), nullable=True, comment="配置类型")
    desc = db.Column(db.Text(), comment="描述")

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.queryType.data:
            filters.append(cls.type == form.queryType.data)
        if form.create_user.data:
            filters.append(cls.create_user == form.create_user.data)
        if form.name.data:
            filters.append(cls.name.like(f'%{form.name.data}%'))
        if form.value.data:
            filters.append(cls.value.like(f'%{form.value.data}%'))

        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.id.desc()
        )

    @classmethod
    def get_kym(cls):
        """ 获取kym配置项 """
        return cls.loads(cls.get_first(name="kym").value)

    @classmethod
    def get_http_methods(cls):
        """ 配置的http请求方法 """
        return cls.get_first(name="http_methods").value

    @classmethod
    def get_default_diff_message_send_addr(cls):
        """ 配置的对比结果通知地址 """
        return cls.get_first(name="default_diff_message_send_addr").value

    @classmethod
    def get_callback_webhook(cls):
        return cls.get_first(name="callback_webhook").value

    @classmethod
    def get_call_back_response(cls):
        return cls.get_first(name="call_back_response").value

    @classmethod
    def get_data_source_callback_addr(cls):
        return cls.get_first(name="data_source_callback_addr").value

    @classmethod
    def get_data_source_callback_token(cls):
        return cls.get_first(name="data_source_callback_token").value

    @classmethod
    def get_run_time_error_message_send_addr(cls):
        return cls.get_first(name="run_time_error_message_send_addr").value

    @classmethod
    def get_request_time_out(cls):
        return cls.get_first(name="request_time_out").value

    @classmethod
    def get_wait_time_out(cls):
        return cls.get_first(name="wait_time_out").value

    @classmethod
    def get_suite_type_list(cls, suite_type="api"):
        return cls.loads(cls.get_first(name=f"{suite_type}_suite_list").value)

    @classmethod
    def get_report_host(cls):
        return cls.get_first(name="report_host").value

    @classmethod
    def get_func_error_addr(cls):
        return cls.get_first(name="func_error_addr").value

    @classmethod
    def get_diff_api_addr(cls):
        return cls.get_first(name="diff_api_addr").value

    @classmethod
    def get_api_report_addr(cls):
        return cls.get_first(name="api_report_addr").value

    @classmethod
    def get_web_ui_report_addr(cls):
        return cls.get_first(name="web_ui_report_addr").value

    @classmethod
    def get_app_ui_report_addr(cls):
        return cls.get_first(name="app_ui_report_addr").value

    @classmethod
    def get_appium_new_command_timeout(cls):
        return cls.get_first(name="appium_new_command_timeout").value

    @classmethod
    def get_find_element_option(cls):
        return cls.loads(cls.get_first(name="find_element_option").value)

    @classmethod
    def get_pagination_size(cls):
        return cls.loads(cls.get_first(name="pagination_size").value)

    @classmethod
    def get_ui_report_addr(cls):
        return cls.get_first(name="ui_report_addr").value

    @classmethod
    def get_run_type(cls):
        return cls.loads(cls.get_first(name="run_type").value)

    @classmethod
    def get_sync_mock_data(cls):
        return cls.loads(cls.get_first(name="sync_mock_data").value)

    @classmethod
    def get_save_func_permissions(cls):
        return cls.get_first(name="save_func_permissions").value

    @classmethod
    def get_call_back_msg_addr(cls):
        return cls.get_first(name="call_back_msg_addr").value


class FuncErrorRecord(BaseModel):
    """ 自定义函数执行错误记录表 """
    __tablename__ = "func_error_record"
    __table_args__ = {"comment": "自定义函数执行错误记录表"}

    name = db.Column(db.String(255), nullable=True, comment="错误title")
    detail = db.Column(db.Text(), default="", comment="错误详情")

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.name.data:
            filters.append(FuncErrorRecord.name.like(f"%{form.name.data}%"))
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.created_time.desc())


class SaveRequestLog(BaseModel):
    """ 记录请求表 """
    __abstract__ = True

    ip = db.Column(db.String(256), nullable=True, comment="访问来源ip")
    url = db.Column(db.String(256), nullable=True, comment="请求地址")
    method = db.Column(db.String(10), nullable=True, comment="请求方法")
    headers = db.Column(db.Text, nullable=True, comment="头部参数")
    params = db.Column(db.String(256), nullable=True, comment="查询字符串参数")
    data_form = db.Column(db.Text, nullable=True, comment="form_data参数")
    data_json = db.Column(db.Text, nullable=True, comment="json参数")

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if hasattr(form, 'url') and form.url.data:
            filters.append(cls.url == form.url.data)
        if hasattr(form, 'method') and form.method.data:
            filters.append(cls.method == form.method.data)
        if hasattr(form, 'request_user') and form.request_user.data:
            filters.append(cls.create_user == form.request_user.data)
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.created_time.desc()
        )
