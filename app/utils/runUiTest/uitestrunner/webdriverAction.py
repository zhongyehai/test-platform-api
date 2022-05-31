import time
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as chromeOptions
from selenium.webdriver.firefox.options import Options as firefoxOptions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.select import Select
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


class GetDriver:
    """ 浏览器对象管理 """

    def __init__(self, browser_driver_path: str):
        """ 实例化浏览器对象
        browser_driver_path: 浏览器驱动地址
        """
        self.browser_driver_path = browser_driver_path

    def chrome(self):
        chrome_options = chromeOptions()

        # 设置配置信息:试了下这个变量还必须是prefs，不然会报错，想不通
        prefs = {'profile.default_content_settings.popups': 0, 'download.default_directory': 'd:\\'}
        chrome_options.add_experimental_option('prefs', prefs)

        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        return webdriver.Chrome(executable_path=self.browser_driver_path, chrome_options=chrome_options)
        # return webdriver.Chrome(executable_path=self.browser_driver_path)

    def firefox(self):
        firefox_options = firefoxOptions()

        firefox_options.set_preference('browser.download.folderList', 2)  # 置成0代表下载到浏览器默认下载路径，设置成2则可以保存到指定的目录
        firefox_options.set_preference('browser.download.dir', 'd:\\')  # 指定存放目录
        firefox_options.set_preference('browser.download.manager.showWhenStarting', False)  # 是否显示开始：True为显示开始，False为不显示开始
        firefox_options.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/octet-stream')  # 对所给文件类型不再弹出框进行询问

        firefox_options.add_argument('--headless')
        firefox_options.add_argument('--no-sandbox')
        firefox_options.add_argument('--disable-dev-shm-usage')
        return webdriver.Firefox(executable_path=self.browser_driver_path, firefox_profile=firefox_options)


