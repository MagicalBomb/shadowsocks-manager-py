# 这个程序应该将核心功能和业务逻辑分离开来
# 这样可以提高整个程序的维护性，简洁性，稳定性


from pprint import pprint as pp
import logging
import os
import sqlite3
import json
import subprocess
import socket
import random
import copy
import time

class User:
    '''
    这个类表示数据库中用户表的一条记录
    
    同时这个类也是数据库中用户表的模型

    unique_key 恒指向区别将一个用户区别于其它用户的属性
    '''
    table_name = "user"
    unique_key = "user_name"
    def __init__(self):
        '''
        used_statistics and allowed_statistics are all in MB
        '''
        self.user_name = ""
        self.password = ""
        self.port = 0
        self.is_delete = 0
        self.used_statistics = 0    
        self.allowed_statistics = 0 # in MB

    def __repr__(self):
        return "< {} >".format(self.user_name)

    def is_public_custom_attr(self,attr):
        '''
            这只是一个图方便的函数，用于快速判断
            一个 attr 是否是 __init__ 中定义的
            属性
        '''
        valid_attr = self.attrs_in_init()
        return attr in valid_attr

    def attrs_in_init(self):
        exclude_list = ["table_name","unique_key","is_public_custom_attr","attrs_in_init"]
        return [attr for attr in dir(self) if not (attr.startswith("_") or  (attr in exclude_list) )]
class MgrConfig:
    '''
    这个类代表整个 SS Server Mgr 的配置

    同时它也是数据库中全局配置表的模型

    "server_address": "0.0.0.0",
    "manager_port":9997,
    "acc_rec_out_cli_port":9998,
    "acc_rec_out_ser_port":9999,
    "base_port": 10000,
    "timeout": 300,
    "method": "aes-256-cfb"

    /*Windows*/
    "db_path": ".\\config_data\\manager.sqlite"
    /*Unix-like*/
    "db_path": "./config/data/manager.sqlite"

    /*Windows*/
    "log_file": ".\\config_data\\manager.log"
    /*Unix-like*/
    "log_file": "./config_data/manager.log"

    '''
    table_name = "manager_config"

    def __init__(self,mgr_config_dict=None,mgr_db=None):
        '''
        mgr_config_dict :   dict
        mgr_db  :   str


        mgr_db: 
            提供一个方便的功能， 只要指定了数据库的位置，就会自动从中获取
            配置信息对自身进行初始化
        '''
        self.server_address = ""
        self.manager_port = -1
        self.acc_rec_out_cli_port = -1
        self.acc_rec_out_ser_port = -1
        self.base_port = -1
        self.timeout = -1
        self.method = ""
        self.db_path = ""
        self.log_file = ""

        if mgr_config_dict:
            self._construct_with_dict(mgr_config_dict)
        
        if mgr_db:
            self._construct_with_db(mgr_db)

    def _construct_with_dict(self,mgr_config_dict):
        _attrs_list = self.attrs_in_init()
        for _a in _attrs_list:
            if _a == "db_path":
                self.db_path = os.path.realpath(mgr_config_dict[_a])
            elif _a == "log_file":
                self.log_file = os.path.realpath(mgr_config_dict[_a])
            else:
                self.__setattr__(_a,mgr_config_dict[_a])

    def _construct_with_db(self,mgr_db):

        def _generate_select_sql_cmd_with_MgrConfig():
            _sql_cmd = \
            '''
            SELECT 
                {attrs_list}
            FROM
                {table_name}
            '''
            _attrs_list = ""
            for _a in self.attrs_in_init():
                _attrs_list += "{},".format(_a)
            _attrs_list = _attrs_list[:-1]

            return _sql_cmd.format(
                        attrs_list = _attrs_list,
                        table_name = MgrConfig.table_name,
                    )
        
        _db_connection = sqlite3.connect(mgr_db)
        r = _db_connection.execute(_generate_select_sql_cmd_with_MgrConfig())

        _values_list = r.fetchone()
        if _values_list:
            _attrs_list = self.attrs_in_init()
            for _a,_v in zip(_attrs_list,_values_list):
                if _a == "db_path":
                    self.db_path = os.path.realpath(_v)
                elif _a == "log_file":
                    self.log_file = os.path.realpath(_v)
                else:
                    self.__setattr__(_a,_v)
        else:
            raise Exception("Table '{}' dont exist in database".format(MgrConfig.table_name))

    def is_public_custom_attr(self,attr):
        '''
            这只是一个图方便的函数，用于快速判断
            一个 attr 是否是 __init__ 中定义的
            属性
        '''
        valid_attr = self.attrs_in_init()
        return attr in valid_attr

    def attrs_in_init(self):
        exclude_list = ["table_name","is_public_custom_attr","attrs_in_init"]
        return [attr for attr in dir(self) if not (attr.startswith("_") or  (attr in exclude_list) )]
