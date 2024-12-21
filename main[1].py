import discord
from discord import Interaction, app_commands
from discord.ext import commands
from discord.ui import Button, View
import os
import time

# Define the bot and intents
intents = discord.Intents.default()
intents.message_content = True  # Enable intent for reading message content
intents.members = True  # Enable intent to read member details (for infractions)
bot = commands.Bot(command_prefix="!", intents=intents)

# Retrieve the bot token from Replit Secrets
bot_token = os.getenv('BOT_TOKEN')
if not bot_token:
    raise ValueError("Bot token not found. Please set it in the Replit Secrets Manager.")

# Define channel IDs and other constants
review_channel_id = 1317772119731343400  # Replace with the desired review channel's ID
infraction_channel_id = 1317772125972725802  # Replace with the desired infraction logs channel ID
session_channel_id = 1261160972413042718  # Replace with the session announcement channel ID
SESSION_COLOR = discord.Color(int("2b2d31", 16))  # Dark Gray for session-related commands
DEFAULT_COLOR = discord.Color(0xFFFFFF)  # White color for other commands

# Voting class that tracks votes and user votes
class VotingView(View):
    def __init__(self):
        super().__init__()
        self.votes = 0  # Initial vote count
        self.voted_users = set()  # A set of user IDs who have voted

    @discord.ui.button(label="Vote", style=discord.ButtonStyle.primary)
    async def vote_button(self, interaction: discord.Interaction, button: Button):
        user_id = interaction.user.id

        if user_id in self.voted_users:  # If user has already voted, remove their vote
            self.voted_users.remove(user_id)
            self.votes -= 1
            await interaction.response.edit_message(content=f"Vote removed! Total votes: {self.votes}")
        else:  # If user has not voted, add their vote
            self.voted_users.add(user_id)
            self.votes += 1
            await interaction.response.edit_message(content=f"Vote received! Total votes: {self.votes}")

    @discord.ui.button(label="Check Voters", style=discord.ButtonStyle.grey)
    async def check_voters(self, interaction: discord.Interaction, button: Button):
        # Show total votes in an ephemeral message
        await interaction.response.send_message(
            content=f"Total votes: {self.votes}",
            ephemeral=True  # This makes the response only visible to the user who clicked
        )

# Slash command for /review with a select menu for rating
@bot.tree.command(name="review", description="Submit a review with a rating and feedback.")
@app_commands.describe(
    user="The user you're reviewing",
    rating="Rating out of 5 stars",
    feedback="Your feedback for the user"
)
async def review(interaction: discord.Interaction, user: discord.User, rating: int, feedback: str):
    # Ensure the rating is between 1 and 5
    if rating < 1 or rating > 5:
        await interaction.response.send_message("Please provide a rating between 1 and 5 stars.", ephemeral=True)
        return

    # Create the embed for the review (with white color)
    embed = discord.Embed(
        title=f"Review for {user.name}",
        description=f"**Feedback**: {feedback}",
        color=discord.Color(0xFFFFFF)  # White color
    )
    embed.add_field(name="Rating", value="⭐" * rating + " " * (5 - rating), inline=False)  # Stars as per the rating
    embed.set_footer(text=f"Review submitted by {interaction.user.name}", icon_url=interaction.user.avatar.url)

    # Set the user's avatar as the thumbnail
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1289883319634366498/1316697817498259486/f65e9627e8284318956fcf28c6ec82be.png?ex=67653866&is=6763e6e6&hm=939f9f0ceb0ab84706c7686a00eb1c05fa5249cb9229a2d2b31e7b3cdf1b5e91&")

    # Get the specific channel where the review should be sent
    channel = bot.get_channel(review_channel_id)

    # Check if the channel is valid
    if channel:
        # Send the review embed to the specified channel
        await channel.send(content=f"{user.mention}", embed=embed)
        # Acknowledge the command
        await interaction.response.send_message(f"Review submitted for {user.mention}!", ephemeral=True)
    else:
        await interaction.response.send_message("Could not find the specified review channel. Please check the channel ID.", ephemeral=True)

