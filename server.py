#Import all the packages we need
import rpyc, sys, socket,time,math
from rpyc.utils.server import ThreadedServer

#The threaded server class
class MyService(rpyc.Service):
    #constructor for the server class
    def __init__(self,ippys,ip_names,ip,port,test,v,d,initial_election):
        #test is used for simulating the server being offline, lest we continue with the base data
        if test == True:
            #we must deep copy in the version vector
            temp = []
            for i in v:
                temp.append(i)
            self.vector = temp
            #we must deep copy in the data dictionary
            temp2 = {}
            for i in d:
                temp2[i] = d[i]
            self.data   = temp2
        else:
            #normal baseline data and version vectors each server starts with
            self.vector               = [0,0,0,0,0,0,0,0,0,0]
            self.data                 = {1:"Alpha",2:"Bravo",3:"Charlie",4:"Delta",5:"Echo",6:"Golf",7:"Apples",8:"pepsi",9:"Baker",10:"Foxy"}
        #This is used to keep track of conflicted data
        self.conflicted_check     = [0,0,0,0,0,0,0,0,0,0]
        self.conflicted_vector    = [0,0,0,0,0,0,0,0,0,0]
        self.conflicted_values    = {1:"",2:"",3:"",4:"",5:"",6:"",7:"",8:"",9:"",10:""}
        #this is used to keep track of the created server's properties and the other 4 it needs to know of.
        self.servers              = ip_names
        self.server_ports         = {1:5001,2:5002,3:5003,4:5004,5:5005}
        self.ippys                = ippys
        self.ip                   = ip
        self.port                 = port
        self.server_names         = {5001:1,5002:2,5003:3,5004:4,5005:5}
        self.server_ids           = [1,2,3,4,5]
        self.id                   = self.server_names[self.port]
        self.name                 = "Server: {}".format(self.id) 
        self.isleader             = False
        self.leader               = 0
        self.start_election       = initial_election
        self.nodes                = int(len(self.server_ports))
        self.nodes_w              = int(math.ceil((self.nodes/2)+1))
        self.election_voted       = False
        if self.nodes_w == self.nodes:
            self.nodes_w += -1
        self.nodes_r              = 0
        while (self.nodes_r + self.nodes_w) <= self.nodes:
            self.nodes_r+=1
        #This server declares it is alive
        print("{}, {} is online!!!".format(self.name,self.ip))
        #first check if we should initiate the leader selection
        if self.start_election == True:
            self.exposed_begin_election()


    def exposed_begin_election(self):
        if self.election_voted == False:
            #Go through our connections list
            visted =[]
            msgs   =[0,0,0,0,0]
            for i in range(1,6):
                if i <= self.id:
                    msgs[i-1] = -1
            for i in range(1,6):
                #We don't contact ourselves
                if self.servers[i] == self.ip:
                    continue
                elif i <= self.id:
                    continue
                #we don't contact the same server twice
                elif i in visted:
                    continue
                try:
                    #set up the connection and send the assumed new data
                    s = rpyc.connect(self.servers[i],self.server_ports[i])
                    print("I, {} sent election to {}".format(self.name,i))
                    msgs[i-1] = s.root.election_college(self.id)
                    visted.append(i)
                    s.close()
                except:
                    print("Error, I, {} can't connect to Server {}".format(self.name,i))
                    msgs[i-1] = -1
                    continue
            while 0 in msgs:
                time.sleep(.1)
            self.election_voted = True
            if True in msgs:
                print("I, Server {}, Lost election".format(self.id))
                #loop through and make the others do theres
                visted =[]
                for i in range(1,6):
                    #We don't contact ourselves
                    if self.servers[i] == self.ip:
                        continue
                    elif i <= self.id:
                        continue
                    #we don't contact the same server twice
                    elif i in visted:
                        continue
                    try:
                        #set up the connection and send the assumed new data
                        s = rpyc.connect(self.servers[i],self.server_ports[i])
                        ss = rpyc.async_(s.root.begin_election)
                        ss()
                        visted.append(i)
                        s.close()
                    except:
                        continue
                print("I, Server {}, retired".format(self.id))
            else:
                print("I, Server {}, Won election".format(self.id))
                visted =[]
                for i in range(1,6):
                    #We don't contact ourselves
                    if i == self.id:
                        continue
                    #we don't contact the same server twice
                    elif i in visted:
                        continue
                    try:
                        #set up the connection and send the assumed new data
                        s = rpyc.connect(self.servers[i],self.server_ports[i])
                        s.root.set_leader(self.id)
                        visted.append(i)
                        s.close()
                    except:
                        continue
            print("")
            
    def exposed_set_leader(self,leader):
        self.leader = leader
        print("I, Server {}, Submit to Leader {}".format(self.id,leader))


    def exposed_election_college(self,received_id):
        #return True for okay
        if received_id < self.id:
            x=True
        else:
            x=False
        #try:
        return x
        #finally:
            #self.exposed_begin_election()



    #exposed read function used by the clients to read data values
    def exposed_read(self,key):
        #initially no conflict is detected
        conflict = False
        #check if we have a conflicted key
        if(self.conflicted_check[key-1] == 1):
            #we do
            conflict=True
            #return the conflicted data values, version vector and conflict set to True
            return self.conflicted_values[key],self.conflicted_vector[key-1],conflict
        #we dont
        else:
            #return the non conflicted boolean, data values and version vector
            return self.data[key],self.vector[key-1],conflict

    #exposed add function used by the clients to update data and version values
    def exposed_add_update(self,key, value):
        #update the key-value
        self.data[key] = "{},{},".format(self.data[key],value)
        #update the clock
        self.vector[key-1] += 1
        #return the updated version vector
        return self.vector[key-1]

    #exposed function used by other servers for data sharing
    def exposed_reciprocate(self,vect,data):
        #booleans for vector decisions
        conflict   = False
        concurrent = False
        dom        = False
        sub        = False
        #local and imported vector copies
        a = self.vector
        b = vect
        #Truth lists to determine the logic vector situation
        c1 = []
        c2 = []
        c3 = []
        c4 = []
        #populate the truth lists
        for i in range(10):
            if a[i] > b[i]:
                c1.append(True)
            else: 
                c1.append(False)
            if a[i] >= b[i]:
                c2.append(True)
            else: 
                c2.append(False)
            if b[i] > a[i]:
                c3.append(True)
            else: 
                c3.append(False)
            if b[i] >=a[i]:
                c4.append(True)
            else: 
                c4.append(False)
        #Does the local vector dominate the imported one
        if (True in c1):
            if (False in c2) == False:
                dom = True
        #Does the imported vector dominate the local one
        elif(True in c3):
            if (False in c4) == False:
                sub = True
        #Are the vectors the same
        elif(a == b):
            concurrent = True
        #if nothing is true then we are conflicted
        if (True in [dom,sub,concurrent]) ==False:
            conflict = True
        #If the imported vector dominates the local one
        if sub == True:
            #deep copy the imported vector to the local one
            temp = []
            for i in vect:
                temp.append(i)
            self.vector = temp
            #deep copy the imported dictionary to the local one
            temp2 = {}
            for i in data:
                temp2[i] = data[i]
            self.data   = temp2
        #if we are conflicted
        elif conflict == True:
            #first we create copies of vectors and data to avoid connection blocking
            temp = []
            for i in vect:
                temp.append(i)
            temp2 = {}
            for i in data:
                temp2[i] = data[i]
            #The local server logs all conflicted values and version vectors
            for i in range(10):
                if temp[i] != self.vector[i]:
                    self.conflicted_check[i] = 1
                    self.conflicted_vector[i]= [temp[i],self.vector[i]]
                    self.conflicted_values[i]= [temp2[i],self.data[i]]

    #exposed function used by the client send data propagation signal
    def exposed_propagate(self):
        #Go through our connections list
        visted =[]
        for i in range(1,6):
            #We don't contact ourselves
            if self.servers[i] == self.ip:
                continue
            #we don't contact the same server twice
            elif i in visted:
                continue
            try:
                #set up the connection and send the assumed new data
                s = rpyc.connect(self.servers[i],self.server_ports[i])
                a = self.vector.copy()
                b = self.data.copy()
                s.root.reciprocate(a,b)
                print("I, {} sent the update to {}".format(self.name,i))
                visted.append(i)
                s.close()
            except:
                print("Error, I, {} can't connect to Server {}".format(self.name,i))
                continue
        print("")


