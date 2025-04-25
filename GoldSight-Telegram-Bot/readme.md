# GoldSight Trading Bot 🤖💹

GoldSight is a professional Telegram bot designed to provide VIP trading signals, market analysis, and a seamless subscription experience. Whether you're a beginner or an experienced trader, GoldSight helps you make informed trading decisions.

---

## Features 🌟

- **Real-Time Market Signals**: Stay updated with accurate and timely trading signals.
- **VIP Subscription System**: Unlock exclusive benefits with our subscription plans.
- **Referral Program**: Earn 10% commission for every successful referral.
- **24/7 Automated Support**: Get assistance anytime with our Help Bot.
- **Rate Limiting Protection**: Prevents abuse and ensures smooth operation.

---

## Subscription Plans 💎

### Bi-Weekly Plan ($30)
- **Duration**: 1 week
- **Benefits**:
  - Full access to all trading signals
  - Priority support

### Monthly Plan ($50)
- **Duration**: 1 month
- **Benefits**:
  - Full access to all trading signals
  - Priority support
  - Early market alerts

---

## Commands 📚

### User Commands
- `/start` - Initialize the bot and view the welcome message.
- `/subscribe` - View available VIP subscription plans.
- `/referral` - Get your referral code to share and earn commissions.
- `/terms` - View the Terms & Conditions.

### Admin Commands
- `/approve <user_id> <plan>` - Approve a user's subscription (bi-weekly/monthly).
- `/broadcast <message>` - Send announcements to VIP members.

---

## Technical Details 🔧

- **Programming Language**: Python 3.12+
- **Framework**: aiogram 3.x
- **Database**: SQLite3
- **Features**:
  - Automatic subscription tracking
  - Thread-safe database operations
  - Rate limiting: 30 requests per minute
- **Deployment**: Compatible with cloud platforms (e.g., Heroku, AWS, etc.)

---

## Environment Setup 🛠️

To run the bot, ensure the following environment variables are set:

```plaintext
MAIN_BOT_TOKEN=your_main_bot_token
HELP_BOT_TOKEN=your_help_bot_token
ADMIN_ID=your_admin_id
VIP_CHANNEL_ID=your_channel_id
```

### Installation Steps:
1. Clone the repository:
   ```bash
   git clone https://github.com/japhetjohn/GoldSight-Telegram-Bot.git
   cd GoldSight-Telegram-Bot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Create a `.env` file in the root directory.
   - Add the required variables as shown above.

4. Run the bot:
   ```bash
   python main.py
   ```

---

## Referral Program 💰

GoldSight offers a **10% commission** for every successful referral. Share your referral code with others and earn rewards when they subscribe to a VIP plan.

---

## Terms & Conditions 📜

1. **No Refund Policy**: Payments made for VIP access are non-refundable.
2. **Educational Purpose**: All trading signals are for educational purposes only.
3. **Trade Responsibly**: Users are advised to trade responsibly and within their financial capacity.
4. **Payment Issues**: For any payment-related issues, contact support at [@GoldSightSupport](https://t.me/GoldSightSupport).
5. **Subscription Renewal**: Subscriptions must be renewed manually to avoid service interruptions.
6. **Privacy Policy**: We do not share your personal information with third parties.

---

## Support 💬

For assistance, contact our support team at [@GoldSightSupport](https://t.me/GoldSightSupport). We’re here to help you with any questions or issues.

---

## License 📄

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

## Contributing 🤝

We welcome contributions to improve GoldSight! Feel free to submit a pull request or open an issue for suggestions.

---

## Disclaimer ⚠️

GoldSight provides trading signals for educational purposes only. We are not responsible for any financial losses incurred while using our services. Always trade responsibly.