# Slash command for /ping with the white embed color
@bot.tree.command(name="ping", description="Get the bot's ping and latency stats.")
async def ping(interaction: discord.Interaction):
    # Capture the time when the message is sent to measure round trip latency
    start_time = time.time()

    # Check the bot's latency from the Discord API
    api_latency = round(bot.latency * 1000)  # bot.latency is in seconds

    # Measure message round trip (approximate)
    message_latency = round((time.time() - start_time) * 1000)  # in ms

    # Simulate database latency
    db_latency = query_database()

    # Create an embed with the latency stats (with white color)
    embed = discord.Embed(
        title="Bot Latency Stats",
        description="Here are the current latency and performance metrics for the bot!",
        color=discord.Colour(0xFFFFFF)  # White color
    )
    embed.add_field(name="Message Latency", value=f"{message_latency}ms", inline=False)
    embed.add_field(name="Message Round Trip", value=f"{message_latency}ms", inline=False)
    embed.add_field(name="Shard Latency", value=f"{api_latency}ms", inline=False)
    embed.add_field(name="Database Latency", value=f"{db_latency}ms", inline=False)

    # Set a custom image thumbnail for the ping embed
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1289883319634366498/1316697817498259486/f65e9627e8284318956fcf28c6ec82be.png?ex=67653866&is=6763e6e6&hm=939f9f0ceb0ab84706c7686a00eb1c05fa5249cb9229a2d2b31e7b3cdf1b5e91&")  # Customize this URL

    # Send the response as an embed
    await interaction.response.send_message(embed=embed)

# Slash command for /infract to log user infractions with selectable infraction type
@bot.tree.command(name="infract", description="Infraction system for staff.")
@app_commands.describe(
    user="The user you're logging an infraction for",
    infraction_type="Choose the infraction of the user",
    reason="The reason for the infraction"
)
async def infract(interaction: discord.Interaction, user: discord.User, infraction_type: str, reason: str):
    # Infraction choices
    infraction_options = ["Notice", "Warning", "Strike", "Termination", "Blacklist", "Suspension"]

    # Create the embed for the infraction
    embed = discord.Embed(
        title=f"Infraction: {infraction_type} for {user.name}",
        description=f"**Reason**: {reason}",
        color=discord.Color(0xFFFFFF)  # White color
    )
    embed.add_field(name="Important Notice", value="This user has violated one or more of our guidelines. The infraction is logged accordingly.", inline=False)
    embed.add_field(name="Infraction Type", value=infraction_type, inline=False)
    embed.add_field(name="Issued by", value=interaction.user.name, inline=False)

    # Get the infraction log channel
    infraction_channel = bot.get_channel(infraction_channel_id)
    if infraction_channel:
        await infraction_channel.send(content=f"{user.mention}", embed=embed)
        await interaction.response.send_message(f"Infraction logged for {user.mention}!", ephemeral=True)
    else:
        await interaction.response.send_message("Could not find the infraction logs channel. Please check the channel ID.", ephemeral=True)

# Session voting command
@bot.tree.command(name="sessionvote", description="Start a session vote.")
async def sessionvote(interaction: discord.Interaction):
    embed = discord.Embed(
        title=":Bell: Session Vote",
        description=("Our high-ranking team has started a session poll, 7 votes are required to start a session."),
        color=SESSION_COLOR
    )
    embed.add_field(name="Owner", value="Shadow43059", inline=False)
    embed.add_field(name="Server", value="New York State Roleplay | New | Strict", inline=False)
    embed.add_field(name="Server Code", value="nysxx", inline=False)

    # Create a voting view and send it to the channel
    view = VotingView()
    channel = bot.get_channel(session_channel_id)
    if channel:
        message = await channel.send(content="@here", embed=embed, view=view)
        await interaction.response.send_message("Session vote announcement sent!", ephemeral=True)
    else:
        await interaction.response.send_message("Session announcement channel not found.", ephemeral=True)

# Event triggered when the bot is ready
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")
    await bot.tree.sync()
    print(f"Slash commands synchronized.")
    await bot.change_presence(activity=discord.Game(name="Session Management"))

# Run the bot
bot.run(bot_token)
