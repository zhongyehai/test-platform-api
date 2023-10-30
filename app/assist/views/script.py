# -*- coding: utf-8 -*-
import importlib
import sys
import types
import traceback

from flask import current_app as app, request

from utils.redirectPrintLog import RedirectPrintLogToMemory
from utils.util.fileUtil import FileUtil
from utils.client.testRunner.parser import parse_function, extract_functions
from app.assist.blueprint import assist
from app.assist.models.script import Script
from app.assist.forms.script import HasScriptForm, CreatScriptForm, EditScriptForm, DebuggerScriptForm, \
    DeleteScriptForm, GetScriptFileForm


@assist.login_get("/script/list")
def assist_get_script_list():
    """ 自定义脚本文件列表 """
    form = GetScriptFileForm().do_validate()
    data_list = Script.make_pagination(form)
    return app.restful.success("获取成功", data=data_list)


@assist.login_post("/script/copy")
def assist_copy_script():
    """ 复制自定义脚本文件 """
    form = HasScriptForm().do_validate()
    data = form.script.to_dict()
    data["name"] += '_copy'
    script = Script().create(data)
    return app.restful.success("复制成功", data=script.to_dict())


@assist.login_put("/script/sort")
def assist_change_script_sort():
    """ 更新服务的排序 """
    Script.change_sort(request.json.get("List"), request.json.get("pageNum"), request.json.get("pageSize"))
    return app.restful.success(msg="修改排序成功")


@assist.login_post("/script/debug")
def assist_debug_script():
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

        # 重定向print内容到内存
        redirect = RedirectPrintLogToMemory()
        result = module_functions_dict[func["func_name"]](*func["args"], **func["kwargs"])  # 执行脚本
        script_print = redirect.get_text_and_redirect_to_default()

        return app.restful.success(msg="执行成功，请查看执行结果", result={
            "env": form.env.data,
            "expression": form.expression.data,
            "result": result,
            "script_print": script_print,
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


@assist.login_get("/script")
def assist_get_script():
    """ 获取脚本文件 """
    form = HasScriptForm().do_validate()
    return app.restful.success(msg="获取成功", script_data=form.script.script_data)


@assist.login_post("/script")
def assist_add_script():
    """ 新增脚本文件 """
    form = CreatScriptForm().do_validate()
    form.num.data = Script.get_insert_num()
    script = Script().create(form.data)
    return app.restful.success(f'脚本文件 {form.name.data} 创建成功', data=script.to_dict())


@assist.login_put("/script")
def assist_change_script():
    """ 修改脚本文件 """
    form = EditScriptForm().do_validate()
    form.script.update(form.data)
    return app.restful.success(f'脚本文件 {form.name.data} 修改成功', data=form.script.to_dict())


@assist.login_delete("/script")
def assist_delete_script():
    """ 删除脚本文件 """
    form = DeleteScriptForm().do_validate()
    form.script.delete()
    return app.restful.success(f'脚本文件 {form.script.name} 删除成功')
