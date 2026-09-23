from __future__ import annotations
import os, sqlite3, uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from flask import Flask, jsonify, request, render_template

BASE=Path(__file__).parent
DB=Path(os.getenv("AMALORA_DB_PATH", BASE/"amalora.db"))
app=Flask(__name__)

def now(): return datetime.now(timezone.utc).isoformat(timespec="seconds")
def uid(p): return f"{p}_{uuid.uuid4().hex[:10]}"

@contextmanager
def db():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
    try: yield c; c.commit()
    finally: c.close()

def allrows(c,q,a=()): return [dict(x) for x in c.execute(q,a).fetchall()]
def onerow(c,q,a=()):
    x=c.execute(q,a).fetchone(); return dict(x) if x else None

def audit(c,action,etype,eid):
    c.execute("INSERT INTO audit_log VALUES(?,?,?,?,?,?)",(uid("aud"),request.headers.get("X-Amalora-Actor","demo.user"),action,etype,eid,now()))

def init():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,name TEXT,role TEXT,languages TEXT);
        CREATE TABLE IF NOT EXISTS patients(id TEXT PRIMARY KEY,mrn TEXT UNIQUE,full_name TEXT,dob TEXT,phone TEXT,email TEXT,preferred_language TEXT,balance REAL,created_at TEXT);
        CREATE TABLE IF NOT EXISTS appointments(id TEXT PRIMARY KEY,patient_id TEXT,clinician_id TEXT,service TEXT,resource TEXT,start_at TEXT,end_at TEXT,status TEXT,channel TEXT,payment_status TEXT,language TEXT,created_at TEXT);
        CREATE TABLE IF NOT EXISTS encounters(id TEXT PRIMARY KEY,patient_id TEXT,clinician_id TEXT,subjective TEXT,objective TEXT,assessment TEXT,plan TEXT,icd_codes TEXT,cpt_codes TEXT,status TEXT,created_at TEXT);
        CREATE TABLE IF NOT EXISTS invoices(id TEXT PRIMARY KEY,patient_id TEXT,total REAL,patient_share REAL,insurer_share REAL,status TEXT,created_at TEXT);
        CREATE TABLE IF NOT EXISTS claims(id TEXT PRIMARY KEY,invoice_id TEXT,insurer TEXT,preauth_status TEXT,claim_status TEXT,amount REAL,remittance REAL,rejection_reason TEXT,updated_at TEXT);
        CREATE TABLE IF NOT EXISTS inventory(id TEXT PRIMARY KEY,sku TEXT UNIQUE,name TEXT,category TEXT,qty REAL,reorder_level REAL,expiry_date TEXT,supplier TEXT);
        CREATE TABLE IF NOT EXISTS labs(id TEXT PRIMARY KEY,patient_id TEXT,clinician_id TEXT,test_name TEXT,barcode TEXT,status TEXT,result TEXT,approved_by TEXT,ordered_at TEXT);
        CREATE TABLE IF NOT EXISTS prescriptions(id TEXT PRIMARY KEY,patient_id TEXT,clinician_id TEXT,medication TEXT,dosage TEXT,frequency TEXT,duration TEXT,erx_status TEXT,dispense_status TEXT,created_at TEXT);
        CREATE TABLE IF NOT EXISTS telehealth(id TEXT PRIMARY KEY,appointment_id TEXT,identity_status TEXT,consent_status TEXT,device_status TEXT,room_status TEXT,join_token TEXT,created_at TEXT);
        CREATE TABLE IF NOT EXISTS notifications(id TEXT PRIMARY KEY,patient_id TEXT,channel TEXT,template_key TEXT,locale TEXT,status TEXT,scheduled_at TEXT,sent_at TEXT);
        CREATE TABLE IF NOT EXISTS integrations(id TEXT PRIMARY KEY,name TEXT,category TEXT,mode TEXT,status TEXT,notes TEXT);
        CREATE TABLE IF NOT EXISTS audit_log(id TEXT PRIMARY KEY,actor TEXT,action TEXT,entity_type TEXT,entity_id TEXT,created_at TEXT);
        """)
        if c.execute("SELECT COUNT(*) FROM users").fetchone()[0]==0:
            c.executemany("INSERT INTO users VALUES(?,?,?,?)",[("dr_mary","Dr. Mary","doctor","en,fa,ar"),("dr_larina","Dr. Larina","doctor","en,ru"),("reception","Reception","reception","en,ar")])
        if c.execute("SELECT COUNT(*) FROM patients").fetchone()[0]==0:
            c.executemany("INSERT INTO patients VALUES(?,?,?,?,?,?,?,?,?)",[("pat_1","AM-10001","Maya Hassan","1991-05-12","+971500000001","maya@example.com","ar",0,now()),("pat_2","AM-10002","Sara Rahimi","1988-11-03","+971500000002","sara@example.com","fa",350,now())])
        if c.execute("SELECT COUNT(*) FROM inventory").fetchone()[0]==0:
            c.executemany("INSERT INTO inventory VALUES(?,?,?,?,?,?,?,?)",[("stk_1","MED-BTX-01","Botulinum toxin vial","injectable",18,8,"2027-04-30","Demo Supplier"),("stk_2","CON-GLV-M","Nitrile gloves M","consumable",420,150,"2028-01-01","Demo Supplier")])
        if c.execute("SELECT COUNT(*) FROM integrations").fetchone()[0]==0:
            vals=[("int_nabidh","NABIDH","compliance","regulated_connector","blocked_credentials","Requires approved onboarding"),("int_malaffi","Malaffi","compliance","regulated_connector","blocked_credentials","Requires approved onboarding"),("int_riayati","Riayati","compliance","regulated_connector","blocked_credentials","Requires approved onboarding"),("int_eclaim","eClaimLink / Shafafiya","insurance","regulated_connector","blocked_credentials","Requires payer credentials"),("int_erx","eRx","clinical","regulated_connector","blocked_credentials","Requires approved eRx integration"),("int_wa","WhatsApp Business","messaging","adapter","not_configured","Templates/webhooks required"),("int_gcal","Google Calendar","calendar","adapter","not_configured","Two-way availability sync"),("int_pay","Payment Gateway","payment","adapter","not_configured","Tokenized payments/webhooks")]; c.executemany("INSERT INTO integrations VALUES(?,?,?,?,?,?)",vals)

@app.get("/")
def home(): return render_template("index.html")

@app.get("/health")
def health(): return jsonify(ok=True,service="Amalora Unified Clinic OS",time=now())

@app.get("/api/dashboard")
def dashboard():
    with db() as c:
        m={"patients":c.execute("SELECT COUNT(*) FROM patients").fetchone()[0],"upcoming":c.execute("SELECT COUNT(*) FROM appointments WHERE start_at>=? AND status!='cancelled'",(now(),)).fetchone()[0],"open_invoices":c.execute("SELECT COUNT(*) FROM invoices WHERE status!='paid'").fetchone()[0],"open_claims":c.execute("SELECT COUNT(*) FROM claims WHERE claim_status NOT IN ('paid','closed')").fetchone()[0],"low_stock":c.execute("SELECT COUNT(*) FROM inventory WHERE qty<=reorder_level").fetchone()[0],"pending_labs":c.execute("SELECT COUNT(*) FROM labs WHERE status NOT IN ('approved','cancelled')").fetchone()[0]}
        return jsonify(metrics=m)

@app.route("/api/patients",methods=["GET","POST"])
def patients():
    with db() as c:
        if request.method=="GET": return jsonify(allrows(c,"SELECT * FROM patients ORDER BY created_at DESC"))
        d=request.get_json(); pid=uid("pat"); mrn=d.get("mrn") or f"AM-{uuid.uuid4().hex[:6].upper()}"
        c.execute("INSERT INTO patients VALUES(?,?,?,?,?,?,?,?,?)",(pid,mrn,d["full_name"],d.get("dob"),d.get("phone"),d.get("email"),d.get("preferred_language","en"),float(d.get("balance",0)),now())); audit(c,"create","patient",pid)
        return jsonify(onerow(c,"SELECT * FROM patients WHERE id=?",(pid,))),201

@app.get("/api/clinicians")
def clinicians():
    with db() as c: return jsonify(allrows(c,"SELECT * FROM users WHERE role='doctor'"))

@app.route("/api/appointments",methods=["GET","POST"])
def appointments():
    with db() as c:
        if request.method=="GET":
            return jsonify(allrows(c,"SELECT a.*,p.full_name patient_name,u.name clinician_name FROM appointments a JOIN patients p ON p.id=a.patient_id JOIN users u ON u.id=a.clinician_id ORDER BY start_at DESC"))
        d=request.get_json(); start=datetime.fromisoformat(d["start_at"]); end=start+timedelta(minutes=int(d.get("duration_minutes",45)))
        hit=onerow(c,"SELECT id FROM appointments WHERE status NOT IN ('cancelled','no_show') AND start_at<? AND end_at>? AND (clinician_id=? OR (resource IS NOT NULL AND resource=?)) LIMIT 1",(end.isoformat(),start.isoformat(),d["clinician_id"],d.get("resource")))
        if hit: return jsonify(error="booking_conflict",conflict=hit),409
        aid=uid("apt"); c.execute("INSERT INTO appointments VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(aid,d["patient_id"],d["clinician_id"],d["service"],d.get("resource"),start.isoformat(),end.isoformat(),d.get("status","pending"),d.get("channel","web"),d.get("payment_status","unpaid"),d.get("language","en"),now()))
        c.execute("INSERT INTO notifications VALUES(?,?,?,?,?,?,?,?)",(uid("ntf"),d["patient_id"],d.get("notify_channel","in_app"),"appointment_"+d.get("status","pending"),d.get("language","en"),"queued",now(),None)); audit(c,"create","appointment",aid)
        return jsonify(onerow(c,"SELECT * FROM appointments WHERE id=?",(aid,))),201

@app.route("/api/encounters",methods=["GET","POST"])
def encounters():
    with db() as c:
        if request.method=="GET": return jsonify(allrows(c,"SELECT e.*,p.full_name patient_name,u.name clinician_name FROM encounters e JOIN patients p ON p.id=e.patient_id JOIN users u ON u.id=e.clinician_id ORDER BY created_at DESC"))
        d=request.get_json(); eid=uid("enc"); c.execute("INSERT INTO encounters VALUES(?,?,?,?,?,?,?,?,?,?,?)",(eid,d["patient_id"],d["clinician_id"],d.get("subjective"),d.get("objective"),d.get("assessment"),d.get("plan"),d.get("icd_codes"),d.get("cpt_codes"),d.get("status","draft"),now())); audit(c,"create","encounter",eid); return jsonify(onerow(c,"SELECT * FROM encounters WHERE id=?",(eid,))),201

@app.post("/api/ai/scribe")
def scribe():
    t=(request.get_json().get("transcript") or "").strip()
    if not t: return jsonify(error="transcript_required"),400
    s=[x.strip() for x in t.replace("\n"," ").split(".") if x.strip()]
    return jsonify(status="draft_requires_clinician_review",soap={"subjective":". ".join(s[:2])+("." if s else ""),"objective":"Clinician examination findings required.","assessment":"Draft placeholder — clinician must verify diagnosis and coding.","plan":"Clinician must confirm treatment plan before signing."},coding_suggestions=[],safety="Demo does not diagnose or auto-post.")

@app.route("/api/invoices",methods=["GET","POST"])
def invoices():
    with db() as c:
        if request.method=="GET": return jsonify(allrows(c,"SELECT i.*,p.full_name patient_name FROM invoices i JOIN patients p ON p.id=i.patient_id ORDER BY created_at DESC"))
        d=request.get_json(); iid=uid("inv"); total=float(d["total"]); ps=float(d.get("patient_share",total)); ins=float(d.get("insurer_share",total-ps)); c.execute("INSERT INTO invoices VALUES(?,?,?,?,?,?,?)",(iid,d["patient_id"],total,ps,ins,d.get("status","open"),now())); audit(c,"create","invoice",iid); return jsonify(onerow(c,"SELECT * FROM invoices WHERE id=?",(iid,))),201

@app.route("/api/claims",methods=["GET","POST"])
def claims():
    with db() as c:
        if request.method=="GET": return jsonify(allrows(c,"SELECT * FROM claims ORDER BY updated_at DESC"))
        d=request.get_json(); cid=uid("clm"); c.execute("INSERT INTO claims VALUES(?,?,?,?,?,?,?,?,?)",(cid,d["invoice_id"],d["insurer"],d.get("preauth_status","pending"),d.get("claim_status","draft"),float(d["amount"]),float(d.get("remittance",0)),d.get("rejection_reason"),now())); audit(c,"create","claim",cid); return jsonify(onerow(c,"SELECT * FROM claims WHERE id=?",(cid,))),201

@app.get("/api/inventory")
def inventory():
    with db() as c: return jsonify(allrows(c,"SELECT *,CASE WHEN qty<=reorder_level THEN 1 ELSE 0 END low_stock FROM inventory ORDER BY low_stock DESC,name"))

@app.route("/api/labs",methods=["GET","POST"])
def labs():
    with db() as c:
        if request.method=="GET": return jsonify(allrows(c,"SELECT l.*,p.full_name patient_name,u.name clinician_name FROM labs l JOIN patients p ON p.id=l.patient_id JOIN users u ON u.id=l.clinician_id ORDER BY ordered_at DESC"))
        d=request.get_json(); lid=uid("lab"); c.execute("INSERT INTO labs VALUES(?,?,?,?,?,?,?,?,?)",(lid,d["patient_id"],d["clinician_id"],d["test_name"],"AM"+uuid.uuid4().hex[:10].upper(),d.get("status","ordered"),d.get("result"),d.get("approved_by"),now())); audit(c,"create","lab",lid); return jsonify(onerow(c,"SELECT * FROM labs WHERE id=?",(lid,))),201

@app.route("/api/prescriptions",methods=["GET","POST"])
def prescriptions():
    with db() as c:
        if request.method=="GET": return jsonify(allrows(c,"SELECT rx.*,p.full_name patient_name,u.name clinician_name FROM prescriptions rx JOIN patients p ON p.id=rx.patient_id JOIN users u ON u.id=rx.clinician_id ORDER BY created_at DESC"))
        d=request.get_json(); rid=uid("rx"); c.execute("INSERT INTO prescriptions VALUES(?,?,?,?,?,?,?,?,?,?)",(rid,d["patient_id"],d["clinician_id"],d["medication"],d.get("dosage"),d.get("frequency"),d.get("duration"),d.get("erx_status","draft"),d.get("dispense_status","not_dispensed"),now())); audit(c,"create","prescription",rid); return jsonify(onerow(c,"SELECT * FROM prescriptions WHERE id=?",(rid,))),201

@app.route("/api/telehealth",methods=["GET","POST"])
def telehealth():
    with db() as c:
        if request.method=="GET": return jsonify(allrows(c,"SELECT * FROM telehealth ORDER BY created_at DESC"))
        d=request.get_json(); tid=uid("tel"); c.execute("INSERT INTO telehealth VALUES(?,?,?,?,?,?,?,?)",(tid,d["appointment_id"],d.get("identity_status","pending"),d.get("consent_status","pending"),d.get("device_status","pending"),d.get("room_status","scheduled"),uuid.uuid4().hex,now())); audit(c,"create","telehealth",tid); return jsonify(onerow(c,"SELECT * FROM telehealth WHERE id=?",(tid,))),201

@app.get("/api/notifications")
def notifications():
    with db() as c: return jsonify(allrows(c,"SELECT * FROM notifications ORDER BY scheduled_at DESC LIMIT 100"))

@app.get("/api/integrations")
def integrations():
    with db() as c: return jsonify(allrows(c,"SELECT * FROM integrations ORDER BY category,name"))

@app.get("/api/audit")
def audits():
    with db() as c: return jsonify(allrows(c,"SELECT * FROM audit_log ORDER BY created_at DESC LIMIT 200"))

@app.get("/api/compliance/registry")
def compliance():
    return jsonify(principle="No regulated submission is claimed until certified credentials and authority acceptance tests pass.",connectors=[{"name":"NABIDH","scope":"Dubai HIE","status":"adapter only"},{"name":"Malaffi","scope":"Abu Dhabi HIE","status":"adapter only"},{"name":"Riayati","scope":"Federal HIE","status":"adapter only"},{"name":"eClaimLink / Shafafiya","scope":"Insurance","status":"adapter only"},{"name":"eRx","scope":"Electronic prescription","status":"adapter only"}])

init()
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.getenv("PORT","5000")),debug=os.getenv("FLASK_DEBUG")=="1")
