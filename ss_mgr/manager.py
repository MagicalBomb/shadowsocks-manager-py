#   本脚本是整个程序的入口
#   其主要任务用于正确获取用户的输入，即充当人机接口职能。
#   只适用 Unix-like 系统
#    
#   "server_address": "0.0.0.0",
#   "base_port": 10000,
#   "root_password": "magicalbomb",
#   "timeout": 300,
#   "method": "aes-256-cfb"
#   "acc_rec_out_cli_port":9999,
#   "acc_rec_out_ser_port":9998,
#   "manager_port":9997
#
#   acc_rec_out_cli_port: SS 服务器输出访问记录时，用于接受信息的端口号
#   acc_rec_out_ser_port:   SS 服务器输出方位记录时，服务器位于的端口号
#   base_port:  SS 服务器多用户下，端口号从 base_port 开始自增， base_port 分配给默认的 root 用户 


import sys
import os
sys.path.append(os.path.dirname(__file__))

import argparse
import threading
import json
import logging
import sqlite3
from pprint import pprint as pp
import cmdhandler
import os



# 本包目录
__PACKAGE_DIR_NAME__ = os.path.dirname(os.path.realpath(__file__))
# 配置文件的位置
__GLOBAL_CONIF_FILE__ = os.path.join(__PACKAGE_DIR_NAME__,"config_data","manager_config.json")




def main():
    # 初始化日志配置
    logging.basicConfig(level=logging.INFO,
                        format='%(levelname)-s: %(message)s')

    # 获取命令行输入
    # PS: 用户若给不出实际可执行的指令， 则程序可能就在此终止了
    args = _parse_command_line()


    # 执行命令
    try:
        _run(args)
        logging.info("Normally Exit")
    except SystemExit as e:
        if e.code == 1:
            logging.error("Abnormally Exit")
        if e.code == 0:
            logging.info("Normally Exit")        
    
def _run(args):
    subcommand_name = args.subcommand_name

    if subcommand_name == None:
        return
    elif subcommand_name == "init":
        cmdhandler.init_ss_server()
    elif subcommand_name == 'server':
        _ser_cmd_handler(args)     
    elif subcommand_name == 'user':
        _usr_cmd_handler(args)

def _ser_cmd_handler(args):
    if args.start:
        cmdhandler.start_ss_server()
    elif args.stop:
        cmdhandler.stop_ss_server()
    elif args.refresh:
        cmdhandler.refresh()
    elif args.record:
        cmdhandler.start_record()

def _usr_cmd_handler(args):
    if not args.subcommand_name == 'user':
        return

    if args.create:
        cmdhandler.create_user(
            user_name=args.create[0],
            password=args.create[1]
        )
    elif args.delete:
        cmdhandler.delete_user(user_name=args.delete[0])
    elif args.restore:
        cmdhandler.restore_user(user_name=args.restore[0])
    elif args.list:
        cmdhandler.all_users_info()
    elif args.user_info:
        cmdhandler.user_info(user_name=args.user_info[0])
        
def _parse_command_line() -> argparse.Namespace:

    # 初始化主命令分析
    main_parser = argparse.ArgumentParser(description=
        '''
        SS Server Manager, support Statics , Access Record, Multiple User Manage
        '''
    )
    sub_parsers = main_parser.add_subparsers(
        title='Supported Command',
        metavar='',
        dest='subcommand_name'  # 
    )

    ################################################################################
    # 创建 init 命令
    ss_mgr_parser = sub_parsers.add_parser(
        'init',
        help='Init this SS Server manager with default_config.json'
    )
    ################################################################################

    ################################################################################
    # 创建 server 相关命令
    ssserver_parser = sub_parsers.add_parser(
        'server',help='Commands with regards to SS Server operation'
    )

    # 
    me_group = ssserver_parser.add_mutually_exclusive_group()
    me_group.add_argument(
        '--start',
        action='store_true',
        help='Start Server'
    )
    me_group.add_argument(
        '--stop',
        action='store_true',
        help='Stop Server'
    )
    me_group.add_argument(
        '--refresh',
        action='store_true',
        help='Add all user to ss server'
    )
    me_group.add_argument(
        '--record',
        action='store_true',
        help='Start recording user access record'   
    )
    # ssserver_parser.add_argument(
    #     '--config',
    #     nargs=1,metavar='config_file',
    #     help='Only available for --start'
    # )
    ################################################################################


    ################################################################################
    # 创建 user 相关命令
    user_mgr_parser = sub_parsers.add_parser(
        'user',help='Commands with regards to Multiple Users Manage'
    )
    me_group = user_mgr_parser.add_mutually_exclusive_group()
    me_group.add_argument(
        '--create',
        nargs=2,metavar=('user_name',"password"),
        help='Create new user'
    )
    me_group.add_argument(
        '--delete',
        nargs=1,metavar='user_name',
        help='Delete a user'
    )
    me_group.add_argument(
        '--restore',
        nargs=1,metavar='user_name',
        help='Restore a user'
    )
    me_group.add_argument(
        '--list',
        action='store_true',
        help='List info of all users.'
    )
    me_group.add_argument(
        '--user_info',
        nargs=1,metavar='user_name',
        help="Display user's info"
    )
    ################################################################################

    return main_parser.parse_args()

if __name__ == "__main__":
    main()
    # cmdhandler.keep_acc_rec()
