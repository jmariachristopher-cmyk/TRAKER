"""
GET UPSTOX ACCESS TOKEN -- ONE COMMAND, NO COPY-PASTING
---------------------------------------------------------
Run this once each trading morning. It will:
  1. Open your browser to the Upstox login page automatically
  2. Catch the redirect locally (no manual copying of codes/URLs)
  3. Exchange it for an access token automatically
  4. Print the token for you to paste into the Streamlit app

SETUP (one-time):
  1. In your Upstox app settings (developer.upstox.com), change the
     Redirect URL to exactly:   http://127.0.0.1:8765/callback
     (Save it there -- it must match exactly what this script uses below.)
  2. Fill in CLIENT_ID and CLIENT_SECRET below with your API Key and API Secret.
  3. Run:  python get_token.py
"""

import http.server
import webbrowser
import requests
import threading
import urllib.parse

CLIENT_ID = "PASTE_YOUR_API_KEY_HERE"
CLIENT_SECRET = "PASTE_YOUR_API_SECRET_HERE"
REDIRECT_URI = "http://127.0.0.1:8765/callback"
PORT = 8765

captured_code = {"value": None}


class CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        code = params.get("code", [None])[0]

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        if code:
            captured_code["value"] = code
            self.wfile.write(b"<h2>Login successful. You can close this tab and go back to the terminal.</h2>")
        else:
            self.wfile.write(b"<h2>No code received. Something went wrong -- check the terminal.</h2>")

    def log_message(self, format, *args):
        pass  # silence default request logging


def run_server():
    server = http.server.HTTPServer(("127.0.0.1", PORT), CallbackHandler)
    while captured_code["value"] is None:
        server.handle_request()


def main():
    if "PASTE_YOUR" in CLIENT_ID or "PASTE_YOUR" in CLIENT_SECRET:
        print("Edit this file first: fill in CLIENT_ID and CLIENT_SECRET near the top.")
        return

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    auth_url = (
        "https://api.upstox.com/v2/login/authorization/dialog"
        f"?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
    )
    print("Opening your browser to log in to Upstox...")
    webbrowser.open(auth_url)

    server_thread.join(timeout=120)

    code = captured_code["value"]
    if not code:
        print("Timed out waiting for login. Try running this again.")
        return

    print("Login captured. Exchanging for an access token...")
    resp = requests.post(
        "https://api.upstox.com/v2/login/authorization/token",
        headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
        data={
            "code": code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        },
        timeout=15,
    )

    if resp.status_code != 200:
        print(f"Upstox rejected the exchange: {resp.status_code} {resp.text}")
        return

    token = resp.json().get("access_token")
    if not token:
        print(f"No access_token in response: {resp.json()}")
        return

    print("\n" + "=" * 60)
    print("ACCESS TOKEN (paste this into the Streamlit app sidebar):")
    print(token)
    print("=" * 60)


if __name__ == "__main__":
    main()
