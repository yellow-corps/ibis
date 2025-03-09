# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/yellow-corps/ibis/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/yellow-corps/ibis/releases/tag/v1.1.0
[1.0.0]: https://github.com/yellow-corps/ibis/releases/tag/v1.0.0
