# -*- coding: utf-8 -*-
from threading import Thread

from flask import current_app as app, request, send_from_directory, g

from app.api_test.models.module import ApiModule
from app.api_test.models.project import ApiProject
from app.api_test.models.report import ApiReport as Report
from app.baseView import LoginRequiredView
from utils.filePath import STATIC_ADDRESS
from utils.parseExcel import parse_file_content
from utils.client.runApiTest.runHttpRunner import RunApi
from app.api_test import api_test
from app.baseModel import db
from app.api_test.models.api import ApiMsg
from app.config.models.config import Config
from app.api_test.forms.api import AddApiForm, EditApiForm, RunApiMsgForm, DeleteApiForm, ApiListForm, GetApiByIdForm, \
    ApiBelongToForm
from config.config import assert_mapping_list

ns = api_test.namespace("apiMsg", description="接口管理相关接口")


@ns.route('/assertMapping/')
class ApiAssertMappingView(LoginRequiredView):

    def get(self):
        """ 获取断言类型 """
        return app.restful.success('获取成功', data=assert_mapping_list)


@ns.route('/methods/')
class ApiMethodsMappingView(LoginRequiredView):

    def get(self):
        """ 获取配置的请求方法列表 """
        return app.restful.success(
            '获取成功',
            data=[{'value': method} for method in Config.get_http_methods().split(',')]
        )


@ns.route('/list/')
class ApiGetApiListView(LoginRequiredView):

    def get(self):
        """ 根据模块查接口list """
        form = ApiListForm()
        if form.validate():
            return app.restful.success(data=ApiMsg.make_pagination(form))
        return app.restful.fail(form.get_error())


@ns.route('/belongTo/')
class ApiGetApiBelongToView(LoginRequiredView):

    def get(self):
        """ 根据接口地址获取接口的归属信息 """
        form = ApiBelongToForm()
        if form.validate():
            api_msg = form.api
            project = ApiProject.get_first(id=api_msg.project_id)
            module = ApiModule.get_first(id=api_msg.module_id)
            return app.restful.success(msg=f'此接口归属于：{project.name}_{module.name}_{api_msg.name}')
        return app.restful.fail(form.get_error())


@ns.route('/upload/')
class ApiGetApiUploadView(LoginRequiredView):

    def post(self):
        """ 从excel中导入接口 """
        file, module, user_id = request.files.get('file'), ApiModule.get_first(id=request.form.get('id')), g.user_id
        if not module:
            return app.restful.fail('模块不存在')
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
            return app.restful.success('接口导入成功')
        return app.restful.fail('请上传后缀为xls的Excel文件')


@ns.route('/template/download/')
class ApiTemplateDownloadView(LoginRequiredView):

    def get(self):
        """ 下载接口模板 """
        return send_from_directory(STATIC_ADDRESS, '接口导入模板.xls', as_attachment=True)


@ns.route('/run/')
class ApiRunApiMsgView(LoginRequiredView):

    def post(self):
        """ 运行接口 """
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
            return app.restful.success(msg='触发执行成功，请等待执行完毕', data={'report_id': report.id})
        return app.restful.fail(form.get_error())


@ns.route('/sort/')
class ApiChangeApiSortView(LoginRequiredView):

    def put(self):
        """ 修改接口的排序 """
        ApiMsg.change_sort(request.json.get('List'), request.json.get('pageNum'), request.json.get('pageSize'))
        return app.restful.success(msg='修改排序成功')


@ns.route('/')
class ApiMsgView(LoginRequiredView):
    """ 接口信息 """

    def get(self):
        """ 获取接口 """
        form = GetApiByIdForm()
        if form.validate():
            return app.restful.success(data=form.api.to_dict())
        return app.restful.fail(form.get_error())

    def post(self):
        """ 新增接口 """
        form = AddApiForm()
        if form.validate():
            form.num.data = ApiMsg.get_insert_num(module_id=form.module_id.data)
            new_api = ApiMsg().create(form.data)
            return app.restful.success(f'接口【{form.name.data}】新建成功', data=new_api.to_dict())
        return app.restful.fail(form.get_error())

    def put(self):
        """ 修改接口 """
        form = EditApiForm()
        if form.validate():
            form.api.update(form.data)
            return app.restful.success(f'接口【{form.name.data}】修改成功', form.api.to_dict())
        return app.restful.fail(form.get_error())

    def delete(self):
        """ 删除接口 """
        form = DeleteApiForm()
        if form.validate():
            form.api.delete()
            return app.restful.success(f'接口【{form.api.name}】删除成功')
        return app.restful.fail(form.get_error())
