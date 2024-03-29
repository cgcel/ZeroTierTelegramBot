# ZeroTierTelegramBot

**ZeroTierTelegramBot** is a telegram bot which helps you manage your [ZeroTier Network](https://my.zerotier.com/), runs on Python 3+. The API requests base on [ZeroTier Central API v1](https://apidocs.zerotier.com/).

## Bot Features

* Show networks info
* Show network members info
* Set member name (Admin only)
* Authorize new member (Admin only)
* Unauthorize member (Admin only)
* Delete member (Admin only)
* Set sub admin (Invite your friends to group chat, set as admin and manage the network with you)

## Getting Started

1. Create your own ZeroTier Web API Token:

    Create an API Access Token at: https://my.zerotier.com/account

2. Create your own Telegram Bot:

    Create a telegram bot by sending commands to @BotFather, feel free to send the commands descriptions below to @BotFather:

    ```
    help - Show commands list.
    show_network - Show your zerotier networks.
    set_member_name - Set your member's name by using this command.
    auth_member - Authorize a member.
    unauth_member - Unauthorize a member.
    delete_member - Delete a member.
    ```
    
    **When creating a bot, you need to specify:**

    - /setjoingroups -- enable
    - /setprivacy -- disable

3. Clone repository:

    ```
    $ git clone https://github.com/koonchung/ZeroTierTelegramBot.git
    ```

4. Install requirements:

    ```
    $ pip3 install -r requirements.txt
    ```

5. Edit `config.yaml`

    ```yaml
    # Fill with your telegram bot token
    # Create your bot by sending commands to @BotFather in Telegram
    bot_token: "your_bot_token"

    # Fill with your zerotier token
    # Get your own API Access Token at: https://my.zerotier.com/account
    zerotier_token: "your_zerotier_web_api_token"

    # Fill with telegram id which you want to set as admin
    admin_id:
       - your_telegram_id

    # Fill with refresh seconds, used to check new members
    refresh_seconds: 60
    ```

6. Run Bot

    ```
    $ cd ZeroTierTelegramBot
    $ python3 zerotiertelegrambot
    ```

    Invite your bot to a group chat, send `/start@your_bot` in group chat, and you can start to manage your ZeroTier Networks.

## Screenshots

1. start&help

    ![start&help](screenshots/start&help.png)

2. show_network

    ![show_network](screenshots/show_network.png)

3. network_info

    ![network_info](screenshots/network_info.png)

4. accept&setname

    ![accept&setname](screenshots/accept&setname.png)

5. auth&setname

    ![auth&setname](screenshots/auth&setname.png)

6. new_member

    ![new_member](screenshots/new_member.png)
