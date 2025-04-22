
# GoldSight Trading Bot 🤖💹

Professional Telegram trading bot providing VIP trading signals and market analysis.

## Features 🌟

- Real-time market signals
- VIP subscription system
- Referral program (10% commission)
- 24/7 automated support
- Rate limiting protection

## Subscription Plans 💎

- Bi-weekly: $30
  - 1 weeks full access
  - All trading signals
  - Priority support

- Monthly: $50
  - 3 weeks full access
  - All trading signals
  - Priority support
  - Early market alerts

## Commands 📚

### User Commands
- `/start` - Initialize bot
- `/subscribe` - View VIP plans
- `/referral` - Get referral code
- `/terms` - View terms

### Admin Commands
- `/approve <user_id> <plan>` - Approve subscription
- `/broadcast <message>` - Send VIP announcements

## Technical Details 🔧

- Python 3.12+
- aiogram 3.x
- SQLite3 database
- Rate limiting: 30 req/min
- Automatic subscription tracking
- Thread-safe database operations

## Environment Setup 🛠️

Required environment variables:
```
MAIN_BOT_TOKEN=your_main_bot_token
HELP_BOT_TOKEN=your_help_bot_token
ADMIN_ID=your_admin_id
VIP_CHANNEL_ID=your_channel_id
```

## Support 💬
Contact @GoldSightSupport for assistance
