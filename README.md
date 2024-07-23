# ibis

A discord bot for the yellow corps

## Features

- Message Auditing (Trusty-cogs/extendedmodlog)
- Message Relaying (coffee-cogs/msgmover)
- Message Purging

## Requirments

- Git
- Docker/Podman
- A Discord App/Bot Token
  - _Adding a Bot to a Discord server is not covered in these instructions._
  - _See [Red-DiscordBot](https://docs.discord.red/en/stable/bot_application_guide.html) Documentation._

## Installation

### Clone the Repo

```shell
git clone https://github.com/yellow-corps/ibis
cd ibis
git submodule update --init
```

### Setup Token

Create a file, `.env`, with the following contents.

```
RED_TOKEN=<discord token>
```

### Run Container

```shell
docker compose up -d
```

## After Setup

> [!NOTE]
>
> Replace any instance of `[@]` below with a mention of the bot.
>
> For example, if the bot is named `Ibis`, replace `[@]` with `@Ibis`.

### 1. Limit Who Can Use The Bot

Add one or more people to the allowlist for the bot, starting with yourself.

```discord
[@] allowlist add @<User>
[@] allowlist remove @<User>
[@] allowlist list
[@] allowlist clear
```

_Example_

```discord
[@] allowlist add @SpiltCoffee
```

This should prevent any unintended actions from the bot taking place.

### 2. Configure the Audit Channel

Tell the bot which channel to post audit messages to.

```discorddocke
[@] modlogset modlog #<Channel>
```

_Example_

```discord
[@] modlogset modlog #audit
```

### 3. Configure Message Relays

Tell the bot which channels to relay to other channels.

```discord
[@] msgrelay add #<Source Channel> #<Target Channel>
```

_Example_

```
[@] msgrelay add #source #target
```

### 4. Purge messages when necessary

Use one of the following methods to cleanup messages using the bot.

```
[@] cleanup messages #<Number of messages>
```

An alias exists to cleanup 1000 messages at a time.

```
[@] purge
```
