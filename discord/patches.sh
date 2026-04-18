#!/bin/sh

set -ex

BASE_DIR="$(pip show Red-DiscordBot | grep 'Location:' | awk '{print $2}' )"

function patch() {
  local file="$BASE_DIR/$1"
  local temp="$file.temp"
  local from="$2"
  local to="$3"
  sed -e "s/$from/$to/" $file > "$temp"
  if cmp --silent "$file" "$temp"; then
    echo "contents of $file did not change!"
    exit 1
  fi
  rm "$file"
  mv "$temp" "$file"
}

# disable startup version check DM - it's so annoying!!
patch 'redbot/core/_events.py' 'await send_to_owners_with_prefix_replaced(bot, outdated_red_message)' 'pass'

# rename invite command so we can alias invite to other things
patch 'redbot/core/core_commands.py' 'async def invite\b' 'async def botinviteurl'

# remove deprecated shutdown_timeout assignment
patch 'redbot/core/_rpc.py' 'shutdown_timeout=120' ''

# otel patching (easier to understand for now)
patch 'discord/ext/commands/bot.py' 'import discord' 'import discord\nimport ibis.otel_intercept'
patch 'discord/ext/commands/bot.py' '    async def invoke(self, ctx: Context\[BotT\], \/) -> None\:' '    async def invoke(self, ctx: Context[BotT], \/) -> None:\n        await ibis.otel_intercept.invoke_intercept(ctx, self.invoke_orig)\n    async def invoke_orig(self, ctx: Context[BotT], \/) -> None:'
