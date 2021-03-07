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

# 获取本地IP
hostname = socket.gethostname()
hipaddr = socket.gethostbyname(hostname)

download_dir = r'./filesend'    # 待发文件存放地址
share_dir = r'./filerec'        # 文件接收地址
dec_dir = r'./dec'              # 解密文件地址


# 非对称加密模块：RSA
# 密钥对生成
def create_keys(ID):  # 生成公钥和私钥
    (pubkey, privkey) = rsa.newkeys(1024)
    pub = pubkey.save_pkcs1()
    with open('public' + ID + '.pem', 'wb+')as f:   # 以文件形式存放公钥
        f.write(pub)

    pri = privkey.save_pkcs1()
    with open('private' + ID + '.pem', 'wb+')as f:  # 以文件形式存放私钥
        f.write(pri)

# 公钥加密
def encrypt(text, PK):
    pubkey = rsa.PublicKey.load_pkcs1(PK)
    original_text = text.encode('utf8')
    crypt_text = rsa.encrypt(original_text, pubkey)
    return crypt_text  # 加密后的密文

# 私钥解密
def decrypt(crypt_text, ID):
    with open('private' + ID + '.pem', 'rb') as privatefile:
        p = privatefile.read()
    privkey = rsa.PrivateKey.load_pkcs1(p)
    lase_text = rsa.decrypt(crypt_text, privkey).decode()
    return lase_text    #解密后的明文

# 对称加密模块：DES
# 密钥生成
def newKey():
    KEY = ''.join(random.sample(string.ascii_letters + string.digits, 8))   # 随机生成一次传输使用的临时密钥
    return KEY

# 文件加密
def desenc_file(filename, KEY):
    cf = open(download_dir + '/' + filename + r'_des', 'wb')
    with open('%s/%s' % (download_dir, filename), 'rb') as f:
        for a in f:
            c = des_encrypt(a, KEY)
            cf.write(c)
        f.close()
    cf.close()

# 字符串加密
def des_encrypt(s, KEY):
    secret_key = KEY
    iv = secret_key
    k = des(secret_key, CBC, iv, pad=None, padmode=PAD_PKCS5)
    en = k.encrypt(s, padmode=PAD_PKCS5)
    return binascii.b2a_hex(en)

# 文件解密
def desdec_file(filename, KEY):
    mf = open(dec_dir + '/' + filename, 'wb')
    with open(share_dir + '/' + filename + '_des', 'rb') as d:
        for a in d:
            c = des_descrypt(a, KEY)
            mf.write(c)
        d.close()
    mf.close()

# 字符串解密
def des_descrypt(s, KEY):
    secret_key = KEY
    iv = secret_key
    k = des(secret_key, CBC, iv, pad=None, padmode=PAD_PKCS5)
    de = k.decrypt(binascii.a2b_hex(s), padmode=PAD_PKCS5)
    return de

# 压缩模块：ZIP
# 压缩
def zip(filename):
    target = download_dir + '/' + filename + r'.zip'                # 目标压缩文件
    fp = download_dir + '/' + filename                              # 待压缩文件
    f = zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED)
    f.write(fp + r'_des', filename + r'_des')                       # 压缩加密文件
    f.write(fp + r'_rdk', filename + r'_rdk')                       # 压缩对称密钥
    f.close()

# 解压缩
def un_zip(zip_path):
    unzip_file_path = share_dir                                     # 解压缩后文件的存放路径
    dir_list = glob.glob(zip_path)                                  # 定位压缩文件夹
    if dir_list:                                                    # 循环zip文件夹
        for dir_zip in dir_list:
            with zipfile.ZipFile(dir_zip, 'r') as f:
                for file in f.namelist():
                    f.extract(file, path=unzip_file_path)
            os.remove(dir_zip)

