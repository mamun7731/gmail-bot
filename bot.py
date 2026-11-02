import os
import random
import string
import time
from datetime import datetime
import psycopg2
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from flask import Flask, request
import requests
import pyotp
import cv2
import numpy as np
import io

TOKEN = '8788513514:AAGwboQDDtl198sib3_3GX3ahtmh0wg4iS0'
bot = telebot.TeleBot(TOKEN)

ADMIN_ID = 5813365228

GMAIL_RATE = 0.15
MIN_PAYOUT = 0.20
REF_BONUS = 0.02

# How to enable 2FA video link
HOW_TO_2FA_VIDEO = "https://t.me/Gmail_Farmer2_0News/22"

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
                two_fa TEXT DEFAULT 'None',
                status TEXT DEFAULT 'pending',
                date TEXT,
                reason TEXT DEFAULT NULL,
                account_type TEXT DEFAULT 'New Gmail',
                reward_amount REAL DEFAULT 0.15
            )
        ''')
        cursor.execute('ALTER TABLE pending_tasks ADD COLUMN IF NOT EXISTS recovery TEXT DEFAULT \'None\';')
        cursor.execute('ALTER TABLE pending_tasks ADD COLUMN IF NOT EXISTS two_fa TEXT DEFAULT \'None\';')
        cursor.execute('ALTER TABLE pending_tasks ADD COLUMN IF NOT EXISTS date TEXT;')
        cursor.execute('ALTER TABLE pending_tasks ADD COLUMN IF NOT EXISTS reason TEXT DEFAULT NULL;')
        cursor.execute("ALTER TABLE pending_tasks ADD COLUMN IF NOT EXISTS account_type TEXT DEFAULT 'New Gmail';")
        cursor.execute("ALTER TABLE pending_tasks ADD COLUMN IF NOT EXISTS reward_amount REAL DEFAULT 0.15;")
        
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

def extract_secret_from_qr(image_stream):
    try:
        image_bytes = image_stream.read()
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        detector = cv2.QRCodeDetector()
        val, points, _ = detector.detectAndDecode(img)
        
        if val and "secret=" in val:
            parsed_secret = val.split("secret=")[1].split("&")[0]
            return parsed_secret
    except Exception as e:
        print(f"QR Extract Error: {e}")
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

def process_submission_done(user_id, email, password, recovery, two_fa, acc_type, message_obj):
    try:
        current_date = datetime.now().strftime("%m/%d/%Y")
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO pending_tasks (user_id, email, password, recovery, two_fa, status, date, account_type, reward_amount) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (user_id, email, password, recovery, two_fa, 'pending', current_date, acc_type, GMAIL_RATE)
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
                f"🔔 **New Pending Task ({acc_type})!**\n\n🆔 User ID: `{user_id}`\n💰 Balance: ${u_bal}\n✅ Approved Gmails: {u_completed}\n\n📂 Type: **{acc_type}**\n📧 Email: `{email}`\n🔑 Password: `{password}`\n🔄 Recovery: `{recovery}`\n🔐 2FA Key: `{two_fa}`\n\n📋 **Format:** `{email}:{password}::{two_fa}`",
                parse_mode="Markdown",
                reply_markup=markup
            )
        except Exception as e:
            print(f"Admin notify error: {e}")

        success_message = (
            f"✅ **Task submitted successfully ({acc_type})!**\n\n"
            f"Your account is currently under **Hold (Pending review)**. Once admin verifies it, reward will be added to your balance. 💸"
        )

        bot.send_message(
            user_id,
            success_message,
            parse_mode="Markdown",
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
                cursor.execute("SELECT email, password, status, date, reason, account_type, recovery, two_fa FROM pending_tasks WHERE user_id = %s ORDER BY id DESC", (user_id,))
                tasks = cursor.fetchall()
            except Exception as e:
                conn.rollback()
                cursor.execute("SELECT email, password, status, date, reason FROM pending_tasks WHERE user_id = %s ORDER BY id DESC", (user_id,))
                rows = cursor.fetchall()
                tasks = [(r[0], r[1], r[2], r[3], r[4], "New Gmail", "None", "None") for r in rows]
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
                    if status == 'rejected':
                        if reason and reason.strip():
                            msg += f"\n💬 **Decline Reason:** {reason}"
                        else:
                            msg += f"\n💬 **Decline Reason:** Photo proof provided / Rejected by admin."
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
                
                user_temp_data[user_id]["password"] = password
                user_temp_data[user_id]["account_type"] = "New Gmail"
                user_temp_data[user_id]["recovery"] = "None"
                
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton("🔐 Enable 2FA", callback_data="reg_enable_2fa"))
                markup.add(InlineKeyboardButton("▶️ How to enable 2FA", callback_data="reg_how_to_2fa"))
                markup.add(InlineKeyboardButton("❌ Cancel Registration", callback_data="reg_cancel"))
                
                bot.send_message(user_id, "Choose an option below to proceed with your registration:", reply_markup=markup)
                return

        if user_id in user_states:
            state = user_states[user_id]
            
            if state.startswith("awaiting_reject_reason_") and user_id == ADMIN_ID:
                parts = state.split("_")
                task_id = int(parts[3])
                target_user_id = int(parts[4])
                user_states.pop(user_id, None)
                
                reason = message.text if message.content_type == 'text' else (message.caption or "")
                photo_id = message.photo[-1].file_id if message.content_type == 'photo' else None
                
                if photo_id:
                    if reason:
                        reason = f"{reason} [Photo attached]"
                    else:
                        reason = "Rejected with photo proof [Photo attached]"
                elif not reason or not reason.strip():
                    reason = "No reason provided."
                    
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
                cursor.execute("UPDATE pending_tasks SET status = 'approved', reward_amount = %s WHERE id = %s", (custom_price, task_id))
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
                
                user_states[user_id] = "sub_awaiting_2fa"
                markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
                markup.add(KeyboardButton("⏭ Skip 2FA QR"), KeyboardButton("🚫 Cancel registration"))
                bot.send_message(user_id, "🔐 Please send the **2FA QR Code screenshot** (or text secret key), or tap **Skip 2FA QR**:", reply_markup=markup)
                return

            elif state == "sub_awaiting_2fa":
                two_fa_val = "None"
                is_register_flow = user_temp_data.get(user_id, {}).get("account_type") == "New Gmail" and "assigned_email" in user_temp_data.get(user_id, {})
                
                if message.content_type == 'photo':
                    try:
                        file_info = bot.get_file(message.photo[-1].file_id)
                        downloaded_file = bot.download_file(file_info.file_path)
                        image_stream = io.BytesIO(downloaded_file)
                        secret_key = extract_secret_from_qr(image_stream)
                        if secret_key:
                            two_fa_val = secret_key
                        else:
                            bot.send_message(user_id, "❌ QR Code scan করা যায়নি! অনুগ্রহ করে পরিষ্কার স্ক্রিনশট পাঠান অথবা টেক্সট সিক্রেট কি দিন।")
                            return
                    except Exception as e:
                        print(f"2FA QR Read Error: {e}")
                        bot.send_message(user_id, "❌ QR Code পড়তে সমস্যা হয়েছে। আবার চেষ্টা করুন।")
                        return
                elif message.content_type == 'text':
                    if "skip" in text_lower or "⏭" in text:
                        if is_register_flow:
                            bot.send_message(user_id, "❌ 2FA QR Code is mandatory! Please send the QR screenshot or secret key.")
                            return
                        two_fa_val = "None"
                    else:
                        two_fa_val = text.strip()

                if is_register_flow and two_fa_val in ["None", "QR_Upload_Error", "QR_Uploaded_But_Not_Decoded"]:
                    bot.send_message(user_id, "❌ সঠিকভাবে QR code স্ক্যান হয়নি। অনুগ্রহ করে আবার পরিষ্কার স্ক্রিনশট পাঠান।")
                    return

                if user_id not in user_temp_data:
                    user_temp_data[user_id] = {}
                user_temp_data[user_id]["two_fa"] = two_fa_val
                
                acc = user_temp_data[user_id]
                email = acc.get("email", "unknown@gmail.com")
                password = acc.get("password", "123456")
                recovery = acc.get("recovery", "None")
                two_fa = acc.get("two_fa", "None")
                acc_type = acc.get("account_type", "New Gmail")
                
                user_states.pop(user_id, None)

                if not is_register_flow or two_fa == "None":
                    user_temp_data.pop(user_id, None)
                    process_submission_done(user_id, email, password, recovery, two_fa, acc_type, message)
                    return

                otp_code = "N/A"
                try:
                    totp = pyotp.TOTP(two_fa)
                    otp_code = totp.now()
                except Exception as e:
                    print(f"OTP Generation Error: {e}")

                user_verification_msg = (
                    f"📧 **Email:** `{email}`\n"
                    f"🔑 **Password:** `{password}`\n"
                    f"🔐 **OTP Code:** `{otp_code}`\n\n"
                    f"⏳ *Time left for current OTP code: 30 seconds*\n\n"
                    f"👇 **Click Done after completing verification!**"
                )
                
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton("✔ Done", callback_data="reg_final_done"))
                markup.add(InlineKeyboardButton("❌ Cancel Registration", callback_data="reg_cancel"))
                
                bot.send_message(user_id, user_verification_msg, parse_mode="Markdown", reply_markup=markup)
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
                        bot.send_message(u[0], f"📢 **Broadcast Message:**\n\n{text}", parse_mode=None)
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
            
        elif call.data == "reg_enable_2fa":
            bot.answer_callback_query(call.id)
            user_states[user_id] = "sub_awaiting_2fa"
            
            markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
            markup.add(KeyboardButton("🚫 Cancel registration"))
            bot.send_message(user_id, "🔐 Please send the **2FA QR Code screenshot** (or text secret key) to complete registration:", reply_markup=markup)
            
        elif call.data == "reg_how_to_2fa":
            bot.answer_callback_query(call.id)
            try:
                bot.send_video(user_id, HOW_TO_2FA_VIDEO, caption="▶️ **How to enable 2FA Guide Video**\n\nWatch this video to learn how to enable 2FA and get the QR code.", parse_mode="Markdown")
            except Exception:
                bot.send_message(user_id, f"▶️ **How to enable 2FA Guide:**\n{HOW_TO_2FA_VIDEO}")
            
        elif call.data == "reg_cancel":
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM assigned_gmails WHERE user_id = %s AND status = 'assigned'", (user_id,))
            conn.commit()
            cursor.close()
            conn.close()
            
            user_states.pop(user_id, None)
            user_temp_data.pop(user_id, None)
            bot.answer_callback_query(call.id, "Registration cancelled.")
            try:
                bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id, text="❌ Registration has been cancelled.", reply_markup=None)
            except:
                pass
            bot.send_message(user_id, "Main Menu:", reply_markup=main_menu())
            
        elif call.data == "reg_final_done":
            bot.answer_callback_query(call.id, "Task submitted successfully!")
            try:
                bot.edit_message_reply_markup(chat_id=user_id, message_id=call.message.message_id, reply_markup=None)
            except:
                pass
                
            if user_id in user_temp_data:
                acc = user_temp_data[user_id]
                email = acc.get("email", "unknown@gmail.com")
                password = acc.get("password", "123456")
                recovery = acc.get("recovery", "None")
                two_fa = acc.get("two_fa", "None")
                acc_type = acc.get("account_type", "New Gmail")
                
                user_temp_data.pop(user_id, None)
                process_submission_done(user_id, email, password, recovery, two_fa, acc_type, call.message)
            else:
                bot.send_message(user_id, "❌ Session expired or already submitted.", reply_markup=main_menu())
            return
            
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
            
            if user_id not in user_temp_data:
                user_temp_data[user_id] = {}
            user_temp_data[user_id]["assigned_email"] = email
            user_temp_data[user_id]["password"] = password
            user_temp_data[user_id]["account_type"] = "New Gmail"
            user_temp_data[user_id]["recovery"] = "None"
            
            bot.answer_callback_query(call.id)
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔐 Enable 2FA", callback_data="reg_enable_2fa"))
            markup.add(InlineKeyboardButton("▶️ How to enable 2FA", callback_data="reg_how_to_2fa"))
            markup.add(InlineKeyboardButton("❌ Cancel Registration", callback_data="reg_cancel"))
            
            bot.send_message(user_id, "Choose an option below to proceed with your registration:", reply_markup=markup)
            return
            
        elif call.data.startswith("app_") or call.data.startswith("rej_") or call.data.startswith("cancelapp_"):
            if call.from_user.id != ADMIN_ID:
                bot.answer_callback_query(call.id, "You are not authorized!", show_alert=True)
                return
                
            parts = call.data.split("_")
            action, task_id, target_user_id = parts[0], int(parts[1]), int(parts[2])
            
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT email, status, reward_amount FROM pending_tasks WHERE id = %s", (task_id,))
            task = cursor.fetchone()
            if not task:
                cursor.close()
                conn.close()
                bot.answer_callback_query(call.id, "Task not found!")
                return
                
            email, current_status, reward_amt = task[0], task[1], (task[2] if task[2] is not None else GMAIL_RATE)
            
            if action == "app":
                if current_status != 'pending':
                    cursor.close()
                    conn.close()
                    bot.answer_callback_query(call.id, "Task already processed!")
                    return
                cursor.execute("UPDATE pending_tasks SET status = 'approved' WHERE id = %s", (task_id,))
                cursor.execute("UPDATE users SET balance = balance + %s, hold_balance = GREATEST(0, hold_balance - %s), completed_count = completed_count + 1 WHERE user_id = %s", (GMAIL_RATE, GMAIL_RATE, target_user_id))
                cursor.execute("UPDATE pending_tasks SET reward_amount = %s WHERE id = %s", (GMAIL_RATE, task_id))
                cursor.execute("INSERT INTO history (user_id, text) VALUES (%s, %s)", (target_user_id, f"+${GMAIL_RATE:.2f} - Gmail Approved ({email})"))
                conn.commit()
                cursor.close()
                conn.close()
                
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton("❌ Cancel Approval (Revoke)", callback_data=f"cancelapp_{task_id}_{target_user_id}"))
                bot.answer_callback_query(call.id, "Approved successfully!")
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=call.message.text + f"\n\n✅ **Status:** Task for `{email}` has been **APPROVED**.", reply_markup=markup)
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
                
                deduct_amount = reward_amt if reward_amt else GMAIL_RATE

                cursor.execute("UPDATE pending_tasks SET status = 'rejected', reason = 'Approval cancelled by admin' WHERE id = %s", (task_id,))
                cursor.execute("UPDATE users SET balance = GREATEST(0, balance - %s), completed_count = GREATEST(0, completed_count - 1) WHERE user_id = %s", (deduct_amount, target_user_id))
                cursor.execute("INSERT INTO history (user_id, text) VALUES (%s, %s)", (target_user_id, f"Approval Cancelled - Gmail ({email}) [Deducted ${deduct_amount:.2f}]"))
                conn.commit()
                cursor.close()
                conn.close()
                
                bot.answer_callback_query(call.id, f"Approval cancelled and ${deduct_amount:.2f} deducted!")
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=call.message.text + f"\n\n❌ **Status:** Approval for `{email}` has been **CANCELLED / REVOKED**.", parse_mode="Markdown")
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

        elif call.data.startswith("admin_pending_") or call.data == "admin_view_pending":
            if call.from_user.id != ADMIN_ID:
                bot.answer_callback_query(call.id, "Unauthorized!", show_alert=True)
                return
            
            offset = 0
            if call.data.startswith("admin_pending_"):
                try:
                    offset = int(call.data.split("_")[2])
                except:
                    offset = 0

            conn = get_db()
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT id, user_id, email, password, recovery, two_fa, account_type FROM pending_tasks WHERE status = 'pending' ORDER BY id ASC LIMIT 5 OFFSET %s", (offset,))
                rows = cursor.fetchall()
                
                cursor.execute("SELECT COUNT(*) FROM pending_tasks WHERE status = 'pending'")
                total_pending = cursor.fetchone()[0]
            except Exception as e:
                print(f"Pending fetch error: {e}")
                rows = []
                total_pending = 0
            cursor.close()
            conn.close()
            
            if not rows and offset == 0:
                bot.answer_callback_query(call.id, "No pending tasks found!", show_alert=True)
                return
            elif not rows:
                bot.answer_callback_query(call.id, "No more pending tasks!", show_alert=True)
                return
                
            bot.answer_callback_query(call.id, f"Showing tasks {offset+1} to {offset+len(rows)} of {total_pending}")
            
            for idx, r in enumerate(rows, start=offset+1):
                try:
                    t_id, u_id, email, pwd, recovery, two_fa, acc_type = r[0], r[1], r[2], r[3], r[4], r[5], r[6]
                except Exception as ex:
                    print(f"Row unpacking error: {ex}")
                    continue

                if not acc_type:
                    acc_type = "New Gmail"
                if not recovery:
                    recovery = "None"
                if not two_fa:
                    two_fa = "None"
                    
                u_data = get_user_data(u_id)
                u_bal = round(u_data["balance"], 2)
                u_completed = u_data["completed_count"]
                
                markup = InlineKeyboardMarkup()
                markup.add(
                    InlineKeyboardButton("✅ Approve ($0.15)", callback_data=f"app_{t_id}_{u_id}"),
                    InlineKeyboardButton("💵 Custom Price", callback_data=f"customapp_{t_id}_{u_id}")
                )
                markup.add(InlineKeyboardButton("❌ Reject", callback_data=f"rej_{t_id}_{u_id}"))
                
                try:
                    bot.send_message(
                        ADMIN_ID,
                        f"🔔 **Pending Task #{idx} ({acc_type})!**\n\n🆔 User ID: `{u_id}`\n💰 Balance: ${u_bal}\n✅ Approved Gmails: {u_completed}\n\n📂 Type: **{acc_type}**\n📧 Email: `{email}`\n🔑 Password: `{pwd}`\n🔄 Recovery: `{recovery}`\n🔐 2FA Key: `{two_fa}`\n\n📋 **Format:** `{email}:{password}::{two_fa}`",
                        parse_mode="Markdown",
                        reply_markup=markup
                    )
                    time.sleep(1.0)
                except Exception as ex:
                    print(f"Send task message error: {ex}")

            if offset + 5 < total_pending:
                next_offset = offset + 5
                nav_markup = InlineKeyboardMarkup()
                nav_markup.add(InlineKeyboardButton("➡️ Next 5 Tasks", callback_data=f"admin_pending_{next_offset}"))
                
                try:
                    time.sleep(0.5)
                    bot.send_message(
                        ADMIN_ID,
                        f"📄 **Page info:** Showing tasks {offset+1} - {offset+len(rows)} of {total_pending}\nClick below to load next tasks:",
                        parse_mode="Markdown",
                        reply_markup=nav_markup
                    )
                except Exception as e:
                    print(f"Nav send error: {e}")

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
