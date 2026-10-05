# Auto Tagger

Automatically apply tags to threads in forum channels.

## Usage

- Must be a bot admin to use commands.
- Instanced per channel.

Tags will be applied as follows:

- Threads with `exclude_tag` will be ignored, if that is configured.
- `off_tag` will be applied whenever a thread is created without either tag.
- To the best of the cog's ability, one of either `off_tag` or `on_tag` will be maintained on all threads.

### Load

```discord
[@] load autotagger
```

### Setup automatic tagging

Configure autotagging per forum channel.

```discord
// list autotaggers in server
[@] autotagger list

// enable autotagging on a channel
[@] autotagger enable #<forum channel> <off tag> <on tag> [<exclude tag>]
// Quote tags that have spaces. Tags are case-insensitively matched.
[@] autotagger enable #forum "nOt AnSwErEd" Answered "ignore THIS one"

// disable autotagging on a channel
[@] autotagger disable #<forum channel>
```

### Gotchas

- Discord only allows up to 5 tags per thread.
  Autotagging will fail to apply correctly on threads at the limit.
