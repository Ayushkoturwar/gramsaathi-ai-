import streamlit as st, sqlite3, hashlib, hmac, os, re
from pathlib import Path
DB=Path(__file__).with_name("gramsaathi.db")
def db():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def hp(p,s=None):
 s=s or os.urandom(16); d=hashlib.pbkdf2_hmac("sha256",p.encode(),s,200000); return s.hex()+"$"+d.hex()
def verify(p,x):
 try:
  s,d=x.split("$"); return hmac.compare_digest(hp(p,bytes.fromhex(s)).split("$")[1],d)
 except:return False
def init():
 with db() as c:
  c.executescript("""CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,username TEXT UNIQUE,password TEXT);
  CREATE TABLE IF NOT EXISTS schemes(id INTEGER PRIMARY KEY,name TEXT,name_mr TEXT,category TEXT,description TEXT,eligibility TEXT,documents TEXT,steps TEXT,keywords TEXT,source TEXT,verified TEXT,active INTEGER DEFAULT 1);
  CREATE TABLE IF NOT EXISTS feedback(id INTEGER PRIMARY KEY,rating INTEGER,message TEXT,created DATETIME DEFAULT CURRENT_TIMESTAMP);
  CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,actor TEXT,action TEXT,created DATETIME DEFAULT CURRENT_TIMESTAMP);""")
  if not c.execute("SELECT 1 FROM users WHERE username='admin'").fetchone(): c.execute("INSERT INTO users(username,password) VALUES(?,?)",("admin",hp("GramSaathi@2026")))
  if c.execute("SELECT COUNT(*) n FROM schemes").fetchone()["n"]==0:
   rows=[
   ("PM-KISAN","पीएम-किसान","Farmer","Farmer income-support information. Verify current rules on the official portal.","Subject to current official eligibility and exclusions.","Aadhaar, bank and land/registration details as currently required.","Check eligibility and current application/e-KYC instructions on the official portal.","farmer kisan agriculture sheti शेतकरी किसान खेती","https://pmkisan.gov.in/","2026-10-28"),
   ("National Scholarship Portal","राष्ट्रीय शिष्यवृत्ती पोर्टल","Student","Scholarship discovery/application portal; each scholarship has separate rules.","Depends on the current scholarship notification.","Identity, academic, bank and scheme-specific documents.","Choose a scholarship and follow its current official guidelines.","student scholarship college विद्यार्थी शिष्यवृत्ती छात्रवृत्ति","https://scholarships.gov.in/","2026-10-28"),
   ("Ayushman Bharat PM-JAY","आयुष्मान भारत पीएम-जय","Health","Public health assurance information; verify beneficiary status officially.","Determined by current PM-JAY beneficiary rules/data.","Identity and beneficiary documents requested by the official service.","Verify through official PM-JAY channels or an authorized facility.","health hospital medical ayushman आरोग्य स्वास्थ्य अस्पताल","https://pmjay.gov.in/","2026-10-28")]
   c.executemany("INSERT INTO schemes(name,name_mr,category,description,eligibility,documents,steps,keywords,source,verified) VALUES(?,?,?,?,?,?,?,?,?,?)",rows)
init()
st.set_page_config(page_title="GRAMSAATHI AI",page_icon="🌾",layout="wide")
st.markdown("""<style>.block-container{max-width:1100px}.hero{padding:25px;border:1px solid #ddd;border-radius:20px}</style><div class=hero><h1>🌾 GRAMSAATHI AI</h1><h3>आपला आवाज • आपली भाषा • आपल्या सरकारी सेवा</h3><p>Verified-record-first citizen service prototype</p></div>""",unsafe_allow_html=True)
if "admin" not in st.session_state: st.session_state.admin=False
lang=st.sidebar.selectbox("Language / भाषा",["मराठी","हिंदी","English"])
page=st.sidebar.radio("Menu",["🏠 Assistant","📚 Schemes","📝 Feedback","🔐 Admin"])
def schemes(all=False):
 with db() as c:return [dict(x) for x in c.execute("SELECT * FROM schemes"+("" if all else " WHERE active=1")+" ORDER BY id DESC")]
