# -*- coding: utf-8 -*-
import importlib
import types
import traceback

from flask import current_app as app, g

from app.utils import restful
from app.utils.required import login_required
from app.utils.globalVariable import os, FUNC_ADDRESS
from app.utils.parse import parse_function, extract_functions
from app.api_test import api_test
from app.baseView import BaseMethodView
from app.api_test.models.func import Func
from app.api_test.forms.func import HasFuncForm, SaveFuncDataForm, CreatFuncForm, EditFuncForm, DebuggerFuncForm, DeleteFuncForm, GetFuncFileForm


@api_test.route('/func/list', methods=['GET'])
@login_required
def func_list():
    """ 查找所有自定义函数文件 """
    form = GetFuncFileForm()
    if form.validate():
        return restful.success('获取成功', data=Func.make_pagination(form))
    return restful.error(form.get_error())


@api_test.route('/func/debug', methods=['POST'])
@login_required
def debug_func():
    """ 函数调试 """
    form = DebuggerFuncForm()
    if form.validate():
        name, debug_data = form.func.name, form.debug_data.data

        # 把自定义函数脚本内容写入到python脚本中
        with open(os.path.join(FUNC_ADDRESS, f'{name}.py'), 'w', encoding='utf8') as file:
            # file.write(form.func.func_data)
            file.write('# coding:utf-8\n\n' + f'env = "test"\n\n' + form.func.func_data)

        # 动态导入脚本
        try:
            import_path = f'func_list.{name}'
            func_list = importlib.reload(importlib.import_module(import_path))
            module_functions_dict = {name: item for name, item in vars(func_list).items() if
                                     isinstance(item, types.FunctionType)}
            ext_func = extract_functions(debug_data)
            func = parse_function(ext_func[0])
            result = module_functions_dict[func['func_name']](*func['args'], **func['kwargs'])
            return restful.success(msg='执行成功，请查看执行结果', result=result)
        except Exception as e:
            app.logger.info(str(e))
            error_data = '\n'.join('{}'.format(traceback.format_exc()).split('↵'))
            return restful.fail(msg='语法错误，请检查', result=error_data)
    return restful.fail(msg=form.get_error())


@api_test.route('/func/data', methods=['PUt'])
def save_func_data():
    """ 保存函数文件内容 """
    form = SaveFuncDataForm()
    if form.validate():
        form.func.update({'func_data': form.func_data.data})
        return restful.success(f'保存成功')
    return restful.fail(form.get_error())


class FuncView(BaseMethodView):

    def get(self):
        form = HasFuncForm()
        if form.validate():
            return restful.success(msg='获取成功', func_data=form.func.func_data)
        return restful.fail(form.get_error())

    def post(self):
        form = CreatFuncForm()
        if form.validate():
            Func().create(dict(name=form.name.data, create_user=g.user_id, update_user=g.user_id))
            return restful.success(f'函数文件 {form.name.data} 创建成功')
        return restful.fail(form.get_error())

    def put(self):
        form = EditFuncForm()
        if form.validate():
            form.func.update({'name': form.name.data, 'desc': form.desc.data})
            return restful.success(f'函数文件 {form.name.data} 修改成功', data=form.func.to_dict())
        return restful.fail(form.get_error())

    def delete(self):
        form = DeleteFuncForm()
        if form.validate():
            form.func.delete()
            return restful.success(f'函数文件 {form.name.data} 删除成功')
        return restful.fail(form.get_error())


api_test.add_url_rule('/func', view_func=FuncView.as_view('func'))
