"""
MIT License

Copyright (c) 2025 Ammar Abbas

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os
import re
from typing import Any, Optional, Union
from dotenv import load_dotenv

import discord
from discord.ext import commands

# Stable fork of Google Translate API
from deep_translator import GoogleTranslator, single_detection

# Trig and rounding support for calculate command
from math import floor, ceil, sqrt, pi, sin, cos, tan, asin, acos, atan, \
                degrees as deg, radians as rad


def fetch_key(key_name: str,
            err_msg: Optional[str] = "Error in fetching keys",
            err_code: Optional[int] = -1,
            to_int: Optional[bool] = False) -> Union[str, int]:
    """
    Fetches a system environment variable and concatenates it to an integer if
    desired.
    
    If the variable is not found, then the program is terminated and a custom
    error message and exit code are returned.
    
    Args:
        key_name (str): Key name of the environment variable
        err_code (Optional[int]): Exit code to terminate program with in case
        of error.
        err_msg (Optional[str]): Error message to display if there is a key
        error.
        to_int (Optional[bool]): Controls concatenation to int. Leaving this
        as False returns the key as a string.
        
    Returns:
        Union[str, int]: Returns the key as either a string or int or stops
        the program and returns an error message if the key isn't accessible.
    """
    # Attempt to access the key
    try:
        key = os.getenv(key_name)
    
        # Handle nonexistent key
        if key == None:
            print(f"{err_msg}\nError: Key Does Not Exist")
            raise SystemExit(err_code)
    
        # Converts key to int if necessary and returns
        if to_int:
            try:
                return int(key)
            except ValueError as e:
                print(f"{err_msg}\nError: Concatenation Failed\n{e}")
                raise SystemExit(err_code)
        return key
    # Handle unknown errors
    except Exception as e:
        print(f"{err_msg}\nError: Unknown\n{e}")
        raise SystemExit(err_code)


def key_from_value(dictionary: dict[Any, Any], 
                value: Any) -> Union[str, None]:
    """
    Returns the key associated with a given value in a dictionary.
    """
    # Searches dictionary, returns key if found
    for item in dictionary.items():
        if value == item[1]:
            return item[0]
    
    # Return None if key is not found
    return None


# Fetch keys
load_dotenv()

TOKEN = fetch_key("BOT_TOKEN", "BOT TOKEN ERROR", 1)
ID = fetch_key("BOT_ID", "BOT ID ERROR", 2, True)
TRANSLATE_API_KEY = fetch_key("LANGUAGE_DETECTION_API_KEY", "API KEY ERROR", 3)

# Get supported languages for translation
LANGUAGES = GoogleTranslator().get_supported_languages(as_dict=True)
# Max character length of a Discord message
MAX_MESSAGE_LENGTH = 2000

# Create bot object
bot = commands.Bot(command_prefix="-", intents=discord.Intents.all())


async def return_message(ctx, content: str) -> discord.Message:
    """
    Returns translation of a message in chunks of 2000 characters to prevent
    message from being blocked by Discord's max character limit.
    
    Returns:
        Message(s) on Discord
    """
    # Make the first chunk a reply
    await ctx.message.reply(content[0:MAX_MESSAGE_LENGTH])
    # Send all other chunks
    for i in range(MAX_MESSAGE_LENGTH, len(content), MAX_MESSAGE_LENGTH):
        await ctx.send(content[i:i+MAX_MESSAGE_LENGTH])


@bot.command()
async def h(ctx) -> discord.Message:
    """
    Prints a list of available commands, how to use them, and their
    descriptions.
    """
    # send message
    return await ctx.message.reply("""```
LIST OF COMMANDS:
==========================================================================================================
| Name      | Command           | Usage                           | Description                          |
|========================================================================================================|
| Help      | -h                | -h                              | Print this message                   |
| Translate | -t <translate_to> | Use while replying to a message | Translate a message                  |
| Languages | -l                | -l                              | Prints a list of supported languages |
| Calculate | -c <equation>     | -c <equation>                   | Calculate an arithmetic equation     |
| Echo      | -e <string>       | -e <string>                     | Echo a message                       |
```""")


def get_lang_code(dest_lang: str) -> Union[str, None]:
    """
    Converts user's desired destination language into its postal code for
    compatibility with the program.
    
    Args:
        lang (str): Language that the user wants to translate to.
        
    Returns:
        Union[str, None]: User's destination language as a postal code or
        `None` if the language is not supported.
    """
    dest_lang = dest_lang.lower()

    # Get language code
    for l in LANGUAGES.items():
        if dest_lang in l:
            return l[1]
        
    # Special cases for Chinese
    if dest_lang == "chinese" or dest_lang == "zh":
        return "zh-CN"
    
    elif dest_lang == "zh-tw":
        return "zh-TW"

    elif dest_lang == "zh-cn":
        return "zh-CN"
    
    # Return None if invalid language
    return None


@bot.command()
async def t(ctx, dest_lang: str = "en") -> discord.Message:
    """
    Translates a message being replied to by a Discord user to a language of
    their choice (defaults to english).
    
    Args:
        dest (str): Language that the user want to translate to. Defaults to
        english if no value is given.
    """
    try:
        USAGE_ERROR = "\nUsage: Reply to a message with `-t <language>`."

        # Handles invalid execution
        if not ctx.message.reference:
            return await ctx.message.reply(f"Error: No Message Found.{USAGE_ERROR}")

        # Get destination language
        dest_lang = get_lang_code(dest_lang)

        # Handles invalid destination language
        if dest_lang is None:
            return await ctx.message.reply(f"Error: `{dest_lang}` is not a valid language.{USAGE_ERROR}")

        # Get replied message
        msg_id = ctx.message.reference.message_id
        msg = await ctx.channel.fetch_message(msg_id)
        msg_content = msg.content.strip().replace("*", "")  # Removes italics/bolding

        # Remove translation suffix if it's a retranslation
        if msg.author.id == ID:
            keys = "|".join(re.escape(key.title()) for key in LANGUAGES)
            pattern = rf"\s*\((?:{keys}) -> (?:{keys})\)\s*"
            msg_content = re.sub(pattern, "", msg_content).strip()

        # Handles empty message
        if not msg_content:
            return await ctx.message.reply(f"Error: No Message Found.\n{USAGE_ERROR}")

        # Detect source language
        src_lang = single_detection(msg_content, api_key=TRANSLATE_API_KEY)

        # Special case for Chinese
        if src_lang == "zh":
            src_lang = "zh-CN"
        
        # Handles invalid source language
        if src_lang not in LANGUAGES.values():
            return await ctx.message.reply(f"Error: `{src_lang}` is not a supported source language.\n{USAGE_ERROR}")

        # Translate message
        translated_msg = GoogleTranslator(source=src_lang, target=dest_lang).translate(msg_content)

        # Handles API error
        if not translated_msg:
            return await ctx.message.reply(f"Error: Translation failed.\n{USAGE_ERROR}")

        # Output translated text
        return await return_message(ctx, f"**{translated_msg}** ({key_from_value(LANGUAGES, src_lang).title()} -> {key_from_value(LANGUAGES, dest_lang).title()})")
    # Handles any other errors
    except Exception as e:
        print(f"Translation Error: {e}")
        return await ctx.message.reply(f"Error: Unknown.\n{USAGE_ERROR}")


@bot.command()
async def l(ctx) -> discord.Message:
    """
    Lists all the languages available for translation in pages, pagination
    controlled by reactions.
    """
    languages = list(LANGUAGES.items())
    per_page = 20
    pages: list[str] = []

    # Appends pages to a list
    for i in range(0, len(languages), per_page):
        chunk = languages[i:i+per_page]
        page_content = f"```SUPPORTED LANGUAGES ({i//per_page+1} of {ceil(len(languages)/per_page)}):\n=======================================\n"
        page_content += "| Language              | Abbreviation |\n"
        page_content += "|======================================|\n"

        # Uses ASCII art to neatly separate items
        for key, value in chunk:
            page_content += f"| {key.title():<21} | {value.upper():<12} |\n"

        page_content += "```"
        pages.append(page_content)

    # Page switching logic
    current_page = 0
    message = await ctx.message.reply(pages[current_page])

    # Adding reactions for navigation
    if len(pages) > 1:
        await message.add_reaction("◀️")  # Back
        await message.add_reaction("▶️")  # Forward


        def check(reaction, user) -> bool:
            """
            Check function exclusively for checking if reactions are correct
            and reacted by the correct user.
            
            Args:
                reaction (reaction): Gets reaction made on the message.
                user (user): Gets the user that the reaction was made by.
                
            Returns:
                bool: Returns a bool if the reaction was one of the correct reactions
                and if the author of the reaction was also the author of the command.
            """
            return user == ctx.author and reaction.message.id == message.id and reaction.emoji in ["◀️", "▶️"]


        # Adjusts page
        while True:
            reaction, user = await bot.wait_for("reaction_add", check=check)

            if reaction.emoji == "▶️":
                current_page += 1
            elif reaction.emoji == "◀️":
                current_page -= 1
            
            # Edits message to display new languages and remove user reaction
            new_page: list[str] = pages[current_page%len(pages)]
            await message.edit(content=new_page)
            await message.remove_reaction(reaction, user)


@bot.command()
async def c(ctx, *equation) -> discord.Message:
    """
    Evaluates an arithmetic equation given by the user and returns the result.
    Also has support for pi and trigonometry.
    """
    try:
        # Get equation
        eq = " ".join(equation).replace("^", "**")

        # Handles no equation found
        if not eq:
            return await ctx.message.reply("Error: No Equation Found.\nUsage: `-c <equation>`")

        # Calculate and return total rounded to 5 decimals
        return await ctx.message.reply(f"Total: **{round(eval(eq), 5)}**")
    # Handles domain error
    except ValueError:
        return await ctx.message.reply("Undefined")
    # Handles unknown function error
    except NameError as e:
        return await ctx.message.reply(f'Unknown Function: "{e.split()[1][1:-1]}"')
    # Handles unknown error
    except Exception as e:
        print(e)
        return await ctx.message.reply("Unknown Error:\nUsage: `-c <equation>`")


@bot.command()
async def e(ctx, *string) -> discord.Message:
    """
    Echoes back an inputted string.
    """
    try:
        string = " ".join(string)
        
        # Handles no string found
        if not string:
            return await ctx.message.reply("Error: Invalid String\nUsage: `-e <string>`")

        # Echoes string
        return await ctx.message.reply(string)
    except Exception as e:
        print(e)
        return await ctx.message.reply("Unknown Error\nUsage: `-e <string>`")

# Run program
if __name__ == "__main__":
    bot.run(TOKEN)
