#!/usr/bin/env python3

# Bluesky timeline live


login = ('your-handle-here','your-password-here')

interval = 60

play_sound = True


from atproto import Client
from os.path import abspath, dirname
from datetime import datetime, timezone
from time import sleep
from sys import exit
import re
if play_sound:
    from playsound3 import playsound


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
    elif days >= 1: return f'{days:.0f}d'
    elif hour >= 1: return f'{hour:.0f}h'
    elif mins >= 1: return f'{mins:.0f}m'
    else: return f'{secs:.0f}s'


# xterm formatting signals
def clear(): return '\r\x1B[K'
def fmt(code): return '\x1B[' + code + 'm'
def col(code): return fmt('38;5;' + code)


# colored regex matches
def match_fmt(text, pattern, FMT1, FMT2):
    p = re.compile(pattern, re.IGNORECASE)
    def color_str(match):
        return FMT1 + match.group() + FMT2
    return p.sub(color_str, text)


if __name__ == "__main__":

    # my path
    mypath = dirname(abspath(__file__))

    # new bluesky client
    print('connecting . . .')
    handle, password = login
    client = Client()
    client.login(handle, password)
    print('\n' + '🦋', 'Bluesky' + '\n')

    # main loop
    known_ids = []
    while True:

        # API: get the feed
        try: feed = client.get_timeline(limit=30).feed
        except Exception:
            try: sleep(interval)
            except KeyboardInterrupt: print(clear()); exit()
            continue

        # fill list of new messages
        new_messages = []
        for item in feed:
            # parse
            try:
                post = item.post
                id = post.cid
                handle = '@' + post.author.handle
                author = post.author.display_name.strip()
                if not author: author = handle
                text = post.record.text.strip()
                date = post.record.created_at
            except Exception as e:
                continue

            # real new post?
            if text and not (id in known_ids):
                new_messages.insert(0, (date,handle,author,text))
                known_ids.append(id)

        # process new messages
        now = datetime.now(tz=timezone.utc).astimezone()
        notify = False
        for msg in new_messages:
            date, handle, author, text = msg

            # calc time delta
            timedelta = ago(now - datetime.fromisoformat(date))

            # remove line breaks
            while 2*'\n' in text:
                text = text.replace(2*'\n', '\n')
            text = text.replace('\n', ' ')

            # message formatting
            author = col('33') + fmt('1') + author + fmt('')
            handle = col('33') + fmt('2') + handle
            timedelta += fmt('')

            # highlighted patterns
            pattern = r'^(NEWS?:|BREAKING|SCOOP|BOMBSHELL)\b'
            text = match_fmt(text, pattern, col('196'), fmt(''))

            # message output
            print(author, handle, '⋅', timedelta)
            print(text + '\n')
            notify = True

        # play sound
        if (play_sound and notify):
            playsound(mypath + '/incoming.m4a')

        # wait…
        try: sleep(interval)
        except KeyboardInterrupt: print(clear()); exit()
