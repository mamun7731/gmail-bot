import os
import random
import string
from datetime import datetime
import psycopg2
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from flask import Flask, request
import requests

TOKEN = '8788513514:AAGwboQDDtl198sib3_3GX3ahtmh0wg4iS0'
bot = telebot.TeleBot(TOKEN)

ADMIN_ID = 5813365228

GMAIL_RATE = 0.15
MIN_PAYOUT = 0.20
REF_BONUS = 0.02

DATABASE_URL = "postgresql://postgres.ijussavmhziblqswfgwf:mamun347731@aws-0-ap-southeast-2.pooler.supabase.com:6543/postgres"

def get_db():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def init_db():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                balance REAL DEFAULT 0.0,
                hold_balance REAL DEFAULT 0.0,
                completed_count INTEGER DEFAULT 0,
                referred_by BIGINT DEFAULT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pending_tasks (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                email TEXT,
                password TEXT,
                recovery TEXT DEFAULT 'None',
                status TEXT DEFAULT 'pending',
                date TEXT,
                reason TEXT DEFAULT NULL,
                account_type TEXT DEFAULT 'New Gmail'
            )
        ''')
        cursor.execute('ALTER TABLE pending_tasks ADD COLUMN IF NOT EXISTS recovery TEXT DEFAULT \'None\';')
        cursor.execute('ALTER TABLE pending_tasks ADD COLUMN IF NOT EXISTS date TEXT;')
        cursor.execute('ALTER TABLE pending_tasks ADD COLUMN IF NOT EXISTS reason TEXT DEFAULT NULL;')
        cursor.execute("ALTER TABLE pending_tasks ADD COLUMN IF NOT EXISTS account_type TEXT DEFAULT 'New Gmail';")
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                text TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assigned_gmails (
                email TEXT PRIMARY KEY,
                user_id BIGINT,
                status TEXT DEFAULT 'assigned'
            )
        ''')
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"DB Init Error: {e}")

init_db()

def get_user_data(user_id, referred_by=None):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT balance, hold_balance, completed_count FROM users WHERE user_id = %s", (user_id,))
        row = cursor.fetchone()
        
        if not row:
            cursor.execute("INSERT INTO users (user_id, referred_by) VALUES (%s, %s) ON CONFLICT (user_id) DO NOTHING", (user_id, referred_by))
            conn.commit()
            if referred_by and referred_by != user_id:
                cursor.execute("UPDATE users SET balance = balance + %s WHERE user_id = %s", (REF_BONUS, referred_by))
                cursor.execute("INSERT INTO history (user_id, text) VALUES (%s, %s)", (referred_by, f"+${REF_BONUS} Referral Bonus"))
                conn.commit()
                try:
                    bot.send_message(referred_by, f"🎉 You received a ${REF_BONUS} referral bonus!")
                except:
                    pass
            cursor.execute("SELECT balance, hold_balance, completed_count FROM users WHERE user_id = %s", (user_id,))
            row = cursor.fetchone()
            
        cursor.close()
        conn.close()
        if row:
            return {"balance": row[0], "hold_balance": row[1], "completed_count": row[2]}
    except Exception as e:
        print(f"get_user_data error: {e}")
    return {"balance": 0.0, "hold_balance": 0.0, "completed_count": 0}

def generate_unique_gmail(cursor):
    cursor.execute("SELECT email FROM assigned_gmails")
    assigned_emails = {row[0] for row in cursor.fetchall()}
    
    for _ in range(100):
        letters = ''.join(random.choices(string.ascii_letters, k=random.randint(6, 9)))
        numbers = ''.join(random.choices(string.digits, k=random.randint(3, 4)))
        username = f"{letters}{numbers}"
        email = f"{username}@gmail.com"
        
        if email not in assigned_emails:
            password = f"{letters[:3].capitalize()}#{numbers}Xk"
            return {
                "first": letters[:5].capitalize(),
                "last": "❌",
                "email": email,
                "pass": password,
                "year": "2000"
            }
    return None

def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = KeyboardButton("➕ Register a new Gmail")
    item2 = KeyboardButton("📥 Submit my own")
    item3 = KeyboardButton("📋 My accounts")
    item4 = KeyboardButton("💰 Balance")
    item5 = KeyboardButton("👥 My referrals")
    item6 = KeyboardButton("💬 Help")
    markup.add(item1, item2)
    markup.add(item3, item4)
    markup.add(item5, item6)
    return markup

