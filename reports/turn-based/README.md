# Turn-based ASK USER audits (public)

Full per-turn audits of every ASK USER interaction (question → answer), one
date-time folder per run — same convention as `assets/db/public/<run-ts>/`:

```
reports/turn-based/
├── README.md
├── ask-query-single/<run-ts>/<task>.md
└── ask-query-multi/<run-ts>/<task>.md
```

Runs present: `2026-08-20-003030`, `2026-08-22-195244`

## ask-query-single/
| Run | Task | Day | # asks | Asked? | Fact |
|---|---|---|---|---|---|
| 2026-08-22-195244 | [hard__chrome-telegram-notes__008](ask-query-single/2026-08-22-195244/hard__chrome-telegram-notes__008.md) | day2 | 1 | ✅ asked | The item is wireless earbuds. |
| 2026-08-22-195244 | [hard__chrome-youtube-notes__088](ask-query-single/2026-08-22-195244/hard__chrome-youtube-notes__088.md) | day3 | 1 | ✅ asked | The task is changing a bike tyre. |
| 2026-08-22-195244 | [hard__drive-notes-telegram__010](ask-query-single/2026-08-22-195244/hard__drive-notes-telegram__010.md) | day1 | 0 | ❌ never asked | Message Yuvraj Airtel about the budget spreadsheet. |
| 2026-08-22-195244 | [hard__google-search-obsidian-telegram__057](ask-query-single/2026-08-22-195244/hard__google-search-obsidian-telegram__057.md) | day3 | 0 | ❌ never asked | Message Yuvraj Singh Jio when it crosses the threshold. |
| 2026-08-22-195244 | [hard__google-search-telegram-clock__018](ask-query-single/2026-08-22-195244/hard__google-search-telegram-clock__018.md) | day2 | 2 | ✅ asked | The place is the SBI ATM. The person to message is Yuvraj Si |
| 2026-08-22-195244 | [hard__photos-gmail-obsidian__012](ask-query-single/2026-08-22-195244/hard__photos-gmail-obsidian__012.md) | day2 | 0 | ❌ never asked | The event is the Bhubaneswar trip. |
| 2026-08-22-195244 | [medium__google-search__008](ask-query-single/2026-08-22-195244/medium__google-search__008.md) | day3 | 1 | ✅ asked | The route is from IIIT Bhubaneswar to Bhubaneswar Airport. |

## ask-query-multi/
| Run | Task | Day | # asks | Asked? | Fact |
|---|---|---|---|---|---|
| 2026-08-20-003030 | [hard__gmail-calendar__003](ask-query-multi/2026-08-20-003030/hard__gmail-calendar__003.md) | day2 | 0 | ❌ never asked | multiturn_kb: gmail-calendar::bbi-del-reminder |
| 2026-08-22-195244 | [hard__gmail-calendar__003](ask-query-multi/2026-08-22-195244/hard__gmail-calendar__003.md) | day2 | 1 | ✅ asked | multiturn_kb: gmail-calendar::bbi-del-reminder |
| 2026-08-22-195244 | [hard__music-obsidian__077](ask-query-multi/2026-08-22-195244/hard__music-obsidian__077.md) | day2 | 0 | ❌ never asked | multiturn_kb: youtube-music::sleep-timer-1030pm |
| 2026-08-22-195244 | [hard__swiggy__005](ask-query-multi/2026-08-22-195244/hard__swiggy__005.md) | day1 | 1 | ✅ asked | multiturn_kb: swiggy::reorder-downtown-delight-murgh-mughlai |
| 2026-08-22-195244 | [hard__telegram-calendar__016](ask-query-multi/2026-08-22-195244/hard__telegram-calendar__016.md) | day1 | 5 | ✅ asked | multiturn_kb: telegram::forever-21-meetup-sat-7pm |

