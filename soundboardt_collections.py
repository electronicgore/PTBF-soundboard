from pydub import AudioSegment as pd_audio
from pydub.playback import play as pd_play
from twitchbot import (
    Command,
    Message,
    cfg
)
from random import choice as rndchoice
from soundboardt import Sound, get_sound


####################
###    Config    ###
####################

# These config sanity checks are extremely weak; it might be better to make them more strict and error messages more informative
if 'soundbank_use_collections' not in cfg.data: 
    if 'soundbank_collections' not in cfg.data: 
        cfg.data['soundbank_use_collections'] = False
    else:
        cfg.data['soundbank_use_collections'] = True
        print('Warning: config defines some soundboard collections but "soundbank_use_collections" is undefined! Attempting to use the collections anyway')

if 'soundbank_collections' not in cfg.data: 
    cfg.data['soundbank_use_collections'] = False; 
    print('Warning: config says to use soundboard collections, but none are defined! Cancelling!')



#########################
###    Collections    ###
#########################

def playfromsbcollection(msg: Message, sndCollection: str):
    print(f'Playing a random sound from collection "{sndCollection}"')
    snd = get_sound(msg.channel_name, rndchoice(sndCollections[sndCollection]))
    sound = pd_audio.from_file(snd.filepath) + cfg.soundbank_gain
    pd_play(sound)


if cfg.soundbank_use_collections:
    sndCollections = cfg.soundbank_collections
    for sndCollection in sndCollections:
        """This loop creates a command for each collection in sndCollections, using high amounts of jank.
        Mind the indentation in the exec string!
        """
        exec(f"""@Command('{sndCollection}', syntax='', cooldown=cfg.soundbank_cooldown) 
async def cmd_playfromsbcollection(msg: Message): 
    playfromsbcollection(msg, '{sndCollection}')
""")