def balance_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = KeyboardButton("💳 Payout")
    item2 = KeyboardButton("📝 Balance history")
    item3 = KeyboardButton("⬅️ Back")
    markup.add(item1, item2)
    markup.add(item3)
    return markup

user_states = {}
user_temp_data = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        user_id = message.chat.id
        user_states.pop(user_id, None)
        user_temp_data.pop(user_id, None)
        
        ref_id = None
        args = message.text.split()
        if len(args) > 1 and args[1].isdigit():
            ref_id = int(args[1])
            
        get_user_data(user_id, referred_by=ref_id)
        bot.send_message(
            user_id, 
            "Welcome to Gmail Farmer Bot! Select an option below:", 
            reply_markup=main_menu()
        )
    except Exception as e:
        print(f"Start error: {e}")

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    try:
        if message.chat.id != ADMIN_ID:
            return
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*), SUM(balance) FROM users")
        stats = cursor.fetchone()
        cursor.execute("SELECT COUNT(*) FROM pending_tasks WHERE status = 'pending'")
        pending_count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        total_users = stats[0] or 0
        total_bal = round(stats[1] or 0.0, 2)
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(f"🔔 Pending Approvals ({pending_count})", callback_data="admin_view_pending"))
        markup.add(InlineKeyboardButton("📢 Broadcast Message", callback_data="admin_broadcast"))
        
        bot.send_message(
            message.chat.id,
            f"👑 **Admin Dashboard**\n\n👥 Total Users: {total_users}\n💰 Total User Balance: ${total_bal}\n⏳ Pending Gmail Tasks: {pending_count}",
            parse_mode="Markdown",
            reply_markup=markup
        )
    except Exception as e:
        print(f"Admin panel error: {e}")

