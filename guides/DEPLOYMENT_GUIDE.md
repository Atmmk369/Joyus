# 🚀 Step-by-Step Deployment Guide (Beginner-Friendly)

## 📁 Part 1: Organize Your Files (5 minutes)

### Step 1: Download All Files
Download these files I provided to a folder on your computer:

**Create this folder structure on your computer:**
```
C:\Users\YourName\Documents\joy-streak-bot\
```
(Or wherever you want - just remember the location!)

### Step 2: Extract Files Into This Structure

**Main folder should look like this:**
```
joy-streak-bot/
├── joy_streak_bot.py
├── database.py
├── admin.py
├── requirements.txt
├── .env.example
│
├── data/
│   ├── monsters.json
│   ├── items.json
│   ├── classes.json
│   └── achievements.json
│
├── config/
│   └── config.json
│
└── (optional documentation files)
    ├── QUICK_START.md
    ├── RAILWAY_SETUP.md
    └── PRODUCTION_CHANNELS.md
```

**CRITICAL FILES (Must have these):**
- ✅ `joy_streak_bot.py` (main bot file)
- ✅ `database.py` (database manager)
- ✅ `admin.py` (admin commands)
- ✅ `requirements.txt` (dependencies)
- ✅ `data/` folder with all 4 JSON files
- ✅ `config/` folder with config.json

### Step 3: Create .env File

1. Copy `.env.example` and rename it to `.env`
2. Open `.env` in Notepad
3. Add your bot token:
```
DISCORD_BOT_TOKEN=YOUR_ACTUAL_BOT_TOKEN_HERE
DATABASE_URL=will_be_added_by_railway
```
4. Save and close

**⚠️ IMPORTANT:** The `.env` file will NOT be uploaded to GitHub (for security)

---

## 📤 Part 2: Upload to GitHub (10 minutes)

### Option A: Using GitHub Desktop (Easiest)

#### Step 1: Install GitHub Desktop
1. Go to https://desktop.github.com/
2. Download and install
3. Sign in with your GitHub account (create one if needed at github.com)

#### Step 2: Create Repository
1. Open GitHub Desktop
2. Click **"File"** → **"New Repository"**
3. Fill in:
   - **Name:** `joy-streak-bot`
   - **Description:** `Discord bot for Joy streaks with RPG mechanics`
   - **Local Path:** Click "Choose..." and select your `joy-streak-bot` folder
   - ✅ Check "Initialize this repository with a README"
   - ✅ Check "Git Ignore:" and select **"Python"**
4. Click **"Create Repository"**

#### Step 3: Add .gitignore (Protect Secrets)
1. In your folder, create a file called `.gitignore` (with Notepad)
2. Add this content:
```
.env
*.pyc
__pycache__/
.DS_Store
streak_data.json
*.log
```
3. Save

#### Step 4: Commit Files
1. In GitHub Desktop, you'll see all your files listed
2. **Bottom left:** Enter commit message: "Initial bot setup with database"
3. Click **"Commit to main"**

#### Step 5: Publish to GitHub
1. Click **"Publish repository"** (top right)
2. Uncheck "Keep this code private" if you want it public (or leave checked)
3. Click **"Publish Repository"**

**✅ Done! Your code is on GitHub**

---

### Option B: Using Command Line (Advanced)

If you prefer terminal/command line:

```bash
# Navigate to your folder
cd C:\Users\YourName\Documents\joy-streak-bot

# Initialize git
git init

# Create .gitignore
echo .env > .gitignore
echo __pycache__/ >> .gitignore
echo *.pyc >> .gitignore

# Add all files
git add .

# Commit
git commit -m "Initial bot setup with database"

# Create GitHub repo (do this on github.com first)
# Then link it:
git remote add origin https://github.com/YourUsername/joy-streak-bot.git

# Push
git branch -M main
git push -u origin main
```

---

## 🚂 Part 3: Deploy to Railway (10 minutes)

### Step 1: Create Railway Account
1. Go to https://railway.app
2. Click **"Login"**
3. Sign in with GitHub (easiest)

### Step 2: Create New Project
1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. If first time:
   - Click **"Configure GitHub App"**
   - Give Railway access to your repositories
   - Select **"Only select repositories"** → Choose `joy-streak-bot`
   - Click **"Install & Authorize"**
