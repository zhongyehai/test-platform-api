# -*- coding: utf-8 -*-

from datetime import datetime
from werkzeug.exceptions import abort

from flask import g, current_app as app
from flask_sqlalchemy import SQLAlchemy as _SQLAlchemy, BaseQuery, Pagination
from sqlalchemy import MetaData
from contextlib import contextmanager

from utils.jsonUtil import JsonUtil
from utils.parse import parse_list_to_dict, update_dict_to_list


class SQLAlchemy(_SQLAlchemy):
    """ 自定义SQLAlchemy并继承SQLAlchemy """

    @contextmanager
    def auto_commit(self):
        """ 自定义上下文处理数据提交和异常回滚 """
        try:
            yield
            self.session.commit()  # 提交到数据库，修改数据
        except Exception as error:
            db.session.rollback()  # 事务如果发生异常，执行回滚
            raise error

    def execute_query_sql(self, sql):
        """ 执行原生查询sql，并返回字典 """
        res = self.session.execute(sql).fetchall()
        return dict(res) if res else {}


class Qeury(BaseQuery):
    """ 重写query方法，使其默认加上status=0 """

    def filter_by(self, **kwargs):
        """ 如果传过来的参数中不含is_delete，则默认加一个is_delete参数，状态为0 查询有效的数据"""
        # kwargs.setdefault('is_delete', 0)
        return super(Qeury, self).filter_by(**kwargs)

    def paginate(self, page=1, per_page=20, error_out=True, max_per_page=None):
        """ 重写分页器，把页码和页数强制转成int，解决服务器吧int识别为str导致分页报错的问题"""
        page, per_page = int(page) or app.conf['page']['pageNum'], int(per_page) or app.conf['page']['pageSize']
        if max_per_page is not None:
            per_page = min(per_page, max_per_page)
        items = self.limit(per_page).offset((page - 1) * per_page).all()
        if not items and page != 1 and error_out:
            abort(404)
        total = self.order_by(None).count()
        return Pagination(self, page, per_page, total, items)


# 由于数据库迁移的时候，不兼容约束关系的迁移，下面是百度出的解决方案
naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
db = SQLAlchemy(
    query_class=Qeury,  # 指定使用修改过后的Qeury
    metadata=MetaData(naming_convention=naming_convention),
    use_native_unicode='utf8')


