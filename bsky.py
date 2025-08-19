#!/usr/bin/env python3

# Bluesky timeline live
# usage: bsky.py [--critical] [--silent]

# https://github.com/MarshalX/atproto
# https://atproto.blue/en/latest/atproto_client/client.html


import sys, os.path, tomllib, argparse, re, time
from datetime import datetime, timezone


# read TOML file
def read_configuration(my_dir, my_name):
    config_file = os.path.splitext(my_name)[0] + '.toml'
    config_path = os.path.join(my_dir, config_file)
    try:
        with open(config_path, 'rb') as f:
            return tomllib.load(f)
    except: return None


# parse arguments
def get_arguments(my_name):
    parser = argparse.ArgumentParser(prog=my_name)
    parser.add_argument('--critical',
                        action='store_true',
                        help='print critical posts only',
                        required=False)
    parser.add_argument('--silent',
                        action='store_true',
                        help='no sound',
                        required=False)
    return parser.parse_args()


# timedelta
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


# xterm formatting
def ln_clear(): return '\r\x1B[K'
def f(code): return '\x1B[' + str(code) + 'm'
def c(code): return f('38;5;' + str(code))


# colored re matches
def match_fmt(text, pattern, FMT1, FMT2):
    def color_str(match):
        return FMT1 + match.group() + FMT2
    return pattern.sub(color_str, text)


# filter characters
def char_filter(text):
    whitelist_pattern = r'[^' \
        r'\s\n' \
        r'\u0020-\u007e' \
        r'\u00a0-\u200a' \
        r'\u2010-\u22ff' \
        r'\u2c00-\ufdff' \
        r']'
    return re.sub(whitelist_pattern, '', text)


# collapse whitespace
def collapse_whitespace(text):
    return re.sub(r'\s+', '\x20', text).strip()


# typing effect
def typer(text, delay=0.001):
    for c in text:
        print(c, end='', flush=True)
        time.sleep(delay)
    print()


def main():

    # my path
    my_path = os.path.abspath(__file__)
    my_dir  = os.path.dirname(my_path)
    my_name = os.path.basename(my_path)

    # get arguments
    arguments = get_arguments(my_name)

    # load configuration file
    config = read_configuration(my_dir, my_name)
    # set up handle
    try:
        login = (str(config['login_user']),
                 str(config['login_pass']))
    except:
        return 'error: handle missing'
    # set up interval
    try:
        interval = int(config['interval'])
    except:
        interval = 60
    # set up sound
    try:
        enable_sound = bool(config['enable_sound'])
    except:
        enable_sound = True
    if enable_sound:
        from playsound3 import playsound
    # set up typing effect
    try:
        enable_typing = bool(config['typing_effect'])
    except:
        enable_typing = True
    # set up logging
    try:
        log_folder = str(config['log_folder'])
        if log_folder == '':
            log_folder = None
        elif not os.path.isdir(log_folder):
            return 'error: log_folder: ' + str(log_folder)
    except: log_folder = None

    # create bsky client
    logo = chr(129419)
    print('\n' + logo, 'loading atproto...', end=' ', flush=True)
    try:
        from atproto import Client
    except Exception as e:
        print(ln_clear())
        return 'atproto error: ' + str(e)
    print(ln_clear() + logo, 'creating client...', end=' ', flush=True)
    try:
        handle, password = login
        client = Client()
        profile = client.login(handle, password)
    except Exception as e: # crash
        print(ln_clear())
        return 'client error: ' + str(e)
    # client success
    print(ln_clear() + logo, '@' + profile['handle'] + '\n')

    # main loop
    known_ids = []
    while True:

        # get the feed
        try:
            feed = client.get_timeline(limit=20).feed
        except Exception: # wait
            try:
                time.sleep(interval)
            except KeyboardInterrupt:
                print(ln_clear())
                return 0
            continue

        # fill list of new messages
        new_messages = []
        for item in feed:
            # parse feed
            try:
                post = item.post
                if post.record.reply:
                    continue
                reposter = '@'+item.reason.by.handle if item.reason else None
                id = post.cid
                handle = post.author.handle
                if not handle:
                    continue
                handle = '@' + handle
                author = post.author.display_name.strip()
                if not author:
                    author = handle
                text = post.record.text.strip()
                date = post.record.created_at
            except Exception as e:
                continue

            # a real new post?
            if text and not (id in known_ids):
                new_messages.insert(0, (date,reposter,handle,author,text))
                known_ids.append(id)

        # process new messages
        now = datetime.now(tz=timezone.utc).astimezone()
        log_name = 'bsky_' + now.strftime('%Y-%m-%d') + '.log'
        log = os.path.join(log_folder, log_name) if log_folder else None
        new_criticals = False

        for msg in new_messages:
            # expand msg
            date, reposter, handle, author, text = msg

            # datetime object
            timestamp = datetime.fromisoformat(date).astimezone()

            # text processing
            # remove color symbols
            author = char_filter(author)
            text = char_filter(text)
            # preserve newlines in text
            text = text.replace('\n', '\\n')
            # collapse whitespace
            author = collapse_whitespace(author)
            text = collapse_whitespace(text)

            # log message
            if log:
                line = timestamp.isoformat() + '\x20' + handle + '\x20' + text + '\n'
                with open(log, 'a') as logfile:
                    logfile.write(line)

            # calculate timedelta
            timedelta = ago(now - timestamp)

            # terminal formatting
            if reposter:
                reposter = '⇄ Reposted by ' + reposter
                reposter = c(33) + f(2) + reposter + f(0)
            author = c(33) + f(1) + author + f(0)
            handle = c(33) + f(2) + handle
            timedelta += f(0)

            # detect and format critical
            critical = False
            pattern = r'^(BREAKING|BOMBSHELL|SCOOP|NEW)\b'
            p = re.compile(pattern, re.IGNORECASE)
            if bool(p.search(text)):
                critical, new_criticals = True, True
                text = match_fmt(text, p, c(196), f(0))

            # new lines format
            text = text.replace('\\n', f(2) + '⮐' + f(22) + '\n')

            # print message
            if arguments.critical and (not critical):
                continue
            if reposter:
                print(reposter)
            print(author, handle, '⋅', timedelta)
            if enable_typing:
                typer(text + '\n')
            else:
                print(text + '\n')

        # notify sound
        if enable_sound and (not arguments.silent) and new_criticals:
            try:
                playsound(os.path.join(my_dir, 'incoming.m4a'), block=False)
            except Exception:
                pass

        # wait…
        try:
            time.sleep(interval)
        except KeyboardInterrupt:
            print(ln_clear(), end='')
            return 0


if __name__ == '__main__':
    sys.exit(main())
