import csv
import json
import os
import socket
import time
from functools import wraps

from flask import Flask, jsonify, request, Response, abort, send_from_directory
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
from mcstatus import MinecraftServer
import requests

from launch import launch_minecraft_server, get_public_ip_address_of_server, notify_sns

app = Flask(__name__, static_url_path='')

SERVER_IP = os.environ['SERVER_IP']
CLIENT_ID = os.environ['GOOGLE_CLIENT_ID']

CACHED_ACCESS_LIST = None
CACHED_ACCESS_LIST_TIMESTAMP = 0
CACHE_DURATION = 60


def get_user_whitelist():
    """Returns a set or list containing email addresses that should be allowed
    to access this site."""
    if os.getenv('USER_WHITELIST_CSV_URL'):
        return get_access_csv(os.getenv('USER_WHITELIST_CSV_URL'))
    else:
        return json.loads(os.environ['USER_WHITELIST'])


def get_access_csv(csv_url):
    global CACHED_ACCESS_LIST, CACHED_ACCESS_LIST_TIMESTAMP
    if time.time() - CACHED_ACCESS_LIST_TIMESTAMP < CACHE_DURATION:
        return CACHED_ACCESS_LIST

    raw_csv = requests.get(csv_url)
    reader = csv.reader(raw_csv.text.splitlines())
    # skip first line of headers
    # first column is email addresses
    allowed_accounts = set([r[0] for r in reader][1:])
    CACHED_ACCESS_LIST = allowed_accounts
    CACHED_ACCESS_LIST_TIMESTAMP = time.time()
    return allowed_accounts


def auth_required(func):
    @wraps(func)
    def with_auth_required(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            abort(401)
        token = auth_header[7:]
        idinfo = id_token.verify_oauth2_token(token, grequests.Request(), CLIENT_ID)
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
        if "email" not in idinfo:
            abort(401)
        if not idinfo['email_verified']:
            print("Email is not verified. Not accepting it.")
            abort(403)

        if idinfo['email'] not in get_user_whitelist():
            print("Email %s is not in whitelist" % (idinfo['email'],))
            abort(403)

        return func(*args, user=idinfo['email'], **kwargs)
    return with_auth_required


@app.route("/")
def homepage():
    return app.send_static_file('index.html')

@app.route("/<path:filename>")
def static_get(filename):
    return send_from_directory('static', filename)

@app.route("/dev/<path:filename>")
def static_get_hack(filename):
    return send_from_directory('static', filename)

@app.route("/serverstatus.json")
@auth_required
def get_server_status(user=None):
    # Since lambda doesn't support ipv6, we can't use the static ipv6 address.
    # Instead, find the Ec2 instance that is the currently running minecraft
    # server and get its public ipv4 address
    server_ip = get_public_ip_address_of_server()
    if server_ip is None:
        return jsonify(
            online=False,
            players=0,
            version=None
        )
    server = MinecraftServer(server_ip, 25565)
    try:
        status = server.status(retries=2)
        is_online = True
        players = status.players.online
        version = status.version.name
    # mcstatus seems to like to throw AttributeError when the Minecraft server
    # is in the process of starting up
    except:
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
def start_server(user=None):
    print("%s requested a server start." % (user,))
    notify_sns("%s started the server!" % (user,))
    try:
        results = launch_minecraft_server()
    except Exception as e:
        print(e)
        return Response(str(e), status=500, mimetype='text/plain')
    if results == True:
        return Response("Server started", mimetype='text/plain')
    elif isinstance(results, str):
        print(results)
        return Response(results, status=409, mimetype='text/plain')
