# 老用户
# 1、使用此sql初始化数据库
# 2、执行数据库迁移那3条命令
"""


-- 更新字段值
UPDATE api_test_api set up_func='[]' WHERE up_func in (null, '');
UPDATE api_test_api set down_func='[]' WHERE down_func in (null, '');
UPDATE api_test_api set response='{}' WHERE response is null;
-- 接口0和1互换状态
UPDATE api_test_api set deprecated=-1 WHERE deprecated=1;
UPDATE api_test_api set deprecated=1 WHERE deprecated=0;
UPDATE api_test_api set deprecated=0 WHERE deprecated=-1;
UPDATE api_test_step set up_func='[]' WHERE up_func in (null, '');
UPDATE api_test_step set quote_case=null where quote_case='';
UPDATE api_test_step set data_urlencoded='{}' where data_urlencoded='null';
UPDATE api_test_case_suite set suite_type='make_data' WHERE suite_type='assist';
UPDATE api_test_step set down_func='[]' WHERE down_func in (null, '');
UPDATE api_test_task set email_to='[]' WHERE email_to in (null, '');
UPDATE api_test_task set is_send='not_send' WHERE is_send='1';
UPDATE api_test_task set is_send='always' WHERE is_send='2';
UPDATE api_test_task set is_send='on_fail' WHERE is_send='3';
UPDATE api_test_task SET receive_type = 'not_receive' WHERE receive_type in (null, '');
UPDATE api_test_task SET webhook_list = '[]' WHERE webhook_list is null;
UPDATE api_test_task SET call_back = '[]' WHERE call_back is null;
UPDATE api_test_report set temp_variables='{}' WHERE temp_variables='null';
UPDATE api_test_step set pop_header_filed='[]' WHERE pop_header_filed in (null, '', 'null');

UPDATE app_ui_test_case_suite set suite_type='make_data' WHERE suite_type='assist';
UPDATE app_ui_test_step set up_func='[]' WHERE up_func in (null, '');
UPDATE app_ui_test_step set down_func='[]' WHERE down_func in (null, '');
UPDATE app_ui_test_step set quote_case=null where quote_case='';
UPDATE app_ui_test_task set email_to='[]' WHERE email_to in (null, '');
UPDATE app_ui_test_task set is_send='not_send' WHERE is_send='1';
UPDATE app_ui_test_task set is_send='always' WHERE is_send='2';
UPDATE app_ui_test_task set is_send='on_fail' WHERE is_send='3';
UPDATE app_ui_test_report set temp_variables='{}' WHERE temp_variables='null';
UPDATE app_ui_test_task SET receive_type = 'not_receive' WHERE receive_type in (null, '');
UPDATE app_ui_test_task SET webhook_list = '[]' WHERE webhook_list is null;
UPDATE app_ui_test_task SET call_back = '[]' WHERE call_back is null;

UPDATE web_ui_test_case_suite set suite_type='make_data' WHERE suite_type='assist';
UPDATE web_ui_test_step set up_func='[]' WHERE up_func in (null, '');
UPDATE web_ui_test_step set down_func='[]' WHERE down_func in (null, '');
UPDATE web_ui_test_task set email_to='[]' WHERE email_to in (null, '');
UPDATE web_ui_test_task set is_send='not_send' WHERE is_send='1';
UPDATE web_ui_test_task set is_send='always' WHERE is_send='2';
UPDATE web_ui_test_task set is_send='on_fail' WHERE is_send='3';
UPDATE web_ui_test_task SET receive_type = 'not_receive' WHERE receive_type in (null, '');
UPDATE web_ui_test_task SET webhook_list = '[]' WHERE webhook_list is null;
UPDATE web_ui_test_task SET call_back = '[]' WHERE call_back is null;
UPDATE web_ui_test_step set quote_case=null where quote_case='';
UPDATE web_ui_test_report set temp_variables='{}' WHERE temp_variables='null';

UPDATE config_config set name='holiday_list' where name ='api_holiday_list';

-- 修改字段
ALTER TABLE api_test_project
    RENAME COLUMN created_time TO create_time,
    MODIFY COLUMN script_list JSON comment '引用的脚本文件';

ALTER TABLE api_test_project_env
    RENAME COLUMN created_time TO create_time,
    MODIFY COLUMN headers JSON comment '头部信息',
    MODIFY COLUMN variables JSON comment '公共变量';

ALTER TABLE api_test_module RENAME COLUMN created_time TO create_time;

ALTER TABLE api_test_api
    RENAME COLUMN created_time TO create_time,
    RENAME COLUMN data_type TO body_type,
    RENAME COLUMN deprecated TO status,
    RENAME COLUMN quote_count TO use_count,
    MODIFY COLUMN up_func JSON comment '前置条件',
    MODIFY COLUMN down_func JSON comment '后置条件',
    MODIFY COLUMN headers JSON comment '头部信息',
    MODIFY COLUMN params JSON comment 'url参数',
    MODIFY COLUMN data_form JSON comment 'form-data参数',
    MODIFY COLUMN data_json JSON comment 'json参数',
    MODIFY COLUMN data_urlencoded JSON comment 'form_urlencoded参数',
    MODIFY COLUMN extracts JSON comment '提取信息',
    MODIFY COLUMN validates JSON comment '断言信息',
    MODIFY COLUMN response JSON comment '响应对象';

ALTER TABLE api_test_case_suite RENAME COLUMN created_time TO create_time;

ALTER TABLE api_test_case
    RENAME COLUMN created_time TO create_time,
    MODIFY COLUMN headers JSON comment '头部信息',
    MODIFY COLUMN variables JSON comment '公共变量',
    MODIFY COLUMN script_list JSON comment '引用的脚本文件',
    MODIFY COLUMN skip_if JSON comment '是否跳过的判断条件',
    MODIFY COLUMN output JSON comment '用例出参（步骤提取的数据）';

ALTER TABLE api_test_step
    RENAME COLUMN created_time TO create_time,
    RENAME COLUMN data_type TO body_type,
    MODIFY COLUMN up_func JSON comment '前置条件',
    MODIFY COLUMN down_func JSON comment '后置条件',
    MODIFY COLUMN skip_if JSON comment '是否跳过的判断条件',
    MODIFY COLUMN headers JSON comment '头部信息',
    MODIFY COLUMN params JSON comment 'url参数',
    MODIFY COLUMN data_form JSON comment 'form-data参数',
    MODIFY COLUMN data_json JSON comment 'json参数',
    MODIFY COLUMN data_urlencoded JSON comment 'form_urlencoded参数',
    MODIFY COLUMN extracts JSON comment '提取信息',
    MODIFY COLUMN validates JSON comment '断言信息',
    MODIFY COLUMN pop_header_filed JSON comment '头部参数中去除指定字段';

ALTER TABLE api_test_task
    RENAME COLUMN created_time TO create_time,
    MODIFY COLUMN env_list JSON comment '运行环境',
    MODIFY COLUMN case_ids JSON comment '用例id',
    MODIFY COLUMN suite_ids JSON comment '用例集id',
    MODIFY COLUMN email_to JSON comment '收件人邮箱',
    MODIFY COLUMN call_back JSON comment '回调给流水线',
    MODIFY COLUMN conf JSON comment '运行配置，webUi存浏览器，appUi存运行服务器、手机、是否重置APP',
    MODIFY COLUMN webhook_list JSON comment '机器人地址';

ALTER TABLE api_test_report
    RENAME COLUMN created_time TO create_time,
    RENAME COLUMN run_id TO trigger_id,
    MODIFY COLUMN temp_variables JSON comment '此次运行时指定的临时参数，用于重跑',
    MODIFY COLUMN summary JSON comment '报告的统计';
ALTER TABLE api_test_report
    MODIFY COLUMN trigger_id JSON comment '运行id，用于触发重跑';

ALTER TABLE api_test_report_case
    RENAME COLUMN created_time TO create_time,
    RENAME COLUMN from_id TO case_id,
    MODIFY COLUMN summary JSON comment '用例的报告统计',
    MODIFY COLUMN case_data JSON comment '用例的数据';

ALTER TABLE api_test_report_step
    RENAME COLUMN created_time TO create_time,
    RENAME COLUMN from_id TO element_id,
    MODIFY COLUMN summary JSON comment '步骤的统计',
    MODIFY COLUMN step_data JSON comment '步骤的数据';

ALTER TABLE app_ui_test_run_phone
    RENAME COLUMN created_time TO create_time,
    MODIFY COLUMN extends JSON comment '设备扩展字段';

ALTER TABLE app_ui_test_run_server RENAME COLUMN created_time TO create_time;

ALTER TABLE app_ui_test_project
    RENAME COLUMN created_time TO create_time,
    MODIFY COLUMN script_list JSON comment '引用的脚本文件';

ALTER TABLE app_ui_test_project_env
    RENAME COLUMN created_time TO create_time,
    MODIFY COLUMN variables JSON comment '公共变量';

ALTER TABLE app_ui_test_module RENAME COLUMN created_time TO create_time;

ALTER TABLE app_ui_test_page RENAME COLUMN created_time TO create_time;

ALTER TABLE app_ui_test_element RENAME COLUMN created_time TO create_time;

ALTER TABLE app_ui_test_case_suite RENAME COLUMN created_time TO create_time;

ALTER TABLE app_ui_test_case
    RENAME COLUMN created_time TO create_time,
    MODIFY COLUMN variables JSON comment '公共变量',
    MODIFY COLUMN script_list JSON comment '引用的脚本文件',
    MODIFY COLUMN skip_if JSON comment '是否跳过的判断条件',
    MODIFY COLUMN output JSON comment '用例出参（步骤提取的数据）';

ALTER TABLE app_ui_test_step
    RENAME COLUMN created_time TO create_time,
    MODIFY COLUMN up_func JSON comment '前置条件',
    MODIFY COLUMN down_func JSON comment '后置条件',
    MODIFY COLUMN skip_if JSON comment '是否跳过的判断条件',
    MODIFY COLUMN extracts JSON comment '提取信息',
    MODIFY COLUMN validates JSON comment '断言信息';

ALTER TABLE app_ui_test_task
    RENAME COLUMN created_time TO create_time,
    MODIFY COLUMN env_list JSON comment '运行环境',
    MODIFY COLUMN case_ids JSON comment '用例id',
    MODIFY COLUMN suite_ids JSON comment '用例集id',
    MODIFY COLUMN email_to JSON comment '收件人邮箱',
    MODIFY COLUMN call_back JSON comment '回调给流水线',
    MODIFY COLUMN conf JSON comment '运行配置，webUi存浏览器，appUi存运行服务器、手机、是否重置APP',
    MODIFY COLUMN webhook_list JSON comment '机器人地址';

ALTER TABLE app_ui_test_report
    RENAME COLUMN created_time TO create_time,
    RENAME COLUMN run_id TO trigger_id,
    MODIFY COLUMN temp_variables JSON comment '此次运行时指定的临时参数，用于重跑',
    MODIFY COLUMN summary JSON comment '报告的统计';
ALTER TABLE app_ui_test_report
    MODIFY COLUMN trigger_id JSON comment '运行id，用于触发重跑';

ALTER TABLE app_ui_test_report_case
    RENAME COLUMN created_time TO create_time,
    RENAME COLUMN from_id TO case_id,
    MODIFY COLUMN summary JSON comment '用例的报告统计',
    MODIFY COLUMN case_data JSON comment '用例的数据';

ALTER TABLE app_ui_test_report_step
    RENAME COLUMN created_time TO create_time,
    RENAME COLUMN from_id TO element_id,
    MODIFY COLUMN summary JSON comment '步骤的统计',
    MODIFY COLUMN step_data JSON comment '步骤的数据';

ALTER TABLE web_ui_test_project
    RENAME COLUMN created_time TO create_time,
    MODIFY COLUMN script_list JSON comment '引用的脚本文件';

ALTER TABLE web_ui_test_project_env
    RENAME COLUMN created_time TO create_time,
    MODIFY COLUMN variables JSON comment '公共变量';

ALTER TABLE web_ui_test_module RENAME COLUMN created_time TO create_time;

ALTER TABLE web_ui_test_page RENAME COLUMN created_time TO create_time;

ALTER TABLE web_ui_test_element RENAME COLUMN created_time TO create_time;

ALTER TABLE web_ui_test_case_suite RENAME COLUMN created_time TO create_time;

ALTER TABLE web_ui_test_case
    RENAME COLUMN created_time TO create_time,
    MODIFY COLUMN variables JSON comment '公共变量',
    MODIFY COLUMN script_list JSON comment '引用的脚本文件',
    MODIFY COLUMN skip_if JSON comment '是否跳过的判断条件',
    MODIFY COLUMN output JSON comment '用例出参（步骤提取的数据）';

ALTER TABLE web_ui_test_step
    RENAME COLUMN created_time TO create_time,
    MODIFY COLUMN up_func JSON comment '前置条件',
    MODIFY COLUMN down_func JSON comment '后置条件',
    MODIFY COLUMN skip_if JSON comment '是否跳过的判断条件',
    MODIFY COLUMN extracts JSON comment '提取信息',
    MODIFY COLUMN validates JSON comment '断言信息';

ALTER TABLE web_ui_test_task
    RENAME COLUMN created_time TO create_time,
    MODIFY COLUMN env_list JSON comment '运行环境',
    MODIFY COLUMN case_ids JSON comment '用例id',
    MODIFY COLUMN suite_ids JSON comment '用例集id',
    MODIFY COLUMN email_to JSON comment '收件人邮箱',
    MODIFY COLUMN call_back JSON comment '回调给流水线',
    MODIFY COLUMN conf JSON comment '运行配置，webUi存浏览器，appUi存运行服务器、手机、是否重置APP',
    MODIFY COLUMN webhook_list JSON comment '机器人地址';


ALTER TABLE web_ui_test_report
    RENAME COLUMN created_time TO create_time,
    RENAME COLUMN run_id TO trigger_id,
    MODIFY COLUMN temp_variables JSON comment '此次运行时指定的临时参数，用于重跑',
    MODIFY COLUMN summary JSON comment '报告的统计';
ALTER TABLE web_ui_test_report
    MODIFY COLUMN trigger_id JSON comment '运行id，用于触发重跑';

ALTER TABLE web_ui_test_report_case
    RENAME COLUMN from_id TO case_id,
    RENAME COLUMN created_time TO create_time,
    MODIFY COLUMN summary JSON comment '用例的报告统计',
    MODIFY COLUMN case_data JSON comment '用例的数据';

ALTER TABLE web_ui_test_report_step
    RENAME COLUMN created_time TO create_time,
    RENAME COLUMN from_id TO element_id,
    MODIFY COLUMN summary JSON comment '步骤的统计',
    MODIFY COLUMN step_data JSON comment '步骤的数据';

ALTER TABLE apscheduler_jobs RENAME COLUMN created_time TO create_time;

ALTER TABLE auto_test_call_back
    RENAME COLUMN created_time TO create_time,
    MODIFY COLUMN headers JSON comment '头部参数',
    MODIFY COLUMN data_form JSON comment 'form_data参数',
    MODIFY COLUMN data_json JSON comment 'json参数',
    MODIFY COLUMN params JSON comment '查询字符串参数';

ALTER TABLE auto_test_data_pool RENAME COLUMN created_time TO create_time;

ALTER TABLE auto_test_hits RENAME COLUMN created_time TO create_time;

ALTER TABLE auto_test_user RENAME COLUMN created_time TO create_time;

ALTER TABLE config_business
    RENAME COLUMN created_time TO create_time,
    MODIFY COLUMN webhook_list JSON comment '接收该业务线自动化测试阶段统计通知地址',
    MODIFY COLUMN env_list JSON comment '业务线能使用的运行环境';

ALTER TABLE config_config RENAME COLUMN created_time TO create_time;
ALTER TABLE config_run_env RENAME COLUMN created_time TO create_time;
ALTER TABLE config_type RENAME COLUMN created_time TO create_time;
ALTER TABLE func_error_record RENAME COLUMN created_time TO create_time;
ALTER TABLE python_script RENAME COLUMN created_time TO create_time;
ALTER TABLE swagger_diff_record RENAME COLUMN created_time TO create_time;
ALTER TABLE swagger_pull_log
    RENAME COLUMN created_time TO create_time,
    MODIFY COLUMN pull_args JSON comment '拉取时指定的参数';

ALTER TABLE system_error_record RENAME COLUMN created_time TO create_time;
ALTER TABLE system_job_run_log RENAME COLUMN created_time TO create_time;
ALTER TABLE system_permission RENAME COLUMN created_time TO create_time;
ALTER TABLE system_role
    RENAME COLUMN created_time TO create_time,
    MODIFY COLUMN extend_role JSON comment '继承其他角色的权限';

ALTER TABLE system_role_permissions RENAME COLUMN created_time TO create_time;

ALTER TABLE system_user
    RENAME COLUMN created_time TO create_time,
    MODIFY COLUMN business_list JSON comment '用户拥有的业务线';

ALTER TABLE system_user_operation_log RENAME COLUMN created_time TO create_time;
ALTER TABLE system_user_roles RENAME COLUMN created_time TO create_time;
ALTER TABLE test_work_bug_track RENAME COLUMN created_time TO create_time;
ALTER TABLE test_work_env RENAME COLUMN created_time TO create_time;
ALTER TABLE test_work_kym
    RENAME COLUMN created_time TO create_time,
    MODIFY COLUMN kym JSON comment 'kym分析';

ALTER TABLE test_work_weekly
    RENAME COLUMN created_time TO create_time,
    MODIFY COLUMN task_item JSON comment '任务明细和进度';

ALTER TABLE test_work_weekly_config RENAME COLUMN created_time TO create_time;


"""
