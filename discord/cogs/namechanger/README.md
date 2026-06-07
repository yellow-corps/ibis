# Name Changer

*It's been here the whole time!*

A cog for handling Enforcer handle change requests.

## Usage

* Must be a bot admin to use commands.
* Instanced per guild.

### Load

```discord
[@] load namechanger
```

### Setup Responders

Control the users automatically added to any requests to review them.

```discord
// list responders
[@] namechanger responders

// add responders
[@] namechanger responders add @<user or role> [...@<user or role>]

// remove responders
[@] namechanger responders remove @<user or role> [...@<user or role>]
```

### Setup Request Button

> [!NOTE]
>
> * If used in a `TextChannel`, requests will be created as private threads.
>   * The bot will encounter an error if it does not have permission to create private threads
>     in the channel the button appears in.
> * If used in a `ForumChannel`, requests will be created as public threads.
>   * This is because `ForumChannel`s do not allow private threads at this time.

The Request Button can be assigned into any `ForumChannel`, `TextChannel`, or thread of a
`TextChannel`.

Any requests made via said button will appear in its own thread in the same channel.

```discord
[@] namechanger create #<channel or thread>
```

## Development

### Rules

#### Warnings

Warnings won't stop a request, but will show up in the resulting thread.

* Handle is similar to another handle and may cause confusion.
  * Similar handles will be detailed in the validation result.
* Handle possibly contains swear words or slurs.
  * Swear words or slurs will not be detailed. If the swear word or slur is not obvious, ignore this validation result.
* andle contains too many digits (>50%)
  * Main intention is to avoid handles that cannot be easily pronounced.

#### Errors

Errors will stop a request, and will show up immediately as a private ephemeral response to the requesting user.

* Handles must be between 3 and 20 characters in length.
* Handles must only contain letters, numbers, hyphens, underscores, periods, and spaces.
* Handles cannot have sequential hyphens, underscores, periods, or spaces.
* Handles cannot start or end with hyphens, underscores, periods, or spaces.

### profanity.txt

* Each line is a swear word or slur.
* Individually base64 encoded so they don't have to be present in original form in the repo.
* Taken from the npm package [@2toad/profanity](https://github.com/2Toad/Profanity).