def process_submission_done(user_id, email, password, recovery, acc_type, message_obj):
    try:
        current_date = datetime.now().strftime("%m/%d/%Y")
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO pending_tasks (user_id, email, password, recovery, status, date, account_type) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (user_id, email, password, recovery, 'pending', current_date, acc_type)
        )
        task_id = cursor.fetchone()[0]
        cursor.execute("UPDATE users SET hold_balance = hold_balance + %s WHERE user_id = %s", (GMAIL_RATE, user_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        user_info = message_obj.from_user
        name = user_info.first_name or "Unknown"
        username = f"@{user_info.username}" if user_info.username else "No Username"
        
        u_data = get_user_data(user_id)
        u_bal = round(u_data["balance"], 2)
        u_completed = u_data["completed_count"]

        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ Approve ($0.15)", callback_data=f"app_{task_id}_{user_id}"),
            InlineKeyboardButton("💵 Custom Price", callback_data=f"customapp_{task_id}_{user_id}")
        )
        markup.add(InlineKeyboardButton("❌ Reject", callback_data=f"rej_{task_id}_{user_id}"))
        
        try:
            bot.send_message(
                ADMIN_ID,
                f"🔔 **New Pending Task ({acc_type})!**\n\n👤 Name: {name}\n🔗 Username: {username}\n🆔 User ID: `{user_id}`\n💰 Balance: ${u_bal}\n✅ Approved Gmails: {u_completed}\n\n📂 Type: **{acc_type}**\n📧 Email: `{email}`\n🔑 Password: `{password}`\n🔄 Recovery: `{recovery}`",
                parse_mode="Markdown",
                reply_markup=markup
            )
        except Exception as e:
            print(f"Admin notify error: {e}")

        bot.send_message(
            user_id,
            f"⏳ Task submitted successfully ({acc_type})!\n\nYour account is currently under **Hold (Pending review)**. Once admin verifies it, reward will be added to your balance.",
            reply_markup=main_menu()
        )
    except Exception as e:
        print(f"process_submission_done error: {e}")
        bot.send_message(user_id, f"❌ Error submitting task: {e}", reply_markup=main_menu())

@bot.message_handler(content_types=['text', 'photo'])
def handle_message(message):
    try:
        user_id = message.chat.id
        text = message.text if message.content_type == 'text' else (message.caption or "")
        text_lower = text.lower()
        
        if "cancel" in text_lower or "back" in text_lower or "⬅️ back" in text_lower:
            user_states.pop(user_id, None)
            user_temp_data.pop(user_id, None)
            bot.send_message(user_id, "Main Menu:", reply_markup=main_menu())
            return

        if "my accounts" in text_lower or text == "📋 My accounts":
            user_states.pop(user_id, None)
            user_temp_data.pop(user_id, None)
                
            conn = get_db()
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT email, password, status, date, reason, account_type, recovery FROM pending_tasks WHERE user_id = %s ORDER BY id DESC", (user_id,))
                tasks = cursor.fetchall()
            except Exception as e:
                conn.rollback()
                cursor.execute("SELECT email, password, status, date, reason FROM pending_tasks WHERE user_id = %s ORDER BY id DESC", (user_id,))
                rows = cursor.fetchall()
                tasks = [(r[0], r[1], r[2], r[3], r[4], "New Gmail", "None") for r in rows]
            cursor.close()
            conn.close()
            
            total_count = len(tasks)
            paid_count = sum(1 for t in tasks if t[2] == 'approved')
            pending_count = sum(1 for t in tasks if t[2] == 'pending')
            declined_count = sum(1 for t in tasks if t[2] == 'rejected')
            
            summary_text = (
                f"📁 Your submitted accounts ({total_count}):\n\n"
                f"📊 Summary:\n"
                f"✅ Paid: {paid_count}\n"
                f"⏳ Pending: {pending_count}\n"
                f"❌ Declined: {declined_count}\n"
                f"⚠️ Failed: 0\n"
            )
            bot.send_message(user_id, summary_text, reply_markup=main_menu())
            
            if tasks:
                for i, t in enumerate(tasks[:15], 1):
                    email, pwd, status, date_str, reason, acc_type = t[0], t[1], t[2], t[3], t[4], t[5]
                    if not date_str:
                        date_str = datetime.now().strftime("%m/%d/%Y")
                    
                    if status == 'approved':
                        icon, status_text = "✅", "paid"
                    elif status == 'pending':
                        icon, status_text = "⏳", "pending"
                    else:
                        icon, status_text = "❌", "declined"
                    
                    msg = f"{i}. {icon} {acc_type}\n💰 ${GMAIL_RATE:.2f} | 📅 {date_str} | {status_text}\n📋 {email}:{pwd}"
                    if status == 'rejected' and reason:
                        msg += f"\n💬 **Decline Reason:** {reason}"
                    bot.send_message(user_id, msg)
            else:
                bot.send_message(user_id, "📁 You have not submitted any accounts yet.", reply_markup=main_menu())
            return

        if "done" in text_lower or "✔" in text:
            if user_id in user_temp_data and "assigned_email" in user_temp_data[user_id]:
                email = user_temp_data[user_id]["assigned_email"]
                prefix = email.split('@')[0]
                letters = "".join([c for c in prefix if c.isalpha()])
                numbers = "".join([c for c in prefix if c.isdigit()])
                password = f"{letters[:3].capitalize()}#{numbers}Xk"
                
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute("UPDATE assigned_gmails SET status = 'submitted' WHERE email = %s", (email,))
                conn.commit()
                cursor.close()
                conn.close()
                
                user_states.pop(user_id, None)
                user_temp_data.pop(user_id, None)
                process_submission_done(user_id, email, password, "None", "New Gmail", message)
                return

        if user_id in user_states:
            state = user_states[user_id]
            
            if state.startswith("awaiting_reject_reason_") and user_id == ADMIN_ID:
                parts = state.split("_")
                task_id = int(parts[3])
                target_user_id = int(parts[4])
                user_states.pop(user_id, None)
                
                reason = message.caption if message.content_type == 'photo' else message.text
                if not reason:
                    reason = "No reason provided."
                
                photo_id = message.photo[-1].file_id if message.content_type == 'photo' else None
                if photo_id:
                    reason = f"{reason} [Photo attached]"
                    
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute("SELECT email FROM pending_tasks WHERE id = %s", (task_id,))
                task = cursor.fetchone()
                email = task[0] if task else "Unknown"
                
                cursor.execute("UPDATE pending_tasks SET status = 'rejected', reason = %s WHERE id = %s", (reason, task_id))
                cursor.execute("UPDATE users SET hold_balance = GREATEST(0, hold_balance - %s) WHERE user_id = %s", (GMAIL_RATE, target_user_id))
                cursor.execute("INSERT INTO history (user_id, text) VALUES (%s, %s)", (target_user_id, f"Rejected - Gmail ({email})"))
                conn.commit()
                cursor.close()
                conn.close()
                
                bot.send_message(ADMIN_ID, f"❌ Task for `{email}` rejected.", parse_mode="Markdown")
                try:
                    if photo_id:
                        bot.send_photo(target_user_id, photo=photo_id, caption=f"❌ Sorry, your Gmail account (`{email}`) submission was rejected.\n\n📝 **Reason:** {reason}", parse_mode="Markdown")
                    else:
                        bot.send_message(target_user_id, f"❌ Sorry, your Gmail account (`{email}`) submission was rejected.\n\n📝 **Reason:** {reason}", parse_mode="Markdown")
                except Exception as e:
                    print(f"Send fail: {e}")
                return

            if state.startswith("awaiting_custom_price_") and user_id == ADMIN_ID:
                parts = state.split("_")
                task_id = int(parts[3])
                target_user_id = int(parts[4])
                user_states.pop(user_id, None)
                
                try:
                    custom_price = float(text.strip())
                except ValueError:
                    bot.send_message(ADMIN_ID, "❌ Invalid amount! Send a valid number (e.g. 0.30):")
                    user_states[ADMIN_ID] = f"awaiting_custom_price_{task_id}_{target_user_id}"
                    return
                    
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute("SELECT email, status FROM pending_tasks WHERE id = %s", (task_id,))
                task = cursor.fetchone()
                if not task or task[1] != 'pending':
                    cursor.close()
                    conn.close()
                    bot.send_message(ADMIN_ID, "❌ Task not found or already processed!")
                    return
                    
                email = task[0]
                cursor.execute("UPDATE pending_tasks SET status = 'approved' WHERE id = %s", (task_id,))
                cursor.execute("UPDATE users SET balance = balance + %s, hold_balance = GREATEST(0, hold_balance - %s), completed_count = completed_count + 1 WHERE user_id = %s", (custom_price, GMAIL_RATE, target_user_id))
                cursor.execute("INSERT INTO history (user_id, text) VALUES (%s, %s)", (target_user_id, f"+${custom_price:.2f} - Gmail Approved ({email}) [Custom]"))
                conn.commit()
                cursor.close()
                conn.close()
                
                bot.send_message(ADMIN_ID, f"✅ Task for `{email}` approved with custom price `${custom_price:.2f}`!", parse_mode="Markdown")
                try:
                    bot.send_message(target_user_id, f"🎉 Good news! Your Gmail account ({email}) has been approved with custom reward +${custom_price:.2f} added to your balance!")
                except:
                    pass
                return

            user_data = get_user_data(user_id)
            
            if state == "sub_awaiting_type":
                acc_type = "Old Gmail" if "old" in text_lower or "🌟" in text else "New Gmail"
                user_temp_data[user_id] = {"account_type": acc_type}
                user_states[user_id] = "sub_awaiting_email"
                markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
                markup.add(KeyboardButton("🚫 Cancel registration"))
                bot.send_message(user_id, f"Selected: **{acc_type}**\n\n📬 Please enter your Gmail email address:", parse_mode="Markdown", reply_markup=markup)
                return

            elif state == "sub_awaiting_email":
                if user_id not in user_temp_data:
                    user_temp_data[user_id] = {}
                user_temp_data[user_id]["email"] = text
                user_states[user_id] = "sub_awaiting_password"
                markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
                markup.add(KeyboardButton("🚫 Cancel registration"))
                bot.send_message(user_id, "🔐 Please enter your password:", reply_markup=markup)
                return
                
            elif state == "sub_awaiting_password":
                if user_id not in user_temp_data:
                    user_temp_data[user_id] = {}
                user_temp_data[user_id]["password"] = text
                user_states[user_id] = "sub_awaiting_recovery"
                markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
                markup.add(KeyboardButton("⏭ Skip recovery email"))
                markup.add(KeyboardButton("🚫 Cancel registration"))
                bot.send_message(user_id, "📧 Please enter your recovery email address, or tap **Skip** — it is optional:", parse_mode="Markdown", reply_markup=markup)
                return
                
            elif state == "sub_awaiting_recovery":
                is_skip = "skip" in text_lower or "⏭" in text or not text.strip()
                recovery_val = "None" if is_skip else text
                
                if user_id not in user_temp_data:
                    user_temp_data[user_id] = {}
                user_temp_data[user_id]["recovery"] = recovery_val
                
                acc = user_temp_data[user_id]
                email = acc.get("email", "unknown@gmail.com")
                password = acc.get("password", "123456")
                recovery = acc.get("recovery", "None")
                acc_type = acc.get("account_type", "New Gmail")
                
                user_states.pop(user_id, None)
                user_temp_data.pop(user_id, None)
                
                process_submission_done(user_id, email, password, recovery, acc_type, message)
                return

            if state in ["payout_bkash", "payout_nagad", "payout_crypto"]:
                method = "bKash" if state == "payout_bkash" else ("Nagad" if state == "payout_nagad" else "Crypto (BEP20)")
                user_states.pop(user_id, None)
                
                bal = user_data["balance"]
                if bal < MIN_PAYOUT:
                    bot.send_message(user_id, f"❌ Insufficient balance. Minimum payout is ${MIN_PAYOUT:.2f}")
                    return
                
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET balance = 0.0 WHERE user_id = %s", (user_id,))
                cursor.execute("INSERT INTO history (user_id, text) VALUES (%s, %s)", (user_id, f"-${bal:.2f} Payout via {method} ({text})"))
                conn.commit()
                cursor.close()
                conn.close()
                
                try:
                    markup = InlineKeyboardMarkup()
                    markup.add(InlineKeyboardButton("✅ Confirm & Send TXID", callback_data=f"payapp_{user_id}"))
                    bot.send_message(ADMIN_ID, f"🔔 **New Payout Request!**\n\nUser ID: `{user_id}`\nMethod: `{method}`\nAmount: `${bal:.2f}`\nDetails/Number: `{text}`", parse_mode="Markdown", reply_markup=markup)
                except:
                    pass
                
                bot.send_message(user_id, f"✅ Withdrawal request of ${bal:.2f} via {method} submitted successfully!", reply_markup=main_menu())
                return
                
            elif state.startswith("awaiting_txid_") and user_id == ADMIN_ID:
                target_user_id = int(state.split("_")[2])
                user_states.pop(user_id, None)
                try:
                    bot.send_message(target_user_id, f"🎉 **Your Payout has been Paid!**\n\n✅ Transaction ID / Proof:\n`{text}`", parse_mode="Markdown")
                    bot.send_message(ADMIN_ID, f"✅ TXID successfully sent to user `{target_user_id}`!", parse_mode="Markdown")
                except Exception as e:
                    bot.send_message(ADMIN_ID, f"❌ Failed to send message: {e}")
                return
                
            elif state == "awaiting_broadcast" and user_id == ADMIN_ID:
                user_states.pop(user_id, None)
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute("SELECT user_id FROM users")
                all_users = cursor.fetchall()
                cursor.close()
                conn.close()
                
                sent = 0
                for u in all_users:
                    try:
                        bot.send_message(u[0], f"📢 **Broadcast Message:**\n\n{text}", parse_mode="Markdown")
                        sent += 1
                    except:
                        pass
                bot.send_message(ADMIN_ID, f"✅ Broadcast sent to {sent} users!")
                return

        if message.content_type != 'text':
            return

        user_data = get_user_data(user_id)

        if "register" in text_lower or "➕" in text:
            conn = get_db()
            cursor = conn.cursor()
            selected_acc = generate_unique_gmail(cursor)
            if not selected_acc:
                cursor.close()
                conn.close()
                bot.send_message(user_id, "❌ Sorry, could not generate a unique Gmail right now. Please try again later.")
                return
                
            email = selected_acc['email']
            cursor.execute("INSERT INTO assigned_gmails (email, user_id, status) VALUES (%s, %s, 'assigned')", (email, user_id))
            conn.commit()
            cursor.close()
            conn.close()
            
            user_temp_data[user_id] = {"assigned_email": email}
            
            response_text = (
                f"Register Gmail account using the specified data and get ${GMAIL_RATE:.2f}\n\n"
                f"First name: `{selected_acc['first']}`\n"
                f"Last name: {selected_acc['last']}\n"
                f"Email: `{email}`\n"
                f"Password: `{selected_acc['pass']}`\n"
                f"Year of birth: {selected_acc['year']}\n\n"
                f"🔐 Be sure to use the specified data, otherwise the account will not be paid."
            )
            markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
            markup.add(KeyboardButton("✔ Done"))
            markup.add(KeyboardButton("🚫 Cancel registration"))
            markup.add(KeyboardButton("❓ How to create account"))
            bot.send_message(user_id, response_text, parse_mode="Markdown", reply_markup=markup)

        elif "submit" in text_lower or "📥" in text:
            user_states[user_id] = "sub_awaiting_type"
            markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
            markup.add(KeyboardButton("⭐ New Gmail"), KeyboardButton("🌟 Old Gmail"))
            markup.add(KeyboardButton("🚫 Cancel registration"))
            bot.send_message(user_id, "📥 Please select which type of Gmail you want to submit:", reply_markup=markup)
            
        elif "balance" in text_lower and "history" not in text_lower:
            bal = round(user_data["balance"], 2)
            hold = round(user_data["hold_balance"], 2)
            bot.send_message(user_id, f"Balance: {bal}$\nHold: {hold}$", reply_markup=balance_menu())
            
        elif "payout" in text_lower or "💳" in text:
            bal = round(user_data["balance"], 2)
            if bal < MIN_PAYOUT:
                bot.send_message(user_id, f"⚠️ Minimum payout amount is ${MIN_PAYOUT:.2f}. Your current balance is ${bal:.2f}.")
            else:
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton("🔹 bKash (Fee: 5 BDT)", callback_data="pay_bkash"))
                markup.add(InlineKeyboardButton("🔹 Nagad (Fee: 5 BDT)", callback_data="pay_nagad"))
                markup.add(InlineKeyboardButton("🔹 Crypto BEP20 (Fee: $0.03)", callback_data="pay_crypto"))
                bot.send_message(user_id, f"💰 Your Balance: ${bal:.2f}\n\nSelect your payout method:", reply_markup=markup)
                
        elif "history" in text_lower or "📝" in text:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT text FROM history WHERE user_id = %s ORDER BY id DESC LIMIT 10", (user_id,))
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            if not rows:
                bot.send_message(user_id, "📝 No transactions found in your balance history.")
            else:
                bot.send_message(user_id, "📝 Balance History:\n\n" + "\n".join([r[0] for r in rows]))
                
        elif "referral" in text_lower or "👥" in text:
            bot_info = bot.get_me()
            ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
            bot.send_message(user_id, f"👥 **Your Referral Link:**\n{ref_link}\n\n🎁 Invite friends and earn ${REF_BONUS:.2f} per active referral!", parse_mode="Markdown")
            
        elif "help" in text_lower or "💬" in text or "how to create account" in text_lower:
            bot.send_message(user_id, "ℹ️ Guidelines:\n1. Guide: Create Gmail using given name and DOB\n2. Submit exact email & password\n3. Tap Done.\n\n💬 Support contact: @mamun9894")
    except Exception as e:
        print(f"handle_message error: {e}")

