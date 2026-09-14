# Website redirect (GitHub Pages)

The AndroidLife site source and Vercel deploy live in the private repo
[`YuvrajSingh-mist/androidlife-website`](https://github.com/YuvrajSingh-mist/androidlife-website).

This folder only publishes a redirect so
https://yuvrajsingh-mist.github.io/AndroidLife/ keeps working and forwards
to https://androidlife-website.vercel.app/ (path + query + hash preserved).

For harness setup (repo-relative paths, `$S` from `adb devices`, tested on
MacBook Air M1 2020 + Mac mini M4 2025 16 GB), see the top-level
[README](../README.md).