#Function used to check the command line arguments
def check_input(temp):
    #replica amount
    rep  = 0
    #ip address 
    ippys = []
    #ports
    ports = []

    #splice our local ip to be used
    if '-host' in temp:
        t_index = temp.index('-host') + 1
        ippy  = temp[t_index]
        try:
            socket.inet_aton(ippy)
            ippys.append(ippy)
        except:
            print("Can't connect to,  "+ippy+"\n")
            sys.exit()
    else:
        print("ERROR: No host given. "+"\n")
        sys.exit()

    #splice our local port to be used
    if '-port' in temp:
        t_index = temp.index('-port') + 1
        try:
            porty = temp[t_index]
            porty = int(porty)
            if porty < 2000:
                print("ERROR: IVALID PORT, "+porty+"\n")
                sys.exit()
            else:
                ports.append(porty)
        except:
                print("ERROR: IVALID PORT, "+porty+"\n")
                sys.exit()
    else:
        print("ERROR: No port given. "+"\n")
        sys.exit()

    #splice the amount of replicas
    if '-n' in temp:
        t_index = temp.index('-n') + 1
        try:
            replicas = temp[t_index]
            replicas = int(replicas)
            if replicas < 0:
                print("ERROR: IVALID replica amount, "+replicas+"\n")
                sys.exit()
            else:
                rep = replicas
        except:
                print("ERROR: IVALID replica amount, "+replicas+"\n")
                sys.exit()
    else:
        print("ERROR: No replica amount given, "+"\n")
        sys.exit()

    #splice the other server hosts used for connections
    if '-hosts' in temp:
        t_index = temp.index('-hosts') + 1
        try:            
            hosts = temp[t_index]
            if ',' in hosts:
                tempy = hosts.split(',')
                for i in tempy:
                    if i != '':
                        ippys.append(i)
                try:
                    for i in ippys:
                        socket.inet_aton(i)
                except:
                    print("ERROR: Please check hosts,  {}"+"\n".format(hosts))
                    sys.exit()
        except:
            print("ERROR: Please check hosts,  {}"+"\n".format(hosts))
            sys.exit()
    else:
        print("ERROR: No hosts given. "+"\n")
        sys.exit()

    #splice the other ports used for connections
    if '-ports' in temp:
        t_index = temp.index('-ports') + 1
        try:            
            porty = temp[t_index]
            if ',' in porty:
                tempy = porty.split(',')
                for i in tempy:
                    if i != '':
                        a = int(i)
                        if a < 2000:
                            print("ERROR: IVALID PORT, "+a+"\n")
                            sys.exit()
                        else:
                            ports.append(i)
        except:
            print("ERROR: Please check ports,  {}"+"\n".format(tempy))
            sys.exit()
    else:
        print("ERROR: No port given. "+"\n")
        sys.exit()

    #return the replica amount, ip address list and port lists
    return rep,ippys,ports

