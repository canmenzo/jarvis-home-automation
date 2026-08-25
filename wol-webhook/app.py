import hmac
import os
from flask import Flask, request, abort
from wakeonlan import send_magic_packet

app = Flask(__name__)

MAC = os.environ["WOL_MAC"]      # e.g. "AA:BB:CC:DD:EE:FF"
TOKEN = os.environ["WOL_TOKEN"]  # your secret token


@app.route("/wakeup")
def wakeup():
    # compare_digest rather than ==, which returns on the first wrong byte and so
    # leaks the token one character at a time to anyone timing the replies
    if hmac.compare_digest(request.args.get("token", ""), TOKEN):
        send_magic_packet(MAC)
        return "OK", 200
    abort(403)


@app.route("/health")
def health():
    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8765)
