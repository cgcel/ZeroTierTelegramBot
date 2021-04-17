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
bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

myZerotier = MyZerotier()

pushed_node_id = {}  # store pushed node

SUB_ADMIN_ID = []  # store sub admins' telegram id


def check_per_min():
    """check for updates from ZeroTier Web API
    """
    global pushed_node_id_list
    network_list = myZerotier.get_network()
    for network in network_list:
        new_member_list = myZerotier.check_new_member(network['id'])
        for new_member in new_member_list:
            if new_member['nodeId'] not in pushed_node_id:
                send_msg = """New member attached!
networkId: `{}`
nodeId: `{}`
online: `{}`
""".format(new_member['networkId'], new_member['nodeId'], new_member['online'])
                pushed_node_id[new_member['nodeId']] = {
                    'online': new_member['online']}
                for id in ADMIN_ID or SUB_ADMIN_ID:
                    bot.send_message(id, send_msg, reply_markup=new_member_options_markup(
                        new_member['networkId'], new_member['nodeId']), parse_mode="markdown")

            elif new_member['nodeId'] in pushed_node_id:
                if pushed_node_id[new_member['nodeId']]['online'] != new_member['online']:
                    if pushed_node_id[new_member['nodeId']]['online'] == False:
                        send_msg = """New member attached!
networkId: `{}`
nodeId: `{}`
online: `{}`
""".format(new_member['networkId'], new_member['nodeId'], new_member['online'])
                        pushed_node_id[new_member['nodeId']]['online'] = True
                        for id in ADMIN_ID or SUB_ADMIN_ID:
                            bot.send_message(id, send_msg, reply_markup=new_member_options_markup(
                                new_member['networkId'], new_member['nodeId']), parse_mode="markdown")
                    elif pushed_node_id[new_member['nodeId']]['online'] == True:
                        pushed_node_id[new_member['nodeId']]['online'] = False


def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)