@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    try:
        user_id = call.from_user.id
        
        if call.data == "pay_bkash":
            user_states[user_id] = "payout_bkash"
            bot.answer_callback_query(call.id)
            bot.send_message(user_id, "📱 Please send your **bKash Number**:")
        elif call.data == "pay_nagad":
            user_states[user_id] = "payout_nagad"
            bot.answer_callback_query(call.id)
            bot.send_message(user_id, "📱 Please send your **Nagad Number**:")
        elif call.data == "pay_crypto":
            user_states[user_id] = "payout_crypto"
            bot.answer_callback_query(call.id)
            bot.send_message(user_id, "🌐 Please send your **Crypto BEP20 Wallet Address**:")
            
        elif call.data.startswith("payapp_"):
            if call.from_user.id != ADMIN_ID:
                bot.answer_callback_query(call.id, "You are not authorized!", show_alert=True)
                return
            target_user_id = int(call.data.split("_")[1])
            user_states[ADMIN_ID] = f"awaiting_txid_{target_user_id}"
            bot.answer_callback_query(call.id)
            bot.edit_message_text(chat_id=ADMIN_ID, message_id=call.message.message_id, text=call.message.text + f"\n\n👉 **Status:** Clicked! Now send the **Transaction ID (TXID)** in chat for user `{target_user_id}`:", parse_mode="Markdown")
            
        elif call.data.startswith("customapp_"):
            if call.from_user.id != ADMIN_ID:
                bot.answer_callback_query(call.id, "You are not authorized!", show_alert=True)
                return
            parts = call.data.split("_")
            task_id, target_user_id = int(parts[1]), int(parts[2])
            user_states[ADMIN_ID] = f"awaiting_custom_price_{task_id}_{target_user_id}"
            bot.answer_callback_query(call.id)
            bot.send_message(ADMIN_ID, "💵 Please send the **Custom Price / Amount** (e.g. 0.30 or 0.50) to add to user's balance:")
            
        elif call.data == "btn_done" or call.data.startswith("btn_done_"):
            email = None
            if user_id in user_temp_data and "assigned_email" in user_temp_data[user_id]:
                email = user_temp_data[user_id]["assigned_email"]
            
            conn = get_db()
            cursor = conn.cursor()
            if not email:
                cursor.execute("SELECT email FROM assigned_gmails WHERE user_id = %s AND status = 'assigned' ORDER BY email DESC LIMIT 1", (user_id,))
                assigned = cursor.fetchone()
                if assigned:
                    email = assigned[0]
            
            if not email:
                letters = ''.join(random.choices(string.ascii_letters, k=8))
                numbers = ''.join(random.choices(string.digits, k=4))
                email = f"{letters}{numbers}@gmail.com"
                cursor.execute("INSERT INTO assigned_gmails (email, user_id, status) VALUES (%s, %s, 'assigned') ON CONFLICT (email) DO NOTHING", (email, user_id))
            
            prefix = email.split('@')[0]
            letters = "".join([c for c in prefix if c.isalpha()])
            numbers = "".join([c for c in prefix if c.isdigit()])
            password = f"{letters[:3].capitalize()}#{numbers}Xk"
            
            cursor.execute("UPDATE assigned_gmails SET status = 'submitted' WHERE email = %s", (email,))
            conn.commit()
            cursor.close()
            conn.close()
            
            user_temp_data.pop(user_id, None)
            user_states.pop(user_id, None)
            
            bot.answer_callback_query(call.id, "Submitted successfully!")
            process_submission_done(user_id, email, password, "None", "New Gmail", call.message)
            
        elif call.data.startswith("app_") or call.data.startswith("rej_") or call.data.startswith("cancelapp_"):
            if call.from_user.id != ADMIN_ID:
                bot.answer_callback_query(call.id, "You are not authorized!", show_alert=True)
                return
                
            parts = call.data.split("_")
            action, task_id, target_user_id = parts[0], int(parts[1]), int(parts[2])
            
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT email, status FROM pending_tasks WHERE id = %s", (task_id,))
            task = cursor.fetchone()
            if not task:
                cursor.close()
                conn.close()
                bot.answer_callback_query(call.id, "Task not found!")
                return
                
            email, current_status = task[0], task[1]
            
            if action == "app":
                if current_status != 'pending':
                    cursor.close()
                    conn.close()
                    bot.answer_callback_query(call.id, "Task already processed!")
                    return
                cursor.execute("UPDATE pending_tasks SET status = 'approved' WHERE id = %s", (task_id,))
                cursor.execute("UPDATE users SET balance = balance + %s, hold_balance = GREATEST(0, hold_balance - %s), completed_count = completed_count + 1 WHERE user_id = %s", (GMAIL_RATE, GMAIL_RATE, target_user_id))
                cursor.execute("INSERT INTO history (user_id, text) VALUES (%s, %s)", (target_user_id, f"+${GMAIL_RATE:.2f} - Gmail Approved ({email})"))
                conn.commit()
                cursor.close()
                conn.close()
                
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton("❌ Cancel Approval (Revoke)", callback_data=f"cancelapp_{task_id}_{target_user_id}"))
                bot.answer_callback_query(call.id, "Approved successfully!")
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"✅ Task for `{email}` has been **APPROVED**.", reply_markup=markup)
                try:
                    bot.send_message(target_user_id, f"🎉 Good news! Your Gmail account ({email}) has been approved. +${GMAIL_RATE:.2f} added to your balance!")
                except:
                    pass
                    
            elif action == "cancelapp":
                if current_status != 'approved':
                    cursor.close()
                    conn.close()
                    bot.answer_callback_query(call.id, "Only approved tasks can be cancelled!")
                    return
                
                # Automatically extract the exact reward amount given to this user for this email from history
                cursor.execute("SELECT text FROM history WHERE user_id = %s AND text LIKE %s ORDER BY id DESC LIMIT 1", (target_user_id, f"%Gmail Approved ({email})%"))
                hist_row = cursor.fetchone()
                deduct_amount = GMAIL_RATE
                if hist_row:
                    h_text = hist_row[0]
                    # Parse amount e.g. "+$0.25 - Gmail Approved..." or "+$0.05..."
                    try:
                        if "+$" in h_text:
                            part_str = h_text.split("+$")[1].split(" - ")[0]
                            deduct_amount = float(part_str)
                    except Exception as ex:
                        print(f"Error parsing reward amount from history: {ex}")

                cursor.execute("UPDATE pending_tasks SET status = 'rejected', reason = 'Approval cancelled by admin' WHERE id = %s", (task_id,))
                cursor.execute("UPDATE users SET balance = GREATEST(0, balance - %s), completed_count = GREATEST(0, completed_count - 1) WHERE user_id = %s", (deduct_amount, target_user_id))
                cursor.execute("INSERT INTO history (user_id, text) VALUES (%s, %s)", (target_user_id, f"Approval Cancelled - Gmail ({email}) [Deducted ${deduct_amount:.2f}]"))
                conn.commit()
                cursor.close()
                conn.close()
                
                bot.answer_callback_query(call.id, f"Approval cancelled and ${deduct_amount:.2f} deducted!")
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"❌ Approval for `{email}` has been **CANCELLED / REVOKED** and `${deduct_amount:.2f}` deducted from user balance.", parse_mode="Markdown")
                try:
                    bot.send_message(target_user_id, f"⚠️ Notice: Your approved Gmail account ({email}) approval was cancelled by admin. ${deduct_amount:.2f} was deducted from your balance.")
                except:
                    pass

            elif action == "rej":
                cursor.close()
                conn.close()
                user_states[ADMIN_ID] = f"awaiting_reject_reason_{task_id}_{target_user_id}"
                bot.answer_callback_query(call.id)
                bot.edit_message_text(chat_id=ADMIN_ID, message_id=call.message.message_id, text=call.message.text + f"\n\n👉 **Status:** Rejected clicked! Now send the **Reject Reason (Text or Photo with caption)** in chat for user `{target_user_id}`:", parse_mode="Markdown")

        elif call.data == "admin_view_pending":
            if call.from_user.id != ADMIN_ID:
                return
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT id, user_id, email, password, recovery, account_type FROM pending_tasks WHERE status = 'pending' LIMIT 5")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            if not rows:
                bot.answer_callback_query(call.id, "No pending tasks found!")
                return
            bot.answer_callback_query(call.id, "Showing pending tasks:")
            for r in rows:
                t_id, u_id, email, pwd, recovery, acc_type = r[0], r[1], r[2], r[3], r[4], r[5]
                if not acc_type:
                    acc_type = "New Gmail"
                u_data = get_user_data(u_id)
                u_bal = round(u_data["balance"], 2)
                u_completed = u_data["completed_count"]
                
                markup = InlineKeyboardMarkup()
                markup.add(
                    InlineKeyboardButton("✅ Approve ($0.15)", callback_data=f"app_{t_id}_{u_id}"),
                    InlineKeyboardButton("💵 Custom Price", callback_data=f"customapp_{t_id}_{u_id}")
                )
                markup.add(InlineKeyboardButton("❌ Reject", callback_data=f"rej_{t_id}_{u_id}"))
                
                bot.send_message(
                    ADMIN_ID,
                    f"⏳ Pending Task ({acc_type}):\n🆔 User ID: `{u_id}`\n💰 Balance: ${u_bal}\n✅ Approved Gmails: {u_completed}\n📂 Type: **{acc_type}**\n📧 Email: `{email}`\n🔑 Password: `{pwd}`\n🔄 Recovery: `{recovery}`",
                    parse_mode="Markdown",
                    reply_markup=markup
                )

        elif call.data == "btn_cancel":
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM assigned_gmails WHERE user_id = %s AND status = 'assigned'", (user_id,))
            conn.commit()
            cursor.close()
            conn.close()
            user_states.pop(user_id, None)
            user_temp_data.pop(user_id, None)
            bot.answer_callback_query(call.id, "Registration cancelled.")
            bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id, text="❌ Registration has been cancelled.")
            
        elif call.data == "btn_help":
            bot.answer_callback_query(call.id, "Instructions sent.")
            bot.send_message(user_id, "ℹ️ Guidelines:\n1. Guide: Create Gmail using given name and DOB\n2. Submit exact email & password\n3. Tap Done.")
            
        elif call.data == "admin_broadcast" and user_id == ADMIN_ID:
            user_states[user_id] = "awaiting_broadcast"
            bot.send_message(ADMIN_ID, "📢 Please send the broadcast message to send to all users:")
    except Exception as e:
        print(f"callback_listener error: {e}")

# Flask Web Server & Webhook Handler
app = Flask(__name__)

@app.route(f"/{TOKEN}", methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return 'Forbidden', 403

@app.route('/')
def home():
    return "Bot is running in Webhook mode successfully!"

if __name__ == "__main__":
    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook?drop_pending_updates=true")
        
        render_url = os.environ.get("RENDER_EXTERNAL_URL")
        if render_url:
            webhook_url = f"{render_url}/{TOKEN}"
            bot.set_webhook(url=webhook_url)
            print(f"Webhook forcefully set to: {webhook_url}")

        port = int(os.environ.get("PORT", 10000))
        app.run(host="0.0.0.0", port=port)
    except Exception as e:
        print(f"Webhook server error: {e}")
