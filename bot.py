import os
import threading
import random
import string
from datetime import datetime
import psycopg2
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

TOKEN = '8788513514:AAGwboQDDtl198sib3_3GX3ahtmh0wg4iS0'
bot = telebot.TeleBot(TOKEN)

ADMIN_ID = 5813365228

GMAIL_RATE = 0.15
MIN_PAYOUT = 0.20
REF_BONUS = 0.02

# Supabase Session Pooler URL with correct port 6543 and password
DATABASE_URL = "postgresql://postgres.ijussavmhziblqswfgwf:mamun347731@aws-0-ap-southeast-2.pooler.supabase.com:6543/postgres"

# --- Flask Web Server to keep Render Alive ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def get_db():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def init_db():
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
            status TEXT DEFAULT 'pending',
            date TEXT,
            reason TEXT DEFAULT NULL,
            account_type TEXT DEFAULT 'New Gmail'
        )
    ''')
    cursor.execute('''
        ALTER TABLE pending_tasks ADD COLUMN IF NOT EXISTS reason TEXT DEFAULT NULL;
    ''')
    cursor.execute('''
        ALTER TABLE pending_tasks ADD COLUMN IF NOT EXISTS account_type TEXT DEFAULT 'New Gmail';
    ''')
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

init_db()

def get_user_data(user_id, referred_by=None):
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
    return {"balance": row[0], "hold_balance": row[1], "completed_count": row[2]}

# --- Dynamic Random Difficult Gmail Generator ---
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

def task_inline_menu():
    markup = InlineKeyboardMarkup()
    btn_done = InlineKeyboardButton("✔ Done", callback_data="btn_done")
    btn_cancel = InlineKeyboardButton("🚫 Cancel registration", callback_data="btn_cancel")
    btn_help = InlineKeyboardButton("❓ How to create account", callback_data="btn_help")
    markup.add(btn_done)
    markup.add(btn_cancel)
    markup.add(btn_help)
    return markup

user_states = {}
user_temp_data = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
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

@bot.message_handler(commands=['admin'])
def admin_panel(message):
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

@bot.message_handler(content_types=['text', 'photo'])
def handle_message(message):
    user_id = message.chat.id
    
    if user_id in user_states:
        state = user_states[user_id]
        
        # Admin Rejection Reason Handler
        if state.startswith("awaiting_reject_reason_") and user_id == ADMIN_ID:
            parts = state.split("_")
            task_id = int(parts[3])
            target_user_id = int(parts[4])
            del user_states[user_id]
            
            reason = message.caption if message.content_type == 'photo' else message.text
            if not reason:
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
                if message.content_type == 'photo':
                    photo_id = message.photo[-1].file_id
                    bot.send_photo(
                        target_user_id,
                        photo=photo_id,
                        caption=f"❌ Sorry, your Gmail account (`{email}`) submission was rejected.\n\n📝 **Reason:** {reason}",
                        parse_mode="Markdown"
                    )
                else:
                    bot.send_message(
                        target_user_id,
                        f"❌ Sorry, your Gmail account (`{email}`) submission was rejected.\n\n📝 **Reason:** {reason}",
                        parse_mode="Markdown"
                    )
            except Exception as e:
                bot.send_message(ADMIN_ID, f"⚠️ Failed to send message to user: {e}")
            return

        # Admin Custom Price Handler
        if state.startswith("awaiting_custom_price_") and user_id == ADMIN_ID:
            parts = state.split("_")
            task_id = int(parts[3])
            target_user_id = int(parts[4])
            del user_states[user_id]
            
            try:
                custom_price = float(message.text.strip())
            except ValueError:
                bot.send_message(ADMIN_ID, "❌ Invalid amount! Please send a valid number (e.g. 0.30):")
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

        text = message.text if message.content_type == 'text' else ""
        user_data = get_user_data(user_id)
        
        # --- "Submit My Own" Multi-step Flow ---
        if state == "sub_awaiting_type":
            acc_type = "Old Gmail" if "old" in text.lower() else "New Gmail"
            user_temp_data[user_id] = {"account_type": acc_type}
            user_states[user_id] = "sub_awaiting_email"
            markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
            markup.add(KeyboardButton("🚫 Cancel registration"))
            bot.send_message(user_id, f"Selected: **{acc_type}**\n\n📬 Please enter your Gmail email address:", parse_mode="Markdown", reply_markup=markup)
            return

        elif state == "sub_awaiting_email":
            user_temp_data[user_id]["email"] = text
            user_states[user_id] = "sub_awaiting_password"
            markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
            markup.add(KeyboardButton("🚫 Cancel registration"))
            bot.send_message(user_id, "🔐 Please enter your password:", reply_markup=markup)
            return
            
        elif state == "sub_awaiting_password":
            user_temp_data[user_id]["password"] = text
            user_states[user_id] = "sub_awaiting_recovery"
            markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
            markup.add(KeyboardButton("⏭ Skip recovery email"))
            markup.add(KeyboardButton("🚫 Cancel registration"))
            bot.send_message(user_id, "📧 Please enter your recovery email address, or tap **Skip** — it is optional:", reply_markup=markup)
            return
            
        elif state == "sub_awaiting_recovery":
            user_temp_data[user_id]["recovery"] = text if "skip" not in text.lower() else "None"
            
            acc = user_temp_data[user_id]
            email = acc["email"]
            password = acc["password"]
            acc_type = acc["account_type"]
            current_date = datetime.now().strftime("%m/%d/%Y")
            
            if user_id in user_states:
                del user_states[user_id]
            if user_id in user_temp_data:
                del user_temp_data[user_id]
                
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO pending_tasks (user_id, email, password, status, date, account_type) VALUES (%s, %s, %s, 'pending', %s, %s)", (user_id, email, password, current_date, acc_type))
            cursor.execute("UPDATE users SET hold_balance = hold_balance + %s WHERE user_id = %s", (GMAIL_RATE, user_id))
            cursor.execute("SELECT currval(pg_get_serial_sequence('pending_tasks','id'))")
            task_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            
            user_info = message.from_user
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
                    f"🔔 **New Pending Task ({acc_type})!**\n\n"
                    f"👤 Name: {name}\n"
                    f"🔗 Username: {username}\n"
                    f"🆔 User ID: `{user_id}`\n"
                    f"💰 Balance: ${u_bal}\n"
                    f"✅ Approved Gmails: {u_completed}\n\n"
                    f"📂 Type: **{acc_type}**\n"
                    f"📧 Email: `{email}`\n"
                    f"🔑 Password: `{password}`",
                    parse_mode="Markdown",
                    reply_markup=markup
                )
            except:
                pass

            bot.send_message(
                user_id,
                f"⏳ Task submitted successfully ({acc_type})!\n\nYour account is currently under **Hold (Pending review)**. Once admin verifies it, reward will be added to your balance.",
                reply_markup=main_menu()
            )
            return

        if state in ["payout_bkash", "payout_nagad", "payout_crypto"]:
            method = "bKash" if state == "payout_bkash" else ("Nagad" if state == "payout_nagad" else "Crypto (BEP20)")
            del user_states[user_id]
            
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
                bot.send_message(
                    ADMIN_ID,
                    f"🔔 **New Payout Request!**\n\nUser ID: `{user_id}`\nMethod: `{method}`\nAmount: `${bal:.2f}`\nDetails/Number: `{text}`",
                    parse_mode="Markdown",
                    reply_markup=markup
                )
            except:
                pass
            
            bot.send_message(user_id, f"✅ Withdrawal request of ${bal:.2f} via {method} submitted successfully!", reply_markup=main_menu())
            return
            
        elif state.startswith("awaiting_txid_") and user_id == ADMIN_ID:
            target_user_id = int(state.split("_")[2])
            del user_states[user_id]
            
            txid = text
            try:
                bot.send_message(
                    target_user_id,
                    f"🎉 **Your Payout has been Paid!**\n\n✅ Transaction ID / Proof:\n`{txid}`",
                    parse_mode="Markdown"
                )
                bot.send_message(ADMIN_ID, f"✅ TXID successfully sent to user `{target_user_id}`!", parse_mode="Markdown")
            except Exception as e:
                bot.send_message(ADMIN_ID, f"❌ Failed to send message to user: {e}")
            return
            
        elif state == "awaiting_broadcast" and user_id == ADMIN_ID:
            del user_states[user_id]
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

    text = message.text
    user_data = get_user_data(user_id)

    if "Register a new Gmail" in text:
        conn = get_db()
        cursor = conn.cursor()
        
        selected_acc = generate_unique_gmail(cursor)
        
        if not selected_acc:
            cursor.close()
            conn.close()
            bot.send_message(user_id, "❌ Sorry, could not generate a unique Gmail right now. Please try again later.")
            return
            
        cursor.execute("INSERT INTO assigned_gmails (email, user_id, status) VALUES (%s, %s, 'assigned')", (selected_acc['email'], user_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        response_text = (
            f"Register Gmail account using the specified data and get ${GMAIL_RATE:.2f}\n\n"
            f"First name: `{selected_acc['first']}`\n"
            f"Last name: {selected_acc['last']}\n"
            f"Email: `{selected_acc['email']}`\n"
            f"Password: `{selected_acc['pass']}`\n"
            f"Year of birth: {selected_acc['year']}\n\n"
            f"🔐 Be sure to use the specified data, otherwise the account will not be paid."
        )
        
        bot.send_message(user_id, response_text, parse_mode="Markdown", reply_markup=task_inline_menu())

    elif "Submit my own" in text:
        user_states[user_id] = "sub_awaiting_type"
        markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        markup.add(KeyboardButton("⭐ New Gmail"), KeyboardButton("🌟 Old Gmail"))
        markup.add(KeyboardButton("🚫 Cancel registration"))
        bot.send_message(user_id, "📥 Please select which type of Gmail you want to submit:", reply_markup=markup)
        
    elif text == "💰 Balance":
        bal = round(user_data["balance"], 2)
        hold = round(user_data["hold_balance"], 2)
        response_text = f"Balance: {bal}$\nHold: {hold}$"
        bot.send_message(user_id, response_text, reply_markup=balance_menu())
        
    elif text == "💳 Payout":
        bal = round(user_data["balance"], 2)
        if bal < MIN_PAYOUT:
            bot.send_message(user_id, f"⚠️ Minimum payout amount is ${MIN_PAYOUT:.2f}. Your current balance is ${bal:.2f}.")
        else:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔹 bKash (Fee: 5 BDT)", callback_data="pay_bkash"))
            markup.add(InlineKeyboardButton("🔹 Nagad (Fee: 5 BDT)", callback_data="pay_nagad"))
            markup.add(InlineKeyboardButton("🔹 Crypto BEP20 (Fee: $0.03)", callback_data="pay_crypto"))
            bot.send_message(user_id, f"💰 Your Balance: ${bal:.2f}\n\nSelect your payout method:", reply_markup=markup)
            
    elif text == "📝 Balance history":
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT text FROM history WHERE user_id = %s ORDER BY id DESC LIMIT 10", (user_id,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not rows:
            bot.send_message(user_id, "📝 No transactions found in your balance history.")
        else:
            history_text = "📝 Balance History:\n\n" + "\n".join([r[0] for r in rows])
            bot.send_message(user_id, history_text)
            
    elif text == "⬅️ Back" or text == "🚫 Cancel registration":
        if user_id in user_states:
            del user_states[user_id]
        if user_id in user_temp_data:
            del user_temp_data[user_id]
        bot.send_message(user_id, "Main Menu:", reply_markup=main_menu())
        
    elif text == "👥 My referrals":
        bot_info = bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
        bot.send_message(user_id, f"👥 **Your Referral Link:**\n{ref_link}\n\n🎁 Invite friends and earn ${REF_BONUS:.2f} per active referral!", parse_mode="Markdown")
        
    elif text == "📋 My accounts":
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT email, password, status, date, reason, account_type FROM pending_tasks WHERE user_id = %s ORDER BY id DESC", (user_id,))
        tasks = cursor.fetchall()
        cursor.close()
        conn.close()
        
        total_count = len(tasks)
        paid_count = sum(1 for t in tasks if t[2] == 'approved')
        pending_count = sum(1 for t in tasks if t[2] == 'pending')
        declined_count = sum(1 for t in tasks if t[2] == 'rejected')
        
        summary_text = (
            f"📁 **Your submitted accounts ({total_count}):**\n\n"
            f"📊 Summary:\n"
            f"✅ Paid: {paid_count}\n"
            f"⏳ Pending: {pending_count}\n"
            f"❌ Declined: {declined_count}\n"
            f"⚠️ Failed: 0\n"
        )
        bot.send_message(user_id, summary_text, parse_mode="Markdown")
        
        if tasks:
            for i, t in enumerate(tasks[:15], 1):
                email, pwd, status, date_str, reason, acc_type = t[0], t[1], t[2], t[3], t[4], t[5]
                if not date_str:
                    date_str = datetime.now().strftime("%m/%d/%Y")
                if not acc_type:
                    acc_type = "New Gmail"
                
                if status == 'approved':
                    icon = "✅"
                    status_text = "paid"
                elif status == 'pending':
                    icon = "⏳"
                    status_text = "pending"
                else:
                    icon = "❌"
                    status_text = "declined"
                
                msg = (
                    f"{i}. {icon} {acc_type}\n"
                    f"💰 ${GMAIL_RATE:.2f} | 📅 {date_str} | {status_text}\n"
                    f"📋 `{email}:{pwd}`"
                )
                if status == 'rejected' and reason:
                    msg += f"\n💬 {reason}"
                
                bot.send_message(user_id, msg, parse_mode="Markdown")
        
    elif text == "⚙️ Settings":
        bot.send_message(user_id, "⚙️ Settings option coming soon.")
        
    elif text == "💬 Help":
        bot.send_message(user_id, "💬 Support contact: @mamun9894")

@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    user_id = call.message.chat.id
    
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
        bot.edit_message_text(
            chat_id=ADMIN_ID,
            message_id=call.message.message_id,
            text=call.message.text + f"\n\n👉 **Status:** Clicked! Now send the **Transaction ID (TXID)** in chat for user `{target_user_id}`:",
            parse_mode="Markdown"
        )
        
    elif call.data.startswith("customapp_"):
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "You are not authorized!", show_alert=True)
            return
            
        parts = call.data.split("_")
        task_id = int(parts[1])
        target_user_id = int(parts[2])
        
        user_states[ADMIN_ID] = f"awaiting_custom_price_{task_id}_{target_user_id}"
        bot.answer_callback_query(call.id)
        bot.send_message(ADMIN_ID, "💵 Please send the **Custom Price / Amount** (e.g. 0.30 or 0.50) to add to user's balance:")
        
    elif call.data == "btn_done":
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM assigned_gmails WHERE user_id = %s AND status = 'assigned'", (user_id,))
        assigned = cursor.fetchone()
        
        if not assigned:
            cursor.close()
            conn.close()
            bot.answer_callback_query(call.id, "No active task found!", show_alert=True)
            return
            
        email = assigned[0]
        prefix = email.split('@')[0]
        letters = "".join([c for c in prefix if c.isalpha()])
        numbers = "".join([c for c in prefix if c.isdigit()])
        password = f"{letters[:3].capitalize()}#{numbers}Xk"
        current_date = datetime.now().strftime("%m/%d/%Y")
        
        cursor.execute("UPDATE assigned_gmails SET status = 'submitted' WHERE email = %s", (email,))
        cursor.execute("UPDATE users SET hold_balance = hold_balance + %s WHERE user_id = %s", (GMAIL_RATE, user_id))
        cursor.execute("INSERT INTO pending_tasks (user_id, email, password, status, date, account_type) VALUES (%s, %s, %s, 'pending', %s, 'New Gmail')", (user_id, email, password, current_date))
        cursor.execute("SELECT currval(pg_get_serial_sequence('pending_tasks','id'))")
        task_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        user_info = call.from_user
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
                f"🔔 **New Pending Task Check!**\n\n"
                f"👤 Name: {name}\n"
                f"🔗 Username: {username}\n"
                f"🆔 User ID: `{user_id}`\n"
                f"💰 Balance: ${u_bal}\n"
                f"✅ Approved Gmails: {u_completed}\n\n"
                f"📧 Email: `{email}`\n"
                f"🔑 Password: `{password}`",
                parse_mode="Markdown",
                reply_markup=markup
            )
        except:
            pass

        bot.answer_callback_query(call.id, "Submitted! Account is under review (Hold).")
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text=f"⏳ Task submitted successfully!\n\nYour account is currently under **Hold (Pending review)**. Once admin verifies it, ${GMAIL_RATE:.2f} will be added to your balance within 24 hours."
        )
        
    elif call.data.startswith("app_") or call.data.startswith("rej_") or call.data.startswith("cancelapp_"):
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "You are not authorized!", show_alert=True)
            return
            
        parts = call.data.split("_")
        action = parts[0]
        task_id = int(parts[1])
        target_user_id = int(parts[2])
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT email, status FROM pending_tasks WHERE id = %s", (task_id,))
        task = cursor.fetchone()
        
        if not task:
            cursor.close()
            conn.close()
            bot.answer_callback_query(call.id, "Task not found!")
            return
            
        email = task[0]
        current_status = task[1]
        
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
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"✅ Task for `{email}` has been **APPROVED**.",
                reply_markup=markup
            )
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
                
            cursor.execute("UPDATE pending_tasks SET status = 'rejected', reason = 'Approval cancelled by admin' WHERE id = %s", (task_id,))
            cursor.execute("UPDATE users SET balance = GREATEST(0, balance - %s), completed_count = GREATEST(0, completed_count - 1) WHERE user_id = %s", (GMAIL_RATE, target_user_id))
            cursor.execute("INSERT INTO history (user_id, text) VALUES (%s, %s)", (target_user_id, f"Approval Cancelled - Gmail ({email})"))
            conn.commit()
            cursor.close()
            conn.close()
            
            bot.answer_callback_query(call.id, "Approval cancelled successfully!")
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"❌ Approval for `{email}` has been **CANCELLED / REVOKED**.",
                parse_mode="Markdown"
            )
            try:
                bot.send_message(target_user_id, f"⚠️ Notice: Your approved Gmail account ({email}) approval was cancelled by admin.")
            except:
                pass

        elif action == "rej":
            cursor.close()
            conn.close()
            user_states[ADMIN_ID] = f"awaiting_reject_reason_{task_id}_{target_user_id}"
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                chat_id=ADMIN_ID,
                message_id=call.message.message_id,
                text=call.message.text + f"\n\n👉 **Status:** Rejected clicked! Now send the **Reject Reason (Text or Photo with caption)** in chat for user `{target_user_id}`:",
                parse_mode="Markdown"
            )

    elif call.data == "admin_view_pending":
        if call.from_user.id != ADMIN_ID:
            return
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, user_id, email, password, account_type FROM pending_tasks WHERE status = 'pending' LIMIT 5")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not rows:
            bot.answer_callback_query(call.id, "No pending tasks found!")
            return
            
        bot.answer_callback_query(call.id, "Showing pending tasks:")
        for r in rows:
            t_id, u_id, email, pwd, acc_type = r[0], r[1], r[2], r[3], r[4]
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
                f"⏳ Pending Task ({acc_type}):\n"
                f"🆔 User ID: `{u_id}`\n"
                f"💰 Balance: ${u_bal}\n"
                f"✅ Approved Gmails: {u_completed}\n"
                f"📂 Type: **{acc_type}**\n"
                f"📧 Email: `{email}`\n"
                f"🔑 Password: `{pwd}`",
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
        
        bot.answer_callback_query(call.id, "Registration cancelled.")
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text="❌ রেজিস্ট্রেশন বাতিল করা হয়েছে।"
        )
    elif call.data == "btn_help":
        bot.answer_callback_query(call.id, "নির্দেশনা পাঠানো হয়েছে।")
        bot.send_message(
            user_id,
            "ℹ️ নিয়মাবলি:\n1. জিমেইল অ্যাপে যান\n2. প্রদত্ত নাম ও জন্ম সাল দিয়ে একাউন্ট তৈরি করুন\n3. ঠিক নির্দিষ্ট জিমেইল এবং পাসওয়ার্ড ব্যবহার করুন\n4. কাজ শেষ হলে Done বাটনে ক্লিক করুন।"
        )
    elif call.data == "admin_broadcast" and user_id == ADMIN_ID:
        user_states[user_id] = "awaiting_broadcast"
        bot.send_message(ADMIN_ID, "📢 সকল ব্যবহারকারীকে পাঠানোর জন্য ব্রডকাস্ট মেসেজটি লিখুন:")

# Start Flask in a background thread so Render detects an active web port
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    print("Bot & Supabase Database connected successfully. Running...")
    try:
        bot.remove_webhook()
        bot.infinity_polling(timeout=60, long_polling_timeout=60, skip_pending=True)
    except Exception as e:
        print(f"Polling error: {e}")
