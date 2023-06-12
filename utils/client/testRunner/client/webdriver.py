# -*- coding: utf-8 -*-
import time

from selenium.common.exceptions import SessionNotCreatedException, InvalidArgumentException, WebDriverException

from utils.client.testRunner import logger
from utils.client.testRunner.client import BaseSession
from utils.client.testRunner.exceptions import TimeoutException, RunTimeException, InvalidElementStateException


class WebDriverSession(BaseSession):
    """ 实例化webdriver，并执行webdriver动作 """

    def __init__(self):
        self.driver = None
        self.init_step_meta_data()

    def do_action(self, driver, name=None, case_id=None, variables_mapping={}, **kwargs):
        """ 重写 requests.Session.request 方法，加一个参数 name，用作记录请求的标识"""

        self.init_step_meta_data()
        self.meta_data["name"] = name  # 记录测试名
        self.meta_data["case_id"] = case_id  # 步骤对应的用例id
        self.meta_data["variables_mapping"] = variables_mapping  # 记录发起此次请求时内存中的自定义变量
        self.meta_data["data"][0]["test_action"] = kwargs  # 记录原始的请求信息

        # 执行前截图
        self.meta_data["data"][0]['before'] = getattr(driver, 'get_screenshot_as_base64')()

        # 执行测试步骤
        start_timestamp = time.time()
        result = self._do_action(driver, **kwargs)  # 执行步骤
        end_timestamp = time.time()

        # 执行后截图
        self.meta_data["data"][0]['after'] = getattr(driver, 'get_screenshot_as_base64')()

        # 记录消耗的时间
        self.meta_data["stat"] = {"response_time_ms": round((end_timestamp - start_timestamp) * 1000, 2)}

        return result

    def _do_action(self, driver, **kwargs):
        """ 发送HTTP请求，并捕获由于连接问题而可能发生的任何异常。 """
        try:
            doc = getattr(driver, kwargs.get('action')).__doc__.split('，')[0]
            msg = f"解析后的执行数据:\n> 执行动作：{doc}，定位方式：{kwargs.get('by_type')}，定位元素：{kwargs.get('element')}，文本内容：{kwargs.get('text')}\n"
            logger.log_debug(msg)

            # 以反射机制执行浏览器操作
            action_name = kwargs.get('action')
            action_func = getattr(driver, action_name)

            if 'open' in action_name:  # 打开页面
                return action_func(kwargs.get('element'))

            elif any(key in action_name for key in ['close', 'quit']):  # 不需要定位元素、不需要输入数据的方法，直接执行
                return action_func()
            else:
                return action_func(
                    (
                        kwargs.get('by_type'),
                        kwargs.get('element')
                    ),
                    kwargs.get('text'),
                    wait_time_out=kwargs.get('wait_time_out')
                )

            # elif any(key in action_name for key in ['click', 'focus']):  # 需要定位元素、不需要输入数据的方法
            #     return action_func(
            #         (
            #             kwargs.get('by_type'),
            #             kwargs.get('element')
            #         ),
            #         wait_time_out=kwargs.get('wait_time_out')
            #     )
            #
            # else:  # 需要定位元素、需要输入数据的方法
            #     return action_func(
            #         (
            #             kwargs.get('by_type'),
            #             kwargs.get('element')
            #         ),
            #         kwargs.get('text'),
            #         wait_time_out=kwargs.get('wait_time_out')
            #     )

        except TimeoutException as error:
            raise RunTimeException('等待元素超时')

        except InvalidArgumentException as error:
            raise RunTimeException('元素与操作事件不匹配，请检查元素和操作事件，异常代码【InvalidArgumentException】')

        except InvalidElementStateException as error:
            raise RunTimeException(f'元素与操作事件不匹配，请检查元素和操作事件\n异常代码【InvalidElementStateException】\n异常内容{error.msg}')

        except SessionNotCreatedException as error:
            raise RunTimeException('实例化浏览器失败，请联系管理员检查驱动与浏览器是否匹配，异常代码【SessionNotCreatedException】')

        except WebDriverException as error:
            raise RunTimeException('事件驱动异常，请查看日志')


if __name__ == '__main__':
    pass
