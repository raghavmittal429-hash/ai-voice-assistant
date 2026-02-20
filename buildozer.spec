[app]
title = AI Voice Assistant
package.name = aivoiceassistant
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
version = 1.0.0

# Match your requirements.txt exactly
requirements = python3,kivy==2.2.1,kivymd==1.1.1,langchain-ollama==0.0.1,aiohttp==3.8.5,plyer==2.1.0,pillow==10.0.0,typing_extensions==4.7.1,pydantic==2.3.0,numpy==1.24.3,Cython==0.29.33

orientation = portrait
fullscreen = 0

# ... other settings ...

# Android SDK/NDK paths (leave empty for auto-download)
android.sdk_path = 
android.ndk_path = 

# Android specific
android.permissions = INTERNET,RECORD_AUDIO
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a

# Include assets
source.include_patterns = assets/*

[buildozer]
log_level = 2
warn_on_root = 1

# Increase timeout for SDK downloads
android.accept_sdk_license = True