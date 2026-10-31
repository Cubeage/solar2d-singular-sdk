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
- Android: com.singular.sdk:singular_sdk:12.6.3
- iOS: Singular-SDK (coming soon)
