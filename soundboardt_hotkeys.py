from twitchbot import cfg
from .soundboardt import play_sound, play_collection

# pynput is an optional dependency; only attempt to import it if needed
if 'soundbank_use_hotkeys' not in cfg.data:
    cfg.data['soundbank_use_hotkeys'] = False
    cfg.save()
elif cfg.soundbank_use_hotkeys == True:
    from pynput import keyboard


if 'soundbank_hotkeys_channel' not in cfg.data:
    CHANNEL = cfg.channels[0]
else:
    CHANNEL = cfg.soundbank_hotkeys_channel


if cfg.soundbank_use_hotkeys:
	hotkeyDictionary = {}
	if cfg.soundbank_hotkeys:
		for key, snd in cfg.soundbank_hotkeys.items():
			# Hotkey receiver needs a function with no arguments:
			exec(f"def hotkey_sound_{snd}(): play_sound(get_sound('{CHANNEL}', '{snd}'))")
			exec(f"hotkeyDictionary['{key}'] = hotkey_sound_{snd}")

	if cfg.soundbank_hotkeys_collections:
		for key, collection in cfg.soundbank_hotkeys_collections.items():
			# Hotkey receiver needs a function with no arguments:
			exec(f"def hotkey_collection_{collection}(): play_collection('{collection}')")
			exec(f"hotkeyDictionary['{key}'] = hotkey_collection_{collection}")

	def test_hotkeys():
		print('the required key combo was pressed')
		play_collection('uhoh')
		print('sound played')
	hotkeyDictionary["<cmd>+<alt>+w"] = test_hotkeys

	hotkeyListener = keyboard.GlobalHotKeys(hotkeyDictionary)
	hotkeyListener.start()
