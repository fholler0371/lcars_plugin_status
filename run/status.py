import asyncio
from datetime import datetime
from itertools import zip_longest
import socket
import sys
import pathlib
import tomllib
import yaml

from pprint import pprint


BERRY = """\033[1;32m   .~~.   .~~.    \033[1;36m
\033[1;32m  '. \ ' ' / .'\033[0;37m
\033[1;31m   .~ .~~~..~.    \033[0;37m
\033[1;31m  : .~.'~'.~. :   \033[0;37m
\033[1;31m ~ (   ) (   ) ~  \033[0;37m
\033[1;31m( : '~'.~.'~' : ) \033[0;37m
\033[1;31m ~ .~ (   ) ~. ~  \033[0;37m
\033[1;31m  (  : '~' :  )   \033[0;37m
\033[1;31m   '~ .~~~. ~'    \033[0;37m
\033[1;31m       '~'        \033[0;37m"""
WEEKDAYS = "Montag Dienstag Mitwoch Donnerstag Freitag Samstag Sontag".split(' ')
MONTHS = "Januar Februar März April Mai Juni Juli August September Oktober November Dezember".split(' ')
LEN = 15

async def last_login() -> str:
    p = await asyncio.subprocess.create_subprocess_shell('last -2 -a', 
                                                         stderr=asyncio.subprocess.PIPE, 
                                                         stdout=asyncio.subprocess.PIPE)
    out, _ = await p.communicate()
    out = out.decode()
    for _ in range(5):
        out = out.replace('  ',' ')
    out = out.split('\n')[0].split(' ')
    d = datetime.strptime(' '.join(out[2:6]), '%a %b %d %H:%M')
    return f'{WEEKDAYS[d.weekday()]}, {d.day} {MONTHS[d.month-1]} {d.hour}:{d.minute} von {out[9]}'

async def last_start() -> str:
    p = await asyncio.subprocess.create_subprocess_shell('uptime -s', 
                                                         stderr=asyncio.subprocess.PIPE, 
                                                         stdout=asyncio.subprocess.PIPE)
    out, _ = await p.communicate()
    out = out.decode().split('\n')[0]
    d = datetime.strptime(out, '%Y-%m-%d %H:%M:%S')
    return f'{WEEKDAYS[d.weekday()]}, {d.day} {MONTHS[d.month-1]} {d.hour}:{d.minute}'

async def uptime() -> str:
    p = await asyncio.subprocess.create_subprocess_shell('cat /proc/uptime', 
                                                         stderr=asyncio.subprocess.PIPE, 
                                                         stdout=asyncio.subprocess.PIPE)
    out, _ = await p.communicate()
    out = int(float(out.decode().split(' ')[0])) // 60
    line = f':{(out % 60) :0>2} Stunden'
    out = out // 60
    line = f'{(out % 24) :0>2}{line}'
    out = out // 24
    if out == 1:
        line = f'1 Tag {line}'
    elif out > 1:
        line = f'{out} Tage {line}'
    return line

async def lastavg() -> str:
    p = await asyncio.subprocess.create_subprocess_shell('cat /proc/loadavg', 
                                                         stderr=asyncio.subprocess.PIPE, 
                                                         stdout=asyncio.subprocess.PIPE)
    out, _ = await p.communicate()
    out = out.decode().split(' ')
    return f'{out[0].replace(".", ",")} (1 Min.) | {out[1].replace(".", ",")} (5 Min.) | {out[2].replace(".", ",")} (15 Min.)'

async def temperatur() -> str:
    p = await asyncio.subprocess.create_subprocess_shell('cat /sys/class/thermal/thermal_zone0/temp', 
                                                         stderr=asyncio.subprocess.PIPE, 
                                                         stdout=asyncio.subprocess.PIPE)
    out, _ = await p.communicate()
    out = int(out.decode().split('\n')[0])/1000
    out = f'{out:.1f}'
    return f'{out.replace(",", ".")} °C'

async def updates() -> str:
    p = await asyncio.subprocess.create_subprocess_shell('cat /sys/class/thermal/thermal_zone0/temp', 
                                                         stderr=asyncio.subprocess.PIPE, 
                                                         stdout=asyncio.subprocess.PIPE)
    out, _ = await p.communicate()
    out = int(out.decode().split('\n')[0])/1000
    out = f'{out:.1f}'
    return f'{out.replace(",", ".")} °C'

