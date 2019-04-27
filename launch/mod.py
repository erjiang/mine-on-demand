import json
import os
import socket
from functools import wraps

from flask import Flask, jsonify, request, Response, abort
from google.oauth2 import id_token
from google.auth.transport import requests
from mcstatus import MinecraftServer

from launch import launch_minecraft_server

app = Flask(__name__)

SERVER_IP = os.environ['SERVER_IP']
USER_WHITELIST = json.loads(os.environ['USER_WHITELIST'])
CLIENT_ID = os.environ['GOOGLE_CLIENT_ID']


def auth_required(func):
    @wraps(func)
    def with_auth_required(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            abort(401)
        token = auth_header[7:]
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), CLIENT_ID)
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
        if "email" not in idinfo:
            abort(401)
        if idinfo['email_verified'] != "true":
            print("Email is not verified. Not accepting it.")
            abort(403)

        if idinfo['email'] not in USER_WHITELIST:
            print("Email %s is not in whitelist" % (idinfo['email'],))
            abort(403)

        return func(*args, **kwargs)
    return with_auth_required


@app.route("/")
def homepage():
    return app.send_static_file('static/index.html')

@app.route("/<path:filename>")
def static_get(filename):
    return send_from_directory('static', filename)

@app.route("/serverstatus.json")
@auth_required
def get_server_status():
    server = MinecraftServer(SERVER_IP, 25565)
    try:
        status = server.status(retries=2)
        is_online = True
        players = status.players.online
        version = status.version.name
    except (ConnectionRefusedError, socket.timeout):
        is_online = False
        players = 0
        version = None
    return jsonify(
        online=is_online,
        players=players,
        version=version
    )

@app.route("/start_server", methods=['POST'])
@auth_required
def start_server():
    return Response(launch_minecraft_server(), mimetype='text/plain')
