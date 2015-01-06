'''
----------------W4119 Programming Assignment 3---------------
Created Date:        Dec 6, 2014
File name:           DVclinet.py
Operating System:    Ubuntu 12.04 on VM (Parallels Desktop 9)
IDE:                 Pycharm Community Edition 3.4.1
Language:            Python 2.7.3
Author:              Zhuo (Kevin) Li
---------------------All rights reserved---------------------
'''
#---------------------Source Import--------------------
import sys
import socket
import time
import thread
from threading import Thread

#-----------------------Variables----------------------
INFINITE = 9999999999                  # The value of infinite cost
TIMEOUT = 0                            # Original timeout set by the user
NEIGHBOR_LIST = []                     # Original neighbor_list
DV_LIST = []                           # Original dv_list
NEIGHBOR_NUM = 0                       # Original neighbor_num

CLOSE_INFORMING = False                # Flag for whether informing the neighbors about the closing
NODE_SHUTDOWN = False                  # Flag for whether this node has been shut down
CLOSE_NEIGHBOR = INFINITE              # Number of the closed neighbor in the neighbor_list, infinite means no neighbor is closed in the neighbor_list

#------------------------Classes-----------------------
class Node:
    "This class represents the node(client). It includes the possible behaviors of the node"
    listen_socket = 0                                      # The listening UDP socket
    neighbor_socket = 0                                    # The UDP socket used to send DV to neighbors
    linkdown_neighbor = []                                 # To store linkdown neighbor information for recovering
    
    def __init__(self, host, port, init_neighbor_num, init_neighborlist, init_DVtable, init_timeout):
        "Initialization of the node"
        self.node_ip = host
        self.node_port = port
        self.neighbor_num = init_neighbor_num
        # Each element in the neighbor_list and dv_list is a list for a neighbor node and another node in the network respectively. 
        # The format of each element is: [(neighbor_ip, neighbor_port), cost, [neighbor_current_dvlist], [start_time, stop_time], [check_dead_start_time, check_dead_stop_time]]
        self.neighbor_list = init_neighborlist             
        # The format of each element is: [(destination_ip, destination_port), cost, [nexthop_ip, nexthop_port]]
        self.dv_list = init_DVtable                        
        self.timeout = init_timeout
    
    def init_listen_socket(self):
        "Initialization of the UDP listening socket"
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        self.listen_socket.bind((self.node_ip, self.node_port))

    def init_neighbor_socket(self):
        "Initialization of the UDP socket to send data to neighbors"
        self.neighbor_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    def init_display(self):
        "Display initial settings at the beginning"
        
        print '[NODE INFORMATION]'
        print '-' * 50
        print 'Node IP:'.ljust(10), self.node_ip, ':', self.node_port
        print 'Current timeout:'.ljust(10), self.timeout, 's'
        print '< %s s > Original Neighbor list is:'%str(time.time())[-7:]
        for num in range(self.neighbor_num):
            print 'Neighbor:'.ljust(10), '%s : %d'%(self.neighbor_list[num][0][0], self.neighbor_list[num][0][1]), 'Direct link cost : %f'%self.neighbor_list[num][1] 
        print '-' * 50
        
    def display_neighbor(self):
        "Display the neighbors of the node"
        
        print '-' * 50
        print '< %s s > Neighbor list is:'%str(time.time())[-7:]
        for num in range(self.neighbor_num):
            if self.neighbor_list[num][1] != INFINITE:
                print 'Neighbor:'.ljust(10), '%s : %d'%(self.neighbor_list[num][0][0], self.neighbor_list[num][0][1]), 'Direct link cost : %f'%self.neighbor_list[num][1] 
            else:
                print 'Neighbor:'.ljust(10), '%s : %d'%(self.neighbor_list[num][0][0], self.neighbor_list[num][0][1]), 'Direct link cost : infinite(link temporary down)'
        print '-' * 50 
            
    def display_table(self):
        "Display current Distance Vector list of the node"
        #print self.dv_list
        print '-' * 80
        print '< %s s > Distance Vector list is:'%str(time.time())[-7:]
        for num in range(len(self.dv_list)):
            if self.dv_list[num][1] == INFINITE:
                print 'Destination = %s:%d, Cost = infinite, Link = (%s:%d)'%(self.dv_list[num][0][0], self.dv_list[num][0][1], self.dv_list[num][2][0], self.dv_list[num][2][1])
            else:
                print 'Destination = %s:%d, Cost = %f, Link = (%s:%d)'%(self.dv_list[num][0][0], self.dv_list[num][0][1], self.dv_list[num][1], self.dv_list[num][2][0], self.dv_list[num][2][1])
        print '-' * 80
    
    def dv_sending(self, neighbor_num):
        "To send the DV of the node to each of its neighbors"
        # Messages used in inter-client communication are under particular sending format as follows
        # Sending format <source_ip, source_port, dv_length\n [destination_ip, destination_port, cost, nexthop_ip, nexthop_port\n ...]>
        
        # Calculating each part of the sending format
        source_ip = self.node_ip
        source_port = str(self.node_port)
        dv_length = str(len(self.dv_list))
        dv_message = source_ip + ',' + source_port + ',' + dv_length + '\n'
        for num in range(len(self.dv_list)):
            dv_message += self.dv_list[num][0][0] + ',' + str(self.dv_list[num][0][1]) + ',' + str(self.dv_list[num][1]) + ',' + self.dv_list[num][2][0] + ',' + str(self.dv_list[num][2][1]) + '\n'
            
        #Send the message to the specific neighbor, if the cost is not infinite (the link is not down)
        if self.neighbor_list[neighbor_num][1] != INFINITE:
            self.neighbor_socket.sendto(dv_message, (self.neighbor_list[neighbor_num][0][0], self.neighbor_list[neighbor_num][0][1]))
            
    def dv_receiving(self):
        "To receive DV of the neighbors"
        
        global CLOSE_NEIGHBOR
        
        # When receiving DV from the neighbors, the node should check:
        # 1. If it is a new neighbor?
        # 2. If there are new destinations in the received DV?
        # 3. If there are destinations that are closed and need to be deleted
        
        while True:
            message = self.listen_socket.recv(1024)
            
            if  message[0:7] == '<close>':
                
                close_neighbor_ip = message[7:message.find(',')]
                close_neighbor_port = int(message[message.find(',')+1:])
                
                # Find the neighbor that is closed and delete it from the neighbor_list 
                for num in range(self.neighbor_num):
                    if self.neighbor_list[num][0][0] == close_neighbor_ip and self.neighbor_list[num][0][1] == close_neighbor_port:
                        close_neighbor = num
                        CLOSE_NEIGHBOR = close_neighbor 
                        time.sleep(0.1)      # Waiting for the close of timer thread
                        self.neighbor_num -= 1
                del self.neighbor_list[close_neighbor]
                
                # Find the neighbor that is closed and delete it from the dv_list
                for num in range(len(self.dv_list)):
                    if self.dv_list[num][0][0] == close_neighbor_ip and self.dv_list[num][0][1] == close_neighbor_port:
                        close_neighbor = num
                del self.dv_list[close_neighbor]
                
                # Change the cost of destinations in the dv_list which are with the closed neighbor as the next hop to infinite
                for dests in self.dv_list:
                    if dests[2][0] == close_neighbor_ip and dests[2][1] == close_neighbor_port:
                        dests[1] = INFINITE 
                
                # Send updated DV to all the neighbors
                for num in range(self.neighbor_num):
                    self.dv_sending(num)   
                    # restart the sending timer if the link is not down (start_time != -1)
                    if self.neighbor_list[num][3][0] != -1:  
                        self.neighbor_list[num][3][0] = time.time()     
                        
            elif message[0:10] == '<linkdown>' :
                
                linkdown_neighbor_ip = message[10:message.find(',')]
                linkdown_neighbor_port = int(message[message.find(',')+1:])      
                
                # Set the cost in the neighbor_list of the link to infinite
                for neighbors in self.neighbor_list:
                    if neighbors[0][0] == linkdown_neighbor_ip  and neighbors[0][1] == linkdown_neighbor_port:
                        self.linkdown_neighbor.append([(linkdown_neighbor_ip,linkdown_neighbor_port),neighbors[1]])
                        neighbors[1] = INFINITE
                        # Stop the sending timer and death detecting timer of this neighbor
                        neighbors[3][0] = -1
                        neighbors[3][1] = -1
                        neighbors[4][0] = -1
                        neighbors[4][1] = -1
                # Set the cost of destinations in dv_list which next hops are the neighbor to infinite
                for dests in self.dv_list:
                    if dests[2][0] == linkdown_neighbor_ip and dests[2][1] == linkdown_neighbor_port:
                        dests[1] = INFINITE
                
                # Send updated DV to all the neighbors
                for num in range(self.neighbor_num):
                    self.dv_sending(num)   
                    # restart the sending timer if the link is not down (start_time != -1)
                    if self.neighbor_list[num][3][0] != -1:  
                        self.neighbor_list[num][3][0] = time.time() 
                
                
            elif message[0:8] == '<linkup>':
                
                linkup_neighbor_ip = message[8:message.find(',')]
                linkup_neighbor_port = int(message[message.find(',')+1:]) 
                
                original_cost = 0
                recovery_link = 0
                
                # To find the stored link cost
                for num in range(len(self.linkdown_neighbor)):
                    if self.linkdown_neighbor[num][0][0] == linkup_neighbor_ip and self.linkdown_neighbor[num][0][1] == linkup_neighbor_port:
                        original_cost = self.linkdown_neighbor[num][1]
                        recovery_link = num
                # Delete the neighbor from the linkdown_neighbor list
                del self.linkdown_neighbor[recovery_link]
        
                # Recover the original link cost in the neighbor_list
                for neighbors in self.neighbor_list:
                    if neighbors[0][0] == linkup_neighbor_ip and neighbors[0][1] == linkup_neighbor_port:
                        neighbors[1] = original_cost
                        # Restart the sending timer and death detecting timer of the neighbor
                        neighbors[3][0] = time.time()
                        neighbors[3][1] = time.time()
                        neighbors[4][0] = time.time()
                        neighbors[4][1] = time.time()
            
            elif message[0:12] == '<linkchange>':
                
                message = message.split(',')
                
                linkchange_neighbor_ip = message[0][message[0].find('>')+1:]
                linkchange_neighbor_port = int(message[1])
                linkchange_cost = float(message[2])
                
                # Set the cost in the neighbor_list of the link to infinite
                for neighbors in self.neighbor_list:
                    if neighbors[0][0] == linkchange_neighbor_ip  and neighbors[0][1] == linkchange_neighbor_port:
                    
                        neighbors[1] = linkchange_cost
                    
                # Set the cost of destinations in dv_list which next hops are the neighbor to infinite
                for dests in self.dv_list:
                    if dests[2][0] == linkchange_neighbor_ip and dests[2][1] == linkchange_neighbor_port:
                        dests[1] = INFINITE
                
                # Send updated DV to all the neighbors
                for num in range(self.neighbor_num):
                    self.dv_sending(num)   
                    # restart the sending timer if the link is not down (start_time != -1)
                    if self.neighbor_list[num][3][0] != -1:  
                        self.neighbor_list[num][3][0] = time.time() 
                        
            else:
                new_neighbor = True
                new_destination = False
                
                # Decode the received message according to the sending format
                # Then store the information in a list as the following format:
                # message format here: [[source_ip, source_port, dv_length], [destination_ip, destination_port, cost, nexthop_ip, nexthop_port], ...]         
                message = message.splitlines()  
                for num in range(len(message)):
                    message[num] = message[num].split(',') 
                
                # Get the header of the message   
                source_ip = message[0][0]
                source_port = int(message[0][1])
                dv_length = int(message[0][2])
            
                # Check with the neighbor list to determine if it is received from a new neighbor
                for num in range(self.neighbor_num):
                    if self.neighbor_list[num][0][0] == source_ip and self.neighbor_list[num][0][1] == source_port:
                        this_neighbor = num
                        self.neighbor_list[num][4][0] = time.time()
                        #print self.neighbor_list[num][0][1], 'dead time start updated'
                        new_neighbor = False
            
                # If it is not a new neighbor
                if new_neighbor == False:
                    
                    this_is_new_dest = [True]
                    # Save its DV to the neighbor list of the node
                    for num in range(dv_length): 
                        self.neighbor_list[this_neighbor][2].append([message[num+1][0],int(message[num+1][1]),float(message[num+1][2]),message[num+1][3],int(message[num+1][4])])
                        updated_neighbor = this_neighbor
                    # Comparing the dv_list of the node with the destinations in the receiving dv of the neighbor
                    # To see if there are destinations that do not in the dv_list of the node.(i.e. new destinations)
                    for lines in self.neighbor_list[this_neighbor][2]:
                        for dests in self.dv_list:
                            if lines[0] == dests[0][0] and lines[1] == dests[0][1]:
                                this_is_new_dest.append(False)
                        # Only when there is no such destination in its dv_list and the destination is not hopped by itself, it can be a new destination
                        if False not in this_is_new_dest and (lines[3] != self.node_ip or lines[4] != self.node_port):
                            new_destination = True
                            #print 'new des'
                        this_is_new_dest = [True]
                    
                    # To find if there are some destination closed and need to be deleted
                    del_mark = []                               # To mark the index of destinations that need to be deleted
                    this_is_del_dest = [True]
                    # Comparing the receiving dv of the neighbor with the dv_list of the node
                    # If the dv of the neighbor has a destination with hop of this node, which is not in the dv_list of this node, it needs to be deleted
                    for dests in self.dv_list:
                        if dests[2][0] == source_ip and dests[2][1] == source_port:
                            for lines in self.neighbor_list[this_neighbor][2]:
                                if lines[0] == dests[0][0] and lines[1] == dests[0][1]:
                                    this_is_del_dest.append(False)
                            if False not in this_is_del_dest:
                                #del_destination = True
                                del_mark.append(self.dv_list.index(dests))
                        this_is_del_dest = [True]
                    # To delete the destinations marked in the dv_list
                    for num in del_mark:
                        del self.dv_list[num]        
                    
                
                # If it is a new neighbor   
                else:
                                     
                    # Update neighbor number
                    self.neighbor_num += 1
                    # Find the cost between the node and this new neighbor. And add it to the neighbor list of the node
                    for num in range(dv_length):
                        if message[num+1][0] == self.node_ip  and int(message[num+1][1]) == self.node_port:
                            cost = float(message[num+1][2])
                    self.neighbor_list.append([(source_ip, source_port) ,cost,[], [time.time(), time.time()], [time.time(),0]])
                    # For a new neighbor, a new sending timer and death detecting timer should be set up
                    new_thread = Thread(target = self.timeout_sending, args = (self.neighbor_num-1,))
                    new_thread.setDaemon(True)
                    new_thread.start()
                    new_thread = Thread(target = self.timeout_dead_detect, args = (self.neighbor_num-1,))
                    new_thread.setDaemon(True)
                    new_thread.start()            
                    
                    # Save its DV to the neighbor list of the node
                    for num in range(dv_length):
                        self.neighbor_list[self.neighbor_num-1][2].append([message[num+1][0],int(message[num+1][1]),float(message[num+1][2]),message[num+1][3],int(message[num+1][4])])
                        updated_neighbor = self.neighbor_num-1
                        new_destination = True
    
            
                # Use Bellman-Ford equation to update dv_list of the node
                updated = self.dv_updating(new_destination, updated_neighbor)
                # If there are any changes in the dv_list, restart timer and send the dv to all the neighbors
                if updated == True:
    
                    for num in range(self.neighbor_num):
                        self.dv_sending(num)   
                        if self.neighbor_list[num][3][0] != -1:  
                            self.neighbor_list[num][3][0] = time.time() 
                            
                # Empty the current dv for each neighbor in the neighbor_list
                for neighbors in self.neighbor_list:
                    neighbors[2] = []
    
    def dv_updating(self, new_dest, neighbor):
        "Use Bellman-Ford equation to update the distance vector"
        updated = False
        this_is_new = [True]
        
        # If there are any new destinations in the received dv
        # the node will find the addresses of the new destinations and add it the the dv_list of the node
        if new_dest == True:
            new_destination_ip = []
            new_destination_port = []
            # Comparing the dv_list of the node with the destinations in the receiving dv of the neighbor
            # To see if there are destinations that do not in the dv_list of the node.(i.e. new destinations)
            for lines in self.neighbor_list[neighbor][2]:
                for dests in self.dv_list:
                    if lines[0] == dests[0][0] and lines[1] == dests[0][1]:
                        this_is_new.append(False)
                if False not in this_is_new:
                    new_destination_ip.append(lines[0])
                    new_destination_port.append(lines[1])
                this_is_new = [True]
            
            new_cost = INFINITE                # This stands for infinite cost
            # Add new destinations to the dv_list of the node
            for num in range(len(new_destination_ip)):
                self.dv_list.append([(new_destination_ip[num],new_destination_port[num]),new_cost,[new_destination_ip[num],new_destination_port[num]], 'on'])
        
        # Calculate cost to all the destinations via the neighbor
        for nodes in self.dv_list:
            current_ip = nodes[0][0]
            current_port = nodes[0][1]
            for neighbors in self.neighbor_list:
                for num in range(len(neighbors[2])):
                    if neighbors[2][num][0] == current_ip and neighbors[2][num][1] == current_port:  
                        cost = neighbors[1] + neighbors[2][num][2]        # This is the sum cost via the neighbor
                        # Check with current cost, if it is smaller, update the cost and next hop address
                        if cost < nodes[1] and (neighbors[2][num][3] != self.node_ip or neighbors[2][num][4] != self.node_port):              
                            nodes[1] = cost
                            nodes[2][0] = neighbors[0][0]                 # Update ip of the next hop
                            nodes[2][1] = neighbors[0][1]                 # Update port of the next hop
                            # To mark changes in dv_list, tell the node to send dv to neighbors then
                            updated = True
                        # This is in case of link down situation. Even though the cost in dv less then the sum=(node to neighbor +neighbor to destination) , the next hop is actually the neighbor
                        # So it can not be the cost as in the dv. Then set it to infinite and converge again. 
                        if cost > nodes[1] and nodes[2][0] == neighbors[0][0] and nodes[2][1] == neighbors[0][1]:
                            nodes[1] = INFINITE
                            updated = True
                                                            
        # Return the flag of updates
        return updated
        
    def node_close(self):
        "To close the node"
        
        global NODE_SHUTDOWN
        
        if CLOSE_INFORMING == True:
            #Send the closing message to all the neighbors
            close_message = '<close>' + self.node_ip + ',' + str(self.node_port)
            for num in range(self.neighbor_num):
                self.neighbor_socket.sendto(close_message, (self.neighbor_list[num][0][0], self.neighbor_list[num][0][1]))
        
        NODE_SHUTDOWN = True
    
    def node_linkdown(self, down_ip, down_port):
        "To destroy an existing link"
        
        # Check if it is in the neighbor_list of the node
        not_neighbor = True
        for neighbors in self.neighbor_list:
            if neighbors[0][0] == down_ip  and neighbors[0][1] == down_port:
                not_neighbor = False
                
        if not_neighbor == True:
            print '>> %s:%d is not your neighbor, you can not destroy the link!'%(down_ip, down_port)
        else:
            # Send linkdown message to the neighbor of the link
            linkdown_message = '<linkdown>' + self.node_ip + ',' + str(self.node_port)
            self.neighbor_socket.sendto(linkdown_message, (down_ip, down_port))
            # Set the cost in the neighbor_list of the link to infinite
            for neighbors in self.neighbor_list:
                if neighbors[0][0] == down_ip  and neighbors[0][1] == down_port:
                    self.linkdown_neighbor.append([(down_ip,down_port),neighbors[1]])
                    neighbors[1] = INFINITE
                    # Stop the sending timer and death detecting timer of this neighbor
                    neighbors[3][0] = -1
                    neighbors[3][1] = -1
                    neighbors[4][0] = -1
                    neighbors[4][1] = -1
            # Set the cost of destinations in dv_list which next hops are the neighbor to infinite
            for dests in self.dv_list:
                if dests[2][0] == down_ip and dests[2][1] == down_port:
                    dests[1] = INFINITE        
            
    def node_linkup(self, up_ip, up_port):
        "To recover a destroyed link"
        
        original_cost = 0
        recovery_link = 0
        
        # Check if it is a destroyed link
        not_down = True
        for num in range(len(self.linkdown_neighbor)):
            if self.linkdown_neighbor[num][0][0] == up_ip and self.linkdown_neighbor[num][0][1] == up_port:
                original_cost = self.linkdown_neighbor[num][1]
                recovery_link = num
                not_down = False
        
        del self.linkdown_neighbor[recovery_link]
        
        if not_down == True:
            print '>> %s:%d is not a destroyed link!'%(up_ip, up_port)
        else:
            # Send linkup message to the neighbor of the link
            linkup_message = '<linkup>' + self.node_ip + ',' + str(self.node_port)
            self.neighbor_socket.sendto(linkup_message, (up_ip, up_port))
            # Recover the original link cost in the neighbor_list
            for neighbors in self.neighbor_list:
                if neighbors[0][0] == up_ip and neighbors[0][1] == up_port:
                    neighbors[1] = original_cost
                    # Restart the sending timer and death detecting timer of the neighbor
                    neighbors[3][0] = time.time()
                    neighbors[3][1] = time.time()
                    neighbors[4][0] = time.time()
                    neighbors[4][1] = time.time()
     
    def node_linkchange(self, change_ip, change_port, change_cost): 
        "To change a cost of a link"
        
        # Check if it is in the neighbor_list of the node
        not_neighbor = True
        for neighbors in self.neighbor_list:
            if neighbors[0][0] == change_ip  and neighbors[0][1] == change_port:
                not_neighbor = False
                
        if not_neighbor == True:
            print '>> %s:%d is not your neighbor, you can not change cost of the link!'%(change_ip, change_port)
        else:
            # Send linkchange message to the neighbor of the link
            linkchange_message = '<linkchange>' + self.node_ip + ',' + str(self.node_port) + ',' + str(change_cost)
            self.neighbor_socket.sendto(linkchange_message, (change_ip, change_port))
            # Set the cost in the neighbor_list of the link to new cost
            for neighbors in self.neighbor_list:
                if neighbors[0][0] == change_ip  and neighbors[0][1] == change_port:
                    
                    neighbors[1] = change_cost
                    
            # Set the cost of destinations in dv_list which next hops are the neighbor to infinite
            for dests in self.dv_list:
                if dests[2][0] == change_ip and dests[2][1] == change_port:
                    dests[1] = INFINITE 
        
                            
    def user_command(self):
        "User command interface"
        
        global CLOSE_INFORMING
        
        while NODE_SHUTDOWN == False:
            try:
                command = raw_input('Command>> ')
            except:
                thread.exit()
                
            if command == 'SHOWRT':
                self.display_table()
            elif command == 'SHOWNB':
                self.display_neighbor()
            elif command == 'CLOSE':
                self.node_close()
            elif command[0:8] == 'LINKDOWN':
                linkdown_ip = command[9:command.rfind(' ')]
                linkdown_port = int(command[command.rfind(' ')+1:])
                self.node_linkdown(linkdown_ip, linkdown_port)
            elif command[0:6] == 'LINKUP':
                linkup_ip = command[7:command.rfind(' ')]
                linkup_port = int(command[command.rfind(' ')+1:])
                self.node_linkup(linkup_ip, linkup_port)
            elif command == 'CLOSEMODE':
                close_mode_choice = raw_input('\r>> Should the node inform its neighbors when it is closed (y/n)? ')
                if close_mode_choice == 'y':
                    CLOSE_INFORMING = True
                    print '\r>> Now the node will inform its neighbors when it is closed'
                elif close_mode_choice == 'n':
                    CLOSE_INFORMING = False
                    print '\r>> Now the node will not inform its neighbors when it is closed'
                else:
                    print '\r>> I can not understand...'
            elif command[0:10] == 'LINKCHANGE':
                command = command.split(' ')
                link_neighbor_ip = command[1]
                link_neighbor_port = int(command[2])
                new_cost = float(command[3])
                self.node_linkchange(link_neighbor_ip, link_neighbor_port, new_cost)
            elif command == 'CHANGETIMEOUT':
                new_timeout = float(raw_input('\r>> Please enter the new timeout value: '))
                self.timeout = new_timeout
                print '>> Now the timeout value of the node is: %f s'%self.timeout
            elif command == 'HELP':
                print '=' * 100
                print 'COMMAND'.ljust(30), 'FUNCTIONALITY'
                print '-' * 100
                print 'SHOWRT'.ljust(30), 'Show the distance vector list of the node'
                print 'SHOWNB'.ljust(30), 'Show the neighbor information of the node'
                print 'CLOSE'.ljust(30), 'Close the node permanently'
                print 'LINKDOWN {ip port}'.ljust(30), 'Temporarily shut down a link between the node and specified neighbor'
                print 'LINKUP {ip port}'.ljust(30), 'Recover the shut down link between the node and specified neighbor'
                print 'LINKCHANGE {ip port cost}'.ljust(30), 'Change a link cost between the node and the specified neighbor'
                print 'CLOSEMODE'.ljust(30), 'Choose if the node should inform its neighbors when it is close'
                print 'CHANGETIMEOUT'.ljust(30), 'Change the timeout value of the node'
                print '=' * 100
            else:
                print 'We cannot understand your command. Please enter HELP for more information.'
        
        thread.exit()
    
    def timeout_sending(self, neighbor_num):
        "To send DV to all the neighbors when timeout happens"
        
        global CLOSE_NEIGHBOR
        
        # This iteration is under condition that the node is not closed and the neighbor this timer is counting is not closed
        while NODE_SHUTDOWN == False and CLOSE_NEIGHBOR != neighbor_num:
            try:
                # If the link is not down, update the stop time
                if self.neighbor_list[neighbor_num][3][1] != -1:
                    self.neighbor_list[neighbor_num][3][1] = time.time()
                # If the link is not down and time exceeds the timeout value, restart the timer and send DV to this neighbor
                if self.neighbor_list[neighbor_num][3][1] - self.neighbor_list[neighbor_num][3][0] >= self.timeout and self.neighbor_list[neighbor_num][3][0] != -1 and self.neighbor_list[neighbor_num][3][1] != -1:
                    self.neighbor_list[neighbor_num][3][0] = time.time()
                    self.dv_sending(neighbor_num)
            except IndexError:
                break
        
        # Recover the number of the closed neighbor in the neighbor_list
        CLOSE_NEIGHBOR = INFINITE
        
        thread.exit()
    
    def timeout_dead_detect(self, neighbor_nums):
        "To detect if a neighbor is dead"
        
        global CLOSE_NEIGHBOR
        
        # This iteration is under condition that the node is not closed and the neighbor this timer is counting is not closed
        while NODE_SHUTDOWN == False and CLOSE_NEIGHBOR != neighbor_nums:
            try:
                # If the link is not down, update the stop time
                if self.neighbor_list[neighbor_nums][4][1] != -1:
                    self.neighbor_list[neighbor_nums][4][1] = time.time()
                # If the link is not down and time exceeds the 3*timeout value, the neighbor is considered dead
                if self.neighbor_list[neighbor_nums][4][1] - self.neighbor_list[neighbor_nums][4][0] >= (3*self.timeout) and self.neighbor_list[neighbor_nums][4][0] != -1 and self.neighbor_list[neighbor_nums][4][1] != -1:
                    
                    close_neighbor_ip = self.neighbor_list[neighbor_nums][0][0]
                    close_neighbor_port = self.neighbor_list[neighbor_nums][0][1]
                
                    print '\r>> Do not receive UPDATE from %s:%d for 3* %f s, it is considered as dead.'%(close_neighbor_ip, close_neighbor_port, self.timeout)
                    print 'Command>> '
                    
                    # Delete the neighbor from the neighbor_list
                    CLOSE_NEIGHBOR = neighbor_nums
                    self.neighbor_num -= 1
                    del self.neighbor_list[neighbor_nums]
                
                    # Find the neighbor that is closed and delete it from the dv_list
                    for num in range(len(self.dv_list)):
                        if self.dv_list[num][0][0] == close_neighbor_ip and self.dv_list[num][0][1] == close_neighbor_port:
                            close_neighbor = num
                    del self.dv_list[close_neighbor]
                
                    # Change the cost of destinations in the dv_list which are with the closed neighbor as the next hop to infinite
                    for dests in self.dv_list:
                        if dests[2][0] == close_neighbor_ip and dests[2][1] == close_neighbor_port:
                            dests[1] = INFINITE 
                    
                    # Send updated DV to all the neighbors
                    for num in range(self.neighbor_num):
                        self.dv_sending(num)   
                        # restart the sending timer if the link is not down (start_time != -1)
                        if self.neighbor_list[num][3][0] != -1:
                            self.neighbor_list[num][3][0] = time.time() 
            except IndexError:
                pass
        
        # Recover the number of the closed neighbor in the neighbor_list
        CLOSE_NEIGHBOR = INFINITE
        
        thread.exit()
        
