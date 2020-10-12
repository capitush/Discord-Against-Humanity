import discord
import random

client = discord.Client()
white_cards = []
black_cards = []

hands = {}
points = {}
queue = []
choices = {}

black_embed = discord.Embed(
            colour=discord.Color.blurple()
        )

global embed_message
embed_message = []

card_size = 10
numbers = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]


async def init_library():
    white_cards.clear()
    black_cards.clear()
    white_channel, black_channel = main_channels[2].channels
    async for message in white_channel.history(limit=500):
        white_cards.append(message.content)
    async for message in black_channel.history(limit=500):
        black_cards.append(message.content)
    shuffle_library()


def shuffle_library():
    random.shuffle(white_cards)
    random.shuffle(black_cards)


def draw_card(library):
    try:
        card = random.choice(library)
    except IndexError as e:
        print(e)
        return "The library is empty!"
    library.remove(card)
    return card


def get_players():
    return main_channels[1].members


async def deal_hands(member=None):
    if member:
        players = [member]
    else:
        players = get_players()
    for player in players:
        hand = []
        for i in range(10):
            hand.append(draw_card(white_cards))
        hands[player.display_name] = hand


def get_viewable_channel(member):
    channels = main_channels[3].channels
    viewable_channel = list(filter(lambda channel: channel.permissions_for(member).view_channel, channels))
    # viewable_channel = [channel for channel in channels if channel.permissions_for(member).view_channel]
    return viewable_channel[0] if len(viewable_channel) > 0 else None


def get_category_channel(guild, name):
    if len(guild.categories) > 0:
        channels = list(filter(lambda x: x.name == name, guild.categories))
        if len(channels) > 0:
            return channels[0]
        else:
            raise ValueError("No channel was found: " + name)


async def create_card_channels():
    card_channels = main_channels[3]
    server = main_channels[0].guild
    for member in server.members:
        if not get_viewable_channel(member):
            overwrites = {
                server.default_role: discord.PermissionOverwrite(read_messages=False),
                member: discord.PermissionOverwrite(read_messages=True)
            }
            await card_channels.create_text_channel(member.display_name, overwrites=overwrites)


async def announce_black_card():
    embed_message.clear()
    black_embed.set_author(name=queue[0].display_name + " is the card czar.", icon_url=queue[0].avatar_url)
    black_embed.title = draw_card(black_cards)
    update_black_embed_description()
    embed_message.append(await main_channels[0].send(embed=black_embed))


def get_remaining_choosing_players():
    return len(get_players()) - len(choices) - 1


def update_black_embed_description():
    black_embed.description = str(get_remaining_choosing_players()) + " players haven't chosen their card yet."


async def update_black_embed():
    await embed_message[0].edit(embed=black_embed)


async def show_hand(dis, is_czar):
    server = main_channels[0].guild
    if is_czar:
        message = \
            "You are the card czar! Everyone's choices will be visible to you in <#{}>".format(main_channels[0].id)
    else:
        message = ""
        for i, card in enumerate(hands[dis]):
            message += str(i+1) + ") " + card + "\n"
        message += "\nWrite the number of the card you choose!"
        message += "\nIf you think a card is bad, write: bad <number>."
        message += "\nIf you think the current black card is bad, write: bad black"
    await get_viewable_channel(server.get_member_named(dis)).send(message)


async def clear_hand_channels():
    for channel in main_channels[3].channels:
        await channel.purge()


async def total_cards_length(guild):
    white_channel, black_channel = get_category_channel(guild, "Cards").channels
    white_cards_len = len(await white_channel.history(limit=500).flatten())
    black_cards_len = len(await black_channel.history(limit=500).flatten())
    return "We have a total of " + str(white_cards_len) + \
           " white cards, and " + str(black_cards_len) + " black cards! Our ratio between white cards and black cards" \
                                                         " is: " + str(round(white_cards_len/black_cards_len, 4)) +\
                                                         " . Cards against humanity" \
                                                         " has 500 white cards and 80 black cards " \
                                                         "(with a ratio of 6.25). That's " +\
           str(white_cards_len*100/500) + "% of white cards and " + str(black_cards_len*100/80) + "% of black cards."


def use_card(dis, index):
    if dis not in choices.keys():
        choices[dis] = ""
    cards = []
    for i in index:
        if int(i) > 10:
            return False
        cards.append(hands[dis][int(i) - 1])
    for card in cards:
        hands[dis].remove(card)
        hands[dis].append(draw_card(white_cards))
        choices[dis] += card + "\n"
    choices[dis] -= "\n"
    return True


def init_queue():
    queue.extend(get_players())
    random.shuffle(queue)


def shuffle_dict(d):
    l = list(d.items())
    random.shuffle(l)
    d.clear()
    new_dict = dict(l)
    d.update(new_dict)