# P2PServerr模块
# P2P被动方上传
def sget(cmds, conn):
    filename = cmds[1]
    header_dic = {                                                  # 1制作报头
        'filename': filename,
        'md5': 'xxdxx',
        'file_size': os.path.getsize(r'%s/%s' % (share_dir, filename))
    }
    header_json = json.dumps(header_dic)
    header_bytes = header_json.encode('utf-8')

    conn.send(struct.pack('i', len(header_bytes)))                  # 发送报头长度：4
    conn.send(header_bytes)                                         # 发送报头

    with open('%s/%s' % (share_dir, filename), 'rb') as f:          # 发送数据
        for a in f:
            conn.send(a)

# P2P被动接收
def sput(pc, ID):
    obj = pc.recv(4)                                                # 接收报头长度
    header_size = struct.unpack('i', obj)[0]

    header_bytes = pc.recv(header_size)                             # 接收报头

    header_json = header_bytes.decode('utf-8')                      # 解析报头，得到与传输数据相关的信息
    header_dic = json.loads(header_json)
    print(header_dic)
    total_size = header_dic['file_size']
    file_name = header_dic['filename']

    with open('%s/%s' % (share_dir, file_name), 'wb') as f:         # 接受具体数据
        recv_size = 0
        while recv_size < total_size:
            res = pc.recv(1024)
            f.write(res)
            recv_size += len(res)
            print('总大小：%s  已经下载大小：%s' % (total_size, recv_size))

    un_zip('%s/%s' % (share_dir, file_name))                        # 解压缩数据

    file_name = file_name[:-4]
    with open('%s/%s_rdk' % (share_dir, file_name), 'rb') as f:     # 获取对称密钥dk
        m = f.read()
    dk = decrypt(m, ID)                                             # 解密对称密钥
    desdec_file(file_name, dk)                                      # 解密数据

# P2PClient模块
# P2P主动方下载
def cget(pc):
    obj = pc.recv(4)                                                # 接报头长度
    try:
        header_size = struct.unpack('i', obj)[0]

        header_bytes = pc.recv(header_size)                         # 接收报头

        header_json = header_bytes.decode('utf-8')                  # 解析报头，得到与传输数据相关的信息
        header_dic = json.loads(header_json)
        print(header_dic)
        total_size = header_dic['file_size']
        file_name = header_dic['filename']

        with open('%s/%s' % (download_dir, file_name), 'wb')as f:   # 接受具体数据
            recv_size = 0
            print("Congratulation: The file is in transit! Please wait a mintue!")
            while recv_size < total_size:
                res = pc.recv(1024)
                f.write(res)
                recv_size += len(res)
                print('总大小：%s  已经下载大小：%s' % (total_size, recv_size))
    except struct.error:
        print("Error: File not found! Please check the name of file again!")

# P2P主动方发送
def cput(cmds, conn, PK):
    filename = cmds[1]
    dk = newKey()                                                   # 生成临时密钥
    desenc_file(filename, dk)                                       # 使用临时密钥加密待发数据

    rdk = encrypt(dk, PK)                                           # 使用rsa加密对称密钥并写入文件
    rdkf = open(download_dir + '/' + filename + r'_rdk', 'wb')
    rdkf.write(rdk)
    rdkf.close()

    zip(filename)                                                   # 将对称密钥和数据一并压缩
    filename = filename + r'.zip'

    header_dic = {                                                  # 制作报头
        'filename': filename,
        'md5': 'xxdxx',
        'file_size': os.path.getsize(r'%s/%s' % (download_dir, filename))
    }
    header_json = json.dumps(header_dic)
    header_bytes = header_json.encode('utf-8')

    conn.send(struct.pack('i', len(header_bytes)))                  # 发送报头长度：4

    conn.send(header_bytes)                                         # 发报头

    send_size = 0                                                   # 发送具体数据
    with open('%s/%s' % (download_dir, filename), 'rb') as f :
        for a in f:
            conn.send(a)
            send_size += len(a)
            print(send_size)

