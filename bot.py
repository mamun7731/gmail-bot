import os
import threading
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

# Supabase PostgreSQL Database URL with updated password
DATABASE_URL = "postgresql://postgres:Mamun347731@db.nadctophsunyanoxaqrv.supabase.co:5432/postgres"

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
            status TEXT DEFAULT 'pending'
        )
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

gmail_accounts = [
    {"first": "Masako", "last": "❌", "email": "izonuyujif168@gmail.com", "pass": "6zW1W4UhGgclbO", "year": "2000"},
    {"first": "Alena", "last": "❌", "email": "itadocato758@gmail.com", "pass": "BoFCRVFWJZbSU", "year": "2000"},
    {"first": "Tomey", "last": "❌", "email": "tomeyufop028@gmail.com", "pass": "TomeyP928501", "year": "2000"},
    {"first": "Xerizi", "last": "❌", "email": "xerizixacom91@gmail.com", "pass": "XeriziP782910", "year": "2000"},
    {"first": "Pujegara", "last": "❌", "email": "pujegara687@gmail.com", "pass": "PujeP6728190", "year": "2000"},
    {"first": "Elena", "last": "❌", "email": "elenarodriguez2000@gmail.com", "pass": "El#Rod7890xK", "year": "2000"},
    {"first": "Lucas", "last": "❌", "email": "lucasbennett00@gmail.com", "pass": "L8k!Benn2000", "year": "2000"},
    {"first": "Sophie", "last": "❌", "email": "sophiemiller2000@gmail.com", "pass": "SoPh!eM9918", "year": "2000"},
    {"first": "Aiden", "last": "❌", "email": "aidenwalker2001@gmail.com", "pass": "Aid!Walk9012", "year": "2000"},
    {"first": "Bella", "last": "❌", "email": "bellascott2002@gmail.com", "pass": "Bell#Scot345", "year": "2000"},
    {"first": "Caleb", "last": "❌", "email": "calebturner2003@gmail.com", "pass": "CalebT8890!", "year": "2000"},
    {"first": "Daisy", "last": "❌", "email": "daisycooper2004@gmail.com", "pass": "Dais#Coop112", "year": "2000"},
    {"first": "Ethan", "last": "❌", "email": "ethanward2005@gmail.com", "pass": "Eth!Ward5564", "year": "2000"},
    {"first": "Fiona", "last": "❌", "email": "fionapeterson2006@gmail.com", "pass": "Fion#Pete778", "year": "2000"},
    {"first": "Gavin", "last": "❌", "email": "gavinreed2007@gmail.com", "pass": "Gavi!Reed334", "year": "2000"},
    {"first": "Hazel", "last": "❌", "email": "hazelkelly2008@gmail.com", "pass": "Haz#Kell9900", "year": "2000"},
    {"first": "Ian", "last": "❌", "email": "ianhoward2009@gmail.com", "pass": "Ian!How2211", "year": "2000"},
    {"first": "Julia", "last": "❌", "email": "juliaramos2010@gmail.com", "pass": "Juli#Ram5544", "year": "2000"},
    {"first": "Kevin", "last": "❌", "email": "kevinkim2011@gmail.com", "pass": "Kev!Kim7788", "year": "2000"},
    {"first": "Lily", "last": "❌", "email": "lilycox2012@gmail.com", "pass": "Lily#Cox9988", "year": "2000"},
    {"first": "Mason", "last": "❌", "email": "masonward2013@gmail.com", "pass": "Maso!Ward1122", "year": "2000"},
    {"first": "Nora", "last": "❌", "email": "norarichardson2014@gmail.com", "pass": "Nora#Rich3344", "year": "2000"},
    {"first": "Owen", "last": "❌", "email": "owenwatson2015@gmail.com", "pass": "Owen!Wats5566", "year": "2000"},
    {"first": "Piper", "last": "❌", "email": "piperbrooks2016@gmail.com", "pass": "Pipe#Broo7788", "year": "2000"},
    {"first": "Quinn", "last": "❌", "email": "quinnsanders2017@gmail.com", "pass": "Quin!Sand9900", "year": "2000"},
    {"first": "Ruby", "last": "❌", "email": "rubyprice2018@gmail.com", "pass": "Ruby#Pric1133", "year": "2000"},
    {"first": "Sam", "last": "❌", "email": "sambennett2019@gmail.com", "pass": "Sam!Benn2244", "year": "2000"},
    {"first": "Tessa", "last": "❌", "email": "tessawood2020@gmail.com", "pass": "Tess#Wood5566", "year": "2000"},
    {"first": "Uriah", "last": "❌", "email": "uriahbarnes2021@gmail.com", "pass": "Uri!Barn7788", "year": "2000"},
    {"first": "Vera", "last": "❌", "email": "veraross2022@gmail.com", "pass": "Vera#Ross9900", "year": "2000"},
    {"first": "Wyatt", "last": "❌", "email": "wyatthenderson2023@gmail.com", "pass": "Wyat!Hend1144", "year": "2000"},
    {"first": "Xena", "last": "❌", "email": "xenacoleman2024@gmail.com", "pass": "Xena#Cole2255", "year": "2000"},
    {"first": "Yara", "last": "❌", "email": "yarajenkins2025@gmail.com", "pass": "Yara!Jenk3366", "year": "2000"},
    {"first": "Zack", "last": "❌", "email": "zackperry2026@gmail.com", "pass": "Zack#Perr4477", "year": "2000"},
    {"first": "Aaron", "last": "❌", "email": "aaronpowell2027@gmail.com", "pass": "Aaro!Powe5588", "year": "2000"},
    {"first": "Brooke", "last": "❌", "email": "brookelong2028@gmail.com", "pass": "Broo#Long6699", "year": "2000"},
    {"first": "Chase", "last": "❌", "email": "chasepatterson2029@gmail.com", "pass": "Chas!Patt7711", "year": "2000"},
    {"first": "Diana", "last": "❌", "email": "dianahughes2030@gmail.com", "pass": "Dian#Hugh8822", "year": "2000"},
    {"first": "Elias", "last": "❌", "email": "eliasflores2031@gmail.com", "pass": "Elia!Flor9933", "year": "2000"},
    {"first": "Faith", "last": "❌", "email": "faithwashington2032@gmail.com", "pass": "Fait#Wash1144", "year": "2000"},
    {"first": "George", "last": "❌", "email": "georgebutler2033@gmail.com", "pass": "Geor!Butl2255", "year": "2000"},
    {"first": "Hope", "last": "❌", "email": "hopesimmons2034@gmail.com", "pass": "Hope#Simm3366", "year": "2000"},
    {"first": "Isaac", "last": "❌", "email": "isaacfoster2035@gmail.com", "pass": "Isaa!Fost4477", "year": "2000"},
    {"first": "Jade", "last": "❌", "email": "jadegonzales2036@gmail.com", "pass": "Jade#Gonz5588", "year": "2000"},
    {"first": "Kyle", "last": "❌", "email": "kylebryant2037@gmail.com", "pass": "Kyle!Brya6699", "year": "2000"},
    {"first": "Luna", "last": "❌", "email": "lunaalexander2038@gmail.com", "pass": "Luna#Alex7711", "year": "2000"},
    {"first": "Miles", "last": "❌", "email": "milesrussell2039@gmail.com", "pass": "Mile!Russ8822", "year": "2000"},
    {"first": "Naomi", "last": "❌", "email": "naomigriffin2040@gmail.com", "pass": "Naom#Grif9933", "year": "2000"},
    {"first": "Oscar", "last": "❌", "email": "oscardiaz2041@gmail.com", "pass": "Osca!Diaz1144", "year": "2000"},
    {"first": "Paige", "last": "❌", "email": "paigehayes2042@gmail.com", "pass": "Paig#Haye2255", "year": "2000"},
    {"first": "Riley", "last": "❌", "email": "rileymyers2043@gmail.com", "pass": "Rile!Myer3366", "year": "2000"},
    {"first": "Stella", "last": "❌", "email": "stellaford2044@gmail.com", "pass": "Stel#Ford4477", "year": "2000"},
    {"first": "Tristan", "last": "❌", "email": "tristanhamilton2045@gmail.com", "pass": "Tris!Hami5588", "year": "2000"},
    {"first": "Violet", "last": "❌", "email": "violetgraham2046@gmail.com", "pass": "Vio#Grah6699", "year": "2000"},
    {"first": "Wesley", "last": "❌", "email": "wesleysullivan2047@gmail.com", "pass": "Wesl!Sull7711", "year": "2000"},
    {"first": "Zara", "last": "❌", "email": "zarawallace2048@gmail.com", "pass": "Zara#Wall8822", "year": "2000"},
    {"first": "Adam", "last": "❌", "email": "adamwoods2049@gmail.com", "pass": "Adam!Wood9933", "year": "2000"},
    {"first": "Chloe", "last": "❌", "email": "chloecole2050@gmail.com", "pass": "Chlo#Cole1144", "year": "2000"},
    {"first": "Dylan", "last": "❌", "email": "dylanwest2051@gmail.com", "pass": "Dyla!West2255", "year": "2000"},
    {"first": "Eva", "last": "❌", "email": "evajordan2052@gmail.com", "pass": "Eva#Jord3366", "year": "2000"},
    {"first": "Felix", "last": "❌", "email": "felixowens2053@gmail.com", "pass": "Feli!Owen4477", "year": "2000"},
    {"first": "Grace", "last": "❌", "email": "gracereynolds2054@gmail.com", "pass": "Grac#Reyn5588", "year": "2000"},
    {"first": "Henry", "last": "❌", "email": "henryfisher2055@gmail.com", "pass": "Henr!Fish6699", "year": "2000"},
    {"first": "Isla", "last": "❌", "email": "islaellis2056@gmail.com", "pass": "Isla#Elli7711", "year": "2000"},
    {"first": "Jack", "last": "❌", "email": "jackharrison2057@gmail.com", "pass": "Jack!Harr8822", "year": "2000"},
    {"first": "Kylie", "last": "❌", "email": "kyliegibson2058@gmail.com", "pass": "Kyli#Gibs9933", "year": "2000"},
    {"first": "Leo", "last": "❌", "email": "leomcdonald2059@gmail.com", "pass": "Leo!Mcdo1144", "year": "2000"},
    {"first": "Maya", "last": "❌", "email": "mayacruz2060@gmail.com", "pass": "Maya#Cruz2255", "year": "2000"},
    {"first": "Nolan", "last": "❌", "email": "nolanmarshall2061@gmail.com", "pass": "Nola!Mars3366", "year": "2000"},
    {"first": "Penelope", "last": "❌", "email": "penelopeortiz2062@gmail.com", "pass": "Pene#Ortiz4477", "year": "2000"},
    {"first": "Ryder", "last": "❌", "email": "rydergomez2063@gmail.com", "pass": "Ryde!Gome5588", "year": "2000"},
    {"first": "Savannah", "last": "❌", "email": "savannahmurray2064@gmail.com", "pass": "Sava#Murr6699", "year": "2000"},
    {"first": "Tobias", "last": "❌", "email": "tobiasfreeman2065@gmail.com", "pass": "Tobi!Free7711", "year": "2000"},
    {"first": "Victoria", "last": "❌", "email": "victoriawells2066@gmail.com", "pass": "Vict#Well8822", "year": "2000"},
    {"first": "Zachary", "last": "❌", "email": "zacharywebb2067@gmail.com", "pass": "Zach!Webb9933", "year": "2000"},
    {"first": "Alice", "last": "❌", "email": "alicesimpson2068@gmail.com", "pass": "Alic#Simp1144", "year": "2000"},
    {"first": "Brandon", "last": "❌", "email": "brandonstevens2069@gmail.com", "pass": "Bran!Stev2255", "year": "2000"},
    {"first": "Clara", "last": "❌", "email": "claratucker2070@gmail.com", "pass": "Clar#Tuck3366", "year": "2000"},
    {"first": "Damian", "last": "❌", "email": "damianporter2071@gmail.com", "pass": "Dami!Port4477", "year": "2000"},
    {"first": "Elena", "last": "❌", "email": "elenahunter2072@gmail.com", "pass": "Elen#Hunt5588", "year": "2000"},
    {"first": "Frankie", "last": "❌", "email": "frankiehicks2073@gmail.com", "pass": "Fran!Hick6699", "year": "2000"},
    {"first": "Gemma", "last": "❌", "email": "gemmacrawford2074@gmail.com", "pass": "Gemm#Craw7711", "year": "2000"},
    {"first": "Hayden", "last": "❌", "email": "haydenhenry2075@gmail.com", "pass": "Hayd!Henr8822", "year": "2000"},
    {"first": "Iris", "last": "❌", "email": "irisboyd2076@gmail.com", "pass": "Iris#Boyd9933", "year": "2000"},
    {"first": "Jaxon", "last": "❌", "email": "jaxonmason2077@gmail.com", "pass": "Jaxo!Maso1144", "year": "2000"},
    {"first": "Kendra", "last": "❌", "email": "kendramorales2078@gmail.com", "pass": "Kend#Mora2255", "year": "2000"},
    {"first": "Logan", "last": "❌", "email": "logankennedy2079@gmail.com", "pass": "Loga!Kenn3366", "year": "2000"},
    {"first": "Melanie", "last": "❌", "email": "melaniewarren2070@gmail.com", "pass": "Mela#Warr4477", "year": "2000"},
    {"first": "Nathan", "last": "❌", "email": "nathandixon2081@gmail.com", "pass": "Nath!Dixo5588", "year": "2000"},
    {"first": "Olive", "last": "❌", "email": "oliveramos2082@gmail.com", "pass": "Oliv#Ramo6699", "year": "2000"},
    {"first": "Preston", "last": "❌", "email": "prestonrice2083@gmail.com", "pass": "Pres!Rice7711", "year": "2000"},
    {"first": "Queenie", "last": "❌", "email": "queenieburns2084@gmail.com", "pass": "Quee#Burn8822", "year": "2000"},
    {"first": "Reid", "last": "❌", "email": "reidgordon2085@gmail.com", "pass": "Reid!Gord9933", "year": "2000"},
    {"first": "Sienna", "last": "❌", "email": "siennashaw2086@gmail.com", "pass": "Sien#Shaw1144", "year": "2000"},
    {"first": "Travis", "last": "❌", "email": "travisholmes2087@gmail.com", "pass": "Trav!Holm2255", "year": "2000"},
    {"first": "Una", "last": "❌", "email": "unarice2088@gmail.com", "pass": "Una#Rice3366", "year": "2000"},
    {"first": "Vincent", "last": "❌", "email": "vincentrobertson2089@gmail.com", "pass": "Vinc!Robe4477", "year": "2000"},
    {"first": "Willa", "last": "❌", "email": "willahunt2090@gmail.com", "pass": "Will#Hunt5588", "year": "2000"},
    {"first": "Xavier", "last": "❌", "email": "xavierblack2091@gmail.com", "pass": "Xavi!Blac6699", "year": "2000"},
    {"first": "Yvonne", "last": "❌", "email": "yvonnedaniels2092@gmail.com", "pass": "Yvon#Dani7711", "year": "2000"},
    {"first": "Zane", "last": "❌", "email": "zanepalmer2093@gmail.com", "pass": "Zane!Palm8822", "year": "2000"},
    {"first": "Amber", "last": "❌", "email": "ambermills2094@gmail.com", "pass": "Ambe#Mill9933", "year": "2000"},
    {"first": "Bryce", "last": "❌", "email": "brycenichols2095@gmail.com", "pass": "Bryc!Nich1144", "year": "2000"},
    {"first": "Cora", "last": "❌", "email": "coragrant2096@gmail.com", "pass": "Cora#Gran2255", "year": "2000"},
    {"first": "Derek", "last": "❌", "email": "derekknight2097@gmail.com", "pass": "Dere!Knig3366", "year": "2000"},
    {"first": "Elise", "last": "❌", "email": "eliseferguson2098@gmail.com", "pass": "Elis#Ferg4477", "year": "2000"},
    {"first": "Finn", "last": "❌", "email": "finnrose2099@gmail.com", "pass": "Finn!Rose5588", "year": "2000"},
    {"first": "Giselle", "last": "❌", "email": "gisellestone2100@gmail.com", "pass": "Gise#Ston6699", "year": "2000"},
    {"first": "Hudson", "last": "❌", "email": "hudsonhawkins2101@gmail.com", "pass": "Huds!Hawk7711", "year": "2000"},
    {"first": "Isabel", "last": "❌", "email": "isabeldunn2102@gmail.com", "pass": "Isab#Dunn8822", "year": "2000"},
    {"first": "Jared", "last": "❌", "email": "jaredperkins2103@gmail.com", "pass": "Jare!Perk9933", "year": "2000"},
    {"first": "Kara", "last": "❌", "email": "karahudson2104@gmail.com", "pass": "Kara#Huds1144", "year": "2000"},
    {"first": "Landon", "last": "❌", "email": "landonspencer2105@gmail.com", "pass": "Land!Spen2255", "year": "2000"},
    {"first": "Monica", "last": "❌", "email": "monicagardner2106@gmail.com", "pass": "Moni#Gard3366", "year": "2000"},
    {"first": "Nash", "last": "❌", "email": "nashpayne2107@gmail.com", "pass": "Nash!Payn4477", "year": "2000"},
    {"first": "Opal", "last": "❌", "email": "opalpierce2108@gmail.com", "pass": "Opal#Pier5588", "year": "2000"},
    {"first": "Parker", "last": "❌", "email": "parkerberry2109@gmail.com", "pass": "Park!Berr6699", "year": "2000"},
    {"first": "Queenie", "last": "❌", "email": "queeniematthews2110@gmail.com", "pass": "Quee#Matt7711", "year": "2000"},
    {"first": "Rowan", "last": "❌", "email": "rowanarnold2111@gmail.com", "pass": "Rowa!Arno8822", "year": "2000"},
    {"first": "Selena", "last": "❌", "email": "selenawagner2112@gmail.com", "pass": "Sele#Wagn9933", "year": "2000"},
    {"first": "Toby", "last": "❌", "email": "tobywillis2113@gmail.com", "pass": "Toby!Will1144", "year": "2000"},
    {"first": "Uma", "last": "❌", "email": "umaray2114@gmail.com", "pass": "Uma#Ray2255", "year": "2000"},
    {"first": "Vance", "last": "❌", "email": "vancewatkins2115@gmail.com", "pass": "Vanc!Watk3366", "year": "2000"},
    {"first": "Wendy", "last": "❌", "email": "wendyolson2116@gmail.com", "pass": "Wend#Olso4477", "year": "2000"},
    {"first": "Xander", "last": "❌", "email": "xandercarroll2117@gmail.com", "pass": "Xand#Carr5588", "year": "2000"},
    {"first": "Yasmine", "last": "❌", "email": "yasmineduncan2118@gmail.com", "pass": "Yasm#Dunc6699", "year": "2000"},
    {"first": "Zion", "last": "❌", "email": "zionsnyder2119@gmail.com", "pass": "Zion!Snyd7711", "year": "2000"},
    {"first": "Ashton", "last": "❌", "email": "ashtonhart2120@gmail.com", "pass": "Asht!Hart8822", "year": "2000"},
    {"first": "Bianca", "last": "❌", "email": "biancacunningham2121@gmail.com", "pass": "Bian#Cunn9933", "year": "2000"},
    {"first": "Cole", "last": "❌", "email": "colebradley2122@gmail.com", "pass": "Cole!Brad1144", "year": "2000"},
    {"first": "Dakota", "last": "❌", "email": "dakotalane2123@gmail.com", "pass": "Dako#Lane2255", "year": "2000"},
    {"first": "Eden", "last": "❌", "email": "edenandrews2124@gmail.com", "pass": "Eden!Andr3366", "year": "2000"},
    {"first": "Flint", "last": "❌", "email": "flintruiz2125@gmail.com", "pass": "Flin#Ruiz4477", "year": "2000"},
    {"first": "Gia", "last": "❌", "email": "giaharper2126@gmail.com", "pass": "Gia!Harp5588", "year": "2000"},
    {"first": "Holden", "last": "❌", "email": "holdenfox2127@gmail.com", "pass": "Hold#Fox6699", "year": "2000"},
    {"first": "Ivy", "last": "❌", "email": "ivyriley2128@gmail.com", "pass": "Ivy!Rile7711", "year": "2000"},
    {"first": "Jonah", "last": "❌", "email": "jonahschmidt2129@gmail.com", "pass": "Jona#Schm8822", "year": "2000"},
    {"first": "Kira", "last": "❌", "email": "kiraolson2130@gmail.com", "pass": "Kira!Olso9933", "year": "2000"},
    {"first": "Liam", "last": "❌", "email": "liamharvey2131@gmail.com", "pass": "Liam#Harv1144", "year": "2000"},
    {"first": "Mila", "last": "❌", "email": "milapatterson2132@gmail.com", "pass": "Mila!Patt2255", "year": "2000"},
    {"first": "Orion", "last": "❌", "email": "orionmedina2133@gmail.com", "pass": "Orio#Medi3366", "year": "2000"},
    {"first": "Piper", "last": "❌", "email": "piperfowler2134@gmail.com", "pass": "Pipe!Fowl4477", "year": "2000"},
    {"first": "Quentin", "last": "❌", "email": "quentinbrewer2135@gmail.com", "pass": "Quen#Brew5588", "year": "2000"},
    {"first": "Reese", "last": "❌", "email": "reesehoffman2136@gmail.com", "pass": "Rees!Hoff6699", "year": "2000"},
    {"first": "Skylar", "last": "❌", "email": "skylarcarlson2137@gmail.com", "pass": "Skyl#Carl7711", "year": "2000"},
    {"first": "Tatum", "last": "❌", "email": "tatumsilva2138@gmail.com", "pass": "Tatu!Silv8822", "year": "2000"},
    {"first": "Uri", "last": "❌", "email": "uripearson2139@gmail.com", "pass": "Uri#Pear9933", "year": "2000"},
    {"first": "Valerie", "last": "❌", "email": "valeriemedeiros2140@gmail.com", "pass": "Vale!Medi1144", "year": "2000"},
    {"first": "Wade", "last": "❌", "email": "wademckinney2141@gmail.com", "pass": "Wade#McKi2255", "year": "2000"},
    {"first": "Xia", "last": "❌", "email": "xialucas2142@gmail.com", "pass": "Xia!Luca3366", "year": "2000"},
    {"first": "Yusuf", "last": "❌", "email": "yusufjohnson2143@gmail.com", "pass": "Yusu#John4477", "year": "2000"},
    {"first": "Zelda", "last": "❌", "email": "zeldasmith2144@gmail.com", "pass": "Zeld!Smit5588", "year": "2000"},
    {"first": "Abel", "last": "❌", "email": "abelwilliams2145@gmail.com", "pass": "Abel#Will6699", "year": "2000"},
    {"first": "Bridget", "last": "❌", "email": "bridgetbrown2146@gmail.com", "pass": "Brid!Brow7711", "year": "2000"},
    {"first": "Cyrus", "last": "❌", "email": "cyrusjones2147@gmail.com", "pass": "Cyru#Jone8822", "year": "2000"},
    {"first": "Daphne", "last": "❌", "email": "daphnegarcia2148@gmail.com", "pass": "Daph!Garc9933", "year": "2000"},
    {"first": "Ezekiel", "last": "❌", "email": "ezekielmiller2149@gmail.com", "pass": "Ezek#Mill1144", "year": "2000"},
    {"first": "Freya", "last": "❌", "email": "freyadavis2150@gmail.com", "pass": "Frey!Davi2255", "year": "2000"},
    {"first": "Gideon", "last": "❌", "email": "gideonrodriguez2151@gmail.com", "pass": "Gide#Rodr3366", "year": "2000"},
    {"first": "Hadley", "last": "❌", "email": "hadleymartinez2152@gmail.com", "pass": "Hadl!Mart4477", "year": "2000"},
    {"first": "Ignacio", "last": "❌", "email": "ignaciohernandez2153@gmail.com", "pass": "Igna#Hern5588", "year": "2000"},
    {"first": "Jocelyn", "last": "❌", "email": "jocelynlopez2154@gmail.com", "pass": "Joce!Lope6699", "year": "2000"},
    {"first": "Kian", "last": "❌", "email": "kiangonzalez2155@gmail.com", "pass": "Kian#Gonz7711", "year": "2000"},
    {"first": "Lana", "last": "❌", "email": "lanawilson2156@gmail.com", "pass": "Lana!Wils8822", "year": "2000"},
    {"first": "Milo", "last": "❌", "email": "miloanderson2157@gmail.com", "pass": "Milo#Ande9933", "year": "2000"},
    {"first": "Noelle", "last": "❌", "email": "noellethomas2158@gmail.com", "pass": "Noel!Thom1144", "year": "2000"},
    {"first": "Orson", "last": "❌", "email": "orsontaylor2159@gmail.com", "pass": "Orso#Tayl2255", "year": "2000"},
    {"first": "Paloma", "last": "❌", "email": "palomamoore2160@gmail.com", "pass": "Palo!Moor3366", "year": "2000"},
    {"first": "Quincy", "last": "❌", "email": "quincyjackson2161@gmail.com", "pass": "Quin#Jack4477", "year": "2000"},
    {"first": "Ramon", "last": "❌", "email": "ramonmartin2162@gmail.com", "pass": "Ramo!Mart5588", "year": "2000"},
    {"first": "Selma", "last": "❌", "email": "selmalee2163@gmail.com", "pass": "Selm#Lee6699", "year": "2000"},
    {"first": "Thaddeus", "last": "❌", "email": "thaddeusperez2164@gmail.com", "pass": "Thad!Perez7711", "year": "2000"},
    {"first": "Ulric", "last": "❌", "email": "ulricthompson2165@gmail.com", "pass": "Ulri#Thom8822", "year": "2000"},
    {"first": "Veda", "last": "❌", "email": "vedawhite2166@gmail.com", "pass": "Veda!Whit9933", "year": "2000"},
    {"first": "Winston", "last": "❌", "email": "winstonharris2167@gmail.com", "pass": "Wins#Harr1144", "year": "2000"},
    {"first": "Xens", "last": "❌", "email": "xensclark2168@gmail.com", "pass": "Xens!Clar2255", "year": "2000"},
    {"first": "Yara", "last": "❌", "email": "yaralewis2169@gmail.com", "pass": "Yara#Lewi3366", "year": "2000"},
    {"first": "Zephyr", "last": "❌", "email": "zephyrrobinson2170@gmail.com", "pass": "Zeph!Robi4477", "year": "2000"},
    {"first": "Althea", "last": "❌", "email": "altheawalker2171@gmail.com", "pass": "Alth#Walk5588", "year": "2000"},
    {"first": "Bane", "last": "❌", "email": "baneyoung2172@gmail.com", "pass": "Bane!Youn6699", "year": "2000"},
    {"first": "Calista", "last": "❌", "email": "calistaking2173@gmail.com", "pass": "Cali#King7711", "year": "2000"},
    {"first": "Darius", "last": "❌", "email": "dariuswright2174@gmail.com", "pass": "Dari!Wrig8822", "year": "2000"},
    {"first": "Ember", "last": "❌", "email": "emberscott2175@gmail.com", "pass": "Embe#Scot9933", "year": "2000"},
    {"first": "Falcon", "last": "❌", "email": "falcongreen2176@gmail.com", "pass": "Falc!Gree1144", "year": "2000"},
    {"first": "Gwen", "last": "❌", "email": "gwenbaker2177@gmail.com", "pass": "Gwen#Bake2255", "year": "2000"},
    {"first": "Hakeem", "last": "❌", "email": "hakeemadams2178@gmail.com", "pass": "Hake!Adam3366", "year": "2000"},
    {"first": "Iliana", "last": "❌", "email": "iliananelson2179@gmail.com", "pass": "Ilia#Nels4477", "year": "2000"},
    {"first": "Jagger", "last": "❌", "email": "jaggerhill2180@gmail.com", "pass": "Jagg!Hill5588", "year": "2000"},
    {"first": "Kenna", "last": "❌", "email": "kennaramirez2181@gmail.com", "pass": "Kenn#Rami6699", "year": "2000"},
    {"first": "Laker", "last": "❌", "email": "lakercampbell2182@gmail.com", "pass": "Lake!Camp7711", "year": "2000"},
    {"first": "Maris", "last": "❌", "email": "marismitchell2183@gmail.com", "pass": "Mari#Mitt8822", "year": "2000"},
    {"first": "Neriah", "last": "❌", "email": "neriahroberts2184@gmail.com", "pass": "Neri!Robe9933", "year": "2000"},
    {"first": "Otis", "last": "❌", "email": "otiscarter2185@gmail.com", "pass": "Otis#Cart1144", "year": "2000"},
    {"first": "Pia", "last": "❌", "email": "piaphillips2186@gmail.com", "pass": "Pia!Phil2255", "year": "2000"},
    {"first": "Qasim", "last": "❌", "email": "qasimevans2187@gmail.com", "pass": "Qasi#Evan3366", "year": "2000"},
    {"first": "Rory", "last": "❌", "email": "roryturner2188@gmail.com", "pass": "Rory!Turn4477", "year": "2000"},
    {"first": "Sari", "last": "❌", "email": "saritorres2189@gmail.com", "pass": "Sari#Torr5588", "year": "2000"},
    {"first": "Talon", "last": "❌", "email": "talonparker2190@gmail.com", "pass": "Talo!Park6699", "year": "2000"},
    {"first": "Uziah", "last": "❌", "email": "uziahcollins2191@gmail.com", "pass": "Uzia#Coll7711", "year": "2000"},
    {"first": "Veda", "last": "❌", "email": "vedastewart2192@gmail.com", "pass": "Veda!Stew8822", "year": "2000"},
    {"first": "Waldo", "last": "❌", "email": "waldomorris2193@gmail.com", "pass": "Wald#Morr9933", "year": "2000"},
    {"first": "Xena", "last": "❌", "email": "xenarogers2194@gmail.com", "pass": "Xena!Roge1144", "year": "2000"},
    {"first": "Yaro", "last": "❌", "email": "yaroreed2195@gmail.com", "pass": "Yaro#Reed2255", "year": "2000"},
    {"first": "Zita", "last": "❌", "email": "zitacook2196@gmail.com", "pass": "Zita!Cook3366", "year": "2000"},
    {"first": "Alistair", "last": "❌", "email": "alistairmorgan2197@gmail.com", "pass": "Alis#Morg4477", "year": "2000"},
    {"first": "Bria", "last": "❌", "email": "briabell2198@gmail.com", "pass": "Bria!Bell5588", "year": "2000"},
    {"first": "Cai", "last": "❌", "email": "caimurphy2199@gmail.com", "pass": "Cai#Murp6699", "year": "2000"},
    {"first": "Dara", "last": "❌", "email": "darabailey2200@gmail.com", "pass": "Dara!Bail7711", "year": "2000"},
    {"first": "Ezra", "last": "❌", "email": "ezrabrooks2201@gmail.com", "pass": "Ezra#Broo9933", "year": "2000"},
    {"first": "Faye", "last": "❌", "email": "fayecooper2202@gmail.com", "pass": "Faye!Coop1144", "year": "2000"},
    {"first": "Gage", "last": "❌", "email": "gageward2203@gmail.com", "pass": "Gage#Ward2255", "year": "2000"},
    {"first": "Hana", "last": "❌", "email": "hanapeterson2204@gmail.com", "pass": "Hana!Pete3366", "year": "2000"},
    {"first": "Idris", "last": "❌", "email": "idrisreed2205@gmail.com", "pass": "Idri#Reed4477", "year": "2000"},
    {"first": "Jada", "last": "❌", "email": "jadakelly2206@gmail.com", "pass": "Jada!Kell5588", "year": "2000"},
    {"first": "Kade", "last": "❌", "email": "kadehoward2207@gmail.com", "pass": "Kade#Howa6699", "year": "2000"},
    {"first": "Lyla", "last": "❌", "email": "lylaramos2208@gmail.com", "pass": "Lyla!Ramo7711", "year": "2000"},
    {"first": "Mads", "last": "❌", "email": "madskim2209@gmail.com", "pass": "Mads#Kim8822", "year": "2000"},
    {"first": "Noa", "last": "❌", "email": "noacox2210@gmail.com", "pass": "Noa!Cox9933", "year": "2000"},
    {"first": "Paz", "last": "❌", "email": "pazward2211@gmail.com", "pass": "Paz#Ward1144", "year": "2000"},
    {"first": "Remy", "last": "❌", "email": "remyrichardson2212@gmail.com", "pass": "Remy!Rich2255", "year": "2000"},
    {"first": "Sage", "last": "❌", "email": "sagewatson2213@gmail.com", "pass": "Sage#Wats3366", "year": "2000"},
    {"first": "Tate", "last": "❌", "email": "tatebrooks2214@gmail.com", "pass": "Tate!Broo4477", "year": "2000"},
    {"first": "Vail", "last": "❌", "email": "vailsanders2215@gmail.com", "pass": "Vail#Sand5588", "year": "2000"},
    {"first": "Wren", "last": "❌", "email": "wrenprice2216@gmail.com", "pass": "Wren!Pric6699", "year": "2000"},
    {"first": "Zev", "last": "❌", "email": "zevbennett2217@gmail.com", "pass": "Zev#Benn7711", "year": "2000"},
    {"first": "Axel", "last": "❌", "email": "axelwood2218@gmail.com", "pass": "Axel!Wood8822", "year": "2000"},
    {"first": "Bess", "last": "❌", "email": "bessbarnes2219@gmail.com", "pass": "Bess#Barn9933", "year": "2000"},
    {"first": "Cain", "last": "❌", "email": "cainross2220@gmail.com", "pass": "Cain!Ross1144", "year": "2000"},
    {"first": "David", "last": "❌", "email": "davidmiller2221@gmail.com", "pass": "Davi!Mill5566", "year": "2000"},
    {"first": "Emma", "last": "❌", "email": "emmawilson2222@gmail.com", "pass": "Emma#Wils7788", "year": "2000"},
    {"first": "Frank", "last": "❌", "email": "frankmoore2223@gmail.com", "pass": "Fran!Moor9900", "year": "2000"},
    {"first": "Gina", "last": "❌", "email": "ginataylor2224@gmail.com", "pass": "Gina#Tayl1122", "year": "2000"},
    {"first": "Harry", "last": "❌", "email": "harryanderson2225@gmail.com", "pass": "Harr!Ande3344", "year": "2000"},
    {"first": "Ivy", "last": "❌", "email": "ivythomas2226@gmail.com", "pass": "Ivy#Thom5566", "year": "2000"},
    {"first": "John", "last": "❌", "email": "johnjackson2227@gmail.com", "pass": "John!Jack7788", "year": "2000"},
    {"first": "Kelly", "last": "❌", "email": "kellywhite2228@gmail.com", "pass": "Kell#Whit9900", "year": "2000"},
    {"first": "Luke", "last": "❌", "email": "lukeharris2229@gmail.com", "pass": "Luke!Harr1122", "year": "2000"},
    {"first": "Mary", "last": "❌", "email": "marymartin2230@gmail.com", "pass": "Mary#Mart3344", "year": "2000"},
    {"first": "Nick", "last": "❌", "email": "nickthompson2231@gmail.com", "pass": "Nick!Thom5566", "year": "2000"},
    {"first": "Olga", "last": "❌", "email": "olgagarcia2232@gmail.com", "pass": "Olga#Garc7788", "year": "2000"},
    {"first": "Paul", "last": "❌", "email": "paulmartinez2233@gmail.com", "pass": "Paul!Mart9900", "year": "2000"},
    {"first": "Rose", "last": "❌", "email": "roserobinson2234@gmail.com", "pass": "Rose#Robi1122", "year": "2000"},
    {"first": "Sean", "last": "❌", "email": "seanclark2235@gmail.com", "pass": "Sean!Clar3344", "year": "2000"},
    {"first": "Tina", "last": "❌", "email": "tinaferguson2236@gmail.com", "pass": "Tina#Ferg5566", "year": "2000"},
    {"first": "Vince", "last": "❌", "email": "vincetyler2237@gmail.com", "pass": "Vinc!Tyle7788", "year": "2000"},
    {"first": "Wanda", "last": "❌", "email": "wandasoto2238@gmail.com", "pass": "Wand#Soto9900", "year": "2000"},
    {"first": "Yuri", "last": "❌", "email": "yurikyung2239@gmail.com", "pass": "Yuri!Kyun1122", "year": "2000"},
    {"first": "Zoe", "last": "❌", "email": "zoezhang2240@gmail.com", "pass": "Zoe#Zhan3344", "year": "2000"},
    {"first": "Zoya", "last": "❌", "email": "zoyazhang2241@gmail.com", "pass": "Zoya#Zhan5566", "year": "2000"},
    {"first": "Ali", "last": "❌", "email": "aliabbasi2242@gmail.com", "pass": "Ali!Abba7788", "year": "2000"},
    {"first": "Bano", "last": "❌", "email": "banokhan2243@gmail.com", "pass": "Bano#Khan9900", "year": "2000"},
    {"first": "Cen", "last": "❌", "email": "cenwang2244@gmail.com", "pass": "Cen!Wang1122", "year": "2000"},
    {"first": "Dina", "last": "❌", "email": "dinapatel2245@gmail.com", "pass": "Dina#Pate3344", "year": "2000"},
    {"first": "Erol", "last": "❌", "email": "erolyilmaz2246@gmail.com", "pass": "Erol!Yilm5566", "year": "2000"},
    {"first": "Farah", "last": "❌", "email": "farahkhan2247@gmail.com", "pass": "Fara#Khan7788", "year": "2000"},
    {"first": "Gani", "last": "❌", "email": "ganidemir2248@gmail.com", "pass": "Gani!Demi9900", "year": "2000"},
    {"first": "Hale", "last": "❌", "email": "haleyildiz2249@gmail.com", "pass": "Hale#Yild1122", "year": "2000"},
    {"first": "Irem", "last": "❌", "email": "iremsahin2250@gmail.com", "pass": "Irem!Sahi3344", "year": "2000"},
    {"first": "Jan", "last": "❌", "email": "jancolak2251@gmail.com", "pass": "Jan#Cola5566", "year": "2000"},
    {"first": "Kaan", "last": "❌", "email": "kaanaydin2252@gmail.com", "pass": "Kaan!Aydi7788", "year": "2000"},
    {"first": "Lale", "last": "❌", "email": "lalecetin2253@gmail.com", "pass": "Lale#Ceti9900", "year": "2000"},
    {"first": "Mert", "last": "❌", "email": "mertarslan2254@gmail.com", "pass": "Mert!Arsl1122", "year": "2000"},
    {"first": "Nihal", "last": "❌", "email": "nihalyilmaz2255@gmail.com", "pass": "Niha#Yilm3344", "year": "2000"},
    {"first": "Ozan", "last": "❌", "email": "ozankaya2256@gmail.com", "pass": "Ozan!Kaya5566", "year": "2000"},
    {"first": "Pelin", "last": "❌", "email": "pelindemir2257@gmail.com", "pass": "Peli#Demi7788", "year": "2000"},
    {"first": "Ruzgar", "last": "❌", "email": "ruzgarcelik2258@gmail.com", "pass": "Ruzg!Celi9900", "year": "2000"},
    {"first": "Selin", "last": "❌", "email": "selindemir2259@gmail.com", "pass": "Seli#Demi1122", "year": "2000"},
    {"first": "Tarik", "last": "❌", "email": "tarikaydin2260@gmail.com", "pass": "Tari!Aydi3344", "year": "2000"},
    {"first": "Utku", "last": "❌", "email": "utkucetin2261@gmail.com", "pass": "Utku#Ceti5566", "year": "2000"},
    {"first": "Volkan", "last": "❌", "email": "volkanarslan2262@gmail.com", "pass": "Volk!Arsl7788", "year": "2000"},
    {"first": "Yigit", "last": "❌", "email": "yigitkorkmaz2263@gmail.com", "pass": "Yigi#Kork9900", "year": "2000"},
    {"first": "Zehra", "last": "❌", "email": "zehrakaya2264@gmail.com", "pass": "Zehr!Kaya1122", "year": "2000"},
    {"first": "Ayla", "last": "❌", "email": "aylacelik2265@gmail.com", "pass": "Ayla#Celi3344", "year": "2000"},
    {"first": "Bora", "last": "❌", "email": "borademir2266@gmail.com", "pass": "Bora!Demi5566", "year": "2000"},
    {"first": "Cem", "last": "❌", "email": "cemyilmaz2267@gmail.com", "pass": "Cem#Yilm7788", "year": "2000"},
    {"first": "Defne", "last": "❌", "email": "defnesahin2268@gmail.com", "pass": "Defn!Sahi9900", "year": "2000"},
    {"first": "Ece", "last": "❌", "email": "eceaydin2269@gmail.com", "pass": "Ece#Aydi1122", "year": "2000"},
    {"first": "Firat", "last": "❌", "email": "firatsen2270@gmail.com", "pass": "Fira!Sen3344", "year": "2000"},
    {"first": "Gizem", "last": "❌", "email": "gizemkoc2271@gmail.com", "pass": "Gize#Koc5566", "year": "2000"},
    {"first": "Hakan", "last": "❌", "email": "hakanyildiz2272@gmail.com", "pass": "Haka!Yild7788", "year": "2000"},
    {"first": "Ipek", "last": "❌", "email": "ipekpolat2273@gmail.com", "pass": "Ipek#Pola9900", "year": "2000"},
    {"first": "Kaan", "last": "❌", "email": "kaandogan2274@gmail.com", "pass": "Kaan!Doga1122", "year": "2000"},
    {"first": "Leyla", "last": "❌", "email": "leylacelik2275@gmail.com", "pass": "Leyl#Celi3344", "year": "2000"},
    {"first": "Melis", "last": "❌", "email": "melisarslan2276@gmail.com", "pass": "Meli!Arsl5566", "year": "2000"},
    {"first": "Nil", "last": "❌", "email": "nilkara2277@gmail.com", "pass": "Nil#Kara7788", "year": "2000"},
    {"first": "Onur", "last": "❌", "email": "onurtoprak2278@gmail.com", "pass": "Onur!Topr9900", "year": "2000"},
    {"first": "Pinar", "last": "❌", "email": "pinarbulut2279@gmail.com", "pass": "Pina#Bulu1122", "year": "2000"},
    {"first": "Rengin", "last": "❌", "email": "renginsuer2280@gmail.com", "pass": "Reng!Suer3344", "year": "2000"},
    {"first": "Sinan", "last": "❌", "email": "sinanyilmaz2281@gmail.com", "pass": "Sina#Yilm5566", "year": "2000"},
    {"first": "Tugba", "last": "❌", "email": "tugbasahin2282@gmail.com", "pass": "Tugb!Sahi7788", "year": "2000"},
    {"first": "Umut", "last": "❌", "email": "umutaydin2283@gmail.com", "pass": "Umut!Aydi9900", "year": "2000"},
    {"first": "Yagmur", "last": "❌", "email": "yagmursen2284@gmail.com", "pass": "Yagm#Sen1122", "year": "2000"},
    {"first": "Zafer", "last": "❌", "email": "zaferkoc2285@gmail.com", "pass": "Zafe!Koc3344", "year": "2000"},
    {"first": "Asli", "last": "❌", "email": "asliaksoy2286@gmail.com", "pass": "Asli#Akso5566", "year": "2000"},
    {"first": "Berk", "last": "❌", "email": "berkpolat2287@gmail.com", "pass": "Berk!Pola7788", "year": "2000"},
    {"first": "Ceren", "last": "❌", "email": "cerendogan2288@gmail.com", "pass": "Cere#Doga9900", "year": "2000"},
    {"first": "Deniz", "last": "❌", "email": "denizcelik2289@gmail.com", "pass": "Deni!Celi1122", "year": "2000"},
    {"first": "Emre", "last": "❌", "email": "emrearslan2290@gmail.com", "pass": "Emre#Arsl3344", "year": "2000"},
    {"first": "Filiz", "last": "❌", "email": "filizkara2291@gmail.com", "pass": "Fili!Kara5566", "year": "2000"},
    {"first": "Gorkem", "last": "❌", "email": "gorkemtoprak2292@gmail.com", "pass": "Gork#Topr7788", "year": "2000"},
    {"first": "Hande", "last": "❌", "email": "handebulut2293@gmail.com", "pass": "Hand!Bulu9900", "year": "2000"},
    {"first": "Ilker", "last": "❌", "email": "ilkersuer2294@gmail.com", "pass": "Ilke#Suer1122", "year": "2000"},
    {"first": "Kivanc", "last": "❌", "email": "kivancyilmaz2295@gmail.com", "pass": "Kiva!Yilm3344", "year": "2000"},
    {"first": "Melike", "last": "❌", "email": "melikesahin2296@gmail.com", "pass": "Meli#Sahi5566", "year": "2000"},
    {"first": "Nehir", "last": "❌", "email": "nehiraydin2297@gmail.com", "pass": "Nehi!Aydi7788", "year": "2000"},
    {"first": "Oguz", "last": "❌", "email": "oguzsen2298@gmail.com", "pass": "Oguz#Sen9900", "year": "2000"},
    {"first": "Pelin", "last": "❌", "email": "pelinkoc2299@gmail.com", "pass": "Peli!Koc1122", "year": "2000"},
    {"first": "Sarp", "last": "❌", "email": "sarpaksoy2300@gmail.com", "pass": "Sarp#Akso3344", "year": "2000"},
    {"first": "Tolgay", "last": "❌", "email": "tolgaypolat2301@gmail.com", "pass": "Tolg!Pola5566", "year": "2000"},
    {"first": "Ugur", "last": "❌", "email": "ugurdogan2302@gmail.com", "pass": "Ugur#Doga7788", "year": "2000"},
    {"first": "Yasin", "last": "❌", "email": "yasincelik2303@gmail.com", "pass": "Yasi!Celi9900", "year": "2000"},
    {"first": "Zeynep", "last": "❌", "email": "zeyneparslan2304@gmail.com", "pass": "Zeyn#Arsl1122", "year": "2000"},
    {"first": "Arda", "last": "❌", "email": "ardakara2305@gmail.com", "pass": "Arda!Kara3344", "year": "2000"},
    {"first": "Burak", "last": "❌", "email": "buraktoprak2306@gmail.com", "pass": "Bura#Topr5566", "year": "2000"},
    {"first": "Cagla", "last": "❌", "email": "caglabulut2307@gmail.com", "pass": "Cagl!Bulu7788", "year": "2000"},
    {"first": "Demet", "last": "❌", "email": "demetsuer2308@gmail.com", "pass": "Deme#Suer9900", "year": "2000"},
    {"first": "Erdem", "last": "❌", "email": "erdemyilmaz2309@gmail.com", "pass": "Erde!Yilm1122", "year": "2000"},
    {"first": "Funda", "last": "❌", "email": "fundasahin2310@gmail.com", "pass": "Fund#Sahi3344", "year": "2000"},
    {"first": "Gokhan", "last": "❌", "email": "gokhanaydin2311@gmail.com", "pass": "Gokh!Aydi5566", "year": "2000"},
    {"first": "Harun", "last": "❌", "email": "harunsen2312@gmail.com", "pass": "Haru#Sen7788", "year": "2000"},
    {"first": "Ismail", "last": "❌", "email": "ismailkoc2313@gmail.com", "pass": "Isma!Koc9900", "year": "2000"},
    {"first": "Kadir", "last": "❌", "email": "kadriaksoy2314@gmail.com", "pass": "Kadi#Akso1122", "year": "2000"},
    {"first": "Levent", "last": "❌", "email": "leventpolat2315@gmail.com", "pass": "Leve!Pola3344", "year": "2000"},
    {"first": "Meltem", "last": "❌", "email": "meltemdogan2316@gmail.com", "pass": "Melt#Doga5566", "year": "2000"},
    {"first": "Nuri", "last": "❌", "email": "nuricelik2317@gmail.com", "pass": "Nuri!Celi7788", "year": "2000"},
    {"first": "Orhan", "last": "❌", "email": "orhanarslan2318@gmail.com", "pass": "Orha#Arsl9900", "year": "2000"},
    {"first": "Polat", "last": "❌", "email": "polatkara2319@gmail.com", "pass": "Pola!Kara1122", "year": "2000"},
    {"first": "Rabia", "last": "❌", "email": "rabiatoprak2320@gmail.com", "pass": "Rabi#Topr3344", "year": "2000"},
    {"first": "Serkan", "last": "❌", "email": "serkanbulut2321@gmail.com", "pass": "Serk!Bulu5566", "year": "2000"},
    {"first": "Tuba", "last": "❌", "email": "tubasuer2322@gmail.com", "pass": "Tuba#Suer7788", "year": "2000"},
    {"first": "Ufuk", "last": "❌", "email": "ufukyilmaz2323@gmail.com", "pass": "Ufuk!Yilm9900", "year": "2000"},
    {"first": "Yavuz", "last": "❌", "email": "yavuzsahin2324@gmail.com", "pass": "Yavu#Sahi1122", "year": "2000"},
    {"first": "Ziya", "last": "❌", "email": "ziyaaydin2325@gmail.com", "pass": "Ziya!Aydi3344", "year": "2000"},
    {"first": "Ahmet", "last": "❌", "email": "ahmetsen2326@gmail.com", "pass": "Ahme#Sen5566", "year": "2000"},
    {"first": "Banu", "last": "❌", "email": "banukoc2327@gmail.com", "pass": "Banu!Koc7788", "year": "2000"},
    {"first": "Can", "last": "❌", "email": "canaksoy2328@gmail.com", "pass": "Can#Akso9900", "year": "2000"},
    {"first": "Derya", "last": "❌", "email": "deryapolat2329@gmail.com", "pass": "Dery!Pola1122", "year": "2000"},
    {"first": "Enes", "last": "❌", "email": "enesdogan2330@gmail.com", "pass": "Enes!Doga3344", "year": "2000"},
    {"first": "Fatma", "last": "❌", "email": "fatmacelik2331@gmail.com", "pass": "Fatm#Celi5566", "year": "2000"},
    {"first": "Gulay", "last": "❌", "email": "gulayarslan2332@gmail.com", "pass": "Gula!Arsl7788", "year": "2000"},
    {"first": "Hasan", "last": "❌", "email": "hasankara2333@gmail.com", "pass": "Hasa#Kara9900", "year": "2000"},
    {"first": "Ilkay", "last": "❌", "email": "ilkaytoprak2334@gmail.com", "pass": "Ilka!Topr1122", "year": "2000"},
    {"first": "Kaan", "last": "❌", "email": "kaanbulut2335@gmail.com", "pass": "Kaan#Bulu3344", "year": "2000"},
    {"first": "Lale", "last": "❌", "email": "lalesuer2336@gmail.com", "pass": "Lale!Suer5566", "year": "2000"},
    {"first": "Merve", "last": "❌", "email": "merveyilmaz2337@gmail.com", "pass": "Merv#Yilm7788", "year": "2000"},
    {"first": "Nalan", "last": "❌", "email": "nalansahin2338@gmail.com", "pass": "Nala!Sahi9900", "year": "2000"},
    {"first": "Omer", "last": "❌", "email": "omeraydin2339@gmail.com", "pass": "Omer#Aydi1122", "year": "2000"},
    {"first": "Pinar", "last": "❌", "email": "pinarsen2340@gmail.com", "pass": "Pina!Sen3344", "year": "2000"},
    {"first": "Recep", "last": "❌", "email": "recepkoc2341@gmail.com", "pass": "Rece#Koc5566", "year": "2000"},
    {"first": "Seda", "last": "❌", "email": "sedaaksoy2342@gmail.com", "pass": "Seda!Akso7788", "year": "2000"},
    {"first": "Tamer", "last": "❌", "email": "tamerpolat2343@gmail.com", "pass": "Tame#Pola9900", "year": "2000"},
    {"first": "Ufuk", "last": "❌", "email": "ufukdogan2344@gmail.com", "pass": "Ufuk!Doga1122", "year": "2000"},
    {"first": "Yusuf", "last": "❌", "email": "yusufcelik2345@gmail.com", "pass": "Yusu#Celi3344", "year": "2000"},
    {"first": "Zeki", "last": "❌", "email": "zekiarslan2346@gmail.com", "pass": "Zeki!Arsl5566", "year": "2000"},
    {"first": "Ali", "last": "❌", "email": "alikara2347@gmail.com", "pass": "Ali#Kara7788", "year": "2000"},
    {"first": "Buse", "last": "❌", "email": "busetoprak2348@gmail.com", "pass": "Buse!Topr9900", "year": "2000"},
    {"first": "Cenk", "last": "❌", "email": "cenkbulut2349@gmail.com", "pass": "Cenk#Bulu1122", "year": "2000"},
    {"first": "Dilek", "last": "❌", "email": "dileksuer2350@gmail.com", "pass": "Dile!Suer3344", "year": "2000"},
    {"first": "Ebru", "last": "❌", "email": "ebruyilmaz2351@gmail.com", "pass": "Ebru#Yilm5566", "year": "2000"},
    {"first": "Faruk", "last": "❌", "email": "faruksahin2352@gmail.com", "pass": "Faru!Sahi7788", "year": "2000"},
    {"first": "Gizem", "last": "❌", "email": "gizemaydin2353@gmail.com", "pass": "Gize#Aydi9900", "year": "2000"},
    {"first": "Hulya", "last": "❌", "email": "hulyasen2354@gmail.com", "pass": "Huly!Sen1122", "year": "2000"},
    {"first": "Ibrahim", "last": "❌", "email": "ibrahimkoc2355@gmail.com", "pass": "Ibra#Koc3344", "year": "2000"},
    {"first": "Kamil", "last": "❌", "email": "kamilaksoy2356@gmail.com", "pass": "Kami!Akso5566", "year": "2000"},
    {"first": "Leman", "last": "❌", "email": "lemanpolat2357@gmail.com", "pass": "Lema#Pola7788", "year": "2000"},
    {"first": "Metin", "last": "❌", "email": "metindogan2358@gmail.com", "pass": "Meti!Doga9900", "year": "2000"},
    {"first": "Nazli", "last": "❌", "email": "nazlicelik2359@gmail.com", "pass": "Nazl#Celi1122", "year": "2000"},
    {"first": "Okan", "last": "❌", "email": "okanarslan2360@gmail.com", "pass": "Okan!Arsl3344", "year": "2000"},
    {"first": "Pelin", "last": "❌", "email": "pelinkara2361@gmail.com", "pass": "Peli#Kara5566", "year": "2000"},
    {"first": "Riza", "last": "❌", "email": "rizatoprak2362@gmail.com", "pass": "Riza!Topr7788", "year": "2000"},
    {"first": "Selim", "last": "❌", "email": "selimbulut2363@gmail.com", "pass": "Seli#Bulu9900", "year": "2000"},
    {"first": "Tunc", "last": "❌", "email": "tuncsuer2364@gmail.com", "pass": "Tunc!Suer1122", "year": "2000"},
    {"first": "Umran", "last": "❌", "email": "umranyilmaz2365@gmail.com", "pass": "Umra#Yilm3344", "year": "2000"},
    {"first": "Yilmaz", "last": "❌", "email": "yilmazsahin2366@gmail.com", "pass": "Yilm!Sahi5566", "year": "2000"},
    {"first": "Zuhal", "last": "❌", "email": "zuhalaydin2367@gmail.com", "pass": "Zuha#Aydi7788", "year": "2000"},
    {"first": "Adem", "last": "❌", "email": "ademsen2368@gmail.com", "pass": "Adem!Sen9900", "year": "2000"},
    {"first": "Bahar", "last": "❌", "email": "baharkoc2369@gmail.com", "pass": "Baha#Koc1122", "year": "2000"},
    {"first": "Cemil", "last": "❌", "email": "cemilaksoy2370@gmail.com", "pass": "Cemi!Akso3344", "year": "2000"},
    {"first": "Duygu", "last": "❌", "email": "duygupolat2371@gmail.com", "pass": "Duyg#Pola5566", "year": "2000"},
    {"first": "Erkan", "last": "❌", "email": "erkandogan2372@gmail.com", "pass": "Erka!Doga7788", "year": "2000"},
    {"first": "Ferit", "last": "❌", "email": "feritcelik2373@gmail.com", "pass": "Feri#Celi9900", "year": "2000"},
    {"first": "Gonul", "last": "❌", "email": "gonularslan2374@gmail.com", "pass": "Gonu!Arsl1122", "year": "2000"},
    {"first": "Halil", "last": "❌", "email": "halilkara2375@gmail.com", "pass": "Hali#Kara3344", "year": "2000"},
    {"first": "Irfan", "last": "❌", "email": "irfantoprak2376@gmail.com", "pass": "Irfa!Topr5566", "year": "2000"},
    {"first": "Kemal", "last": "❌", "email": "kemalbulut2377@gmail.com", "pass": "Kema#Bulu7788", "year": "2000"},
    {"first": "Leyla", "last": "❌", "email": "leylasuer2378@gmail.com", "pass": "Leyl!Suer9900", "year": "2000"},
    {"first": "Mesut", "last": "❌", "email": "mesutyilmaz2379@gmail.com", "pass": "Mesu#Yilm1122", "year": "2000"},
    {"first": "Niyazi", "last": "❌", "email": "niyazisahin2380@gmail.com", "pass": "Niya!Sahi3344", "year": "2000"},
    {"first": "Orhan", "last": "❌", "email": "orhanaydin2381@gmail.com", "pass": "Orha#Aydi5566", "year": "2000"},
    {"first": "Polat", "last": "❌", "email": "polatsen2382@gmail.com", "pass": "Pola!Sen7788", "year": "2000"},
    {"first": "Rustem", "last": "❌", "email": "rustemkoc2383@gmail.com", "pass": "Rust#Koc9900", "year": "2000"},
    {"first": "Serap", "last": "❌", "email": "serapaksoy2384@gmail.com", "pass": "Sera!Akso1122", "year": "2000"},
    {"first": "Tarik", "last": "❌", "email": "tarikpolat2385@gmail.com", "pass": "Tari#Pola3344", "year": "2000"},
    {"first": "Ulku", "last": "❌", "email": "ulkudogan2386@gmail.com", "pass": "Ulku!Doga5566", "year": "2000"},
    {"first": "Yener", "last": "❌", "email": "yenercelik2387@gmail.com", "pass": "Yene#Celi7788", "year": "2000"},
    {"first": "Zafer", "last": "❌", "email": "zaferarslan2388@gmail.com", "pass": "Zafe!Arsl9900", "year": "2000"},
    {"first": "Asli", "last": "❌", "email": "aslikara2389@gmail.com", "pass": "Asli#Kara1122", "year": "2000"},
    {"first": "Burcu", "last": "❌", "email": "burcutoprak2390@gmail.com", "pass": "Burc!Topr3344", "year": "2000"},
    {"first": "Cemre", "last": "❌", "email": "cemrebulut2391@gmail.com", "pass": "Cemr#Bulu5566", "year": "2000"},
    {"first": "Duygu", "last": "❌", "email": "duygusuer2392@gmail.com", "pass": "Duyg!Suer7788", "year": "2000"},
    {"first": "Emine", "last": "❌", "email": "emineyilmaz2393@gmail.com", "pass": "Emin#Yilm9900", "year": "2000"},
    {"first": "Figen", "last": "❌", "email": "figensahin2394@gmail.com", "pass": "Fige!Sahi1122", "year": "2000"},
    {"first": "Gul", "last": "❌", "email": "gulaydin2395@gmail.com", "pass": "Gul#Aydi3344", "year": "2000"},
    {"first": "Hacer", "last": "❌", "email": "hacersen2396@gmail.com", "pass": "Hace!Sen5566", "year": "2000"},
    {"first": "Inci", "last": "❌", "email": "incikoc2397@gmail.com", "pass": "Inci#Koc7788", "year": "2000"},
    {"first": "Kadir", "last": "❌", "email": "kadriaksoy2398@gmail.com", "pass": "Kadi!Akso9900", "year": "2000"},
    {"first": "Leman", "last": "❌", "email": "lemanpolat2399@gmail.com", "pass": "Lema#Pola1122", "year": "2000"},
    {"first": "Melisa", "last": "❌", "email": "melisadogan2400@gmail.com", "pass": "Meli!Doga3344", "year": "2000"}
]

