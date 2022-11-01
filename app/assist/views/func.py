# -*- coding: utf-8 -*-
import importlib
import types
import traceback

from flask import current_app as app, request

from app.baseView import LoginRequiredView
from utils.util.fileUtil import FileUtil
from utils.client.testRunner.parser import parse_function, extract_functions
from app.assist.blueprint import assist
from app.assist.models.func import Func
from app.assist.forms.func import HasFuncForm, SaveFuncDataForm, CreatFuncForm, EditFuncForm, DebuggerFuncForm, \
    DeleteFuncForm, GetFuncFileForm


class GetFuncListView(LoginRequiredView):

    def get(self):
        """ 自定义函数文件列表 """
        form = GetFuncFileForm().do_validate()
        return app.restful.success('获取成功', data=Func.make_pagination(form))


class FuncChangeSortView(LoginRequiredView):

    def put(self):
        """ 更新服务的排序 """
        Func.change_sort(request.json.get('List'), request.json.get('pageNum'), request.json.get('pageSize'))
        return app.restful.success(msg='修改排序成功')


class DebugFuncView(LoginRequiredView):

    def post(self):
        """ 函数调试 """
        form = DebuggerFuncForm().do_validate()
        name, debug_data = form.func.name, form.debug_data.data

        # 把自定义函数脚本内容写入到python脚本中
        FileUtil.save_func_data(name, form.func.func_data)

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


class SaveFuncDataView(LoginRequiredView):

    def put(self):
        """ 保存函数文件内容 """
        form = SaveFuncDataForm().do_validate()
        form.func.update({'func_data': form.func_data.data})
        return app.restful.success(f'保存成功')


class FuncView(LoginRequiredView):

    def get(self):
        """ 获取函数文件 """
        form = HasFuncForm().do_validate()
        return app.restful.success(msg='获取成功', func_data=form.func.func_data)

    def post(self):
        """ 新增函数文件 """
        form = CreatFuncForm().do_validate()
        form.num.data = Func.get_insert_num()
        Func().create(form.data)
        return app.restful.success(f'函数文件 {form.name.data} 创建成功')

    def put(self):
        """ 修改函数文件 """
        form = EditFuncForm().do_validate()
        form.func.update(form.data)
        return app.restful.success(f'函数文件 {form.name.data} 修改成功', data=form.func.to_dict())

    def delete(self):
        """ 删除函数文件 """
        form = DeleteFuncForm().do_validate()
        form.func.delete()
        return app.restful.success(f'函数文件 {form.func.name} 删除成功')


assist.add_url_rule('/func', view_func=FuncView.as_view('FuncView'))
assist.add_url_rule('/func/debug', view_func=DebugFuncView.as_view('DebugFuncView'))
assist.add_url_rule('/func/list', view_func=GetFuncListView.as_view('GetFuncListView'))
assist.add_url_rule('/func/data', view_func=SaveFuncDataView.as_view('SaveFuncDataView'))
assist.add_url_rule('/func/sort', view_func=FuncChangeSortView.as_view('FuncChangeSortView'))
