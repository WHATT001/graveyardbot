import discord, os, urllib.request, json, random, asyncio, requests, re, config
from discord.ext import tasks, commands
from osuapi import OsuApi, ReqConnector
from datetime import datetime
import musicbrainzngs as mb

intents = discord.Intents.default()
intents.members = True
client = commands.Bot(command_prefix=config.prefix, intents=intents)

tmp_token=''
date=''

async def return_token():
    '''return temporary token / retrieve new token'''
    global tmp_token
    global date
    url = 'https://osu.ppy.sh/oauth/token'
    data = {'client_id': config.api_id,'client_secret': config.api_token,'grant_type': 'client_credentials','scope': 'public'}
    
    if tmp_token:
        if datetime.now().timestamp() - date >= 86000:
            print("Token older than 30 seconds, retrieving new one")
            tmp_token = requests.post(url, data).json()
            date = datetime.now().timestamp()
            return tmp_token['access_token']
        else:
            print("Using token retrieved earlier")
            return tmp_token['access_token']
    else:
        print("Retrieving new token")
        tmp_token = requests.post(url, data).json()
        date = datetime.now().timestamp()
        return tmp_token['access_token']

@client.event
async def on_ready():
    print("I'm ready")
    await client.change_presence(status=discord.Status.idle, activity=discord.Game(name="87th dimension"))

@client.event
async def on_member_join(member):
    channel = client.get_channel(config.join_channel)
    await member.add_roles(discord.utils.get(member.guild.roles, name="Newcomers"))
    await channel.send(f"{random.choice(config.greetings)}, {member.mention}\nUse `!verify <osu_username>` to get verified!")

@client.command()
async def user(ctx, user_id):
    '''User details. Use: !user <osu_username>'''
    response = requests.get('https://osu.ppy.sh/api/v2/users/'+user_id+'/osu', headers={'Authorization': 'Bearer '+ await return_token()}).json()
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
async def verify(ctx, user):
    '''Verify an user. Use: !verify <osu_username>'''
    response = requests.get('https://osu.ppy.sh/api/v2/users/'+user+'/osu', headers={'Authorization': 'Bearer ' + await return_token()}).json()
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
async def download(ctx, *, input: str):
    ''' Graveyard Gamer Maneuver™ '''
    args = input.split()
    mb.set_useragent("GraveyardBot", "8.7", "beatmaster@beatconnect.io")
    result = mb.search_recordings(query=" AND ".join(args), limit=5)
    print(json.dumps(result, indent=4))
    song_title = result["recording-list"][0]["title"]
    artist_name = result["recording-list"][0]["artist-credit"][0]["name"]
    album_title = result["recording-list"][0]["release-list"][0]["release-group"]["title"]
    found = False
    e = discord.Embed(title = f"Song Found!")
    for release in result["recording-list"][0]["release-list"]:
        try:
            cover_art = mb.get_image_list(release["id"])
            link = requests.get(cover_art["images"][0]["thumbnails"]["small"])
            print(json.dumps(cover_art, indent=4))
            print(link.url)
            e.set_thumbnail(url=link.url)
            found = True
            break
        except Exception:
            pass
    if not found:
        print("cover art not found")
    print(song_title)
    print(artist_name)
    print(album_title)
    e.add_field(name = "Title", value = song_title, inline = False)
    e.add_field(name = "Artist", value = artist_name, inline = False)
    e.add_field(name = "Album", value = album_title, inline = False)
    await ctx.send(embed = e)
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
