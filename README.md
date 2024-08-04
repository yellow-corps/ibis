# ibis

A discord bot for the yellow corps

# Features

- Message Auditing (Trusty-cogs/extendedmodlog)
- Message Relaying (coffee-cogs/msgmover)
- Message Purging
- Shopify Orders

# Requirments

- Git
- Docker/Podman
- A Discord App/Bot Token
  - _Adding a Bot to a Discord server is not covered in these instructions._
  - _See [Red-DiscordBot](https://docs.discord.red/en/stable/bot_application_guide.html) Documentation._
- (Optional) A Shopify App Client ID and Client Secret
  - _Best practice is to create an app specifically for the Shopify shop being connected._
  - _See [Shopify Custom Apps](https://help.shopify.com/en/manual/apps/app-types/custom-apps) Documentation._
  - _For the scopes, select `read_orders`._
- (Required for Shopify) An Ngrok Authtoken and Domain
  - _You must use a static domain with Ngrok for this to all work._
  - _As of 04/08/2024, Ngrok allows you to allocate one random static domain to your account._

# Installation

## 1. Clone the Repo

```shell
git clone https://github.com/yellow-corps/ibis
cd ibis
git submodule update --init
```

## 2. Setup Environment

Copy the `.env.example` file to `.env` and fill out the variables within.

## 2a. (Optional) Deploy Shopify

```shell
(cd shopify && npm run install && npm run deploy)
```

This will configure your app on Shopify correctly with the correct Webhooks.

## 3. Run Containers

```shell
docker compose up -d
```

This will do the following:

- Create a number of volumes prefixed with `ibis_`.
  - This is where any settings on the bot will be stored. If you want to migrate the bot and keep any settings, one way would be to migrate these volumes in particular to the new location.
- Create a `discord` container that primary runs the bot.
- If Shopify is configured, `shopify` and `ngrok` containers will also be created.
  - `shopify` is responsible for relaying the Shopify HTTP Webhooks to Discord via JSON RPC calls.
  - `ngrok` is responsible for providing ingress from the outside world to the `shopify` container for the Shopify HTTP Webhooks, without needing to punch holes in firewalls.

# Configuration

> [!NOTE]
>
> Replace any instance of `[@]` below with a mention of the bot.
>
> For example, if the bot is named `Ibis`, replace `[@]` with `@Ibis`.

## 1. Limit Who Can Use The Bot

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

## 2. Configure the Audit Channel

Tell the bot which channel to post audit messages to.

```discorddocke
[@] modlogset modlog #<Channel>
```

_Example_

```discord
[@] modlogset modlog #audit
```

## 3. Configure Message Relays

Tell the bot which channels to relay to other channels.

```discord
[@] msgrelay add #<Source Channel> #<Target Channel>
```

_Example_

```
[@] msgrelay add #source #target
```

## 4. Purge messages when necessary

Use one of the following methods to cleanup messages using the bot.

```
[@] cleanup messages #<Number of messages>
```

An alias exists to cleanup 1000 messages at a time.

```
[@] purge
```

Just keep in mind you will also need to say "Yes" when cleaning up/purging more than 99 messages at a time.

## 5. Configure Shopify

### 5a. Set Shop channel

```
[@] shopify channel #<Shop Channel>
```

_Example_

```
[@] shopify channel #shop
```

### 5b. Set Shop Messages

You can customise the messages that are shown for each status change of an order.

The statuses are `created`, `updated`, `fulfilled`, and `cancelled`

The Order Name (e.g. "Order #1234") is represented in the message as `{}`.

```
[@] shopify message <status> <message>
```

_Example_

```
[@] shopify message created Your {} has been created!
```

_This would appear as..._

> Your Order #1234 has been created!

### 5c. Set Staff Users

Staff Users will always be added to threads created by the bot.

```
[@] shopify staff add @<Staff>
[@] shopify staff remove @<Staff>
```

_Example_

```
[@] shopify staff add @Frontdesk
```
