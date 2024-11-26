#!/usr/bin/env python3


# Bluesky timeline live
# usage: bsky [--critical]

# https://github.com/MarshalX/atproto
# https://atproto.blue/en/latest/atproto_client/client.html


login = ('your-handle-here','your-password-here')

interval = 30 # seconds

play_sound = True


import argparse
import re
from sys import argv, exit
from os.path import abspath, dirname, basename
from datetime import datetime, timezone
from time import sleep
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

    # argument
    myname = basename(argv[0])
    parser = argparse.ArgumentParser(prog=myname)
    parser.add_argument('--critical',
                        action='store_true',
                        help='print critical posts only',
                        required=False)
    args = parser.parse_args()
    critical_only = args.critical

    # my path
    mypath = dirname(abspath(__file__))

    # create bluesky client
    logo = chr(129419)
    print('\n' + logo, 'loading atproto...', end=' ', flush=True)
    try:
        from atproto import Client
    except Exception as e:
        print(ln_clear())
        exit('atproto error: ' + str(e))
    print(ln_clear() + logo, 'creating client...', end=' ', flush=True)
    try:
        handle, password = login
        client = Client()
        profile = client.login(handle, password)
    except Exception as e:
        print(ln_clear())
        exit('client error: ' + str(e))
    # client success
    print(ln_clear() + logo, profile['handle'] + '\n')

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
            # parse feed
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

            # a real new post?
            if text and not (id in known_ids):
                new_messages.insert(0, (date,handle,author,text))
                known_ids.append(id)

        # process new messages
        now = datetime.now(tz=timezone.utc).astimezone()
        new_posts, new_criticals = False, False
        for msg in new_messages:
            date, handle, author, text = msg

            # calculate timedelta
            timedelta = ago(now - datetime.fromisoformat(date))

            # remove newlines
            while 2*'\n' in text:
                text = text.replace(2*'\n', '\n')
            text = text.replace('\n', ' ')

            # message formatting
            author = col('33') + fmt('1') + author + fmt('')
            handle = col('33') + fmt('2') + handle
            timedelta += fmt('')

            # detect critical
            critical = False
            pattern = r'^(NEW:|(NEWS|JUST IN|BREAKING|SCOOP|BOMBSHELL)\b)'
            p = re.compile(pattern, re.IGNORECASE)
            if bool(p.search(text)):
                critical, new_criticals = True, True
                text = match_fmt(text, p, col('196'), fmt(''))

            # print message
            if critical_only and (not critical): continue
            new_posts = True
            print(author, handle, '⋅', timedelta)
            print(text)

        # newline
        if new_posts: print()
        # notify sound
        if play_sound and new_criticals:
            playsound(mypath + '/incoming.m4a')

        # wait…
        try: sleep(interval)
        except KeyboardInterrupt:
            print(ln_clear(), end='')
            exit()