class Record:
    '''
    这个类是保存访问记录表的模型

    cli_ip  : SS 客户端的 ip
    '''

    table_name = "record"
    def __init__(self):
        self.user_name = ""
        self.url = ""
        self.time = ""
        self.cli_ip = ""

    def attrs_in_init(self):
        exclude_list = ["table_name","primary_key","attrs_in_init"]
        return [attr for attr in dir(self) if not (attr.startswith("_") or  (attr in exclude_list) )]


class SSServerLaunchResult:
    def __init__(self):
        self.already_running = False
        self.success = False
        self.dont_exist = False
def init_ss_manager(mgr_config):
    '''
    初始化数据库

    这个函数，会在指定的 sqlite 数据库中根据 User 和 MgrConfig 创建两个表：
    1. 用户信息表 2. 管理器配置表

    mgr_conifg  :   MgrConfig

    return      :   None    , it success if there is no exception, 
    '''

    def _generate_sql_cmd_with_User(db_connection):
        _sql_cmd = \
            '''
            CREATE TABLE "main"."{}" (
                "id" INTEGER NOT NULL DEFAULT 0 PRIMARY KEY AUTOINCREMENT
                {}
            );
            '''
        _tmp = ""
        _user = User()
        _attrs = _user.attrs_in_init()
        for _a in _attrs:
            if isinstance(_user.__getattribute__(_a),int):
                _tmp += ''',"{attr_name}" {type} NOT NULL\n'''.format(attr_name=_a,type="INTEGER")
            elif isinstance(_user.__getattribute__(_a),str):
                _tmp += ''',"{attr_name}" {type} NOT NULL\n'''.format(attr_name=_a,type="TEXT")
            else:
                logging.error("The attribute {} is neither int nor str!")
                raise Exception("Internal error")
        if _user.unique_key:
            _tmp += ''',CONSTRAINT "{key_name}" UNIQUE ("{key_name}") '''.format(key_name=_user.unique_key)
        return _sql_cmd.format(User.table_name,_tmp)
    def _generate_sql_cmd_with_Record(db_connection):
        _sql_cmd = \
        '''
        CREATE TABLE "main"."{}" (
            {}
        );
        '''
        _tmp  = ""
        _rec = Record()
        _attrs = _rec.attrs_in_init()
        for _a in _attrs:
            _value = _rec.__getattribute__(_a)
            if isinstance(_value,int):
                _tmp += ''',"{attr_name}" {type} NOT NULL\n'''.format(attr_name=_a,type="INTEGER")
            elif isinstance(_value,str):
                _tmp += ''',"{attr_name}" {type} NOT NULL\n'''.format(attr_name=_a,type="TEXT")
            else:
                logging.error("The attribute {} is neither int nor str!")
                raise Exception("Internal error")

        _tmp = _tmp[1:]
        return _sql_cmd.format(_rec.table_name,_tmp)
    def _generate_sql_cmd_with_MgrConfig(db_connection):
        _sql_cmd = \
        '''
        CREATE TABLE "main"."{}" (
        {}
        );
        '''

        _tmp = ""
        _mgr_config = MgrConfig()
        _attrs = MgrConfig().attrs_in_init()
        for _a in _attrs:
            if isinstance(_mgr_config.__getattribute__(_a),int):
                _tmp += '''"{attr_name}" {type} NOT NULL,\n'''.format(attr_name=_a,type="INTEGER")
            elif isinstance(_mgr_config.__getattribute__(_a),str):
                _tmp += '''"{attr_name}" {type} NOT NULL,\n'''.format(attr_name=_a,type="TEXT")
            else:
                logging.error("The attribute {} is neither int nor str!")
                raise Exception("Internal error")
        _tmp = _tmp[:-2]
        
        return _sql_cmd.format(MgrConfig.table_name,_tmp)
    def _generate_insert_sql_cmd_with_MgrConfig(db_connection,mgr_config):
        _sql_cmd = \
        '''
        INSERT INTO {table_name} {attr_list} VALUES(
            {values_list}
        )
        '''
        _attrs = mgr_config.attrs_in_init()
        _attr_list = "("
        _values_list = ""
        for _a in _attrs:
            _attr_list += (_a + ",")
            _value = mgr_config.__getattribute__(_a)
            if isinstance(_value,int):
                _values_list += "{},\n".format(_value)
            elif isinstance(_value,str):
                _values_list += "'{}',\n".format(_value)
            else:
                logging.error("The attribute {} is neither int nor str!")
                raise Exception("Internal error")
            
        _attr_list = _attr_list[:-1]
        _attr_list += ")"
        _values_list = _values_list[:-2]

        return _sql_cmd.format(
            table_name=mgr_config.table_name,
            attr_list=_attr_list,
            values_list = _values_list
            )
    

    # 创建数据库
    db_connection = sqlite3.connect(
        "file:"+mgr_config.db_path,
        uri=True
        )
    
    # 创建用户表
    _sql_cmd = _generate_sql_cmd_with_User(db_connection)
    db_connection.execute(_sql_cmd)

    # 创建访问记录表
    _sql_cmd = _generate_sql_cmd_with_Record(db_connection)
    db_connection.execute(_sql_cmd)

    # 创建配置表（只有一行）
    _sql_cmd = _generate_sql_cmd_with_MgrConfig(db_connection)
    db_connection.execute(_sql_cmd)

    # 配置文件写入数据库
    _sql_cmd = _generate_insert_sql_cmd_with_MgrConfig(db_connection,mgr_config)
    db_connection.execute(_sql_cmd)

    db_connection.commit()
    db_connection.close()

