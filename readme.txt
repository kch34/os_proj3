The two test docker images must be pulled are 
 
kch34/dist_os_2:test_a

kch34/dist_os_2:test_b

*******Please use docker run -it ****************

Otherwise the only dependency is rpyc if you wish to run this locally outside of the two automatic test suites, though I know it only works on linux

If you do wish to run the server spawner and client locally through two terminals then run the following in the same directory

terminal one  --> python3 server.py -host 127.0.0.1 -port 5001 -n 5 -hosts 127.0.0.2,127.0.0.3,127.0.0.4,127.0.0.5 -ports 5002,5003,5004,5005

Terminal two --> python3 client.py -hosts 127.0.0.1,127.0.0.2,127.0.0.3,127.0.0.4,127.0.0.5 -ports 5001,5002,5003,5004,5005

After this feel free to mess around with terminal two.
