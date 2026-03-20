import streamlit as st
import yt_dlp
import sqlite3
import hashlib
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
from datetime import datetime, timedelta
import pandas as pd
from streamlit_option_menu import option_menu
from streamlit_lottie import st_lottie
import requests

# --- ১. সবার আগে কনফিগারেশন ---
st.set_page_config(page_title="Infinity Pro", layout="wide", page_icon="♾️")

# --- ২. সেশন স্টেট ইনিশিয়ালাইজেশন ---
if 'logged_in' not in st.session_state:
    st.session_state.update({
        'logged_in': False, 
        'user': None, 
        'page': 'landing', 
        'done_today': 0
    })

# --- ৩. এপিআই ও ডাটাবেস সেটআপ ---
# এখানে আপনার জেমিনি এপিআই কি বসান
GEMINI_API_KEY = "AIzaSyDYBFyyJzFVkOXwybViaZvEc25mkJyKKK8" 
genai.configure(api_key=GEMINI_API_KEY)

BKASH_NUMBER = "01315-815599"
ADMIN_SECRET_KEY = "admin786" # রেজিস্ট্রেশনের সময় এটি দিলে অ্যাডমিন হওয়া যাবে

conn = sqlite3.connect('infinity_master_v12.db', check_same_thread=False)
c = conn.cursor()

def init_db():
    c.execute('CREATE TABLE IF NOT EXISTS library (id INTEGER PRIMARY KEY, name TEXT, playlist_id TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, user_email TEXT, v_id TEXT, note_content TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, username TEXT, password TEXT, sub_end TEXT, role TEXT, points INTEGER)')
    c.execute('CREATE TABLE IF NOT EXISTS playlist_names (id INTEGER PRIMARY KEY, user_email TEXT, name TEXT, target_date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS videos (id INTEGER PRIMARY KEY, playlist_id INTEGER, title TEXT, v_id TEXT, status TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS notices (id INTEGER PRIMARY KEY, msg TEXT, date TEXT)')
    conn.commit()

init_db()

# --- ৪. হেল্পার ফাংশনসমূহ ---
def load_lottieurl(url):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code != 200: return None
        return r.json()
    except: return None

def hash_pass(password): 
    return hashlib.sha256(str.encode(password)).hexdigest()

lottie_hero = load_lottieurl("https://lottie.host/e8c894b9-0870-4966-9538-4e0e227a94f6/D9wUf1R3eI.json")

