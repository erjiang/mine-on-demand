from flask import Flask
from mcstatus import MinecraftServer

app = Flask(__name__)

SERVER_IP = os.environ['SERVER_IP']

@app.route("/")
def homepage():
    return app.send_static_file('static/index.html')


@app.route("/serverstatus.json")
def get_server_status():
    server = MinecraftServer(SERVER_IP, 25565)
    try:
        status = server.status(retries=2)
        is_online = True
        players = status.players.online
        version = status.software.version
    except:
        is_online = False
        players = 0
        version = None
    return jsonify(
        online=is_online,
        players=players,
        version=version
    )
