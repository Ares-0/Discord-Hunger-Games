import aiohttp
import discord
import io

from discord.ext import commands

class Greetings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # Say hi
    @commands.command()
    async def greetings(self, ctx):
        await ctx.send("Hello, {0}".format(ctx.author.mention))

    # Repeats the argument given
    @commands.command()
    async def echo(self, ctx, *args):
        await ctx.send(' '.join(args))

    @commands.command()
    async def test_args(self, ctx, *args):
        await ctx.send('{} arguments: {}'.format(len(args), ', '.join(args)))

    # example embed
    @commands.command()
    async def embed(self, ctx, arg):
        embedVar = discord.Embed(title=arg, color=0x0000ff, description="Some decription here <@!250522471227195393>")
        embedVar.set_image(url='https://i.imgur.com/wSTFkRM.png')
        await ctx.send(embed=embedVar)

    # example embed everything
    @commands.command()
    async def embed_full(self, ctx, arg):
        embedVar = discord.Embed(title=arg, color=0x00ff00, url='https://discord.js.org/', description="Some description here")
        embedVar.add_field(name="Field1", value="hi", inline=True)
        embedVar.add_field(name="Field2", value="hi2", inline=True)
        str = "https://i.imgur.com/wSTFkRM.png"
        embedVar.set_image(url='https://i.imgur.com/wSTFkRM.png')
        embedVar.set_image(url="https://media0.giphy.com/media/W5C9c8nqoaDJWh34i6/giphy.gif")
        embedVar.set_thumbnail(url=str)
        embedVar.set_author(name="Some author", url='https://discord.js.org/', icon_url="https://i.imgur.com/wSTFkRM.png")
        embedVar.set_footer(text='Some footer text here', icon_url='https://discord.js.org/')
        await ctx.send(embed=embedVar)

    # pulling images from imgur
    @commands.command()
    async def image2(self, ctx):
        async with ctx.typing():
            async with aiohttp.ClientSession() as session:
                async with session.get("https://i.imgur.com/KIdt2hYb.png") as resp:
                    if resp.status != 200:
                        return await ctx.send('Could not download file...')
                    data = io.BytesIO(await resp.read())
                    await ctx.send(file=discord.File(data, 'cool_image.png'))

async def setup(bot):
    await bot.add_cog(Greetings(bot))
