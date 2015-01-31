*****************************************************************************************
IMPORTANT NOTICE: Thanks for referring to the README.txt. Please take minutes to read this file, especially for section d and e, before running the code.

Author:            Zhuo(Kevin) Li
Email:             lizhuogo@gmail.com
Last modification: Dec 10th 2014

All rights reserved.
*****************************************************************************************

a. A brief description of the code

This is a simple version of Distance Vector algorithm that can simulate real routing protocol to update forwarding table among different nodes, based on socket programming and multi-thread processing. It contains only one code script (DVclient.py) for testing. This script can be run on the same or different machine. The nodes will communicate with each other via UDP and updating their own DV tables. 

The brief structure of the python script is as follows.

The codes contains a class Node to represent all the behaviors of the node. The node has two UDP socket: one for listening from its neighbors to get their distance vectors, one for sending its distance vector to its neighbors. The main thread set up two threads first: one for user interface which receives command from the user and one for always listening from its neighbors.

For each neighbor, there are two timers, one for sending distance vector timeout and one for checking if the neighbor is dead without receiving UPDATE more than 3 * timeout.


————————————————————————————————————————————————————————————————————————————————————————
b. Program features

This section is mainly about the communication protocol I used for neighbors communication.

The syntax and format is as follow:

For DV updating message:
<source_ip, source_port, dv_length\n [destination_ip, destination_port, cost, nexthop_ip, nexthop_port\n ...]>

source_ip : the sending node ip
source_port : the sending node port
dv_length : the number of destinations in the distance vector (i.e. how long will the message be

[destination_ip, destination_port, cost, nexthop_ip, nexthop_port]
for each line is a destination together with the cost and next hop
how many destinations there are, how many lines will be followed

Lines are separated by ‘\n’. In each line, elements are separated by ‘,’ .

Example:
127.0.0.1,4115,3\n127.0.0.1,4115,0,127.0.0.1,4115\n127.0.0.1,4116,5,127.0.0.1,4116\n127.0.0.1,4118,10,127.0.0.1,4116\n

This stands for sending a DV of this:
Destination = 127.0.0.1:4115, Cost = 0.000000, Link = (127.0.0.1:4115)
Destination = 127.0.0.1:4116, Cost = 5.000000, Link = (127.0.0.1:4116)
Destination = 127.0.0.1:4118, Cost = 10.000000, Link = (127.0.0.1:4116)

————————————————————————————————————————————————————————————————————————————————————————
c. Details on development environment

Operating System:    Ubuntu 12.04 on VM (Parallels Desktop 9)
IDE:                 Eclipse 4.4.1
Language:            Python 2.7.3

————————————————————————————————————————————————————————————————————————————————————————
d. Instructions on how to run the codes

Just cd to the directory that contains the DVclient.py script and use the following format to invoke the codes

python DVclinet.py 4115 3 127.0.0.1 4116 5.0 127.0.0.1 4118 30.0

————————————————————————————————————————————————————————————————————————————————————————
e. Sample command and usage scenario

parallels@parallels-Parallels-Virtual-Platform:~/Desktop/Parallels Shared Folders/Home/Documents/workspace/DValgorithm/DValgorithm$ python DVclient.py 4115 3 127.0.0.1 4116 5.0 127.0.0.1 4118 30.0
[NODE INFORMATION]
--------------------------------------------------
Node IP:   127.0.0.1 : 4115
Current timeout: 3.0 s
< 8596.98 s > Original Neighbor list is:
Neighbor:  127.0.0.1 : 4116 Direct link cost : 5.000000
Neighbor:  127.0.0.1 : 4118 Direct link cost : 30.000000
--------------------------------------------------
Command>> SHOWRT
--------------------------------------------------------------------------------
< 8701.74 s > Distance Vector list is:
Destination = 127.0.0.1:4115, Cost = 0.000000, Link = (127.0.0.1:4115)
Destination = 127.0.0.1:4116, Cost = 5.000000, Link = (127.0.0.1:4116)
Destination = 127.0.0.1:4118, Cost = 10.000000, Link = (127.0.0.1:4116)
Destination = 127.0.0.1:4117, Cost = 15.000000, Link = (127.0.0.1:4116)
--------------------------------------------------------------------------------
Command>> SHOWNB
--------------------------------------------------
< 8706.19 s > Neighbor list is:
Neighbor:  127.0.0.1 : 4116 Direct link cost : 5.000000
Neighbor:  127.0.0.1 : 4118 Direct link cost : 30.000000
--------------------------------------------------
Command>> LINKDOWN 127.0.0.1 4116
Command>> SHOWRT
--------------------------------------------------------------------------------
< 8966.02 s > Distance Vector list is:
Destination = 127.0.0.1:4115, Cost = 0.000000, Link = (127.0.0.1:4115)
Destination = 127.0.0.1:4116, Cost = 35.000000, Link = (127.0.0.1:4118)
Destination = 127.0.0.1:4118, Cost = 30.000000, Link = (127.0.0.1:4118)
Destination = 127.0.0.1:4117, Cost = 45.000000, Link = (127.0.0.1:4118)
--------------------------------------------------------------------------------
Command>> LINKUP 127.0.0.1 4116
Command>> SHOWRT
--------------------------------------------------------------------------------
< 9116.63 s > Distance Vector list is:
Destination = 127.0.0.1:4115, Cost = 0.000000, Link = (127.0.0.1:4115)
Destination = 127.0.0.1:4116, Cost = 5.000000, Link = (127.0.0.1:4116)
Destination = 127.0.0.1:4118, Cost = 10.000000, Link = (127.0.0.1:4116)
Destination = 127.0.0.1:4117, Cost = 15.000000, Link = (127.0.0.1:4116)
--------------------------------------------------------------------------------
(After we close node 127.0.0.1:4116)
>> Do not receive UPDATE from 127.0.0.1:4116 for 3* 3.000000 s, it is considered as dead.
Command>> 
SHOWRT
--------------------------------------------------------------------------------
< 29187.0 s > Distance Vector list is:
Destination = 127.0.0.1:4115, Cost = 0.000000, Link = (127.0.0.1:4115)
Destination = 127.0.0.1:4118, Cost = 30.000000, Link = (127.0.0.1:4118)
Destination = 127.0.0.1:4117, Cost = infinite, Link = (127.0.0.1:4116)
--------------------------------------------------------------------------------
Command>> 
Command>> HELP
====================================================================================================
COMMAND                        FUNCTIONALITY
----------------------------------------------------------------------------------------------------
SHOWRT                         Show the distance vector list of the node
SHOWNB                         Show the neighbor information of the node
CLOSE                          Close the node permanently
LINKDOWN {ip port}             Temporarily shut down a link between the node and specified neighbor
LINKUP {ip port}               Recover the shut down link between the node and specified neighbor
LINKCHANGE {ip port cost}      Change a link cost between the node and the specified neighbor
CLOSEMODE                      Choose if the node should inform its neighbors when it is close
CHANGETIMEOUT                  Change the timeout value of the node
====================================================================================================
Command>> LINKCHANGE 127.0.0.1 4118 40
Command>> SHOWRT
--------------------------------------------------------------------------------
< 9302.67 s > Distance Vector list is:
Destination = 127.0.0.1:4115, Cost = 0.000000, Link = (127.0.0.1:4115)
Destination = 127.0.0.1:4118, Cost = 40.000000, Link = (127.0.0.1:4118)
Destination = 127.0.0.1:4117, Cost = infinite, Link = (127.0.0.1:4116)
--------------------------------------------------------------------------------
Command>> CHANGETIMEOUT
>> Please enter the new timeout value: 4
>> Now the timeout value of the node is: 4.000000 s
————————————————————————————————————————————————————————————————————————————————————————
f. Additional functions

1) Extra command for user

