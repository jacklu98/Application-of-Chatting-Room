Jincheng Lu    UNI: jl5801

Initially, use this command in the window to start program:
python3 ChatApp.py


command in program:

ChatApp -s <port>: Start server, the default IP address of server is your local IP.

ChatApp -c <name> <server-ip> <server-port> <client-port>: Start a client. 
Target server is usually the server you set up above, so server-ip could be your local IP, 
and server-port is what you set before. Default IP address of this client is your local IP. 

send <name> <message>: Send inforamtion to a client that you intend.
Name is your intended client's name (eg. mike, x, client1), that is used to register in the server table.
Because any active clients have updated info table from the server, so we can search intened clients' IP and port 
in that table, according to the client's name.

dereg <name>: Tell the server that this person in this client is about to de-register. 
Before send message to the server, should check name with the registered name in this client.
In the server, it will update this name's status to 'no' in the table, and broadcast all active clients.

reg <name>: Tell the server that this de-reg client wants to log back.
Before send message to the server, should check name with the registered name in this client.
In the server, it will update this name's status to 'yes' in the table, and broadcast all active clients.

send_all <message>: chat with all active people in the channel.




