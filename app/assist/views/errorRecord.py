# -*- coding: utf-8 -*-
from flask import current_app as app

from app.assist import assist
from app.assist.models.errorRecord import ErrorRecord
from app.assist.forms.errorRecord import FindErrorForm


@assist.route('/errorRecord/list', methods=['GET'])
def error_record_list_not_login_required():
    """ 错误列表 """
    form = FindErrorForm()
    if form.validate():
        return app.restful.success(data=ErrorRecord.make_pagination(form))
    return app.restful.fail(form.get_error())
