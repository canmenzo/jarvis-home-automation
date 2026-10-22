import hmac
import os
from flask import Flask, request, abort
from waitress import serve
from wakeonlan import send_magic_packet

app = Flask(__name__)

MAC = os.environ["WOL_MAC"]      # e.g. "AA:BB:CC:DD:EE:FF"
TOKEN = os.environ["WOL_TOKEN"]  # your secret token


@app.route("/wakeup")
def wakeup():
    # Prefer the Authorization header; the query param stays for the Siri shortcut
    auth = request.headers.get("Authorization", "")
    token = auth[7:] if auth.startswith("Bearer ") else request.args.get("token", "")
    # compare_digest rather than ==, which returns on the first wrong byte and so
    # leaks the token one character at a time to anyone timing the replies
    if hmac.compare_digest(token.encode(), TOKEN.encode()):
        send_magic_packet(MAC)
        return "OK", 200
    abort(403)


@app.route("/health")
def health():
    return "OK", 200


if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=8765)
