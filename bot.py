# -*- coding: utf-8 -*-
# author: elvin

import threading
import time
from datetime import datetime

import schedule
import telebot
import yaml
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from zerotier_service import MyZerotier


with open("config.yaml", "r", encoding="utf-8") as f:
    yaml_data = yaml.safe_load(f)
    BOT_TOKEN = yaml_data['bot_token']
    ADMIN_ID = yaml_data['admin_id']
    REFRESH_SECONDS = yaml_data['refresh_seconds']

# You can set parse_mode by default. HTML or MARKDOWN
bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None, threaded=True, num_threads=5)

myZerotier = MyZerotier()

pushed_node_id = {}  # 存放已推送过的新客户端

SUB_ADMIN_ID = []


def check_per_min():
    global pushed_node_id_list
    network_list = myZerotier.get_network()
    now = datetime.now()
    timestamp_now = now.timestamp()
    for network in network_list:
        new_member_list = myZerotier.check_new_member(network['id'])
        for new_member in new_member_list:
            if new_member['nodeId'] not in pushed_node_id:
                send_msg = """New member attached!
networkId: {}
nodeId: {}
online: {}
""".format(new_member['networkId'], new_member['nodeId'], new_member['online'])
                pushed_node_id[new_member['nodeId']] = {
                    'online': new_member['online']}
                print("new pushed", pushed_node_id)
                for id in ADMIN_ID or SUB_ADMIN_ID:
                    bot.send_message(id, send_msg, reply_markup=new_member_options_markup(
                        new_member['networkId'], new_member['nodeId']))

            elif new_member['nodeId'] in pushed_node_id:
                if pushed_node_id[new_member['nodeId']]['online'] != new_member['online']:
                    print("test data", new_member['nodeId'], new_member['online'])
                    if pushed_node_id[new_member['nodeId']]['online'] == False:
                        send_msg = """New member attached!
networkId: {}
nodeId: {}
online: {}
""".format(new_member['networkId'], new_member['nodeId'], new_member['online'])
                        pushed_node_id[new_member['nodeId']]['online'] = True
                        print("repeat pushed", pushed_node_id)
                        for id in ADMIN_ID or SUB_ADMIN_ID:
                            bot.send_message(id, send_msg, reply_markup=new_member_options_markup(
                                new_member['networkId'], new_member['nodeId']))
                    elif pushed_node_id[new_member['nodeId']]['online'] == True:
                        pushed_node_id[new_member['nodeId']]['online'] = False


def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)


def new_member_options_markup(network_id, node_id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("Accept", callback_data="cb_accept:{},{}".format(network_id, node_id)),
               InlineKeyboardButton("Ignore", callback_data="cb_ignore"))
    return markup


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data.split(":")[0] == "cb_accept":
        network_id = call.data.split(":")[1].split(",")[0]
        node_id = call.data.split(":")[1].split(",")[1]
        json_data = myZerotier.accept_member(network_id, node_id)
        msg = """Member accepted!
NetworkId: {}
NodeId: {}
Name: {}
ManagedIPs: {}
""".format(json_data['networkId'], json_data['nodeId'], json_data['name'], str(json_data['config']['ipAssignments']))
        # bot.answer_callback_query(call.id, "Answer is Yes")
        bot.edit_message_text(msg, call.message.chat.id,
                              call.message.id, reply_markup=None)
    elif call.data == "cb_ignore":
        msg = "Member ignored."
        bot.edit_message_text(msg, call.message.chat.id,
                              call.message.id, reply_markup=None)
        # bot.answer_callback_query(call.id, "Answer is No")
    elif call.data.split(":")[0] == "cb_network":
        # bot.edit_message_reply_markup(call.message.chat.id, call.message.id, reply_markup=None)
        member_list = myZerotier.get_network_member(call.data.split(":")[1])
        member_list = [
            {
                'name': i['name'],
                'online': i['online'],
                'ipAssignments': i['config']['ipAssignments'],
            }
            for i in member_list
        ]
        bot.edit_message_text(
            str(member_list), call.message.chat.id, call.message.id, reply_markup=None)


@bot.message_handler(commands=['start', 'help'])
def help_commad(message):
    if message.chat.id in ADMIN_ID:
        help_text = '''
Following the commands below to use this bot:
/help
    Show commands list.
/get_network
    Show your zerotier networks.
/show_sub_admin
    Show sub admin list.
/set_sub_admin
    Set a telegram id as sub admin.
/remove_sub_admin
    Remove a telegram id from sub admin.
/remove_all_sub_admins
    Remove all sub admins.
'''
        bot.send_message(message.chat.id, help_text)


@bot.message_handler(commands=['get_network'])
def get_network_command(message):
    if message.chat.id in ADMIN_ID:
        json_data = myZerotier.get_network()
        send_msg = "List of your networks:"
        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        for i in json_data:
            markup.add(InlineKeyboardButton("{}".format(
                i['config']['name']), callback_data="cb_network:{}".format(i['config']['id'])))
            send_msg += "\n{}: {}".format(i['config']
                                          ['name'], i['config']['id'])
        bot.send_message(message.chat.id, send_msg, reply_markup=markup)


@bot.message_handler(commands=['show_sub_admin'])
def show_sub_admin(message):
    if message.chat.id in ADMIN_ID:
        msg = "Sub admin list:"
        for i in SUB_ADMIN_ID:
            msg += "\n{}".format(str(i))
        bot.send_message(message.chat.id, msg)


@bot.message_handler(commands=['set_sub_admin'])
def set_sub_admin(message):
    if message.chat.id in ADMIN_ID:
        bot.send_message(message.chat.id, "Send me a telegram id",
                         add_sub_admin, timeout=60)


def add_sub_admin(message):
    if message.chat.id in ADMIN_ID:
        SUB_ADMIN_ID.append(int(message.text))


@bot.message_handler(commands=['remove_sub_admin'])
def remove_sub_admin(message):
    if message.id in ADMIN_ID:
        bot.send_message(message.chat.id, "Send me a telegram id",
                         del_sub_admin, timeout=60)


def del_sub_admin(message):
    if message.chat.id in ADMIN_ID:
        SUB_ADMIN_ID.remove(int(message.text))


@bot.message_handler(commands=['remove_all_sub_admins'])
def remove_all_sub_admins(message):
    if message.chat.id in ADMIN_ID:
        SUB_ADMIN_ID.clear()
        bot.send_message(message.chat.id, "Remove success")


if __name__ == '__main__':
    schedule.every(REFRESH_SECONDS).seconds.do(check_per_min)
    threading.Thread(target=run_schedule, name="ScheduleThread").start()
    bot.infinity_polling()
