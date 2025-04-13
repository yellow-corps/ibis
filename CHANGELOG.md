# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.3.0] - 2025-04-13

### Added

- SOS Tickets, a cog to handle an emergency ticket system using text channels

### Updated

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

### Fixed

- Fixed error in command in README
- Clarified installation requirements in README (requires Node.js for Shopify functionality)

### Changed

- Changed ngrok to always restart unless stopped
- Taught Shopify cog to fuzzy match customers as a plan B

## [1.0.0] - 2024-09-01

- Initial Release

<!-- Versions -->

[Unreleased]: https://github.com/yellow-corps/ibis/compare/v1.3.0...HEAD
[1.3.0]: https://github.com/yellow-corps/ibis/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/yellow-corps/ibis/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/yellow-corps/ibis/releases/tag/v1.1.0
[1.0.0]: https://github.com/yellow-corps/ibis/releases/tag/v1.0.0
