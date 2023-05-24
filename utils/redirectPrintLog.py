import sys

from utils.util.fileUtil import FileUtil


def redirect_print_log_to_file(file_name):
    """ 重定向print内容到文本中 """
    sys.stdout = open(FileUtil.get_script_print_addr(file_name), "a", encoding='utf8')

    # sys.stdout = sys.__stdout__  # 恢复输出到console


class RedirectPrintLogToMemory:
    """ 重定向print内容到内存中 """

    def __init__(self):
        self.text = ""
        sys.stdout = self

    def write(self, out_stream):
        self.text += out_stream

    def flush(self):
        pass

    @classmethod
    def redirect_to_default(cls):
        """ 恢复输出到console """
        sys.stdout = sys.__stdout__

    # def __del__(self):
    #     """ 恢复输出到console """
    #     sys.stdout = sys.__stdout__
