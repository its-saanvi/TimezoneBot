import os
import sqlite3
from parser import parse_message
import discord
from dotenv import load_dotenv
from discord import app_commands
from discord.ext import commands

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

conn = sqlite3.connect("timezone-bot.db")
table_name = "user_timezones"
bot = commands.Bot(command_prefix="$", intents=intents)


@bot.tree.command(name="timezone", description="Manage your current timezone")
@app_commands.choices(
    action=[
        app_commands.Choice(name="set", value="set"),
        app_commands.Choice(name="get", value="get"),
        app_commands.Choice(name="delete", value="delete"),
        app_commands.Choice(name="update", value="update"),
    ]
)
@app_commands.describe(
    action="Action to perform",
    timezone="Timezone to set in IANA database format e.g. America/New_York",
)
async def timezone(
    interaction: discord.Interaction, action: str, timezone: str | None = None
):
    await interaction.response.defer(ephemeral=True)
    user_id = interaction.user.id
    cursor = conn.cursor()
    if action == "set":
        if timezone is None:
            await interaction.followup.send(content="Please provide a timezone")
            return
        cursor.execute(
            f"INSERT INTO {table_name} (id, timezone) VALUES (?, ?)",
            (user_id, timezone),
        )
        conn.commit()
        await interaction.followup.send(
            content=f"Successfully set your timezone to {timezone}"
        )
    elif action == "get":
        cursor.execute(f"SELECT timezone FROM {table_name} WHERE id={user_id}")
        timezone = cursor.fetchone()[0]
        await interaction.followup.send(content=f"Your current timezone is {timezone}")
    elif action == "delete":
        cursor.execute(f"DELETE FROM {table_name} WHERE id={user_id}")
        conn.commit()
        await interaction.followup.send(content="Successfully deleted your timezone")
    elif action == "update":
        if timezone is None:
            await interaction.followup.send(content="Please provide a timezone")
            return
        cursor.execute(
            f"UPDATE {table_name} SET timezone=? WHERE id=?", (timezone, user_id)
        )
        conn.commit()
        await interaction.followup.send(
            content=f"Successfully updated your timezone to {timezone}"
        )
    cursor.close()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    cursor = conn.cursor()
    cursor.execute(
        f"CREATE TABLE IF NOT EXISTS {
            table_name
        } (id BIGINT PRIMARY KEY, timezone TEXT)"
    )
    conn.commit()
    cursor.close()
    await bot.tree.sync()


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    user_id = message.author.id
    cursor = conn.cursor()
    cursor.execute(f"SELECT timezone FROM {table_name} WHERE id={user_id}")
    fetches = cursor.fetchone()
    if fetches is None:
        cursor.close()
        return
    timezone = fetches[0]
    cursor.close()

    timezones = parse_message(message.content, timezone)

    message_content = ""
    for timezone in timezones:
        message_content += f"\n`{timezone.original_time}`: {timezone.unix_time}"

    if message_content == "":
        return

    await message.reply(message_content.strip())


bot.run(os.getenv("BOT_TOKEN"))
