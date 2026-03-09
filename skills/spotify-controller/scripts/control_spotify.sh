#!/bin/bash
COMMAND=$1
ARG=$2

case $COMMAND in
  "play_liked_songs")
    open -a Spotify
    sleep 1
    osascript -e 'tell application "Spotify" to play track "spotify:collection:tracks"'
    ;;
  "play_track")
    if [ -z "$ARG" ]; then
      echo "Error: Track URI required"
      exit 1
    fi
    open -a Spotify
    sleep 1
    osascript -e "tell application \"Spotify\" to play track \"$ARG\""
    ;;
  "play")
    osascript -e 'tell application "Spotify" to play'
    ;;
  "pause")
    osascript -e 'tell application "Spotify" to pause'
    ;;
  "next")
    osascript -e 'tell application "Spotify" to next track'
    ;;
  "prev")
    osascript -e 'tell application "Spotify" to previous track'
    ;;
  *)
    echo "Usage: $0 {play_liked_songs|play_track <uri>|play|pause|next|prev}"
    exit 1
    ;;
esac
