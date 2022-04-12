from pydub import AudioSegment as pd_audio
from pydub.playback import play as pd_play
from random import choice as rndchoice

from twitchbot import cfg
from soundboardt import play_sound
from soundboardt_collections import play_collection

# pynput is an optional dependency; only attempt to import it if needed
if 'soundbank_use_hotkeys' not in cfg.data: cfg.data['soundbank_use_hotkeys'] = False
elif cfg.soundbank_use_hotkeys == True:
    from pynput import keyboard 
    


if 'soundbank_hotkeys_channel' not in cfg.data: 
    CHANNEL = cfg.channels[0]
else:
    CHANNEL = cfg.soundbank_hotkeys_channel


hotkeyDictionary = {}

if cfg.soundbank_hotkeys:
    for key, snd in cfg.soundbank_hotkeys.items():
        # Hotkey receiver needs a function with no arguments:
        #exec(f"def hotkey_sound_{snd}(): hotkey_sound('{snd}')")
        exec(f"def hotkey_sound_{snd}(): play_sound(get_sound('{CHANNEL}', '{snd}'))")
        exec(f"hotkeyDictionary['{key}'] = hotkey_sound_{snd}")

if cfg.soundbank_hotkeys_collections:
    for key, collection in cfg.soundbank_hotkeys_collections.items():
        # Hotkey receiver needs a function with no arguments:
        exec(f"def hotkey_collection_{collection}(): play_collection('{CHANNEL}', '{collection}')")
        exec(f"hotkeyDictionary['{key}'] = hotkey_collection_{collection}")


hotkeyListener = keyboard.GlobalHotKeys(hotkeyDictionary)
hotkeyListener.start()
