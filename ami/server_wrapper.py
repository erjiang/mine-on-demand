import json
import subprocess
import urllib.request
from xmlrpc.server import SimpleXMLRPCServer

# This should be run in the /home/ubuntu directory

SERVER_FLAGS = [
    "-XX:+UseConcMarkSweepGC",
    # next 2 options removed in later versions of openjdk
    #"-XX:+UseParNewGC",
    #"-XX:+CMSIncrementalPacing",
    "-XX:ParallelGCThreads=2",
    "-XX:+AggressiveOpts",
]

SERVER_JAR_PATH = "/home/ubuntu/server.jar"

minecraft_server = None


def download_json(url):
    with urllib.request.urlopen(url) as json_feed:
        return json.loads(json_feed.read().decode())


def download_latest_server(out_path):
    """Given an output path "out_path", download the latest Minecraft server
    JAR and save it to out_path. Note that out_path needs to be the full path
    and filename, e.g. "/tmp/minecraft_server.jar"."""
    mc_versions = download_json("https://launchermeta.mojang.com/mc/game/version_manifest.json")
    # This assumes the versions are listed from newest to oldest. If this is
    # not the case, then we need to use mc_versions['latest'] instead.
    latest_release = next((ver for ver in mc_versions['versions'] if ver['type'] == 'release'), None)
    latest_metadata = download_json(latest_release['url'])
    jar_url = latest_metadata['downloads']['server']['url']
    with urllib.request.urlopen(jar_url) as server_jar_req:
        with open(out_path, 'wb') as out_handle:
            out_handle.write(server_jar_req.read())
    return True


def run_command(cmd):
    """Takes a Minecraft server command as a string (without trailing
    newline) and send it to the Minecraft server process."""
    if minecraft_server is None:
        return "No server proc available. Is server running?"

    minecraft_server.stdin.write((cmd + "\n").encode("utf-8"))
    return "Success"


def run_minecraft(server_jar_path):
    global minecraft_server
    minecraft_server = subprocess.Popen(
        ["java", "-Xms1024M", "-Xmx3000M"] + SERVER_FLAGS + ["-jar", server_jar_path, "nogui"],
        stdin=subprocess.PIPE
    )


def main():
    download_latest_server(SERVER_JAR_PATH)
    run_minecraft(SERVER_JAR_PATH)

    # Allow other processes on this machine to send commands to the Minecraft
    # server via XMLRPC. The automatic shutdown uses this to tell players on
    # the server, for example.
    with SimpleXMLRPCServer(("localhost", 25560)) as server:
        server.register_function(run_command)
        server.serve_forever()


if __name__ == "__main__":
    main()