async def start_czar_choosing():
    shuffle_dict(choices)
    description = ""
    for i, cards in enumerate(choices.values()):
        description += str(i+1) + ": " + cards + "\n"
        if "http" in cards:
            await main_channels[0].send(cards)
        if i < len(numbers):
            await embed_message[0].add_reaction(numbers[i])
        else:
            await embed_message[0].add_reaction("♾")  # If there are more than 10 players, adds infinity emoji
    black_embed.description = description
    await embed_message[0].edit(embed=black_embed)


async def new_turn():
    choices.clear()
    prev_czar = queue.pop(0)
    queue.append(prev_czar)
    await clear_hand_channels()
    for player in get_players():
        if player is queue[0]:
            await show_hand(player.display_name, True)
        else:
            await show_hand(player.display_name, False)
    await announce_black_card()


def init_points():
    for player in get_players():
        points[player.display_name] = 0


def append_points(dis):
    points[dis] = 0


def add_point(dis):
    points[dis] += 1


def get_scoreboard():
    scoreboard = "Scoreboard: \n"
    for player, score in points.items():
        scoreboard += player + ": " + str(score) + "\n"
    return scoreboard


def is_containing_digits(message):
    return all([i.isdigit() for i in message.split(" ")]) and len(message.split(" ")) > 0


def get_cards_category(text_channel):
    pass


def return_cards():
    pass


main_channels = []


async def init_game(text_channel, voice_channel):
    main_channels.append(text_channel)
    main_channels.append(voice_channel)
    try:
        main_channels.append(get_category_channel(text_channel.guild, "Cards"))
        main_channels.append(get_category_channel(text_channel.guild, "Hands"))
    except ValueError as e:
        await main_channels[0].send(e)
        return
    await create_card_channels()
    await init_library()
    init_queue()
    init_points()
    await deal_hands()
    await new_turn()


@client.event
async def on_ready():
    print("ready!")


@client.event
async def on_message(message):
    content = message.content
    if message.author.bot:
        return
    print(content, "   In channel: ", message.channel.name)
    if "total cards" in content:
        await message.channel.send(await total_cards_length(message.guild))

    elif "start" in content:
        await init_game(message.channel, message.author.voice.channel)
    elif len(main_channels) == 0:
        pass
    elif is_containing_digits(content):
        if message.author is not queue[0] or True:
            content = content.split(" ")
            if not use_card(message.author.display_name, content):
                await get_viewable_channel(message.author).send("Pick a card number from 1-10!")
            else:
                update_black_embed_description()
                await update_black_embed()
            if get_remaining_choosing_players() == 0:
                await start_czar_choosing()

    elif "bad" in content:
        if "black" in content:
            with open("bad.txt", "a+") as f:
                f.write(black_embed.title + ", ")
        else:
            args = content.split()
            digit = list(filter(lambda x: str(x).isdigit(), args))
            if digit[0]:
                digit = int(digit[0])
                if digit <= 10:
                    card = hands[message.author.display_name][digit - 1]
                    with open("bad.txt", "a+") as f:
                        f.write(card + ", ")


@client.event
async def on_raw_reaction_add(payload):
    user = payload.member
    if user.bot:  # Bot won't listen to himself
        return
    emoji = str(payload.emoji)
    reaction_channel = client.get_channel(payload.channel_id)
    reaction_guild = client.get_guild(payload.guild_id)
    reaction_message = await reaction_channel.fetch_message(payload.message_id)
    print(emoji, user.display_name)
    czar = queue[0].display_name
    if user.display_name is czar:
        print(user)
        if emoji in numbers:
            # index = numbers.index(emoji)
            indices = [reaction.emoji for reaction in reaction_message.reactions]
            index = indices.index(emoji)
            # print(index, index_test)
            choice = list(choices.values())[index]
            winner = list(choices.keys())[index]
            description = choice + "\n \n The winner is: " + winner
            add_point(winner)
            description += "\n \n" + get_scoreboard()
            black_embed.description = description
            await update_black_embed()
            await new_turn()


@client.event
async def on_voice_state_update(member, before, after):
    if before.channel == main_channels[1] and after.channel != main_channels[1]:  # Person left
        if member == queue[0]:
            return_cards()
            queue.remove(member)
            await new_turn()
        else:
            queue.remove(member)
            if get_remaining_choosing_players() == 0:
                await start_czar_choosing()
    elif after.channel == main_channels[1] and before.channel != main_channels[1]:  # Person joined
        queue.append(member)
        if member not in hands.keys():
            await deal_hands(member)
            append_points(member.display_name)
        await show_hand(member.display_name, False)


@client.event
async def on_member_join(member):
    await create_card_channels()

client.run("whatever your token is, I'm not telling you mine")