import re,os
from sqlalchemy import Column, Integer, String, Float
from typing import Optional
from pydub import AudioSegment as pd_audio
from pydub.playback import play as pd_play
from pydub.utils import mediainfo as pd_mediainfo
from random import choice as rndchoice
from twitchbot import (
    Command,
    Message,
    cfg,
    Base,
    session,
    InvalidArgumentsError,
    get_currency_name,
    get_balance_from_msg,
    subtract_balance,
    reset_command_last_execute
)
from .soundboard_bot import CooldownTag

__all__ = ('Sound', 'SoundCommand', 'get_sound', 'play_sound', '_create_colln')



####################
###    Config    ###
####################

if 'soundbank_path' not in cfg.data: cfg.data['soundbank_path']='./sounds'
if 'soundbank_default_price' not in cfg.data: cfg.data['soundbank_default_price']=0
if 'soundbank_verbose' not in cfg.data: cfg.data['soundbank_verbose']=True
#if 'soundbank_gain' not in cfg.data: cfg.data['soundbank_gain']=0
if 'soundbank_cooldown' not in cfg.data: cfg.data['soundbank_cooldown']=15
if 'soundbank_permission' not in cfg.data: cfg.data['soundbank_permission']=''

if 'soundbank_gain' not in cfg.data:
    cfg.data['soundbank_gain']={}
else:
    # This next check is needed for migration from an earlier version of the config
    try:
        float(cfg.soundbank_gain)
    except:
        pass
    else:
        cfg.data['soundbank_gain']={}


# Collections
if 'soundbank_collections' not in cfg.data:
    cfg.data['soundbank_collections'] = {}

if 'soundbank_collections_price' not in cfg.data:
    if 'soundbank_default_price' in cfg.data:
        SBCOLL_PRICE = cfg.soundbank_default_price
    else:
        SBCOLL_PRICE = 0
else:
    SBCOLL_PRICE = cfg.soundbank_collections_price

cfg.save()


PREFIX = cfg.prefix
SB_COOLDOWN = cfg.soundbank_cooldown
SB_PATH = cfg.soundbank_path
SB_DEFPRICE = cfg.soundbank_default_price
SB_PERM = cfg.soundbank_permission
SB_GAIN = cfg.soundbank_gain




##########################################
###    Database class and functions    ###
##########################################

class Sound(Base):
    __tablename__ = 'sounds'

    id = Column(Integer, primary_key=True, nullable=False)
    channel = Column(String(255), nullable=False)
    sndid = Column(String(255), nullable=False)
    filepath = Column(String(255), nullable=False)
    price = Column(Integer)
    pricemult = Column(Float)
    gain = Column(Float)

    @classmethod
    def create(cls, channel: str, sndid: str, filepath: str, **kwargs):
        optargs = {}
        for key in ['price','pricemult','gain']:
            if key in kwargs:
                optargs[key] = kwargs[key]
        return Sound(channel=channel.lower(), sndid=sndid.lower(),
            filepath=filepath, **optargs)



def SoundCommand(self):
    """a decorator that adds a cmd.permission_tag="Sound" to a command"""
    self.permission_tag="Sound"
    return self


def add_sound(snd: Sound) -> str:
    """add a sound object to the soundbank, return a string describing the outcome"""
    assert isinstance(snd, Sound), 'sound must be of type Sound'

    if sound_exist(snd.channel, snd.sndid, snd.filepath):
        resp = f'failed to add sound: sound "{sndid}" already exists in soundbank'
        return resp

    if pd_mediainfo(snd.filepath):
        session.add(snd)
        session.commit()
        resp = f'successfully added sound "{sndid}" to soundboard'
    else:
        resp = f'failed to add sound: file not found or not recognized'
    return resp


def get_sound(channel: str, sndid: str) -> Optional[Sound]:
    """return a Sound object from the soundback given sndid"""
    assert isinstance(sndid, str), 'sound sndid must be of type str'
    return session.query(Sound).filter(Sound.channel == channel, Sound.sndid == sndid).one_or_none()


