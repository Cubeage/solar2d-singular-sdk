# solar2d-singular

<p align="center"><img src="https://mark.sylphx.com/api/v1/mark/hero.svg?type=aurora&color=0:A02028,50:E03840,100:1A1A1A&text=solar2d-singular&desc=Solar2D%20plugin%20for%20Singular%20attribution" alt="solar2d-singular" /></p>

Solar2D plugin for [Singular](https://www.singular.net/) Attribution SDK.

## Installation

Add to your  plugins:

```lua
["plugin.singular"] = {
    publisherId = "com.cubeage",
    supportedPlatforms = {
        android = { url = "https://github.com/Cubeage/solar2d-singular-sdk/releases/download/v1.0.0/android.tgz" },
        iphone  = { url = "https://github.com/Cubeage/solar2d-singular-sdk/releases/download/v1.0.0/iphone.tgz" },
        ["mac-sim"]  = false,
        ["win32-sim"] = false,
    },
},
```

## Lua API

```lua
local Singular = require("plugin.singular")

-- Initialize (call once at app start)
Singular.init({ apiKey = "YOUR_API_KEY", secretKey = "YOUR_SECRET_KEY" })

-- Track event
Singular.event("EventName")
Singular.event("EventName", { key = "value" })

-- Report ad revenue
Singular.adRevenue({ adPlatform = "ironSource", currency = "USD", revenue = 0.05 })
```

## SDK Versions
- Android: [`android/build.gradle`](android/build.gradle) declares the Singular SDK version; [`android/corona.gradle`](android/corona.gradle) supplies it to consuming apps.
- iOS: Singular-SDK (coming soon)

## Android validation and releases

`Build Android` compiles and assembles the Android library on every pull request,
merge group and push to `main`, without path filters. It also checks that
`android.tgz` contains the compiled `plugin.singular.LuaLoader` entry point,
Android manifest, and unchanged source copies of `metadata.lua` and
`corona.gradle`. The `ci-ok` job succeeds only when the build and package checks
succeed; a failed, cancelled or skipped build cannot pass it. Repository rules
must require this context to enforce it; defining a workflow alone does not
install branch protection.

The workflow pins and verifies its compile-only Solar2D SDK download. It does
not bundle the Solar2D runtime or change the plugin's Lua API or Singular SDK
dependency. Package smoke checks do not prove attribution behavior on a device.

Run the fast regression checks with `python3 -m unittest discover -s tests -v`.
With Java 17, Android SDK platform 34/build tools 34.0.0 and the compile-only
Corona classes available, build with `cd android && sh ./gradlew assembleRelease`.
Check the resulting package with `python3 scripts/check_android_package.py android.tgz`.

Tag pushes matching `v*` still call the same Android build and publish
`android.tgz` through `Release`. The workflow artifact remains `android-plugin`;
inside the package the consumer filenames remain `plugin-release.aar`,
`corona.gradle` and `metadata.lua`. CI changes alone do not publish a release
or change the existing installation URLs.
