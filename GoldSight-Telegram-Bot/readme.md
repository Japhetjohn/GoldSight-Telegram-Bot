# GoldSight Telegram Bot

Welcome to *GoldSightBot*, a Telegram bot built to manage a VIP trading signals channel for XAUUSD (Gold/USD). This bot handles automated signals, VIP subscriptions, referral commissions, spam filtering, and a help bot—all coded from scratch by Japhet and powered by aiogram, sqlite3, and Alpha Vantage API.

---

## Features

- *Channel Management*:
  - Auto-posts XAUUSD signals every 5 minutes via Alpha Vantage (GLOBAL_QUOTE).
  - Restricts “Goldsight VIP” channel to VIPs only—non-VIPs get deleted + warned.
  - Manual signal posting with /signal (admin only).

- *VIP Subscription System*:
  - Plans: $30 Bi-Weekly or $50 Monthly via /subscribe.
  - Payment proof submission (screenshots/text) to admin.
  - Admin approval with /approve <user_id> <plan>.
  - Auto-expiration and 2-day reminders via SQLite database.

- *Referral Program*:
  - Earn 10% commission ($3 bi-weekly, $5 monthly) per paid referral.
  - Get your link with /referral, share it, and cash in.

- *Help Bot*:
  - @Goldsighthelpbot answers FAQs (/faq) and forwards live support to admin.
  - Quick replies for “how to join”, “cost”, and “support”.

- *Signals*:
  - Automated: Latest XAUUSD price every 5 mins with network retries and fallback.
  - Manual: Post custom signals to VIP channel with /signal.

- *Payment Verification*:
  - Manual proof submission via Telegram—admin approves.

---

## Prerequisites

- *Python*: 3.12+
- *Libraries*: aiogram, sqlite3, requests, python-dotenv
- *Telegram*: Two bot tokens (main + help) from [@BotFather](https://t.me/BotFather)
- *Alpha Vantage*: Free API key from [alphavantage.co](https://www.alphavantage.co)

---

## Setup

1. *Clone or Download*:
   - Grab this repo or copy the files to C:\Users\YourName\Desktop\GoldSight-Telegram-Bot.

2. *Install Dependencies*:
   ```bash
   pip install aiogram sqlite3 requests python-dotenv
