# 🚂 Railway Deployment Guide for Joy Streak Bot v3

This guide will help you deploy the bot to Railway with PostgreSQL database.

## 📋 Prerequisites

- Railway account (https://railway.app)
- Discord bot token
- Your bot code uploaded to GitHub (or Railway CLI)

---

## 🗄️ Step 1: Add PostgreSQL Database

1. **Open your Railway project**
2. Click **"+ New"** → **"Database"** → **"Add PostgreSQL"**
3. Railway will automatically provision a PostgreSQL database
4. The `DATABASE_URL` environment variable is **automatically set**

---

## 🤖 Step 2: Set Environment Variables

1. Go to your bot service in Railway
2. Click **"Variables"** tab
3. Add these variables:

```
DISCORD_BOT_TOKEN=your_actual_bot_token_here
```

**Note:** `DATABASE_URL` is automatically added when you create the PostgreSQL service!

### Optional Variables:
```
ADMIN_USER_ID=your_discord_user_id
```

---

## 📦 Step 3: Deploy Bot Code

### Option A: Deploy from GitHub

1. Connect your GitHub repository
2. Railway will auto-detect `requirements.txt`
3. Set start command to: `python joy_streak_bot.py`

### Option B: Deploy via Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Deploy
railway up
```

---

## 🔧 Step 4: Verify Deployment

Once deployed, check the logs for:

```
✅ Database connected successfully
✅ Database schema initialized
Daily Dose of Joy#2195 has connected to Discord!
Using timezone: Eastern Time (America/New_York)
```

---

## 📂 File Structure on Railway

Your Railway deployment should have:

```
/app/
├── joy_streak_bot.py
├── database.py
├── admin.py
├── requirements.txt
├── .env (automatically created from variables)
│
├── data/
│   ├── monsters.json
│   ├── items.json
│   ├── classes.json
│   └── achievements.json
│
└── config/
    └── config.json
```

---

## ⚙️ Railway Configuration

### Start Command:
```
python joy_streak_bot.py
```

### Build Command (if needed):
```
pip install -r requirements.txt
```

---

## 🆘 Troubleshooting

### Database Connection Error

**Error:** `DATABASE_URL environment variable not set!`

**Fix:** Make sure PostgreSQL service is added and linked to your bot service.

### Module Not Found

**Error:** `ModuleNotFoundError: No module named 'psycopg2'`

**Fix:** Ensure `requirements.txt` is in the root directory.

### Bot Not Responding

1. Check logs for errors
2. Verify `DISCORD_BOT_TOKEN` is set correctly
3. Make sure bot has proper Discord permissions

---

## 🔄 Database Migration from v2

If you have existing data from the old JSON-based bot:

**IMPORTANT:** The bot will start fresh with a new database. Your old `streak_data.json` is NOT automatically migrated.

To migrate old data:
1. Keep your old `streak_data.json` file
2. Ask me to create a migration script
3. Run it once after first deployment

---

## 📊 Database Management

### View Database:
1. Go to PostgreSQL service in Railway
2. Click **"Data"** tab
3. Browse tables: users, inventory, achievements, etc.

### Backup Database:
Railway automatically backs up your database. You can also:
1. Click PostgreSQL service
2. **"Settings"** → **"Backup"**
3. Download backup

### Reset Database:
Use the bot command: `!reset_all` (admin only)

---

## 🎯 Post-Deployment Checklist

- [ ] Bot is online in Discord
- [ ] Database connected (check logs)
- [ ] Send a Joy sticker to test
- [ ] Try `!profile` command
- [ ] Set up channels with `!set_channel`
- [ ] Add your Discord ID to admin list

---

## 🔐 Security Notes

- **Never commit** `.env` file to GitHub
- Keep your `DISCORD_BOT_TOKEN` secret
- Only give admin roles to trusted users
- Database is private to your Railway project

---

## 📞 Need Help?

- Railway Docs: https://docs.railway.app
- Discord.py Docs: https://discordpy.readthedocs.io
- PostgreSQL Docs: https://www.postgresql.org/docs/

---

## 🚀 You're Ready!

Your bot should now be running with:
✅ Persistent PostgreSQL database (no more data loss!)
✅ Admin commands for management
✅ Easy-to-edit JSON files for content
✅ Ready for monster hunting system!

Next steps: Configure channels and start adding monsters! 🎮
