#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# author: elvin

import threading

from bot.zerotiertgbot import *

if __name__ == '__main__':
    schedule.every(REFRESH_SECONDS).seconds.do(check_per_min)
    threading.Thread(target=run_schedule, name="ScheduleThread").start()
    # bot.polling()
    bot.infinity_polling()
