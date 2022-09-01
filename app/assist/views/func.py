# -*- coding: utf-8 -*-
import importlib
import types
import traceback

from flask import current_app as app, g, views

from utils.globalVariable import os, FUNC_ADDRESS
from utils.parse import parse_function, extract_functions
from app.assist import assist
from app.assist.models.func import Func
from app.assist.forms.func import HasFuncForm, SaveFuncDataForm, CreatFuncForm, EditFuncForm, DebuggerFuncForm, DeleteFuncForm, GetFuncFileForm


@assist.route('/func/list', methods=['GET'])
def func_list():
    """ 查找所有自定义函数文件 """
    form = GetFuncFileForm()
    if form.validate():
        return app.restful.success('获取成功', data=Func.make_pagination(form))
    return app.restful.error(form.get_error())


@assist.route('/func/debug', methods=['POST'])
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
            return app.restful.success(msg='执行成功，请查看执行结果', result=result)
        except Exception as e:
            app.logger.info(str(e))
            error_data = '\n'.join('{}'.format(traceback.format_exc()).split('↵'))
            return app.restful.fail(msg='语法错误，请检查', result=error_data)
    return app.restful.fail(msg=form.get_error())


@assist.route('/func/data', methods=['PUt'])
def save_func_data():
    """ 保存函数文件内容 """
    form = SaveFuncDataForm()
    if form.validate():
        form.func.update({'func_data': form.func_data.data})
        return app.restful.success(f'保存成功')
    return app.restful.fail(form.get_error())


class FuncView(views.MethodView):

    def get(self):
        form = HasFuncForm()
        if form.validate():
            return app.restful.success(msg='获取成功', func_data=form.func.func_data)
        return app.restful.fail(form.get_error())

    def post(self):
        form = CreatFuncForm()
        if form.validate():
            Func().create(form.data)
            return app.restful.success(f'函数文件 {form.name.data} 创建成功')
        return app.restful.fail(form.get_error())

    def put(self):
        form = EditFuncForm()
        if form.validate():
            form.func.update(form.data)
            return app.restful.success(f'函数文件 {form.name.data} 修改成功', data=form.func.to_dict())
        return app.restful.fail(form.get_error())

    def delete(self):
        form = DeleteFuncForm()
        if form.validate():
            form.func.delete()
            return app.restful.success(f'函数文件 {form.name.data} 删除成功')
        return app.restful.fail(form.get_error())


assist.add_url_rule('/func', view_func=FuncView.as_view('func'))