# --- ৫. প্রিমিয়াম সিএসএস স্টাইল (Mobile & Desktop Optimized) ---
st.markdown("""
    <style>
    /* ১. গ্লোবাল ব্যাকগ্রাউন্ড ও ফন্ট (Bengali Support added) */
    @import url('https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;600;700&family=Inter:wght@400;700&display=swap');

    .stApp { 
        background: radial-gradient(circle at top right, #0f172a, #020617); 
        color: #e2e8f0;
        font-family: 'Hind Siliguri', 'Inter', sans-serif;
    }
    
    /* ২. গ্লাস-কার্ড ইফেক্ট (Glassmorphism) */
    .glass-card { 
        background: rgba(30, 41, 59, 0.5); 
        backdrop-filter: blur(12px); 
        border-radius: 16px; 
        padding: clamp(15px, 4vw, 25px); /* মোবাইলে প্যাডিং অটো কমবে */
        border: 1px solid rgba(255,255,255,0.08); 
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        margin-bottom: 20px; 
        transition: 0.3s ease-in-out;
    }
    .glass-card:hover {
        transform: translateY(-5px);
        border: 1px solid rgba(59, 130, 246, 0.4);
    }

    /* ৩. আধুনিক বাটন ডিজাইন (Touch Optimized for Phone) */
    .stButton>button { 
        background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%); 
        border: none; 
        color: white; 
        border-radius: 12px; 
        padding: 12px 20px; /* ফোনে ক্লিক করতে সহজ হবে */
        font-weight: 600; 
        width: 100%; 
        transition: all 0.3s ease; 
    }
    .stButton>button:hover { 
        box-shadow: 0 8px 25px rgba(37,99,235,0.4); 
    }

    /* ৪. রেসপনসিভ হিরো টেক্সট */
    .hero-text { 
        font-size: clamp(28px, 8vw, 60px); /* ফোনের স্ক্রিন অনুযায়ী ফন্ট ছোট-বড় হবে */
        font-weight: 900; 
        background: linear-gradient(to bottom right, #ffffff 30%, #3b82f6 100%);
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent; 
        line-height: 1.2;
        margin-bottom: 15px;
    }

    /* ৫. মোবাইল রেসপনসিভ এডজাস্টমেন্ট */
    @media (max-width: 768px) {
        .stMain {
            padding: 10px !important;
        }
        /* কলামগুলোকে মোবাইলে স্ট্যাক (একটির নিচে একটি) করা */
        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
        }
        /* মেট্রিক বা ছোট কার্ডের গ্যাপ কমানো */
        div[data-testid="stMetric"] {
            background: rgba(255,255,255,0.05);
            padding: 10px;
            border-radius: 10px;
        }
    }

    /* ৬. ইনপুট বক্স স্টাইল */
    .stTextInput>div>div>input, .stSelectbox>div>div>div {
        background-color: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: white !important;
        border-radius: 10px !important;
    }

    /* ৭. হাইড স্ক্রলবার (ক্লিন লুকের জন্য) */
    ::-webkit-scrollbar {
        display: none;
    }
    </style>
""", unsafe_allow_html=True)
# -----------------------------------
# --- ৬. ল্যান্ডিং পেজ (Premium Landing Page) ---
if not st.session_state.logged_in and st.session_state.page == 'landing':
    # ১. হিরো সেকশন
    col_t1, col_t2 = st.columns([1.2, 1])
    
    with col_t1:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<h1 class='hero-text'>Unlock Your <br>Future with <br>Infinity Study</h1>", unsafe_allow_html=True)
        st.write("✨ **ইউটিউব লার্নিংকে করুন গ্যামিফাইড এবং এআই চালিত।**")
        st.markdown("""
            <p style='color: #94a3b8; font-size: 16px;'>
            আপনার প্রিয় ইউটিউব প্লেলিস্টগুলো থেকে শিখুন গুছিয়ে। লক্ষ্য সেট করুন, 
            প্রতিদিন প্রগ্রেস ট্র্যাক করুন এবং এআই নোটের মাধ্যমে পড়াশোনা করুন আরও সহজে।
            </p>
        """, unsafe_allow_html=True)
        
        # কল টু অ্যাকশন বাটন
        if st.button("Get Started Now 🚀", use_container_width=False):
            st.session_state.page = 'auth'
            st.rerun()
            
    with col_t2:
        if lottie_hero:
            from streamlit_lottie import st_lottie
            st_lottie(lottie_hero, height=450, key="hero_anim")
        else:
            # যদি লটি না থাকে তবে একটি সুন্দর ইমেজ বা গ্যাপ
            st.markdown("<br><br><br>", unsafe_allow_html=True)
            st.image("https://img.freepik.com/free-vector/online-education-concept_52683-37307.jpg", use_container_width=True)

    # ২. স্ট্যাটিসটিক্স বা ট্রাস্ট সেকশন (Retention এর জন্য)
    st.markdown("<br><br>", unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("সফল ইউজার", "৫০০০+", "🔥")
    m2.metric("কোর্স লাইব্রেরি", "৫০০+", "📚")
    m3.metric("এআই সামারি", "১০k+", "🤖")
    m4.metric("সফলতা রেট", "৯৮%", "✅")

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: white;'>কেন Infinity Study Pro সেরা?</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #3b82f6;'>আমাদের বিশেষ ফিচারগুলো যা আপনাকে এগিয়ে রাখবে</p>", unsafe_allow_html=True)

    # ৩. ফিচার কার্ড সেকশন (Glassmorphism Layout)
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("""
            <div class='glass-card'>
                <h3 style='font-size: 20px;'>🎯 Daily Target</h3>
                <p style='color: #cbd5e1; font-size: 14px;'>নিজের পড়ার লক্ষ্য নিজে সেট করুন এবং প্রতিদিনের উন্নতি ট্র্যাক করুন ক্যালেন্ডারের মাধ্যমে।</p>
                <span class='category-tag'>Disciplined Learning</span>
            </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
            <div class='glass-card'>
                <h3 style='font-size: 20px;'>🤖 AI Notes</h3>
                <p style='color: #cbd5e1; font-size: 14px;'>বড় ভিডিও দেখে সময় নষ্ট নয়! এআই এর মাধ্যমে ভিডিওর মূল পয়েন্টগুলো বাংলা সামারি আকারে পান।</p>
                <span class='category-tag'>Smart Study</span>
            </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown("""
            <div class='glass-card'>
                <h3 style='font-size: 20px;'>🔥 Study Streaks</h3>
                <p style='color: #cbd5e1; font-size: 14px;'>ধারাবাহিকতা বজায় রেখে পয়েন্ট জিতুন এবং লিডারবোর্ডে সবার উপরে নিজের নাম দেখুন।</p>
                <span class='category-tag'>Gamified</span>
            </div>
        """, unsafe_allow_html=True)

    # ৪. ফুটার সেকশন
    st.markdown("<br><br><hr>", unsafe_allow_html=True)
    st.markdown("""
        <div style='text-align: center; color: #64748b; padding-bottom: 20px;'>
            © 2026 Infinity Study Pro - Empowering Learners Globally 🌍
        </div>
    """, unsafe_allow_html=True)
# --- ৭. অথেন্টিকেশন পেজ (Final Bug-Free Pro Design) ---
elif not st.session_state.logged_in and st.session_state.page == 'auth':
    
    # ব্যাক বাটন
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("← Back to Home", key="back_home_final"):
        st.session_state.page = 'landing'
        st.rerun()

    # প্রো-লেভেল CSS (বক্স সমস্যা ফিক্সড)
    st.markdown("""
        <style>
            /* পুরো পেজের কন্টেইনারকে সুন্দর করা */
            [data-testid="stVerticalBlock"] > div:has(div.stTabs) {
                background: rgba(255, 255, 255, 0.03);
                backdrop-filter: blur(15px);
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                padding: 40px;
                max-width: 500px;
                margin: 0 auto;
                box-shadow: 0 15px 35px rgba(0, 0, 0, 0.5);
            }
            
            /* ইনপুট বক্সের প্যাডিং ও ডিজাইন */
            .stTextInput { margin-top: -15px; }
            
            .stTextInput input {
                background-color: rgba(0, 0, 0, 0.3) !important;
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                border-radius: 12px !important;
                color: white !important;
                height: 45px;
            }

            /* শিরোনামের স্টাইল */
            .main-title {
                text-align: center;
                background: linear-gradient(to right, #3b82f6, #8b5cf6);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-size: 3.5rem;
                font-weight: bold;
                margin-bottom: 0px;
            }
            .sub-title {
                text-align: center;
                color: #888;
                margin-bottom: 30px;
            }
        </style>
    """, unsafe_allow_html=True)

    # শিরোনাম (সরাসরি মার্কডাউন, কোনো div ছাড়া)
    st.markdown("<h1 class='main-title'>My Learning</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>আপনার ভবিষ্যৎ গড়ার সঙ্গী</p>", unsafe_allow_html=True)
    
    # ট্যাব সিস্টেম (এটিই এখন মেইন কার্ড হিসেবে কাজ করবে)
    tab_login, tab_reg = st.tabs(["🔐 Login", "📝 Register"])
    
    with tab_login:
        st.markdown("<br>", unsafe_allow_html=True)
        # ইমেইল ও পাসওয়ার্ড
        le = st.text_input("ইমেইল", placeholder="example@mail.com", key="pro_l_email", label_visibility="collapsed")
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        lp = st.text_input("পাসওয়ার্ড", type='password', placeholder="••••••••", key="pro_l_pass", label_visibility="collapsed")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Get Started 🚀", use_container_width=True, type="primary"):
            if le and lp:
                c.execute('SELECT * FROM users WHERE email=? AND password=?', (le, hash_pass(lp)))
                user = c.fetchone()
                if user:
                    st.session_state.update({'logged_in': True, 'user': user})
                    st.success("স্বাগতম!")
                    st.rerun()
                else: 
                    st.error("ভুল ইমেইল বা পাসওয়ার্ড!")
            else:
                st.warning("তথ্য দিন।")

    with tab_reg:
        st.markdown("<br>", unsafe_allow_html=True)
        re = st.text_input("নতুন ইমেইল", placeholder="Email address", key="pro_r_email", label_visibility="collapsed")
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        ru = st.text_input("ইউজারনেম", placeholder="Your Full Name", key="pro_r_user", label_visibility="collapsed")
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        rp = st.text_input("পাসওয়ার্ড", type='password', placeholder="Min 6 characters", key="pro_r_pass", label_visibility="collapsed")
        
        with st.expander("🔑 Admin Code (Optional)"):
            secret = st.text_input("সিক্রেট কোড", type='password', key="pro_r_secret")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Create Account ✨", use_container_width=True):
            if re and ru and rp:
                try:
                    role = 'admin' if secret == ADMIN_SECRET_KEY else 'user'
                    trial = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
                    c.execute('INSERT INTO users VALUES (?,?,?,?,?,?)', (re, ru, hash_pass(rp), trial, role, 0))
                    conn.commit()
                    st.success("একাউন্ট তৈরি হয়েছে! লগইন করুন।")
                except: 
                    st.error("ইমেইলটি অলরেডি আছে।")
# -----------------------------------
# --- ৮. মেইন অ্যাপ লজিক (Logged In) ---
# -----------------------------------
elif st.session_state.logged_in:
    # ডাটাবেস থেকে লেটেস্ট ইউজার ডাটা রিফ্রেশ করা
    c.execute('SELECT * FROM users WHERE email=?', (st.session_state.user[0],))
    u_data = c.fetchone()
    
    with st.sidebar:
        st.markdown(f"### 👋 স্বাগতম, <br><span style='color:#3b82f6'>{u_data[1]}</span>", unsafe_allow_html=True)
        menu_options = ["Dashboard", "My Courses", "Gain More Skill", "Completed", "Add Course", "Payment"]
        menu_icons = ["house", "play-circle", "rocket", "check-circle", "plus-circle", "wallet"]
        if u_data[4] == 'admin':
            menu_options.append("Admin Panel")
            menu_icons.append("gear")

        selected = option_menu(None, menu_options, icons=menu_icons, default_index=0)
        if st.button("Logout"): 
            st.session_state.update({'logged_in': False, 'user': None, 'page': 'landing'})
            st.rerun()

    # --- ১. Dashboard (Course-wise Deadline & Progress) ---
    if selected == "Dashboard":
        from datetime import datetime
        import urllib.parse

        st.markdown(f"<h2 style='font-family: \"Hind Siliguri\", sans-serif;'>🚀 আপনার লার্নিং ড্যাশবোর্ড</h2>", unsafe_allow_html=True)
        
        # --- ১. ডাটাবেস কলাম চেক এবং অটো-প্যাচ ---
        try:
            c.execute("SELECT target_days FROM playlist_names LIMIT 1")
        except:
            c.execute("ALTER TABLE playlist_names ADD COLUMN target_days INTEGER DEFAULT 30")
            conn.commit()

        # --- ২. নোটিশ বোর্ড ---
        c.execute("SELECT * FROM notices ORDER BY id DESC LIMIT 1")
        notice = c.fetchone()
        if notice:
            st.markdown(f"""
                <div style='background: rgba(59, 130, 246, 0.1); border-left: 5px solid #3b82f6; padding: 15px; border-radius: 12px; margin-bottom: 25px;'>
                    <strong style='color: #60a5fa;'>📢 নোটিশ ({notice[2]}):</strong> {notice[1]}
                </div>
            """, unsafe_allow_html=True)

        # --- ৩. স্ট্যাটাস কার্ডস ---
        c.execute("SELECT COUNT(*) FROM playlist_names WHERE user_email=?", (u_data[0],))
        total_crs = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM videos WHERE playlist_id IN (SELECT id FROM playlist_names WHERE user_email=?) AND status='Done'", (u_data[0],))
        done_vids = c.fetchone()[0]

        m1, m2, m3 = st.columns(3)
        m1.markdown(f"<div class='glass-card' style='text-align:center;'>পয়েন্ট<h2 style='color:#f59e0b;'>✨ {done_vids * 10}</h2></div>", unsafe_allow_html=True)
        m2.markdown(f"<div class='glass-card' style='text-align:center;'>চলমান কোর্স<h2 style='color:#3b82f6;'>📚 {total_crs}</h2></div>", unsafe_allow_html=True)
        m3.markdown(f"<div class='glass-card' style='text-align:center;'>ভিডিও দেখা<h2 style='color:#10b981;'>🎬 {done_vids}</h2></div>", unsafe_allow_html=True)

        st.markdown("<h3 style='margin-top:20px; font-family: \"Hind Siliguri\";'>📅 কোর্স ভিত্তিক লক্ষ্য ও অগ্রগতি</h3>", unsafe_allow_html=True)

        # --- ৪. কোর্স লিস্ট এবং ডেইজ লেফট লজিক ---
        # আমরা target_days এবং target_date দুটোই হ্যান্ডেল করছি যেন এরর না আসে
        c.execute("SELECT id, name, target_days FROM playlist_names WHERE user_email=?", (u_data[0],))
        my_courses = c.fetchall()

        if not my_courses:
            st.info("আপনার কোনো কোর্স ইনরোল করা নেই।")
        else:
            for crs in my_courses:
                c_id, c_name, t_days = crs
                
                # প্রগ্রেস ক্যালকুলেশন
                c.execute("SELECT COUNT(*) FROM videos WHERE playlist_id=?", (c_id,))
                total_v = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM videos WHERE playlist_id=? AND status='Done'", (c_id,))
                done_v = c.fetchone()[0]
                prog = (done_v / total_v) if total_v > 0 else 0

                # দিন বাকি থাকার হিসাব (নিরাপদ চেক)
                days_left = t_days if isinstance(t_days, int) else 30
                border_color = "#3b82f6" if days_left > 5 else "#ef4444"
                
                st.markdown(f"""
                    <div class='glass-card' style='border-left: 6px solid {border_color}; padding: 20px; margin-bottom: 5px;'>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <h4 style='margin:0; font-family: "Hind Siliguri";'>📘 {c_name}</h4>
                            <span style='background: rgba(255,255,255,0.1); padding: 5px 12px; border-radius: 20px; font-weight: bold; color: {border_color};'>
                                ⏳ {days_left} দিন বাকি
                            </span>
                        </div>
                        <p style='color: #94a3b8; font-size: 13px; margin-top: 8px;'>সম্পন্ন: {done_v}/{total_v} ভিডিও</p>
                    </div>
                """, unsafe_allow_html=True)
                st.progress(prog)
                st.markdown("<br>", unsafe_allow_html=True)

            # --- ৫. WhatsApp Sharing ---
            st.markdown("---")
            msg = f"🎓 *আমার লার্নিং রিপোর্ট*\n\n✅ ভিডিও সম্পন্ন: {done_vids}\n🏆 মোট পয়েন্ট: {done_vids * 10}\n📚 চলমান কোর্স: {total_crs}\n\n_Infinity Study Pro AI থেকে পাঠানো হয়েছে_"
            encoded_msg = urllib.parse.quote(msg)
            
            st.markdown(f"""
                <div style='text-align:center;'>
                    <a href="https://wa.me/?text={encoded_msg}" target="_blank" style="text-decoration: none;">
                        <button style='background-color: #25D366; color: white; border: none; padding: 12px 25px; border-radius: 10px; cursor: pointer; font-weight: bold; font-family: "Hind Siliguri"; font-size: 16px;'>
                            📲 WhatsApp-এ প্রগতি শেয়ার করুন
                        </button>
                    </a>
                </div>
            """, unsafe_allow_html=True)
    # --- ২. My Courses ---
    elif selected == "My Courses":
        st.header("📺 চলমান স্টাডি জোন")
        c.execute("SELECT * FROM playlist_names WHERE user_email=?", (u_data[0],))
        all_courses = c.fetchall()
        
        running_courses = []
        for crs in all_courses:
            c.execute("SELECT COUNT(*), SUM(CASE WHEN status='Done' THEN 1 ELSE 0 END) FROM videos WHERE playlist_id=?", (crs[0],))
            tot, dn = c.fetchone()
            if tot > 0 and (dn or 0) < tot: running_courses.append(crs)

        if running_courses:
            col_v, col_ai = st.columns([2, 1])
            with col_v:
                sel_cn = st.selectbox("কোর্স সিলেক্ট", [crs[2] for crs in running_courses])
                cid = [crs[0] for crs in running_courses if crs[2] == sel_cn][0]
                
                c.execute("SELECT * FROM videos WHERE playlist_id=?", (cid,))
                vids = c.fetchall()
                
                default_index = 0
                for i, v in enumerate(vids):
                    if v[4] == 'Pending':
                        default_index = i
                        break
                
                titles = [f"{'✅' if v[4]=='Done' else '⏳'} {v[2]}" for v in vids]
                sel_v = st.selectbox("ভিডিও সিলেক্ট করুন", titles, index=default_index)
                v_data = vids[titles.index(sel_v)]
                
                st.video(f"https://www.youtube.com/watch?v={v_data[3]}")
                
                if st.button("✅ মার্ক ডান ও পরের ভিডিও"):
                    c.execute("UPDATE videos SET status='Done' WHERE id=?", (v_data[0],))
                    conn.commit()
                    st.session_state.done_today += 1
                    st.success(f"সাবাস! '{v_data[2]}' শেষ হয়েছে।")
                    st.rerun()
            
            with col_ai:
                st.markdown("<div class='glass-card'><h4>🤖 AI Summary</h4>", unsafe_allow_html=True)
                if st.button("Generate Summary"):
                    try:
                        with st.spinner("এআই সামারি জেনারেট করছে..."):
                            transcript = YouTubeTranscriptApi.get_transcript(v_data[3], languages=['bn', 'en'])
                            text = " ".join([t['text'] for t in transcript])
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            res = model.generate_content(f"Summarize in Bengali: {text[:8000]}")
                            st.markdown(f"<div style='background:rgba(255,255,255,0.05); padding:10px; border-radius:5px;'>{res.text}</div>", unsafe_allow_html=True)
                    except: st.error("সাবটাইটেল পাওয়া যায়নি।")
                st.markdown("</div>", unsafe_allow_html=True)

                st.markdown("<div class='glass-card'><h4>📝 Study Notes</h4>", unsafe_allow_html=True)
                c.execute("SELECT note_content FROM notes WHERE user_email=? AND v_id=?", (u_data[0], v_data[3]))
                note_res = c.fetchone()
                saved_note = note_res[0] if note_res else ""

                user_note = st.text_area("নোট লিখুন:", value=saved_note, height=150, key=f"nt_{v_data[3]}")
                if st.button("Save Note 💾"):
                    if note_res:
                        c.execute("UPDATE notes SET note_content=? WHERE user_email=? AND v_id=?", (user_note, u_data[0], v_data[3]))
                    else:
                        c.execute("INSERT INTO notes (user_email, v_id, note_content) VALUES (?,?,?)", (u_data[0], v_data[3], user_note))
                    conn.commit(); st.success("সেভ হয়েছে!"); st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
        else: st.info("আপনার সব কোর্স শেষ!")

# --- ৩. Gain More Skill (Advanced Details & Custom Target) ---
    elif selected == "Gain More Skill":
        import yt_dlp
        from datetime import datetime, timedelta
        st.header("🚀 নতুন দক্ষতা অর্জন করুন")
        
        # ১. ক্যাটাগরি মেনু (Interactive Dropdown)
        c.execute("SELECT DISTINCT category FROM library WHERE category IS NOT NULL AND category != ''")
        fetched_cats = [row[0] for row in c.fetchall()]
        category_list = ["All Courses"] + fetched_cats
        sel_cat = st.selectbox("📂 ক্যাটাগরি অনুযায়ী ফিল্টার করুন", category_list, index=0)

        st.markdown("---")

        # ২. ডাটাবেস থেকে ডাটা আনা
        if sel_cat == "All Courses":
            c.execute("SELECT id, name, playlist_id, category FROM library")
        else:
            c.execute("SELECT id, name, playlist_id, category FROM library WHERE category=?", (sel_cat,))
        
        db_library_courses = c.fetchall()

        c.execute("SELECT name FROM playlist_names WHERE user_email=?", (u_data[0],))
        enrolled_course_names = [row[0] for row in c.fetchall()]

        if not db_library_courses:
            st.warning(f"'{sel_cat}' ক্যাটাগরিতে বর্তমানে কোনো কোর্স নেই।")
        else:
            for course in db_library_courses:
                is_already_enrolled = course[1] in enrolled_course_names
                p_id_raw = str(course[2]).strip()
                clean_p_id = p_id_raw.split("list=")[-1].split("&")[0] if "list=" in p_id_raw else p_id_raw

                # কার্ড লেআউট
                col_n, col_p, col_b = st.columns([2, 1.2, 1])
                
                with col_n:
                    st.markdown(f"""
                        <div style='background: linear-gradient(135deg, rgba(59,130,246,0.1) 0%, rgba(255,255,255,0.05) 100%); 
                                    padding: 18px; border-radius: 12px; border-left: 6px solid #3b82f6;'>
                            <h4 style='margin:0; font-size: 16px; color: white;'>📘 {course[1]}</h4>
                            <p style='margin:0; font-size: 11px; color: #3b82f6; font-weight: bold;'># {course[3] if course[3] else 'Skill'}</p>
                        </div>
                    """, unsafe_allow_html=True)

                with col_p:
                    # ৩. কোর্স আওয়ার এবং ভিডিও ডিটেইলস
                    with st.popover("📖 Course Info", use_container_width=True):
                        try:
                            with st.spinner("অ্যানালাইজ করা হচ্ছে..."):
                                ydl_opts = {'quiet': True, 'extract_flat': 'in_playlist', 'skip_download': True}
                                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                                    info = ydl.extract_info(f"https://www.youtube.com/playlist?list={clean_p_id}", download=False)
                                    v_count = len(info.get('entries', []))
                                    # আনুমানিক সময় বের করা (গড়ে প্রতিটি ভিডিও ১৫ মিনিট ধরে)
                                    total_minutes = v_count * 15 
                                    total_hours = total_minutes // 60
                                    remaining_mins = total_minutes % 60

                            st.subheader("🎯 কোর্সের বিস্তারিত")
                            st.write(f"🎬 **মোট ভিডিও:** {v_count} টি")
                            st.write(f"⏳ **মোট সময়:** প্রায় {total_hours} ঘণ্টা {remaining_mins} মিনিট")
                            st.caption("(গড় ভিডিও ডিউরেশন ১৫ মিনিট হিসেবে)")
                            
                            st.divider()
                            st.markdown(f"**📜 ডেসক্রিপশন:**\n{info.get('description', 'নেই।')[:250]}...")
                        except:
                            st.error("ডাটা পাওয়া যায়নি।")

                with col_b:
                    if is_already_enrolled:
                        st.button("Enrolled ✅", key=f"en_{course[0]}", disabled=True, use_container_width=True)
                    else:
                        # --- 🔄 Target Set Description with Calendar ---
                        with st.popover("Enroll 🚀", use_container_width=True):
                            st.markdown("### 🎯 Your Learning Goal")
                            st.write("🔥 **নিজেকের চ্যালেঞ্জ করুন!**")
                            st.write("একটি নির্দিষ্ট টার্গেট ডেট সেট করলে আপনার শেখার গতি **৩ গুণ** বেড়ে যায়।")
                            st.info("📅 নিচে ক্যালেন্ডার থেকে একটি তারিখ বেছে নিন, যেদিন আপনি এই কোর্সটি সফলভাবে শেষ করতে চান।")
                            
                            # কাস্টম টার্গেট ডেট (Calendar)
                            target_date = st.date_input(
                                "টার্গেট ডেট সিলেক্ট করুন",
                                value=datetime.now() + timedelta(days=30),
                                min_value=datetime.now() + timedelta(days=1),
                                key=f"date_{course[0]}"
                            )
                            
                            # দিন ক্যালকুলেশন
                            days_left = (target_date - datetime.now().date()).days
                            
                            st.markdown(f"""
                                <div style='background-color: rgba(59, 130, 246, 0.1); padding: 10px; border-radius: 8px; border: 1px dashed #3b82f6;'>
                                    <p style='margin:0; text-align:center; font-weight:bold;'>⌛ আপনি {days_left} দিনের চ্যালেঞ্জ নিচ্ছেন!</p>
                                </div>
                            """, unsafe_allow_html=True)
                            st.write("") # Space

                            if st.button("চ্যালেঞ্জ শুরু করুন 🏁", key=f"btn_{course[0]}", use_container_width=True):
                                try:
                                    c.execute("INSERT INTO playlist_names (user_email, name, playlist_id, target_days) VALUES (?, ?, ?, ?)", 
                                             (u_data[0], course[1], clean_p_id, days_left))
                                    conn.commit()
                                    st.success(f"অভিনন্দন! আপনার {days_left} দিনের মিশন শুরু হলো।")
                                    st.balloons()
                                    st.rerun()
                                except:
                                    c.execute("INSERT INTO playlist_names (user_email, name, playlist_id) VALUES (?, ?, ?)", 
                                             (u_data[0], course[1], clean_p_id))
                                    conn.commit()
                                    st.rerun()

                st.markdown("<div style='margin-bottom:15px;'></div>", unsafe_allow_html=True)
    # --- ৪. Add Course ---
    elif selected == "Add Course":
        st.header("➕ নতুন প্লেলিস্ট যুক্ত করুন")
        with st.form("add_form", clear_on_submit=True):
            cn, cu, td = st.text_input("কোর্সের নাম"), st.text_input("প্লেলিস্ট লিঙ্ক"), st.date_input("টার্গেট ডেট")
            if st.form_submit_button("সেভ করুন"):
                if "list=" in cu:
                    with st.spinner("সিঙ্ক হচ্ছে..."):
                        with yt_dlp.YoutubeDL({'extract_flat': True, 'quiet': True}) as ydl:
                            items = ydl.extract_info(cu, download=False).get('entries', [])
                        c.execute("INSERT INTO playlist_names (user_email, name, target_date) VALUES (?,?,?)", (u_data[0], cn, str(td)))
                        pid = c.lastrowid
                        for v in items: c.execute("INSERT INTO videos (playlist_id, title, v_id, status) VALUES (?,?,?,?)", (pid, v.get('title'), v.get('id'), 'Pending'))
                        conn.commit(); st.success("যুক্ত হয়েছে!"); st.rerun()
                else: st.error("সঠিক লিঙ্ক দিন।")

    # --- ৫. Payment ---
    elif selected == "Payment":
        st.header("💳 সাবস্ক্রিপশন ও পেমেন্ট")
        st.info(f"📅 আপনার বর্তমান মেয়াদের শেষ তারিখ: {u_data[3]}")
        
        col_pay1, col_pay2 = st.columns(2, gap="large")
        with col_pay1:
            st.markdown(f"""
                <div class='glass-card'>
                    <h3 style='color:#3b82f6;'>কেন প্রিমিয়াম নেবেন?</h3>
                    <ul style='line-height: 1.8;'>
                        <li>✅ আনলিমিটেড কোর্স ইউটিউব থেকে সিঙ্ক করুন।</li>
                        <li>✅ AI দিয়ে ভিডিওর বাংলা সামারি তৈরি করুন।</li>
                        <li>✅ ডেইলি টার্গেট এবং স্ট্রিক ট্র্যাকিং।</li>
                        <li>✅ আজীবন আপনার স্টাডি ডাটা সেভ থাকবে।</li>
                    </ul>
                    <hr>
                    <p>ফি: <b>৳৩০ / মাস</b></p>
                </div>
            """, unsafe_allow_html=True)

        with col_pay2:
            wa_number = "8801607733041"
            wa_text = f"Hi Admin, I have paid 30 TK for Infinity Pro. Please approve my email: {u_data[0]}"
            wa_link = f"https://wa.me/{wa_number}?text={wa_text.replace(' ', '%20')}"
            
            st.markdown(f"""
                <div class='glass-card'>
                    <h3 style='color:#10b981;'>বিকাশ (Payment)</h3>
                    <h2 style='letter-spacing: 2px;'>{BKASH_NUMBER}</h2>
                    <p>টাকা পাঠিয়ে নিচের বাটনে ক্লিক করে অ্যাডমিনকে জানান।</p>
                    <a href="{wa_link}" target="_blank" style="text-decoration: none;">
                        <div style="background-color: #25D366; color: white; padding: 15px; border-radius: 10px; text-align: center; font-weight: bold; font-size: 18px; cursor: pointer; box-shadow: 0 4px 10px rgba(0,0,0,0.2);">
                            💬 পেমেন্ট কনফার্ম করুন (WhatsApp)
                        </div>
                    </a>
                </div>
            """, unsafe_allow_html=True)

# --- ৬. Admin Panel (Premium UI with Separated Category Option) ---
    elif selected == "Admin Panel":
        if u_data[4] == 'admin': 
            st.title("👑 এডমিন কন্ট্রোল সেন্টার")
            
            # ডাটাবেস অটো-প্যাচ
            try:
                c.execute("ALTER TABLE library ADD COLUMN category TEXT")
                conn.commit()
            except: pass

            # --- কুইক স্ট্যাটাস কার্ডস ---
            col_st1, col_st2, col_st3 = st.columns(3)
            c.execute("SELECT COUNT(*) FROM users")
            total_users = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM library")
            total_courses = c.fetchone()[0]
            
            col_st1.metric("মোট ইউজার", f"{total_users} জন", "👤")
            col_st2.metric("মোট কোর্স", f"{total_courses} টি", "📚")
            col_st3.metric("সার্ভার স্ট্যাটাস", "Active", "✅")

            st.markdown("---")

            tab1, tab2, tab3 = st.tabs(["📢 নোটিশ বোর্ড", "👤 ইউজার কন্ট্রোল", "⚙️ কোর্স ম্যানেজমেন্ট"])
            
            # --- ট্যাব ১: নোটিশ ম্যানেজমেন্ট ---
            with tab1:
                st.subheader("📢 গ্লোবাল নোটিশ আপডেট")
                with st.expander("বর্তমান নোটিশ দেখুন"):
                    c.execute("SELECT msg FROM notices")
                    current_msg = c.fetchone()
                    st.info(current_msg[0] if current_msg else "কোনো নোটিশ নেই।")

                new_notice = st.text_area("নতুন নোটিশ লিখুন", height=100)
                if st.button("🚀 পাবলিশ করুন", use_container_width=True):
                    c.execute("DELETE FROM notices")
                    c.execute("INSERT INTO notices (msg, date) VALUES (?,?)", 
                             (new_notice, datetime.now().strftime("%d %b, %Y")))
                    conn.commit()
                    st.success("নোটিশ আপডেট হয়েছে!")
                    st.rerun()

            # --- ট্যাব ২: ইউজার ম্যানেজমেন্ট ---
            with tab2:
                st.subheader("👤 ইউজার সাবস্ক্রিপশন")
                u_col1, u_col2 = st.columns([2, 1])
                with u_col1:
                    target_email = st.text_input("ইউজার ইমেইল")
                with u_col2:
                    days_to_add = st.number_input("মেয়াদ যোগ (দিন)", min_value=1, value=30)
                
                if st.button("✅ মেয়াদ আপডেট করুন", use_container_width=True):
                    c.execute('SELECT sub_end FROM users WHERE email=?', (target_email,))
                    if c.fetchone():
                        new_exp = (datetime.now() + timedelta(days=days_to_add)).strftime("%Y-%m-%d")
                        c.execute('UPDATE users SET sub_end=? WHERE email=?', (new_exp, target_email))
                        conn.commit()
                        st.success(f"আপডেট সফল: {new_exp}")
                    else: st.error("ইউজার পাওয়া যায়নি।")
                
                st.dataframe(pd.read_sql_query("SELECT email, username, sub_end, role FROM users", conn), use_container_width=True)

            # --- ট্যাব ৩: কোর্স ম্যানেজমেন্ট (Updated Layout) ---
            with tab3:
                st.subheader("⚙️ লাইব্রেরি কন্ট্রোল")
                
                # ডায়নামিক ক্যাটাগরি লিস্ট
                c.execute("SELECT DISTINCT category FROM library WHERE category IS NOT NULL AND category != ''")
                existing_cats = [row[0] for row in c.fetchall()]
                default_cats = ["Programming", "Web Dev", "Design", "Marketing"]
                final_cat_list = sorted(list(set(existing_cats + default_cats)))

                with st.form("add_course_form", clear_on_submit=True):
                    st.info("নতুন কোর্স যোগ করার ফর্ম")
                    l_name = st.text_input("📘 কোর্সের নাম")
                    l_pid_raw = st.text_input("🆔 ইউটিউব প্লেলিস্ট লিঙ্ক/আইডি")
                    
                    # বিদ্যমান ক্যাটাগরি ড্রপডাউন
                    l_cat_select = st.selectbox("🏷️ বিদ্যমান ক্যাটাগরি থেকে বেছে নিন", final_cat_list)
                    
                    st.markdown("---")
                    # নতুন ক্যাটাগরি যোগ করার অপশন আলাদা নিচে
                    st.markdown("**✨ আপনি কি নতুন কোনো ক্যাটাগরি তৈরি করতে চান?**")
                    l_cat_custom = st.text_input("✍️ নতুন ক্যাটাগরির নাম লিখুন (নিচে লিখলে ওপরের সিলেকশন কাজ করবে না)")
                    
                    if st.form_submit_button("➕ লাইব্রেরিতে যুক্ত করুন", use_container_width=True):
                        # লজিক: কাস্টম বক্সে কিছু থাকলে সেটিই ক্যাটাগরি হবে
                        final_cat = l_cat_custom.strip() if l_cat_custom.strip() != "" else l_cat_select
                        
                        if l_name and l_pid_raw:
                            l_pid = l_pid_raw.split("list=")[-1].split("&")[0] if "list=" in l_pid_raw else l_pid_raw
                            c.execute("INSERT INTO library (name, playlist_id, category) VALUES (?,?,?)", (l_name, l_pid, final_cat))
                            conn.commit()
                            st.success(f"'{l_name}' সফলভাবে '{final_cat}' ক্যাটাগরিতে যুক্ত হয়েছে!")
                            st.rerun()
                        else:
                            st.error("⚠️ নাম এবং আইডি সঠিক ভাবে দিন।")
                
                st.markdown("---")
                # বর্তমান কোর্স লিস্ট
                lib_df = pd.read_sql_query("SELECT id, name as 'Course', category as 'Category' FROM library", conn)
                st.dataframe(lib_df, use_container_width=True)
                
                # ডিলিট সেকশন
                with st.expander("🗑️ কোর্স ডিলিট করুন"):
                    d_id = st.number_input("মুছে ফেলতে কোর্সের ID লিখুন", min_value=1, step=1, key="del_box")
                    if st.button("নিশ্চিত ডিলিট", type="primary", use_container_width=True):
                        c.execute("DELETE FROM library WHERE id=?", (d_id,))
                        conn.commit()
                        st.warning("কোর্সটি ডিলিট করা হয়েছে।")
                        st.rerun()
        else:
            st.error("🚫 আপনার এডমিন এক্সেস নেই।")
    # --- ৭. Completed ---
    elif selected == "Completed":
        st.header("🏆 সম্পন্ন করা কোর্সসমূহ")
        c.execute("SELECT * FROM playlist_names WHERE user_email=?", (u_data[0],))
        any_done = False
        for crs in c.fetchall():
            c.execute("SELECT COUNT(*), SUM(CASE WHEN status='Done' THEN 1 ELSE 0 END) FROM videos WHERE playlist_id=?", (crs[0],))
            tot, dn = c.fetchone()
            if tot > 0 and dn == tot:
                any_done = True
                st.markdown(f"<div class='glass-card'><h3>🎓 {crs[2]}</h3><p>অভিনন্দন! আপনি এই কোর্সটি সফলভাবে শেষ করেছেন।</p></div>", unsafe_allow_html=True)
        if not any_done:
            st.info("এখনো কোনো কোর্স সম্পন্ন হয়নি। পড়াশোনা চালিয়ে যান!")