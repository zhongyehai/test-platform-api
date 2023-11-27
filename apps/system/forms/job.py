from typing import Optional

from pydantic import Field, field_validator

from ...base_form import BaseForm, PaginationForm
from ..model_factory import ApschedulerJobs, JobRunLog


class GetJobRunLogList(PaginationForm):
    func_name: Optional[str] = Field(None, title="方法名")

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = []
        if self.func_name:
            filter_list.append(JobRunLog.func_name == self.func_name)
        return filter_list


class GetJobLogForm(BaseForm):
    """ 获取job信息 """
    id: int = Field(..., title="数据id")

    @field_validator("id")
    def validate_id(cls, value):
        job_log = cls.validate_data_is_exist("数据不存在", JobRunLog, id=value)
        setattr(cls, "job_log", job_log)
        return value


class GetJobForm(BaseForm):
    """ 获取job信息 """
    task_code: str = Field(..., title="job code")

    @field_validator("task_code")
    def validate_task_code(cls, value):
        job = cls.validate_data_is_exist("数据不存在", ApschedulerJobs, task_code=value)
        setattr(cls, "job", job)
        return value


class EnableJobForm(BaseForm):
    """ 新增job信息 """
    func_name: str = Field(..., title="job方法")


class DisableJobForm(EnableJobForm):
    """ 禁用job """


class RunJobForm(EnableJobForm):
    """ 执行job """