#The main server call
if __name__ == "__main__":
    """
    Run this to run the server
    python3 server.py -host 127.0.0.1 -port 5001 -n 5 -hosts 127.0.0.2,127.0.0.3,127.0.0.4,127.0.0.5 -ports 5002,5003,5004,5005
    """
    #First we take in the command line arguments
    temp       = sys.argv
    #We either get the id and port provided or go with the default values
    rep,ippys,ports= check_input(temp)
    #seperate the results
    ipp = ippys.copy()
    ip_names = {1:ipp[0],2:ipp[1],3:ipp[2],4:ipp[3],5:ipp[4]}


    #starting Server one
    ip   = "127.0.0.1"
    port = 5001
    server1 = ThreadedServer(MyService(ippys,ip_names,ip,port,False,0,0,False), port = port,hostname=ip)
    server1._start_in_thread()
    #starting Server two
    ip   = "127.0.0.2"
    port = 5002
    server2 = ThreadedServer(MyService(ippys,ip_names,ip,port,False,0,0,False), port = port,hostname=ip)
    server2._start_in_thread()
    #starting Server three
    ip   = "127.0.0.3"
    port = 5003
    server3 = ThreadedServer(MyService(ippys,ip_names,ip,port,False,0,0,False), port = port,hostname=ip)
    server3._start_in_thread()
    #starting Server four
    ip   = "127.0.0.4"
    port = 5004
    server4 = ThreadedServer(MyService(ippys,ip_names,ip,port,False,0,0,False), port = port,hostname=ip)
    server4._start_in_thread()
    #starting Server five
    ip   = "127.0.0.5"
    port = 5005
    server5 = ThreadedServer(MyService(ippys,ip_names,ip,port,False,0,0,False), port = port,hostname=ip)
    server5._start_in_thread()




    ip   = "127.0.0.4"
    port = 5004
    s = rpyc.connect(ip,port)
    s.root.begin_election()
    s.close()

    #dont kill the servers
    while True:
        time.sleep(10)

  