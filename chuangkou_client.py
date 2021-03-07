import tkinter as tk
import tkinter.messagebox
import pickle
from socket import socket
from PIL import Image, ImageTk
import threading
import socket
import struct
import json
import os
import threading
import time
import zipfile
import glob
from pyDes import des, CBC, PAD_PKCS5
import binascii
import random
import string
import rsa

from pyDes import des

hostname = socket.gethostname()
hipaddr = socket.gethostbyname(hostname)

download_dir = r'./filesend'  # 待发文件存放地址
share_dir = r'./filerec'      # 文件接收地址
dec_dir = r'./dec'

#非对称加密模块：RSA
def create_keys(ID):  # 生成公钥和私钥
    (pubkey, privkey) = rsa.newkeys(1024)
    pub = pubkey.save_pkcs1()
    with open('public' + ID + '.pem', 'wb+')as f:
        f.write(pub)

    pri = privkey.save_pkcs1()
    with open('private' + ID + '.pem', 'wb+')as f:
        f.write(pri)


def encrypt(text, PK):  # 用公钥加密
    pubkey = rsa.PublicKey.load_pkcs1(PK)
    original_text = text.encode('utf8')
    crypt_text = rsa.encrypt(original_text, pubkey)
    return crypt_text  # 加密后的密文


def decrypt(crypt_text, ID):  # 用私钥解密
    with open('private' + ID + '.pem', 'rb') as privatefile:
        p = privatefile.read()
    privkey = rsa.PrivateKey.load_pkcs1(p)
    lase_text = rsa.decrypt(crypt_text, privkey).decode()  # 注意，这里如果结果是bytes类型，就需要进行decode()转化为str
    return lase_text

#对称加密模块：DES
def newKey():
    KEY = ''.join(random.sample(string.ascii_letters + string.digits, 8))
    return KEY

def desenc_file(filename, KEY):
    cf = open(download_dir + '/' + filename + r'_des', 'wb')
    with open('%s/%s' % (download_dir, filename), 'rb') as f:
        for a in f:
            c = des_encrypt(a, KEY)
            cf.write(c)
        f.close()
    cf.close()

def des_encrypt(s, KEY):
    """
    DES 加密
    :param s: 原始字符串
    :return: 加密后字符串，16进制
    """
    secret_key = KEY
    iv = secret_key
    k = des(secret_key, CBC, iv, pad=None, padmode=PAD_PKCS5)
    en = k.encrypt(s, padmode=PAD_PKCS5)
    return binascii.b2a_hex(en)

def desdec_file(filename, KEY):
    mf = open(dec_dir + '/' + filename, 'wb')
    with open(share_dir + '/' + filename + '_des', 'rb') as d:
        for a in d:
            c = des_descrypt(a, KEY)
            mf.write(c)
        d.close()
    mf.close()

def des_descrypt(s, KEY):
    """
    DES 解密
    :param s: 加密后的字符串，16进制
    :return:  解密后的字符串
    """
    secret_key = KEY
    iv = secret_key
    k = des(secret_key, CBC, iv, pad=None, padmode=PAD_PKCS5)
    de = k.decrypt(binascii.a2b_hex(s), padmode=PAD_PKCS5)
    return de

#压缩模块：ZIP
def zip(filename):
    # target ：待压缩文件存储路径
    # filename ：压缩文件命名
    # file_url ：压缩文件保存路径
    target = download_dir + '/' + filename + r'.zip'
    fp = download_dir + '/' + filename
    f = zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED)
    f.write(fp + r'_des', filename + r'_des')
    f.write(fp + r'_rdk', filename + r'_rdk')
    f.close()

def un_zip(zip_path):
    # 解压缩后文件的存放路径
    unzip_file_path = share_dir
    # 找到压缩文件夹
    dir_list = glob.glob(zip_path)
    if dir_list:
        # 循环zip文件夹
        for dir_zip in dir_list:
            # 以读的方式打开
            with zipfile.ZipFile(dir_zip, 'r') as f:
                for file in f.namelist():
                    f.extract(file, path=unzip_file_path)
            os.remove(dir_zip)

# 连接用户服务器的客户端启动
pc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
pc.connect(('10.38.28.219', 8080))

# 窗口
window = tk.Tk()
window.title('欢迎来到文件传输系统')

sw = window.winfo_screenwidth()
sh = window.winfo_screenheight()
ww = 450
wh = 400

# 窗口宽高为300
x = (sw - ww) / 2
y = (sh - wh) / 2

window.geometry("%dx%d+%d+%d" % (ww, wh, x, y))

