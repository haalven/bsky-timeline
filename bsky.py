#!/usr/bin/env python3

# Bluesky timeline live


login = ('your-handle-here','your-password-here')

interval = 30 # seconds

play_sound = True


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
def ln_clear(): return '\r\x1B[K'
def fmt(code): return '\x1B[' + code + 'm'
def col(code): return fmt('38;5;' + code)


# colored regex matches
def match_fmt(text, pattern, FMT1, FMT2):
    def color_str(match):
        return FMT1 + match.group() + FMT2
    return pattern.sub(color_str, text)


if __name__ == "__main__":

    # my path
    mypath = dirname(abspath(__file__))

    # create bluesky client
    logo = chr(129419)
    print('\n' + logo, 'loading atproto...', end=' ', flush=True)
    from atproto import Client
    print(ln_clear() + logo, 'creating client...', end=' ', flush=True)
    handle, password = login
    try:
        client = Client()
        client.login(handle, password)
    except Exception as e:
        print(ln_clear() + 'client error:', str(e))
        exit()
    # success
    print(ln_clear() + logo, 'Bluesky' + '\n')

    # main loop
    known_ids = []
    while True:

        # API: get the feed
        try: feed = client.get_timeline(limit=20).feed
        except Exception:
            try: sleep(interval)
            except KeyboardInterrupt: print(ln_clear()); exit()
            continue

        # fill list of new messages
        new_messages = []
        for item in feed:
            # parse
            try:
                post = item.post
                if post.record.reply: continue
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
        new_posts = False
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

            # time critical
            pattern = r'^(NEWS?:|(JUST IN|BREAKING|SCOOP|BOMBSHELL)\b)'
            p = re.compile(pattern, re.IGNORECASE)
            if bool(p.search(text)):
                notify = True
                text = match_fmt(text, p, col('196'), fmt(''))

            # message output
            print(author, handle, '⋅', timedelta)
            print(text)
            new_posts = True

        # newline
        if new_posts: print()
        # notify sound
        if (play_sound and notify):
            playsound(mypath + '/incoming.m4a')

        # wait…
        try: sleep(interval)
        except KeyboardInterrupt:
            print(ln_clear(), end='')
            exit()
