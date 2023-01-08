from twitchbot import (
    Command,
    Message,
    cfg,
    is_command_off_cooldown,
    get_time_since_execute,
    get_command,
    get_currency_name,
    get_balance_from_msg,
    subtract_balance
)
from random import choice as rndchoice
from soundboardt import Sound, get_sound, play_sound


####################
###    Config    ###
####################

# These config sanity checks are extremely weak; it might be better to make them more strict and error messages more informative
if 'soundbank_collections' not in cfg.data:
    SBCOLLECTIONS = {}
    if cfg.data['soundbank_use_collections'] == True:
        cfg.data['soundbank_use_collections'] = False;
        print('Warning: config says to use soundboard collections, but none are defined! Cancelling!')
    elif 'soundbank_use_collections' not in cfg.data:
        cfg.data['soundbank_use_collections'] = False
    cfg.save()
else:
    SBCOLLECTIONS = cfg.soundbank_collections


if 'soundbank_collections_permission' not in cfg.data:
    if 'soundbank_permission' not in cfg.data: cfg.data['soundbank_collections_permission']=''
    else: cfg.data['soundbank_collections_permission']=cfg.soundbank_permission
SBCOLL_PERM = cfg.data['soundbank_collections_permission']


if 'soundbank_collections_price' not in cfg.data:
    if 'soundbank_default_price' in cfg.data:
        SBCOLL_PRICE = cfg.soundbank_default_price
    else:
        SBCOLL_PRICE = 0
else:
    SBCOLL_PRICE = cfg.soundbank_collections_price


#########################
###    Collections    ###
#########################

def is_channel_sb_off_cooldown(channel: str) -> (bool, int):
    """Check all soundbank cooldowns, including 'sb' and all collections"""
    checkbox = []
    checkbox.append(is_command_off_cooldown(channel, cfg.prefix + 'sb'))
    for colln in SBCOLLECTIONS[channel]:
        # why this uses a prefix is beyond me...
        checkbox.append(is_command_off_cooldown(channel, cfg.prefix + colln))
    print(checkbox)

    if any(checkbox):
        # also return the time left on the cooldown
        cooldowns = []
        for colln in SBCOLLECTIONS[channel]:
            timer = get_time_since_execute(channel, cfg.prefix + colln)
            cooldowns.append(get_command(cfg.prefix + colln).cooldown - timer)

    return [all(checkbox), max(cooldowns)]


async def accounting_collection(msg: Message, colln: str):
    """Expropriate the points from the message author who dared to play a collection sound"""
    currency = get_currency_name(msg.channel_name).name

    if SBCOLL_PRICE==0:
        # Nothing to do if things are free
        return
    else:
        if get_balance_from_msg(msg).balance < SBCOLL_PRICE:
            raise InvalidArgumentsError(f'{msg.author} tried to play a sound from "{colln}" '
                f'for {SBCOLL_PRICE} {currency}, but they do not have enough {currency}!')
        subtract_balance(msg.channel_name, msg.author, SBCOLL_PRICE)

    if cfg.soundbank_verbose:
        await msg.reply(f'{msg.author} played "{snd.sndid}" for {SBCOLL_PRICE} {currency}')


async def play_collection(msg: Message, colln: str) -> None:
    """The actual command to play a sound from the required collection in a given channel"""
    channel = msg.channel_name

    if not colln in SBCOLLECTIONS[channel]:
        # This can only happen in a multi-channel setup
        raise InvalidArgumentsError(reason=f'There is no collection {colln} defined for channel {channel}!',
            cmd=play_collection)
        return

    if not is_channel_sb_off_cooldown(channel)[0] and is_command_off_cooldown(channel, cfg.prefix + colln):
        # Check if any of the other collection commands are on cooldown
        # If the command itself is on cooldown then the standard bot response should take care of it.
        #print(f'Soundbank is on cooldown')
        await msg.reply(f'The soundbank is on cooldown, seconds left: {is_channel_sb_off_cooldown(channel)[1]}')
        return

    RNDSND = rndchoice(SBCOLLECTIONS[channel][colln])
    print(f'Playing random sound "{RNDSND}" from collection "{colln}" in channel "{channel}"')
    snd = get_sound(channel, RNDSND)
    play_sound(snd)
    await accounting_collection(msg, colln)


if cfg.soundbank_use_collections:
    # construct an inverse dictionary of of collections of the form "collection": ("channel1", "channel2", ...)
    # to know which commands to create
    collections_list = {}
    for channel in SBCOLLECTIONS:
        for colln in SBCOLLECTIONS[channel]:
            if not colln in collections_list:
                collections_list[colln] = []
            collections_list[colln].append(channel)

    # now just need to create a command for every collection.
    # I have not found a better way to do this than exec() plus a lot of jank.
    # !! Mind the indentation in the exec string !!
    for colln in collections_list:
        exec(f"""@Command('{colln}', permission=SBCOLL_PERM, syntax='', cooldown=cfg.soundbank_cooldown)
async def cmd_play_collection(msg: Message):
    await play_collection(msg, '{colln}')""")

