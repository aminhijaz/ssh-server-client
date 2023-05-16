import paramiko
import sys
import time
def main():
    s = paramiko.SSHClient()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    args = sys.argv[1:]
    s.connect(args[0], username=args[2], password=args[3], port=args[1])
    channel = s.invoke_shell()
    channel.setblocking(1)
    out = channel.recv(9999).decode(encoding='utf-8')
    print(out)
    while(True):
        while(not(channel.recv_ready)):
            time.sleep(3)
        command = input() +"\n"
        if(command == "bye"):
            s.close()
            break
        channel.send(command)
        out = channel.recv(1000).decode(encoding='utf-8')
        while(not(channel.recv_ready)):
            time.sleep(3)

        print(out)
    return 0
main()
exit()