# 画布放置背景照片
canvas = tk.Canvas(window, height=550, width=400)

img = Image.open('t.png')
image_file = ImageTk.PhotoImage(img)
imglabel = tk.Label(window, image=image_file)
imglabel.grid(row=0, column=0, columnspan=1)

# 标签 邮箱密码
tk.Label(window, text='邮箱:').place(x=100, y=200)
# tk.Label(window, text='用户名:').place(x=100, y=150)
tk.Label(window, text='密码:').place(x=100, y=190)

# 邮箱输入框
var_usr_mail = tk.StringVar()
entry_usr_mail = tk.Entry(window, textvariable=var_usr_mail)
entry_usr_mail.place(x=160, y=200)

# 密码输入框
var_usr_pwd = tk.StringVar()
entry_usr_pwd = tk.Entry(window, textvariable=var_usr_pwd, show='*')
entry_usr_pwd.place(x=160, y=190)

#用户登录
def client_login():
    # 输入框获取
    usr_mail = var_usr_mail.get()
    #usr_name = var_usr_name.get()
    usr_pwd = var_usr_pwd.get()

    if usr_mail == '' or usr_pwd == '':
        tk.messagebox.showerror(message='邮箱或密码为空')

    while True:
        rec = pc.recv(1024).strip().decode('utf-8')
        if rec == "Please Enter Your E-mail: ":
            pc.send(usr_mail.encode('utf-8'))
            rec = pc.recv(1024).strip().decode('utf-8')
            if rec =="The mailbox format is incorrect, please check.":
                tk.messagebox.showerror(message="邮箱格式错误，请检查！")
            if rec == 'User not exsited，Register now？':
              win1 = tk.Tk()
              win1.title('新用户注册')
              win1.geometry("%dx%d+%d+%d" %(ww, wh, x, y))
              button1 = tk.Button(win1, text='Yes', command='signtowcg')
              button2 = tk.Button(win1, text='No', command=win1.destroy())
              button1.pack
              button2.pack
              win1.mainloop()
            else:
                if rec == "Please Enter Password：":
                    pc.send(usr_pwd.encode('utf-8'))
                    rec = pc.recv(1024).strip().decode('utf-8')
                    if rec[:6] == "Welcome":
                      win2 = tk.Tk()
                      win2.title('welcome!欢迎您使用本系统')
                      win2.geometry("%dx%d+%d+%d" % (ww, wh, x, y))
                      rec = pc.recv(1024).strip().decode('utf-8')
                      if rec[:5] =='\nWhat':
                       but1 = tk.Button(win2, text='Add a friend',command='add_friend')
                       but2 = tk.Button(win2, text='delete a friend', command='delete_friend')
                       but3 = tk.Button(win2, text='check friends', command='check_friend')
                       but4 = tk.Button(win2, text='transport file to friend', command='trans_file')
                       but5 = tk.Button(win2, text='Bye', command='client_sign_quit')
                       but1.pack
                       but2.pack
                       but3.pack
                       but4.pack
                       but5.pack
                      win2.mainloop()
                    else:
                        tk.messagebox.showerror(message='密码或邮箱名错误,登陆失败')

        if rec == 'bye':
            window.destroy()
            break

#添加好友
def add_friend():
    pc.send('1'.encode('utf-8'))
    rec = pc.recv(1024).strip().decode('utf-8')
    if rec[:1] == 'ID':
     win3 = tk.Tk()
     win3.title('ADD FRIENDS')
     win3.geometry("%dx%d+%d+%d" % (ww, wh, x, y))
     tk.Label(win3, text='需要添加好友的ID:').place(x=100, y=200)

    var_add_friend = tk.StringVar()
    entry_add_friend = tk.Entry(window, textvariable=var_add_friend)
    entry_add_friend.place(x=160, y=200)

    add_friend = var_add_friend.get()
    pc.send(add_friend.encode('utf-8'))
    rec = pc.recv(1024).strip().decode('utf-8')

    if rec[3:5] == 'has':
        tk.messagebox.showinfo('恭喜', add_friend + '添加成功')
    else:
        tk.messagebox.showerror('错误', '此好友已在你的好友列表')
    win3.destroy()

