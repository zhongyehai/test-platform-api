import time

from selenium.common.exceptions import SessionNotCreatedException, InvalidArgumentException

from .webdriverAction import Driver
from .exceptions import TimeoutException, RunTimeException
from . import logger


class WebDriverSession:
    """ 实例化webdriver，并执行webdriver动作 """

    def __init__(self):
        self.driver = None

        self.init_meta_data()

    def init_meta_data(self):
        """ 初始化meta_data，用于存储请求和响应的详细数据 """
        self.meta_data = {
            "name": "",
            "data": [
                {"extract_msgs": {},
                 "request": {
                     "url": "N/A",
                     "method": "N/A",
                     "headers": {}
                 },
                 "response": {
                     "status_code": "N/A",
                     "headers": {},
                     "encoding": None,
                     "content_type": ""
                 }
                 }
            ],
            "stat": {
                "content_size": "N/A",
                "response_time_ms": "N/A",
                "elapsed_ms": "N/A",
            }
        }

    def do_action(self, driver, name=None, variables_mapping={}, **kwargs):
        """ 重写 requests.Session.request 方法，加一个参数 name，用作记录请求的标识"""

        self.init_meta_data()
        self.meta_data["name"] = name  # 记录测试名
        self.meta_data["variables_mapping"] = variables_mapping  # 记录发起此次请求时内存中的自定义变量
        self.meta_data["data"][0]["test_action"] = kwargs  # 记录原始的请求信息

        # 执行前截图
        # self.meta_data["data"][0]['before'] = getattr(driver, 'get_screenshot_as_base64')()

        # 执行测试步骤
        start_timestamp = time.time()
        response = self._do_action(driver, **kwargs)  # 执行步骤

        # 执行后截图
        self.meta_data["data"][0]['after'] = getattr(driver, 'get_screenshot_as_base64')()

        # 记录消耗的时间
        self.meta_data["stat"] = {"response_time_ms": round((time.time() - start_timestamp) * 1000, 2)}

        return response

    def _do_action(self, driver, **kwargs):
        """ 发送HTTP请求，并捕获由于连接问题而可能发生的任何异常。 """
        try:
            doc = getattr(Driver, kwargs.get('action')).__doc__.split('，')[0]
            msg = f"解析后的执行数据:\n> 执行动作：{doc}，定位方式：{kwargs.get('by_type')}，定位元素：{kwargs.get('element')}，文本内容：{kwargs.get('text')}\n"
            logger.log_debug(msg)

            # 以反射机制执行浏览器操作
            action_name = kwargs.get('action')
            action_func = getattr(driver, action_name)

            if 'open' in action_name:  # 打开页面
                return action_func(kwargs.get('element'))

            elif any(key in action_name for key in ['close', 'quit']):  # 不需要定位元素、不需要输入数据的方法，直接执行
                return action_func()

            elif any(key in action_name for key in ['click']):  # 需要定位元素、不需要输入数据的方法
                return action_func((kwargs.get('by_type'), kwargs.get('element')))

            else:  # 需要定位元素、需要输入数据的方法
                return action_func((kwargs.get('by_type'), kwargs.get('element')), kwargs.get('text'))

        except TimeoutException:
            raise RunTimeException('浏览器等待元素超时')

        except InvalidArgumentException:
            raise RunTimeException('元素与操作事件不匹配，请检查元素和操作事件')

        except SessionNotCreatedException:
            raise RunTimeException('实例化浏览器失败，请联系管理员检查驱动与浏览器是否匹配')

        # except Exception as error:
        #     print(111111111111)
        #     print(error)
        #     raise
        #
        # except (BrowserDriverNotFound, UITestRunnerTimeoutException) as error:
        #     print(2222222)
        #     print(error)


if __name__ == '__main__':
    # print(Driver.get_action_mapping())
    # print(Driver.get_assert_mapping())
    driver_path = r'D:\PycharmProjects\ui-auto-test-master\browserdriver\chromedriver.exe'
    driver = Driver(driver_path, 'chrome')
    driver.action_01open('https://www.baidu.com/')
