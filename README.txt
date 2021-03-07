文件安全传输系统 1.0.0

作者：zj、lcz20、lzy

*使用邮箱进行注册，邮箱和用户ID一一对应
*注册新用户时会同时生成密钥对，可以在程序目录下查看
*filesend为主动方发送文件目录，请将需要发送的文件置于此处
*filerec为接受到的原始文件（未解密文件），用于调试
*dec为解密后的文件

服务器数据库结构说明：
本程序使用MSSQL。表结构如下：
username  [  ID(PK,int,not null),  username(nchar,not null),  password(nchar,not null),  email(nchar,notnull),  PK(nchar,not null)  ]
online  [  userID(PK,int,not null),  IP(nchar,not null),  port(int,not null)  ]
friend  [  ID1(int,not null),  ID2(int,null)  ]

客户端命令说明：
1：添加好友（需要对方用户ID）
2：删除好友（需要对方用户ID）
3：查看好友信息（若好友在线，将会显示好友IP和端口号）
4：请求传输文件（需要好友用户ID）
bye：下线，关闭与服务器的连接
注：本系统中的好友关系是单向的。

文件传输指令说明：
使用命令4后，会进入与目标用户的通信界面。再此界面下，可使用如下命令与对方进行文件传输：
put：	将filesend下的文件加密压缩并传输，对方得到后会自动进行解压解密。	格式：put filename	例：put test.txt
get：	将对方filerec下的文件下载到本地filesend文件夹下。不经过加密。	格式：get filename	例：get test.txt
close：	关闭与对方的连接，回到与中央服务器的交互界面。		格式：close