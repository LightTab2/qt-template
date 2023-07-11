@echo off
setlocal enabledelayedexpansion

set "maxResolution=0"

for /r ".." %%F in (icon_*x*.png) do (
    for /f "tokens=2,3 delims=_x." %%A in ("%%~nxF") do (
        set "width=%%A"
        set "height=%%B"
        set /a "resolution=width * height"
        if !resolution! gtr !maxResolution! (
            set "maxResolution=!resolution!"
            set "maxResolutionFile=%%F"
        )
    )
)
echo "Creating other icons based on: %maxResolutionFile%"
magick convert "%maxResolutionFile%" -resize 256x256 "../icon_256x256.png"
magick convert "%maxResolutionFile%" -resize 128x128 "../icon_128x128.png"
magick convert "%maxResolutionFile%" -resize 64x64 "../icon_64x64.png"
magick convert "%maxResolutionFile%" -resize 48x48 "../icon_48x48.png"
magick convert "%maxResolutionFile%" -resize 32x32 "../icon_32x32.png"
magick convert "%maxResolutionFile%" -resize 16x16 "../icon_16x16.png"