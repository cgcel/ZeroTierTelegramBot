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

    def get_network(self, *args):
        if len(args) == 1:
            url = url_api + "/network/{}".format(args[0])
            json_data = self.session.get(url).json()
            return json_data
        elif len(args) == 0:
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

    def reject_member(self, network_id, node_id):
        url = url_api + "/network/{}/member/{}".format(network_id, node_id)
        r = self.session.delete(url)
        if r.status_code == 200:
            return True
        else:
            return False

    def set_member_name(self, network_id, node_id, member_name):
        url = url = url_api + \
            "/network/{}/member/{}".format(network_id, node_id)
        form_data = {
            "name": member_name
            }
        payload = json.dumps(form_data)
        json_data = self.session.post(url, data=payload).json()
        return json_data


if __name__ == "__main__":
    myZerotier = MyZerotier()
    # print(myZerotier.get_network())
    print(myZerotier.get_network_member('d3ecf5726d7c94dd')
          [0]['config']['ipAssignments'][0])
