import sys
import pymssql
import socket
import threading
import time
import re

# 连接数据库
conn = pymssql.connect('(local)', 'sa', 'weimo_siji', 'FSTS')
cur = conn.cursor()


# 查询用户数量
def numberofUsers():
    sql = "SELECT TOP 1 ID FROM [FSTS].[dbo].[user] order by ID desc"
    cur.execute(sql)
    result = cur.fetchone()
    return result[0]

# 加入新用户
def db_insert_user(username, password, email, pk):
    newID = numberofUsers() + 1             # 获取新用户ID
    sql = "insert into [user] (ID, username,password,email,PK) values (%d,'%s','%s','%s','%s')" % (newID, username, password, email, pk)
    cur.execute(sql)
    conn.commit()

# 查询用户ID
def db_IDsearch(email):
    sql = "select ID from [user] where email = '%s'" % email
    cur.execute(sql)
    result = cur.fetchone()
    if not result:
        return 0
    else:
        return result[0]

# 查询用户名
def db_usernamesearch(ID):
    sql = "select username from [user] where ID = '%d'" % ID
    cur.execute(sql)
    result = cur.fetchone()
    if not result:
        return 'None'
    else:
        return result[0].strip()

# 验证密码
def db_check_password(ID, pw_input):
    sql = "select password from [user] where ID = '%d'" % ID
    cur.execute(sql)
    pw_in_db = cur.fetchone()
    pw_existed = pw_in_db[0].strip()
    if pw_existed == pw_input:
        return True
    else:
        return False

# 新用户注册
def user_register(socket, email):
    useremail = email
    newID = numberofUsers() + 1
    socket.send(("ID:%d" % newID).encode("utf-8"))          # 发送新用户ID
    time.sleep(0.1)                                         # 防止粘包
    socket.send("Your username：".encode("utf-8"))          # 接受用户名
    username = socket.recv(1024).decode("utf-8").strip()
    socket.send("Your Password：".encode("utf-8"))          # 接收密码
    password = socket.recv(1024).decode("utf-8").strip()
    socket.send("PK".encode("utf-8"))
    PK = socket.recv(1024).decode("utf-8").strip()          # 接受用户公钥
    db_insert_user(username, password, useremail, PK)
    socket.send(("Congratulations! Registered successfully. Your ID is %d\nYour key pair is stored in the local directory.\nPress Enter to Continue" % newID).encode("utf-8"))  # 注册成功
    socket.recv(1024)

# 添加好友
def befriend(ID1, ID2):
    sql = "Select * From [friend] where ID1 = %d and ID2 = %d" % (ID1, ID2)
    cur.execute(sql)
    result = cur.fetchone()
    if not result:
        sql = "insert into [friend] (ID1,ID2) values (%d,%d)" % (ID1, ID2)
        cur.execute(sql)
        conn.commit()
        return 1
    else:
        return 0

# 解除好友
def deletefriend(ID1, ID2):
    sql = "Select * From [friend] where ID1 = %d and ID2 = %d" % (ID1, ID2)
    cur.execute(sql)
    result = cur.fetchone()
    if not result:
        return 0
    else:
        sql = "delete from [friend] where ID1 = %d and ID2 = %d" % (ID1, ID2)
        cur.execute(sql)
        conn.commit()
        return 1


# 查看所有好友状态
def checkfriends(socket, ID):
    socket.send("func3".encode("utf-8"))        # 发送func3控制码
    time.sleep(0.1)
    sql = "SELECT [ID],[username],[email],[IP],[port] FROM [user] as a inner join [friend] as b on a.[ID] = b.[ID2] left join [online] as c on b.[ID2] = c.[userID] where ID1 = %d" % ID
    cur.execute(sql)
    result = cur.fetchall()
    if result:
        for i in result:
            res = ''
            for j in i:
                res = res + str(j) + "\t"
            socket.send((res + "\n").encode("utf-8"))   # 逐行（逐个）发送好友状态
        time.sleep(0.2)
        socket.send("over".encode("utf-8"))             # 发送终止信号
    else:
        socket.send("over".encode("utf-8"))
    socket.recv(1024)


# 发起传输请求
def fileTransportRequest(ID1, ID2):
    sql = "SELECT [userID],[IP],[PK] FROM [online] as a inner join [friend] as b on a.[userID] = b.[ID2] inner join [user] as c on c.[ID] = a.[userID] where ID1 = %d and ID2 = %d" % (ID1, ID2)
    cur.execute(sql)
    result = cur.fetchone()
    if result:
        address = [result[1].strip(), result[2].strip()]    # 返回IP地址和公钥PK
        return address
    else:
        return ''

# 验证邮箱格式
def validateEmail(email):
    if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email) != None:
        return 1
    else:
        return 0

