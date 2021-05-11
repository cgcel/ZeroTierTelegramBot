# -*- coding: utf-8 -*-
# author: elvin

import logging
import time
from datetime import datetime

import schedule
import telebot
import yaml
from retry import retry
from service.zerotier_service import MyZeroTier
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = telebot.logger
logger.setLevel(logging.DEBUG)

with open("config.yaml", "r", encoding="utf-8") as f:
    yaml_data = yaml.safe_load(f)
    BOT_TOKEN = yaml_data['bot_token']
    ADMIN_ID = yaml_data['admin_id']
    REFRESH_SECONDS = yaml_data['refresh_seconds']

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

myZeroTier = MyZeroTier()

pushed_node_id = {}  # store pushed node

groups_id_list = []  # store groups' telegram id


def is_chat_admin(message, id: str):
    """Use this funtion to check member's permission

    Args:
        message ([type]): [description]
        id (str): [description]

    Returns:
        bool: Return True for admin, False for common user
    """
    chat_admin_list = bot.get_chat_administrators(message.chat.id)
    chat_admin_list = [x.user.id for x in chat_admin_list]
    if len(list(set(ADMIN_ID).intersection(set(chat_admin_list)))) > 0:
        if id in chat_admin_list:
            return True
    else:
        return False


@retry(tries=3)
def check_per_min():
    """check for updates from ZeroTier Web API
    """
    global pushed_node_id_list
    try:
        network_list = myZeroTier.get_network()
        for network in network_list:
            new_member_list = myZeroTier.get_network_member(
                network['id'], check_new_member=True)
            for new_member in new_member_list:
                if new_member['nodeId'] not in pushed_node_id:
                    send_msg = """*New member attached!*

networkId: `{}`
nodeId: `{}`
online: `{}`
""".format(new_member['networkId'], new_member['nodeId'], new_member['online'])
                    pushed_node_id[new_member['nodeId']] = {
                        'online': new_member['online']}
                    for group_id in groups_id_list:
                        bot.send_message(group_id, send_msg, reply_markup=new_member_options_markup(
                            new_member['networkId'], new_member['nodeId']), parse_mode="markdown")

                elif new_member['nodeId'] in pushed_node_id:
                    if pushed_node_id[new_member['nodeId']]['online'] != new_member['online']:
                        if pushed_node_id[new_member['nodeId']]['online'] == False:
                            send_msg = """*New member attached!*

networkId: `{}`
nodeId: `{}`
online: `{}`
""".format(new_member['networkId'], new_member['nodeId'], new_member['online'])
                            pushed_node_id[new_member['nodeId']
                                           ]['online'] = True
                            for group_id in groups_id_list:
                                bot.send_message(group_id, send_msg, reply_markup=new_member_options_markup(
                                    new_member['networkId'], new_member['nodeId']), parse_mode="markdown")
                        elif pushed_node_id[new_member['nodeId']]['online'] == True:
                            pushed_node_id[new_member['nodeId']
                                           ]['online'] = False
    except Exception as e:
        logger.error(e)


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
               InlineKeyboardButton("Ignore", callback_data="cb_ignore:{},{}".format(network_id, node_id)))
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


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    """Callback query function, define the InlineKeyboardButton callback

    Args:
        call ([type]): [description]
    """

    if call.data.split(":")[0] == "cb_accept":
        global pushed_node_id
        network_id = call.data.split(":")[1].split(",")[0]
        node_id = call.data.split(":")[1].split(",")[1]
        # check if button clicked by admin
        if is_chat_admin(call.message, call.from_user.id):
            json_data = myZeroTier.set_up_member(network_id, node_id)
            network_id = json_data['networkId']
            node_id = json_data['nodeId']
            member_name = "None" if len(
                json_data['name']) == 0 else json_data['name']
            member_ip = "None" if len(
                json_data['config']['ipAssignments']) == 0 else json_data['config']['ipAssignments'][0]
            msg = """*Member accepted by admin* @{}

NetworkId: `{}`
NodeId: `{}`
Name: `{}`
ManagedIPs: `{}`

_Set name by repling this message with your prefer name_""".format(call.from_user.username, network_id, node_id, member_name, member_ip)
            send_msg = bot.edit_message_text(
                msg, call.message.chat.id, call.message.id, reply_markup=None, parse_mode="markdown")
            bot.register_for_reply(
                send_msg, set_member_name, network_id, node_id)
            try:
                # delete node from dict after accepted
                pushed_node_id.pop(node_id)
            except:
                pass
        else:
            bot.answer_callback_query(call.id, "Admin only!")

    elif call.data.split(":")[0] == "cb_reject":
        network_id = call.data.split(":")[1].split(",")[0]
        node_id = call.data.split(":")[1].split(",")[1]
        if is_chat_admin(call.message, call.from_user.id):
            msg = """*Member rejected by admin* @{}

NetworkId: `{}`
NodeId: `{}`""".format(call.from_user.username, network_id, node_id)
            if myZeroTier.reject_member(network_id, node_id):
                bot.edit_message_text(msg, call.message.chat.id,
                                      call.message.id, reply_markup=None, parse_mode="markdown")
            try:
                pushed_node_id.pop(node_id)
            except:
                pass

    elif call.data.split(":")[0] == "cb_ignore":
        network_id = call.data.split(":")[1].split(",")[0]
        node_id = call.data.split(":")[1].split(",")[1]
        if is_chat_admin(call.message, call.from_user.id):
            msg = """*Member ignored by admin* @{}

NetworkId: `{}`
NodeId: `{}`""".format(call.from_user.username, network_id, node_id)
            bot.edit_message_text(msg, call.message.chat.id,
                                  call.message.id, reply_markup=None, parse_mode="markdown")

    elif call.data.split(":")[0] == "cb_network" or call.data.split(":")[0] == "cb_refresh_network_status" or call.data.split(":")[0] == "cb_show_ip":
        network_id = call.data.split(":")[1]
        member_list = myZeroTier.get_network_member(network_id)
        member_list = [
            {
                'name': i['name'],
                'online': i['online'],
                'authorized': i['config']['authorized'],
                'ipAssignments': i['config']['ipAssignments']
            }
            for i in member_list
        ]
        network_name = myZeroTier.get_network(
            network_id=network_id)['config']['name']
        send_msg = """Network *{}*:
-----------------------------------------------------------
🟢 -- _Online_  🔴 -- _Offline_
☑ -- _Authorized_  ◻ -- _Unauthorized_
-----------------------------------------------------------""".format(network_name.replace('_', '-'))
        for member in member_list:
            format_name = "None" if len(
                member['name']) == 0 else member['name'].replace('_', '-')
            format_ip = "None" if len(
                member['ipAssignments']) == 0 else member['ipAssignments'][0]
            if member['online'] == True and member['authorized'] == True:
                send_msg += "\n🟢☑ {}: `{}`".format(format_name, format_ip)
            elif member['online'] == False and member['authorized'] == True:
                send_msg += "\n🔴☑ {}: `{}`".format(format_name, format_ip)
            elif member['online'] == True and member['authorized'] == False:
                send_msg += "\n🟢◻ {}: `{}`".format(format_name, format_ip)
            elif member['online'] == False and member['authorized'] == False:
                send_msg += "\n🔴◻ {}: `{}`".format(format_name, format_ip)
        send_msg += """
-----------------------------------------------------------
_Updated at: {}_""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        bot.edit_message_text(
            send_msg, call.message.chat.id, call.message.id, reply_markup=network_member_options_markup(network_id, "ip"), parse_mode="markdown")

    elif call.data.split(":")[0] == "cb_show_node_id":
        network_id = call.data.split(":")[1]
        member_list = myZeroTier.get_network_member(network_id)
        member_list = [
            {
                'name': i['name'],
                'online': i['online'],
                'nodeId': i['nodeId'],
                'authorized': i['config']['authorized'],
            }
            for i in member_list
        ]
        network_name = myZeroTier.get_network(
            network_id=network_id)['config']['name']
        send_msg = """Network *{}*:
