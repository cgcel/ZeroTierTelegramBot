# -*- coding: utf-8 -*-
# author: elvin

import requests
import json
from requests.api import head
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
        r = self.session.get(url)
        json_data = json.loads(r.text)
        # print(json_data)
        # print(len(json_data))
        return json_data

    def get_network_member(self, network_id):
        url = url_api + "/network/{}/member".format(network_id)
        r = self.session.get(url)
        json_data = json.loads(r.text)
        member_list = []
        for i in json_data:
            if i['networkId'] == network_id:
                member_list.append(i)
        return member_list

    def check_new_member(self, network_id):
        url = url_api + "/network/{}/member".format(network_id)
        r = self.session.get(url)
        json_data = json.loads(r.text)
        member_list = []
        for i in json_data:
            if i['networkId'] == network_id and i['online'] == True and i['config']['authorized'] == False:
                member_list.append(i)
        return member_list


if __name__ == "__main__":
    myZerotier = MyZerotier()
    # myZerotier.get_network()
    # print(myZerotier.get_network_member("d3ecf5726d7c94dd"))
    print(myZerotier.check_new_member("abfd31bd4779f905"))
