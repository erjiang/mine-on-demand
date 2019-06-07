import subprocess
from xmlrpc.server import SimpleXMLRPCServer

# This should be run in the /home/ubuntu directory


minecraft_server = None


def run_command(cmd):
    """Takes a Minecraft server command as a string (without trailing
    newline) and send it to the Minecraft server process."""
    if minecraft_server is None:
        return "No server proc available. Is server running?"

    minecraft_server.stdin.write((cmd + "\n").encode("utf-8"))
    return "Success"


def run_minecraft():
    global minecraft_server
    minecraft_server = subprocess.Popen(
        ["java", "-Xms1024M", "-Xmx2536M", "-jar", "/home/ubuntu/server.jar"],
        stdin=subprocess.PIPE
    )


def main():
    run_minecraft()

    with SimpleXMLRPCServer(("localhost", 25560)) as server:
        server.register_function(run_command)
        server.serve_forever()


if __name__ == "__main__":
    main()