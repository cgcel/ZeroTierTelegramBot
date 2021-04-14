# -*- coding: utf-8 -*-
# author: elvin

import json

import requests
import yaml

url_api = "https://my.zerotier.com/api"

with open("config.yaml", "r", encoding="utf-8") as f:
    yaml_data = yaml.safe_load(f)
    ZEROTIER_TOKEN = yaml_data['zerotier_token']


class MyZerotier(object):
    def __init__(self) -> None:
        super().__init__()
        header = {"Authorization": "Bearer {}".format(ZEROTIER_TOKEN)}
        self.session = requests.Session()
        self.session.headers.update(header)

    def get_network(self):
        url = url_api + "/network"
        json_data = self.session.get(url).json()
        return json_data

    def get_network_member(self, network_id):
        url = url_api + "/network/{}/member".format(network_id)
        json_data = self.session.get(url).json()
        member_list = []
        for i in json_data:
            if i['networkId'] == network_id:
                member_list.append(i)
        return member_list

    def check_new_member(self, network_id):
        url = url_api + "/network/{}/member".format(network_id)
        json_data = self.session.get(url).json()
        member_list = []
        for i in json_data:
            if i['networkId'] == network_id and i['config']['authorized'] == False:
                member_list.append(i)
        return member_list

    def accept_member(self, network_id, node_id):
        url = url_api + "/network/{}/member/{}".format(network_id, node_id)
        form_data = {
            "config": {
                "authorized": True
            }
        }
        payload = json.dumps(form_data)
        json_data = self.session.post(url, data=payload).json()
        return json_data


if __name__ == "__main__":
    myZerotier = MyZerotier()
    print(myZerotier.get_network())
