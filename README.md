# ZeroTierTelegramBot

**ZeroTierTelegramBot** is a telegram bot which helps you manage your [ZeroTier Network](https://my.zerotier.com/), runs on Python 3+. The API requests base on [ZeroTier Central API v1](https://apidocs.zerotier.com/).

## Bot Features

* Show networks info
* Show network members info
* Set member name
* Authorize new member
* Unauthorize member
* Set sub admin (Invite your friends to manage the network with you)
* Show sub admin list
* Remove sub admin

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
    show_sub_admin - Show sub admin list.
    set_sub_admin - Set a telegram id as sub admin.
    remove_sub_admin - Remove a telegram id from sub admin.
    remove_all_sub_admins - Remove all sub admins.
    ```

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
    $ python3 bot
    ```


