from mcstatus import MinecraftServer
import subprocess
import time

server_last_online = time.time()
server_last_occupied = time.time()

def get_number_of_players():
    server = MinecraftServer('localhost', 25565)
    try:
        status = server.status(retries=2)
        return status.players.online
    except:
        print("Server is not online")
        return None

def status_check():
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

def shutdown():
    # schedule poweroff for 1 minute from now
    subprocess.run('sudo shutdown -P', shell=True)

def main():
    while True:
        status_check()
        if check_shutdown():
            shutdown()
            print("Good-bye")
            break
        time.sleep(20)

if __name__ == "__main__":
    main()
