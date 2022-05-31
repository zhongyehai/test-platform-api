from selenium import webdriver

from common import get_case_id
from common.mongo import Mongo


class Logic(object):

    # def __init__(self):
    #     self.driver = webdriver.Chrome()

    def get(self, params):
        """ 打开页面 """
        url = params.get('value', "http://www.baidu.com")
        self.driver.get(url)

    def find(self, params):
        """ 查找元素 """
        selector = params.get('selector', None)
        value = params.get('value', None)
        return self.driver.find_element(selector, value)

    def send(self, element, params):
        """ 发送内容 """
        text = params.get('value', "默认值")
        element.send_keys(text)

    def click(self, element, params):
        """ 点击操作 """
        element.click()

    def close(self):
        self.driver.quit()

    def execute(self, data):
        """ 执行操作 """
        self.driver = webdriver.Chrome()
        commands = data.get("commands")  # 取出页面设置的操作步骤的列表[{command:xxx, parameter: xxx},{}]

        element = None
        # 把每一个步骤取出来执行
        for command in commands:
            print(command)
            # print(command['command'])
            # print(command['parameter'])
            cmd = command['command']
            params = command['parameter']
            print("run command[{0}] with param[{1}] and element[{2}]".format(cmd, params, element))
            if element is None:
                element = getattr(self, cmd)(params)
            else:
                element = getattr(self, cmd)(element, params)

    def save(self, data):
        """ 保存测试数据 """
        data.setdefault('_id', get_case_id())
        mongo = Mongo()
        mongo.insert("20190316", "automation", data)

        return data['_id']

    def trigger(self, data):
        """ 触发执行 """
        id = data.get('id')
        mongo = Mongo()
        cases = list(mongo.search("20190316", "automation", {'_id': id}))
        print(cases[0])
        self.execute(cases[0])
