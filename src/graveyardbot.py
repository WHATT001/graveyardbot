import discord, os, urllib.request, json, random, asyncio, requests, re, config
from discord.ext import tasks, commands
from osuapi import OsuApi, ReqConnector
from datetime import datetime

intents = discord.Intents.default()
intents.members = True
client = commands.Bot(command_prefix=config.prefix, intents=intents)

tmp_token=''
date=''

@client.event
async def on_ready():
    print("I'm ready")
    await client.change_presence(status=discord.Status.idle, activity=discord.Game(name="87th dimension"))

@client.event
async def on_member_join(member):
    channel = client.get_channel(config.join_channel)
    await member.add_roles(discord.utils.get(member.guild.roles, name="Newcomers"))
    await channel.send(f"{random.choice(config.greetings)}, {member.mention}\nUse `!verify <link-to-your-osu-profile>` to get verified!")

async def return_token():
    url = 'https://osu.ppy.sh/oauth/token'
    data = {'client_id': config.api_id,
            'client_secret': config.api_token,
            'grant_type': 'client_credentials',
            'scope': 'public'}
    
    if tmp_token:
        if datetime.now().timestamp() - date >= 86000:
            tmp_token = requests.post(url, data).json()
            date = datetime.now().timestamp()
            return tmp_token
        else:
            return tmp_token
    else:
        tmp_token = requests.post(url, data).json()
        date = datetime.now().timestamp()
        return tmp_token

@client.command()
async def user(ctx, user_id):
    '''User details. Use: !user <user_id>'''
    user = 'https://osu.ppy.sh/api/v2/users/'+user_id+'/osu'
    b = 'Bearer '+ return_token()
    response = requests.get(user, headers={'Authorization': b}).json()

    e = discord.Embed(title = f"User Details")
    e.add_field(name = "Username", value = response['username'])
    e.add_field(name = "Online", value = ':green_circle:' if response['is_online'] else ':red_circle:')
    e.add_field(name = "Country", value = response['country']['name'])
    e.add_field(name = "PP", value = response['statistics']['pp'])
    e.add_field(name = "Graveyarded Maps", value = response['graveyard_beatmapset_count'])
    e.add_field(name = "Ranked Maps", value = response['ranked_and_approved_beatmapset_count'])
    e.set_thumbnail(url=response['avatar_url'])
    await ctx.send(embed = e)

@client.command()
async def verify(ctx, link):
    '''Verify an user. Use: !verify <link_to_your_osu_profile>'''
    regex = re.search(r'(?P<id>\d+)', link)
    user = 'https://osu.ppy.sh/api/v2/users/'+regex.group('id')+'/osu'
    b = 'Bearer ' + return_token()
    response = requests.get(user, headers={'Authorization': b}).json()
    graved = response['graveyard_beatmapset_count']
    tainted = response['ranked_and_approved_beatmapset_count']

    # perhaps simplify this
    role1 = discord.utils.get(ctx.guild.roles, name="Graveyard Rookie (<5 Maps)")
    role2 = discord.utils.get(ctx.guild.roles, name="Graveyard Amateur (5-15 Maps)")
    role3 = discord.utils.get(ctx.guild.roles, name="Graveyard Adept (15-30 Maps)")
    role4 = discord.utils.get(ctx.guild.roles, name="Graveyard Veteran (30-50 Maps)")
    role5 = discord.utils.get(ctx.guild.roles, name="Graveyard Revenant (50+ Maps)")
    role6 = discord.utils.get(ctx.guild.roles, name="Tainted Mapper")

    if tainted > 0:
        await ctx.author.add_roles(role6)
    elif graved in range(0,5):
        await ctx.author.add_roles(role1)
    elif graved in range(5,15):
        await ctx.author.add_roles(role2)
    elif graved in range(15,30):
        await ctx.author.add_roles(role3)
    elif graved in range(30,50):
        await ctx.author.add_roles(role4)
    elif graved in range(50,666):
        await ctx.author.add_roles(role5)
    await ctx.author.remove_roles(discord.utils.get(ctx.guild.roles, name="Newcomers"))

    e = discord.Embed(title = f"User Verified!")
    e.add_field(name = "Username", value = response['username'], inline=False)
    avatar_url = response['avatar_url']
    if 'avatar-guest' in avatar_url:
        avatar_url = 'https://osu.ppy.sh' + avatar_url
    e.set_thumbnail(url=avatar_url)
    await ctx.send(embed = e)

@client.command()
async def roll(ctx):
    ''' Roll one of the three goblins. Use: !roll '''
    await ctx.send("You've rolled: "+random.choice(config.goblins))

### START DOWNLOAD FUNCTION
@client.command()
async def download(ctx, song):
    ''' Graveyard Gamer Maneuver™ '''
    await ctx.send(song)
### END DOWNLOAD FUNCTION

### START ADMIN FUNCTIONS
@client.command()
@commands.has_role("Admin")
async def kick(ctx, member:discord.Member):
    ''' Kicks a member. Use: !kick <@user> '''
    await member.kick()
    channel = client.get_channel(config.announce_channel)
    await channel.send("**User **" +"`"+(member.nick if member.nick else member.name)+"`"+ f"** {random.choice(config.kick_punishment)}** <:tux:775785821768122459>")

@client.command()
@commands.has_role("Admin")
async def ban(ctx, member:discord.Member):
    ''' Bans a member. Use: !ban <@user> '''
    await member.ban()
    channel = client.get_channel(config.announce_channel)
    await channel.send("**User **" +"`"+(member.nick if member.nick else member.name)+"`"+ f"** {random.choice(ban_punishment)}** <:tux:775785821768122459>")
### END ADMIN FUNCTIONS

client.run(config.discord_token)
