#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2021/11/2 14:05
# @Author : ZhongYeHai
# @Site : 
# @File : models.py
# @Software: PyCharm
from app.baseModel import BaseModel, db


class AutoTestPolyFactoring(BaseModel):
    """ 数据池 """
    __tablename__ = 'auto_test_poly_factoring'
    asset_code = db.Column(db.String(100), nullable=True, default='', comment='资产编号')
    payment_no = db.Column(db.String(100), nullable=True, default='', comment='付款单编号')
    bill_code = db.Column(db.String(100), nullable=True, default='', comment='付款申请单编号')
    batch_no = db.Column(db.String(40), nullable=True, unique=True, default='', comment='批次号')
    batch_code = db.Column(db.String(40), nullable=True, default='', comment='批次号（编号）')
    confirm_date = db.Column(db.TIMESTAMP, nullable=True, default=None, comment='定数时间')
    product_id = db.Column(db.String(40), nullable=True, default='', comment='融资产品id')
    product_name = db.Column(db.String(60), nullable=True, default='', comment='产品名称')
    supplier_org_id = db.Column(db.String(40), nullable=True, default='', comment='债权人公司id')
    supplier_org_name = db.Column(db.String(128), nullable=True, default='', comment='债权人（特定供应商）')
    project_org_id = db.Column(db.String(40), nullable=True, default='', comment='债务人公司id')
    project_org_name = db.Column(db.String(128), nullable=True, default='', comment='债务人（服务公司）')
    purchaser_org_name = db.Column(db.String(128), nullable=True, default='', comment='核心企业名称')
    purchaser_org_id = db.Column(db.String(40), nullable=True, default='', comment='核心企业公司id')
    finance_money = db.Column(db.String(128), nullable=True, default='', comment='融资金额')
    file_upload = db.Column(db.String(10), nullable=True, default='0', comment='文件上传状态(0为上传;1已上传)')
    pledge_init = db.Column(db.String(10), nullable=True, default='0', comment='中登初验(0未进行;1已初验；2已中登)')
    agreement_create = db.Column(db.String(10), nullable=True, default='0', comment='协议生成(0为未生成)')
    document_collect_status = db.Column(db.String(10), nullable=True, default='1', comment='文件收集状态（1未开始;2进行中;3已完成）')
    access_audit_status = db.Column(db.String(10), nullable=True, default='1', comment='准入审核状态（1未开始;2进行中;3不通过;4通过）')
    filter_compare_status = db.Column(db.String(10), nullable=True, default='1', comment='初筛对比状态（1未开始;2进行中;3已完成）')
    six_order_match_status = db.Column(db.String(10), nullable=True, default='1',
                                       comment='六单匹配状态（1未开始,2初审中,3初审不通过,4复审中,5复审通过）')
    pledge_init_status = db.Column(db.String(10), nullable=True, default='1',
                                   comment='中登初验状态（1未开始;2进行中;3复核中;4有风险通过;5无风险通过）')
    agreement_audit_status = db.Column(db.String(10), nullable=True, default='1', comment='协议审核状态（1未开始;2进行中;3不通过;4通过）')
    pledge_status = db.Column(db.String(10), nullable=True, default='1', comment='中登登记状态（1未开始;2进行中;3复核中;4有风险通过;5无风险通过）')
    exception_status = db.Column(db.String(10), nullable=True, default='1', comment='异常状态')
    eliminate_apply_status = db.Column(db.String(10), nullable=True, default='1', comment='剔单申请状态(1默认状态;2剔除申请中;3已剔除；)')
    revoke_status = db.Column(db.String(10), nullable=True, default='1', comment='撤回状态(1默认状态；2已撤回)')
    enable_flag = db.Column(db.String(10), nullable=True, default='1', comment='是否可用（0：不可用；1：可用）')


class AutoTestUser(BaseModel):
    """ 自动化测试用户表 """
    __tablename__ = 'auto_test_user'
    mobile = db.Column(db.String(11), nullable=True, default='', comment='手机号')
    company_name = db.Column(db.String(128), nullable=True, default='', comment='公司名')
    u_token = db.Column(db.String(128), nullable=True, default='', comment='token')
    user_id = db.Column(db.String(128), nullable=True, default='', comment='用户id')
    company_id = db.Column(db.String(128), nullable=True, default='', comment='公司id')
    password = db.Column(db.String(128), nullable=True, default='', comment='密码')
    role = db.Column(db.String(128), nullable=True, default='', comment='角色,平台方admin；核心企业core；供应商supplier；资金方capital')
    comment = db.Column(db.String(256), nullable=True, default='', comment='备注')
