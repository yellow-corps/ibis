# ibis-logger

Simple logger service to pipe any docker logs that contain "error" or "warn" to a Discord channel webhook

## Setup

### 1. Setup Channel Webhook

1. Create a channel in a server, such as `#errors`
2. Create a webhook for it via the "Integrations" tab while editing said channel, and copy the Webhook URL
3. Modify your `.env` file, and supply the URL to the `ERROR_WEBHOOK_URL` environment variable

### 2. Setup Service File

1. Modify ibis-logger.service, and replace all instances of `/path/to/ibis` with the path to the **root** of this project (i.e. not the folder containing the readme you're currently reading, but one up)
2. Copy or make a link of the file to `/etc/systemd/system/ibis-logger.service`
3. `systemctl daemon-reload`
4. `systemctl start ibis-logger`

## Notes

This is a very basic attempt at logging, just to try and raise alerts for any errors coming out of the bot. Do not expect robustness from this approach!

The intent is to alert you to potential problems - you must investigate further yourself.
