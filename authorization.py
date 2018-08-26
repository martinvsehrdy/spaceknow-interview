import os
import requests
import json
import time

class Authorization:
    def __init__(self, host, client_id, username, password, token_file=None):
        self.host = host
        self.client_id = client_id
        self.username = username
        self.password = password
        self.valid_to = 0.0
        if os.path.isfile(token_file):
            self.load_token(token_file)
        if self.valid_to < time.time():
            self.update_token()

    def __repr__(self):
        return f"{self.username} valid to {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.valid_to))}"

    def update_token(self):
        login_data = {
            "client_id": self.client_id,
            "username": self.username,
            "password": self.password,
            "connection": "Username-Password-Authentication",
            "grant_type": "password",
            "scope": "openid"
        }
        r = requests.post(self.host, data=login_data)
        if r.status_code == 200:
            jsondata = r.json()
            self.id_token = jsondata.get("id_token")
            self.valid_to = time.time() + 10 * 60 * 60  # current time plus 10 hours
        else:
            print(r.status_code)
            print(r.headers['content-type'])
            print(r.encoding)
            print(r.text)

    def save_token(self, token_file):
        file_data = {
            "id_token": self.id_token,
            "valid_to": self.valid_to,
        }
        json.dump(file_data, open(token_file, "w"))

    def load_token(self, token_file):
        if os.path.isfile(token_file):
            file_data = json.load(open(token_file))
            self.id_token = file_data["id_token"]
            self.valid_to = file_data["valid_to"]

    def headers(self):
        rest_of_time = self.valid_to - time.time()
        if rest_of_time < 0:
            self.update_token()
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(self.id_token),
        }
        return headers

# username="a6427229@nwytg.net", password="AW3EDCc"
class SpaceKnowAuth(Authorization):
    def __init__(self, **kwargs):
        super().__init__(
            host='https://spaceknow.auth0.com/oauth/ro',
            client_id="hmWJcfhRouDOaJK2L8asREMlMrv3jFE1",
            **kwargs)

class SpaceKnowTestAuth(Authorization):
    def __init__(self, **kwargs):
        super().__init__(
            host='https://spaceknow-test.auth0.com/oauth/ro',
            client_id="UWBUvt919N0sUXjG1CepGhiR0DJuazSY",
            **kwargs)


if __name__ == '__main__':
    token_file = "token_file.json"
    auth = SpaceKnowAuth(username="a6427229@nwytg.net", password="AW3EDCc", token_file=token_file)
    print(auth.id_token)
    rest_of_time = auth.valid_to - time.time()
    print("{} minutes and {} seconds is remaining".format(rest_of_time / 60, rest_of_time % 60))
    auth.save_token(token_file)
