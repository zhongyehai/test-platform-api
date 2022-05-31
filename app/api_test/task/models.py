# -*- coding: utf-8 -*-
from app.baseModel import BaseModel, db


class ApiTask(BaseModel):
    """ 测试任务表 """
    __tablename__ = 'api_test_task'
    num = db.Column(db.Integer(), comment='任务序号')
    name = db.Column(db.String(255), comment='任务名称')
    choice_host = db.Column(db.String(10), default='test', comment='运行环境')
    case_id = db.Column(db.Text(), comment='用例id')
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
    status = db.Column(db.String(10), default=u'禁用中', comment='任务的运行状态，默认是禁用中')

    is_async = db.Column(db.Integer(), default=1, comment='任务的运行机制，0：单线程，1：多线程，默认1')

    set_id = db.Column(db.Text(), comment='用例集id')

    project_id = db.Column(db.Integer, db.ForeignKey('api_test_project.id'), comment='所属的服务id')
    project = db.relationship('ApiProject', backref='tasks')

    def to_dict(self, *args, **kwargs):
        return super(ApiTask, self).to_dict(to_dict=['set_id', 'case_id'])

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


class ApschedulerJobs(BaseModel):
    """ apscheduler任务表，防止执行数据库迁移的时候，把定时任务删除了 """
    __tablename__ = 'apscheduler_jobs'
    id = db.Column(db.String(191), primary_key=True, nullable=False)
    next_run_time = db.Column(db.String(128), comment='任务下一次运行时间')
    job_state = db.Column(db.LargeBinary(length=(2 ** 32) - 1), comment='任务详情')
