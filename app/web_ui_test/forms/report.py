# -*- coding: utf-8 -*-
import os

from wtforms import IntegerField, StringField
from wtforms.validators import DataRequired

from app.assist.models.hits import Hits
from utils.util.fileUtil import WEB_UI_REPORT_ADDRESS, FileUtil
from app.baseForm import BaseForm
from app.web_ui_test.models.report import WebUiReport as Report


class DownloadReportForm(BaseForm):
    """ 报告下载 """
    id = IntegerField(validators=[DataRequired("请选择报告")])

    def validate_id(self, field):
        """ 校验报告是否存在 """
        report = self.validate_data_is_exist("报告不存在", Report, id=field.data)
        report_path = os.path.join(WEB_UI_REPORT_ADDRESS, f"{report.id}.txt")
        self.validate_data_is_true("报告文件不存在", os.path.exists(report_path))
        setattr(self, "report", report)
        setattr(self, "report_path", report_path)
        setattr(self, "report_content", FileUtil.get_web_ui_test_report(field.data))


class GetReportDetailForm(DownloadReportForm):
    """ 查看报告 """


class GetReportForm(BaseForm):
    """ 删除报告 """
    id = IntegerField(validators=[DataRequired("请选择报告")])

    def validate_id(self, field):
        report = self.validate_data_is_exist("报告不存在", Report, id=field.data)
        report_path = os.path.join(WEB_UI_REPORT_ADDRESS, f"{report.id}.txt")
        setattr(self, "report", report)
        setattr(self, "report_path", report_path)


class DeleteReportForm(BaseForm):
    """ 删除报告 """
    id = StringField(validators=[DataRequired("请选择报告")])

    def validate_id(self, field):
        report_list = []
        for report_id in field.data:
            report = Report.get_first(id=report_id)
            if report and Hits.get_first(report_id=report.id) is None:  # 没有被登记失败记录的报告
                report.report_path = os.path.join(WEB_UI_REPORT_ADDRESS, f"{report.id}.txt")
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
    env = IntegerField()