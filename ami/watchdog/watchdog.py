from mcstatus import MinecraftServer
import socket
import subprocess
import time
import xmlrpc.client

server_last_online = time.time()
server_last_occupied = time.time()

server = MinecraftServer('localhost', 25565)

def get_number_of_players():
    try:
        status = server.status(retries=2)
        return status.players.online
    except:
        print("Server is not online")
        return None


def status_check():
    global server_last_online, server_last_occupied
    players = get_number_of_players()
    if players is None:
        # don't change either timestamp
        return
    print("%d players on server" % (players,))
    if players > 0:
        server_last_online = time.time()
        server_last_occupied = time.time()
    else: # players == 0:
        server_last_online = time.time()
        # don't change server_last_occupied


def check_shutdown():
    """If server is due to shutdown, then return True"""
    now = time.time()
    # if server hasn't been online for an hour, it probably crashed
    if now - server_last_online > 3600:
        return True
    # separate checks so that we can set different timeouts for occupied vs online
    if now - server_last_occupied > 3600:
        return True
    return False


def check_termination_notice():
    """Checks the EC2 instance metadata to see if this spot instance is due
    to be terminated. Returns True if it is, False if there is no termination
    notice."""
    import urllib.request
    # if this request returns a 404, then the instance is not scheduled to terminate
    try:
        urllib.request.urlopen('http://169.254.169.254/latest/meta-data/spot/termination-time', timeout=2)
        return True
    except urllib.error.URLError as e:
        print(e)
        print("Could not get instance metadata. Are we in EC2??")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False
        else:
            raise


def shutdown(msg="Minecraft server shutting down!"):
    # schedule poweroff for 1 minute from now
    try:
        s = xmlrpc.client.ServerProxy('http://localhost:25560')
        s.run_command("/say %s" % (msg,))
        time.sleep(5)
        s.run_command("/save-off")
        s.run_command("/save-all")
        s.run_command("/stop")
    except Exception as e:
        print(e)
        print("Continuing with shutdown despite error...")
    time.sleep(15)
    subprocess.run('sudo shutdown -P', shell=True)


def main():
    while True:
        try:
            status_check()
        except Exception as e:
            print("Got exception in status_check:")
            print(e)
        if check_shutdown():
            shutdown()
            print("Good-bye")
            break
        if check_termination_notice():
            shutdown(msg="Spot instance termination notice received!")
            print("Good-bye")
            break
        time.sleep(20)

if __name__ == "__main__":
    main()
