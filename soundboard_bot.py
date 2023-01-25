import asyncio
import logging
import sys
import os
import warnings

from asyncio import get_event_loop
from typing import Optional, Union, TYPE_CHECKING
from threading import Thread

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


__all__ = (
    'SoundBot'
)

SB_COOLDOWN = cfg.soundbank_cooldown
cooldowns = CooldownManager()



def CooldownTag(tag: str):
    """a decorator that adds a cmd.cooldown_tag to a command"""
    def _add_cooldown_tag(self):
        self.cooldown_tag=tag
        return self
    return _add_cooldown_tag


class SoundBot(BaseBot):
    def __init__(self):
        self.irc = Irc()
        self._running = False
        self.pubsub = PubSubClient()
        set_bot(self)


    async def _run_command(self, msg: Message, cmd: Command):
        # mostly a copy of the default _run_command except for the cooldown, exception, and (no) event handling

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
            cooldown_key = cmd.cooldown_tag
        except AttributeError:
            cooldown_key = cmd.fullname

        has_cooldown_bypass_permission = (cfg.enable_cooldown_bypass_permissions and
                                          perms.has_permission(msg.channel_name, msg.author, cmd.cooldown_bypass))

        if ((not has_cooldown_bypass_permission)
                and cooldowns.on_cooldown(key=cooldown_key, required_min_seconds=cmd.cooldown)):
            return await msg.reply(
                f'{cmd.fullname} is on cooldown, seconds left: {cooldowns.seconds_left(key=cooldown_key, required_min_seconds=cmd.cooldown):.1f}')


        # actual execution
        try:
            await cmd.execute(msg)
            if not has_cooldown_bypass_permission:
                cooldowns.set_cooldown(key=cooldown_key)
        except InvalidArgumentsError as e:
            await self._send_cmd_help(msg, cmd.get_sub_cmd(msg.args)[0], e)
        except ValueError as e:
            # it's probably not a great idea to make this a universal handler for all commands when I only need it for !sb...
            # just in case, printing out the error details in the console:
            print(f'there was an error while attempting to execute the command: {e}.')
            return