def play_sound(snd: Sound, gain: float = 0):
    """physically play a Sound object on the running pc"""
    if snd.gain:
        gain += snd.gain
    sound = pd_audio.from_file(snd.filepath) + gain
    pd_play(sound)


def delete_sound(channel: str, sndid: str) -> None:
    """delete a sound by sndid"""
    assert isinstance(sndid, str), 'sound sndid must be of type str'
    session.query(Sound).filter(Sound.channel == channel, Sound.sndid == sndid).delete()
    session.commit()


def purge_sb(channel: str) -> None:
    """delete all entries from soundbank"""
    session.query(Sound).filter(Sound.channel == channel).delete()
    session.commit()


def clean_sb(channel: str, verbose: bool = True) -> int:
    """remove unused files and add new files to soundbank"""
    num=0
    for snd in session.query(Sound).filter(Sound.channel == channel).all():
        if not os.path.exists(snd.filepath):
            session.delete(snd)
            num+=1
            if verbose:
                print(f'sound "{snd.sndid}" has been deleted because the associated file was not found ({snd.filepath})')

    session.commit()
    return num


def _filename_strip(filename: str, strip_prefix: bool = False) -> str:
    """convert a file name to a sndid for automated processing"""
    # (just the file name expected, without path)
    # first identify and strip the prefix, if any and if needed
    if strip_prefix:
        prefixpos = filename.find("_")
    else:
        prefixpos = -1

    # then strip the file extension (defined via the last dot)
    # also drop anything after the first space because no spaces allowed in sndid
    suffixpos1 = filename.rfind(".")
    suffixpos2 = filename.find(" ")
    # not really sure how to simplify these ifs
    if suffixpos1 > -1 and suffixpos2 > -1:
        suffixpos = min(suffixpos1, suffixpos2)
    elif suffixpos1 > -1:
        suffixpos = suffixpos1
    elif suffixpos2 > -1:
        suffixpos = suffixpos2
    else:
        suffixpos = None

    return filename[prefixpos+1:suffixpos]


# A supplementary command to create a command for every collection.
# I have not found a better way to do this than exec() plus a lot of jank.
# (this is not in the collections file due to it being used in updatesb, and a circular import happens otherwise)
# !! Mind the indentation in the exec string !!
def _create_colln(colln):
    exec(f"""@CooldownTag(tag='Sound')
@Command('{colln}', permission=SB_PERM, syntax='', cooldown=cfg.soundbank_cooldown)
async def cmd_play_collection(msg: Message):
    await play_collection(msg, '{colln}')""")



def populate_sb(channel: str, path: str = '.', recursive: bool = False, gen_collections: bool = False,
            replace: bool = False, strip_prefix: bool = False, verbose: bool = True):
    """auto-fill the soundbank (for given channel) from files in the specified folder"""
    if not os.path.exists(path):
        raise ValueError('updatesb is unable to find the folder it was asked to scan')
        return False

    if verbose:
        print('updating the soundbank...')

    # Generate the relevant list of files and collections inferred from disk scan
    scanfiles = []
    scan_collns = {}

    for item in os.scandir(path):
        # item can be a file, a folder, a symlink, a mountpoint...
        if item.is_file():
            fpath = item.path
            fname = item.name

            # Check if pydub can recognize these files. If yes, add it to the lists.
            if not pd_mediainfo(fpath):
                continue

            sndid = _filename_strip(fname, strip_prefix=strip_prefix).lower()
            scanfiles.append([sndid, fpath])

        elif item.is_dir() and (recursive or gen_collections):
            scan_collns[item.name]=[]
            for root, subdirs, files in os.walk(item.path):
                for fname in files:
                    fpath = os.path.join(root, fname)

                    # Check if pydub can recognize these files. If yes, add it to the lists.
                    if not pd_mediainfo(fpath):
                        continue

                    sndid = _filename_strip(fname, strip_prefix=strip_prefix).lower()
                    scanfiles.append([sndid, fpath])
                    scan_collns[item.name].append(sndid)


    # Attempt to import files into database
    num_a=0
    num_r=0
    for sndid,fpath in scanfiles:
        snd = Sound.create(channel=channel, sndid=sndid, filepath=fpath)
        sndex = get_sound(channel=channel, sndid=sndid)
        if not sndex:
            # no conflicts, add sound
            session.add(snd)
            resp = f'successfully added sound "{sndid}" to soundboard from {fpath}'
            num_a+=1
        elif replace:
            # sndid exists and is overwritten
            session.query(Sound).filter(Sound.channel == channel, Sound.sndid == sndid).delete()
            session.add(snd)
            resp = f'replaced sound "{sndid}" from {fpath}'
            num_r+=1
        elif sndex.filepath != snd.filepath:
            # sndid exists but points to a different file
            resp = f'failed to add sound "{sndid}" from {fpath}: sndid already taken by {sndex.filepath}'
        else:
            # sndid exists and points to the same file
            #resp = f'sound "{sndid}" already exists from {fpath}'
            continue

        if verbose and resp:
            print(resp)


    # Now update (overwrite) the collections, if requested
    if gen_collections:
        for colln,sndlist in scan_collns.items():
            # any existing collections are overwritten if their names coincide with parsed collections
            cfg.data['soundbank_collections'][colln] = scan_collns[colln]
            _create_colln(colln)
        cfg.save()

        if verbose:
            resp = 'the following collections have been generated: '
            for key,value in scan_collns.items():
                resp += f'"{key}", '
            resp = resp[:-2] + '.'
            print(resp)

    # Dump the changes to the database
    session.commit()
    if verbose:
        print('changes to db successfully committed')
    return num_a,num_r




