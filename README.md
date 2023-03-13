# PythonTwitchBotFramework Soundboard mod

This is an extension for [PythonTwitchBotFramework](https://github.com/sharkbound/PythonTwitchBotFramework) that adds the soundboard capabilities to the bot. See [the upstream readme](https://github.com/sharkbound/PythonTwitchBotFramework/blob/master/README.md) and  [the upstream wiki](https://github.com/sharkbound/PythonTwitchBotFramework/wiki) for more info on how to install, set up, and use the bot (but a quick guide follows).

Quick notes:
1. As of now, the soundboard *partially* integrates with the bot's own economy, but does not react to bits/subscriptions/channel points. 
2. The bot forks the `BaseBot` PTBF class to better deal with cooldowns, with the fork potentially missing some functionality. If you want soundboard functionality in a way fully compatible with `BaseBot` or your other bot class, older [version 0.3](https://github.com/electronicgore/PTBF-soundboard/releases/tag/v0.3) of this bot should work for you.

For any questions or feature requests, open an issue on github.


# Dependencies

1. [PythonTwitchBotFramework](https://github.com/sharkbound/PythonTwitchBotFramework), obviously
2. [PyDub](https://github.com/jiaaro/pydub/) to play sounds. 
	* If you are on windows and you get a permission error when trying to play sounds, see [PyDub issue 209](https://github.com/jiaaro/pydub/issues/209). The issue can be fixed by a one-line patch to the installed PyDub scripts. But simply installing SimpleAudio in addition to PyDub works for some people too.
3. WAV works with no further dependencies; for other formats you'll need [ffmpeg](http://www.ffmpeg.org/) or [libav](http://libav.org/) installed in the system.
4. [Pynput](https://pypi.org/project/pynput/) (optional) for hotkey controls.


# Installation
Get python and other dependencies, get PythonTwitchBotFramework, download the pyfiles from this repo and put them into the (freshly created by you) `soundbot` folder inside the PTBF folder. Create a `run_soundbot.py` in the **PTBF folder** with the following contents:
```
from soundbot import SoundBot
if __name__ == '__main__':
    SoundBot().run()
```
(or move the file from the repo to the PTBF folder).
Then in the command prompt run `python run_soundbot.py` while in the PTBF folder.


# Quickstart
Create a `sounds` folder in your PTBF folder. Put some audio files in there, e.g. `wow.mp3`. Type `!updatesb` in chat. Now you and your viewers can play this sound using the command `!sb wow`.


# Config options
The following options are relevant for the soundboard and are set in `./config/config.json` (run and kill the bot once after installation to generate the config file):

## General soundbank config
* `soundbank_path` (default: `./sounds`): path to folder with all the sounds. All paths to individual sound files must then be relative to this folder.
* `soundbank_default_price` (default: `0`): default price of playing a sound, in terms of bot currency. Set to `0` if you do not want to use the bot economy for sounds. Note: this default is applied when *adding* sounds, changing it does not retroactively change the price of previously added sounds.
* `soundbank_verbose` (default: `true`): whether the bot will respond with messages a lá `username played "sound" for 50 points`. Set to `False` if you do not want these messages and/or if you do not want to use the bot economy.
* `soundbank_gain` (default: `None`): global volume level modifier for all sounds, in dB. This config option is channel-specific, but you are free to specify a number. The [`!sbvol`](## Adjusting the volume) command can adjust this option during runtime.
* `soundbank_cooldown` (default: `15`): cooldown for playing sounds (in seconds). 
* `soundbank_permission` (default: ``): set the permission group for playing sounds from the bank. By default everyone in chat can use the `!sb` command (see [PTBF readme](https://github.com/sharkbound/PythonTwitchBotFramework#permissions) for an explanation of permissions).

## Soundbank collections
* `soundbank_collections` (default: `None`): defines the soundboard collections for you to use; see [collections](#collections) for more details.
* `soundbank_collections_price` (optional): price for playing a sound from (any) collection. Per-collection prices are not implemented, sorry. If unset, defaults to the value set in `soundbank_default_price`. If that is not set either, defaults to `0`.

## Soundbank hotkeys
* `soundbank_use_hotkeys` (default: `false`): should the bot react to hotkeys defined in the following config items?
* `soundbank_hotkeys_channel` (default: `None`): which channel's soundboard should the sounds be played from. Defaults to the first channel defined in the `channels` section of the config file.
* `soundbank_hotkeys` (default: `None`) and `soundbank_hotkeys_collections` (default: `None`) defines hotkeys and respective sounds/collections; see [hotkeys](#hotkeys) for more details.

## Soundbank config example
The following is an example of the part of the `<botfolder>/configs/config.json` file that defines some collections and some hotkeys. This is meant to go after any other config options and before the final closing `}` (so to clarify, this is *not* a complete `config.json` file!).
```
  "soundbank_path": "./sounds",
  "soundbank_default_price": 20,
  "soundbank_verbose": false,
  "soundbank_gain": -7,
  "soundbank_cooldown": 15,
  "soundbank_collections": {
    "hi": [
      "hello",
      "hellothere",
      "hi"
    ],
    "bb": [
      "boop",
      "honk",
      "wenk"
    ],
    "f": [
      "unacceptable",
      "wilhelm"
   ]
  },
  "soundbank_collections_price": 10,
  "soundbank_use_hotkeys": true,
  "soundbank_hotkeys": {
    "<ctrl>+<shift>+s": "honk"
  },
  "soundbank_hotkeys_collections": {
    "<cmd>+<alt>+q": "hi",
    "<cmd>+<alt>+w": "bb",
    "<cmd>+<alt>+e": "f"
  }
```


# Adding sounds
There are two ways to add sounds to the soundboard: automatic and manual.

## Adding sounds: automatic
The `!updatesb` command runs the automatic scraper. It scans the *soundbank folder* (from the `soundbank_path` config variable) and adds any audio file from that folder to the soundbank, using filename as the sound name in the bank. 

E.g., with default config, file `<botfolder>/sounds/wow.mp3` will be named `wow` and can be then played with `!sb wow`. 

**Notes:**
* File extension (everything after the last dot) is automatically stripped (`wow.mp3` -> `!sb wow`). 
* If filename has spaces, then only the first word is taken as sound name (`wow what.mp3` -> `wow`).
* Sounds are defined on a per-channel basis. So if your bot joins `channel1` and `channel2`, and if you add sounds in `channel1` chat, they will not play when invoked from `channel2` chat.

**Options:**
* `c` -- *clean*, runs !cleansb (removes the sounds with the missing names) before scanning the folder for new sounds
* `f` -- *force*, to force-replace any existing sounds in the bank with new ones in case of conflicting sound names (otherwise conflicts are skipped).
* `r` -- *recursive*, to look for audio files in nested folders as well, and not only in `soundbank_path`;
* `s` -- *strip prefix*, to strip everything until the first underscore when converting filename to sound name. E.g., `owen_wow.mp3` would be named `wow` by `!updatesb s`.
* `g` -- *generate collections* (implies `r`), to automatically create sound [collections](#collections) from filesystem. **This is a destructive operation**, any conflicting collections manually specified in the config will be overwritten! See [collections](#collections) section for more info on this option.
* `q` -- *quiet*, to suppress detailed reporting in the bot output (does not affect the report posted in chat).

The options can be combined in arbitrary order: e.g., `!updatesb rcs` cleans the database, then scans `soundbank_path` and all nested folders, and strips prefixes when generating sound names.

To summarize, there are three ways to organize your sound collection that you can mix and match to your liking: 
1. using whitespaces in filenames: `soundname comment.mp3`;
2. using prefixes with underscores in filenames (with `s` option): `comment_soundname.mp3`;
3. using subfolders (with `r` option and if you do not plan to use the `g` option): `comment/soundname.mp3`.

Note that these features can create conflicts. E.g., if you have sounds named `wow.mp3` and `wow 2.mp3`, both of them will try to claim sndid `wow`. This is not allowed, and running `!updatesb` will lead to you having only one of the two in the database (and you can't be sure which one). If you want a single command to pull a random sound from a pool of sounds, see [collections](#collections).


## Adding sounds: manual
You can also add sounds to the soundbank manually using `!addsound` command. The syntax is:

`!addsound <sndid> <filepath> [price=<price>] [pricemult=<pricemult>] [gain=<gain>]`

Example:
`!addsound wow "owen/wow.mp3" pricemult=x1.5 gain=6`

Arguments:

* `sndid` is the sound name (mandatory)
* `filepath` is the path to audio file (mandatory). The path is relative to the `soundbank_path`, so in the example above, the file is actually in `<botfolder>/sounds/owen/wow.mp3`. To be safe it is best to enclose the filepath in single or double quotes.
* `price` and `pricemult` (optional) modify the price of playing this sound in terms of the bot currency (not channel points). At most one of the two may be specified. If neither is specified, price defaults to `soundbank_default_price` as specified in the config. If `pricemult` is specified, the sound will cost `soundbank_default_price * pricemult`.
* `gain` (optional) specifies how loudly this sound file should be played. Added to `soundbank_gain`.


# Playing and listing sounds
To play a sound with name `sndid`, use command `!sb sndid`. 

If you want to add sounds as first-level commands (`!sndid`), you can do one of the following: 
* create a bunch of singleton [collections](#collections), one for every sound, or
* manually create a custom bot command for every sound (see [upstream readme](https://github.com/sharkbound/PythonTwitchBotFramework/blob/master/README.md#adding-commands) for instructions on how to do that).


# Modifying and deleting sounds

This sections describes the commands for updating and removing/cleaning up the sound entries database.
Note that if you want anyone except for the channel owner to use these commands (as well as the commands for adding sounds), you should give them the `sound` permission (see [PTBF readme](https://github.com/sharkbound/PythonTwitchBotFramework#permissions) for a brief on permissions).

## Adjusting the volume
You can change the volume gain of an individual sound or the whole soundbank using the `!sbvol` command. The command is multifunctional, with the syntax being as follows:
* `!sbvol` shows the current global gain modifier that applies to all sounds (on top of the individual sound gain).
* `!sbvol -5.5` changes the global gain modifier by the amount given, in db (decrease by 5.5db in this example).
* `!sbvol sndid` shows the current gain modifier for sound `sndid`.
* `!sbvol sndid -5.5` changes the gain modifier for sound `sndid` by the amount given, in db.

## Updating sound entries
You can update the sound data using `!updatesnd`. Syntax: 
`!updsound <sndid> [name=<new_sndid>] [price=<price>] [pricemult=<pricemult>] [gain=<gain>]`
Changing the filename is not possible (if you move the file, just delete and re-add). But it is possible to change the sound name. All other options are the same as in [Adding sounds: manual](#adding-sounds-manual)

## Deleting a sound
To delete a sound named `sndid`, use `!delsound sndid`.

## Deleting sounds with missing files
`!cleansb` will remove all sounds from the bank, for which the bot is not able to locate the referenced audio file.

## Deleting all sounds from the bank
`!purgesb` deletes all sounds from the soundbank.


# Collections
Instead of playing a *certain* sound after some command, you might want to randomize over a few different sounds. Say, you have two sounds, `wow.mp3` and `ohmy.ogg`, and you want to have a command `!whoa` that flips a coin and plays one of those two sounds. That's exactly what the collections are for!

## Automatic generation
In your `<sounds>` folder (`<botfolder>/sounds` by default), create a folder named after the collection you want to create; `whoa` in our example. Put the desired sounds inside this folder (`whoa/wow.mp3` and `whoa/ohmy.ogg`). Run `!updatesb g` from chat (can be combined with other `updatesb` options). This creates a collection (`!whoa`) that plays a random sound from the folder. This also adds the individual sounds from the folder to the soundbank, so `!sb wow` and `!sb ohmy` can then be used to play individual sounds.

**Notes:**
* `!updatesb g` is a destructive operation and will overwrite any collections defined in the config if their names coincide with the parsed folder names.
* Collections are only generated for first-level folders in `<sounds`, but not the nested folders.
* Unlike individual sounds, the collections are global (universal across channels), for reasons more historical than technical. [Version 0.3](https://github.com/electronicgore/PTBF-soundboard/releases/tag/v0.3) of this bot made collections channel-specific, same as sounds.

## Manual config
You can also implement the idea described in the intro (collection `whoa` that randomizes between sounds `wow.mp3` and `ohmy.ogg`) by editing the config file manually. Assuming you have already [added](#adding-sounds) the two files to the database and can invoke them using `!sb wow` and `!sb ohmy` in `channel` chat), you should add the following to the config (`<botfolder>/configs/config.json`):
```json
"soundbank_use_collections": true,
"soundbank_collections": {
  "whoa": ["wow", "ohmy"]
}
```

As you can guess, this config defines a new collection `whoa` containing two sounds known to the bot as `wow` and `ohmy`. You (or anyone else in chat) can then use command `!whoa` to play a random sound from this collection. (Note again that it is *not* `!sb whoa`.)

You can, of course, define multiple collections in the config file, separated by commas:
```json
"soundbank_use_collections": true,
"soundbank_collections": {
  "<yourtwitchchannel>": {
    "whoa": ["wow", "ohmy"],
    "f": ["payrespects", "wilhelmscream", "overconfidence"]
  }
}
```

(Ensure that all the sounds that you include as parts of collections are actually added to the database. The collection validity is not verified.)


## Collections: NOTES
* You cannot currently set different prices for different collections.

* Collections are currently invoked via `!collection`, whereas individual sounds require a `!sb sound`. This distinction is arbitrary, but the broad idea is that you have very few easily memorable collections, and possibly a lot of individual sounds. Having the `!sb sound` syntax instead of `!sound` allows the bot to respond when a sound is not found (e.g., due to a typo).

* The collections are global across channels.

* The cooldowns are shared across collections and `!sb`.


# Hotkeys

You can use hotkeys to play sounds, directly or via collections. To do that, ensure first that you have [Pynput](https://pypi.org/project/pynput/) installed in your python distribution. Then add something like the following to your `<botfolder>/configs/config.json` file:
```
  "soundbank_use_hotkeys": true
  "soundbank_hotkeys": {
    "<ctrl>+<shift>+s": "sound1"
  },
  "soundbank_hotkeys_collections": {
    "<cmd>+<alt>+q": "collection1",
    "<cmd>+<alt>+w": "collection2"
  }
```

Then after launching the bot, pressing the hotkey combinations defined in the config file (on the same computer/os/user that the bot is launched from) should play the respective sound or a random sound from the respective collection.

The sounds are taken from the first channel defined in the `channels` section of the config file. 

* `soundbank_hotkeys` (default: `None`): a dictionary of the form `<key>: "<sndid>"`, where `<sndid>` corresponds to a sound identifier (see [Adding sounds](#adding-sounds) below), and `<key>` corresponds to the shortcut you want to use.
* `soundbank_hotkeys_collections` (default: `None`): a dictionary of the form `<key>: "<collection>"`, where `<collection>` corresponds to a collection identifier (see [Collections](#collections) below), and `<key>` corresponds to the shortcut you want to use.
* `<key>` shortcuts must be of the form `"<ctrl>+<shift>+<cmd>+<alt>+q"`. [Pynput docs](https://pynput.readthedocs.io/en/latest/keyboard.html) may be helpful in figuring out how to construct the `<key>` string.