#删除好友
def delete_friend():
    pc.send('2'.encode('utf-8'))
    rec = pc.recv(1024).strip().decode('utf-8')
    if rec[:1] =="ID":
     win4 = tk.Tk()
     win4.title('DELETE FRIENDS')
     win4.geometry("%dx%d+%d+%d" % (ww, wh, x, y))
     tk.Label(win4, text='需要删除好友的ID:').place(x=100, y=200)

    var_delete_friend = tk.StringVar()
    entry_delete_friend = tk.Entry(window, textvariable=var_delete_friend)
    entry_delete_friend.place(x=160, y=200)

    delete_friend = var_delete_friend.get()
    pc.send(delete_friend.encode('utf-8'))
    rec = pc.recv(1024).strip().decode('utf-8')

    if rec[12:17] == 'delete':
        tk.messagebox.showinfo('恭喜', '删除好友'+delete_friend+'成功')
    else:
        tk.messagebox.showerror('错误', '此好友不在你的好友列表')
    win4.destroy()
def check_friend():
    pc.send('3'.encode('utf-8'))
    rec = pc.recv(1024).strip().decode('utf-8')
    if rec == 'fun3':
     win4 = tk.Tk()
     win4.title('FRIENDS LIST')
     win4.geometry("%dx%d+%d+%d" % (ww, wh, x, y))

    i = 0
    rec = pc.recv(1024).decode('utf-8').strip()
    while True:
        if rec == 'over':
            win4.destroy()
        tk.messagebox.showinfo(rec)
        rec = pc.recv(1024).decode('utf-8').strip()
        i = i + 1
    if i == 0:
        tk.messagebox.showerror('抱歉！', '你暂时没有好友')

# 注册函数
def client_sign_up():
    # 确认注册时的相应函数
    def signtowcg():
        # 获取输入框内的内容
        pc.send('Yes'.encode('utf-8'))
        ne = new_email.get()
        nn = new_name.get()
        np = new_pwd.get()
        pk = new_pk.get()

        if np == '' or nn == '' or ne == '':
             tk.messagebox.showerror('错误', '用户名或密码为空')

        rec = pc.recv(1024).strip().decode('utf-8')
        if rec == "Your username：":
            pc.send(nn.encode('utf-8'))
        rec = pc.recv(1024).strip().decode('utf-8')
        if rec == "Your Password：":
            pc.send(np.encode('utf-8'))
        rec = pc.recv(1024).strip().decode('utf-8')
        if rec == "PK":
            pc.send(pk.encode('utf-8'))
        rec = pc.recv(1024).strip().decode('utf-8')
        if rec[:7] =="Congratu":
            tk.messagebox.showinfo('欢迎', '注册成功')
        else:
            tk.messagebox.showerror('错误', '出现异常')

        # 注册成功关闭注册框
        window_sign_up.destroy()

    # 新建注册界面
    window_sign_up = tk.Toplevel(window)
    window_sign_up.geometry('350x200')
    window_sign_up.title('注册')

    # 邮箱及标签、输入框
    new_email = tk.StringVar()
    tk.Label(window_sign_up, text='邮箱：').place(x=10, y=90)
    tk.Entry(window_sign_up, textvariable=new_email).place(x=150, y=90)

    # 用户名变量及标签、输入框
    new_name = tk.StringVar()
    tk.Label(window_sign_up, text='用户名：').place(x=10, y=10)
    tk.Entry(window_sign_up, textvariable=new_name).place(x=150, y=10)

    # 密码变量及标签、输入框
    new_pwd = tk.StringVar()
    tk.Label(window_sign_up, text='请输入密码：').place(x=10, y=50)
    tk.Entry(window_sign_up, textvariable=new_pwd, show='*').place(x=150, y=50)

    # 公钥及标签、输入框
    new_pk = tk.StringVar()
    tk.Label(window_sign_up, text='请输入公钥：').place(x=10, y=50)
    tk.Entry(window_sign_up, textvariable=new_pk, show='*').place(x=150, y=50)


    # 确认注册按钮及位置
    bt_confirm_sign_up = tk.Button(window_sign_up, text='确认注册', command= signtowcg)
    bt_confirm_sign_up.place(x=150, y=130)


# 退出的函数
def client_sign_quit():
    window.destroy()

def cget(pc):
    # 2.接受文件内容，以写的方式打开一个新文件，写入客户端新文件中
    # 1收报头长度

    obj = pc.recv(4)
    try:
        header_size = struct.unpack('i', obj)[0]

    # 2接收报头
        header_bytes = pc.recv(header_size)

    # 3解析报头,对于数据的描述
        header_json = header_bytes.decode('utf-8')
        header_dic = json.loads(header_json)
        print(header_dic)
        total_size = header_dic['file_size']
        file_name = header_dic['filename']

    # 4 接受真实的数据
        with open('%s/%s' % (download_dir, file_name), 'wb')as f:
            recv_size = 0
            win9 = tk.Tk()
            win9.title('TRANSPORT')
            win9.geometry("%dx%d+%d+%d" % (ww, wh, x, y))
            tk.messagebox.showinfo(message="Congratulation: The file is in transit! Please wait a mintue!")
            while recv_size < total_size:
                res = pc.recv(1024)
                f.write(res)
                recv_size += len(res)
                tk.messagebox.showinfo(message="总大小："+ total_size +"已经下载大小："+recv_size)
                #print('总大小：%s  已经下载大小：%s' % (total_size, recv_size))
    except struct.error:
        tk.messagebox.showerror("ERROR","File not found! Please check the name of file again!")
        #print("Error: File not found! Please check the name of file again!")

