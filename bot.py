import telebot
import sqlite3
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

TOKEN = '8788513514:AAGwboQDDtl198sib3_3GX3ahtmh0wg4iS0'
bot = telebot.TeleBot(TOKEN)

ADMIN_ID = 5813365228

GMAIL_RATE = 0.15
MIN_PAYOUT = 0.20
REF_BONUS = 0.02

def init_db():
    conn = sqlite3.connect("bot_database_v9.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0.0,
            hold_balance REAL DEFAULT 0.0,
            completed_count INTEGER DEFAULT 0,
            referred_by INTEGER DEFAULT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pending_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            email TEXT,
            password TEXT,
            status TEXT DEFAULT 'pending'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            text TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assigned_gmails (
            email TEXT PRIMARY KEY,
            user_id INTEGER,
            status TEXT DEFAULT 'assigned'
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_db():
    return sqlite3.connect("bot_database_v9.db")

def get_user_data(user_id, referred_by=None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT balance, hold_balance, completed_count FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    if not row:
        cursor.execute("INSERT INTO users (user_id, referred_by) VALUES (?, ?)", (user_id, referred_by))
        conn.commit()
        if referred_by and referred_by != user_id:
            cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (REF_BONUS, referred_by))
            cursor.execute("INSERT INTO history (user_id, text) VALUES (?, ?)", (referred_by, f"+${REF_BONUS} Referral Bonus"))
            conn.commit()
            try:
                bot.send_message(referred_by, f"🎉 You received a ${REF_BONUS} referral bonus!")
            except:
                pass
        cursor.execute("SELECT balance, hold_balance, completed_count FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        
    conn.close()
    return {"balance": row[0], "hold_balance": row[1], "completed_count": row[2]}

gmail_accounts = [
    {"first": "Masako", "last": "❌", "email": "izonuyujif168@gmail.com", "pass": "6zW1W4UhGgclbO", "year": "2000"},
    {"first": "Alena", "last": "❌", "email": "itadocato758@gmail.com", "pass": "BoFCRVFWJZbSU", "year": "2000"},
    {"first": "Tomey", "last": "❌", "email": "tomeyufop028@gmail.com", "pass": "TomeyP928501", "year": "2000"},
    {"first": "Xerizi", "last": "❌", "email": "xerizixacom91@gmail.com", "pass": "XeriziP782910", "year": "2000"},
    {"first": "Pujegara", "last": "❌", "email": "pujegara687@gmail.com", "pass": "PujeP6728190", "year": "2000"},
    {"first": "Elena", "last": "❌", "email": "elena.rodriguez.2000@gmail.com", "pass": "El#Rod7890xK", "year": "2000"},
    {"first": "Lucas", "last": "❌", "email": "lucas.bennett00@gmail.com", "pass": "L8k!Benn2000", "year": "2000"},
    {"first": "Sophie", "last": "❌", "email": "sophie.miller2000@gmail.com", "pass": "SoPh!eM9918", "year": "2000"},
    {"first": "Aiden", "last": "❌", "email": "aiden.walker2001@gmail.com", "pass": "Aid!Walk9012", "year": "2000"},
    {"first": "Bella", "last": "❌", "email": "bella.scott2002@gmail.com", "pass": "Bell#Scot345", "year": "2000"},
    {"first": "Caleb", "last": "❌", "email": "caleb.turner2003@gmail.com", "pass": "CalebT8890!", "year": "2000"},
    {"first": "Daisy", "last": "❌", "email": "daisy.cooper2004@gmail.com", "pass": "Dais#Coop112", "year": "2000"},
    {"first": "Ethan", "last": "❌", "email": "ethan.ward2005@gmail.com", "pass": "Eth!Ward5564", "year": "2000"},
    {"first": "Fiona", "last": "❌", "email": "fiona.peterson2006@gmail.com", "pass": "Fion#Pete778", "year": "2000"},
    {"first": "Gavin", "last": "❌", "email": "gavin.reed2007@gmail.com", "pass": "Gavi!Reed334", "year": "2000"},
    {"first": "Hazel", "last": "❌", "email": "hazel.kelly2008@gmail.com", "pass": "Haz#Kell9900", "year": "2000"},
    {"first": "Ian", "last": "❌", "email": "ian.howard2009@gmail.com", "pass": "Ian!How2211", "year": "2000"},
    {"first": "Julia", "last": "❌", "email": "julia.ramos2010@gmail.com", "pass": "Juli#Ram5544", "year": "2000"},
    {"first": "Kevin", "last": "❌", "email": "kevin.kim2011@gmail.com", "pass": "Kev!Kim7788", "year": "2000"},
    {"first": "Lily", "last": "❌", "email": "lily.cox2012@gmail.com", "pass": "Lily#Cox9988", "year": "2000"},
    {"first": "Mason", "last": "❌", "email": "mason.ward2013@gmail.com", "pass": "Maso!Ward1122", "year": "2000"},
    {"first": "Nora", "last": "❌", "email": "nora.richardson2014@gmail.com", "pass": "Nora#Rich3344", "year": "2000"},
    {"first": "Owen", "last": "❌", "email": "owen.watson2015@gmail.com", "pass": "Owen!Wats5566", "year": "2000"},
    {"first": "Piper", "last": "❌", "email": "piper.brooks2016@gmail.com", "pass": "Pipe#Broo7788", "year": "2000"},
    {"first": "Quinn", "last": "❌", "email": "quinn.sanders2017@gmail.com", "pass": "Quin!Sand9900", "year": "2000"},
    {"first": "Ruby", "last": "❌", "email": "ruby.price2018@gmail.com", "pass": "Ruby#Pric1133", "year": "2000"},
    {"first": "Sam", "last": "❌", "email": "sam.bennett2019@gmail.com", "pass": "Sam!Benn2244", "year": "2000"},
    {"first": "Tessa", "last": "❌", "email": "tessa.wood2020@gmail.com", "pass": "Tess#Wood5566", "year": "2000"},
    {"first": "Uriah", "last": "❌", "email": "uriah.barnes2021@gmail.com", "pass": "Uri!Barn7788", "year": "2000"},
    {"first": "Vera", "last": "❌", "email": "vera.ross2022@gmail.com", "pass": "Vera#Ross9900", "year": "2000"},
    {"first": "Wyatt", "last": "❌", "email": "wyatt.henderson2023@gmail.com", "pass": "Wyat!Hend1144", "year": "2000"},
    {"first": "Xena", "last": "❌", "email": "xena.coleman2024@gmail.com", "pass": "Xena#Cole2255", "year": "2000"},
    {"first": "Yara", "last": "❌", "email": "yara.jenkins2025@gmail.com", "pass": "Yara!Jenk3366", "year": "2000"},
    {"first": "Zack", "last": "❌", "email": "zack.perry2026@gmail.com", "pass": "Zack#Perr4477", "year": "2000"},
    {"first": "Aaron", "last": "❌", "email": "aaron.powell2027@gmail.com", "pass": "Aaro!Powe5588", "year": "2000"},
    {"first": "Brooke", "last": "❌", "email": "brooke.long2028@gmail.com", "pass": "Broo#Long6699", "year": "2000"},
    {"first": "Chase", "last": "❌", "email": "chase.patterson2029@gmail.com", "pass": "Chas!Patt7711", "year": "2000"},
    {"first": "Diana", "last": "❌", "email": "diana.hughes2030@gmail.com", "pass": "Dian#Hugh8822", "year": "2000"},
    {"first": "Elias", "last": "❌", "email": "elias.flores2031@gmail.com", "pass": "Elia!Flor9933", "year": "2000"},
    {"first": "Faith", "last": "❌", "email": "faith.washington2032@gmail.com", "pass": "Fait#Wash1144", "year": "2000"},
    {"first": "George", "last": "❌", "email": "george.butler2033@gmail.com", "pass": "Geor!Butl2255", "year": "2000"},
    {"first": "Hope", "last": "❌", "email": "hope.simmons2034@gmail.com", "pass": "Hope#Simm3366", "year": "2000"},
    {"first": "Isaac", "last": "❌", "email": "isaac.foster2035@gmail.com", "pass": "Isaa!Fost4477", "year": "2000"},
    {"first": "Jade", "last": "❌", "email": "jade.gonzales2036@gmail.com", "pass": "Jade#Gonz5588", "year": "2000"},
    {"first": "Kyle", "last": "❌", "email": "kyle.bryant2037@gmail.com", "pass": "Kyle!Brya6699", "year": "2000"},
    {"first": "Luna", "last": "❌", "email": "luna.alexander2038@gmail.com", "pass": "Luna#Alex7711", "year": "2000"},
    {"first": "Miles", "last": "❌", "email": "miles.russell2039@gmail.com", "pass": "Mile!Russ8822", "year": "2000"},
    {"first": "Naomi", "last": "❌", "email": "naomi.griffin2040@gmail.com", "pass": "Naom#Grif9933", "year": "2000"},
    {"first": "Oscar", "last": "❌", "email": "oscar.diaz2041@gmail.com", "pass": "Osca!Diaz1144", "year": "2000"},
    {"first": "Paige", "last": "❌", "email": "paige.hayes2042@gmail.com", "pass": "Paig#Haye2255", "year": "2000"},
    {"first": "Riley", "last": "❌", "email": "riley.myers2043@gmail.com", "pass": "Rile!Myer3366", "year": "2000"},
    {"first": "Stella", "last": "❌", "email": "stella.ford2044@gmail.com", "pass": "Stel#Ford4477", "year": "2000"},
    {"first": "Tristan", "last": "❌", "email": "tristan.hamilton2045@gmail.com", "pass": "Tris!Hami5588", "year": "2000"},
    {"first": "Violet", "last": "❌", "email": "violet.graham2046@gmail.com", "pass": "Vio#Grah6699", "year": "2000"},
    {"first": "Wesley", "last": "❌", "email": "wesley.sullivan2047@gmail.com", "pass": "Wesl!Sull7711", "year": "2000"},
    {"first": "Zara", "last": "❌", "email": "zara.wallace2048@gmail.com", "pass": "Zara#Wall8822", "year": "2000"},
    {"first": "Adam", "last": "❌", "email": "adam.woods2049@gmail.com", "pass": "Adam!Wood9933", "year": "2000"},
    {"first": "Chloe", "last": "❌", "email": "chloe.cole2050@gmail.com", "pass": "Chlo#Cole1144", "year": "2000"},
    {"first": "Dylan", "last": "❌", "email": "dylan.west2051@gmail.com", "pass": "Dyla!West2255", "year": "2000"},
    {"first": "Eva", "last": "❌", "email": "eva.jordan2052@gmail.com", "pass": "Eva#Jord3366", "year": "2000"},
    {"first": "Felix", "last": "❌", "email": "felix.owens2053@gmail.com", "pass": "Feli!Owen4477", "year": "2000"},
    {"first": "Grace", "last": "❌", "email": "grace.reynolds2054@gmail.com", "pass": "Grac#Reyn5588", "year": "2000"},
    {"first": "Henry", "last": "❌", "email": "henry.fisher2055@gmail.com", "pass": "Henr!Fish6699", "year": "2000"},
    {"first": "Isla", "last": "❌", "email": "isla.ellis2056@gmail.com", "pass": "Isla#Elli7711", "year": "2000"},
    {"first": "Jack", "last": "❌", "email": "jack.harrison2057@gmail.com", "pass": "Jack!Harr8822", "year": "2000"},
    {"first": "Kylie", "last": "❌", "email": "kylie.gibson2058@gmail.com", "pass": "Kyli#Gibs9933", "year": "2000"},
    {"first": "Leo", "last": "❌", "email": "leo.mcdonald2059@gmail.com", "pass": "Leo!Mcdo1144", "year": "2000"},
    {"first": "Maya", "last": "❌", "email": "maya.cruz2060@gmail.com", "pass": "Maya#Cruz2255", "year": "2000"},
    {"first": "Nolan", "last": "❌", "email": "nolan.marshall2061@gmail.com", "pass": "Nola!Mars3366", "year": "2000"},
    {"first": "Penelope", "last": "❌", "email": "penelope.ortiz2062@gmail.com", "pass": "Pene#Ortiz4477", "year": "2000"},
    {"first": "Ryder", "last": "❌", "email": "ryder.gomez2063@gmail.com", "pass": "Ryde!Gome5588", "year": "2000"},
    {"first": "Savannah", "last": "❌", "email": "savannah.murray2064@gmail.com", "pass": "Sava#Murr6699", "year": "2000"},
    {"first": "Tobias", "last": "❌", "email": "tobias.freeman2065@gmail.com", "pass": "Tobi!Free7711", "year": "2000"},
    {"first": "Victoria", "last": "❌", "email": "victoria.wells2066@gmail.com", "pass": "Vict#Well8822", "year": "2000"},
    {"first": "Zachary", "last": "❌", "email": "zachary.webb2067@gmail.com", "pass": "Zach!Webb9933", "year": "2000"},
    {"first": "Alice", "last": "❌", "email": "alice.simpson2068@gmail.com", "pass": "Alic#Simp1144", "year": "2000"},
    {"first": "Brandon", "last": "❌", "email": "brandon.stevens2069@gmail.com", "pass": "Bran!Stev2255", "year": "2000"},
    {"first": "Clara", "last": "❌", "email": "clara.tucker2070@gmail.com", "pass": "Clar#Tuck3366", "year": "2000"},
    {"first": "Damian", "last": "❌", "email": "damian.porter2071@gmail.com", "pass": "Dami!Port4477", "year": "2000"},
    {"first": "Elena", "last": "❌", "email": "elena.hunter2072@gmail.com", "pass": "Elen#Hunt5588", "year": "2000"},
    {"first": "Frankie", "last": "❌", "email": "frankie.hicks2073@gmail.com", "pass": "Fran!Hick6699", "year": "2000"},
    {"first": "Gemma", "last": "❌", "email": "gemma.crawford2074@gmail.com", "pass": "Gemm#Craw7711", "year": "2000"},
    {"first": "Hayden", "last": "❌", "email": "hayden.henry2075@gmail.com", "pass": "Hayd!Henr8822", "year": "2000"},
    {"first": "Iris", "last": "❌", "email": "iris.boyd2076@gmail.com", "pass": "Iris#Boyd9933", "year": "2000"},
    {"first": "Jaxon", "last": "❌", "email": "jaxon.mason2077@gmail.com", "pass": "Jaxo!Maso1144", "year": "2000"},
    {"first": "Kendra", "last": "❌", "email": "kendra.morales2078@gmail.com", "pass": "Kend#Mora2255", "year": "2000"},
    {"first": "Logan", "last": "❌", "email": "logan.kennedy2079@gmail.com", "pass": "Loga!Kenn3366", "year": "2000"},
    {"first": "Melanie", "last": "❌", "email": "melanie.warren2070@gmail.com", "pass": "Mela#Warr4477", "year": "2000"},
    {"first": "Nathan", "last": "❌", "email": "nathan.dixon2081@gmail.com", "pass": "Nath!Dixo5588", "year": "2000"},
    {"first": "Olive", "last": "❌", "email": "olive.ramos2082@gmail.com", "pass": "Oliv#Ramo6699", "year": "2000"},
    {"first": "Preston", "last": "❌", "email": "preston.rice2083@gmail.com", "pass": "Pres!Rice7711", "year": "2000"},
    {"first": "Queenie", "last": "❌", "email": "queenie.burns2084@gmail.com", "pass": "Quee#Burn8822", "year": "2000"},
    {"first": "Reid", "last": "❌", "email": "reid.gordon2085@gmail.com", "pass": "Reid!Gord9933", "year": "2000"},
    {"first": "Sienna", "last": "❌", "email": "sienna.shaw2086@gmail.com", "pass": "Sien#Shaw1144", "year": "2000"},
    {"first": "Travis", "last": "❌", "email": "travis.holmes2087@gmail.com", "pass": "Trav!Holm2255", "year": "2000"},
    {"first": "Una", "last": "❌", "email": "una.rice2088@gmail.com", "pass": "Una#Rice3366", "year": "2000"},
    {"first": "Vincent", "last": "❌", "email": "vincent.robertson2089@gmail.com", "pass": "Vinc!Robe4477", "year": "2000"},
    {"first": "Willa", "last": "❌", "email": "willa.hunt2090@gmail.com", "pass": "Will#Hunt5588", "year": "2000"},
    {"first": "Xavier", "last": "❌", "email": "xavier.black2091@gmail.com", "pass": "Xavi!Blac6699", "year": "2000"},
    {"first": "Yvonne", "last": "❌", "email": "yvonne.daniels2092@gmail.com", "pass": "Yvon#Dani7711", "year": "2000"},
    {"first": "Zane", "last": "❌", "email": "zane.palmer2093@gmail.com", "pass": "Zane!Palm8822", "year": "2000"},
    {"first": "Amber", "last": "❌", "email": "amber.mills2094@gmail.com", "pass": "Ambe#Mill9933", "year": "2000"},
    {"first": "Bryce", "last": "❌", "email": "bryce.nichols2095@gmail.com", "pass": "Bryc!Nich1144", "year": "2000"},
    {"first": "Cora", "last": "❌", "email": "cora.grant2096@gmail.com", "pass": "Cora#Gran2255", "year": "2000"},
    {"first": "Derek", "last": "❌", "email": "derek.knight2097@gmail.com", "pass": "Dere!Knig3366", "year": "2000"},
    {"first": "Elise", "last": "❌", "email": "elise.ferguson2098@gmail.com", "pass": "Elis#Ferg4477", "year": "2000"},
    {"first": "Finn", "last": "❌", "email": "finn.rose2099@gmail.com", "pass": "Finn!Rose5588", "year": "2000"},
    {"first": "Giselle", "last": "❌", "email": "giselle.stone2100@gmail.com", "pass": "Gise#Ston6699", "year": "2000"},
    {"first": "Hudson", "last": "❌", "email": "hudson.hawkins2101@gmail.com", "pass": "Huds!Hawk7711", "year": "2000"},
    {"first": "Isabel", "last": "❌", "email": "isabel.dunn2102@gmail.com", "pass": "Isab#Dunn8822", "year": "2000"},
    {"first": "Jared", "last": "❌", "email": "jared.perkins2103@gmail.com", "pass": "Jare!Perk9933", "year": "2000"},
    {"first": "Kara", "last": "❌", "email": "kara.hudson2104@gmail.com", "pass": "Kara#Huds1144", "year": "2000"},
    {"first": "Landon", "last": "❌", "email": "landon.spencer2105@gmail.com", "pass": "Land!Spen2255", "year": "2000"},
    {"first": "Monica", "last": "❌", "email": "monica.gardner2106@gmail.com", "pass": "Moni#Gard3366", "year": "2000"},
    {"first": "Nash", "last": "❌", "email": "nash.payne2107@gmail.com", "pass": "Nash!Payn4477", "year": "2000"},
    {"first": "Opal", "last": "❌", "email": "opal.pierce2108@gmail.com", "pass": "Opal#Pier5588", "year": "2000"},
    {"first": "Parker", "last": "❌", "email": "parker.berry2109@gmail.com", "pass": "Park!Berr6699", "year": "2000"},
    {"first": "Queenie", "last": "❌", "email": "queenie.matthews2110@gmail.com", "pass": "Quee#Matt7711", "year": "2000"},
    {"first": "Rowan", "last": "❌", "email": "rowan.arnold2111@gmail.com", "pass": "Rowa!Arno8822", "year": "2000"},
    {"first": "Selena", "last": "❌", "email": "selena.wagner2112@gmail.com", "pass": "Sele#Wagn9933", "year": "2000"},
    {"first": "Toby", "last": "❌", "email": "toby.willis2113@gmail.com", "pass": "Toby!Will1144", "year": "2000"},
    {"first": "Uma", "last": "❌", "email": "uma.ray2114@gmail.com", "pass": "Uma#Ray2255", "year": "2000"},
    {"first": "Vance", "last": "❌", "email": "vance.watkins2115@gmail.com", "pass": "Vanc!Watk3366", "year": "2000"},
    {"first": "Wendy", "last": "❌", "email": "wendy.olson2116@gmail.com", "pass": "Wend#Olso4477", "year": "2000"},
    {"first": "Xander", "last": "❌", "email": "xander.carroll2117@gmail.com", "pass": "Xand#Carr5588", "year": "2000"},
    {"first": "Yasmine", "last": "❌", "email": "yasmine.duncan2118@gmail.com", "pass": "Yasm#Dunc6699", "year": "2000"},
    {"first": "Zion", "last": "❌", "email": "zion.snyder2119@gmail.com", "pass": "Zion!Snyd7711", "year": "2000"},
    {"first": "Ashton", "last": "❌", "email": "ashton.hart2120@gmail.com", "pass": "Asht!Hart8822", "year": "2000"},
    {"first": "Bianca", "last": "❌", "email": "bianca.cunningham2121@gmail.com", "pass": "Bian#Cunn9933", "year": "2000"},
    {"first": "Cole", "last": "❌", "email": "cole.bradley2122@gmail.com", "pass": "Cole!Brad1144", "year": "2000"},
    {"first": "Dakota", "last": "❌", "email": "dakota.lane2123@gmail.com", "pass": "Dako#Lane2255", "year": "2000"},
    {"first": "Eden", "last": "❌", "email": "eden.andrews2124@gmail.com", "pass": "Eden!Andr3366", "year": "2000"},
    {"first": "Flint", "last": "❌", "email": "flint.ruiz2125@gmail.com", "pass": "Flin#Ruiz4477", "year": "2000"},
    {"first": "Gia", "last": "❌", "email": "gia.harper2126@gmail.com", "pass": "Gia!Harp5588", "year": "2000"},
    {"first": "Holden", "last": "❌", "email": "holden.fox2127@gmail.com", "pass": "Hold#Fox6699", "year": "2000"},
    {"first": "Ivy", "last": "❌", "email": "ivy.riley2128@gmail.com", "pass": "Ivy!Rile7711", "year": "2000"},
    {"first": "Jonah", "last": "❌", "email": "jonah.schmidt2129@gmail.com", "pass": "Jona#Schm8822", "year": "2000"},
    {"first": "Kira", "last": "❌", "email": "kira.olson2130@gmail.com", "pass": "Kira!Olso9933", "year": "2000"},
    {"first": "Liam", "last": "❌", "email": "liam.harvey2131@gmail.com", "pass": "Liam#Harv1144", "year": "2000"},
    {"first": "Mila", "last": "❌", "email": "mila.patterson2132@gmail.com", "pass": "Mila!Patt2255", "year": "2000"},
    {"first": "Orion", "last": "❌", "email": "orion.medina2133@gmail.com", "pass": "Orio#Medi3366", "year": "2000"},
    {"first": "Piper", "last": "❌", "email": "piper.fowler2134@gmail.com", "pass": "Pipe!Fowl4477", "year": "2000"},
    {"first": "Quentin", "last": "❌", "email": "quentin.brewer2135@gmail.com", "pass": "Quen#Brew5588", "year": "2000"},
    {"first": "Reese", "last": "❌", "email": "reese.hoffman2136@gmail.com", "pass": "Rees!Hoff6699", "year": "2000"},
    {"first": "Skylar", "last": "❌", "email": "skylar.carlson2137@gmail.com", "pass": "Skyl#Carl7711", "year": "2000"},
    {"first": "Tatum", "last": "❌", "email": "tatum.silva2138@gmail.com", "pass": "Tatu!Silv8822", "year": "2000"},
    {"first": "Uri", "last": "❌", "email": "uri.pearson2139@gmail.com", "pass": "Uri#Pear9933", "year": "2000"},
    {"first": "Valerie", "last": "❌", "email": "valerie.medeiros2140@gmail.com", "pass": "Vale!Medi1144", "year": "2000"},
    {"first": "Wade", "last": "❌", "email": "wade.mckinney2141@gmail.com", "pass": "Wade#McKi2255", "year": "2000"},
    {"first": "Xia", "last": "❌", "email": "xia.lucas2142@gmail.com", "pass": "Xia!Luca3366", "year": "2000"},
    {"first": "Yusuf", "last": "❌", "email": "yusuf.johnson2143@gmail.com", "pass": "Yusu#John4477", "year": "2000"},
    {"first": "Zelda", "last": "❌", "email": "zelda.smith2144@gmail.com", "pass": "Zeld!Smit5588", "year": "2000"},
    {"first": "Abel", "last": "❌", "email": "abel.williams2145@gmail.com", "pass": "Abel#Will6699", "year": "2000"},
    {"first": "Bridget", "last": "❌", "email": "bridget.brown2146@gmail.com", "pass": "Brid!Brow7711", "year": "2000"},
    {"first": "Cyrus", "last": "❌", "email": "cyrus.jones2147@gmail.com", "pass": "Cyru#Jone8822", "year": "2000"},
    {"first": "Daphne", "last": "❌", "email": "daphne.garcia2148@gmail.com", "pass": "Daph!Garc9933", "year": "2000"},
    {"first": "Ezekiel", "last": "❌", "email": "ezekiel.miller2149@gmail.com", "pass": "Ezek#Mill1144", "year": "2000"},
    {"first": "Freya", "last": "❌", "email": "freya.davis2150@gmail.com", "pass": "Frey!Davi2255", "year": "2000"},
    {"first": "Gideon", "last": "❌", "email": "gideon.rodriguez2151@gmail.com", "pass": "Gide#Rodr3366", "year": "2000"},
    {"first": "Hadley", "last": "❌", "email": "hadley.martinez2152@gmail.com", "pass": "Hadl!Mart4477", "year": "2000"},
    {"first": "Ignacio", "last": "❌", "email": "ignacio.hernandez2153@gmail.com", "pass": "Igna#Hern5588", "year": "2000"},
    {"first": "Jocelyn", "last": "❌", "email": "jocelyn.lopez2154@gmail.com", "pass": "Joce!Lope6699", "year": "2000"},
    {"first": "Kian", "last": "❌", "email": "kian.gonzalez2155@gmail.com", "pass": "Kian#Gonz7711", "year": "2000"},
    {"first": "Lana", "last": "❌", "email": "lana.wilson2156@gmail.com", "pass": "Lana!Wils8822", "year": "2000"},
    {"first": "Milo", "last": "❌", "email": "milo.anderson2157@gmail.com", "pass": "Milo#Ande9933", "year": "2000"},
    {"first": "Noelle", "last": "❌", "email": "noelle.thomas2158@gmail.com", "pass": "Noel!Thom1144", "year": "2000"},
    {"first": "Orson", "last": "❌", "email": "orson.taylor2159@gmail.com", "pass": "Orso#Tayl2255", "year": "2000"},
    {"first": "Paloma", "last": "❌", "email": "paloma.moore2160@gmail.com", "pass": "Palo!Moor3366", "year": "2000"},
    {"first": "Quincy", "last": "❌", "email": "quincy.jackson2161@gmail.com", "pass": "Quin#Jack4477", "year": "2000"},
    {"first": "Ramon", "last": "❌", "email": "ramon.martin2162@gmail.com", "pass": "Ramo!Mart5588", "year": "2000"},
    {"first": "Selma", "last": "❌", "email": "selma.lee2163@gmail.com", "pass": "Selm#Lee6699", "year": "2000"},
    {"first": "Thaddeus", "last": "❌", "email": "thaddeus.perez2164@gmail.com", "pass": "Thad!Perez7711", "year": "2000"},
    {"first": "Ulric", "last": "❌", "email": "ulric.thompson2165@gmail.com", "pass": "Ulri#Thom8822", "year": "2000"},
    {"first": "Veda", "last": "❌", "email": "veda.white2166@gmail.com", "pass": "Veda!Whit9933", "year": "2000"},
    {"first": "Winston", "last": "❌", "email": "winston.harris2167@gmail.com", "pass": "Wins#Harr1144", "year": "2000"},
    {"first": "Xens", "last": "❌", "email": "xens.clark2168@gmail.com", "pass": "Xens!Clar2255", "year": "2000"},
    {"first": "Yara", "last": "❌", "email": "yara.lewis2169@gmail.com", "pass": "Yara#Lewi3366", "year": "2000"},
    {"first": "Zephyr", "last": "❌", "email": "zephyr.robinson2170@gmail.com", "pass": "Zeph!Robi4477", "year": "2000"},
    {"first": "Althea", "last": "❌", "email": "althea.walker2171@gmail.com", "pass": "Alth#Walk5588", "year": "2000"},
    {"first": "Bane", "last": "❌", "email": "bane.young2172@gmail.com", "pass": "Bane!Youn6699", "year": "2000"},
    {"first": "Calista", "last": "❌", "email": "calista.king2173@gmail.com", "pass": "Cali#King7711", "year": "2000"},
    {"first": "Darius", "last": "❌", "email": "darius.wright2174@gmail.com", "pass": "Dari!Wrig8822", "year": "2000"},
    {"first": "Ember", "last": "❌", "email": "ember.scott2175@gmail.com", "pass": "Embe#Scot9933", "year": "2000"},
    {"first": "Falcon", "last": "❌", "email": "falcon.green2176@gmail.com", "pass": "Falc!Gree1144", "year": "2000"},
    {"first": "Gwen", "last": "❌", "email": "gwen.baker2177@gmail.com", "pass": "Gwen#Bake2255", "year": "2000"},
    {"first": "Hakeem", "last": "❌", "email": "hakeem.adams2178@gmail.com", "pass": "Hake!Adam3366", "year": "2000"},
    {"first": "Iliana", "last": "❌", "email": "iliana.nelson2179@gmail.com", "pass": "Ilia#Nels4477", "year": "2000"},
    {"first": "Jagger", "last": "❌", "email": "jagger.hill2180@gmail.com", "pass": "Jagg!Hill5588", "year": "2000"},
    {"first": "Kenna", "last": "❌", "email": "kenna.ramirez2181@gmail.com", "pass": "Kenn#Rami6699", "year": "2000"},
    {"first": "Laker", "last": "❌", "email": "laker.campbell2182@gmail.com", "pass": "Lake!Camp7711", "year": "2000"},
    {"first": "Maris", "last": "❌", "email": "maris.mitchell2183@gmail.com", "pass": "Mari#Mitt8822", "year": "2000"},
    {"first": "Neriah", "last": "❌", "email": "neriah.roberts2184@gmail.com", "pass": "Neri!Robe9933", "year": "2000"},
    {"first": "Otis", "last": "❌", "email": "otis.carter2185@gmail.com", "pass": "Otis#Cart1144", "year": "2000"},
    {"first": "Pia", "last": "❌", "email": "pia.phillips2186@gmail.com", "pass": "Pia!Phil2255", "year": "2000"},
    {"first": "Qasim", "last": "❌", "email": "qasim.evans2187@gmail.com", "pass": "Qasi#Evan3366", "year": "2000"},
    {"first": "Rory", "last": "❌", "email": "rory.turner2188@gmail.com", "pass": "Rory!Turn4477", "year": "2000"},
    {"first": "Sari", "last": "❌", "email": "sari.torres2189@gmail.com", "pass": "Sari#Torr5588", "year": "2000"},
    {"first": "Talon", "last": "❌", "email": "talon.parker2190@gmail.com", "pass": "Talo!Park6699", "year": "2000"},
    {"first": "Uziah", "last": "❌", "email": "uziah.collins2191@gmail.com", "pass": "Uzia#Coll7711", "year": "2000"},
    {"first": "Veda", "last": "❌", "email": "veda.stewart2192@gmail.com", "pass": "Veda!Stew8822", "year": "2000"},
    {"first": "Waldo", "last": "❌", "email": "waldo.morris2193@gmail.com", "pass": "Wald#Morr9933", "year": "2000"},
    {"first": "Xena", "last": "❌", "email": "xena.rogers2194@gmail.com", "pass": "Xena!Roge1144", "year": "2000"},
    {"first": "Yaro", "last": "❌", "email": "yaro.reed2195@gmail.com", "pass": "Yaro#Reed2255", "year": "2000"},
    {"first": "Zita", "last": "❌", "email": "zita.cook2196@gmail.com", "pass": "Zita!Cook3366", "year": "2000"},
    {"first": "Alistair", "last": "❌", "email": "alistair.morgan2197@gmail.com", "pass": "Alis#Morg4477", "year": "2000"},
    {"first": "Bria", "last": "❌", "email": "bria.bell2198@gmail.com", "pass": "Bria!Bell5588", "year": "2000"},
    {"first": "Cai", "last": "❌", "email": "cai.murphy2199@gmail.com", "pass": "Cai#Murp6699", "year": "2000"},
    {"first": "Dara", "last": "❌", "email": "dara.bailey2200@gmail.com", "pass": "Dara!Bail7711", "year": "2000"}
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
            fee_text = "5 BDT Fee" if method in ["bKash", "Nagad"] else "0.03$ Fee"
            del user_states[user_id]
            
            bal = user_data["balance"]
            if bal < MIN_PAYOUT:
                bot.send_message(user_id, f"❌ Insufficient balance. Minimum payout is ${MIN_PAYOUT:.2f}")
                return
            
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET balance = 0.0 WHERE user_id = ?", (user_id,))
            cursor.execute("INSERT INTO history (user_id, text) VALUES (?, ?)", (user_id, f"-${bal:.2f} Payout via {method} ({text})"))
            conn.commit()
            conn.close()
            
            try:
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton("✅ Confirm & Send TXID", callback_data=f"payapp_{user_id}"))
                bot.send_message(
                    ADMIN_ID,
                    f"🔔 **New Payout Request!**\n\nUser ID: `{user_id}`\nMethod: `{method}`\nAmount: `${bal:.2f}` (Fee: {fee_text})\nDetails/Number: `{text}`",
                    parse_mode="Markdown",
                    reply_markup=markup
                )
            except:
                pass
            
            bot.send_message(user_id, f"✅ Withdrawal request of ${bal:.2f} via {method} submitted successfully! It will be processed soon.", reply_markup=main_menu())
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
            cursor.execute("SELECT email FROM pending_tasks WHERE id = ?", (task_id,))
            task = cursor.fetchone()
            email = task[0] if task else "Unknown"
            
            cursor.execute("UPDATE pending_tasks SET status = 'rejected' WHERE id = ?", (task_id,))
            cursor.execute("UPDATE users SET hold_balance = MAX(0, hold_balance - ?) WHERE user_id = ?", (GMAIL_RATE, target_user_id))
            cursor.execute("INSERT INTO history (user_id, text) VALUES (?, ?)", (target_user_id, f"Rejected - Gmail ({email})"))
            conn.commit()
            conn.close()
            
            bot.send_message(ADMIN_ID, f"❌ Task for `{email}` rejected with reason sent to user.", parse_mode="Markdown")
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
        
        assigned_emails = [row[0] for row in cursor.execute("SELECT email FROM assigned_gmails").fetchall()]
        
        selected_acc = None
        for acc in gmail_accounts:
            if acc['email'] not in assigned_emails:
                selected_acc = acc
                break
                
        if not selected_acc:
            conn.close()
            bot.send_message(user_id, "❌ Sorry, all Gmail accounts have been distributed! Please check back later.")
            return
            
        cursor.execute("INSERT INTO assigned_gmails (email, user_id, status) VALUES (?, ?, 'assigned')", (selected_acc['email'], user_id))
        conn.commit()
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
        cursor.execute("SELECT text FROM history WHERE user_id = ? ORDER BY id DESC LIMIT 10", (user_id,))
        rows = cursor.fetchall()
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
        cursor.execute("SELECT email FROM assigned_gmails WHERE user_id = ? AND status = 'assigned'", (user_id,))
        assigned = cursor.fetchone()
        
        if not assigned:
            conn.close()
            bot.answer_callback_query(call.id, "No active task found!", show_alert=True)
            return
            
        email = assigned[0]
        acc = next((item for item in gmail_accounts if item["email"] == email), None)
        
        if not acc:
            conn.close()
            bot.answer_callback_query(call.id, "Account error!", show_alert=True)
            return
            
        cursor.execute("UPDATE assigned_gmails SET status = 'submitted' WHERE email = ?", (email,))
        cursor.execute("UPDATE users SET hold_balance = hold_balance + ? WHERE user_id = ?", (GMAIL_RATE, user_id))
        cursor.execute("INSERT INTO pending_tasks (user_id, email, password, status) VALUES (?, ?, ?, 'pending')", (user_id, acc['email'], acc['pass']))
        task_id = cursor.lastrowid
        conn.commit()
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
        cursor.execute("SELECT email, status FROM pending_tasks WHERE id = ?", (task_id,))
        task = cursor.fetchone()
        
        if not task or task[1] != 'pending':
            conn.close()
            bot.answer_callback_query(call.id, "Task already processed!")
            return
            
        email = task[0]
        
        if action == "app":
            cursor.execute("UPDATE pending_tasks SET status = 'approved' WHERE id = ?", (task_id,))
            cursor.execute("UPDATE users SET balance = balance + ?, hold_balance = MAX(0, hold_balance - ?), completed_count = completed_count + 1 WHERE user_id = ?", (GMAIL_RATE, GMAIL_RATE, target_user_id))
            cursor.execute("INSERT INTO history (user_id, text) VALUES (?, ?)", (target_user_id, f"+${GMAIL_RATE:.2f} - Gmail Approved ({email})"))
            conn.commit()
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
        cursor.execute("DELETE FROM assigned_gmails WHERE user_id = ? AND status = 'assigned'", (user_id,))
        conn.commit()
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

print("Bot is running...")
bot.delete_webhook()
bot.infinity_polling(skip_pending=True)
