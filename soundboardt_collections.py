from twitchbot import (
    Command,
    Message,
    cfg,
    get_command,
    get_currency_name,
    get_balance_from_msg,
    subtract_balance
)
from random import choice as rndchoice
from .soundboardt import Sound, SoundCommand, get_sound, play_sound
from .soundboard_bot import CooldownTag


####################
###    Config    ###
####################

# These config sanity checks are extremely weak; it might be better to make them more strict and error messages more informative
if 'soundbank_collections' not in cfg.data:
    SBCOLLECTIONS = {}
else:
    SBCOLLECTIONS = cfg.soundbank_collections


SB_PERM = cfg.soundbank_permission


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


async def accounting_collection(msg: Message, colln: str):
    """Expropriate the points from the message author who dared to play a collection sound"""

    if SBCOLL_PRICE==0:
        # Nothing to do if things are free
        return
    else:
        if get_balance_from_msg(msg).balance < SBCOLL_PRICE:
            currency = get_currency_name(msg.channel_name).name
            raise InvalidArgumentsError(f'{msg.author} tried to play a sound from "{colln}" '
                f'for {SBCOLL_PRICE} {currency}, but they do not have enough {currency}!')
        subtract_balance(msg.channel_name, msg.author, SBCOLL_PRICE)


async def play_collection(msg: Message, colln: str) -> None:
    """The actual command to play a sound from the required collection in a given channel"""
    channel = msg.channel_name

    if not colln in SBCOLLECTIONS:
        # This can only happen in a multi-channel setup
        raise InvalidArgumentsError(reason=f'Collection {colln} is not defined!',
            cmd=play_collection)
        return

    RNDSND = rndchoice(SBCOLLECTIONS[colln]).lower()
    print(f'Playing random sound "{RNDSND}" from collection "{colln}"')
    snd = get_sound(channel, RNDSND)
    if snd is None:
        await msg.reply(f'no sound found with name "{RNDSND}"')
        # raising an exception on no sound found means we skip accounting and avoid starting the cooldown
        raise ValueError(RNDSND)
        return

    play_sound(snd)
    await accounting_collection(msg, colln)
    if cfg.soundbank_verbose:
        await msg.reply(f'{msg.author} played "{snd.sndid}" for {SBCOLL_PRICE} {get_currency_name(msg.channel_name).name}')


# now just need to create a command for every collection.
# I have not found a better way to do this than exec() plus a lot of jank.
# !! Mind the indentation in the exec string !!
for colln in SBCOLLECTIONS:
    exec(f"""@CooldownTag(tag='Sound')
@Command('{colln}', permission=SB_PERM, syntax='', cooldown=cfg.soundbank_cooldown)
async def cmd_play_collection(msg: Message):
    await play_collection(msg, '{colln}')""")