def new_member_options_markup(network_id, node_id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 3
    markup.add(InlineKeyboardButton("Accept", callback_data="cb_accept:{},{}".format(network_id, node_id)),
               InlineKeyboardButton(
                   "Reject", callback_data="cb_reject:{},{}".format(network_id, node_id)),
               InlineKeyboardButton("Ignore", callback_data="cb_ignore"))
    return markup


def network_items_markup(network_list):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    for network in network_list:
        markup.add(InlineKeyboardButton(
            network[0], callback_data="cb_network:{}".format(network[1])))
    markup.add(InlineKeyboardButton(
        "Refresh", callback_data="cb_refresh_network_list"))
    return markup


def network_member_options_markup(network_id, display_mode):
    markup = InlineKeyboardMarkup()
    markup.row_width = 3
    if display_mode == "ip":
        markup.add(InlineKeyboardButton("Back", callback_data="cb_back"),
                   InlineKeyboardButton(
                       "Show nodeId", callback_data="cb_show_node_id:{}".format(network_id)),
                   InlineKeyboardButton("Refresh", callback_data="cb_refresh_network_status:{}".format(network_id)))
    elif display_mode == "node_id":
        markup.add(InlineKeyboardButton("Back", callback_data="cb_back"),
                   InlineKeyboardButton(
                       "Show IP", callback_data="cb_show_ip:{}".format(network_id)),
                   InlineKeyboardButton("Refresh", callback_data="cb_refresh_network_status:{}".format(network_id)))
    return markup


def set_name_options_markup(network_id, node_id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("Yes", callback_data="cb_set_name_yes:{}:{}".format(network_id, node_id)),
               InlineKeyboardButton("Later", callback_data="cb_set_name_later"))
    return markup


@bot.callback_query_handler(func=lambda call: call.data == "cb_set_name_later")
def callback_query(call):
    bot.edit_message_reply_markup(
        call.message.chat.id, call.message.id, reply_markup=None)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data.split(":")[0] == "cb_accept":
        global pushed_node_id
        network_id = call.data.split(":")[1].split(",")[0]
        node_id = call.data.split(":")[1].split(",")[1]
        json_data = myZerotier.accept_member(network_id, node_id)
        network_id = json_data['networkId']
        node_id = json_data['nodeId']
        member_name = "None" if len(
            json_data['name']) == 0 else json_data['name']
        member_ip = "None" if len(
            json_data['config']['ipAssignments']) == 0 else json_data['config']['ipAssignments'][0]
        msg = """Member accepted!
NetworkId: `{}`
NodeId: `{}`
Name: `{}`
ManagedIPs: `{}`
*Set a name for this member?*
""".format(network_id, node_id, member_name, member_ip)
        # bot.answer_callback_query(call.id, "Answer is Yes")
        bot.edit_message_text(msg, call.message.chat.id,
                              call.message.id, reply_markup=set_name_options_markup(network_id, node_id), parse_mode="markdown")
        try:
            pushed_node_id.pop(node_id)  # delete node from dict after accepted
        except:
            pass
    elif call.data.split(":")[0] == "cb_reject":
        network_id = call.data.split(":")[1].split(",")[0]
        node_id = call.data.split(":")[1].split(",")[1]
        if myZerotier.reject_member(network_id, node_id):
            bot.edit_message_text("You have deleted this member.",
                                  call.message.chat.id, call.message.id, reply_markup=None)
    elif call.data == "cb_ignore":
        msg = "Member ignored."
        bot.edit_message_text(msg, call.message.chat.id,
                              call.message.id, reply_markup=None)
        # bot.answer_callback_query(call.id, "Answer is No")
    elif call.data.split(":")[0] == "cb_network" or call.data.split(":")[0] == "cb_refresh_network_status" or call.data.split(":")[0] == "cb_show_ip":
        # bot.edit_message_reply_markup(call.message.chat.id, call.message.id, reply_markup=None)
        network_id = call.data.split(":")[1]
        member_list = myZerotier.get_network_member(network_id)
        member_list = [
            {
                'name': i['name'],
                'online': i['online'],
                'ipAssignments': i['config']['ipAssignments'],
            }
            for i in member_list
        ]
        network_name = myZerotier.get_network(network_id)['config']['name']
        send_msg = """Network *{}*:
--------------------------------------------------------------------
🟢--_Online_ 🔴--_Offline_
--------------------------------------------------------------------""".format(network_name.replace('_', '-'))
        for member in member_list:
            format_name = "Unauthorized member" if len(
                member['name']) == 0 else member['name'].replace('_', '-')
            format_ip = "None" if len(
                member['ipAssignments']) == 0 else member['ipAssignments'][0]
            if member['online'] == True:
                send_msg += "\n🟢 {}: `{}`".format(format_name, format_ip)
            elif member['online'] == False:
                send_msg += "\n🔴 {}: `{}`".format(format_name, format_ip)
        send_msg += """
--------------------------------------------------------------------
_Updated at: {}_""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        bot.edit_message_text(
            send_msg, call.message.chat.id, call.message.id, reply_markup=network_member_options_markup(network_id, "ip"), parse_mode="markdown")

    elif call.data.split(":")[0] == "cb_show_node_id":
        # bot.edit_message_reply_markup(call.message.chat.id, call.message.id, reply_markup=None)
        network_id = call.data.split(":")[1]
        member_list = myZerotier.get_network_member(network_id)
        member_list = [
            {
                'name': i['name'],
                'online': i['online'],
                'nodeId': i['nodeId'],
            }
            for i in member_list
        ]
        network_name = myZerotier.get_network(network_id)['config']['name']
        send_msg = """Network *{}*:
--------------------------------------------------------------------
🟢--_Online_ 🔴--_Offline_
--------------------------------------------------------------------""".format(network_name.replace('_', '-'))
        for member in member_list:
            format_name = "Unauthorized member" if len(
                member['name']) == 0 else member['name'].replace('_', '-')
            node_id = member['nodeId']
            if member['online'] == True:
                send_msg += "\n🟢 {}: `{}`".format(format_name, node_id)
            elif member['online'] == False:
                send_msg += "\n🔴 {}: `{}`".format(format_name, node_id)
        send_msg += """
--------------------------------------------------------------------
_Updated at: {}_""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        bot.edit_message_text(
            send_msg, call.message.chat.id, call.message.id, reply_markup=network_member_options_markup(network_id, "node_id"), parse_mode="markdown")

    elif call.data == "cb_back" or call.data == "cb_refresh_network_list":
        if call.message.chat.id in ADMIN_ID or SUB_ADMIN_ID:
            json_data = myZerotier.get_network()
            payload = [[x['config']['name'], x['config']['id']]
                       for x in json_data]  # [[network_name, network_id],...]
            send_msg = """*List of your networks:*
--------------------------------------------------------------------"""
            for i in json_data:
                send_msg += "\n🌐 {}: `{}`".format(i['config']
                                                  ['name'].replace('_', '-'), i['config']['id'].replace('_', '-'))
            send_msg += """--------------------------------------------------------------------
_Updated at: {}_""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            bot.edit_message_text(send_msg, call.message.chat.id, call.message.id,
                                  reply_markup=network_items_markup(payload), parse_mode="markdown")

    elif call.data.split(":")[0] == "cb_set_name_yes":
        network_id = call.data.split(":")[1]
        node_id = call.data.split(":")[2]
        send_msg = """Set up member name:
NetworkId: `{}`
NodeId: `{}`
*Reply this message with your prefer member name*""".format(network_id, node_id)
        msg = bot.edit_message_text(
            send_msg, call.message.chat.id, call.message.id, parse_mode="markdown")
        bot.register_for_reply(msg, set_name, network_id, node_id)


@bot.message_handler(commands=['start', 'help'])
def help_commad(message):
    if message.chat.id in ADMIN_ID:
        help_text = '''
Following the commands below to use this bot:
/help
    Show commands list.
/show_network
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


@bot.message_handler(commands=['show_network'])
def show_network_command(message):
    if message.chat.id in ADMIN_ID or SUB_ADMIN_ID:
        json_data = myZerotier.get_network()
        payload = [[x['config']['name'], x['config']['id']]
                   for x in json_data]  # [[network_name, network_id],...]
        send_msg = """*List of your networks:*
--------------------------------------------------------------------"""
        for i in json_data:
            send_msg += "\n🌐 {}: `{}`".format(i['config']
                                              ['name'].replace('_', '-'), i['config']['id'].replace('_', '-'))
        send_msg += """--------------------------------------------------------------------
_Updated at: {}_""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        bot.send_message(message.chat.id, send_msg,
                         reply_markup=network_items_markup(payload), parse_mode="markdown")


@bot.message_handler(commands=['set_member_name'])
def set_member_name_command(message):
    if message.chat.id in ADMIN_ID:
        if len(message.text.split(" ")[1:]) == 1:
            node_id = message.text.split(" ")[1]
            msg = bot.send_message(message.chat.id, "Send me the new name:")
            # bot.register_next_step_handler(msg, )

            pass


def set_name(message, network_id, node_id):
    if message.chat.id in ADMIN_ID:
        myZerotier.set_member_name(network_id, node_id, message.text)
        bot.send_message(message.chat.id, "Done.")


@bot.message_handler(commands=['show_sub_admin'])
def show_sub_admin_command(message):
    if message.chat.id in ADMIN_ID:
        if len(SUB_ADMIN_ID) == 0:
            bot.send_message(
                message.chat.id, "There are no sub admins yet. Use /set_sub_admin to set up your sub admin list.")
        else:
            msg = "Sub admin list:"
            for i in SUB_ADMIN_ID:
                msg += "\n`{}`".format(str(i))
            bot.send_message(message.chat.id, msg, parse_mode="markdown")


@bot.message_handler(commands=['set_sub_admin'])
def set_sub_admin_command(message):
    if message.chat.id in ADMIN_ID:
        msg = bot.send_message(
            message.chat.id, "Reply to this message and send me a telegram id.")
        bot.register_for_reply(msg, add_sub_admin)


def add_sub_admin(message):
    if message.chat.id in ADMIN_ID:
        tg_id = int(message.text)
        if tg_id not in SUB_ADMIN_ID:
            SUB_ADMIN_ID.append(int(message.text))
            bot.send_message(message.chat.id, "You have promoted `{}` to sub admin.".format(
                message.text), parse_mode="markdown")
        else:
            bot.send_message(message.chat.id, "This id is already existed!")


@bot.message_handler(commands=['remove_sub_admin'])
def remove_sub_admin_command(message):
    if message.chat.id in ADMIN_ID:
        msg = bot.send_message(
            message.chat.id, "Reply to this message and send me a telegram id.")
        bot.register_for_reply(msg, del_sub_admin)


def del_sub_admin(message):
    if message.chat.id in ADMIN_ID:
        tg_id = int(message.text)
        if tg_id in SUB_ADMIN_ID:
            SUB_ADMIN_ID.remove(int(message.text))
            bot.send_message(message.chat.id, "You have removed `{}` from sub admin.".format(
                message.text), parse_mode="markdown")
        else:
            bot.send_message(
                message.chat.id, "This is not a sub admin. /show_sub_admin")


@bot.message_handler(commands=['remove_all_sub_admins'])
def remove_all_sub_admins_command(message):
    if message.chat.id in ADMIN_ID:
        if len(SUB_ADMIN_ID) > 0:
            SUB_ADMIN_ID.clear()
            bot.send_message(message.chat.id, "Removed.")
        else:
            bot.send_message(
                message.chat.id, "There are no sub admins to remove!")


if __name__ == '__main__':
    schedule.every(REFRESH_SECONDS).seconds.do(check_per_min)
    threading.Thread(target=run_schedule, name="ScheduleThread").start()
    bot.infinity_polling()