##########################
###    Bot commands    ###
##########################

@Command('addsound', permission='sound', syntax='<sndid> <filepath> price=(price) pricemult=(pricemult) gain=(gain)',
    help='adds a sound to the soundboard')
async def cmd_add_sound(msg: Message, *args):
    # sanity checks
    filepath = os.path.join(SB_PATH, args[1])
    if not os.path.exists(filepath):
        raise InvalidArgumentsError(reason='file you are trying to add does not exist', cmd=cmd_add_sound)
    if not args:
        raise InvalidArgumentsError(reason='missing required arguments', cmd=cmd_add_sound)
    sndid=args[0].lower()

    optionals = ' '.join(args[2:])
    optargs = {}

    if 'price=' in optionals and 'pricemult=' in optionals:
        raise InvalidArgumentsError(reason='specify price or pricemult, not both!',
            cmd=cmd_add_sound)

    if 'price=' in optionals:
        m = re.search(r'price=(\d+)', msg.content)
        if m:
            optargs['price'] = int(m.group(1))
        else:
            raise InvalidArgumentsError(
                reason='invalid price for price=, must be an INT',
                        cmd=cmd_add_sound)

    if 'pricemult=' in optionals:
        m = re.search(r'pricemult=(x?)(\d+.\d*)', msg.content)
        if m and float(m.group(2))>=0:
            optargs['pricemult'] = float(m.group(2))
        else:
            raise InvalidArgumentsError(
                reason='invalid argument for pricemult=, must be a non-negative '+
                'FLOAT or xFLOAT, e.g., 0.7 or x1.4', cmd=cmd_add_sound)

    if 'gain=' in optionals:
        m = re.search(r'gain=(-?\d+.\d*)', msg.content)
        if m:
            optargs['gain'] = float(m.group(1))
        else:
            raise InvalidArgumentsError(
                reason='invalid gain for gain=, must be a FLOAT, e.g., -1.4',
                    cmd=cmd_add_sound)

    snd = Sound.create(channel=msg.channel_name, sndid=sndid, filepath=filepath, **optargs)
    resp = add_sound(snd)
    await msg.reply(resp)


@Command('updsound', permission='sound', syntax='<sndid> name=(new_sndid) price=(price) pricemult=(pricemult) gain=(gain)',
    help='updates sound details in the soundboard')
