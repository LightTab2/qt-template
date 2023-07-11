#!/bin/bash

maxResolution=0
maxResolutionFile=""

for file in $(find ".." -name "icon_*x*.png"); do
    filename=$(basename "$file")
    width=$(echo "$filename" | awk -F'[_x.]' '{print $2}')
    height=$(echo "$filename" | awk -F'[_x.]' '{print $3}')
    resolution=$((width * height))

    if [ $resolution -gt $maxResolution ]; then
        maxResolution=$resolution
        maxResolutionFile=$file
    fi
done

echo "Creating other icons based on: $maxResolutionFile"

magick convert "$maxResolutionFile" -resize 256x256 "../icon_256x256.png"
magick convert "$maxResolutionFile" -resize 128x128 "../icon_128x128.png"
magick convert "$maxResolutionFile" -resize 64x64 "../icon_64x64.png"
magick convert "$maxResolutionFile" -resize 48x48 "../icon_48x48.png"
magick convert "$maxResolutionFile" -resize 32x32 "../icon_32x32.png"
magick convert "$maxResolutionFile" -resize 16x16 "../icon_16x16.png"
