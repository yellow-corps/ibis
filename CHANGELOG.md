# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- A backup cog, which invokes `redbot-setup backup` and uploads it

## [1.7.5] - 2025-10-10

### Added

- Aliases resolve and prune for SOS Tickets cog

### Changed

- Shopify container no longer waits for Shopify cog response
- Naive Shopify fulfill delay extended to 30s

### Fixed

- Bug in SOS Tickets cog with resolve and prune commands

## [1.7.4] - 2025-10-10

### Added

- A prune command to the SOS Tickets cog

### Changed

- Changed SOS tickets resolve command to only work if in active category

## [1.7.3] - 2025-10-10

### Changed

- Delay fulfill events by 10s in naive attempt to address race condition with create events

## [1.7.2] - 2025-10-10

### Changed

- Extend timeout for Shopify webhook to 60s

### Fixed

- Faulty error reporting in Shopify container

## [1.7.1] - 2025-10-06

### Changed

- Catch and log exceptions thrown when calling bot in Shopify container

## [1.7.0] - 2025-09-24

### Removed

- Remove linux/arm64 docker container (it's just taking waaaay too long!)

## [1.6.2] - 2025-09-24

### Changed

- Better handle exceptions around exporting SOS Ticket channels

### Fixed

- README instructions for configuring SOS Tickets

## [1.6.1] - 2025-09-20

### Fixed

- Bug in adding Shopify users to threads

## [1.6.0] - 2025-09-04

### Changed

- Unique Invites `create` defaults to 1 invite
- Core `invite` command renamed to `botinviteurl`

## [1.5.4] - 2025-07-06

### Fixed

- Crash in Shopify cog when attempting to add members that do not have permission to see the current channel

## [1.5.3] - 2025-06-26

### Fixed

- Various problems with the Shopify cog (webhooks, staff members)

## [1.5.2] - 2025-06-25

### Fixed

- Crash in Shopify cog when handling products

## [1.5.1] - 2025-06-25

### Removed

- Debug line in CSV Members cog

## [1.5.0] - 2025-06-19

### Added

- CSV Members, a cog that outputs a list of members in a server in a CSV

## [1.4.1] - 2025-04-17

### Changed

- Support linux/amd64 and linux/arm64 platforms for containers

### Fixed

- Fix inability to build duckdb on Alpine Linux in some circumstances

## [1.4.0] - 2025-04-16

### Added

- Persist Messages, a cog to persist messages beyond restarts.

### Fixed

- Fix bug in how SOS Tickets handled messages from DMs (in that it shouldn't be handling them)

## [1.3.2] - 2025-04-14

### Fixed

- Fix first SOS ticket using -true instead of -1
- Fix bug in @ sostickets export command

## [1.3.1] - 2025-04-13

### Fixed

- Fix mistake in Shopify container CMD

## [1.3.0] - 2025-04-13

### Added

- SOS Tickets, a cog to handle an emergency ticket system using text channels

### Changed

- Refactored Shopify cog code to use better practices
- Updated Shopify container code to avoid vulnerable dependencies
- Switched Shopify container to -alpine to avoid vulnerable dependencies
- Updated UniqueInvites cog code to use better practices
- Switched Discord container to -alpine to avoid vulnerable dependencies
- Eradicated the startup version check DM

## [1.2.0] - 2025-03-29

### Added

- UniqueInvites, a cog to create single use, non-expiring, unique invites

### Changed

- Bump dependencies to latest:
  - Red-DiscordBot to 3.5.17
  - wheel to 0.45.1
  - dropped aiohttp as Red-DiscordBot already requests same version

## [1.1.0] - 2024-10-06

### Added

- Added a basic system of logging

### Changed

- Changed ngrok to always restart unless stopped
- Taught Shopify cog to fuzzy match customers as a plan B

### Fixed

- Fixed error in command in README
- Clarified installation requirements in README (requires Node.js for Shopify functionality)

## [1.0.0] - 2024-09-01

- Initial Release

[Unreleased]: https://github.com/yellow-corps/ibis/compare/v1.7.5...HEAD
[1.7.5]: https://github.com/yellow-corps/ibis/compare/v1.7.4...v1.7.5
[1.7.4]: https://github.com/yellow-corps/ibis/compare/v1.7.3...v1.7.4
[1.7.3]: https://github.com/yellow-corps/ibis/compare/v1.7.2...v1.7.3
[1.7.2]: https://github.com/yellow-corps/ibis/compare/v1.7.1...v1.7.2
[1.7.1]: https://github.com/yellow-corps/ibis/compare/v1.7.0...v1.7.1
[1.7.0]: https://github.com/yellow-corps/ibis/compare/v1.6.2...v1.7.0
[1.6.2]: https://github.com/yellow-corps/ibis/compare/v1.6.1...v1.6.2
[1.6.1]: https://github.com/yellow-corps/ibis/compare/v1.6.0...v1.6.1
[1.6.0]: https://github.com/yellow-corps/ibis/compare/v1.5.4...v1.6.0
[1.5.4]: https://github.com/yellow-corps/ibis/compare/v1.5.3...v1.5.4
[1.5.3]: https://github.com/yellow-corps/ibis/compare/v1.5.2...v1.5.3
[1.5.2]: https://github.com/yellow-corps/ibis/compare/v1.5.1...v1.5.2
[1.5.1]: https://github.com/yellow-corps/ibis/compare/v1.5.0...v1.5.1
[1.5.0]: https://github.com/yellow-corps/ibis/compare/v1.4.1...v1.5.0
[1.4.1]: https://github.com/yellow-corps/ibis/compare/v1.4.0...v1.4.1
[1.4.0]: https://github.com/yellow-corps/ibis/compare/v1.3.2...v1.4.0
[1.3.2]: https://github.com/yellow-corps/ibis/compare/v1.3.1...v1.3.2
[1.3.1]: https://github.com/yellow-corps/ibis/compare/v1.3.0...v1.3.1
[1.3.0]: https://github.com/yellow-corps/ibis/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/yellow-corps/ibis/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/yellow-corps/ibis/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/yellow-corps/ibis/releases/tag/v1.0.0
