# -*- coding:utf8 -*-
"""
定义基类:
    ConnectorBase 代表一个到Mysql数据库的连接
    VariableBase  代表一个查询global variable的连接
    StatuBase     代表一个查询global statu   的连接
"""

__all__ = ['ConnectorBase','VariableBase','StatuBase','PsBase']

import mysql.connector
import logging


class ConnectorBase(object):
    user='mtsuser'
    password='mts10352'
    host='127.0.0.1'
    port=3306
    _cnx=None
    _cursor=None
    _logger=None

    def __init__(self,host='127.0.0.1',port=3306,user='mtsuser',password='mts10352',database='mysql',*args,**kws):
        self.host=host
        self.port=port
        self.user=user
        self.password=password
        self.database=database
        self._cnx=None
        self._cursor=None
        self._logger=None
        

    @property
    def cursor(self):
        if self._cursor != None:
            return self._cursor
        else:
            try:
                self._cnx=mysql.connector.connect(user=self.user,password=self.password,host=self.host,port=self.port,database=self.database)
                self._cursor=self._cnx.cursor()
                return self._cursor
            except Exception as e:
                error_message=str(e)
                self.logger.info(e)
                self.logger.info("exit")
                self.close()
                exit()

    def format_string_value(self,raw_value):
        if isinstance(raw_value,str):
            return raw_value
        else:
            self.logger.info(raw_value)
            return 'invalidate str value'

    def format_byte_value(self,raw_value):
        if isinstance(raw_value,int):
            kb_raw_value=raw_value/1024
            if kb_raw_value >1024:
                mb_raw_value=kb_raw_value/1024
                if mb_raw_value>1024:
                    gb_raw_value=mb_raw_value/1024
                    if gb_raw_value >1024:
                        return "{0}TB".format(gb_raw_value/1024)
                    else:
                        return "{0}GB".format(gb_raw_value)
                else:
                    return "{0}MB".format(mb_raw_value)
            else:
                return "{0}KB".format(kb_raw_value)
        else:
            return "invalidate byte value"

    def format_intger_value(self,raw_value):
        return int(raw_value)
    def format_bool_value(self,raw_value):
        if raw_value in ['off',0]:
            return 'OFF'
        else:
            return 'ON'
    
    @property
    def logger(self):
        if self._logger != None:
            return self._logger
        else:
            self._logger=logging.getLogger("mts.base.{0}".format(self.__class__))
            stream_handler=logging.StreamHandler()
            formater=logging.Formatter("%(asctime)-24s %(levelname)-8s %(name)-24s : %(message)s")
            stream_handler.setFormatter(formater)
            self._logger.addHandler(stream_handler)
            self._logger.setLevel(logging.DEBUG)
            return self._logger

    def __str__(self):
        obj_str="{0.__class__} instance (host={0.host},port={0.port},user={0.user},password={0.password} )".format(self)
        return obj_str

    def __del__(self):
        #Object 类中没有__del__相关的方法
        #super(ConnectorBase,self).__del__()
        if self._cnx != None:
            self._cnx.close()
    
    def close(self):
        if self._cnx != None:
            self._cnx.close()
        

class VariableBase(ConnectorBase):
    variable_name=None
    variable_type="string"
    _variable_types=("string","byte","intger","percent","bool")
    _value=None

    def __init__(self,host='127.0.0.1',port=3306,user='mtsuser',password='mts10352',
    variable_name=None,variable_type="string",*args,**kws):
        super(VariableBase,self).__init__(host,port,user,password)
        if variable_name != None:
            self.variable_name=variable_name
            self.variable_type=variable_type

    
    def _get_value(self):
        try:
            self.cursor.execute("select @@{0} ;".format(self.variable_name))
            tmp_value=self.cursor.fetchone()
            if tmp_value != None and len(tmp_value)==1:
                return tmp_value[0]
            else:
                self.logger.info("variable {0} has a bad value {1}".format(self.variable_name,tmp_value))
                self.close()
                exit()
        except Exception as e:
                errore_message=str(e)
                self.logger.info(errore_message)
                self.logger.info("exit")
                self.close()
                exit()            

    
    @property
    def value(self):
        format_mapper={'string':self.format_string_value,
                       'byte'  :self.format_byte_value,
                       'intger':self.format_intger_value,
                       'bool'  :self.format_bool_value,
        }
        if self._value == None:
            self._value=self._get_value()
        return format_mapper[self.variable_type](self._value)

    @property
    def original_value(self):
        return self._get_value()

        
class StatuBase(ConnectorBase):
    statu_name="uptime"
    statu_type="intger"
    _statu_types=("string","byte","intger","percent","bool")
    _value=None

    def __init__(self,host='127.0.0.1',port=3306,user='mtsuser',password='mts10352',
    statu_name=None,statu_type="intger",*args,**kw):
        super(StatuBase,self).__init__(host,port,user,password)
        if statu_name != None:
            self.statu_name=statu_name
            self.statu_type=statu_type
        self._value=None

    def format_byte_value(self,raw_value):
        """
        由于statu 是由show global status like 'xxx' 得到的，所以它返回的是str,对于字节类型的statu,转换一下才行
        """
        return super(StatuBase,self).format_byte_value(int(self._value))

    def _get_value(self):
        if self._value != None:
            return self._value
        else:
            try:
                self.cursor.execute("show global status like '{0}' ;".format(self.statu_name))
                name_and_value=self.cursor.fetchone()
                if name_and_value == None:
                    self.logger.info("get a None value for statu {0} ".format(self.statu_name))
                    self.close()
                    exit()
                name,value=name_and_value
                self._value=value
                return self._value
            except Exception as e:
                error_message=str(e)
                self.logger.info(error_message)
                self.close()
                exit()

    @property
    def value(self):
        format_mapper={'string':self.format_string_value,
                       'intger':self.format_intger_value,
                       'byte'  :self.format_byte_value,}
        return format_mapper[self.statu_type](self._get_value())

    @property
    def original_value(self):
        return self._get_value()
        

class PsBase(ConnectorBase):
    """
    所有与performance_schema操作相关的基类
    """