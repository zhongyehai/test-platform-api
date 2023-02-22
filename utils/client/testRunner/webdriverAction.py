# -*- coding: utf-8 -*-
import base64
import json
import textwrap
import time
import os

from appium import webdriver as appium_webdriver
from appium.webdriver.common.touch_action import TouchAction
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as chromeOptions
from selenium.webdriver.firefox.options import Options as firefoxOptions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.select import Select
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from .utils import get_dict_data


class Actions:
    """
    基于原生的selenium框架做了二次封装
    action_开头的为浏览器页面行为，assert_开头的为元素判断
    """

    def __init__(self, driver):
        self.driver = driver
        self.wait_time_out = 5  # 默认超时的时间设置

    @property
    def width(self):
        """ 获取手机屏幕宽度 """
        return self.driver.get_window_size()['width']

    @property
    def height(self):
        """ 获取屏幕高度 """
        return self.driver.get_window_size()['height']

    @classmethod
    def get_class_property(cls, startswith: str):
        """ 获取类属性，startswith：方法的开头 """
        mapping_dict, mapping_list = {}, []
        for func_name in dir(cls):
            if func_name.startswith(startswith):
                doc = getattr(cls, func_name).__doc__.strip().split('，')[0]  # 函数注释
                mapping_dict.setdefault(doc, func_name)
                mapping_list.append({'label': doc, 'value': func_name})
        return {"mapping_dict": mapping_dict, "mapping_list": mapping_list}

    @classmethod
    def get_action_mapping(cls):
        """ 获取浏览器行为事件 """
        return cls.get_class_property('action_')

    @classmethod
    def get_assert_mapping(cls):
        """ 获取浏览器判断事件 """
        return cls.get_class_property('assert_')

    @classmethod
    def get_extract_mapping(cls):
        """ 获取浏览器提取数据事件 """
        return cls.get_class_property('extract_')

    def web_driver_wait_until(self, *args, **kwargs):
        """ 基于 WebDriverWait().until()封装base方法 """
        return WebDriverWait(self.driver, kwargs.get('wait_time_out', self.wait_time_out), 1).until(*args)

    def find_element(self, locator: tuple, wait_time_out=None, *args, **kwargs):
        """ 定位一个元素，参数locator是元祖类型，(定位方式, 定位元素)，如('id', 'username')，详见By的用法 """
        return self.web_driver_wait_until(
            ec.presence_of_element_located(locator),
            wait_time_out=wait_time_out or self.wait_time_out
        )

    def find_elements(self, locator: tuple, wait_time_out=None):
        """ 定位一组元素 """
        return self.web_driver_wait_until(
            ec.presence_of_all_elements_located(locator),
            wait_time_out=wait_time_out or self.wait_time_out
        )

    def action_01open(self, url: str, *args, **kwargs):
        """ 打开url """
        self.driver.get(url)

    def action_06close(self, *args, **kwargs):
        """ 关闭浏览器 """
        self.driver.close()

    def action_07quit(self, *args, **kwargs):
        """ 关闭窗口 """
        self.driver.quit()

    def action_04click(self, locator: tuple, text: str = '', wait_time_out=None):
        """ 点击元素 """
        if locator[0] == 'coordinate':  # 坐标定位
            coordinate = eval(locator[1])
            TouchAction(self.driver).tap(x=coordinate[0], y=coordinate[1]).perform()
        else:  # 元素定位
            self.find_element(locator, wait_time_out=wait_time_out).click()

    def action_04sleep_is_input(self, locator: tuple, time_seconds: (int, float, str), wait_time_out=None):
        """ 等待指定时间 """
        time.sleep(float(time_seconds) if isinstance(time_seconds, str) else time_seconds)

    def action_04clear_and_send_keys_is_input(self, locator: tuple, text: str = '', wait_time_out=None):
        """ 清空后输入，locator = ("id","xxx")，send_keys(locator, text)， is_input标识为输入内容 """
        element = self.find_element(locator, wait_time_out=wait_time_out)
        element.clear()
        element.send_keys(text)

    def action_04send_keys_is_input(self, locator: tuple, text: str = '', wait_time_out=None):
        """ 追加输入，locator = ("id","xxx")，send_keys(locator, text)， is_input标识为输入内容 """
        element = self.find_element(locator, wait_time_out=wait_time_out)
        element.send_keys(text)

    def action_04send_keys_by_keyboard_is_input(self, locator: tuple, text: str = '', wait_time_out=None):
        """ 模拟键盘输入，locator = ("id","xxx")，send_keys(locator, text)， is_input标识为输入内容 """
        self.driver.press_keycode(text)

    def action_05click_and_clear_and_send_keys_is_input(self, locator: tuple, text: str = '', wait_time_out=None):
        """ 点击并清空后输入，locator = ("id","xxx")，send_keys(locator, text)， is_input标识为输入内容 """
        element = self.find_element(locator, wait_time_out=wait_time_out)
        element.click()
        element.clear()
        element.send_keys(text)

    def action_04click_and_send_keys_is_input(self, locator: tuple, text: str = '', wait_time_out=None):
        """ 点击并追加输入，locator = ("id","xxx")，send_keys(locator, text)， is_input标识为输入内容 """
        element = self.find_element(locator, wait_time_out=wait_time_out)
        element.click()
        element.send_keys(text)

    def action_04click_and_send_keys_by_keyboard_is_input(self, locator: tuple, text: str = '', wait_time_out=None):
        """ 点击并模拟键盘输入，locator = ("id","xxx")，send_keys(locator, text)， is_input标识为输入内容 """
        self.find_element(locator, wait_time_out=wait_time_out).click()
        self.driver.press_keycode(text)

    def action_07move_to_element(self, locator: tuple, text: str = '', wait_time_out=None):
        """ 鼠标悬停 """
        ActionChains(self.driver).move_to_element(self.find_element(locator, wait_time_out=wait_time_out)).perform()

    def action_11js_execute_is_input(self, js: str, *args, **kwargs):
        """ 执行js， is_input标识为输入内容 """
        self.driver.execute_script(js)

    def action_12js_focus_element(self, locator: tuple, text: str = '', wait_time_out=None):
        """ 聚焦元素 """
        self.driver.execute_script(
            "arguments[0].scrollIntoView();",
            self.find_element(locator, wait_time_out=wait_time_out)
        )

    def action_13js_scroll_top(self, *args, **kwargs):
        """ 滚动到浏览器顶部 """
        self.driver.execute_script("window.scrollTo(0,0)")

    def action_14js_scroll_end(self, *args, **kwargs):
        """ 滚动到浏览器底部 """
        self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")

    def action_14app_scroll_coordinate_is_input1(self, conf={}, *args, **kwargs):
        """ 滚动到手机指定坐标(相对位置)，
        conf: {
            "x1": 0.2, "y1": 0.7, "x2": 0.1, "y2": 0.4
        }
        """
        x1, y1 = self.width * float(conf.get("x1", 0.5)), self.height * float(conf.get("y1", 3 / 4))
        x2, y2 = self.width * float(conf.get("x2", 0.5)), self.height * float(conf.get("y2", 1 / 4))
        self.driver.swipe(x1, y1, x2, y2, 2000)  # 两秒完成滑动

    def action_14app_scroll_coordinate_is_input2(self, conf={}, *args, **kwargs):
        """ 滚动到手机指定坐标(绝对位置)，
        conf: {
            "x1": 500, "y1": 1000, "x2": 600, "y2": 1024
        }
        """
        x1, y1 = float(conf.get("x1", 500)), float(conf.get("y1", 1000))
        x2, y2 = float(conf.get("x2", 600)), float(conf.get("y2", 1024))
        self.driver.swipe(x1, y1, x2, y2)  # 两秒完成滑动

    def action_14app_scroll_coordinate_end(self, *args, **kwargs):
        """ 滚动到手机底部 """
        before_swipe = self.driver.page_source  # 滚动前的页面资源
        self.action_14app_scroll_coordinate_is_input1({"y1": 3 / 4, "y2": -1 / 9999})
        after_swipe = self.driver.page_source  # 滚动后的页面资源
        if before_swipe != after_swipe:  # 如果滚动前和滚动后的页面不一致，说明进行了滚动，则继续滚动，否则证明已经滚动到底，不再滚动
            self.action_14app_scroll_coordinate_end()

    def action_15select_by_index_is_input(self, locator: tuple, index: int = 0, wait_time_out=None):
        """ 通过索引选中，index是索引第几个，从0开始，默认选第一个， is_input标识为输入内容 """
        element = self.find_element(locator, wait_time_out=wait_time_out)
        Select(element).select_by_index(index)
        element.click()

    def action_16select_by_value_is_input(self, locator: tuple, value: str = '', wait_time_out=None):
        """ 通过value选中， is_input标识为输入内容 """
        Select(self.find_element(locator, wait_time_out=wait_time_out)).select_by_value(value)

    def action_17select_by_text_is_input(self, locator: tuple, text: str = '', wait_time_out=None):
        """ 通过文本值选中 """
        Select(self.find_element(locator, wait_time_out=wait_time_out)).select_by_visible_text(text)

    def action_18deselect_by_index_is_input(self, locator: tuple, index: int = 0, wait_time_out=None):
        """ 通过index索引定位， is_input标识为输入内容 """
        Select(self.find_element(locator, wait_time_out=wait_time_out)).deselect_by_index(index)

    def action_19select_first(self, locator: tuple, text: str = '', wait_time_out=None):
        """ 选中第一个 """
        Select(self.find_element(locator, wait_time_out=wait_time_out)).first_selected_option()

    def action_20select_all(self, locator: tuple, text: str = '', wait_time_out=None):
        """ 全选 """
        Select(self.find_element(locator, wait_time_out=wait_time_out)).all_selected_options()

    def action_20get_alert_text(self):
        """ 获取alert文本 """
        return self.driver.switch_to.alert.text

    def action_20click_alert_accept(self):
        """ 点击alert确定按钮 """
        return self.driver.switch_to.alert.accept()

    def action_20click_alert_dismiss(self):
        """ 点击alert取消按钮 """
        return self.driver.switch_to.alert.dismiss()

    def action_20switch_to_window_is_input(self, index: int = 0, *args):
        """ 切换到指定索引的窗口，is_input标识为输入内容 """
        self.driver.switch_to.window(self.driver.window_handles[int(index)])

    def action_20switch_to_end_window(self, *args):
        """ 切换到最后一个窗口 """
        self.driver.switch_to.window(self.driver.window_handles[-1])

    def action_20app_upload_file_is_upload(self, locator, file_path, *args, wait_time_out=None):
        """ APP上传文件， is_upload标识为文件上传 """
        with open(file_path, 'r', encoding='utf8') as f:
            content = bytes(f.read(), 'utf-8')
        self.driver.push_file(file_path, base64.b64encode(content).decode('utf-8'))

    def action_20upload_file_by_input_is_upload(self, locator, file_path, *args, wait_time_out=None):
        """ 通过input上传文件， is_upload标识为文件上传 """
        self.find_element(locator, wait_time_out=wait_time_out).send_keys(file_path)

    def action_20upload_file_by_perform_is_upload(self, locator, file_path, *args, wait_time_out=None):
        """ 通过对话框上传文件， is_upload标识为文件上传 """
        ActionChains(driver).click(self.find_element(locator, wait_time_out=wait_time_out)).perform()
        # https://blog.csdn.net/looker53/article/details/123962960
        # https://blog.csdn.net/qq_39314932/article/details/124233302

    def action_21deselect_all(self, locator: tuple, text: str = '', wait_time_out=None):
        """ 清除所有的选项 """
        Select(self.find_element(locator, wait_time_out=wait_time_out)).deselect_all()

    def action_22max_window(self):
        """ 窗口最大化 """
        return self.driver.maximize_window()

    def action_23set_window(self, width: float, height: float):
        """ 窗口缩放为指定大小 """
        return self.driver.set_window_size(float(width), float(height))

    def action_24switch_handle_is_input(self, window_name: str):
        """ 切换到窗口名对应的窗口 """
        self.driver.switch_to.window(window_name)

    def action_25switch_iframe(self, locator: tuple):
        """ 切换到指定的iframe """
        return self.assert_65is_iframe(locator)

    def action_26get_current_handle(self):
        """ 获取当前句柄 """
        return self.driver.current_window_handle

    def action_27get_handles(self):
        """ 获取所有句柄 """
        return self.driver.window_handles

    def action_28get_name(self):
        """ 获取浏览器名称 """
        return self.driver.name

    def action_29get_size(self, locator: tuple, wait_time_out=None):
        """ 获取元素大小 """
        return self.find_element(locator, wait_time_out=wait_time_out).size

    def action_30get_local_storage_value_is_input(self, locator: tuple, key: str, *args):
        """ 根据key从localStorage中获取数据 """
        return self.driver.execute_script(f"window.localStorage.getItem('{key}');")

    def action_30set_local_storage_value_by_dict_is_input(self, locator: tuple, data: dict, *args):
        """ 以字典的形式在localStorage中设置数据 """
        for key, value in get_dict_data(data).items():
            self.driver.execute_script(f"window.localStorage.setItem('{key}', '{value}');")

    def action_30remove_local_storage_value_is_input(self, locator: tuple, key: str, *args):
        """ 根据key在localStorage中删除数据 """
        return self.driver.execute_script(f"window.localStorage.removeItem('{key}');")

    def action_30clear_local_storage_value(self, *args):
        """ 清空localStorage中的所有数据 """
        return self.driver.execute_script("window.localStorage.clear();")

    def action_31get_session_storage_value_is_input(self, key: str, *args):
        """ 根据key从sessionStorage中获取数据 """
        return self.driver.execute_script(f"window.sessionStorage.getItem('{key}');")

    def action_31set_session_storage_value_by_dict_is_input(self, locator: tuple, data: dict, *args):
        """ 以字典的形式在sessionStorage中设置数据 """
        for key, value in get_dict_data(data).items():
            self.driver.execute_script(f"window.sessionStorage.setItem('{key}', '{value}');")

    def action_31remove_session_storage_value_is_input(self, locator: tuple, key: str, *args):
        """ 根据key在sessionStorage中删除数据 """
        return self.driver.execute_script(f"window.sessionStorage.removeItem('{key}');")

    def action_31clear_session_storage_value(self, *args):
        """ 清空sessionStorage中的所有数据 """
        return self.driver.execute_script("window.sessionStorage.clear();")

    def action_32get_all_cookie(self, *args):
        """ 获取cookie中的所有数据 """
        return self.driver.get_cookies()

    def action_32get_cookie_is_input(self, locator: tuple, name: str, *args):
        """ 根据key获取cookie中的指定数据 """
        return self.driver.get_cookie(name)

    def action_32add_cookie_by_dict_is_input(self, locator: tuple, cookie, *args):
        """ 以字典形式添加cookie """
        for key, value in get_dict_data(cookie).items():
            self.driver.add_cookie({"name": key, "value": value})

    def action_32delete_cookie_is_input(self, locator: tuple, name: str, *args):
        """ 根据key删除cookie中的指定数据 """
        return self.driver.delete_cookie(name)

    def action_32delete_all_cookie(self, *args):
        """ 删除cookie中的所有数据 """
        return self.driver.delete_all_cookies()

    def extract_08_title(self, *args):
        """ 获取title """
        return self.driver.title

    def extract_09_text(self, locator: tuple, *args, wait_time_out=None):
        """ 获取文本 """
        return self.find_element(locator, wait_time_out=wait_time_out).text

    def extract_09_value(self, locator: tuple, *args, wait_time_out=None):
        """ 获取value值 """
        return self.find_element(locator, wait_time_out=wait_time_out).get_attribute('value')

    def extract_09_cookie(self, locator: tuple, *args, wait_time_out=None):
        """ 获取cookie值 """
        print(self.driver.execute_driver(script=textwrap.dedent(f"return localStorage;")))
        print(self.driver.execute_driver(script=textwrap.dedent(f"return sessionStorage;")))
        print(self.driver.execute_script(f"return localStorage;"))
        print(self.driver.execute_script(f"return sessionStorage;"))
        print(self.driver.get_cookies())
        return self.driver.get_cookies()

    def extract_10_attribute_is_input(self, locator: tuple, name: str, *args, wait_time_out=None):
        """ 获取指定属性 """
        return self.find_element(locator, wait_time_out=wait_time_out).get_attribute(name)

    # def assert_50is_exists(self, locator: tuple, *args):
    #     """ 元素存在 """
    #     assert self.assert_61is_located(locator)

    def assert_50str_in_value(self, locator: tuple, value: str, *args):
        """
        元素value值包含，没定位到元素返回false,定位到返回判断结果布尔值
        result = driver.text_in_element(locator, text)
        """
        expect_value = self.extract_09_value(locator)
        assert value in expect_value, {'expect_value': expect_value}

    def assert_51_element_value_equal_to(self, locator: tuple, content, *args):
        """ 元素value值等于 """
        expect_value = self.extract_09_value(locator)
        # assert expect_value == content, {'expect_value': expect_value}
        assert expect_value == content, f'实际结果：{expect_value}'

    def assert_52_element_value_larger_than(self, locator: tuple, content, *args):
        """ 元素value值大于 """
        expect_value = self.extract_09_value(locator)
        assert float(expect_value) > content, {'expect_value': expect_value}

    def assert_53_element_value_smaller_than(self, locator: tuple, content, *args):
        """ 元素value值小于 """
        expect_value = self.extract_09_value(locator)
        assert float(expect_value) < content, {'expect_value': expect_value}

    def assert_54is_selected_be(self, locator: tuple, *args, wait_time_out=None):
        """ 元素被选中，返回布尔值"""
        assert self.web_driver_wait_until(
            ec.element_located_selection_state_to_be(locator, True),
            wait_time_out=wait_time_out or self.wait_time_out
        ), {'msg': '元素未被选中'}

    def assert_55is_not_selected_be(self, locator: tuple, *args, wait_time_out=None):
        """ 元素未被选中，返回布尔值"""
        assert self.web_driver_wait_until(
            ec.element_located_selection_state_to_be(locator, False),
            wait_time_out=wait_time_out or self.wait_time_out
        ), {
            'msg': '元素已被选中'}

    def assert_56_element_txt_equal_to(self, locator: tuple, content, *args):
        """ 元素txt值等于 """
        expect_value = self.extract_09_text(locator)
        # assert expect_value == content, {'expect_value': expect_value}
        assert expect_value == content, f'实际结果：{expect_value}'

    def assert_56_element_txt_larger_than(self, locator: tuple, content, *args):
        """ 元素txt值大于 """
        expect_value = self.extract_09_text(locator)
        assert float(expect_value) > content, {'expect_value': expect_value}

    def assert_56_element_txt_smaller_than(self, locator: tuple, content, *args):
        """ 元素txt值小于 """
        expect_value = self.extract_09_text(locator)
        assert float(expect_value) < content, {'expect_value': expect_value}

    def assert_57text_in_element(self, locator: tuple, text: str, *args):
        """
        元素txt值包含，没定位到元素返回False，定位到返回判断结果布尔值
        result = driver.text_in_element(locator, text)
        """
        expect_value = self.extract_09_text(locator)
        assert text in expect_value, {'expect_value': expect_value}

    def assert_58is_visibility(self, locator: tuple, *args, wait_time_out=None):
        """ 元素可见，不可见返回False """
        assert self.web_driver_wait_until(
            ec.visibility_of_element_located(locator),
            wait_time_out=wait_time_out or self.wait_time_out
        ), {'msg': '元素可见'}

    # def assert_59is_invisibility(self, locator: tuple, *args, wait_time_out=None):
    #     """ 元素不存在，不存在、不可见返回True """
    #     assert self.web_driver_wait_until(
    #         ec.invisibility_of_element_located(locator),
    #         wait_time_out=wait_time_out or self.wait_time_out
    #     ), {'msg': '元素存在'}

    def assert_60is_clickable(self, locator: tuple, *args, wait_time_out=None):
        """ 元素可点击，元素可以点击is_enabled返回本身，不可点击返回False """
        assert self.web_driver_wait_until(
            ec.element_to_be_clickable(locator),
            wait_time_out=wait_time_out or self.wait_time_out
        ), {'msg': '元素不可点击'}

    def assert_61is_located(self, locator: tuple, *args, wait_time_out=None):
        """ 元素被定为到，（并不意味着可见），定为到返回element, 没定位到返回False """
        assert self.web_driver_wait_until(
            ec.presence_of_element_located(locator),
            wait_time_out=wait_time_out or self.wait_time_out
        ), {'msg': '元素未被定为到'}

    def assert_62is_title(self, text: str, *args):
        """ 页面title等于 """
        expect_value = self.extract_08_title()
        assert text == expect_value, {'expect_value': expect_value}

    def assert_63is_title_contains(self, text: str, *args):
        """ 页面title包含 """
        expect_value = self.extract_08_title()
        assert text in expect_value, {'expect_value': expect_value}

    def assert_64is_alert_present(self, *args, wait_time_out=None):
        """ 页面有alert，有返回alert对象，没有返回False """
        assert self.web_driver_wait_until(
            ec.alert_is_present(),
            wait_time_out=wait_time_out or self.wait_time_out
        ), {'msg': '页面没有alert'}

    def assert_65is_iframe(self, locator: tuple, *args, wait_time_out=None):
        """ 元素为iframe， locator是tuple类型，locator也可以是id和name名称,返回布尔值 """
        assert self.web_driver_wait_until(
            ec.frame_to_be_available_and_switch_to_it(locator),
            wait_time_out=wait_time_out or self.wait_time_out
        ), {'msg': '元素不为iframe'}

    # def is_selected_(self, locator):
    #     """ 元素被选中，返回布尔值 """
    #     return self.web_driver_wait_until(ec.element_located_to_be_selected(locator))

    def get_screenshot(self, image_path: str):
        """ 获取屏幕截图, 保存为文件 """
        self.driver.get_screenshot_as_file(os.path.join(image_path, time.strftime("%Y-%m-%d %H_%M_%S") + ".png"))

    def get_screenshot_as_base64(self):
        """ 获取屏幕截图，保存的是base64的编码格式，在HTML界面输出截图的时候，会用到 """
        return self.driver.get_screenshot_as_base64()

    def get_screenshot_as_file(self, filename: str):
        """ 获取屏幕截图，保存为二进制数据 """
        return self.driver.get_screenshot_as_file(filename)

    def get_screenshot_as_png(self):
        """ 获取屏幕截图, 保存为png格式 """
        return self.driver.get_screenshot_as_png()