def start_ss_server(mgr_config,ss_port,ss_password):
    '''
    ss_port 是一个合法的 ss 端口，可以用来连接 ss server， 可以选择一个用户的 port 当做 ss port

    mgr_config: MgrConfig
    ss_port: SS SERVER 最初启动占用的端口
    ss_password: SS SERVER 最初启动占用的端口的密码
    '''
    def _generate_ss_server_config_with_mgr_config(mgr_config,ss_port,ss_password) -> dict:
        '''
        # config:
        #     "server": "0.0.0.0"                 服务器监听的 IP 地址
        #     "server_port": 10000,               服务器监听的端口
        #     "password": "magicalbomb"           服务器端口的密码
        #     "manager_port": 9997,               SS 服务器 API 端口
        #     "acc_rec_out_cli_port": 9998,       SS 服务器访问记录客户端端口
        #     "acc_rec_out_ser_port": 9999,       SS 服务器访问记录服务器端口
        #     "timeout": 300,                     
        #     "method": "aes-256-cfb"
        '''

        ss_config = {}

        ss_config['server']= mgr_config.server_address
        ss_config['server_port'] = ss_port
        ss_config['password']= ss_password
        ss_config['timeout']= mgr_config.timeout
        ss_config['method']= mgr_config.method
        ss_config['acc_rec_out_cli_port']= mgr_config.acc_rec_out_cli_port
        ss_config['acc_rec_out_ser_port']= mgr_config.acc_rec_out_ser_port
        ss_config['manager_port']= mgr_config.manager_port


        return ss_config

    # 将 mgr_config 转换成 ss config，然后写入配置文件， 让 ssserver 读取这个配置
    ss_config = _generate_ss_server_config_with_mgr_config(mgr_config,ss_port,ss_password)
    _ss_config_file_path = os.path.join(os.path.dirname(mgr_config.db_path),".ss_config_file.json")
    with open(_ss_config_file_path,"w") as _ss_config_file:
        json.dump(ss_config,_ss_config_file)

    t = subprocess.run(
        "ssserver -c {} --manager-address 127.0.0.1:{} -d start --log-file {}".format(
            _ss_config_file_path,
            mgr_config.manager_port,
            mgr_config.log_file
        ),
        shell=True
    )

    r = SSServerLaunchResult()
    if t.returncode == 1:
        # 表示进程 ssserver 已经处于运行状态
        r.already_running = True
    elif t.returncode == 127:
        # 表示不存在 ssserver 命令
        r.dont_exist = True
    else:
        r.success = True

    return r 

def stop_ss_server():
    subprocess.run("ssserver -d stop",shell=True)