-----------------------------------------------------------
🟢 -- _Online_  🔴 -- _Offline_
☑ -- _Authorized_  ◻ -- _Unauthorized_
-----------------------------------------------------------""".format(network_name.replace('_', '-'))
        for member in member_list:
            format_name = "None" if len(
                member['name']) == 0 else member['name'].replace('_', '-')
            node_id = member['nodeId']
            if member['online'] == True and member['authorized'] == True:
                send_msg += "\n🟢☑ {}: `{}`".format(format_name, node_id)
            elif member['online'] == False and member['authorized'] == True:
                send_msg += "\n🔴☑ {}: `{}`".format(format_name, node_id)
            elif member['online'] == True and member['authorized'] == False:
                send_msg += "\n🟢◻ {}: `{}`".format(format_name, node_id)
            elif member['online'] == False and member['authorized'] == False:
                send_msg += "\n🔴◻ {}: `{}`".format(format_name, node_id)
        send_msg += """
-----------------------------------------------------------
_Updated at: {}_""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        bot.edit_message_text(
            send_msg, call.message.chat.id, call.message.id, reply_markup=network_member_options_markup(network_id, "node_id"), parse_mode="markdown")

    elif call.data == "cb_back" or call.data == "cb_refresh_network_list":
        json_data = myZeroTier.get_network()
        payload = [[x['config']['name'], x['config']['id']]
                   for x in json_data]  # [[network_name, network_id],...]
        send_msg = """*List of your networks:*
-----------------------------------------------------------"""
        for i in json_data:
            send_msg += "\n🌐 {}: `{}`".format(i['config']
                                              ['name'].replace('_', '-'), i['config']['id'].replace('_', '-'))
        send_msg += """-----------------------------------------------------------
_Updated at: {}_""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        bot.edit_message_text(send_msg, call.message.chat.id, call.message.id,
                              reply_markup=network_items_markup(payload), parse_mode="markdown")


@bot.message_handler(commands=['start'])
def start_command(message):
    if message.chat.type == "group":
        if message.from_user.id in ADMIN_ID:
            if message.chat.id not in groups_id_list:
                groups_id_list.append(message.chat.id)
                bot.send_message(
                    message.chat.id, "Bot started, group chat registed. /help")
    elif message.chat.type == "private":
        if message.chat.id in ADMIN_ID:
            bot.send_message(
                message.chat.id, "Add me to a group chat and /start me.")


@bot.message_handler(commands=['help'])
def help_commad(message):
    if message.chat.type == "group":
        help_text = '''*Following the commands below to use this bot:*

`/help`
_Show commands list._

`/show_network`
_Show your zerotier networks._

`/set_member_name network_id node_id`
_Set your member's name by using this command._

`/auth_member network_id node_id`
_Authorize a member._

`/unauth_member network_id node_id`
_Unauthorize a member._

`/delete_member network_id node_id`
_Delete a member._
'''
        bot.send_message(message.chat.id, help_text, parse_mode="markdown")
    elif message.chat.type == "private":
        if message.chat.id in ADMIN_ID:
            bot.send_message(
                message.chat.id, "Add me to a group chat and /start me.")


@bot.message_handler(commands=['show_network'])
def show_network_command(message):
    if is_chat_admin(message, message.from_user.id):
        json_data = myZeroTier.get_network()
        payload = [[x['config']['name'], x['config']['id']]
                   for x in json_data]  # [[network_name, network_id],...]
        send_msg = """*List of your networks:*