def card(s):
 with st.expander(("📌 "+(s["name_mr"] if lang=="मराठी" else s["name"])),expanded=True):
  st.write(s["description"]); st.markdown("**Eligibility / पात्रता**");st.write(s["eligibility"]);st.markdown("**Documents / कागदपत्रे**");st.write(s["documents"]);st.markdown("**Next steps / पुढील पावले**");st.write(s["steps"]);st.caption("Prototype verified date: "+s["verified"]);st.link_button("Official source ↗",s["source"])
def toks(x):return set(re.findall(r"[\w\u0900-\u097F]+",x.lower()))
if page=="🏠 Assistant":
 st.header("Ask GRAMSAATHI")
 q=st.text_area("तुमचा प्रश्न / Your question",placeholder="उदा. मी विद्यार्थी आहे, मला scholarship हवी आहे.")
 if st.button("🔍 Find guidance",type="primary"):
  q=q.strip()[:500]
  if not q:st.warning("Please enter a question.")
  else:
   qq=toks(q); ranked=[]
   for s in schemes():
    score=len(qq&toks(" ".join([s["name"],s["name_mr"],s["category"],s["keywords"]])))
    if score:ranked.append((score,s))
   ranked.sort(key=lambda x:x[0],reverse=True)
   if not ranked:st.warning("No verified local record matched. Try: farmer, scholarship, student, health.")
   else:
    st.success("Possible relevant scheme(s). Final eligibility must be confirmed from the official source.")
    for _,s in ranked[:3]:card(s)
elif page=="📚 Schemes":
 st.header("Verified local scheme directory")
 for s in schemes():card(s)
elif page=="📝 Feedback":
 st.header("Feedback");r=st.slider("Rating",1,5,5);m=st.text_area("Message")
 if st.button("Save feedback"):
  with db() as c:c.execute("INSERT INTO feedback(rating,message) VALUES(?,?)",(r,m[:1000]))
  st.success("Saved locally.")
else:
 st.header("Admin Panel")
 if not st.session_state.admin:
  with st.form("login"):
   u=st.text_input("Username");p=st.text_input("Password",type="password");go=st.form_submit_button("Login")
  if go:
   with db() as c:x=c.execute("SELECT * FROM users WHERE username=?",(u[:100],)).fetchone()
   if x and verify(p,x["password"]):st.session_state.admin=True;st.rerun()
   else:st.error("Invalid login.")
  st.caption("Demo: admin / GramSaathi@2026 — change before public deployment.")
 else:
  if st.button("Logout"):st.session_state.admin=False;st.rerun()
  rows=schemes(True);st.metric("Total scheme records",len(rows))
  with st.form("add"):
   n=st.text_input("Scheme name");nm=st.text_input("Marathi name");cat=st.selectbox("Category",["Farmer","Student","Health","Women","Senior Citizen","Other"]);d=st.text_area("Description");e=st.text_area("Eligibility");doc=st.text_area("Documents");steps=st.text_area("Next steps");keys=st.text_input("Keywords");src=st.text_input("Official HTTPS source");vd=st.date_input("Verified date");add=st.form_submit_button("Add scheme")
  if add:
   if not n or not nm or not src.startswith("https://"):st.error("Names and HTTPS official source are required.")
   else:
    with db() as c:c.execute("INSERT INTO schemes(name,name_mr,category,description,eligibility,documents,steps,keywords,source,verified) VALUES(?,?,?,?,?,?,?,?,?,?)",(n[:200],nm[:200],cat,d[:3000],e[:3000],doc[:3000],steps[:3000],keys[:1000],src[:1000],str(vd)))
    st.success("Added.");st.rerun()
  st.subheader("Manage records")
  for s in rows:
   a,b=st.columns([6,1]);a.write(f"{s['name']} — {'Active' if s['active'] else 'Inactive'}")
   if b.button("Toggle",key=s["id"]):
    with db() as c:c.execute("UPDATE schemes SET active=CASE active WHEN 1 THEN 0 ELSE 1 END WHERE id=?",(s["id"],))
    st.rerun()
st.sidebar.caption("Prototype: answers are limited to locally managed records. Verify current rules at official sources.")
