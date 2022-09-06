from socket import *
from threading import Thread
import time
import os
import sys

global Copen
Copen = False
global ChatSuccess
ChatSuccess = False
global Channel
Channel = False
global ServerStatus
ServerStatus = False
global ClientStatus
ClientStatus = False
global SAStatus
SAStatus = False
global TClose
TClose = True
global TargetAddress
global SAFlag
SAFlag = False
global CSFlag
CSFlag = False


class Client():
    def __init__(self, name, client_IP, client_port, server_IP, server_port):
        # initialization
        self.table = []
        self.name = name
        self.clientIP = client_IP
        self.clientPort = client_port
        self.serverIP = server_IP
        self.serverPort = server_port
        self.clientSocket = socket(AF_INET, SOCK_DGRAM)
        self.thread_recv = Thread(target=self.recv_msg, daemon=True)
        self.thread_send = Thread(target=self.send_msg)

    def start(self):
        # start run
        self.clientSocket.bind((self.clientIP, self.clientPort))
        reg_msg = "-c " + str(self.name)
        # register
        self.clientSocket.sendto(reg_msg.encode(), (self.serverIP, self.serverPort))
        response, server_addr = self.clientSocket.recvfrom(2048)
        if response.decode() == "registered":
            global Copen
            Copen = True
            print(">>> [Welcome, you are registered.]")

        self.thread_recv.start()
        self.thread_send.start()
        self.thread_recv.join()
        self.thread_send.join()

    def recv_msg(self):
        # 接收信息
        while True:
            recv_data, source_addr = self.clientSocket.recvfrom(2048)
            source_ip, source_port = source_addr
            msg = recv_data.decode()
            seg = msg.split(' ')
            # de-reg succeed
            if msg == 'deregack' and source_ip == self.serverIP and source_port == self.serverPort:
                global Copen
                Copen = False
                print(">>> [You are Offline. Bye.]")

            # chat succeed
            if seg[0] == "sendack":
                global ChatSuccess
                ChatSuccess = True
                source_name = seg[1]
                print(">>> [Message received by " + source_name + " ]")

            # check status
            elif msg == "status":
                status_message = "online " + self.name
                self.clientSocket.sendto(status_message.encode(), (self.serverIP, self.serverPort))

            # channel succeed
            elif msg == "channelack":
                global Channel
                Channel = True
                print(">>> Message received by Server.")

            # channel message receive
            elif seg[0] == "Channel_Message":
                self.clientSocket.sendto("ack".encode(), (self.serverIP, self.serverPort))
                print(">>> " + msg)

            # target client is online
            elif seg[0] == "err":
                print(">>> [Client " + seg[1] + " exists!!]")

            # save msg succeed in server
            elif seg[0] == "saveack":
                global ServerStatus
                ServerStatus = True
                print(">>> [Messages received by the server and saved]")

            # print leave msg
            elif seg[0] == "left":
                print(">>> " + ' '.join(seg[1:]))

            # update local table
            elif seg[0] == "table":
                self.table = seg[1:]
                print(">>> [Client table updated. ]")

            # receive chat
            elif seg[0] == "send":
                # respond ack
                response = "sendack " + self.name
                self.clientSocket.sendto(response.encode(), source_addr)
                # present message
                source_name = seg[1]
                message = ">>> " + source_name + ": " + ' '.join(seg[2:])
                print(message)

    def send_msg(self):
        # 发送信息
        while True:
            data_info = input(">>> ").strip()
            sentence = data_info.split(' ')
            # de-reg
            if sentence[0] == "dereg":
                # validation
                while sentence[0] == "dereg" and sentence[1] != self.name:
                    print("Error! Please input corresponding name.")
                    data_info = input(">>> ").strip()
                    sentence = data_info.split(' ')
                self.clientSocket.sendto(data_info.encode(), (self.serverIP, self.serverPort))
                time.sleep(0.5)
                times = 0
                # 500ms no response retry 5 times
                while Copen is True and times < 5:
                    self.clientSocket.sendto(data_info.encode(), (self.serverIP, self.serverPort))
                    time.sleep(0.5)
                    times += 1

                if times == 5:
                    print(">>> [Server not responding]")
                    print(">>> [Exiting]")

            # log back
            if sentence[0] == "reg":
                if sentence[0] == "reg" and sentence[1] == self.name:
                    self.clientSocket.sendto(data_info.encode(), (self.serverIP, self.serverPort))
                else:
                    status = "no"
                    # validation
                    login_name = sentence[1]
                    for i in range(0, len(self.table), 4):
                        # direct chat
                        if self.table[i] == login_name:
                            status = self.table[i+3]
                            break

                    while sentence[0] == "reg" and status == "yes":
                        print("This name exists! Please use another name.")
                        data_info = input(">>> ").strip()
                        sentence = data_info.split(' ')
                        login_name = sentence[1]
                        for i in range(0, len(self.table), 4):
                            # direct chat
                            if self.table[i] == login_name:
                                status = self.table[i + 3]
                                break

                    self.clientSocket.sendto(data_info.encode(), (self.serverIP, self.serverPort))



            # channel
            elif sentence[0] == "send_all":
                msg = "send_all " + self.name + ": " + ' '.join(sentence[1:])
                global Channel
                Channel = False
                self.clientSocket.sendto(msg.encode(), (self.serverIP, self.serverPort))
                time.sleep(0.5)
                times = 0
                # channel ack time out and repeat 5 times
                while Channel is False and times < 5:
                    self.clientSocket.sendto(msg.encode(), (self.serverIP, self.serverPort))
                    time.sleep(0.5)
                    times += 1

                if times == 5:
                    print(">>> [Server not responding.]")

            # chat
            elif sentence[0] == "send":
                target_name = sentence[1]
                message = "send " + self.name + " " + ' '.join(sentence[2:])
                for i in range(0, len(self.table), 4):
                    # direct chat
                    if self.table[i] == target_name:
                        target_ip, target_port, status = self.table[i+1], int(self.table[i+2]), self.table[i+3]
                        break
                if status == "yes":
                    global ChatSuccess
                    ChatSuccess = False
                    self.clientSocket.sendto(message.encode(), (target_ip, target_port))
                    time.sleep(0.5)
                    # 500ms time out -- offline chat -- silent leave
                    if ChatSuccess is False:
                        print(">>> [No ACK from " + target_name + ", message sent to server]")
                        message = "NOACK " + target_name + " " +self.name+" "+ ' '.join(sentence[2:])
                        self.clientSocket.sendto(message.encode(), (self.serverIP, self.serverPort))

                # offline chat -- notified leave
                elif status == "no":
                    print(">>> [No ACK from " + target_name + ", message sent to server]")
                    message = "save " + target_name + " " +self.name+" "+ ' '.join(sentence[2:])
                    global ServerStatus
                    ServerStatus = False
                    self.clientSocket.sendto(message.encode(), (self.serverIP, self.serverPort))
                    time.sleep(0.5)
                    times = 0
                    # 500ms no response retry 5 times
                    while ServerStatus is False and times < 5:
                        self.clientSocket.sendto(message.encode(), (self.serverIP, self.serverPort))
                        time.sleep(0.5)
                        times += 1

                    if times == 5:
                        print(">>> [Server not responding]")
                        print(">>> [Exiting]")


