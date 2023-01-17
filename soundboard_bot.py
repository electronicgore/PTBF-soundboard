import asyncio
import logging
import sys
import os
import warnings

from asyncio import get_event_loop
from typing import Optional, TYPE_CHECKING
from threading import Thread

"""
from ..poll import PollData
from .. import util
from ..channel import Channel, channels
from ..config import cfg, get_nick, get_command_prefix, get_oauth
from ..config import generate_config
from ..database import get_custom_command
from ..disabled_commands import is_command_disabled
from ..enums import Event
from ..enums import MessageType, CommandContext
from ..events import trigger_event
from ..exceptions import InvalidArgumentsError, BotNotRunningError
from ..message import Message
from ..modloader import Mod
from ..modloader import mods
from ..modloader import trigger_mod_event
from ..permission import perms
from ..util import stop_all_tasks
from ..command_whitelist import is_command_whitelisted, send_message_on_command_whitelist_deny
from ..poll import poll_event_processor_loop
from ..event_util import forward_event_with_results, forward_event
from ..extra_configs import logging_config
from ..util import get_oauth_token_info, _check_token
from ..translations import translate

if TYPE_CHECKING:
    from ..pubsub import PubSubData, PubSubPointRedemption, PubSubBits, PubSubModerationAction, PubSubSubscription, PubSubPollData, PubSubFollow
"""
from twitchbot import BaseBot, Message, CooldownManager
from twitchbot.command import Command, commands, CustomCommandAction, is_command_on_cooldown, get_time_since_execute, update_command_last_execute
from twitchbot.irc import Irc
from twitchbot.pubsub import PubSubClient
from twitchbot.shared import set_bot

__all__ = (
    'SoundBot'
)

class SoundBot(BaseBot):
    def __init__(self):
        self.irc = Irc()
        self._running = False
        self.pubsub = PubSubClient()
        set_bot(self)
        self.cooldowns = CooldownManager()


    async def _run_command(self, msg: Message, cmd: Command):
		# mostly a copy of the default _run_command except for the cooldown handling

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

        elif not isinstance(cmd, CustomCommandAction) and is_command_disabled(msg.channel_name, cmd.fullname):
            if cfg.send_message_on_disabled_command_use:
                await msg.reply(f'{cmd.fullname} is disabled for this channel')
            return

        # also check if the command is whitelisted, (if its not a custom command)
        if not isinstance(cmd, CustomCommandAction) and not is_command_whitelisted(cmd.name):
            if send_message_on_command_whitelist_deny():
                await msg.reply(f'{msg.mention} "{cmd.fullname}" is not enabled in the command whitelist')
            return

        has_cooldown_bypass_permission = (cfg.enable_cooldown_bypass_permissions and
                                          perms.has_permission(msg.channel_name, msg.author, cmd.cooldown_bypass))

        if ((not has_cooldown_bypass_permission)
                and is_command_on_cooldown(msg.channel_name, cmd.fullname, cmd.cooldown)):
            return await msg.reply(
                f'{cmd.fullname} is on cooldown, seconds left: {cmd.cooldown - get_time_since_execute(msg.channel_name, cmd.fullname)}')

        # check that all event listeners return True for this command executing
        if not all(await forward_event_with_results(Event.on_before_command_execute, msg, cmd, channel=msg.channel_name)):
            return

        try:
            await cmd.execute(msg)
            if not has_cooldown_bypass_permission:
                update_command_last_execute(msg.channel_name, cmd.fullname)
        except InvalidArgumentsError as e:
            await self._send_cmd_help(msg, cmd.get_sub_cmd(msg.args)[0], e)
        else:
            forward_event(Event.on_after_command_execute, msg, cmd, channel=msg.channel_name)
