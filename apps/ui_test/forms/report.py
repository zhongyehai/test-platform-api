from typing import Optional, List, Union
from sqlalchemy import func
from sqlalchemy.dialects.mysql import JSON

from pydantic import Field, field_validator

from ...base_form import BaseForm, PaginationForm, required_str_field
from ...enums import TriggerTypeEnum
from ...system.models.user import User
from ...assist.models.hits import Hits
from ..model_factory import WebUiReport as Report, WebUiReportStep as ReportStep, WebUiReportCase as ReportCase


class GetReportListForm(PaginationForm):
    """ 查询报告 """
    project_id: int = Field(..., title="服务id")
    name: Optional[str] = Field(None, title="报告名")
    create_user: Optional[Union[int, str]] = Field(None, title="创建人")
    trigger_type: Optional[str] = Field(None, title="触发类型")
    run_type: Optional[str] = Field(None, title="执行类型")
    is_passed: Optional[int] = Field(None, title="是否通过")
    run_env: Optional[str] = Field(None, title="运行环境")
    trigger_id: Optional[int] = Field(None, title="运行数据id", description="接口id、用例id、任务id")

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = [Report.project_id == self.project_id]
        if self.create_user:
            filter_list.append(Report.create_user == self.create_user)
        if self.trigger_type:
            filter_list.append(Report.trigger_type == self.trigger_type)
        if self.run_type:
            filter_list.append(Report.run_type == self.run_type)
        if self.is_passed:
            filter_list.append(Report.is_passed == self.is_passed)
        if self.env_list:
            filter_list.append(Report.env == self.run_env)
        if self.name:
            filter_list.append(Report.name.like(f'%{self.name}%'))
        if self.trigger_id:  # 只查具体数据的测试报告
            filter_list.append(func.cast(Report.trigger_id, JSON) == func.json_array(self.trigger_id))  # 相等
        return filter_list


class GetReportForm(BaseForm):
    """ 获取报告 """
    id: int = Field(..., title="报告id")

    @field_validator("id")
    def validate_id(cls, value):
        report = cls.validate_data_is_exist("报告不存在", Report, id=value)
        setattr(cls, "report", report)
        return value


class DeleteReportForm(BaseForm):
    """ 删除报告 """
    id_list: List[int] = required_str_field(title="报告id list")

    @field_validator("id_list")
    def validate_id_list(cls, value):
        if User.is_admin():
            setattr(cls, 'report_id_list', value)
            return value
        query_list = Report.db.session.query(Report.id).filter(
            Report.id.in_(value),
            Report.trigger_type.notin_([TriggerTypeEnum.pipeline.value, TriggerTypeEnum.cron.value]),
            Hits.report_id.notin_(value)
        ).all()
        setattr(cls, "report_id_list", [query[0] for query in query_list])
        return value


class GetReportCaseSuiteListForm(PaginationForm):
    """ 获取报告用例集列表 """
    report_id: int = Field(..., title="报告id")


class GetReportCaseListForm(PaginationForm):
    """ 获取报告用例列表 """
    report_id: int = Field(..., title="报告id")
    suite_id: Optional[int] = Field(None, title="用例集id")


class GetReportCaseForm(BaseForm):
    """ 获取报告步骤数据 """
    id: int = Field(..., title="报告用例id")

    @field_validator("id")
    def validate_id(cls, value):
        report_case = cls.validate_data_is_exist("数据不存在", ReportCase, id=value)
        setattr(cls, "report_case", report_case)
        return value


class GetReportStepListForm(PaginationForm):
    """ 获取报告步骤列表 """
    report_case_id: int = Field(..., title="报告用例id")


class GetReportStepForm(BaseForm):
    """ 获取报告步骤数据 """
    id: int = Field(..., title="报告步骤id")

    @field_validator("id")
    def validate_id(cls, value):
        report_step = cls.validate_data_is_exist("数据不存在", ReportStep, id=value)
        setattr(cls, "report_step", report_step)
        return value


class GetReportShowIdForm(BaseForm):
    """ 获取报告状态 """
    batch_id: str = required_str_field(title="执行批次id")


class GetReportStatusForm(GetReportShowIdForm):
    """ 获取报告状态 """
    process: int = Field(1, title="当前进度")
    status: int = Field(1, title="当前进度下的状态")


class GetReportStepImgForm(BaseForm):
    """ 获取报告步骤截图 """
    report_id: int = Field(..., title="报告id")
    report_step_id: int = Field(..., title="报告步骤id")
    img_type: str = required_str_field(title="截图类型", description="截图类型，before_page, after_page")


class ChangeReportStepStatus(BaseForm):
    """ 修改测试报告步骤的状态 stop、pause、resume """
    report_id: Optional[int] = Field(None, title="报告id",
                                     description="只传report_id，则代表是对整个测试报告的所有步骤进行操作")
    report_case_id: Optional[int] = Field(None, title="报告用例id")
    report_step_id: Optional[int] = Field(None, title="报告步骤id")
    status: str = Field(..., title="状态", description="stop、pause、resume")
