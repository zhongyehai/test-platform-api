# -*- coding: utf-8 -*-
from wtforms import IntegerField, StringField
from wtforms.validators import DataRequired

from app.assist.models.hits import Hits
from app.baseForm import BaseForm
from app.app_ui_test.models.report import AppUiReport as Report, AppUiReportStep


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
        report_list = []
        for report_id in field.data:
            report = Report.get_first(id=report_id)
            if report and Hits.get_first(report_id=report.id) is None:  # 没有被登记失败记录的报告
                report_list.append(report)
        setattr(self, "report_list", report_list)


class FindReportForm(BaseForm):
    """ 查找报告 """
    projectId = IntegerField(validators=[DataRequired("请选择服务")])
    pageNum = IntegerField()
    pageSize = IntegerField()
    projectName = StringField()
    createUser = StringField()
    trigger_type = StringField()
    run_type = StringField()
    is_passed = StringField()
    env_list = StringField()


class FindReportStepListForm(BaseForm):
    """ 查找报告步骤列表 """
    report_id = IntegerField(validators=[DataRequired("报告id必传")])


class FindReportStepForm(BaseForm):
    """ 查找报告步骤数据 """
    id = IntegerField(validators=[DataRequired("步骤id必传")])

    def validate_id(self, field):
        data = self.validate_data_is_exist('数据不存在', AppUiReportStep, id=field.data)
        setattr(self, 'step_data', data)
