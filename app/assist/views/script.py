# -*- coding: utf-8 -*-
import importlib
import sys
import types
import traceback

from flask import current_app as app, request

from app.baseView import LoginRequiredView
from utils.redirectPrintLog import RedirectPrintLogToMemory, redirect_print_log_to_file
from utils.util.fileUtil import FileUtil
from utils.client.testRunner.parser import parse_function, extract_functions
from app.assist.blueprint import assist
from app.assist.models.script import Script
from app.assist.forms.script import HasScriptForm, CreatScriptForm, EditScriptForm, DebuggerScriptForm, DeleteScriptForm, \
    GetScriptFileForm


class GetScriptListView(LoginRequiredView):

    def get(self):
        """ 自定义脚本文件列表 """
        form = GetScriptFileForm().do_validate()
        data_list = Script.make_pagination(form)
        return app.restful.success("获取成功", data=data_list)


class CopyScriptView(LoginRequiredView):

    def post(self):
        """ 复制自定义脚本文件 """
        form = HasScriptForm().do_validate()
        data = form.script.to_dict()
        data["name"] += '_copy'
        script = Script().create(data)
        return app.restful.success("复制成功", data=script.to_dict())


class ScriptChangeSortView(LoginRequiredView):

    def put(self):
        """ 更新服务的排序 """
        Script.change_sort(request.json.get("List"), request.json.get("pageNum"), request.json.get("pageSize"))
        return app.restful.success(msg="修改排序成功")


class DebugScriptView(LoginRequiredView):

    def post(self):
        """ 函数调试 """
        form = DebuggerScriptForm().do_validate()
        name, expression = f'{form.env.data}_{form.script.name}', form.expression.data

        # 把自定义函数脚本内容写入到python脚本中
        Script.create_script_file(form.env.data)

        # 动态导入脚本
        try:
            import_path = f'script_list.{name}'
            func_list = importlib.reload(importlib.import_module(import_path))
            module_functions_dict = {
                name: item for name, item in vars(func_list).items() if isinstance(item, types.FunctionType)
            }
            ext_func = extract_functions(expression)
            func = parse_function(ext_func[0])

            # 重定向print内容到文件
            # redirect_print_log_to_file(name)
            # result = module_functions_dict[func["func_name"]](*func["args"], **func["kwargs"])
            # # 恢复输出到console、读取print内容、删除printlog文件，顺序不可改变
            # sys.stdout = sys.__stdout__
            # script_print = FileUtil.get_script_print_log(name)
            # FileUtil.delete_script_print_addr(FileUtil.get_script_print_addr(name))

            # 重定向print内容到内存
            redirect = RedirectPrintLogToMemory()
            result = module_functions_dict[func["func_name"]](*func["args"], **func["kwargs"])
            sys.stdout = sys.__stdout__  # 恢复输出到console
            return app.restful.success(msg="执行成功，请查看执行结果", result={
                "env": form.env.data,
                "expression": form.expression.data,
                "result": result,
                "script_print": redirect.text,
                "script": FileUtil.get_func_data_by_script_name(f'{form.env.data}_{form.script.name}')
            })
        except Exception as e:
            sys.stdout = sys.__stdout__  # 恢复输出到console
            app.logger.info(str(e))
            error_data = "\n".join("{}".format(traceback.format_exc()).split("↵"))
            return app.restful.fail(msg="语法错误，请检查", result={
                "env": form.env.data,
                "expression": form.expression.data,
                "result": error_data,
                "script": FileUtil.get_func_data_by_script_name(f'{form.env.data}_{form.script.name}')
            })


class ScriptView(LoginRequiredView):
    default_env = "debug"

    def get(self):
        """ 获取脚本文件 """
        form = HasScriptForm().do_validate()
        return app.restful.success(msg="获取成功", script_data=form.script.script_data)

    def post(self):
        """ 新增脚本文件 """
        form = CreatScriptForm().do_validate()
        form.num.data = Script.get_insert_num()
        script = Script().create(form.data)
        return app.restful.success(f'脚本文件 {form.name.data} 创建成功', data=script.to_dict())

    def put(self):
        """ 修改脚本文件 """
        form = EditScriptForm().do_validate()
        form.script.update(form.data)
        return app.restful.success(f'脚本文件 {form.name.data} 修改成功', data=form.script.to_dict())

    def delete(self):
        """ 删除脚本文件 """
        form = DeleteScriptForm().do_validate()
        form.script.delete()
        return app.restful.success(f'脚本文件 {form.script.name} 删除成功')


assist.add_url_rule("/script", view_func=ScriptView.as_view("ScriptView"))
assist.add_url_rule("/script/copy", view_func=CopyScriptView.as_view("CopyScriptView"))
assist.add_url_rule("/script/debug", view_func=DebugScriptView.as_view("DebugScriptView"))
assist.add_url_rule("/script/list", view_func=GetScriptListView.as_view("GetScriptListView"))
assist.add_url_rule("/script/sort", view_func=ScriptChangeSortView.as_view("ScriptChangeSortView"))
