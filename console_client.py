import os
import argparse
import requests
import time

DEFAULT_URL = os.getenv("API_URL", "http://localhost:5000")


def login(email: str, password: str, api_url: str) -> str:
    r = requests.post(
        f"{api_url}/api/auth/login",
        json={"email": email, "password": password},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def fetch_logs(token: str, api_url: str, start: int = 0):
    r = requests.get(
        f"{api_url}/api/logs/",
        params={"start": start},
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    r.raise_for_status()
    data = r.json()
    return data.get("lines", []), data.get("total", start)


def main():
    parser = argparse.ArgumentParser(description="Console client for PiAPS")
    parser.add_argument("--email", required=True, help="Admin email")
    parser.add_argument("--password", required=True, help="Admin password")
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help=f"Base API URL (default: {DEFAULT_URL})",
    )
    parser.add_argument("--watch", action="store_true", help="Follow logs")
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Polling interval when watching",
    )
    args = parser.parse_args()

    api_url = args.url.rstrip("/")
    token = login(args.email, args.password, api_url)
    start = 0
    while True:
        lines, total = fetch_logs(token, api_url, start)
        for line in lines:
            print(line.rstrip())
        start = total
        if not args.watch:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
