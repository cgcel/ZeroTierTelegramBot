# -*- coding: utf-8 -*-
# author: elvin

import threading
import time

import schedule
import telebot
import yaml
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from zerotier_service import MyZerotier


with open("config.yaml", "r", encoding="utf-8") as f:
    yaml_data = yaml.safe_load(f)
    BOT_TOKEN = yaml_data['bot_token']
    ADMIN_ID = yaml_data['admin_id']

# You can set parse_mode by default. HTML or MARKDOWN
bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None, threaded=True, num_threads=5)

myZerotier = MyZerotier()

pushed_node_id_list = []  # 存放已推送过的新客户端

SUB_ADMIN_ID = []


def check_per_min():
    global pushed_node_id_list
    total_add_node_id_list = []
    network_list = myZerotier.get_network()
    for i in network_list:
        new_member_list = myZerotier.check_new_member(i['id'])
        add_member_list = [
            x for x in new_member_list if x['nodeId'] not in pushed_node_id_list]
        total_add_node_id_list += [x['nodeId'] for x in new_member_list]
        if len(add_member_list) > 0:
            for i in add_member_list:
                msg = """New member attached!
networkId: {}
nodeId: {}
"""
                send_msg = msg.format(i['networkId'], i['nodeId'])
                for id in ADMIN_ID:
                    bot.send_message(
                        id, send_msg, reply_markup=get_new_member_markup(i['networkId'], i['nodeId']))
    remove_list = [
        x for x in pushed_node_id_list if x not in total_add_node_id_list]
    add_list = [
        x for x in total_add_node_id_list if x not in pushed_node_id_list]
    if len(total_add_node_id_list) > 0:
        if len(remove_list) > 0:
            for i in remove_list:
                pushed_node_id_list.remove(i)
        if len(add_list) > 0:
            for i in add_list:
                pushed_node_id_list.append(i)
    else:
        return


def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)


def get_new_member_markup(network_id, node_id):
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
    schedule.every().minute.do(check_per_min)
    threading.Thread(target=run_schedule, name="ScheduleThread").start()
    bot.polling(none_stop=True)