async def cmd_upd_sound(msg: Message, *args):
    # this largely follows the same steps as addsound
    snd = get_sound(msg.channel_name, args[0])
    if snd is None:
        raise InvalidArgumentsError(reason='no sound found with this name', cmd=cmd_upd_sound)

    optionals = ' '.join(args[2:])

    if 'name' in optionals:
        m = re.search(r'name=(\w+)', msg.content)
        if m:
            snd.sndid = m
        else:
            raise InvalidArgumentsError(
                reason='invalid new name for name=',
                        cmd=cmd_upd_sound)

    if 'price=' in optionals and 'pricemult=' in optionals:
        raise InvalidArgumentsError(reason='specify price or pricemult, not both!',
            cmd=cmd_upd_sound)

    if 'price=' in optionals:
        m = re.search(r'price=(\d+)', msg.content)
        if m:
            snd.price = int(m.group(1))
        else:
            raise InvalidArgumentsError(
                reason='invalid price for price=, must be an INT',
                        cmd=cmd_upd_sound)

    if 'pricemult=' in optionals:
        m = re.search(r'pricemult=(x?)(\d+.\d*)', msg.content)
        if m and float(m.group(2))>=0:
            snd.pricemult = float(m.group(2))
        else:
            raise InvalidArgumentsError(
                reason='invalid argument for pricemult=, must be a non-negative '+
                'FLOAT or xFLOAT, e.g., 0.7 or x1.4', cmd=cmd_upd_sound)

    if 'gain=' in optionals:
        m = re.search(r'gain=(-?\d+.\d*)', msg.content)
        if m:
            snd.gain = float(m.group(1))
        else:
            raise InvalidArgumentsError(
                reason='invalid gain for gain=, must be a FLOAT, e.g., -1.4',
                    cmd=cmd_add_sound)

    session.commit()
    await msg.reply(f'successfully updated sound {snd.sndid}')


@CooldownTag(tag='Sound')
@Command('sb', permission=SB_PERM, syntax='<sndid>', cooldown=SB_COOLDOWN, help='plays sound sndid from soundboard')
async def cmd_get_sound(msg: Message, *args):
    # sanity checks:
    if not args:
        await msg.reply(f'You can play sounds from the soundboard with "!sb <sndname>".')
        return

    snd = get_sound(msg.channel_name, args[0].lower())
    if snd is None:
        await msg.reply(f'no sound found with name "{args[0]}"')
        raise ValueError(args[0].lower())
        return

    # calculate the sound price
    if snd.price:
        price = snd.price
    elif snd.pricemult:
        price = snd.pricemult*SB_DEFPRICE
    else:
        price = SB_DEFPRICE

    # make the author pay the price:
    currency = get_currency_name(msg.channel_name).name
    if get_balance_from_msg(msg).balance < price:
        raise InvalidArgumentsError(f'{msg.author} tried to play {snd.sndid} '
            f'for {price} {currency}, but they do not have enough {currency}!')
    subtract_balance(msg.channel_name, msg.author, price)

    # get the per-channel volume gain
    if msg.channel_name in SB_GAIN:
        gain = SB_GAIN[msg.channel_name]
    else:
        gain = 0

    # report success
    if cfg.soundbank_verbose:
        await msg.reply(f'{msg.author} played "{snd.sndid}" for {price} {currency}')

    play_sound(snd, gain)


@Command('delsound', permission='sound', syntax='<sndid>', help='deletes the sound from the soundboard')
async def cmd_del_sound(msg: Message, *args):
    if not args:
        raise InvalidArgumentsError(reason='missing required argument', cmd=cmd_del_sound)

    snd = get_sound(msg.channel_name, args[0])
    if snd is None:
        raise InvalidArgumentsError(reason='no such sound found', cmd=cmd_del_sound)

    delete_sound(msg.channel_name, snd.sndid)
    await msg.reply(f'successfully deleted sound "{snd.sndid}"')


@Command('purgesb', permission='sound', help='deletes all sounds from the soundbank')
async def cmd_purge_sb(msg: Message):
    purge_sb(channel=msg.channel_name)
    await msg.reply(f'soundbank purged')


@Command('cleansb', permission='sound', syntax='[q]uiet', help='clears all sounds with missing files from the soundbank')
async def cmd_clean_sb(msg: Message, *args):
    # this 'if' is bold, but it should work?
    if 'q' in args:
        verbose=False
    else:
        verbose=True
    num = clean_sb(channel=msg.channel_name, verbose=verbose)
    await msg.reply(f'{num} sounds with missing files were deleted')


