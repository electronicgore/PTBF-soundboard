from pydub import AudioSegment as pd_audio
from pydub.playback import play as pd_play
from random import choice as rndchoice

from twitchbot import cfg
#from soundboardt import Sound, get_sound
from soundboardt_collections import play_collection

# pynput is an optional dependency; only attempt to import it if needed
if 'soundbank_use_hotkeys' not in cfg.data: cfg.data['soundbank_use_hotkeys'] = False
elif cfg.soundbank_use_hotkeys == True:
    from pynput import keyboard 
    


# Hotkeys use the soundbank for the first channel defined in the config.
# This is because we can no longer infer the channel from the message.
CHANNEL = cfg.channels[0]


""" the following might still come in handy once collections are integrated in the economy, for the same reason as the next function
def hotkey_collection(snd_collection_name: str):
    sndCollection = cfg.soundbank_collections[CHANNEL][snd_collection_name]
    snd = get_sound(CHANNEL, rndchoice(sndCollection))
    sound = pd_audio.from_file(snd.filepath) + cfg.soundbank_gain
    pd_play(sound)
    """


def hotkey_sound(snd_name: str):
    # this is effectively get_sound() minus all the points-related junk
    # I should probably have a dedicated function for playing a sound instead...
    snd = get_sound(CHANNEL, snd_name)
    if snd.gain:
        gain = snd.gain
    else:
        gain = 0
    sound = pd_audio.from_file(snd.filepath) + cfg.soundbank_gain + gain
    pd_play(sound)


hotkeyDictionary = {}

if cfg.soundbank_hotkeys:
    for key, snd in cfg.soundbank_hotkeys.items():
        # Hotkey receiver needs a function with no arguments:
        exec(f"def hotkey_sound_{snd}(): hotkey_sound('{snd}')")
        exec(f"hotkeyDictionary[key] = hotkey_sound_{snd}")

if cfg.soundbank_hotkeys_collections:
    for key, collection in cfg.soundbank_hotkeys_collections.items():
        # Hotkey receiver needs a function with no arguments:
        exec(f"def hotkey_collection_{collection}(): play_collection('{CHANNEL}', '{collection}')")
        exec(f"hotkeyDictionary[key] = hotkey_collection_{collection}")


hotkeyListener = keyboard.GlobalHotKeys(hotkeyDictionary)
hotkeyListener.start()
