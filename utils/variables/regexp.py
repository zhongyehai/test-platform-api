import re

variable_regexp = r"\$([\w_]+)"  # 变量

function_regexp = r"\$\{([\w_]+\([\$\w\.\-/_ =,]*\))\}"  # 自定义函数

function_regexp_compile = re.compile(r"^([\w_]+)\(([\$\w\.\-/_ =,]*)\)$")

absolute_http_url_regexp = re.compile(r"^https?://", re.I)  # http请求

text_extractor_regexp_compile = re.compile(r".*\(.*\).*")