def cput(cmds, conn, PK):
    filename = cmds[1]
    dk = newKey()
    desenc_file(filename, dk)

    rdk = encrypt(dk, PK)         #rsa加密dk并写入文件
    rdkf = open(download_dir + '/' + filename + r'_rdk', 'wb')
    rdkf.write(rdk)
    rdkf.close()

    zip(filename)

    filename = filename + r'.zip'
    # 3.以读的方式打开,读取文件
    # 1制作报头
    header_dic = {
        'filename': filename,
        'md5': 'xxdxx',
        'file_size': os.path.getsize(r'%s/%s' % (download_dir, filename))
    }
    header_json = json.dumps(header_dic)
    header_bytes = header_json.encode('utf-8')

    # 2 发送报头长度
    conn.send(struct.pack('i', len(header_bytes)))  # 固定长度4

    # 3 发报头
    conn.send(header_bytes)
    # 4发真实数据
    send_size = 0
    with open('%s/%s' % (download_dir, filename), 'rb') as f :
        # conn.send(f.read())
        for a in f:
            conn.send(a)
            send_size += len(a)
            win9 = tk.Tk()
            win9.title('TRANSPORT')
            win9.geometry("%dx%d+%d+%d" % (ww, wh, x, y))
            tk.messagebox.showinfo(message=send_size)
            #print(send_size)

def trans_file_p2p():
    rec = pc.recv(1024).strip().decode('utf-8')
    while True:
     if rec == 'fun4':
        pp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ip = pc.recv(1024).decode("utf-8").strip()
        PK = pc.recv(1024).strip()
        pp.connect((ip, 6000))
        win7 = tk.Tk()
        win7.title('TRANSPORT')
        win7.geometry("%dx%d+%d+%d" % (ww, wh, x, y))
        tk.messagebox.showinfo(title=pp, message="Now you are conneted to the target user.")
        while True:
            #1.发命令
            tk.Label(window, text='传输:').place(x=100, y=200)

            # 命令输入框
            var_trans_file = tk.StringVar()
            entry_trans_file = tk.Entry(window, textvariable=var_trans_file)
            entry_trans_file.place(x=160, y=200)

            inp = var_trans_file.get().strip()

            if not inp:
                continue
            inp = inp + " " + rID
            pp.send(inp.encode('utf-8'))
            cmds = inp.split()
            if cmds[0] == 'get':
                cget(pp)
            elif cmds[0] == 'put':
                cput(cmds, pp, PK)
            elif cmds[0] == 'close':
                  break
        pp.close()

     elif 'want to transport' in rec:
         win8 = tk.Tk()
         win8.title('TRANSPORT')
         win8.geometry("%dx%d+%d+%d" % (ww, wh, x, y))
         tk.Label(window, text='传输:').place(x=100, y=200)

         # 命令输入框
         var_trans_file = tk.StringVar()
         entry_trans_file = tk.Entry(window, textvariable=var_trans_file)
         entry_trans_file.place(x=160, y=200)

         inp = var_trans_file.get().strip()
         if not inp:
            pc.send("go on".encode('utf-8'))
            continue
         rID = inp
         pc.send(inp.encode('utf-8'))
         continue
     elif rec[:3] == 'ID:':
        ID = rec[3:]
        continue

     elif rec == 'PK':
        create_keys(ID)
        with open('public' + ID + '.pem', 'rb') as publickfile:
            p = publickfile.read()
        pc.send(p)
        continue

     elif 'Login Successful' in rec:
        ID = pc.recv(1024).decode('utf-8').strip()

        win9 = tk.Tk()
        win9.title('TRANSPORT')
        win9.geometry("%dx%d+%d+%d" % (ww, wh, x, y))
        tk.Label(window, text='传输:').place(x=100, y=200)
        # 命令输入框
        var_trans_file = tk.StringVar()
        entry_trans_file = tk.Entry(window, textvariable=var_trans_file)
        entry_trans_file.place(x=160, y=200)
        inp = var_trans_file.get().strip()
        if not inp:
         pc.send("go on".encode('utf-8'))
         continue
    pc.send(inp.encode('utf-8'))

    pc.close()

    cl = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cl.connect((hipaddr, 6000))
    time.sleep(0.2)
    cl.send("close".encode("utf-8"))

