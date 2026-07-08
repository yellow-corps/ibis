# Export

Export a channel as text or HTML.

## Usage

- Must be a bot owner to use commands.
- Instanced per guild.
- Must be running `export` container in dev cluster.

### Load

```discord
[@] load export
```

### Export channels

Note that the bot will reply to you where you run the command. Don't run this in public channels if
the channel you're exporting is private.

```discord
// export as text
[@] export text #[TextChannel or ForumChannel]

// export as HTML
[@] export html #[TextChannel or ForumChannel]
```
