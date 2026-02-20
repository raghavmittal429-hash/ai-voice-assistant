[app]
title = AI Voice Assistant
package.name = aivoiceassistant
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
version = 1.0.0
requirements = python3,kivy==2.2.1,kivymd==1.1.1,langchain-ollama==0.0.1,aiohttp==3.8.5,plyer==2.1.0,pillow==10.0.0,typing_extensions==4.7.1,pydantic==2.3.0,numpy==1.24.3,Cython==0.29.33
orientation = portrait
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET,RECORD_AUDIO

# (int) Android API to use
android.api = 33

# (int) Minimum API required
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (str) Android SDK directory
# android.sdk_path = 

# (str) Android NDK directory
# android.ndk_path =

# (list) Source files to include
source.include_patterns = assets/*

[buildozer]
log_level = 2
warn_on_root = 