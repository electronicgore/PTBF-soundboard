from pydub import AudioSegment as pd_audio
from pydub.playback import play as pd_play
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
    if 'soundbank_use_collections' == True: 
        cfg.data['soundbank_use_collections'] = False; 
        print('Warning: config says to use soundboard collections, but none are defined! Cancelling!')
    elif 'soundbank_use_collections' not in cfg.data: 
        cfg.data['soundbank_use_collections'] = False
else:
    SBCOLLECTIONS = cfg.soundbank_collections


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
        raise InvalidArgumentsError(reason=f'There is no collection {colln} defined for channel {channel}!',
            cmd=play_collection)

if cfg.soundbank_use_collections:
    # need to construct (1) full list of collections across all channels and
    # (2) a list of channels using a given collection
    # Although is (2) really necessary?
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
        exec(f"""@Command('{colln}', syntax='', cooldown=cfg.soundbank_cooldown) 
async def cmd_play_collection(msg: Message): 
    play_collection(msg.channel_name, '{colln}')""")

