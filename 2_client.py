#import the packages we need
import rpyc,sys,socket

#Function used to check the command line arguments
def check_input(temp):
    #ip list
    ippys = []
    #port list
    ports = []
    #splicing the hosts from the input.
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
    #splicing the ports from the input.
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
    #return the ips and ports
    return ippys,ports

#The main client call
if __name__ == "__main__":
    """
    Run this to run the client
    python3 client.py -hosts 127.0.0.1,127.0.0.2,127.0.0.3,127.0.0.4,127.0.0.5 -ports 5001,5002,5003,5004,5005
    """
    #First we take in the command line arguments
    temp       = sys.argv
    #We either get the id and port provided or go with the default values
    ippys,ports= check_input(temp)
    #Client's initial knowledge
    vc            = [0,0,0,0,0,0,0,0,0,0]
    data          = {1:"",2:"",3:"",4:"",5:"",6:"",7:"",8:"",9:"",10:""}
    #main client loop
    text = 0
    while text != "stop":
        #select a server to connect to
        print("\n"+"Current local data,    {}".format(data))
        print("Current version clock, {}".format(vc))
        print("Known Servers, {}".format(ports)+"\n")
        text = input("Which Server would you like to connect to(Please type the number)? Else type stop. "+"\n")
        #if stop we quit else continue
        if text != "stop":
            try:
                text = int(text)
            except:
                print("Error in selection, please try again.")
                continue
            if (str(text) in ports) == False:
                print("Error in server name, please try again.")
                continue
            else:
                try:
                    ind = ports.index(str(text))
                    i = ippys[ind]
                    p = text
                    #Start the connection
                    server = rpyc.connect(i,p)                    
                    texty = input("Please select from, <0:edit an entry> <1:read an entry> <2:Leave server>"+"\n")
                    while texty != 2:
                        #edit,read or quit
                        while (int(texty) in [0,1,2]) ==False:
                            print("\n"+"Current local data,    {}".format(data))
                            print("Current version clock, {}".format(vc))
                            texty = input("Please select from, <0:edit an entry> <1:read an entry> <2:Leave server>"+"\n")
                        texty = int(texty)
                        #quitting
                        if texty == 2:
                            print("\n"+"Closing server connection")
                            server.close()
                            #server = []
                            break
                        #editing a value
                        elif texty == 0:
                            print("Current version clock, {}".format(vc))
                            key = input("which entry do you wish to edit?(1-10) "+"\n")
                            value = input("What text do you wish to add? "+"\n")
                            key = int(key)                   
                            #send the update and get back only the vector clock         
                            try:
                                vc[key-1] = server.root.add_update(key,value)                                
                                print("Update request sent" + "\n")
                            except:
                                print("Update request failed, server issues?"+ "\n")
                            #tell the connected server to propagate the data rpc style.
                            try:                                
                                propagate = rpyc.async_(server.root.propagate)
                                propagate()
                            except:
                                print("Propogate failed")
                        #reading a value
                        elif texty == 1:
                            print("\n"+"Current local data,    {}".format(data))
                            key = input("which entry do you wish to read?(1-10) "+"\n")
                            key = int(key)
                            #read in the data
                            try:
                                answer,vect,conflict = server.root.read(key)
                                print("Read request sent"+"\n")
                                #conflicted data detection
                                if conflict == False:
                                    print("Key {} has the value {}".format(key,answer))
                                    data[key] = answer
                                    vc[key-1] = vect
                                else:
                                    print("unfortunately this value was conflicted.")
                                    print("Conflicted vector==>> {}".format(vect))
                                    print("Conflicted Data  ==>> {}".format(data))                                    
                            except:
                                print("Read request failed, server issues?"+"\n")      
                        #reset the selection option
                        texty = -1          
                except:
                    print("\n"+"It seems that the server may be offline."+"\n")
                    continue
            