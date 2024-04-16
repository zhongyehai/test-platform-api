# -*- coding: utf-8 -*-
def parse_cron(expression):
    """ 解析定时任务的时间
     入参 "0,30 1-55 * * * * "
     返回 {"second": "0,30", "minute": "1-55", "hour": "*", "day": "*", "month": "*", "day_of_week": "*"}
     """
    args = {}
    split_exp = expression.split(" ")
    if split_exp[0] != "?":
        args["second"] = split_exp[0]
    if split_exp[1] != "?":
        args["minute"] = split_exp[1]
    if split_exp[2] != "?":
        args["hour"] = split_exp[2]
    if split_exp[3] != "?":
        args["day"] = split_exp[3]
    if split_exp[4] != "?":
        args["month"] = split_exp[4]
    if len(split_exp) >= 6 and split_exp[5] != "?":
        args["day_of_week"] = split_exp[5]
    return args