def start_record(mgr_config):
    '''
    mgr_config  :   MgrConfig
    '''
    db_connection = sqlite3.connect(mgr_config.db_path)
    u_mgr = UserManager(mgr_config)
    rec_socket  = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    rec_socket.bind(('localhost',mgr_config.acc_rec_out_cli_port))
    rec_socket.connect(('localhost',mgr_config.acc_rec_out_ser_port))

    def _listen_rec_info_from_ss_server():
        return rec_socket.recv(100)
        
    def _insert_to_mgr_db(rec):
        '''
        信息格式： 目标访问网址:目标访问网址端口;客户端IP:客户端端口号;服务器端口号
        '''

        _sql_cmd = \
            '''
            INSERT INTO
                {table_name}
                ({attrs_list})
            VALUES
                ({values});
            '''
        attrs_list =  "time,url,cli_ip,user_name"
        rec = rec.decode('ascii')
        rec_info = rec.split(';')

        # 构建记录对象
        _record = Record()
        _record.url = rec_info[0]
        _record.time = time.ctime()

        # 获取客户端 ip
        cli_ip = rec_info[1].split(':')[0]
        _record.cli_ip = cli_ip

        # 获取用户名
        user_name = u_mgr.user_info_with_port(int(rec_info[2]))[0].user_name
        _record.user_name = user_name

        _values = "'{time}','{url}','{cli_ip}','{user_name}'".format(
            time = _record.time,
            url = _record.url,
            cli_ip = _record.cli_ip,
            user_name = _record.user_name
        )

        _sql_cmd = _sql_cmd.format( 
            table_name = Record.table_name,
            attrs_list = attrs_list,
            values = _values
            )
        db_connection.execute(_sql_cmd)
        db_connection.commit()
        return _record

    while True:

        rec = _listen_rec_info_from_ss_server()
        record = _insert_to_mgr_db(rec)
        yield record

def start_ss_server_recoder(mgr_config):
    '''
    开启对服务器访问记录的监控
    '''
    pass

def add_users_to_ss_server(mgr_config,user_list):
    '''
    mgr_config  :   MgrConfig
    user_list   :   list of User

    yield       :   one of user_list add to ss server successfully
    '''

    cli = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    while True:
        try:
            cli.bind(('localhost',random.randint(40000,60000)))
        except OSError as e:
            if OSError.errno != 48:
                raise OSError(e)
        else:
            break
    cli.connect(('localhost',mgr_config.manager_port))

    for _user in user_list:
        cli.send(
            bytes(
                '''add: {{"server_port":{},"password":"{}"}}'''.format(
                    _user.port,_user.password
                ),
                encoding='ascii'
            )
        )
        yield _user.user_name

def delete_users_from_ss_server(mgr_config,user_list):
    '''
    mgr_config  :   MgrConfig
    user_list   :   list of User

    yield       :   one of user_list add to ss server successfully
    '''
    cli = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    while True:
        try:
            cli.bind(('localhost',random.randint(40000,60000)))
        except OSError as e:
            if OSError.errno != 48:
                raise OSError(e)
        else:
            break
    cli.connect(('localhost',mgr_config.manager_port))

    for _user in user_list:
        cli.send(
            bytes(
                '''remove: {{"server_port":{}}}'''.format(
                    _user.port
                    ),
                encoding='ascii'
            )
        )
        yield _user.user_name

def _call_manager_api(cmd,args,mgr_config):
    '''
    cmd     : str
    args    : dict

    command[: JSON data]
    add: {"server_port": 8001, "password":"7cd308cc059"}
    remove: {"server_port": 8001}
 
    例如:
    cmd = "add"
    args = {"server":8001,"password":"7cd308cc059"}

    '''
    cli = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # 获取一个临时可用的端口
    while True:
        try:
            cli_tmp_port = random.randint(20000,65535)
            cli.bind(('localhost',cli_tmp_port))
        except OSError as e:
            if e.errno == 48:
                pass
            else:
                raise e
        else:
            break
    cli.connect(('localhost',mgr_config.manager_port))
    cli.settimeout(5)


    if cmd == "add":
        cli.send(
            bytes(
                '''add: {{"server_port":{},"password":"{}"}}'''.format(
                    args['server_port'],args['password']
                ),
                encoding='ascii'
            )
        )
        cli.recv(100)

    elif cmd == "remove":
        cli.send(
            bytes(
                '''remove: {{"server_port":{}}}'''.format(
                    args['server_port']
                    ),
                encoding='ascii'
            )
        )
        # 一般命令发出后，能正常执行就都会马上收到信�?
        # 若收不到信息，等到超时，则会自动跑出超时异常
        cli.recv(100)

