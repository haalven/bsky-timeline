#!/usr/bin/env python3

# 🦋 timeline live

login = ('your-handle-here','your-password-here')


from bsky_connect import BskySession
from datetime import datetime, timezone
from time import time, sleep
from sys import exit
import re

# timedelta string
def ago(td):
    secs = td.total_seconds()
    mins, secs = divmod(secs, 60)
    hour, mins = divmod(mins, 60)
    days, hour = divmod(hour, 24)
    if days >= 365:
        years = days / 365.242
        return f'{years:.1f}y'
    elif days >= 30:
        months = days / 30.437
        return f'{months:.1f}mo'
    elif days >= 1:
        return f'{days:.0f}d'
    elif hour >= 1:
        return f'{hour:.0f}h'
    elif mins >= 1:
        return f'{mins:.0f}m'
    else:
        return f'{secs:.0f}s'

# colored regex matches
def match_fmt(text, pattern, FMT1, FMT2):
    p = re.compile(pattern, re.IGNORECASE)
    def color_str(match): return FMT1 + match.group() + FMT2
    return p.sub(color_str, text)


if __name__ == "__main__":

    # new API session
    handle, password = login
    session = BskySession(handle, password)

    # main loop
    known_ids = []
    while True:

        # API: get the feed
        try:
            response = session.api_call(endpoint='app.bsky.feed.getTimeline')
            feed = response['feed']
        except Exception:
            try: sleep(60)
            except KeyboardInterrupt: exit()
            continue

        # fill list of new messages
        new_messages = []

        for item in feed:
            if 'reply' in item: continue
            # parse
            try:
                post = item['post']
                id   = post['cid']
                text = post['record']['text'].strip()
                date = post['record']['createdAt']
                handle = '@' + post['author']['handle']
                author = post['author']['displayName'].strip()
                if not author: author = handle
            except Exception:
                continue

            # real new post?
            if text and not (id in known_ids):
                new_messages.insert(0, (id, date, handle, author, text))
                known_ids.append(id)

        # process new messages
        now = datetime.now(tz=timezone.utc).astimezone()

        for msg in new_messages:
            id, date, handle, author, text = msg

            # calc time delta
            timedelta = ago(now - datetime.fromisoformat(date))

            # remove empty lines
            while 2*'\n' in text: text = text.replace(2*'\n', '\n')

            # xterm formatting
            author = '\x1B[38;5;33m\x1B[1m' + author + '\x1B[m'
            handle = '\x1B[38;5;33m\x1B[2m' + handle + '\x1B[m'
            timedelta = '\x1B[38;5;33m\x1B[2m' + timedelta + '\x1B[m'
            pattern = r'^(NEWS?:|BREAKING|SCOOP|BOMBSHELL)\b'
            text = match_fmt(text, pattern, '\x1B[38;5;196m', '\x1B[m')

            # printing
            print(author, handle, '⋅', timedelta)
            print(text + '\n')

        # wait…
        try: sleep(60)
        except KeyboardInterrupt: exit()