#-----------------------Functions----------------------
#------------------Entry of the program----------------

if __name__ == '__main__':
    # Get orininal inputs from the command line
    if ((len(sys.argv) - 3) % 3) != 0 or len(sys.argv) == 2:
        print '>> Please follow the format to invoke the program:'
        print '>> python DVclient.py <localport> <timeout> [ipadress1, port1, weight1...]'
        sys.exit()
    HOST = socket.gethostbyname(socket.gethostname())
    try:
        PORT = int(sys.argv[1])
    except ValueError:
        print '>> <localport> should be an integral number'
        sys.exit()
    TIMEOUT = float(sys.argv[2])
    NEIGHBOR_NUM = (len(sys.argv) - 2) / 3
    DV_LIST.append([(HOST, PORT), float(0), (HOST, PORT)])
    for num in range(NEIGHBOR_NUM):
        NEIGHBOR_LIST.append([(sys.argv[num * 3 + 3], int(sys.argv[num * 3 + 4])), float(sys.argv[num * 3 + 5]), [], [time.time(), 0], [time.time(), 0]])
        DV_LIST.append([(sys.argv[num * 3 + 3], int(sys.argv[num * 3 + 4])), float(sys.argv[num * 3 + 5]), [sys.argv[num * 3 + 3], int(sys.argv[num * 3 + 4])]])
    
    
    # Initialize a Node class object
    CurrentNode = Node(HOST, PORT, NEIGHBOR_NUM, NEIGHBOR_LIST, DV_LIST, TIMEOUT)
    # Initialize the listening socket of the node and the socket for sending data to neighbors
    CurrentNode.init_listen_socket()
    CurrentNode.init_neighbor_socket()
    # Display original setting of the node
    CurrentNode.init_display()
    
    # Thread for receiving data from the neighbors
    new_thread = Thread(target = CurrentNode.dv_receiving, args = ())
    new_thread.setDaemon(True)
    new_thread.start()
    
    # Thread for user command interface
    new_thread = Thread(target = CurrentNode.user_command, args = ())
    new_thread.setDaemon(True)
    new_thread.start()
    
    # For each neighbor of the node, there are two timer threads for sending timeout and death detection timeout
    for neighbor_nums in range(CurrentNode.neighbor_num):
        new_thread = Thread(target = CurrentNode.timeout_sending, args = (neighbor_nums,))
        new_thread.setDaemon(True)
        new_thread.start()
        
        new_thread = Thread(target = CurrentNode.timeout_dead_detect, args = (neighbor_nums,))
        new_thread.setDaemon(True)
        new_thread.start()
        
    while NODE_SHUTDOWN == False:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            print 'Node closed by \'Cltrl + C\'. '
            CurrentNode.node_close()
            sys.exit()
        
    sys.exit()