@Command('updatesb', permission='sound', syntax='[c]lean [g]enerate_collections [r]ecursive [s]trip [f]orce [q]uiet',
    help='auto-imports sounds from the predefined folder')
async def cmd_upd_sb(msg: Message, *args):
    optionals = ''.join(args)
    cln = True if ('c' in optionals) else False
    gencollns = True if ('g' in optionals) else False   # implies rec
    rec = True if ('r' in optionals) else False
    strip = True if ('s' in optionals) else False
    force = True if ('f' in optionals) else False
    quiet = True if ('q' in optionals) else False

    if cln:
        num = clean_sb(channel=msg.channel_name, verbose=not quiet)
        await msg.reply(f'{num} sounds with missing files were deleted')

    num_a,num_r = populate_sb(channel=msg.channel_name, path=SB_PATH, recursive=rec,
            gen_collections=gencollns, replace=force, strip_prefix=strip, verbose=not quiet)
    if force:
        await msg.reply(f'soundbank updated; {num_a} sounds added, {num_r} sounds replaced')
    else:
        await msg.reply(f'soundbank updated; {num_a} sounds added')


"""
@Command('gensblist', permission='sound', help='output list of sounds in soundbank (with prices) to file')
async def cmd_gen_sb_list(msg: Message):
    channel=msg.channel_name
    with open(f"{SB_PATH}/sb_list_{channel}.txt", 'w') as f:
        f.write(f'# Soundbank [sub]commands list for channel {channel}\n\n')
        f.write('# AUTOMATICALLY GENERATED FILE\n')
        currency = get_currency_name(channel).name
        for snd in session.query(Sound).filter(Sound.channel == channel).all():
            if snd.price:
                price=snd.price
            elif snd.pricemult:
                price = snd.pricemult*SB_DEFPRICE
            else:
                price=SB_DEFPRICE
            f.write(f'{PREFIX}sb {snd.sndid}\t\t{price} {currency}\n')
    await msg.reply(f'sound list generated')
"""


@Command('sbvol', permission='sound', syntax='<optional:sndid> <gain>',
    help='changes either the soundbank volume gain, or the gain of an individual sound, in db')
async def cmd_sbvol(msg: Message, *args):
    if msg.channel_name not in SB_GAIN:
        SB_GAIN[msg.channel_name] = 0
    if not args:
        await msg.reply(f'current soundbank volume gain for current channel: {SB_GAIN[msg.channel_name]}')
        return

    try:
        # no sndname given; change global volume
        delta = float(args[0])
    except:
        # change the volume of a given sound
        sndid = args[0]
        try:
            delta = float(args[1])
        except:
            pass

    if 'sndid' in locals():
        # best guess is we're trying to change a given sound gain
        snd = get_sound(msg.channel_name, sndid)
        if snd is None:
            await msg.reply(f'no sound found with name "{sndid}"')
            return
        if 'delta' in locals():
            # found a sound with a given name and are trying to change its gain
            if snd.gain:
                snd.gain += delta
            else:
                snd.gain = delta
            await msg.reply(f'volume gain of sound "{sndid}" changed by {delta}; current gain: {snd.gain}')
        else:
            # found a sound, but no gain given (or can't convert it to float)
            await msg.reply(f'current volume gain of sound "{sndid}": {snd.gain}')
        return
    else:
        # no sndname given (first argument is a float),
        SB_GAIN[msg.channel_name] += delta
        cfg.data['soundbank_gain'] = SB_GAIN
        cfg.save()
        await msg.reply(f'soundbank volume gain for current channel changed by {delta}; current gain: {SB_GAIN[msg.channel_name]}')
        return




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
    collns = cfg.soundbank_collections

    if not colln in collns:
        # This can only happen in a multi-channel setup
        raise InvalidArgumentsError(reason=f'Collection {colln} is not defined!',
            cmd=play_collection)
        return

    RNDSND = rndchoice(collns[colln]).lower()
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


# create a command for every collection (on initialization)
for colln in cfg.soundbank_collections:
    _create_colln(colln)
