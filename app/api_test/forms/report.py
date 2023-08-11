# -*- coding: utf-8 -*-
from wtforms import IntegerField, StringField, BooleanField
from wtforms.validators import DataRequired

from app.assist.models.hits import Hits
from app.baseForm import BaseForm
from app.api_test.models.report import ApiReport as Report, ApiReportStep, ApiReportCase


class GetReportForm(BaseForm):
    """ 获取报告 """
    id = IntegerField(validators=[DataRequired("请选择报告")])

    def validate_id(self, field):
        report = self.validate_data_is_exist("报告不存在", Report, id=field.data)
        setattr(self, "report", report)


class DeleteReportForm(BaseForm):
    """ 删除报告 """
    id = StringField(validators=[DataRequired("请选择报告")])

    def validate_id(self, field):
        report_id_list = []
        for report_id in field.data:
            report = Report.get_first(id=report_id)
            if report:
                # 出于周统计、月统计的数据准确性考虑，触发方式为 pipeline 和 cron，只有管理员权限能删
                if report.trigger_type in ['pipeline', 'cron'] and self.is_not_admin():
                    continue

                # 没有被登记失败记录的报告可以删
                if Hits.get_first(report_id=report.id) is None:
                    report_id_list.append(report.id)

        setattr(self, "report_id_list", report_id_list)


class FindReportForm(BaseForm):
    """ 获取报告 """
    projectId = IntegerField(validators=[DataRequired("请选择服务")])
    pageNum = IntegerField()
    pageSize = IntegerField()
    projectName = StringField()
    createUser = StringField()
    trigger_type = StringField()
    run_type = StringField()
    is_passed = StringField()
    env_list = StringField()


class GetReportCaseListForm(BaseForm):
    """ 获取报告用例列表 """
    report_id = IntegerField(validators=[DataRequired("报告id必传")])
    get_summary = BooleanField()


class GetReportCaseForm(BaseForm):
    """ 获取报告步骤数据 """
    id = IntegerField(validators=[DataRequired("报告用例id必传")])

    def validate_id(self, field):
        data = self.validate_data_is_exist('数据不存在', ApiReportCase, id=field.data)
        setattr(self, 'case_data', data)


class GetReportStepListForm(BaseForm):
    """ 获取报告步骤列表 """
    report_case_id = IntegerField(validators=[DataRequired("报告用例id必传")])
    get_summary = BooleanField()


class GetReportStepForm(BaseForm):
    """ 获取报告步骤数据 """
    id = IntegerField(validators=[DataRequired("步骤id必传")])

    def validate_id(self, field):
        data = self.validate_data_is_exist('数据不存在', ApiReportStep, id=field.data)
        setattr(self, 'step_data', data)
