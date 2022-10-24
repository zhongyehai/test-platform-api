#!/usr/bin/env python

# 提取数据表达式的开头
extract_exp_start = (
    "status_code", "encoding", "ok", "reason", "url", "headers", "elapsed", "cookies", "content", "text", "json"
)

# 支持的请求方法
valid_methods = ["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
# valid_methods = ["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
# if method.upper() not in valid_methods:
#     err_msg = f"请求方法 {method} 错误，仅支持{'/'.join(valid_methods)}"
#     logger.log_error(err_msg)
#     raise exceptions.ParamsError(err_msg)