class Driver:
    """
    基于原生的selenium框架做了二次封装
    action_开头的为浏览器页面行为，assert_开头的为元素判断
    """

    def __init__(self, browser_driver_path: str, browser_name: str, timeout: int = 30):
        """ 启动浏览器参数化
        browser_driver_path: 浏览器驱动地址
        browser_name: 要实例化的浏览器类型，用于反射GetDriver获取，详见 GetDriver 的方法
        """
        self.driver = getattr(GetDriver(browser_driver_path), browser_name)()  # 获取浏览器对象
        self.timeout = timeout  # 超时的时间设置

    @classmethod
    def get_class_property(cls, startswith: str):
        """ 获取类属性，startswith：方法的开头 """
        mapping_dict, mapping_list = {}, []
        for func_name in dir(Driver):
            if func_name.startswith(startswith):
                doc = getattr(Driver, func_name).__doc__.strip().split('，')[0]  # 函数注释
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

    def web_driver_wait_until(self, *args):
        """ 基于 WebDriverWait().until()封装base方法 """
        return WebDriverWait(self.driver, self.timeout, 1).until(*args)

    def find_element(self, locator: tuple):
        """ 定位一个元素，参数locator是元祖类型，(定位方式, 定位元素)，如('id', 'username')，详见By的用法 """
        return self.web_driver_wait_until(ec.presence_of_element_located(locator))

    def find_elements(self, locator: tuple):
        """ 定位一组元素 """
        return self.web_driver_wait_until(ec.presence_of_all_elements_located(locator))

    def action_01open(self, url: str):
        """ 打开url """
        self.driver.get(url)

    def action_02close(self):
        """ 关闭浏览器 """
        self.driver.close()

    def action_03quit(self):
        """ 关闭窗口 """
        self.driver.quit()

    def action_04click(self, locator: tuple):
        """ 点击元素 """
        self.find_element(locator).click()

    def action_05clear_and_send_keys_need_input(self, locator: tuple, text: str):
        """ 清空后输入，locator = ("id","xxx")，send_keys(locator, text) """
        element = self.find_element(locator)
        element.clear()
        element.send_keys(text)

    def action_06send_keys_need_input(self, locator: tuple, text: str):
        """ 追加输入，locator = ("id","xxx")，send_keys(locator, text) """
        element = self.find_element(locator)
        element.send_keys(text)

    def action_07move_to_element(self, locator: tuple):
        """ 鼠标悬停 """
        ActionChains(self.driver).move_to_element(self.find_element(locator)).perform()

    def action_11js_execute_need_input(self, js: str):
        """ 执行js """
        self.driver.execute_script(js)

    def action_12js_focus_element(self, locator: tuple):
        """ 聚焦元素 """
        self.driver.execute_script("arguments[0].scrollIntoView();", self.find_element(locator))

    def action_13js_scroll_top(self):
        """ 滚动到顶部 """
        self.driver.execute_script("window.scrollTo(0,0)")

    def action_14js_scroll_end(self):
        """ 滚动到底部 """
        self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")

    def action_15select_by_index_need_input(self, locator: tuple, index: int = 0):
        """ 通过索引选中，index是索引第几个，从0开始，默认选第一个 """
        element = self.find_element(locator)
        Select(element).select_by_index(index)
        element.click()

    def action_16select_by_value_need_input(self, locator: tuple, value: str):
        """ 通过value选中 """
        Select(self.find_element(locator)).select_by_value(value)

    def action_17select_by_text_need_input(self, locator: tuple, text: str):
        """ 通过文本值选中 """
        Select(self.find_element(locator)).select_by_visible_text(text)

    def action_18deselect_by_index_need_input(self, locator: tuple, index: int):
        """ 通过index索引定位 """
        Select(self.find_element(locator)).deselect_by_index(index)

    def action_19select_first(self, locator: tuple):
        """ 选中第一个 """
        Select(self.find_element(locator)).first_selected_option()

    def action_20select_all(self, locator: tuple):
        """ 全选 """
        Select(self.find_element(locator)).all_selected_options()

    def action_20get_alert_text(self):
        """ 获取alert文本 """
        return self.driver.switch_to.alert.text

    def action_20click_alert_accept(self):
        """ 点击alert确定按钮 """
        return self.driver.switch_to.alert.accept()

    def action_20click_alert_dismiss(self):
        """ 点击alert取消按钮 """
        return self.driver.switch_to.alert.dismiss()

    def action_20switch_to_window_need_input(self, index: int, *args):
        """ 切换到指定索引的窗口 """
        self.driver.switch_to.window(self.driver.window_handles[int(index)])

    def action_20switch_to_end_window(self, *args):
        """ 切换到最后一个窗口 """
        self.driver.switch_to.window(self.driver.window_handles[-1])

    def action_20upload_file_by_input_need_input(self, locator, file_path, *args):
        """ 通过input上传文件 """
        self.find_element(locator).send_keys(file_path)

    def action_20upload_file_by_perform_need_input(self, locator, file_path, *args):
        """ 通过对话框上传文件 """
        ActionChains(driver).click(self.find_element(locator)).perform()
        # https://blog.csdn.net/looker53/article/details/123962960
        # https://blog.csdn.net/qq_39314932/article/details/124233302

    def action_21deselect_all(self, locator: tuple):
        """ 清除所有的选项 """
        Select(self.find_element(locator)).deselect_all()

    def action_22max_window(self):
        """ 窗口最大化 """
        return self.driver.maximize_window()

    def action_23set_window(self, width: float, height: float):
        """ 窗口缩放为指定大小 """
        return self.driver.set_window_size(float(width), float(height))

    def action_24switch_handle_need_input(self, window_name: str):
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

    def action_29get_size(self, locator: tuple):
        """ 获取元素大小 """
        return self.find_element(locator).size

    def extract_08_title(self, *args):
        """ 获取title """
        return self.driver.title

    def extract_09_text(self, locator: tuple, *args):
        """ 获取文本 """
        return self.find_element(locator).text

    def extract_09_value(self, locator: tuple, *args):
        """ 获取value值 """
        return self.find_element(locator).get_attribute('value')

    def extract_10_attribute_need_input(self, locator: tuple, name: str, *args):
        """ 获取指定属性 """
        return self.find_element(locator).get_attribute(name)

    def assert_50is_exists(self, locator: tuple, *args):
        """ 元素存在 """
        assert self.assert_61is_located(locator)

    def assert_51_element_value_equal_to(self, locator: tuple, content, *args):
        """ 元素value值等于 """
        expect_value = self.extract_09_value(locator)
        # assert expect_value == content, {'expect_value': expect_value}
        assert expect_value == content, expect_value

    def assert_52_element_value_larger_than(self, locator: tuple, content, *args):
        """ 元素value值大于 """
        expect_value = self.extract_09_value(locator)
        assert float(self.extract_09_value(locator)) > content, {'expect_value': expect_value}

    def assert_53_element_value_smaller_than(self, locator: tuple, content, *args):
        """ 元素value值小于 """
        expect_value = self.extract_09_value(locator)
        assert float(self.extract_09_value(locator)) < content, {'expect_value': expect_value}

    def assert_54is_selected_be(self, locator: tuple, *args):
        """ 元素被选中，返回布尔值"""
        assert self.web_driver_wait_until(ec.element_located_selection_state_to_be(locator, True)), {'msg': '元素未被选中'}

    def assert_55is_not_selected_be(self, locator: tuple, *args):
        """ 元素未被选中，返回布尔值"""
        assert self.web_driver_wait_until(ec.element_located_selection_state_to_be(locator, False)), {'msg': '元素已被选中'}

    def assert_56text_in_value(self, locator: tuple, value: str, *args):
        """
        元素value值包含，没定位到元素返回false,定位到返回判断结果布尔值
        result = driver.text_in_element(locator, text)
        """
        expect_value = self.extract_09_value(locator)
        assert value in expect_value, {'expect_value': expect_value}
        # assert self.web_driver_wait_until(ec.text_to_be_present_in_element_value(locator, value))

    def assert_57text_in_element(self, locator: tuple, text: str, *args):
        """
        文本在元素里面，没定位到元素返回False，定位到返回判断结果布尔值
        result = driver.text_in_element(locator, text)
        """
        expect_value = self.extract_09_text(locator)
        assert text in expect_value, {'expect_value': expect_value}
        # assert self.web_driver_wait_until(ec.text_to_be_present_in_element(locator, text))

    def assert_58is_visibility(self, locator: tuple, *args):
        """ 元素可见，不可见返回False """
        assert self.web_driver_wait_until(ec.visibility_of_element_located(locator)), {'msg': '元素可见'}

    def assert_59is_invisibility(self, locator: tuple, *args):
        """ 元素不存在，不存在、不可见返回True """
        assert self.web_driver_wait_until(ec.invisibility_of_element_located(locator)), {'msg': '元素存在'}

    def assert_60is_clickable(self, locator: tuple, *args):
        """ 元素可点击，元素可以点击is_enabled返回本身，不可点击返回False """
        assert self.web_driver_wait_until(ec.element_to_be_clickable(locator)), {'msg': '元素不可点击'}

    def assert_61is_located(self, locator: tuple, *args):
        """ 元素被定为到，（并不意味着可见），定为到返回element, 没定位到返回False """
        assert self.web_driver_wait_until(ec.presence_of_element_located(locator)), {'msg': '元素未被定为到'}

    def assert_62is_title(self, text: str, *args):
        """ 页面title等于 """
        expect_value = self.extract_08_title()
        assert text == expect_value, {'expect_value': expect_value}
        # assert self.web_driver_wait_until(ec.title_is(text))

    def assert_63is_title_contains(self, text: str, *args):
        """ 页面title包含 """
        expect_value = self.extract_08_title()
        assert text in expect_value, {'expect_value': expect_value}
        # assert self.web_driver_wait_until(ec.title_contains(text))

    def assert_64is_alert_present(self, *args):
        """ 页面有alert，有返回alert对象，没有返回False """
        assert self.web_driver_wait_until(ec.alert_is_present()), {'msg': '页面没有alert'}

    def assert_65is_iframe(self, locator: tuple, *args):
        """ 元素为iframe， locator是tuple类型，locator也可以是id和name名称,返回布尔值 """
        assert self.web_driver_wait_until(ec.frame_to_be_available_and_switch_to_it(locator)), {'msg': '元素不为iframe'}

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


if __name__ == '__main__':
    # print(Driver.get_action_mapping())
    # print(Driver.get_assert_mapping())
    driver_path = r'D:\PycharmProjects\ui-auto-test-master\browserdriver\chromedriver.exe'
    driver = Driver(driver_path, 'chrome')
    driver.action_01open('https://www.baidu.com/')
