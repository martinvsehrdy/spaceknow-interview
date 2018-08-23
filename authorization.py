import requests
import json

class Authorization:
    def __init__(self, host, client_id):
        self.login_data = {
            "client_id": client_id,
            "username": None,
            "password": None,
            "connection": "Username-Password-Authentication",
            "grant_type": "password",
            "scope": "openid"
        }
        self.host = host
        self.id_token = None

    def connect(self, username, password):
        self.login_data["username"] = username
        self.login_data["password"] = password
        # curl --request POST --url https://spaceknow.auth0.com/oauth/ro --header 'Content-Type: application/json' --data {json.dumps(self.login_data)}
        r = requests.post(self.host, data=self.login_data)
        if r.status_code == 200:
            jsondata = r.json()
            self.id_token = jsondata.get("id_token")
        else:
            print(r.status_code)
            print(r.headers['content-type'])
            print(r.encoding)
            print(r.text)


# username="a6427229@nwytg.net", password="AW3EDCc"
class SpaceKnowAuth(Authorization):
    def __init__(self):
        super().__init__(
            host='https://spaceknow.auth0.com/oauth/ro',
            client_id="hmWJcfhRouDOaJK2L8asREMlMrv3jFE1")

class SpaceKnowTestAuth(Authorization):
    def __init__(self):
        super().__init__(
            host='https://spaceknow-test.auth0.com/oauth/ro',
            client_id="UWBUvt919N0sUXjG1CepGhiR0DJuazSY")


if __name__ == '__main__':
    import time
    token_file = "token_file.json"
    try:
        auth_data = json.load(open(token_file))
        id_token = auth_data["id_token"]
        rest_of_time = auth_data["token_end_time"] - time.time()
        if rest_of_time < 0:
            raise TimeoutError
        print(rest_of_time, "seconds is remaining")
    except:
        auth = SpaceKnowTestAuth()
        auth = SpaceKnowAuth()

        auth.connect("a6427229@nwytg.net", "AW3EDCc")
        print("GET NEW TOKEN")
        print(auth.id_token)

        auth_data = {
            "id_token": auth.id_token,
            "token_end_time": time.time() + 10 * 60 * 60,  # current time plus 10 hours
        }
        json.dump(auth_data, open(token_file, "w"))