class GetWebDriver(Actions):
    """ 浏览器对象管理 """

    def __init__(self, browser_driver_path: str, browser_name: str):
        """ 实例化浏览器对象
        browser_driver_path: 浏览器驱动地址
        """
        self.browser_driver_path = browser_driver_path
        self.browser_name = browser_name
        self.driver = self.get_driver()
        super().__init__(self.driver)

    def __del__(self):
        try:
            self.driver.close()
        except:
            pass
        try:
            self.driver.quit()
        except:
            pass
        try:
            self.driver.close_app()
        except:
            pass

    def get_driver(self):
        """ 获取浏览器实例 """
        return getattr(self, self.browser_name)()  # 获取浏览器对象

    def chrome(self):
        """ chrome浏览器 """
        chrome_options = chromeOptions()

        # 设置配置信息
        prefs = {'profile.default_content_settings.popups': 0, 'download.default_directory': 'd:\\'}
        chrome_options.add_experimental_option('prefs', prefs)

        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        return webdriver.Chrome(executable_path=self.browser_driver_path, chrome_options=chrome_options)
        # return webdriver.Chrome(executable_path=self.browser_driver_path)

    def gecko(self):
        """ 火狐浏览器 """
        firefox_options = firefoxOptions()

        # 置成0代表下载到浏览器默认下载路径，设置成2则可以保存到指定的目录
        firefox_options.set_preference('browser.download.folderList', 2)
        # 指定存放目录
        firefox_options.set_preference('browser.download.dir', 'd:\\')
        # 是否显示开始：True为显示开始，False为不显示开始
        firefox_options.set_preference('browser.download.manager.showWhenStarting', False)
        # 对所给文件类型不再弹出框进行询问
        firefox_options.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/octet-stream')

        firefox_options.add_argument('--headless')
        firefox_options.add_argument('--no-sandbox')
        firefox_options.add_argument('--disable-dev-shm-usage')
        return webdriver.Firefox(executable_path=self.browser_driver_path, firefox_profile=firefox_options)


class GetAppDriver(Actions):
    """ appium对象管理 """

    def __init__(self, **kwargs):
        """ 获取appium操作对象
        {
            "platformName": "iOS" / "Android",
            "platformVersion": "14.5",
            "deviceName": "iPhone Simulator" / other,
            appPackage='com.taobao.taobao',
            appActivity='com.taobao.tao.TBMainActivity',
            noReset=True
        }
        """

        self.host, self.port = kwargs.pop('host'), kwargs.pop('port')
        self.appium_webdriver = appium_webdriver.Remote(f'http://{self.host}:{self.port}/wd/hub', kwargs)  # 启动app
        super().__init__(self.appium_webdriver)


if __name__ == '__main__':
    # print(Driver.get_action_mapping())
    # print(Driver.get_assert_mapping())
    driver_path = r'D:\项目\test-platform\base\api\browser_drivers\chromedriver.exe'
    driver = GetWebDriver(driver_path, 'chrome')
    driver.action_01open('https://www.baidu.com/')
