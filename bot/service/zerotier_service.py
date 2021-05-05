# -*- coding: utf-8 -*-
# author: elvin

import requests
import yaml

url_api = "https://my.zerotier.com/api"

with open("config.yaml", "r", encoding="utf-8") as f:
    yaml_data = yaml.safe_load(f)
    ZEROTIER_TOKEN = yaml_data['zerotier_token']


class MyZeroTier(object):
    def __init__(self) -> None:
        super().__init__()
        header = {"Authorization": "Bearer {}".format(ZEROTIER_TOKEN)}
        self.session = requests.Session()
        self.session.headers.update(header)

    def get_network(self, network_id: str = None):
        """Get network funtion, used to get your networks' informations.

        Args:
            network_id (string, optional): Your ZeroTier networkId. Defaults to None.

        Returns:
            json: Returns a json list about your network.
        """
        if network_id != None:
            url = url_api + "/network/{}".format(network_id)
            json_data = self.session.get(url).json()
            return json_data
        elif network_id == None:
            url = url_api + "/network"
            json_data = self.session.get(url).json()
            return json_data

    def get_network_member(self, network_id: str, check_new_member: bool = False):
        """A funtion used to get network members or check for new members.

        Args:
            network_id (string): Your ZeroTier networkId.
            check_new_member (bool, optional): If True, check for new members and return a new members' list. Defaults to False.

        Returns:
            list: Returns a member list.
        """
        url = url_api + "/network/{}/member".format(network_id)
        json_data = self.session.get(url).json()
        if check_new_member == False:
            member_list = []
            for i in json_data:
                if i['networkId'] == network_id:
                    member_list.append(i)
            return member_list
        elif check_new_member == True:
            member_list = []
            for i in json_data:
                if i['networkId'] == network_id and i['config']['authorized'] == False:
                    member_list.append(i)
            return member_list

    def set_up_member(self, network_id: str, node_id: str, hidden: bool = False, name: str = None, description: str = None, authorized: bool = True):
        """A funtion used to set up your network member

        Args:
            network_id (string): Your ZeroTier networkId.
            node_id (string): Your nodeId in network.
            hidden (bool, optional): Hide your node in network or not. Defaults to False.
            name (string, optional): Name to set up with member. Defaults to None.
            description (string, optional): Write some descriptions for your member. Defaults to None.
            authorized (bool, optional): Auth or unauthorize your network member. Defaults to True.

        Returns:
            [type]: [description]
        """
        url = url_api + "/network/{}/member/{}".format(network_id, node_id)
        form_data = {
            "hidden": hidden,
            "name": name,
            "description": description,
            "config": {
                "authorized": authorized,
            }
        }
        payload = json.dumps(form_data)
        json_data = self.session.post(url, data=payload).json()
        return json_data

    def reject_member(self, network_id: str, node_id: str):
        """Reject member function. The member which you have deleted from network cannot join this network again.

        Args:
            network_id (string): Your ZeroTier networkId.
            node_id (string): Your nodeId in network.

        Returns:
            bool: return True if status_code == 200, else return False.
        """
        url = url_api + "/network/{}/member/{}".format(network_id, node_id)
        r = self.session.delete(url)
        if r.status_code == 200:
            return True
        else:
            return False


if __name__ == "__main__":
    myZerotier = MyZeroTier()
    # print(myZerotier.get_network())
