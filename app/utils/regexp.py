import re

variable_regexp = r"\$([\w_]+)"  # 变量
function_regexp = r"\$\{([\w_]+\([\$\w\.\-/_ =,]*\))\}"  # 自定义函数
function_regexp_compile = re.compile(r"^([\w_]+)\(([\$\w\.\-/_ =,]*)\)$")
