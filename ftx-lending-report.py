#!/usr/bin/env python3
# script: check lending status on FTX exchange
# author: bert2002
# notes:

import hmac
import json
import time
import urllib.parse
from typing import Any, Dict, List, Optional

import dateutil.parser
import requests
from dateutil import tz
from requests import Request, Response, Session

# API credentials
FTX_API_KEY = ""
FTX_SECRET = ""
# symbols to lend
SYMBOLS_TO_LEND = []
# Line bot access token
ACCESS_TOKEN = ""


class FtxClient:
    _ENDPOINT = "https://ftx.com/api/"

    def __init__(self, api_key=None, api_secret=None, subaccount_name=None) -> None:
        self._session = Session()
        self._api_key = api_key
        self._api_secret = api_secret
        self._subaccount_name = subaccount_name

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request("GET", path, params=params)

    def _post(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request("POST", path, json=params)

    def _delete(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request("DELETE", path, json=params)

    def _request(self, method: str, path: str, **kwargs) -> Any:
        request = Request(method, self._ENDPOINT + path, **kwargs)
        self._sign_request(request)
        response = self._session.send(request.prepare())
        return self._process_response(response)

    def _sign_request(self, request: Request) -> None:
        ts = int(time.time() * 1000)
        prepared = request.prepare()
        signature_payload = f"{ts}{prepared.method}{prepared.path_url}".encode()
        if prepared.body:
            signature_payload += prepared.body
        signature = hmac.new(
            self._api_secret.encode(), signature_payload, "sha256"
        ).hexdigest()
        request.headers["FTX-KEY"] = self._api_key
        request.headers["FTX-SIGN"] = signature
        request.headers["FTX-TS"] = str(ts)
        if self._subaccount_name:
            request.headers["FTX-SUBACCOUNT"] = urllib.parse.quote(
                self._subaccount_name
            )

    def _process_response(self, response: Response) -> Any:
        try:
            data = response.json()
        except ValueError:
            response.raise_for_status()
            raise
        else:
            if not data["success"]:
                raise Exception(data["error"])
            return data["result"]


if __name__ == "__main__":
    client = FtxClient(api_key=FTX_API_KEY, api_secret=FTX_SECRET)
    lending_history = client._get("spot_margin/lending_history")
    # sample obj in the list
    # {'coin': 'USDT', 'proceeds': 1.22156779596925, 'rate': 3.425e-05, 'size': 35666.213021, 'time': '2021-02-03T15:00:00+00:00'}
    latest_interest = lending_history[0]
    coin = latest_interest["coin"]
    proceeds = latest_interest["proceeds"]
    principal = latest_interest["size"]
    rate = format(float(latest_interest["rate"]), "f")
    from_zone = tz.gettz("UTC")
    to_zone = tz.gettz("Asia/Taipei")
    lend_time = (
        dateutil.parser.isoparse(latest_interest["time"])
        .replace(tzinfo=from_zone)
        .astimezone(to_zone)
    ).strftime("%m/%d/%Y, %H:%M:%S")

    # submit lending offer with a the new balances
    balances = client._get("wallet/balances")
    # only lend out USDT
    for balance in balances:
        if balance["coin"] in SYMBOLS_TO_LEND:
            print(f"balance {balance}")
            total_bal = balance["total"]
            print("lending out %s %s" % total_bal, balance["coin"])
            client._post(
                "spot_margin/offers",
                # set the rate low, so can still lend out every hour
                {"coin": "USDT", "size": total_bal, "rate": 0.0000068},
            )
    # send to line bot
    message = "%s %s principle %s interest %s, hourly interest rate %s" % (
        lend_time,
        coin,
        principal,
        proceeds,
        rate,
    )
    requests.post(
        "https://api.line.me/v2/bot/message/broadcast",
        data=json.dumps({"messages": [{"type": "text", "text": message}]}),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {ACCESS_TOKEN}",
        },
    )
