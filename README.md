# PythonTwitchBotFramework Soundboard mod

This is an extension for [PythonTwitchBotFramework](https://github.com/sharkbound/PythonTwitchBotFramework) that adds the soundboard capabilities to the bot. See [the original readme](https://github.com/sharkbound/PythonTwitchBotFramework/blob/master/README.md) and  [the original wiki](https://github.com/sharkbound/PythonTwitchBotFramework/wiki) for info on how to install, set up, and use the bot.

As of now, the soundboard *partially* integrates with the bot's own economy, but does not react to bits/subscriptions/channel points. 

For any questions or feature requests, open an issue on github.


# Dependencies

1. [PythonTwitchBotFramework](https://github.com/sharkbound/PythonTwitchBotFramework), obviously
2. [PyDub](https://github.com/jiaaro/pydub/) to play sounds. 
	* If you are on windows and you get a permission error when trying to play sounds, see [PyDub issue 209](https://github.com/jiaaro/pydub/issues/209). The issue can be fixed by a one-line patch to the installed PyDub scripts. But simply installing SimpleAudio works for some people too.
3. WAV works with no further dependencies; for other formats you'll need [ffmpeg](http://www.ffmpeg.org/) or [libav](http://libav.org/) installed in the system.
4. [Pynput](https://pypi.org/project/pynput/) (optional) for hotkey controls.


# Installation
Get python, get PythonTwitchBotFramework, download the pyfiles from this repo and put them in `<botfolder>/commands/`. Launch the bot as usual.


# Quickstart
Create a `sounds` folder in your bot folder. Put some audio files in there, e.g. `wow.mp3`. Type `!updatesb` in chat. Now you and your viewers can play this sound using the command `!sb wow`.


# Config options
The following options are relevant for the soundboard and are set in `./config/config.json`:

## General soundbank config
* `soundbank_path` (default: `./sounds`): path to folder with all the sounds. All paths to individual sound files must then be relative to this folder.
* `soundbank_default_price` (default: `0`): default price of playing a sound, in terms of bot currency. Set to `0` if you do not want to use the bot economy for sounds. Note: this default is applied when *adding* sounds, changing it does not retroactively change the price of previously added sounds.
* `soundbank_verbose` (default: `true`): whether the bot will respond with messages a lá `username played "sound" for 50 points`. Set to `False` if you do not want these messages and/or if you do not want to use the bot economy.
* `soundbank_gain` (default: `0`): global volume level modifier for all sounds, in dB.
* `soundbank_cooldown` (default: `15`): cooldown for playing sounds (in seconds). 
* `soundbank_permission` (default: ``): set the permission group for playing sounds from the bank. By default everyone in chat can use the `!sb` command (see [PTBF readme](https://github.com/sharkbound/PythonTwitchBotFramework#permissions) for an explanation of permissions).

## Soundbank collections
* `soundbank_use_collections` (default: `false`): are you using any soundboard collections? See [collections](#collections)
* `soundbank_collections` (default: `None`): defines the soundboard collections for you to use; see [collections](#collections) for more details.
* `soundbank_collections_permission`: set the permission group for playing sounds from the soundbank collections. If unset, defaults to the value set in `soundbank_permission`. If that is not set either, defaults to unrestricted access.
* `soundbank_collections_price` (default: `0`): price for playing a sound from (any) collection. Per-collection prices are not implemented, sorry.

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
  "soundbank_use_collections": true,
  "soundbank_collections": {
    "<yourtwitchchannel>": {
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
    }
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
The `!updatesb` command runs the automatic scraper. It scans the *soundbank folder* (which is set by the `soundbank_path` config variable) and adds any audio file from that folder to the soundbank, using filename as the sound name in the bank. 

E.g., with default config, file `<botfolder>/sounds/wow.mp3` will be named `wow` and can be then played with `!sb wow`. 

Important notes on scraping:
* File extension (everything after the last dot) is automatically stripped (`wow.mp3` -> `!sb wow`). 
* If filename has spaces, then only the first word is taken as sound name (`wow what.mp3` -> `wow`).

The command takes the following options:

* `r` -- *recursive*, to look for audio files in nested folders as well, and not only in `soundbank_path`;
* `s` -- *strip prefix*, to strip everything until the first underscore when converting filename to sound name. E.g., sound `sounds/owen_wow.mp3` would be named `wow` by `!updatesb s`.
* `f` -- *force*, to force-replace any existing sounds in the bank with new ones in case of conflicting sound names (otherwise conflicts are skipped).
* `q` -- *quiet*, to suppress detailed reporting in the bot output (does not affect the report posted in chat).

The options can be combined: e.g., `!updatesb rs` scans `soundbank_path` and all nested folders *and* strips prefixes.

To summarize, there are three ways to organize your sound collection: using whitespaces in filenames, using prefixes with underscores in filenames (with `s` option), and using subfolders (with `r` option).

Note that many features above can create conflicts. E.g., if you have sounds named `wow.mp3` and `wow 2.mp3`, both of them will try to claim name `wow`. This is not allowed. If you want one command to pull a random sound from a pool of sounds, see [collections](#collections).


## Adding sounds: manual
You can also add sounds to the soundbank manually using `!addsound` command. The syntax is:

`!addsound <sndid> <filepath> [price=<price>] [pricemult=<pricemult>] [gain=<gain>]`

Example:
`!addsound wow "owen/wow.mp3" pricemult=x1.5 gain=6`

Arguments:

* `sndid` is the sound name (mandatory)
* `filepath` is the path to audio file (mandatory). The path is relative to the `soundbank_path`, so in the example above, the file is actually in `<botfolder>/sounds/owen/wow.mp3`. To be safe it is best to enclose the filepath in single or double quotes.
* `price` and `pricemult` are optional arguments modifying the price of playing this sound. At most one of the two may be specified. If neither is specified, price defaults to `soundbank_default_price` as specified in the config. If `pricemult` is specified, the sound will cost `soundbank_default_price * pricemult`.
* `gain` (optional) specifies how loudly this sound file should be played. Added to `soundbank_gain`.


# Playing and listing sounds
To play a sound with name `sndid`, use command `!sb sndid`. It is not currently possible to add sounds as first-level commands (e.g., `!sndid`) without manually creating a custom command, see [upstream readme](https://github.com/sharkbound/PythonTwitchBotFramework/blob/master/README.md#adding-commands).

If you would like to list all sounds currently present in the soundbank, use `!gensblist`. Note that this will not output the list in chat (to avoid problems with large soundbanks), but rather create a text file in your sounds folder. The list will contain all sounds and their current prices. The list is unsorted afaik.


# Modifying and deleting sounds

This sections describes the commands for updating and removing/cleaning up the sound entries database.
Note that if you want anyone except for the channel owner to use these commands (as well as the commands for adding sounds), you should add give them `sound` permission (see [PTBF readme](https://github.com/sharkbound/PythonTwitchBotFramework#permissions) for an explanation of permissions).

## Updating sound entries
You can update the sound data using `!updatesnd`. Syntax: 
`!updsound <sndid> [name=<new_sndid?] [price=<price>] [pricemult=<pricemult>] [gain=<gain>]`
Changing the filename is not possible, because it is too painful to parse them with regexp. But it is possible to change the sound name. All other options are the same as in [Adding sounds: manual](#adding-sounds-manual)

## Deleting a sound
To delete a sound named `sndid`, use `!delsound sndid`.

## Deleting sounds with missing files
`!cleansb` will remove all sounds from the bank, for which the bot is not able to locate the referenced audio file.

## Deleting all sounds from the bank
`!purgesb` deletes all sounds from the soundbank.


# Collections
Instead of playing a *certain* sound after some command, you might want to randomize over a few different sounds. Say, you have two sounds, `wow.mp3` and `ohmy.ogg`, and you want to have a command `!whoa` that flips a coin and plays one of those two sounds. That's exactly what the collections are for!

To implement the idea described above (assuming you already [added](#adding-sounds) the two files to the database and can invoke them using `!sb wow` and `!sb ohmy` in `channel` chat), you should add the following to the config (`<botfolder>/configs/config.json`, replacing `<yourtwitchchannel>` with your channel name):
```json
"soundbank_use_collections": true,
"soundbank_collections": {
  "<yourtwitchchannel>": {
    "whoa": ["wow", "ohmy"]
  }
}
```

As you can guess, this config defines a new collection `whoa` containing two sounds known to the bot as `wow` and `ohmy`. You (or anyone else in chat) can then use command `!whoa` to play a random sound from this collection.

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

And, in principle, you can have different collections for different twitch channels (could be useful if you stream to different channels from the same PC):
```json
"soundbank_use_collections": true,
"soundbank_collections": {
  "<yourtwitchchannel>": {
    "whoa": ["wow", "ohmy"]
  },
  "<anotherchannel>":{
    "whoa": ["wilhelmscream", "overconfidence"]
  }
}
```

(Reminder: ensure that all the sounds that you include as parts of collections are actually added to the database (in respective channels!).)


## Collections: NOTES
* Unlike the rest of the soundboard, collections are currently *not integrated into the bot economy*. I.e., playing a sound from a collection does **not** require channel currency. This is 90% lazy, 10% intentional. (Imagine a collection where one sound costs 10 moneys, another 30 moneys, and the viewer only has 20 moneys. Should the bot ignore an unfortunate roll altogether? Or should it restrict the roll to only affordable sounds? Or should there be a uniform price for the whole collection, possibly detached from the individual sound prices? The bot basically adopts the latter approach as of now, with a price set to zero, but a case can be made for either.) Create an issue on github if you ever need to integrate collections into the economy, and I'll probably be able to implement that.

* Collections are currently invoked via `!collection`, whereas individual sounds require a `!sb sound`. This distinction is 100% lazy and exists mostly for historical reasons.

* Same as you can have different sounds in different channels, you can have different collections in different channels. Collections from different channels can have the same name. 


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

Then after launching the bot, pressing the hotkeys defined in the configfile (on the same computer/os/user that the bot is launched from) should play the respective sound or a random sound from the respective collection.

Both sounds and collections are taken from the first channel defined in the `channels` section of the config file. 

* `soundbank_hotkeys` (default: `None`): a dictionary of the form `<key>: "<sndid>"`, where `<sndid>` corresponds to a sound identifier (see [Adding sounds](#adding-sounds) below), and `<key>` corresponds to the shortcut you want to use.
* `soundbank_hotkeys_collections` (default: `None`): a dictionary of the form `<key>: "<collection>"`, where `<collection>` corresponds to a collection identifier (see [Collections](#collections) below), and `<key>` corresponds to the shortcut you want to use.
* `<key>` shortcuts must be of the form `"<ctrl>+<shift>+<cmd>+<alt>+q"`. [Pynput docs](https://pynput.readthedocs.io/en/latest/keyboard.html) may be helpful in figuring out how to construct the `<key>` string.