async def apt(cfg: dict) -> str:
    try:
        data_file = pathlib.Path(sys.argv[1]) / cfg.get('folder', {}).get('data', '') / 'apt.yaml'
        with data_file.open() as f:
            data = yaml.safe_load(f)
        return f'\033[1;33m{data["update_count"]}'
    except:
        return 'keine Daten.'

async def ram() -> str:
    p = await asyncio.subprocess.create_subprocess_shell('free --mega', 
                                                         stderr=asyncio.subprocess.PIPE, 
                                                         stdout=asyncio.subprocess.PIPE)
    out, _ = await p.communicate()
    out = out.decode().split('\n')
    info = ''
    for line in out:
        for _ in range(5):
            line = line.replace('  ',' ')
        if line.startswith('Speicher'):
            data = line.split(' ')
            info += f'Gesamt: {data[1]} | Belegt: {data[2]} | Frei: {data[3]} | Swap: '
        elif line.startswith('Swap'):
            info += line.split(' ')[2]
    return info

async def get_drive_data(drive: str) -> str:
    p = await asyncio.subprocess.create_subprocess_shell('df -h', 
                                                         stderr=asyncio.subprocess.PIPE, 
                                                         stdout=asyncio.subprocess.PIPE)
    out, _ = await p.communicate()
    out = out.decode().split('\n')
    info = ''
    for line in out:
        for _ in range(5):
            line = line.replace('  ',' ')
        if line.startswith(drive):
            data = line.split(' ')
            info = f'Gesamt: {data[1]} | Belegt: {data[2]} | Frei: {data[3]}'
    return info

async def network(net: dict) -> str:
    data = []
    for label, interface in net.items():
        p = await asyncio.subprocess.create_subprocess_shell(f'ifconfig {interface}', 
                                                            stderr=asyncio.subprocess.PIPE, 
                                                            stdout=asyncio.subprocess.PIPE)
        out, _ = await p.communicate()
        out = out.decode().split('\n')
        for line in out:
            for _ in range(5):
                line = line.replace('  ',' ')
            if line.startswith(' inet '):
                data.append(f'{label}: \033[1;35m{line.split(" ")[2]}\033[0;37m')
    return ' | '.join(data)

async def main() -> None:
    cfg_file = pathlib.Path(sys.argv[1]) / 'config' / 'config.toml'
    try:
        with cfg_file.open('rb') as f:
            cfg = tomllib.load(f)
    except:
        return
    info : list = []
    now = datetime.now()
    info.append(f"{WEEKDAYS[now.weekday()]}, {now.day} {MONTHS[now.month-1]} {now.year}")
    info.append('')
    info.append(f'{"Hostname" :.<{LEN}}: \033[1;33m{socket.getfqdn()}')
    results = []
    async with asyncio.TaskGroup() as tg:
        results.append(('Letzter Login', tg.create_task(last_login())))
        results.append(('Laufzeit', tg.create_task(uptime())))
        results.append(('Letzter Start', tg.create_task(last_start())))
        results.append(('Ø Auslastung', tg.create_task(lastavg())))
        results.append(('Temperatur', tg.create_task(temperatur())))
        results.append(('Updates', tg.create_task(apt(cfg))))
        results.append(('RAM (MB)', tg.create_task(ram())))
        for plugin in cfg.get('plugins', ''):
            if plugin.get('name', '') == 'status':
                for label, drive in plugin.get('drive', {}).items():
                    results.append((f'Ordner ({label})', tg.create_task(get_drive_data(drive))))
                if 'net' in plugin:
                    results.append((f'IP-Adressen', tg.create_task(network(plugin['net']))))
    for result in results:
        if result[1].result() is not None:
            info.append(f'{result[0]:.<{LEN}}: {result[1].result()}')
    for line in zip_longest(BERRY.split('\n'), info):
        print(f'{"                  " if line[0] is None else line[0]}{"" if line[1] is None else line[1]}')
    print('')

if __name__ == '__main__':
    asyncio.run(main())
    
#uptime -s