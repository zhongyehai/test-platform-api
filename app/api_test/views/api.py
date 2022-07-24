# -*- coding: utf-8 -*-
from threading import Thread

from flask import request, send_from_directory, g

from app.api_test.models.module import ApiModule
from app.api_test.models.project import ApiProject
from app.api_test.models.report import ApiReport as Report
from utils import restful
from utils.globalVariable import TEMPLATE_ADDRESS
from utils.parseExcel import parse_file_content
from utils.required import login_required
from utils.client.runApiTest.runHttpRunner import RunApi
from app.api_test import api_test
from app.baseView import BaseMethodView
from app.baseModel import db
from app.api_test.models.api import ApiMsg
from app.config.models.config import Config
from app.api_test.forms.api import AddApiForm, EditApiForm, RunApiMsgForm, DeleteApiForm, ApiListForm, GetApiByIdForm, \
    ApiBelongToForm
from config.config import assert_mapping_list


@api_test.route('/apiMsg/assertMapping', methods=['GET'])
@login_required
def api_assert_mapping():
    """ 断言类型 """
    return restful.success('获取成功', data=assert_mapping_list)


@api_test.route('/apiMsg/methods', methods=['GET'])
@login_required
def api_methods_mapping():
    """ 获取配置的请求方法列表 """
    return restful.success(
        '获取成功',
        data=[{'value': method} for method in Config.get_first(name='http_methods').value.split(',')]
    )


@api_test.route('/apiMsg/list', methods=['GET'])
@login_required
def api_get_api_list():
    """ 根据模块查接口list """
    form = ApiListForm()
    if form.validate():
        return restful.success(data=ApiMsg.make_pagination(form))
    return restful.fail(form.get_error())


@api_test.route('/apiMsg/belongTo', methods=['GET'])
@login_required
def api_get_api_belong_to():
    """ 根据接口地址获取接口的归属信息 """
    form = ApiBelongToForm()
    if form.validate():
        api_msg = form.api
        project = ApiProject.get_first(id=api_msg.project_id)
        module = ApiModule.get_first(id=api_msg.module_id)
        return restful.success(msg=f'此接口归属于：{project.name}_{module.name}_{api_msg.name}')
    return restful.fail(form.get_error())


@api_test.route('/apiMsg/upload', methods=['POST'])
@login_required
def api_api_upload():
    """ 从excel中导入接口 """
    file, module, user_id = request.files.get('file'), ApiModule.get_first(id=request.form.get('id')), g.user_id
    if not module:
        return restful.fail('模块不存在')
    if file and file.filename.endswith('xls'):
        excel_data = parse_file_content(file.read())  # [{'请求类型': 'get', '接口名称': 'xx接口', 'addr': '/api/v1/xxx'}]
        with db.auto_commit():
            for api_data in excel_data:
                new_api = ApiMsg()
                for key, value in api_data.items():
                    if hasattr(new_api, key):
                        setattr(new_api, key, value)
                new_api.method = api_data.get('method', 'post').upper()
                new_api.num = new_api.get_insert_num(module_id=module.id)
                new_api.project_id = module.project_id
                new_api.module_id = module.id
                new_api.create_user = user_id
                db.session.add(new_api)
        return restful.success('接口导入成功')
    return restful.fail('请上传后缀为xls的Excel文件')


@api_test.route('/apiMsg/template/download', methods=['GET'])
def api_download_api_template():
    """ 下载接口模板 """
    return send_from_directory(TEMPLATE_ADDRESS, '接口导入模板.xls', as_attachment=True)


@api_test.route('/apiMsg/run', methods=['POST'])
@login_required
def api_run_api_msg():
    """ 跑接口信息 """
    form = RunApiMsgForm()
    if form.validate():
        api, api_list = form.api_list[0], form.api_list
        report = Report.get_new_report(api.name, 'api', g.user_name, g.user_id, form.projectId.data)

        # 新起线程运行接口
        Thread(
            target=RunApi(
                project_id=form.projectId.data,
                run_name=report.name,
                api_ids=api_list,
                report_id=report.id,
                env=form.env.data
            ).run_case
        ).start()
        return restful.success(msg='触发执行成功，请等待执行完毕', data={'report_id': report.id})
    return restful.fail(form.get_error())


@api_test.route('/apiMsg/sort', methods=['put'])
@login_required
def api_change_api_sort():
    """ 更新接口的排序 """
    ApiMsg.change_sort(request.json.get('List'), request.json.get('pageNum'), request.json.get('pageSize'))
    return restful.success(msg='修改排序成功')


class ApiMsgView(BaseMethodView):
    """ 接口信息 """

    def get(self):
        form = GetApiByIdForm()
        if form.validate():
            return restful.success(data=form.api.to_dict())
        return restful.fail(form.get_error())

    def post(self):
        form = AddApiForm()
        if form.validate():
            form.num.data = ApiMsg.get_insert_num(module_id=form.module_id.data)
            new_api = ApiMsg().create(form.data)
            return restful.success(f'接口【{form.name.data}】新建成功', data=new_api.to_dict())
        return restful.fail(form.get_error())

    def put(self):
        form = EditApiForm()
        if form.validate():
            form.api.update(form.data)
            return restful.success(f'接口【{form.name.data}】修改成功', form.api.to_dict())
        return restful.fail(form.get_error())

    def delete(self):
        form = DeleteApiForm()
        if form.validate():
            form.api.delete()
            return restful.success(f'接口【{form.api.name}】删除成功')
        return restful.fail(form.get_error())


api_test.add_url_rule('/apiMsg', view_func=ApiMsgView.as_view('apiMsg'))