[DESCRIPTION] I also implement SHOWNB, LINKCHANGE, CLOSEMODE, CHANGETIMEOUT command for user. The functionality of the command can be found when you type HELP in the user interface.

SHOWNB: To show the neighbors of the node, including the current link cost

LINKCHANGE: Change the link cost according to the format in HELP or the sample in section e. This can increase or decrease the cost. No count to infinite problem will happen. Because a poisson reverse mechanism is implemented as shown in 2)

CLOSEMODE: This is to choose whether the node should tell its neighbor about its close when it it about to be closed. The default is not to tell and let the neighbors to find it is dead according to the time out of 3*timeout. But you can change the mode to tell the neighbor about this when manually shut down a node. This can update the DV in the neighbors before the 3*timeout happens which speed up a new converge.

CHANGETIMEOUT: It is easy to understand. Just to change the timeout value that will be used.

[TEST] Just use this command in the user command interface, you will see the functionality.

2) Support poisson reverse

[DESCRIPTION] A poisson reverse mechanism is implemented and you can increase the link cost without worrying about counting to infinite.

[TEST] Use LINKCHANGE command (in the given format) to increase the link cost and see the DV tables of the nodes again 

*****************************************************************************************
Thanks for reading the README.txt. Because of time limited, quite a lot other essential functionalities I came up with can not be completed. And there is also possible to have some BUGs I haven’t found out. It needs the feedback from the user experiences. But I am sure there will be no big problems in the program.

Kevin Li
10th Dec 2014 
*****************************************************************************************

