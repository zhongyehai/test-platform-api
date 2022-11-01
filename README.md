# 基于python-flask生态开发的rest风格的测试平台后端

## [体验demo](http://139.196.100.202/#/login) ，  账号：tester、密码：123456

## [去前端](https://github.com/zhongyehai/test-platform-front)

## Python版本：python => 3.9+

### 1.安装依赖包：sudo pip install -i https://pypi.douban.com/simple/ -r requirements.txt

### 2.创建MySQL数据库
    数据库名自己取，编码选择utf8mb4，对应config.yaml下db配置为当前数据库信息即可
    查看最大连接数 show variables like 'max_connections';
    设置最大连接数 set global max_connections=16384;

### 3.初始化数据库表结构（项目根目录下依次执行下面3条命令）：
    sudo python dbMigration.py db init
    sudo python dbMigration.py db migrate
    sudo python dbMigration.py db upgrade

### 4.初始化权限、角色、管理员一起一些初始化配置（项目根目录下执行，账号：admin，密码：123456）
    sudo python dbMigration.py init

### 5、若要进行UI自动化：

    5.1安装浏览器，详见：https://www.cnblogs.com/zhongyehai/p/16266455.html

    5.2.准备浏览器驱动
        5.2.1、根据要用来做自动化的浏览器的类型下载对应版本的驱动，详见：https://www.selenium.dev/documentation/zh-cn/webdriver/driver_requirements/
        5.2.2、把下载的驱动放到项目外的 browser_drivers 路径下，项目启动时若没有则会自动创建，若项目未启动过，则需手动创建

    5.3.给驱动加权限：chmod +x chromedriver


### 6.生产环境下的一些配置:
    1.把main端口改为8024启动
    2.把job端口改为8025启动
    3.准备好前端包，并在nginx.location / 下指定前端包的路径
    4.直接把项目下的nginx.conf文件替换nginx下的nginx.conf文件
    5.nginx -s reload 重启nginx

### 7.启动测试平台
    开发环境: 
        运行测试平台后端 main.py
        运行测试平台定时任务服务 jobServer.py
    
    生产环境:

        运行测试平台：
            使用配置文件: sudo nohup gunicorn -c gunicornConfig.py main:app –preload &
            不使用配置文件: sudo nohup gunicorn -w 1 -b 0.0.0.0:8024 main:app –preload &
        
        运行定时任务服务（定时任务只起一个进程即可，起多了会冲突）：
            不使用配置文件: sudo nohup gunicorn -w 1 -b 0.0.0.0:8025 job:job –preload &
    
    如果报 gunicorn 命令不存在，则先找到 gunicorn 安装目录，创建软连接
    ln -s /usr/local/python3/bin/gunicorn /usr/bin/gunicorn
    ln -s /usr/local/python3/bin/gunicorn  /usr/local/bin/gunicorn
    sudo nohup /usr/local/bin/gunicorn -w 1 -b 0.0.0.0:8024 main:app –preload &

### 修改依赖后创建依赖：sudo pip freeze > requirements.txt


### 创作不易，麻烦给个星哦

### QQ交流群：249728408
### 博客地址：https://www.cnblogs.com/zhongyehai/