-----------------------------------------------------------"""
        for i in json_data:
            send_msg += "\n🌐 {}: `{}`".format(i['config']
                                              ['name'].replace('_', '-'), i['config']['id'].replace('_', '-'))
        send_msg += """-----------------------------------------------------------
_Updated at: {}_""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        bot.send_message(message.chat.id, send_msg,
                         reply_markup=network_items_markup(payload), parse_mode="markdown")


@bot.message_handler(commands=['set_member_name'])
def set_member_name_command(message):
    if is_chat_admin(message, message.from_user.id):
        if len(message.text.split(" ")[1:]) == 2:
            network_id = message.text.split(" ")[1]
            node_id = message.text.split(" ")[2]
            msg = bot.send_message(
                message.chat.id, "Set name by repling this message with your prefer name")
            bot.register_for_reply(
                msg, set_member_name, network_id=network_id, node_id=node_id)
    else:
        bot.send_message(message.chat.id, "Admin only!")


def set_member_name(message, network_id: str, node_id: str):
    if is_chat_admin(message, message.from_user.id):
        json_data = myZeroTier.set_up_member(
            network_id, node_id, name=message.text)
        if json_data['name'] == message.text:
            msg = """*Name changed by admin* @{}

networkId: `{}`
nodeId: `{}`
name: `{}`""".format(message.from_user.username, network_id, node_id, message.text)
            bot.send_message(message.chat.id, msg, parse_mode="markdown")
        else:
            bot.send_message(message.chat.id, "Failed.")
    else:
        bot.send_message(message.chat.id, "Admin only!")


@bot.message_handler(commands=['auth_member'])
def unauth_member_command(message):
    if is_chat_admin(message, message.from_user.id):
        if len(message.text.split(" ")[1:]) == 2:
            network_id = message.text.split(" ")[1]
            node_id = message.text.split(" ")[2]
            json_data = myZeroTier.set_up_member(
                network_id=network_id, node_id=node_id, authorized=True)
            if json_data['config']['authorized'] == True:
                msg = """*Member authorized by admin* @{}

networkId: {}
nodeId: {}""".format(message.from_user.username, network_id, node_id)
                bot.send_message(message.chat.id, msg, parse_mode="markdown")
            else:
                bot.send_message(message.chat.id, "Failed.")
    else:
        bot.send_message(message.chat.id, "Admin only!")


@bot.message_handler(commands=['unauth_member'])
def unauth_member_command(message):
    if is_chat_admin(message, message.from_user.id):
        if len(message.text.split(" ")[1:]) == 2:
            network_id = message.text.split(" ")[1]
            node_id = message.text.split(" ")[2]
            json_data = myZeroTier.set_up_member(
                network_id=network_id, node_id=node_id, authorized=False)
            if json_data['config']['authorized'] == False:
                msg = """*Member unauthorized by admin* @{}

networkId: {}
nodeId: {}""".format(message.from_user.username, network_id, node_id)
                bot.send_message(message.chat.id, msg, parse_mode="markdown")
            else:
                bot.send_message(message.chat.id, "Failed.")
    else:
        bot.send_message(message.chat.id, "Admin only!")


@bot.message_handler(commands=['delete_member'])
def delete_member_command(message):
    if is_chat_admin(message, message.from_user.id):
        if len(message.text.split(" ")[1:]) == 2:
            network_id = message.text.split(" ")[1]
            node_id = message.text.split(" ")[2]
            flag = myZeroTier.reject_member(
                network_id=network_id, node_id=node_id)
            if flag:
                msg = """*Member deleted by admin* @{}

networkId: {}
nodeId: {}""".format(message.from_user.username, network_id, node_id)
                bot.send_message(message.chat.id, msg, parse_mode="markdown")
            else:
                bot.send_message(message.chat.id, "Failed.")
    else:
        bot.send_message(message.chat.id, "Admin only!")