#P2PServerr模块
def sget(cmds, conn):
    filename = cmds[1]
    # 3.以读的方式打开,读取文件
    # 1制作报头
    header_dic = {
        'filename': filename,
        'md5': 'xxdxx',
        'file_size': os.path.getsize(r'%s/%s' % (share_dir, filename))
    }
    header_json = json.dumps(header_dic)
    header_bytes = header_json.encode('utf-8')

    # 2 发送报头长度
    conn.send(struct.pack('i', len(header_bytes)))  # 固定长度4

    # 3 发报头
    conn.send(header_bytes)
    # 4发真实数据
    with open('%s/%s' % (share_dir, filename), 'rb') as f:
        # conn.send(f.read())
        for a in f:
            conn.send(a)

def sput(pc, ID):
    # 2.接受文件内容，以写的方式打开一个新文件，写入客户端新文件中
    # 1收报头长度
    obj = pc.recv(4)
    header_size = struct.unpack('i', obj)[0]

    # 2接收报头
    header_bytes = pc.recv(header_size)

    # 3解析报头,对于数据的描述
    header_json = header_bytes.decode('utf-8')
    header_dic = json.loads(header_json)

    win9 = tk.Tk()
    win9.title('TRANSPORT_p2p')
    win9.geometry("%dx%d+%d+%d" % (ww, wh, x, y))
    tk.messagebox.showinfo(message=header_dic)
    #print(header_dic)
    total_size = header_dic['file_size']
    file_name = header_dic['filename']

    # 4 接受真实的数据
    with open('%s/%s' % (share_dir, file_name), 'wb') as f:
        recv_size = 0
        while recv_size < total_size:
            res = pc.recv(1024)
            f.write(res)
            recv_size += len(res)
            tk.messagebox.showinfo(message="总大小：" + total_size + "已经下载大小：" + recv_size)
            #print('总大小：%s  已经下载大小：%s' % (total_size, recv_size))

    un_zip('%s/%s' % (share_dir, file_name))

    file_name = file_name[:-4]
    ##获取对称密钥dk
    with open('%s/%s_rdk' % (share_dir, file_name), 'rb') as f:
        m = f.read()
    dk = decrypt(m, ID)

    desdec_file(file_name, dk)


def trans_p2p():
    # 客户端文件传输服务器启动
    phone = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    phone.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 回收重用端口10000
    phone.bind((hipaddr, 6000))  # 0-65535  0-1024给操作系统，
    phone.listen(5)

    while True:  # 建链接循环
        win10 = tk.Tk()
        win10.title('TRANSPORT_P2P')
        win10.geometry("%dx%d+%d+%d" % (ww, wh, x, y))
        conn, client_addr = phone.accept()
        tk.messagebox.showinfo(client_addr)
        #print(client_addr)
        while True:  # 通信循环
            try:
                # 1.收命令
                res = conn.recv(1024)  # get jiaoyue.mp4
                # 2.解析命令，提取相应命令参数
                cmds = res.decode('utf-8').split()  # ['get', 'jiaoyue.mp4']
                if cmds[0] == 'get':
                    try: sget(cmds, conn)
                    except FileNotFoundError:
                        tk.messagebox.showerror("Error: File not found! ")
                        #print ("Error: File not found! ")
                        break
                    else:
                        tk.messagebox.showinfo(message="Congratulation: The file is in transit! ")
                        #print("Congratulation: The file is in transit! ")
                elif cmds[0] == 'put':
                    sput(conn, cmds[2])
                elif cmds[0] == 'close':
                    break
            except ConnectionResetError:
                break
        conn.close()
        address = str(client_addr).split()
        IP = address[0][2:-2]
        if IP == hipaddr:
            break
    phone.close()


# 登录 注册按钮
bt_login = tk.Button(window, text='登录', command=client_login())
bt_login.place(x=140, y=230)
bt_logup = tk.Button(window, text='注册', command=client_sign_up())
bt_logup.place(x=210, y=230)
bt_logquit = tk.Button(window, text='退出', command=client_sign_quit())
bt_logquit.place(x=280, y=230)

window.mainloop()

if __name__ == '__main__':
    client = threading.Thread(target=trans_file)
    client.start()
    server = threading.Thread(target=trans_file_p2p)
    server.start()
