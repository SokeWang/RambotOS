---
name: spotify-controller
description: Controls Spotify playback on macOS using AppleScript via a shell utility. Includes play/pause, track skipping, playing liked songs, and playing specific tracks via URIs.
---

# Spotify Controller

## Overview
This skill enables Rambot to control Spotify on macOS. It uses a specialized shell script that bridges AppleScript commands to the Spotify application.

## Core Capabilities

### 1. Playback Control
Use these commands to manage current playback:
- **Play**: `exec "/Users/wangpeidong/Documents/RambotOS/skills/spotify-controller/scripts/control_spotify.sh play"`
- **Pause**: `exec "/Users/wangpeidong/Documents/RambotOS/skills/spotify-controller/scripts/control_spotify.sh pause"`
- **Next Track**: `exec "/Users/wangpeidong/Documents/RambotOS/skills/spotify-controller/scripts/control_spotify.sh next"`
- **Previous Track**: `exec "/Users/wangpeidong/Documents/RambotOS/skills/spotify-controller/scripts/control_spotify.sh prev"`

### 2. Music Selection
- **Play Liked Songs**: `exec "/Users/wangpeidong/Documents/RambotOS/skills/spotify-controller/scripts/control_spotify.sh play_liked_songs"`
- **Play Specific Track**: `exec "/Users/wangpeidong/Documents/RambotOS/skills/spotify-controller/scripts/control_spotify.sh play_track <Spotify_URI>"`
  *Note: To play a specific track, use web search to find the Spotify URI (e.g., spotify:track:...) first.*

## Resources

### scripts/
- `control_spotify.sh`: The main interface for Spotify interaction.

## Protocol Highlights
- **No Direct Script Reading**: Do not attempt to read the `.sh` file. All necessary commands are documented here.
- **Dependency**: Requires Spotify installed on macOS.
