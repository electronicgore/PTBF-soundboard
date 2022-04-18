from twitchbot import (
    Command,
    Message,
    cfg
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
    SBCOLL_PRICE = 0
else:
    SBCOLL_PRICE = cfg.soundbank_collections_price


#########################
###    Collections    ###
#########################

def play_collection(channel: str, colln: str):
    """Play a sound from the required collection in a given channel, with the channel inferred from the chat message"""
    if colln in SBCOLLECTIONS[channel]:
        print(f'Playing a random sound from collection "{colln}" in channel "{channel}"')
        snd = get_sound(channel, rndchoice(SBCOLLECTIONS[channel][colln]))
        play_sound(snd)
    else: 
        # This can only happen in a multi-channel setup
        raise InvalidArgumentsError(reason=f'There is no collection {colln} defined for channel {channel}!',
            cmd=play_collection)


async def accounting_collection(msg: Message, colln: str):
    """Expropriate the points from the message author who dared to play a collection sound"""
    if SBCOLL_PRICE==0:
        # Nothing to do if things are free
        return
    else:
        currency = get_currency_name(msg.channel_name).name
        if get_balance_from_msg(msg).balance < SBCOLL_PRICE:
            raise InvalidArgumentsError(f'{msg.author} tried to play a sound from "{colln}" '
                f'for {SBCOLL_PRICE} {currency}, but they do not have enough {currency}!')
        subtract_balance(msg.channel_name, msg.author, SBCOLL_PRICE)
        
        if cfg.soundbank_verbose:
            await msg.reply(f'{msg.author} played "{snd.sndid}" for {price} {currency}')


if cfg.soundbank_use_collections:
    # construct a full list of collections across all channels, to know which commands to create
    # outputs a dictionary of the form "collection": ("channel1", "channel2", ...)
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
    try: await accounting_collection(msg, '{colln}')
    except: pass
    else: play_collection(msg.channel_name, '{colln}')""")