4. Select your **`joy-streak-bot`** repository
5. Railway will start deploying (but will fail - that's okay!)

### Step 3: Add PostgreSQL Database
1. In your Railway project, click **"+ New"**
2. Select **"Database"**
3. Click **"Add PostgreSQL"**
4. Wait ~30 seconds for it to provision
5. ✅ `DATABASE_URL` is now automatically set!

### Step 4: Configure Bot Service

#### 4a: Set Environment Variables
1. Click on your **bot service** (not the database)
2. Click **"Variables"** tab
3. Click **"+ New Variable"**
4. Add:
   ```
   Variable: DISCORD_BOT_TOKEN
   Value: YOUR_ACTUAL_BOT_TOKEN_HERE
   ```
5. Click **"Add"**

**Where to get your bot token:**
1. Go to https://discord.com/developers/applications
2. Click your bot application
3. Click **"Bot"** (left sidebar)
4. Under "Token" click **"Reset Token"**
5. Copy the token
6. Paste into Railway

#### 4b: Set Start Command (Important!)
1. Still in your bot service, click **"Settings"** tab
2. Scroll down to **"Deploy"** section
3. Under **"Custom Start Command"** enter:
   ```
   python joy_streak_bot.py
   ```
4. Click outside the box to save

#### 4c: Set Root Directory (if needed)
1. In Settings, check **"Root Directory"**
2. Should be `/` (the default)
3. If not, set it to `/`

### Step 5: Deploy!
1. Go to **"Deployments"** tab
2. Click **"Deploy"** or wait for auto-deploy
3. Watch the logs...

### Step 6: Check Logs
You should see:
```
✅ Database connected successfully
✅ Database schema initialized
Daily Dose of Joy#2195 has connected to Discord!
📋 Configured Channels:
  joy_stickers: #daily-dose-of-joy
  monster_hunting: #hunting
  ...
✅ Bot is ready!
```

**If you see errors, scroll down to "Troubleshooting"**

---

## ✅ Part 4: Verify It's Working

### Step 1: Check Discord
1. Go to your test Discord server
2. Bot should show as **Online** (green dot)

### Step 2: Test Commands
In your `#bot-commands` channel:
```
!joyhelp
```
Bot should respond with help menu!

### Step 3: Test Joy Sticker
In your `#daily-dose-of-joy` channel:
1. Send the Joy sticker
2. Bot should react with ✅
3. Should get message: "**+30 XP** earned!"

### Step 4: Check Profile
```
!profile
```
Should show your stats!

---

## 🐛 Troubleshooting Common Issues

### Issue 1: "ModuleNotFoundError: No module named 'discord'"

**Fix:**
1. Railway → Your service → Settings
2. Check "Build Command" is empty (Railway auto-detects requirements.txt)
3. Redeploy

### Issue 2: "DATABASE_URL environment variable not set"

**Fix:**
1. Make sure PostgreSQL service is added
2. Make sure bot service and PostgreSQL are in the same project
3. Railway should auto-link them
4. Redeploy

### Issue 3: Bot shows offline in Discord

**Fix:**
1. Check Railway logs for errors
2. Verify `DISCORD_BOT_TOKEN` is set correctly
3. Make sure token is from the right bot
4. Redeploy

### Issue 4: "CommandNotFound" or bot doesn't respond

**Fix:**
1. Make sure bot has proper permissions in Discord server
2. Check bot has these permissions:
   - Send Messages
   - Embed Links
   - Read Message History
   - Add Reactions
   - Use External Emojis
3. Try reinviting bot with this URL:
   ```
   https://discord.com/api/oauth2/authorize?client_id=YOUR_BOT_ID&permissions=2147526656&scope=bot
   ```
   (Replace YOUR_BOT_ID with your bot's ID)

### Issue 5: Logs show "Invalid channel ID"

**Fix:**
1. Check `config/config.json` has your channel IDs
2. Make sure IDs are numbers, not strings
3. Push to GitHub (GitHub Desktop: commit + push)
4. Railway will auto-redeploy

---

## 🔄 Making Updates Later

### When you want to add new monsters, items, or change config:

#### Using GitHub Desktop:
1. Edit files on your computer
2. Open GitHub Desktop
3. See changes listed
4. Enter commit message (e.g., "Added new monsters")
5. Click "Commit to main"
6. Click "Push origin"
7. Railway auto-detects and redeploys!

#### Or use `!reload_data` command:
- For JSON files (monsters, items, classes)
- Just use `!reload_data` in Discord
- No need to redeploy!

---

## 📊 Monitoring Your Bot

### Railway Dashboard:
- **Deployments:** See deploy history
- **Metrics:** CPU, Memory usage
- **Logs:** Real-time bot logs
- **Variables:** Manage environment variables

### Discord:
- Bot status (online/offline)
- Test commands regularly
- Check error messages

---

## 💾 Backup Your Data

### Database Backups:
1. Railway → PostgreSQL service
2. Settings → Backup
3. Download backup
4. Store somewhere safe

### Code Backups:
- Already on GitHub! ✅
- Can download anytime from your repo

---

## 🎉 You're Done!

Your bot is now:
✅ Running on Railway (always online)
✅ Connected to PostgreSQL (no data loss)
✅ Backed up on GitHub (version control)
✅ Ready for testing!

---

## 📞 Next Steps

1. **Test thoroughly** in your test server
2. **Report any issues** to me
3. **When ready:** We'll add combat system
4. **Later:** Switch to production server channels

---

## 🆘 Still Need Help?

If stuck at any step, tell me:
1. Which step you're on
2. What error message you see (screenshot helps)
3. What you've tried

I'll help you debug! 🐛🔧
