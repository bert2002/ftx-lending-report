#!/usr/bin/env python3
# script: check lending status on FTX exchange
# author: bert2002
# notes:

import time
import urllib.parse
from typing import Optional, Dict, Any, List

from requests import Request, Session, Response
import hmac

# API credentials

FTX_API_KEY=''
FTX_SECRET=''

class FtxClient:
    _ENDPOINT = 'https://ftx.com/api/'

    def __init__(self, api_key=None, api_secret=None, subaccount_name=None) -> None:
        self._session = Session()
        self._api_key = api_key
        self._api_secret = api_secret
        self._subaccount_name = subaccount_name

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('GET', path, params=params)

    def _post(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('POST', path, json=params)

    def _delete(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('DELETE', path, json=params)

    def _request(self, method: str, path: str, **kwargs) -> Any:
        request = Request(method, self._ENDPOINT + path, **kwargs)
        self._sign_request(request)
        response = self._session.send(request.prepare())
        return self._process_response(response)

    def _sign_request(self, request: Request) -> None:
        ts = int(time.time() * 1000)
        prepared = request.prepare()
        signature_payload = f'{ts}{prepared.method}{prepared.path_url}'.encode()
        if prepared.body:
            signature_payload += prepared.body
        signature = hmac.new(self._api_secret.encode(), signature_payload, 'sha256').hexdigest()
        request.headers['FTX-KEY'] = self._api_key
        request.headers['FTX-SIGN'] = signature
        request.headers['FTX-TS'] = str(ts)
        if self._subaccount_name:
            request.headers['FTX-SUBACCOUNT'] = urllib.parse.quote(self._subaccount_name)

    def _process_response(self, response: Response) -> Any:
        try:
            data = response.json()
        except ValueError:
            response.raise_for_status()
            raise
        else:
            if not data['success']:
                raise Exception(data['error'])
            return data['result']

    def lending_history(self) -> List[dict]:
        return self._get('spot_margin/lending_history')

    def lending_rates(self) -> List[dict]:
        return self._get('spot_margin/lending_rates')

    def lending_info(self) -> List[dict]:
        return self._get('spot_margin/lending_info')

    def offers(self) -> List[dict]:
        return self._get('spot_margin/offers')

client = FtxClient(api_key=FTX_API_KEY, api_secret=FTX_SECRET)
lending_history = client.lending_history()
lending_history_coin = lending_history[0]['coin']
lending_history_time = lending_history[0]['time']
lending_history_size = lending_history[0]['size']
lending_history_rate = lending_history[0]['rate']
lending_history_rate_d = format(float(lending_history[0]['rate']), 'f')

lending_rates = client.lending_rates()
for rates in lending_rates:
    if rates['coin'] == 'USDT':
        lending_rates_estimate = format(float(rates['estimate']), 'f')

lending_info = client.lending_info()
for info in lending_info:
    if info['coin'] == 'USDT':
        lending_info_rate = format(float(info['minRate']), 'f')

print('%s was lent last at %s at %s with total %s. The current rate is %s and your offer is %s' % (lending_history_coin,lending_history_time,lending_history_rate_d,lending_history_size,lending_rates_estimate,lending_info_rate))
