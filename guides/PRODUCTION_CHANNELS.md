# 🚨 CHANNEL ID REMINDER

## Current Setup (TEST SERVER):
```json
{
  "joy_stickers": 1471318785502740501,
  "monster_hunting": 1471318812610531491,
  "shop": 1471318830046511229,
  "bot_commands": 1471319082862383138
}
```

## Production Server IDs (TO BE UPDATED LATER):
```json
{
  "joy_stickers": 1449316037852921868,  // #daily-dose-of-joy (ORIGINAL)
  "monster_hunting": ???,                 // GET THIS LATER
  "shop": ???,                           // GET THIS LATER
  "bot_commands": ???                    // GET THIS LATER
}
```

---

## ⚠️ BEFORE DEPLOYING TO PRODUCTION:

1. **Create channels in production server:**
   - #monster-hunting
   - #shop  
   - #bot-commands

2. **Get new channel IDs:**
   - Right-click each channel → Copy Channel ID

3. **Update config/config.json:**
   - Replace test IDs with production IDs
   - OR use `!set_channel` commands in production server

4. **Redeploy to Railway**

---

## 🔄 Quick Channel Swap:

**Option 1: Edit config.json before deploy**
```bash
# Open config/config.json
# Replace channel IDs
# Deploy to Railway
```

**Option 2: Use bot commands after deploy**
```
!set_channel joy_stickers #daily-dose-of-joy
!set_channel monster_hunting #monster-hunting
!set_channel shop #shop
!set_channel bot_commands #bot-commands
```

---

## 📝 Notes:
- Bot can work in MULTIPLE servers simultaneously
- Each server can have different channel IDs
- Current config points to TEST server
- Remember to swap before going live!
