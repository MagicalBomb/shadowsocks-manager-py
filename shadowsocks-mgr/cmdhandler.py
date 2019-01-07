'''
    
    This module as handler deal with command received from manager.py

    So most of function don't have to return, just using logging.

'''
import logging
import json
import manager
import socket
import random
import sqlite3
import os
import sys
import mgr_core


# 当前目录
__CURRENT_DIR__ = os.path.dirname(__file__)
# 数据及配置目录
__CONFIG_DIR__ = os.path.join(__CURRENT_DIR__,"config_data")
# 配置数据库及配置文件的位置
__MANAGER_DB__ = os.path.join(__CONFIG_DIR__,"manager.sqlite")
__MANAGER_CONFIG__ = os.path.join(__CONFIG_DIR__,"manager_config.json")
# SS Server 配置文件存放位置
__SS_SER_CONIF_FILE = os.path.join(__CONFIG_DIR__,".ssserver_config.json")
# SS Server 日志文件存放位置
__SS_SER_LOG_FILE = os.path.join(__CONFIG_DIR__,"ssserver_log.log")
# 默认用户信息
__DEFAULT_USER_NAME__ = "root"
__DEFAULT_USER_PWD__ = "magicalbomb"


def init_ss_server():
    '''
    初始化 ss server 数据库
    +
    加入默认用户 root， 密码: magicalbomb

    '''
    if is_init():
        logging.warning("Already initialize manager, you can reinitialize after delete {}".format(os.path.basename(__MANAGER_DB__)))
        sys.exit(1)
    if not os.path.exists(__MANAGER_CONFIG__):
        logging.error("{} don't exist".format(__MANAGER_CONFIG__))
        sys.exit(1)

    # 读取配置
    with open(__MANAGER_CONFIG__,"rb") as fp:
        mgr_config_dict = json.loads(fp.read().decode("utf8"))
        mgr_config = mgr_core.MgrConfig(mgr_config_dict)
    
    # 初始化数据库
    logging.info("Initializing manager.")
    mgr_core.init_ss_manager(mgr_config)


    # 加入默认用户
    logging.info("Adding default user: {}".format(__DEFAULT_USER_NAME__))
    user_manager = mgr_core.UserManager(mgr_config)
    root_user = mgr_core.User()
    root_user.user_name = __DEFAULT_USER_NAME__
    root_user.password = __DEFAULT_USER_PWD__
    root_user.port = mgr_config.base_port
    root_user.is_delete = 0
    root_user.used_statistics = 0 
    root_user.allowed_statistics = 50 * 1024 # in MB
    r = user_manager.create_user(root_user)
    if r.success:
        logging.info("Adding default user successfully.")
    else:
        # 加入默认用户失败， 删掉初始化的数据库，回到最初的状态
        logging.error("Adding default user failed.")
        logging.error("error info : {}".format(r.reason))
        os.remove(__MANAGER_DB__)
        sys.exit(1)

    logging.info("Initialize successfully.")
    
def start_ss_server():
    '''
    mgr_config_file_path    :   str
    '''
    _check_init()

    mgr_config = mgr_core.MgrConfig(mgr_db=__MANAGER_DB__)
    u_mgr = mgr_core.UserManager(mgr_config)
    
    root_user,_ = u_mgr.user_info(__DEFAULT_USER_NAME__)
    mgr_core.start_ss_server(mgr_config,root_user.port,root_user.password)

    def _add_user_to_ssserver(mgr_config,user):
        '''
        user    :   mgr_core.User
        '''

    user_list = []
    for user_name in u_mgr.list_all_users_name():
        user,_ = u_mgr.user_info(user_name)
        if user.is_delete == 0:
            user_list.append(user)

    for user_name in mgr_core.add_users_to_ss_server(mgr_config,user_list):
        logging.info("Add user : {} to ss server successfully".format(user_name))

def stop_ss_server():
    mgr_core.stop_ss_server()

def create_user(user_name,password):
    _check_init()

    def _add_user_to_ssserver(mgr_config,user):
        '''
        user    :   mgr_core.User
        '''
        if not is_ss_server_running():
            return

        mgr_core.add_users_to_ss_server(mgr_config,[user])


    mgr_config = mgr_core.MgrConfig(mgr_db=__MANAGER_DB__)
    u_mgr = mgr_core.UserManager(mgr_config)

    # 创建 User 对象
    user = mgr_core.User()
    user.user_name = user_name
    user.password = password
    user.port = mgr_config.base_port + u_mgr.max_id()
    user.is_delete = 0
    user.used_statistics = 0
    user.allowed_statistics = 50 * 1024 # in MB

    # 将新用户写入 DB
    r = u_mgr.create_user(user)

    if r.success:
        logging.info("Create user : {} in databse successfully".format(user_name))
        try:
            _add_user_to_ssserver(mgr_config,user)
        except Exception as e:
            logging.error("Can't add user to ss server.")
            raise e    
        else:
            logging.info("Add user to ss server successfully".format(user_name))
    else:
        logging.error("Create user : {} failed".format(user_name))
        logging.error("Failed reason: {}".format(r.reason))
        sys.exit(1)

