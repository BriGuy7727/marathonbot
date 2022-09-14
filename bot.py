import json
import os
from datetime import datetime
import copy

import discord
import requests
from discord.ext import tasks
from dotenv import load_dotenv

load_dotenv()
client = discord.Client(intents=discord.Intents.default())


def format_time(ts):
    try:
        newtime = datetime.strptime(ts, '%Y-%m-%dT%H:%M:%SZ').strftime("%m/%d/%Y")
        return newtime
    except TypeError:
        return ts


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    clean_channel = client.get_channel(958009642343075860)
    await clean_channel.purge()
    sub_messages.start()


@tasks.loop(hours=1)
async def sub_messages():
    if not os.path.exists('current_marathons.json'):
        with open('current_marathons.json', 'w') as newfile:
            newfile.write(json.dumps({}))
    with open('current_marathons.json') as marathon_file:
        marathon_dict = json.load(marathon_file)
    sub_channel = client.get_channel(958009642343075860)
    response = requests.get("https://oengus.io/api/marathons")
    x = json.loads(response.text)
    max_subs = len(x['open'])
    sub_num = 0
    check_list = []
    for xx, yy in x.items():
        if xx == "open":
            for z in yy:
                check_list.append(z['id'])
            for y, v in copy.deepcopy(marathon_dict).items():
                if y not in check_list:
                    message = await sub_channel.fetch_message(v['msg_id'])
                    await message.delete()
                    del marathon_dict[y]
            while sub_num < max_subs:
                embed = discord.Embed()
                current = yy[sub_num]
                if current['id'] in marathon_dict:
                    pass
                else:
                    details = requests.get(f"https://oengus.io/api/marathons/{current['id']}")
                    d = json.loads(details.text)
                    if current['onsite']:
                        try:
                            eventloc = ', '.join([current['location'], current['country']])
                        except TypeError:
                            eventloc = "Online"
                    else:
                        eventloc = "Online"
                    embed.title = f"{current['name']}"
                    embed.url = f'https://v1.oengus.io/marathon/{current["id"]}'
                    if d['description'] and len(d['description']) > 500:
                        embed.description = ''.join([str(d['description'])[0:500], "..."])
                    else:
                        embed.description = d['description']
                    embed.add_field(name='Start Date', value=format_time(current['startDate']))
                    embed.add_field(name="End Date", value=format_time(current['endDate']))
                    embed.add_field(name="Submissions Open Until", value=format_time(current['submissionsEndDate']),
                                    inline=False)
                    embed.add_field(name="Location", value=eventloc)
                    embed.add_field(name="Language", value=current['language'].upper())
                    embed.add_field(name="Max Runners", value=d['maxNumberOfScreens'])
                    if d['emulatorAuthorized']:
                        embed.add_field(name="Emulators Okay?", value="Yes")
                    else:
                        embed.add_field(name="Emulators Okay?", value="No")
                    if d['discordRequired']:
                        embed.add_field(name="Required to Join Discord?",
                                        value=''.join(["Yes\nhttps://discord.gg/", d['discord']]))
                    else:
                        embed.add_field(name="Required to Join Discord?", value="No")
                    embed.colour = discord.Colour.random()
                    sub_msg_id = await sub_channel.send(embed=embed)
                    marathon_dict[current['id']] = {"msg_id": sub_msg_id.id}
                sub_num += 1
    with open('current_marathons.json', 'w') as newfile:
        newfile.write(json.dumps(marathon_dict))


client.run(os.getenv('DISCORD_TOKEN'))