def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = KeyboardButton("➕ Register a new Gmail")
    item2 = KeyboardButton("📋 My accounts")
    item3 = KeyboardButton("💰 Balance")
    item4 = KeyboardButton("👥 My referrals")
    item5 = KeyboardButton("⚙️ Settings")
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

@bot.message_handler(content_types=['text'])
def handle_message(message):
    user_id = message.chat.id
    text = message.text
    user_data = get_user_data(user_id)
    
    if user_id in user_states:
        state = user_states[user_id]
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
            
        elif state.startswith("awaiting_reject_reason_") and user_id == ADMIN_ID:
            parts = state.split("_")
            task_id = int(parts[3])
            target_user_id = int(parts[4])
            del user_states[user_id]
            
            reason = text
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM pending_tasks WHERE id = %s", (task_id,))
            task = cursor.fetchone()
            email = task[0] if task else "Unknown"
            
            cursor.execute("UPDATE pending_tasks SET status = 'rejected' WHERE id = %s", (task_id,))
            cursor.execute("UPDATE users SET hold_balance = GREATEST(0, hold_balance - %s) WHERE user_id = %s", (GMAIL_RATE, target_user_id))
            cursor.execute("INSERT INTO history (user_id, text) VALUES (%s, %s)", (target_user_id, f"Rejected - Gmail ({email})"))
            conn.commit()
            cursor.close()
            conn.close()
            
            bot.send_message(ADMIN_ID, f"❌ Task for `{email}` rejected.", parse_mode="Markdown")
            try:
                bot.send_message(
                    target_user_id,
                    f"❌ Sorry, your Gmail account (`{email}`) submission was rejected.\n\n📝 **Reason:** {reason}",
                    parse_mode="Markdown"
                )
            except:
                pass
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

    if "Register a new Gmail" in text:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT email FROM assigned_gmails")
        assigned_emails = [row[0] for row in cursor.fetchall()]
        
        selected_acc = None
        for acc in gmail_accounts:
            if acc['email'] not in assigned_emails:
                selected_acc = acc
                break
                
        if not selected_acc:
            cursor.close()
            conn.close()
            bot.send_message(user_id, "❌ Sorry, all Gmail accounts have been distributed! Please check back later.")
            return
            
        cursor.execute("INSERT INTO assigned_gmails (email, user_id, status) VALUES (%s, %s, 'assigned')", (selected_acc['email'], user_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        response_text = (
            f"Register Gmail account using the specified data and get ${GMAIL_RATE:.2f}\n\n"
            f"First name: {selected_acc['first']}\n"
            f"Last name: {selected_acc['last']}\n"
            f"Email: {selected_acc['email']}\n"
            f"Password: {selected_acc['pass']}\n"
            f"Year of birth: {selected_acc['year']}\n\n"
            f"🔐 Be sure to use the specified data, otherwise the account will not be paid."
        )
        
        bot.send_message(user_id, response_text, reply_markup=task_inline_menu())
        
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
            
    elif text == "⬅️ Back":
        bot.send_message(user_id, "Main Menu:", reply_markup=main_menu())
        
    elif text == "👥 My referrals":
        bot_info = bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
        bot.send_message(user_id, f"👥 **Your Referral Link:**\n{ref_link}\n\n🎁 Invite friends and earn ${REF_BONUS:.2f} per active referral!", parse_mode="Markdown")
        
    elif text == "📋 My accounts":
        completed = user_data["completed_count"]
        bot.send_message(user_id, f"📋 Total submitted accounts: {completed}")
        
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
        acc = next((item for item in gmail_accounts if item["email"] == email), None)
        
        if not acc:
            cursor.close()
            conn.close()
            bot.answer_callback_query(call.id, "Account error!", show_alert=True)
            return
            
        cursor.execute("UPDATE assigned_gmails SET status = 'submitted' WHERE email = %s", (email,))
        cursor.execute("UPDATE users SET hold_balance = hold_balance + %s WHERE user_id = %s", (GMAIL_RATE, user_id))
        cursor.execute("INSERT INTO pending_tasks (user_id, email, password, status) VALUES (%s, %s, %s, 'pending')", (user_id, acc['email'], acc['pass']))
        cursor.execute("SELECT currval(pg_get_serial_sequence('pending_tasks','id'))")
        task_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ Approve", callback_data=f"app_{task_id}_{user_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"rej_{task_id}_{user_id}")
        )
        try:
            bot.send_message(
                ADMIN_ID,
                f"🔔 **New Pending Task Check!**\n\nUser ID: `{user_id}`\nEmail: `{acc['email']}`\nPassword: `{acc['pass']}`\nReward on approval: ${GMAIL_RATE:.2f}",
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
        
    elif call.data.startswith("app_") or call.data.startswith("rej_"):
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
        
        if not task or task[1] != 'pending':
            cursor.close()
            conn.close()
            bot.answer_callback_query(call.id, "Task already processed!")
            return
            
        email = task[0]
        
        if action == "app":
            cursor.execute("UPDATE pending_tasks SET status = 'approved' WHERE id = %s", (task_id,))
            cursor.execute("UPDATE users SET balance = balance + %s, hold_balance = GREATEST(0, hold_balance - %s), completed_count = completed_count + 1 WHERE user_id = %s", (GMAIL_RATE, GMAIL_RATE, target_user_id))
            cursor.execute("INSERT INTO history (user_id, text) VALUES (%s, %s)", (target_user_id, f"+${GMAIL_RATE:.2f} - Gmail Approved ({email})"))
            conn.commit()
            cursor.close()
            conn.close()
            
            bot.answer_callback_query(call.id, "Approved successfully!")
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"✅ Task for `{email}` has been **APPROVED**."
            )
            try:
                bot.send_message(target_user_id, f"🎉 Good news! Your Gmail account ({email}) has been approved. +${GMAIL_RATE:.2f} added to your balance!")
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
                text=call.message.text + f"\n\n👉 **Status:** Rejected clicked! Now send the **Reject Reason / Message** in chat for user `{target_user_id}`:",
                parse_mode="Markdown"
            )

    elif call.data == "admin_view_pending":
        if call.from_user.id != ADMIN_ID:
            return
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, user_id, email, password FROM pending_tasks WHERE status = 'pending' LIMIT 5")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not rows:
            bot.answer_callback_query(call.id, "No pending tasks found!")
            return
            
        bot.answer_callback_query(call.id, "Showing pending tasks:")
        for r in rows:
            t_id, u_id, email, pwd = r[0], r[1], r[2], r[3]
            markup = InlineKeyboardMarkup()
            markup.add(
                InlineKeyboardButton("✅ Approve", callback_data=f"app_{t_id}_{u_id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"rej_{t_id}_{u_id}")
            )
            bot.send_message(ADMIN_ID, f"⏳ Pending Task:\nUser ID: `{u_id}`\nEmail: `{email}`\nPassword: `{pwd}`", parse_mode="Markdown", reply_markup=markup)

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
            text="❌ Registration cancelled."
        )
    elif call.data == "btn_help":
        bot.answer_callback_query(call.id, "Instructions sent.")
        bot.send_message(
            user_id,
            "ℹ️ Instructions:\n1. Open Gmail app\n2. Create account with provided Name & DOB\n3. Use exact Email & Password\n4. Click Done when finished."
        )
    elif call.data == "admin_broadcast" and user_id == ADMIN_ID:
        user_states[user_id] = "awaiting_broadcast"
        bot.send_message(ADMIN_ID, "📢 Enter the broadcast message you want to send to all users:")

# Start Flask in a background thread so Render detects an active web port
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    print("Bot & Supabase Database connected successfully. Running...")
    bot.delete_webhook()
    bot.infinity_polling(skip_pending=True)
