# TuriChips Android app

A Capacitor shell around the chat in `ops/chat`. The app holds no chat code: it opens
`https://turichips.tail5e9d29.ts.net`, which is the VM's chat served over Tailscale, so web
changes go live without a new build. If the phone can't reach it (Tailscale off), it shows
`www/offline.html`.

- **Phone:** install the Tailscale app, sign in to the same tailnet, then install the APK.
- **VM:** `sudo tailscale serve --bg 8600` publishes the localhost-only chat to the tailnet over HTTPS.
  Nothing is exposed to the public internet.
- **Build** (needs JDK 21 and the Android SDK):
  ```
  npm install
  echo "sdk.dir=$HOME/Android/Sdk" > android/local.properties
  JAVA_HOME=~/.local/jdk-21 npm run apk
  ```
  The output is `android/app/build/outputs/apk/debug/app-debug.apk`.
- Install with `adb install -r <apk>` over USB, or copy the APK to the phone and open it.