class BaseModel(db.Model, JsonUtil):
    """ 基类模型 """
    __abstract__ = True

    # is_delete = db.Column(db.SmallInteger, default=0, comment='通过更改状态来判断记录是否被删除, 0数据有效, 1数据已删除')
    id = db.Column(db.Integer(), primary_key=True, comment='主键，自增')
    created_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='修改时间')
    create_user = db.Column(db.Integer(), nullable=True, default=1, comment='创建数据的用户id')
    update_user = db.Column(db.Integer(), nullable=True, default=1, comment='修改数据的用户id')

    # 需要做序列化和反序列化的字段
    args = [
        'headers', 'variables', 'func_files',
        'params', 'data_form', 'data_json', 'extracts', 'validates', "data_driver",
        'set_ids', 'case_ids',
        'cookies', 'session_storage', 'local_storage',
        'kym', 'task_item',
    ]

    @property
    def str_created_time(self):
        return datetime.strftime(self.created_time, "%Y-%m-%d %H:%M:%S")

    @property
    def str_update_time(self):
        return datetime.strftime(self.update_time, "%Y-%m-%d %H:%M:%S")

    def create(self, attrs_dict: dict, *args):
        """ 插入数据，若指定了字段，则把该字段的值转为json """
        if not args:
            args = self.args

        with db.auto_commit():
            for key, value in attrs_dict.items():
                if hasattr(self, key) and key != 'id':
                    setattr(self, key, self.dumps(value) if key in args else value)

            # 如果是执行初始化脚本，获取不到g，try一下
            try:
                setattr(self, 'create_user', g.user_id)
                setattr(self, 'update_user', g.user_id)
            except Exception as error:
                pass
            db.session.add(self)
        return self

    def update(self, attrs_dict: dict, *args):
        """ 修改数据，若指定了字段，则把该字段的值转为json """
        # 如果是执行初始化脚本，获取不到g，try一下
        if not args:
            args = self.args

        with db.auto_commit():
            for key, value in attrs_dict.items():
                if hasattr(self, key) and key not in ['id', 'num']:
                    setattr(self, key, self.dumps(value) if key in args else value)
            try:
                setattr(self, 'update_user', g.user_id)
            except Exception as error:
                pass

    def insert_or_update(self, attrs_dict: dict, *args, **kwargs):
        """ 创建或更新 """
        old_data = self.get_first(**kwargs)
        if old_data:
            old_data.update(attrs_dict, *args)
            return old_data
        return self.create(attrs_dict, *args)

    def delete(self):
        """ 删除单条数据 """
        with db.auto_commit():
            db.session.delete(self)

    # def delete(self):
    #     """ 软删除 """
    #     self.is_delete = 1

    def is_create_user(self, user_id):
        """ 判断当前传进来的id为数据创建者 """
        return self.create_user == user_id

    @classmethod
    def get_first(cls, **kwargs):
        """ 获取第一条数据 """
        return cls.query.filter_by(**kwargs).first()

    @classmethod
    def get_all(cls, **kwargs):
        """ 获取全部数据 """
        return cls.query.filter_by(**kwargs).all()

    @classmethod
    def get_filter_by(cls, **kwargs):
        """ 获取filter_by对象 """
        return cls.query.filter_by(**kwargs)

    @classmethod
    def get_filter(cls, **kwargs):
        """ 获取filter对象 """
        return cls.query.filter(**kwargs)

    @classmethod
    def change_sort(cls, id_list, page_num, page_size):
        """ 批量修改排序 """
        with db.auto_commit():
            for index, data_id in enumerate(id_list):
                cls.get_first(id=data_id).num = (page_num - 1) * page_size + index

    @classmethod
    def get_max_num(cls, **kwargs):
        """ 返回 model 表中**kwargs筛选条件下的已存在编号num的最大值 """
        max_num_data = cls.get_filter_by(**kwargs).order_by(cls.num.desc()).first()
        return max_num_data.num if max_num_data else 0

    @classmethod
    def get_insert_num(cls, **kwargs):
        """ 返回 model 表中**kwargs筛选条件下的已存在编号num的最大值 + 1 """
        return cls.get_max_num(**kwargs) + 1

    def to_dict(self, to_dict: list = [], pop_list: list = [], filter_list: list = []):
        """ 自定义序列化器，把模型的每个字段转为key，方便返回给前端
        to_dict: 要转为字典的字段
        pop_list: 序列化时忽略的字段
        filter_list: 仅要序列化的字段
        当 pop_list 与 filter_list 同时包含同一个字段时，以 filter_list 为准
        """
        if not to_dict:
            to_dict = self.args

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
        if column_name == 'created_time':
            return self.str_created_time
        elif column_name == 'update_time':
            return self.str_update_time
        else:
            data = getattr(self, column_name)
            # 字段有值且在要转json的列表里面，就转为json
            return self.loads(data) if data and column_name in to_dict_list else data

    @classmethod
    def pagination(cls, page_num, page_size, filters: list = [], order_by=None):
        """ 分页, 如果没有传页码和页数，则根据查询条件获取全部数据
        filters：过滤条件
        page_num：页数
        page_size：页码
        order_by: 排序规则
        """
        if page_num and page_size:
            query_obj = cls.query.filter(*filters).order_by(order_by) if filters else cls.query.order_by(order_by)
            result = query_obj.paginate(page_num, per_page=page_size, error_out=False)
            return {"total": result.total, "data": [model.to_dict() for model in result.items]}
        all_data = cls.query.filter(*filters).order_by(order_by).all()
        return {"total": len(all_data), "data": [model.to_dict() for model in all_data]}


class ApschedulerJobs(BaseModel):
    """ apscheduler任务表，防止执行数据库迁移的时候，把定时任务删除了 """
    __tablename__ = 'apscheduler_jobs'
    id = db.Column(db.String(191), primary_key=True, nullable=False)
    next_run_time = db.Column(db.String(128), comment='任务下一次运行时间')
    job_state = db.Column(db.LargeBinary(length=(2 ** 32) - 1), comment='任务详情')


