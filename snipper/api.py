import os
import requests

BASE_URL = 'https://api.bitbucket.org/2.0'


class BitbucketApi(object):
    base_url = BASE_URL

    def set_config(self, config):
        self.config = config

    def get(self, endpoint):
        username = self.config.get('username')
        password = self.config.get('password')

        return requests.get(self.build_endpoint(endpoint), auth=(username, password))

    def build_endpoint(self, endpoint):
        return os.path.join(self.base_url, endpoint)


class Snippet(BitbucketApi):
    base_url = '{}/snippets'.format(BASE_URL)

    def get_all(self):
        res = self.get(self.username)
        return res.json()
