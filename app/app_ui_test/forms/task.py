# -*- coding: utf-8 -*-
from wtforms import StringField, IntegerField
from wtforms.validators import ValidationError, DataRequired
from crontab import CronTab

from app.baseForm import BaseForm
from app.config.models.config import Config
from app.app_ui_test.models.task import AppUiTask as Task
from app.app_ui_test.models.project import AppUiProject as Project
from app.app_ui_test.models.env import AppUiRunServer as Server, AppUiRunPhone as Phone


class AddTaskForm(BaseForm):
    """ 添加定时任务的校验 """
    project_id = IntegerField(validators=[DataRequired("请选择项目")])
    set_ids = StringField()
    case_ids = StringField()
    env = StringField(validators=[DataRequired("请选择要运行的环境")])
    name = StringField(validators=[DataRequired("任务名不能为空")])
    we_chat = StringField()
    ding_ding = StringField()
    is_send = StringField(validators=[DataRequired("请选择是否发送报告")])
    send_type = StringField()
    email_server = StringField()
    email_to = StringField()
    email_from = StringField()
    email_pwd = StringField()
    cron = StringField()
    num = StringField()
    call_back = StringField()
    is_async = IntegerField()

    def validate_is_send(self, field):
        """ 发送报告类型 1.不发送、2.始终发送、3.仅用例不通过时发送 """
        if field.data in ["2", "3"]:
            if self.send_type.data == "we_chat":
                self.validate_data_is_true('选择了要通过机器人发送报告，则webhook地址必填', self.we_chat.data)
            elif self.send_type.data == "ding_ding":
                self.validate_data_is_true('选择了要通过机器人发送报告，则webhook地址必填', self.ding_ding.data)
            elif self.send_type.data == "email":
                self.validate_email(
                    self.email_server.data, self.email_from.data, self.email_pwd.data, self.email_to.data
                )
            elif self.send_type.data == "all":
                self.validate_data_is_true(
                    '选择了要通过机器人发送报告，则webhook地址必填', self.ding_ding.data or self.we_chat.data
                )
                self.validate_email(
                    self.email_server.data, self.email_from.data, self.email_pwd.data, self.email_to.data
                )

    def validate_cron(self, field):
        """ 校验cron格式 """
        try:
            if len(field.data.strip().split(" ")) == 6:
                field.data += " *"
            CronTab(field.data)
        except Exception as error:
            raise ValidationError(f"时间配置【{field.data}】错误，需为cron格式, 请检查")

    def validate_name(self, field):
        """ 校验任务名不重复 """
        self.validate_data_is_not_exist(
            f"当前项目中，任务名【{field.data}】已存在",
            Task,
            project_id=self.project_id.data,
            name=field.data
        )


class HasTaskIdForm(BaseForm):
    """ 校验任务id已存在 """
    id = IntegerField(validators=[DataRequired("任务id必传")])

    def validate_id(self, field):
        """ 校验id存在 """
        task = self.validate_data_is_exist(f"任务id【{field.data}】不存在", Task, id=field.data)
        setattr(self, "task", task)


class DisableTaskIdForm(HasTaskIdForm):
    """ 禁用任务 """

    def validate_id(self, field):
        """ 校验id存在 """
        task = self.validate_data_is_exist(f"任务id【{field.data}】不存在", Task, id=field.data)
        setattr(self, "task", task)

        self.validate_data_is_true(f"任务【{task.name}】的状态不为启用中", task.is_enable())


class RunTaskForm(HasTaskIdForm):
    """ 运行任务 """
    env = StringField()
    is_async = IntegerField()
    trigger_type = StringField()  # pipeline 代表是流水线触发，跑完过后会发送测试报告
    extend = StringField()  # 运维传过来的扩展字段，接收的什么就返回什么
    server_id = IntegerField(validators=[DataRequired("请选择执行服务器")])
    phone_id = IntegerField(validators=[DataRequired("请选择执行手机")])

    def validate_env(self, field):
        """ 检验环境 """
        if field.data:
            self.validate_data_is_true(f"环境【{field.data}】不存在", field.data.lower() in Config.get_run_test_env())

    def validate_server_id(self, field):
        """ 校验服务id存在 """
        server = self.validate_data_is_exist(f"id为【{field.data}】的服务器不存在", Server, id=field.data)
        setattr(self, "server", server)

    def validate_phone_id(self, field):
        """ 校验手机id存在 """
        phone = self.validate_data_is_exist(f"id为【{field.data}】的手机不存在", Phone, id=field.data)
        setattr(self, "phone", phone)


class EditTaskForm(AddTaskForm, HasTaskIdForm):
    """ 编辑任务 """

    def validate_id(self, field):
        """ 校验id存在 """
        task = self.validate_data_is_exist(f"任务id【{field.data}】不存在", Task, id=field.data)
        self.validate_data_is_true(f"任务【{task.name}】的状态不为禁用中，请先禁用再修改", task.is_disable())
        setattr(self, "task", task)

    def validate_name(self, field):
        """ 校验任务名不重复 """
        self.validate_data_is_not_repeat(
            f"当前项目中，任务名【{field.data}】已存在",
            Task,
            self.id.data,
            project_id=self.project_id.data,
            name=field.data
        )


class GetTaskListForm(BaseForm):
    """ 获取任务列表 """
    projectId = IntegerField(validators=[DataRequired("项目id必传")])
    pageNum = IntegerField()
    pageSize = IntegerField()


class DeleteTaskIdForm(HasTaskIdForm):
    """ 删除任务 """

    def validate_id(self, field):
        """ 校验id存在 """
        task = self.validate_data_is_exist(f"任务id【{field.data}】不存在", Task, id=field.data)
        self.validate_data_is_true(f"请先禁用任务【{task.name}】", task.is_disable())
        self.validate_data_is_true(f"不能删除别人的数据【{task.name}】", Project.is_can_delete(task.project_id, task))
        setattr(self, "task", task)