class BaseProject(BaseModel):
    """ 服务基类表 """
    __abstract__ = True

    name = db.Column(db.String(255), nullable=True, comment='服务名称')
    manager = db.Column(db.Integer(), nullable=True, default=1, comment='服务管理员id，默认为admin')
    test = db.Column(db.String(255), default='', comment='测试环境域名')

    def is_not_manager(self):
        """ 判断用户非服务负责人 """
        return g.user_id != self.manager

    @classmethod
    def is_not_manager_id(cls, project_id):
        """ 判断当前用户非当前数据的负责人 """
        return cls.get_first(id=project_id).manager != g.user_id

    @classmethod
    def is_manager_id(cls, project_id):
        """ 判断当前用户为当前数据的负责人 """
        return cls.get_first(id=project_id).manager == g.user_id

    @classmethod
    def is_admin(cls, ):
        """ 角色为2，为管理员 """
        return g.user_role == 2

    @classmethod
    def is_not_admin(cls):
        """ 角色不为2，非管理员 """
        return not cls.is_admin()

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
        if form.name.data:
            filters.append(cls.name.like(f'%{form.name.data}%'))
        if form.projectId.data:
            filters.append(cls.id == form.projectId.data)
        if form.manager.data:
            filters.append(cls.manager == form.manager.data)
        if form.create_user.data:
            filters.append(cls.create_user == form.create_user.data)
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.created_time.desc())


class BaseProjectEnv(BaseModel):
    """ 服务环境基类表 """
    __abstract__ = True

    env = db.Column(db.String(10), nullable=True, comment='所属环境')
    host = db.Column(db.String(255), default='', comment='域名')
    func_files = db.Column(db.Text(), nullable=True, default='[]', comment='引用的函数文件')
    variables = db.Column(db.Text(), default='[{"key": "", "value": "", "remark": ""}]', comment='服务的公共变量')
    project_id = db.Column(db.Integer(), nullable=True, comment='所属的服务id')

    @classmethod
    def synchronization(cls, from_env, to_env_list: list, filed_list: list):
        """ 把当前环境同步到其他环境
        from_env: 从哪个环境
        to_env_list: 同步到哪些环境
        filed_list: 指定要同步的字段列表
        """

        # 同步数据来源解析
        from_env_dict = {}
        for filed in filed_list:
            filed_data = cls.loads(getattr(from_env, filed))
            from_env_dict[filed] = parse_list_to_dict(filed_data) if filed != 'func_files' else filed_data

        # 已同步数据的容器
        synchronization_result = {}

        # 同步至指定环境
        for to_env in to_env_list:
            to_env_data = cls.get_first(project_id=from_env.project_id, env=to_env)
            new_env_data = {}
            for filed in filed_list:
                from_data, to_data = from_env_dict[filed], cls.loads(getattr(to_env_data, filed))
                new_env_data[filed] = cls.dumps(
                    update_dict_to_list(from_data, to_data) if filed != 'func_files' else list(set(to_data + from_data))
                )

            to_env_data.update(new_env_data)  # 同步环境
            synchronization_result[to_env] = to_env_data.to_dict()  # 保存已同步的环境数据
        return synchronization_result


class BaseModule(BaseModel):
    """ 模块基类表 """
    __abstract__ = True

    name = db.Column(db.String(255), nullable=True, comment='模块名')
    num = db.Column(db.Integer(), nullable=True, comment='模块在对应服务下的序号')
    level = db.Column(db.Integer(), nullable=True, default=2, comment='模块级数')
    parent = db.Column(db.Integer(), nullable=True, default=None, comment='上一级模块id')

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

    num = db.Column(db.Integer(), nullable=True, comment='序号')
    name = db.Column(db.String(255), nullable=True, comment='名称')
    desc = db.Column(db.Text(), default='', nullable=True, comment='描述')


class BaseCaseSet(BaseModel):
    """ 用例集基类表 """
    __abstract__ = True

    name = db.Column(db.String(255), nullable=True, comment='用例集名称')
    num = db.Column(db.Integer(), nullable=True, comment='用例集在对应服务下的序号')
    level = db.Column(db.Integer(), nullable=True, default=2, comment='用例集级数')
    parent = db.Column(db.Integer(), nullable=True, default=None, comment='上一级用例集id')

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.projectId.data:
            filters.append(cls.project_id == form.projectId.data)
        if form.name.data:
            filters.append(cls.name == form.name.data)
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.num.asc()
        )


