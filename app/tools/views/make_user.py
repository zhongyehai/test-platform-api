# -*- coding: utf-8 -*-
import json
import os

from faker import Faker
from flask import request, current_app as app, send_from_directory, g

from app.tools.blueprint import tool
from utils.make_data import make_user_tools
from utils.util.file_util import FileUtil, TEMP_FILE_ADDRESS


@tool.get("/makeUser")
def tool_get_make_user():
    """ 生成用户信息 """
    all_data, args = [], request.args.to_dict()
    language, count, options = args.get("language"), int(args.get("count")), json.loads(args.get("options"))
    fake = Faker(language)
    for option in options:
        temp_data = []
        if hasattr(fake, option) or option == "credit_code":
            i = 0
            while True:
                if i >= count:
                    break
                data = make_user_tools.get_credit_code() if option == "credit_code" else getattr(fake, option)()
                if data not in temp_data:
                    temp_data.append(data)
                    i += 1
        all_data.append(temp_data)
    return app.restful.success("获取成功", data=[dict(zip(options, data)) for data in zip(*all_data)])


@tool.post("/makeUser/contact/download")
def tool_download_make_user_as_contact():
    """ 导出为通讯录文件 """
    """
    [
      {"name": "name1", "phone_number": "159xxxxxxxx"},
      {"name": "name2", "phone_number": "131xxxxxxxx"}
    ]
    """
    # 数据解析为通讯录格式
    language, count, data_list = request.json["language"], request.json["count"], request.json["data_list"]
    contact_text = ''
    for index, data in enumerate(data_list):
        if index >= count:
            break
        contact_text += f'BEGIN:VCARD\nVERSION:2.1\nFN:{data.get("name", f"name_{index}")}\nTEL;CELL:{data.get("phone_number", "")}\nEND:VCARD\n'

    # 写入到文件
    file_name = f'通讯录_{g.user_id}_{language}_{count}条.vcf'
    file_path = os.path.join(TEMP_FILE_ADDRESS, file_name)
    with open(file_path, "w", encoding='utf-8') as fp:
        fp.write(contact_text)

    return send_from_directory(TEMP_FILE_ADDRESS, file_name, as_attachment=True)
