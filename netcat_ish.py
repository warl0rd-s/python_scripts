import sys
import socket
import getopt
import threading
import subprocess

#defining global variables for use
listen                  = False
command                 = False
upload                  = False
execute                 = ""
target                  = ""
upload_destination      = ""
port                    = 0  

def usage():
    print ("""\
        [...]Netcat-ish @Tony Tools[...]
        Usage: netcat-ish.py -t target -p  port
        -l --listen                 - listen on [host]:[port] for incoming connection
        -e --execute=file_to_run    - execute the given file upon connection
        -c --command                - init a command shell
        -u --upload=destination     - upon connection, upload a file & write to [dest]
        Examples:[-->]")

        netcat-ish.py -t 192.168.142.100 -p 4545 -l -c:
        netcat-ish.py -l -t 192.167.100.1 -p 444 -u=c:\\target.exe
        netcat-ish.py =t 198.192.100.14 -p 447 -l -e 
        echo 'ABCDEFGHI' | python netcat-ish.py -t 192.168.11.14 -p 135""")

    sys.exit(0)


def client_sender(buffer):
    
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        #connect to target host
        client.connect((target,port))

        if len(buffer):
            client.send(buffer)

        while True:
            #now wait for data
            recv_len = 1
            response = ""

            while recv_len:
                data     = client.recv(4096)
                recv_len = len(data)
                response += data

                if recv_len < 4096:
                    break

            print response,

            #wait for more input
            buffer = raw_input("")
            buffer += "\n"

            #send the data off
            client.send(buffer)


    except:
        print("[*] Exception! Terminanting in 3...2...1...\n[-->[*/*|terminated|*\*]<--]")
        #tear down the connection
        client.close()


def server_loop():
    global target
    #if there is no target defined, we fall back to listen on all interfaces

    if not len(target):
        target = "0.0.0.0"

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target,port))
    server.listen(5)

    while True:
        client_socket, addr = server.accept()

        #a thread to handle our new client
        client_thread = threading.Thread(target=client_handler, args=(client_socket,))
        client_thread.start()


def run_command(command):
    command = command.rstrip()

    #run the command and get the output back
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
    except:
        output = "[*] Failed to execute command. :( \r\n"

    #send output to client
    return output


def client_handler(client_socket):
    global upload
    global execute
    global command

    #check for upload
    if len(upload_destination):
        #read all of the bytes and write to dest
        file_buffer = ""

        #keep reading data till completion
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            else:
                file_buffer += data

        #now we take bytes and write out
        try:
            file_descriptor = open(upload_destination, "wb")
            file_descriptor.write(file_buffer)
            file_descriptor.close()

            #acknowledge file written out
            client_socket.send("[-->Success!!<--] File saved to %s\r\n" % upload_destination)
        except:
            client_socket.send("]>--Failed!!--<[ File was not saved to %s \r\n" % upload_destination)

    #check for command execution
    if len(execute):
        #run command
        output = run_command(execute)

        client_socket.send(output)

    #now another loop if command shell is requested
    if command:
        while True:
            #display a prompt
            client_socket.send("-->[..]Netcat-ish @Tony Tool:#> ")
            cmd_buffer = ""
            while "\n" not in cmd_buffer:
                cmd_buffer += client_socket.recv(1024)

            #send back command output
            response = run_command(cmd_buffer)

            #send back response
            client_socket.send(response)



def main():
    global listen
    global port
    global execute
    global command
    global upload_destination
    global target

    if not len(sys.argv[1:]):
        usage()

    #read the command line options
    try:
        opts, args = getopt.getopt(sys.argv[1:],"hle:t:p:cu:",["help","listen","execute","target","port","command","upload"])
    except getopt.GetoptError as err:
        print(str(err))
        usage()


    for o,a in opts:
        if o in ("-h", "--help"):
            usage()
        elif o in ("-l", "--listen"):
            listen = True
        elif o in ("-e", "--execute"):
            execute = a
        elif o in ("-c", "--commandshell"):
            command = True
        elif o in ("-u", "--upload"):
            upload_destination = a
        elif o in ("-t", "--target"):
            target = a
        elif o in ("-p", "--port"):
            port = int(a)
        else:
            assert False, "Unhandled Option"


    #either we listen or send data from stdin
    if not listen and len(target) and port > 0:
        #read in buffer from cmd line
        #this will block, so use CTRL+D if not sending input to stdin
        buffer =sys.stdin.read()

        #send data off
        client_sender(buffer)

    #now to listen and hopefully upload things
    #possibly drop a shell, and or execute commands

    if listen:
        server_loop()

main()