class BaseCase(BaseModel):
    """ 用例基类表 """

    __abstract__ = True

    num = db.Column(db.Integer(), nullable=True, comment='用例序号')
    name = db.Column(db.String(255), nullable=True, comment='用例名称')
    desc = db.Column(db.Text(), comment='用例描述')
    is_run = db.Column(db.Boolean(), default=True, comment='是否执行此用例，True执行，False不执行，默认执行')
    run_times = db.Column(db.Integer(), default=1, comment='执行次数，默认执行1次')
    func_files = db.Column(db.Text(), comment='用例需要引用的函数list')
    variables = db.Column(db.Text(), comment='用例级的公共参数')

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.setId.data:
            filters.append(cls.set_id == form.setId.data)
        if form.name.data:
            filters.append(cls.name.like(f'%{form.name.data}%'))
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.num.asc()
        )


class BaseStep(BaseModel):
    """ 测试步骤基类表 """

    __abstract__ = True

    num = db.Column(db.Integer(), nullable=True, comment='步骤序号，执行顺序按序号来')
    is_run = db.Column(db.Boolean(), default=True, comment='是否执行此步骤，True执行，False不执行，默认执行')
    run_times = db.Column(db.Integer(), default=1, comment='执行次数，默认执行1次')

    name = db.Column(db.String(255), comment='步骤名称')
    up_func = db.Column(db.Text(), default='', comment='步骤执行前的函数')
    down_func = db.Column(db.Text(), default='', comment='步骤执行后的函数')

    data_driver = db.Column(db.Text(), default='[]', comment='数据驱动，若此字段有值，则走数据驱动的解析')
    quote_case = db.Column(db.String(5), default='', comment='引用用例的id')


class BaseTask(BaseModel):
    """ 定时任务基类表 """
    __abstract__ = True

    num = db.Column(db.Integer(), comment='任务序号')
    name = db.Column(db.String(255), comment='任务名称')
    env = db.Column(db.String(10), default='test', comment='运行环境')
    case_ids = db.Column(db.Text(), comment='用例id')
    task_type = db.Column(db.String(10), default='cron', comment='定时类型')
    cron = db.Column(db.String(255), nullable=True, comment='cron表达式')
    is_send = db.Column(db.String(10), comment='是否发送报告，1.不发送、2.始终发送、3.仅用例不通过时发送')
    send_type = db.Column(db.String(10), default='webhook', comment='测试报告发送类型，webhook，email，all')
    we_chat = db.Column(db.Text(), comment='企业微信机器人地址')
    ding_ding = db.Column(db.Text(), comment='钉钉机器人地址')
    email_server = db.Column(db.String(255), comment='发件邮箱服务器')
    email_from = db.Column(db.String(255), comment='发件人邮箱')
    email_pwd = db.Column(db.String(255), comment='发件人邮箱密码')
    email_to = db.Column(db.Text(), comment='收件人邮箱')
    status = db.Column(db.Integer(), default=0, comment='任务的运行状态，0：禁用中、1：启用中，默认0')
    is_async = db.Column(db.Integer(), default=1, comment='任务的运行机制，0：单线程，1：多线程，默认1')
    set_ids = db.Column(db.Text(), comment='用例集id')

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

    name = db.Column(db.String(128), nullable=True, comment='测试报告名称')
    status = db.Column(db.String(10), nullable=True, default='未读', comment='阅读状态，已读、未读')
    is_passed = db.Column(db.Integer, default=1, comment='是否全部通过，1全部通过，0有报错')
    performer = db.Column(db.String(16), nullable=True, comment='执行者')
    run_type = db.Column(db.String(10), default='task', nullable=True, comment='报告类型，task/case/api')
    is_done = db.Column(db.Integer, default=0, comment='是否执行完毕，1执行完毕，0执行中')

    @classmethod
    def get_new_report(cls, name, run_type, performer, create_user, project_id):
        with db.auto_commit():
            report = cls()
            report.name = name
            report.run_type = run_type
            report.performer = performer
            report.create_user = create_user
            report.project_id = project_id
            db.session.add(report)
        return report

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
            order_by=cls.created_time.desc()
        )