def delete_user(user_name):
    _check_init()

    def _delete_user_from_ss_server(mgr_config,user):
        '''
        mgr_config  :   mgr_core.MgrConfig
        user    :   mgr_core.User
        '''
        if not is_ss_server_running():
            return

        mgr_core.delete_users_from_ss_server(mgr_config,[user])
    
    mgr_config = mgr_core.MgrConfig(mgr_db=__MANAGER_DB__)
    u_mgr = mgr_core.UserManager(mgr_config)
    
    # 获取要删除的用户的信息
    u,r = u_mgr.user_info(user_name)

    # 从数据库删除用户
    if not r.success:
        logging.warning("Can't delete user don't exist")
    elif u.is_delete:
        logging.warning("{} had been already deleted".format(user_name))
    else:
        u_mgr.delete_user(u)
        logging.info("Delete user {} from database successfully".format(user_name))
        try:
            delete_user_from_ss_server(mgr_config,u)
        except Exception as e:
            logging.error("Can't add user to ss server.")
            raise e
        else:
            logging.info("Deleting user from SS Server successfully")
        
def restore_user(user_name):
    _check_init()

    def _add_user_to_ssserver(mgr_config,user):
        '''
        user    :   mgr_core.User
        '''
        if not is_ss_server_running():
            return

        mgr_core.add_users_to_ss_server(mgr_config,[user])



    mgr_config = mgr_core.MgrConfig(mgr_db=__MANAGER_DB__)
    u_mgr = mgr_core.UserManager(mgr_config)

    u,r = u_mgr.user_info(user_name)
    if not r.success:
        logging.warning("Can't restore user don't exist")
    elif not u.is_delete:
        logging.warning("{} is not deleted,dont need to restore".format(user_name))
    else:
        u_mgr.restore_user(u)
        logging.info("Restore user {} in database successfully".format(user_name))
        try:
            _add_user_to_ssserver(mgr_config,user)
        except Exception as e:
            logging.error("Can't add user to ss server.")
            raise e    
        else:
            logging.info("Add user to ss server successfully".format(user_name))

def user_info(user_name):
    _check_init()

    mgr_config = mgr_core.MgrConfig(mgr_db=__MANAGER_DB__)
    u_mgr = mgr_core.UserManager(mgr_config)

    u,r = u_mgr.user_info(user_name)
    
    if not r.success:
        logging.warning(r.reason)
    else:
        def _generate_elegant_str_with_User(user):
            _rtn = "用户名:{user_name},\n密码:{password},\n端口:{port},\n是否被删除:{is_delete},\n已用流量:{used_statistics},\n可用流量:{allowed_statistics}"
            return _rtn.format(
                        user_name = user.user_name,
                        password = user.password,
                        port = user.port,
                        is_delete = '是' if user.is_delete else '否',
                        used_statistics = "{} MB".format(user.used_statistics),
                        allowed_statistics = "{} MB".format(user.allowed_statistics)
                    )
        print(_generate_elegant_str_with_User(u))

def all_users_info():
    _check_init()

    mgr_config = mgr_core.MgrConfig(mgr_db=__MANAGER_DB__)
    u_mgr = mgr_core.UserManager(mgr_config)

    _print_info = []
    _print_info.append("user_name    |   password    |   port    |   is_delete   |   statistics")
    for user_name in u_mgr.list_all_users_name():
        u,r  = u_mgr.user_info(user_name)
        _print_info.append(
            "{}  |   {}  |   {}  |   {}  |   {}/{}".format(
                u.user_name,
                u.password,
                u.port,
                u.is_delete,
                u.used_statistics,
                u.allowed_statistics
            )
        )
    
    for _row in _print_info:
        print(_row)

def refresh():
    '''
    将所有用户再加入一遍服务器
    '''
    _check_init()

    if not is_ss_server_running():
        logging.info("SS Server is not running.")
        return

    mgr_config = mgr_core.MgrConfig(mgr_db=__MANAGER_DB__)
    u_mgr = mgr_core.UserManager(mgr_config)

    user_list = []
    for user_name in u_mgr.list_all_users_name():
        user,_ = u_mgr.user_info(user_name)
        if user.is_delete == 0:
            user_list.append(user)

    for user_name in mgr_core.add_users_to_ss_server(mgr_config,user_list):
        logging.info("Add user : {}").format(user_name)

def start_record():
    _check_init()

    if not is_ss_server_running():
        logging.warning("SS server is not running.")
        sys.exit(1)
        
    mgr_config = mgr_core.MgrConfig(mgr_db=__MANAGER_DB__)
    for record in mgr_core.start_record(mgr_config):
        print("{user_name}   {url}  {time}".format(user_name=record.user_name,url=record.url,time=record.time))

def is_init():
    return os.path.exists(__MANAGER_DB__)

def is_ss_server_running():
    return os.path.exists("/var/run/shadowsocks.pid")

def _check_init():
    if not is_init():
        logging.error("You must init ss server manager firstly")
        sys.exit(1)

if __name__ == "__main__":
    # ser_cmd_handler("start","default_config.json")
    # list_user()
    pass