class Server():
    def __init__(self, address):
        self.__SOpen = False
        self.table = []
        self.channel = []
        self.online_list = []
        self.file_status = {}
        self.serverAddr = address
        self.serverSocket = socket(AF_INET, SOCK_DGRAM)
        # local port number
        self.serverSocket.bind(self.serverAddr)
        self.thread1 = Thread(target=self.recv_msg)
        # self.thread_send = Thread(target=self.send_msg)
        self.thread2 = Thread(target=self.recv_msg)

    def start(self):
        self.__SOpen = True
        print("The server starts!")
        self.thread1.start()
        self.thread2.start()
        self.thread1.join()
        self.thread2.join()

    def recv_msg(self):
        # keep operating
        while True:
            recv_data, client_addr = self.serverSocket.recvfrom(2048)

            print(client_addr, recv_data)
            info_list = str(recv_data.decode()).split(' ')
            ip, port = client_addr[0], client_addr[1]
            # client de-register
            if info_list[0] == 'dereg':
                name = info_list[1]
                self.online_list = []
                for i in range(len(self.table)):
                    seg = self.table[i].split(' ')
                    # account in this address offline
                    if seg[0] == name and seg[1] == ip and int(seg[2]) == port:
                        seg[3] = "no"
                        self.table[i] = seg[0] + " " + seg[1] + " " + seg[2] + " no"
                    # record online client
                    elif seg[3] == "yes":
                        self.online_list.append((seg[1], int(seg[2])))
                # broadcast updated table to online clients
                self.broadcast("table " + ' '.join(self.table), self.online_list)
                # send ack to this client
                self.serverSocket.sendto("deregack".encode(), client_addr)

            # client register
            elif info_list[0] == '-c':
                # update table
                new_client = info_list[1] + " " + client_addr[0] + " " + str(client_addr[1]) + ' yes'
                self.table.append(new_client)
                self.channel.append((client_addr[0], client_addr[1]))
                self.online_list.append((client_addr[0], client_addr[1]))
                # reply client
                self.serverSocket.sendto("registered".encode(), client_addr)
                # broadcast updated table to online clients
                self.broadcast("table " + ' '.join(self.table), self.online_list)
                # self.broadcast(">>> [Client table updated.]", self.online_list)

            # send to all
            elif info_list[0] == "send_all":
                # respond client ack
                self.serverSocket.sendto("channelack".encode(), client_addr)

                broadcast_message = "Channel_Message " + ' '.join(info_list[1:])
                save_message = "Channel_Message " + str(info_list[1]) + self.timestamp() + ' '.join(info_list[2:])

                # send active
                self.send_to_all(broadcast_message, self.online_list, client_addr)
                # send offline
                addrs = set(self.channel).difference(set(self.online_list))
                for addr in addrs:
                    (ip, port) = addr
                    for i in range(len(self.table)):
                        seg = self.table[i].split(' ')
                        # account in this address offline
                        if seg[1] == ip and int(seg[2]) == port:
                            target_name = seg[0]
                            self.save_file(target_name, save_message)
                            break

            # log back
            elif info_list[0] == "reg":
                user_name = info_list[1]

                # check saved msg
                if user_name in self.file_status:
                    if self.file_status[user_name] is True:
                        # send left msg
                        self.serverSocket.sendto("left You have messages".encode(), client_addr)
                        file_name = user_name + ".txt"
                        for line in open(file_name, "r"):
                            msg = "left " + line
                            self.serverSocket.sendto(msg.encode(), client_addr)
                        # delete leave msg file
                        self.file_status[user_name] = False
                        os.remove(file_name)

                # update status
                for i in range(len(self.table)):
                    seg = self.table[i].split(' ')
                    # account in this address offline
                    if seg[0] == user_name:
                        self.table[i] = seg[0] + " " + seg[1] + " " + seg[2] + " yes"
                        # record online client
                        self.online_list.append((seg[1], int(seg[2])))
                        break
                # a new user
                if i == len(self.table):
                    new_client = info_list[1] + " " + client_addr[0] + " " + str(client_addr[1]) + ' yes'
                    self.table.append(new_client)
                    self.channel.append((client_addr[0], client_addr[1]))
                    self.online_list.append((client_addr[0], client_addr[1]))
                # broadcast updated table to online clients
                self.broadcast("table " + ' '.join(self.table), self.online_list)

            # save msg
            elif info_list[0] == "save":
                # save msg file
                target_name = info_list[1]
                source_name = info_list[2]
                self.file_status[target_name] = True
                leave_message = source_name + ": " + self.timestamp() + ' '.join(info_list[3:])
                file_name = target_name + ".txt"
                file = open(file_name, "a")
                file.write(leave_message + "\n")
                file.close()

                # ack
                self.serverSocket.sendto("saveack".encode(), client_addr)

            # save no ack msg progress
            elif info_list[0] == "NOACK":
                global TClose
                target_name = info_list[1]
                # check client status
                for i in range(len(self.table)):
                    seg = self.table[i].split(' ')
                    # find target
                    if seg[0] == target_name:
                        target_ip, target_port = seg[1], int(seg[2])
                        break
                global ClientStatus
                ClientStatus = False
                global TargetAddress
                TargetAddress = (target_ip, target_port)

                TClose = False
                # check target client status
                self.serverSocket.sendto("status".encode(), (target_ip, target_port))
                # if client offline: update status and broadcast table
                time.sleep(0.5)
                if ClientStatus is False:
                    revised = False

                    self.online_list = []
                    for i in range(len(self.table)):
                        seg = self.table[i].split(' ')
                        # account in this address offline
                        if seg[0] == target_name and seg[1] == target_ip and int(seg[2]) == target_port:
                            if seg[3] != "no":
                                revised = True
                            seg[3] = "no"

                            self.table[i] = seg[0] + " " + seg[1] + " " + seg[2] + " no"
                        # record online client
                        if seg[3] == "yes":
                            self.online_list.append((seg[1], int(seg[2])))
                    # broadcast updated table to online clients
                    if revised:
                        self.broadcast("table " + ' '.join(self.table), self.online_list)

                    # save msg file
                    source_name = info_list[2]
                    self.file_status[target_name] = True
                    leave_message = source_name + ": " + self.timestamp() + ' '.join(info_list[3:])
                    file_name = target_name + ".txt"
                    file = open(file_name, "a")
                    file.write(leave_message + "\n")
                    file.close()

                    # ack
                    self.serverSocket.sendto("saveack".encode(), client_addr)

                    TClose = True

            # client is online
            if info_list[0] == "online":
                ClientStatus = True
                client_name = info_list[1]
                error_message = "err " + client_name
                self.serverSocket.sendto(error_message.encode(), TargetAddress)

                self.online_list = []
                for i in range(len(self.table)):
                    seg = self.table[i].split(' ')
                    # account in this address offline
                    if seg[0] == client_name:
                        self.table[i] = seg[0] + " " + seg[1] + " " + seg[2] + " yes"
                        self.online_list.append((seg[1], int(seg[2])))
                        break
                # broadcast updated table to online clients
                self.broadcast("table " + ' '.join(self.table), self.online_list)
                TClose = True

            elif info_list[0] == "ack":
                global SAStatus
                SAStatus = True
                TClose = True

    # update table to active clients
    def broadcast(self, data_info, addr_list):
        for address in addr_list:
            self.serverSocket.sendto(data_info.encode(), address)

    # broadcast to active clients in channel
    def send_to_all(self, data_info, addr_list, except_addr):
        for address in addr_list:
            if address == except_addr:
                continue
            global SAStatus
            SAStatus = False
            global TClose
            TClose = False

            self.serverSocket.sendto(data_info.encode(), address)
            time.sleep(0.5)
            # time out
            if SAStatus is False:
                # check status
                global ClientStatus
                ClientStatus = False
                # check target client status
                self.serverSocket.sendto("status".encode(), address)
                # if client offline: update status and broadcast table
                time.sleep(0.5)
                if ClientStatus is False:
                    TClose = True
                    (ip, port) = address
                    revised = False

                    self.online_list = []
                    for i in range(len(self.table)):
                        seg = self.table[i].split(' ')
                        # account in this address offline
                        if seg[1] == ip and int(seg[2]) == port:
                            if seg[3] != "no":
                                revised = True
                            seg[3] = "no"
                            self.table[i] = seg[0] + " " + seg[1] + " " + seg[2] + " no"
                        # record online client
                        if seg[3] == "yes":
                            self.online_list.append((seg[1], int(seg[2])))
                    # broadcast updated table to online clients
                    if revised:
                        self.broadcast("table " + ' '.join(self.table), self.online_list)

    # save leave msg in file
    def save_file(self, target_name, msg):
        self.file_status[target_name] = True
        file_name = target_name + ".txt"
        file = open(file_name, "a")
        file.write(msg + "\n")
        file.close()

    # get time stamp
    def timestamp(self):
        return ' <' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + '> '


if __name__ == '__main__':
    # client mode
    if sys.argv[1] == "-c":
        # validation
        if int(sys.argv[4]) < 1024 or int(sys.argv[4]) > 65535:
            print("client port number 1024 ~ 65535.")
            sys.exit()

        name = sys.argv[2]
        server_ip = sys.argv[3]
        server_port = int(sys.argv[4])
        client_port = int(sys.argv[5])
        client = Client(name, '', client_port, server_ip, server_port)
        client.start()

    # server mode
    elif sys.argv[1] == "-s":
        # validation
        if int(sys.argv[2]) < 1024 or int(sys.argv[2]) > 65535:
            print("server port number 1024 ~ 65535.")
            sys.exit()

        port_number = int(sys.argv[2])
        server1 = Server(('', port_number))
        server1.start()