# C/S：Client2Center线程
def c2s():
    # 建立socket实例，连接中央服务器
    pc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    pc.connect(('10.38.28.219', 8080))
    print(pc)

    while True:
        rec = pc.recv(1024).decode('utf-8').strip()                 # 接收服务器返回的内容并打印
        print(rec)

        if rec == 'bye':                                            # 服务器返回bye指令：终止通信
            break

        elif rec == 'func3':                                        # 服务器进入功能3
            i = 0
            rec = pc.recv(1024).decode('utf-8').strip()             # 接收好友信息列表
            while True:
                if rec == 'over':                                   # 接收结束
                    break
                print(rec)
                rec = pc.recv(1024).strip().decode('utf-8')
                i = i + 1
            if i == 0:                                              # 好友信息列表空：尚未添加好友
                print("You have no friends yet.")

        elif rec == 'func4':                                        # 服务器进入功能4
            # 建立新的socket实例，连接传输目标用户
            pp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ip = pc.recv(1024).decode("utf-8").strip()
            PK = pc.recv(1024).strip()
            pp.connect((ip, 6000))
            print("Now you are conneted to the target user.")
            print(pp)
            while True:
                inp = input('>>>:').strip()                         # 输入文件传输指令。指令格式：指令+文件名，如：put test.txt
                if not inp:
                    continue
                inp = inp + " " + rID                               # 拼接目标用户ID
                pp.send(inp.encode('utf-8'))                        # 发送指令
                cmds = inp.split()
                if cmds[0] == 'get':
                    cget(pp)                                        # 进入主动下载模块
                elif cmds[0] == 'put':
                    cput(cmds, pp, PK)                              # 进入主动发送模块
                elif cmds[0] == 'close':
                    break                                           # 关闭与对方的连接
            pp.close()

        # 进行文件传输准备工作
        elif 'want to transport' in rec:
            inp = input('>>>:').strip()
            if not inp:
                pc.send("go on".encode('utf-8'))
                continue
            rID = inp                                               # 记录目标用户ID
            pc.send(inp.encode('utf-8'))
            continue

        # 接收服务器返回的本用户ID
        elif rec[:3] == 'ID:':
            ID = rec[3:]
            continue

        # 上传公钥
        elif rec == 'PK':
            create_keys(ID)                                         # 生成密钥对
            with open('public' + ID + '.pem', 'rb') as publickfile:
                p = publickfile.read()
            pc.send(p)                                              # 向服务器发送公钥
            continue

        # 登录时获得本机用户ID
        elif 'Login Successful' in rec:
            ID = pc.recv(1024).decode('utf-8').strip()

        # 向服务器发送指令
        inp = input('>>>:').strip()
        if not inp:
            pc.send("go on".encode('utf-8'))
            continue
        pc.send(inp.encode('utf-8'))


    pc.close()

    cl = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cl.connect((hipaddr, 6000))
    time.sleep(0.2)
    cl.send("close".encode("utf-8"))

#P2P：Server线程
def p2p():
    # 建立socket实例，监听端口准备与其他用户连接
    phone = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    phone.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)     # 回收重用端口10000
    phone.bind((hipaddr, 6000))
    phone.listen(5)
    # 建链接循环
    while True:
        conn, client_addr = phone.accept()
        print(client_addr)
        # 通信循环
        while True:
            try:
                res = conn.recv(1024)                               # 接收文件传输指令
                cmds = res.decode('utf-8').split()                  # 解析命令，提取相应命令参数
                if cmds[0] == 'get':
                    try: sget(cmds, conn)                           # 进入被动上传模块
                    except FileNotFoundError:
                        print("Error: File not found! ")
                        break
                    else:
                        print("Congratulation: The file is in transit! ")
                elif cmds[0] == 'put':                              # 进入被动接收模块
                    sput(conn, cmds[2])
                elif cmds[0] == 'close':                            # 关闭连接
                    break
            except ConnectionResetError:
                break
        conn.close()
        address = str(client_addr).split()
        IP = address[0][2:-2]                                       # 检查主动方IP
        if IP == hipaddr:                                           # 如果主动方为本地
            break                                                   # 终止监听
    phone.close()                                                   # 用于终止程序

#主函数
if __name__ == '__main__':
    client = threading.Thread(target=c2s)
    client.start()                                                  # 启动与中央服务器通信的线程
    server = threading.Thread(target=p2p)
    server.start()                                                  # 启动P2P服务器被动监听，即“上线”
