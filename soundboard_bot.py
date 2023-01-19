import asyncio
import logging
import sys
import os
import warnings

from asyncio import get_event_loop
from typing import Optional, Union, TYPE_CHECKING
from threading import Thread

"""
from twitchbot.poll import PollData
from twitchbot import util
from twitchbot.channel import Channel, channels
from twitchbot.command_whitelist import is_command_whitelisted, send_message_on_command_whitelist_deny
from twitchbot.config import get_nick, get_command_prefix, get_oauth, generate_config
from twitchbot.database import get_custom_command
from twitchbot.disabled_commands import is_command_disabled
from twitchbot.enums import Event
from twitchbot.enums import MessageType, CommandContext
from twitchbot.events import trigger_event
from twitchbot.exceptions import InvalidArgumentsError, BotNotRunningError
from twitchbot.message import Message
from twitchbot.modloader import Mod
from twitchbot.modloader import mods
from twitchbot.modloader import trigger_mod_event
from twitchbot.util import stop_all_tasks
from twitchbot.poll import poll_event_processor_loop
from twitchbot.event_util import forward_event_with_results, forward_event
from twitchbot.extra_configs import logging_config
from twitchbot.util import get_oauth_token_info, _check_token
from twitchbot.translations import translate
"""
if TYPE_CHECKING:
    from .pubsub import PubSubData, PubSubPointRedemption, PubSubBits, PubSubModerationAction, PubSubSubscription, PubSubPollData, PubSubFollow

from twitchbot import BaseBot, Message, CooldownManager
from twitchbot.config import cfg
from twitchbot.command import Command, commands
from twitchbot.exceptions import InvalidArgumentsError, BotNotRunningError
from twitchbot.permission import perms
from twitchbot.irc import Irc
from twitchbot.pubsub import PubSubClient
from twitchbot.shared import set_bot

# for old cooldowns:
from twitchbot.command import is_command_on_cooldown, get_time_since_execute, update_command_last_execute

__all__ = (
    'SoundBot'
)

SB_COOLDOWN = cfg.soundbank_cooldown

class SoundBot(BaseBot):
    def __init__(self):
        self.irc = Irc()
        self._running = False
        self.pubsub = PubSubClient()
        set_bot(self)
        self.cooldowns = CooldownManager()


    async def _run_command(self, msg: Message, cmd: Command):
        # mostly a copy of the default _run_command except for the cooldown handling and no event handling

        # permissions
        # [0] is needed here because get_sub_cmd() also returns the modified args relative to the level it recursively reached
        if not await cmd.get_sub_cmd(msg.args)[0].has_permission_to_run_from_msg(msg):
            if cfg.disable_command_permission_denied_message:
                print(f'denied {msg.author} permission to run command "{msg.content}" in #{msg.channel_name}', file=sys.stderr)
            else:
                await msg.reply(
                    whisper=True,
                    msg=f'you do not have permission to execute "{msg.content}" in #{msg.channel_name}, do "{cfg.prefix}findperm {msg.parts[0]}" to see it\'s permission'
                )
            return


        # cooldowns
        try:
            cooldown_key = cmd.permission_tag
        except NameError:
            cooldown_key = cmd.fullname

        has_cooldown_bypass_permission = (cfg.enable_cooldown_bypass_permissions and
                                          perms.has_permission(msg.channel_name, msg.author, cmd.cooldown_bypass))

        if ((not has_cooldown_bypass_permission)
                and self.cooldowns.on_cooldown(key=cooldown_key, required_min_seconds=cmd.cooldown)):
            return await msg.reply(
                f'{cmd.fullname} is on cooldown, seconds left: {self.cooldowns.seconds_left(key=cooldown_key, required_min_seconds=cmd.cooldown):.1f}')


        # actual execution
        try:
            await cmd.execute(msg)
            if not has_cooldown_bypass_permission:
                self.cooldowns.set_cooldown(key=cooldown_key)
        except InvalidArgumentsError as e:
            await self._send_cmd_help(msg, cmd.get_sub_cmd(msg.args)[0], e)
        except ValueError as e:
            # it's probably not a great idea to make this a universal handler for all commands when I only need it for !sb...
            # just in case, printing out the error details in the console:
            print(f'there was an error while attempting to execute the command: {e}')
            return
