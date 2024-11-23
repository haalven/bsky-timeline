# bluesky API

import requests


class BskySession:
    BASE_URL = 'https://bsky.social/xrpc'

    def __init__(self, handle, app_password):
        self.handle = handle
        self.app_password = app_password
        self.access_token, self.did = self._create_session()

    def _create_session(self):
        url = f'{self.BASE_URL}/com.atproto.server.createSession'
        try:
            resp = requests.post(url, json={'identifier': self.handle, 'password': self.app_password}, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            print('⚠️', 'BskySession.create_session() error:', str(e) + '\n')
        session = resp.json()
        return session['accessJwt'], session['did']

    def get_auth_header(self):
        return {'Authorization': f'Bearer {self.access_token}'}

    def api_call(self, endpoint, method='GET', json=None, data=None, headers=None):
        url = f'{self.BASE_URL}/{endpoint}'
        headers = headers or {}
        headers.update(self.get_auth_header())
        try:
            resp = requests.request(method, url, headers=headers, json=json, data=data, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print('⚠️', 'BskySession.api_call() error:', str(e) + '\n')
