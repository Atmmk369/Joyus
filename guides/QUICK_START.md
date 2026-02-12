# 🚀 Quick Start Guide - Bot v3.0

## ✅ What's Ready to Test

Your bot is now ready to deploy with:
- ✅ PostgreSQL database (no data loss!)
- ✅ Joy streak tracking (preserved from v2)
- ✅ HP system (10 HP/level for peasants)
- ✅ Channel enforcement (wrong channel = -5 XP)
- ✅ Class selection at Level 3
- ✅ Coin claiming (1 coin/level daily)
- ✅ Admin commands (reset, give XP/coins/items)
- ✅ Profile, leaderboard, class info commands

## 📦 Files You Have

### Core Bot Files:
- `joy_streak_bot.py` - Main bot file
- `database.py` - PostgreSQL database manager
- `admin.py` - Admin commands module
- `requirements.txt` - Python dependencies
- `.env.example` - Environment variable template

### Data Files (Easy to Edit):
- `data/monsters.json` - 12 monsters defined (not used yet)
- `data/items.json` - 20+ items defined (not used yet)
- `data/classes.json` - All 5 classes with HP formulas
- `data/achievements.json` - 25+ achievements (not used yet)

### Configuration:
- `config/config.json` - **Updated with your TEST channel IDs**

### Documentation:
- `RAILWAY_SETUP.md` - Step-by-step deployment
- `PRODUCTION_CHANNELS.md` - Reminder to swap IDs later
- `QUICK_START.md` - This file!

---

## 🚂 Deploy to Railway (5 Minutes)

### Step 1: Add PostgreSQL
1. Open your Railway project
2. Click "+ New" → "Database" → "Add PostgreSQL"
3. Done! `DATABASE_URL` is auto-set

### Step 2: Upload Files
**Option A: GitHub (Recommended)**
```bash
# Create GitHub repo, upload all files
# Connect to Railway
# Railway auto-deploys
```

**Option B: Railway CLI**
```bash
npm install -g @railway/cli
railway login
railway link
railway up
```

### Step 3: Set Environment Variables
In Railway → Your Service → Variables:
```
DISCORD_BOT_TOKEN=your_bot_token_here
```
(DATABASE_URL is already set by PostgreSQL service)

### Step 4: Set Start Command
Railway → Settings → Deploy:
```
Start Command: python joy_streak_bot.py
```

### Step 5: Deploy!
Railway will automatically deploy. Check logs for:
```
✅ Database connected successfully
✅ Database schema initialized
Daily Dose of Joy#2195 has connected to Discord!
```

---

## 🧪 Test in Your Test Server

### Channel IDs (Already Configured):
- Daily Joy: `1471318785502740501`
- Hunting: `1471318812610531491`
- Shop: `1471318830046511229`
- Bot Commands: `1471319082862383138`

### Commands to Test:

**In #daily-dose-of-joy:**
1. Send Joy sticker → Should get XP
2. Send Joy again → Should break streak
3. Wait until tomorrow → Send Joy → Should maintain streak

**In #bot-commands:**
```
!profile              - View your profile
!claim                - Claim daily coins
!selectclass          - Choose class (once level 3)
!classes              - View all classes
!leaderboard level    - View rankings
!joyhelp             - Help menu
```

**Admin Commands (Work in ANY channel):**
```
!reset_all            - Wipe database (requires confirmation)
!give_xp @user 1000   - Give XP to reach level 3 quickly
!give_coins @user 500 - Give coins for testing
!bot_stats            - View bot statistics
!newday               - 🧪 Force new day (testing daily mechanics)
```

**🧪 Testing Daily Progression with !newday:**

The `!newday` command is perfect for testing! It:
- ✅ Lets you send Joy again (clears daily tracking)
- ✅ Lets you claim coins again
- ✅ Keeps your streak intact (no reset)
- ✅ Keeps your XP intact

**Test Flow:**
1. Send Joy → Get 30 XP
2. Try to send again → Breaks streak (expected)
3. Use `!newday` → Resets daily tracking
4. Send Joy again → Get 30 XP, streak continues!
5. Repeat to test progression over "days"

**Test Wrong Channel Penalty:**
- Try `!profile` in #daily-dose-of-joy
- Should get: "⚠️ Wrong Channel! -5 XP"

---

## 🎯 Testing Checklist

- [ ] Bot comes online in Discord
- [ ] Send Joy sticker → Get XP
- [ ] Use `!profile` → See stats
- [ ] Try wrong channel → Get penalty
- [ ] Use `!give_xp @yourself 1000` → Level up
- [ ] Reach level 3 → `!selectclass` works
- [ ] Select a class → HP updates
- [ ] Use `!claim` → Get coins
- [ ] Send Joy again same day → Streak breaks
- [ ] Check `!leaderboard`
- [ ] **Use `!newday`** → Daily tracking resets
- [ ] Send Joy again → Streak continues, get XP
- [ ] Use `!claim` again → Get more coins
- [ ] Repeat `!newday` cycle to test daily progression

---

## 🐛 Troubleshooting

### Bot Won't Start
- Check logs for errors
- Verify `DISCORD_BOT_TOKEN` is set
- Verify PostgreSQL service is running
- Check `DATABASE_URL` exists

### Commands Don't Work
- Make sure bot has "Send Messages" permission
- Check you're in the right channel
- Try with `!` prefix

### Channel Enforcement Not Working
- Verify channel IDs are correct
- Use `!set_channel <type> #channel` to update

---

## 🎮 What's Coming Next

Once you test and verify the foundation works:

**Phase 2: Combat System**
- Monster hunting in #monster-hunting
- DnD-style combat with rolls
- Depth mechanic (deeper = harder)
- Co-op monster fights
- Loot drops

**Phase 3: Shop System**
- Buy items in #shop
- Rotating inventory
- Item effects (weapons, armor, potions)
- Equipment system

**Phase 4: Advanced Features**
- Achievement tracking
- Trap system (PvP)
- Fishing minigame
- Tycoon/mining system

---

## 📞 Need Help?

- Check `RAILWAY_SETUP.md` for detailed deployment
- Check logs in Railway dashboard
- Test admin commands to debug issues

---

## ✅ You're Ready!

Deploy the bot, test in your test server, and let me know when you're ready for the combat system! 🎮⚔️