def _test_ss_server(mgr_config):
    '''
    用于测试 ss server 是否处于工作状态
    若处于正常工作则返回 b'pong'
    '''
    cli = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # 获取一个临时可用的端口
    while True:
        try:
            cli_tmp_port = random.randint(20000,65535)
            cli.bind(('localhost',cli_tmp_port))
        except OSError as e:
            if e.errno == 48:
                pass
            else:
                raise e
        else:
            break
    cli.connect(('localhost',mgr_config.manager_port))
    cli.settimeout(5)

    cli.send(
        bytes('''ping''',encoding='ascii')
    )
    return cli.recv(100)


class UserOperationResult:

    def __init__(self,success=False,reason=""):
        '''
        success :   bool
        reason  :   str
        '''
        self.success = success
        self.reason = reason

    def __repr__(self):
        return "< success = {},reason = {} >".format(self.success,self.reason)
class UserManager:
    '''
    用于对用户进行管理
    '''

    def __init__(self,mgr_config):
        # self._users_info_list = []
        self._mgr_config = mgr_config
        self._db_connection = sqlite3.connect(self._mgr_config.db_path)

    def create_user(self,user):
        '''
        user    :   User
        '''
        cursor = self._db_connection.execute(
            '''
            select {unique_key} from {table_name} where {unique_key}='{unique_key_value}'
            '''.format(
                unique_key=User.unique_key,
                table_name=User.table_name,
                unique_key_value  = user.user_name
                )
        )
        r = cursor.fetchone()


        if r:
            return UserOperationResult(False,"already exist")
        else:
            def _generate_insert_sql_cmd_with_User(user):
                '''
                user    :   User
                '''
                _sql_cmd = \
                '''
                INSERT INTO {table_name} {attr_list} VALUES(
                    {values_list}
                )
                '''
                _attrs = user.attrs_in_init()
                _attr_list = "("
                _values_list = ""
                for _a in _attrs:
                    _attr_list += (_a + ",")
                    _value = user.__getattribute__(_a)
                    if isinstance(_value,int):
                        _values_list += "{},\n".format(_value)
                    elif isinstance(_value,str):
                        _values_list += "'{}',\n".format(_value)
                    else:
                        logging.error("The attribute {} is neither int nor str!")
                        raise Exception("Internal error")
                    
                _attr_list = _attr_list[:-1]
                _attr_list += ")"
                _values_list = _values_list[:-2]

                return _sql_cmd.format(
                    table_name  =   user.table_name,
                    attr_list   =   _attr_list,
                    values_list =   _values_list
                    )
            
            _sql_cmd = _generate_insert_sql_cmd_with_User(user)
            self._db_connection.execute(_sql_cmd)
            self._db_connection.commit()
            return UserOperationResult(True)
            
    def delete_user(self,user):
        '''
        这个函数与  User 是较强耦合的
        因为它假设  User 存在 is_delete 属性
        并且这个属性用于标记一个用户是否是处于被删除的状态

        并不会真正的将用户信息从数据库中删除
        只是将该用户标记为已删除。

        user    :   User
        '''
        user_name = user.user_name
        dst_user = copy.copy(user)
        dst_user.is_delete = 1
        return self._modify_user_attr(user_name,dst_user)

    def restore_user(self,user):
        '''
        user    :   User
        '''
        user_name = user.user_name
        dst_user = copy.copy(user)
        dst_user.is_delete = 0
        return self._modify_user_attr(user_name,dst_user)

    def list_all_users_name(self):
        '''
        return -> ["user1","user2",...]
        '''
        _sql_cmd = \
        '''
        SELECT 
            user_name
        FROM
            {table_name}
        '''.format(table_name = User.table_name)

        r = self._db_connection.execute(_sql_cmd)
        rtn = [ e[0] for e in r.fetchall() ]
        return rtn
        
    def exist(self,user_name):
        _,r = self.user_info(user_name)
        return r.success

    def user_info(self,user_name):
        '''
        user_name   :   str
        
        return  :   User,UserOperationResult
        '''
        
        def _generate_select_sql_cmd_with_User(user_name):
            _sql_cmd = \
            '''
            SELECT 
                {attrs_list}
            FROM
                {table_name}
            WHERE
                {unique_key} = '{unique_key_value}'
            '''
            _attrs_list = ""
            for _a in User().attrs_in_init():
                _attrs_list += "{},".format(_a)
            _attrs_list = _attrs_list[:-1]

            return _sql_cmd.format(
                        attrs_list = _attrs_list,
                        table_name = User.table_name,
                        unique_key = User.unique_key,
                        unique_key_value = user_name
                    )

        _sql_cmd = _generate_select_sql_cmd_with_User(user_name)
        r = self._db_connection.execute(_sql_cmd)
        
        _values_list = r.fetchone()
        if _values_list:
            user = User()
            _attrs_list = user.attrs_in_init()
            for _a,_v in zip(_attrs_list,_values_list):
                user.__setattr__(_a,_v)
            return user,UserOperationResult(True)
        else:
            return User(),UserOperationResult(False,"{} does not exist.".format(user_name))

    def user_info_with_port(self,port):


        def _generate_select_sql_cmd_with_port():
            _sql_cmd = \
            '''
            SELECT 
                {attrs_list}
            FROM
                {table_name}
            WHERE
                port = {port}
            '''
            _attrs_list = ""
            for _a in User().attrs_in_init():
                _attrs_list += "{},".format(_a)
            _attrs_list = _attrs_list[:-1]

            return _sql_cmd.format(
                        attrs_list = _attrs_list,
                        table_name = User.table_name,
                        port = port
                    )

        _sql_cmd = _generate_select_sql_cmd_with_port()
        r = self._db_connection.execute(_sql_cmd)

        _values_list = r.fetchone()
        if _values_list:
            user = User()
            _attrs_list = user.attrs_in_init()
            for _a,_v in zip(_attrs_list,_values_list):
                user.__setattr__(_a,_v)
            return user,UserOperationResult(True)
        else:
            return User(),UserOperationResult(False,"{} does not exist.".format(port))

    def _modify_user_attr(self,user_name,dst_user):
        '''
        user_name   :   str
        dst_user    :   User

        将指定用户的信息更新为 dst_user 中指定的用户信息
        '''

        if user_name != dst_user.user_name:
            return UserOperationResult(False,"user_name is not equal to dst_user.user_name")

        if not (self.user_info(user_name)[1].success):
            return UserOperationResult(False,"{} does not exist.")

        def _genegrate_key_eq_value_with_user(dst_user):
            _key_eq_value = ""
            _attrs = dst_user.attrs_in_init()
            for _a in _attrs:
                _value = dst_user.__getattribute__(_a)
                if isinstance(_value,int):
                    _key_eq_value += "{key}={value},".format(key=_a,value=_value)
                elif isinstance(_value,str):
                    _key_eq_value += "{key}='{value}',".format(key=_a,value=_value)
                else:
                    raise Exception("type is neither str nor int")
            return _key_eq_value[:-1]
            
        r = self._db_connection.execute(
                '''
                UPDATE {table_name} set {key_eq_value} where {unique_key}='{unique_key_value}'
                '''.format(
                    table_name=User.table_name,
                    key_eq_value=_genegrate_key_eq_value_with_user(dst_user),
                    unique_key=User.unique_key,
                    unique_key_value=user_name
                    )
            )
        
        self._db_connection.commit()
        return UserOperationResult(True)
        
    def max_id(self):
        '''
        如果数据库中没有任何一条记录，则这个函数返回  0
        '''
        r = self._db_connection.execute(
            '''
            SELECT
                max(id)
            FROM
                {table_name}
            '''.format(table_name=User.table_name)
        )
        if r:
            return r.fetchone()[0]
        else:
            return 0


if __name__ == "__main__":
    
    with open("./config_data/manager_config.json","rb") as fp:
        mgr_config_dict = json.loads(fp.read().decode("utf8"))
        mgr_config = MgrConfig(mgr_config_dict)

    # u_mgr = UserManager(mgr_config)

    # # dst_user = User()
    # # dst_user.user_name = "user3"
    # # dst_user.password = 9999
    # # r = u_mgr._modify_user_attr("user3",dst_user)
    # u,_ = u_mgr.user_info("user3")
    # r = u_mgr.restore_user(u)
    # print(r)
    # print(_test_ss_server(mgr_config))
    for e in start_record(mgr_config):
        print(e)
    
