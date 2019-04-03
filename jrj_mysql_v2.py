

import json, warnings

import pymysql, requests
from multiprocessing import Pool
warnings.filterwarnings("ignore")

"""
    2019-04-03 12:13
    
    0. 确保已安装第三方库
        
        pip3 install pymysql requests multiprocess
    
    1. 填写 MYSQL 配置

    2. 填写进程数量 PROCESS
    
    3. 终端执行 python3 xx.py

    4. 查看结果在mysql->jrj_registered表，或本地路径的txt文档
    
"""

# MYSQL 配置
HOST     = "127.0.0.1"
USER     = "root"
PASSWORD = ""
DATABASE = "test"
TABLE    = "mobile"
COLUMN   = "phone"
PAGESIZE = 1000       # 分页读取行数

# 进程设置
PROCESS  = 5

# 保存结果
SAVE_TABLE = "jrj_registered"  # 数据库
SAVE_TXT   = "jrj_registerd.txt"  # 文本


def link_mysql():
    try:
        conn = pymysql.connect(host=HOST, user=USER, password=PASSWORD, database=DATABASE)
        return conn
    except Exception as e:
        print("\n数据库连接失败：%s\n请检查MYSQL配置！\n" % e)


def check_table(cursor):
    sql = "CREATE TABLE IF NOT EXISTS %s" % SAVE_TABLE + "(id INT (11) AUTO_INCREMENT, phone VARCHAR(11), PRIMARY KEY(id) USING BTREE); "
    cursor.execute(sql)


def save_phone(phone):
    try:
        sql = "INSERT INTO %s" % SAVE_TABLE + "(phone) VALUES(%s)" % phone
        cursor.execute(sql)
        conn.commit()
    except Exception as e:
        print("保存失败：", e)


conn = link_mysql()  # 连数据库
cursor = conn.cursor()
check_table(cursor)  # 检查表


class Jrj(object):
    def __init__(self):

        self.start_page = 0

    def get_phone(self):
        sql = "SELECT %s" % COLUMN + " FROM %s" % TABLE + " LIMIT %s, %s; " % (self.start_page * PAGESIZE, PAGESIZE)
        cursor.execute(sql)

        result = cursor.fetchall()  # 读取结果

        return result

    @staticmethod
    def jrj(mobile):
        url = "https://sso.jrj.com.cn/sso/entryRetrievePwdMobile"
        form = {'mobile': mobile, 'verifyCode': '1'}
        headers = {
            "Host": "sso.jrj.com.cn",
            "Origin": "https://sso.jrj.com.cn",
            "Referer": "https://sso.jrj.com.cn/sso/retrievePassport/retrieveByMobile.jsp",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
        }

        try:
            r = requests.post(url, data=form,)
            if r.status_code == 200:
                res = json.loads(r.text)  # 请求结果
                print(mobile, res)

                # 保存有效结果
                if res['resultCode'] == '4':
                    # print(mobile)

                    # 保存文本
                    with open("{}".format(SAVE_TXT), "a") as f:
                        f.write(mobile + "\n")

                    save_phone(phone=mobile)  # 保存数据库

            else:
                print("响应状态码异常：", r.status_code)

        except requests.exceptions.RequestException as e:
            print("请求异常：", e)
            return

    def run(self):
        data_null = False  # 数据库数据读取状态
        pool = Pool(processes=PROCESS)  # 开启线程池

        while not data_null:
            result = self.get_phone()
            print("\nRead from Mysql: page %s, pageSize %s \n" % (self.start_page, PAGESIZE))

            # 结果非空
            if len(result) != 0:
                phones = [phone[0] for phone in result]

                # for phone in phones:
                #     self.jrj(phone)  # 进入请求

                pool.map(self.jrj, {phone for phone in phones})

                self.start_page = (self.start_page + 1)

            # 结果空，停止
            else:
                data_null = True

        conn.close()  # 关闭数据库连接


if __name__ == '__main__':
    try:
        Jrj().run()
    except Exception as e:
        print("执行出错：", e)