# 登录
def login(socket, IP, port):
    while True:
        socket.send("Please Enter Your E-mail: ".encode("utf-8"))
        email = socket.recv(1024).decode('utf-8').strip()
        if not validateEmail(email):    # 检查邮箱格式
            socket.send("The mailbox format is incorrect, please check.".encode("utf-8"))
            socket.recv(1024)
            continue

        ID = db_IDsearch(email)
        if ID == 0:
            socket.send('User not exsited，Register now？[Y/N]'.encode("utf-8"))  #邮箱未注册，是否注册？
            ifreg = socket.recv(1024).decode('utf-8').strip()
            if (ifreg == 'Y') or (ifreg == 'y'):
                user_register(socket, email)
                continue
        else:
            while 1:
                socket.send("Please Enter Password：".encode("utf-8"))
                password = socket.recv(1024).decode('utf-8').strip()    # 输入密码
                if db_check_password(ID, password):
                    username = db_usernamesearch(ID)
                    if ifonline(ID):
                        socket.send(("Welcome %s ,Login Successful!\nDetected that you did not exit properly the last time. Execute the bye command when going offline please.\nPress Enter to Continue." % username).encode("utf-8"))  # 上次未正常下线
                        socket.send(str(ID).encode("utf-8"))
                        socket.recv(1024)
                    else:
                        socket.send(("Welcome %s ,Login Successful! Press Enter to Continue." % username).encode("utf-8"))      # 登陆成功
                        time.sleep(0.1)
                        socket.send(str(ID).encode("utf-8"))
                        socket.recv(1024)
                        sql = "insert into online (userID,IP,port) values (%d,'%s',%d)" % (ID, IP, port)    # 用户上线
                        cur.execute(sql)
                        conn.commit()
                    break
                else:
                    socket.send('Sorry, Your Email or Password is Wrong, Press Enter to Try again.'.encode("utf-8"))
                    socket.recv(1024)
            break
    return ID

# 在线状态检查
def ifonline(ID):
    sql = "select userID from [online] where userID = %d" % ID
    cur.execute(sql)
    result = cur.fetchone()
    if result:
        return 1
    else:
        return 0

# 下线操作
def offline(ID):
    sql = "delete from [online] where userID = %d" % ID
    cur.execute(sql)
    conn.commit()

# 服务器主程序
def servermian(newSocket: socket.socket, addr):
    address = str(addr).split()
    IP = address[0][2:-2]               # 获取IP地址
    port = int(address[1][:-1])         # 获取端口
    ID = login(newSocket, IP, port)     # 获取通信用户ID

    while True:
        newSocket.send("\nWhat do you want to do?\n[1:Add a friend  2:Delete a friend  3:Check your friends  4:Transport Files to someone  bye:offline]".encode("utf-8"))
        res = newSocket.recv(1024)
        data = res.decode('utf-8').strip().split()
        if data == "":  # 跳过空操作
            pass
        else:
            # 下线
            if data[0] == 'bye':
                newSocket.send("bye".encode("utf-8"))
                print("client [%s] exit" % str(addr))
                newSocket.close()
                break
            else:
                print("%s:%s" % (str(addr), res.decode('utf-8')))
                op = data[0]    # 读取命令码
                # go on:跳过
                if op == 'go':
                    pass
                # 1：添加好友
                elif op == '1':
                    newSocket.send("ID of target user you want to be friend with:".encode("utf-8"))
                    tID = int(newSocket.recv(1024).decode("utf-8").strip())     # 获取目标用户ID
                    cmd = befriend(ID, tID)                                     # 添加好友
                    if cmd:
                        username = db_usernamesearch(tID)
                        newSocket.send(("%s has been add to your friends!" % username).encode("utf-8"))     # 添加成功
                        newSocket.recv(1024)
                    else:
                        newSocket.send("You have been friends with this user, or the user is not existed.".encode("utf-8"))     # 添加失败
                        newSocket.recv(1024)
                # 2：删除好友
                elif op == '2':
                    newSocket.send("ID of target user you want to delete from your friends:".encode("utf-8"))
                    tID = int(newSocket.recv(1024).decode("utf-8").strip())     # 获取目标用户ID
                    cmd = deletefriend(ID, tID)                                 # 删除好友
                    if cmd:
                        username = db_usernamesearch(tID)
                        newSocket.send(("%s has been delete from your friends!" % username).encode("utf-8"))    # 删除成功
                        newSocket.recv(1024)
                    else:
                        newSocket.send("You have not been friends with this user yet.".encode("utf-8"))         # 删除失败
                        newSocket.recv(1024)
                # 3：查看好友状态
                elif op == '3':
                    checkfriends(newSocket, ID)
                # 4：请求进行文件传输
                elif op == '4':
                    newSocket.send("ID of target user you want to transport files to:".encode("utf-8"))
                    tID = int(newSocket.recv(1024).decode("utf-8").strip())     # 获取目标用户ID
                    cmd = fileTransportRequest(ID, tID)                         # 获取目标用户信息
                    if cmd:                                         # 进入文件传输过程
                        newSocket.send("func4".encode("utf-8"))     # 发送func4控制码
                        time.sleep(0.1)
                        newSocket.send(cmd[0].encode("utf-8"))      # 发送目标用户IP
                        time.sleep(0.1)
                        newSocket.send(cmd[1].encode("utf-8"))      # 发送目标用户公钥
                        newSocket.recv(1024)
                    else:
                        newSocket.send("You and the target user are not friends or target user is offline.".encode("utf-8"))    # 进入文件传输过程失败
                        newSocket.recv(1024)
                # else：命令码未识别
                else:
                    newSocket.send("Opcode can not be recognized, please check your input".encode("utf-8"))
                    newSocket.recv(1024)

    offline(ID) # 下线

# 主函数
def main():
    # 建立socket实例，监听来自客户端的连接请求
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("10.38.28.219", 8080))
    server.listen(10)
    print("server is running!")
    while True:         # 多个通信线程同时进行
        newSocket, addr = server.accept()
        print("client [%s] is connected!" % str(addr))
        client = threading.Thread(target=servermian, args=(newSocket, addr))
        client.start()

    conn.close()        # 关闭数据库连接

if __name__ == '__main__':
    main()

