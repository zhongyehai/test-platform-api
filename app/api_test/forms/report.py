# -*- coding: utf-8 -*-
import os

from wtforms import IntegerField, StringField
from wtforms.validators import DataRequired

from utils.util.fileUtil import API_REPORT_ADDRESS, FileUtil
from app.baseForm import BaseForm
from app.api_test.models.report import ApiReport as Report


class DownloadReportForm(BaseForm):
    """ 报告下载 """
    id = IntegerField(validators=[DataRequired("请选择报告")])

    def validate_id(self, field):
        """ 校验报告是否存在 """
        report = self.validate_data_is_exist("报告还未生成, 请联系管理员处理", Report, id=field.data)
        report_path = os.path.join(API_REPORT_ADDRESS, f"{report.id}.txt")
        self.validate_data_is_true("报告文件不存在, 请联系管理员处理", os.path.exists(report_path))
        setattr(self, "report", report)
        setattr(self, "report_path", report_path)
        setattr(self, "report_content", FileUtil.get_api_test_report(field.data))


class GetReportDetailForm(DownloadReportForm):
    """ 查看报告 """


class GetReportForm(BaseForm):
    """ 获取报告 """
    id = IntegerField(validators=[DataRequired("请选择报告")])

    def validate_id(self, field):
        report = self.validate_data_is_exist("报告不存在", Report, id=field.data)
        report_path = os.path.join(API_REPORT_ADDRESS, f"{report.id}.txt")
        setattr(self, "report", report)
        setattr(self, "report_path", report_path)


class FindReportForm(BaseForm):
    """ 查找报告 """
    projectId = IntegerField(validators=[DataRequired("请选择服务")])
    pageNum = IntegerField()
    pageSize = IntegerField()
    projectName = StringField()
    createUser = StringField()
