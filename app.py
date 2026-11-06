import os, secrets, csv, io
import psycopg
from psycopg.rows import dict_row
from psycopg import errors
from datetime import date, datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort, Response
from werkzeug.security import generate_password_hash, check_password_hash

BASE = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError('Set DATABASE_URL to your Supabase Postgres connection string')

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
if os.environ.get('PRODUCTION') == '1' and not os.environ.get('SECRET_KEY'):
    raise RuntimeError('Set SECRET_KEY for production')
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', SESSION_COOKIE_SECURE=os.environ.get('COOKIE_SECURE') == '1', MAX_CONTENT_LENGTH=1024*1024)
MONTHLY = 2000

def conn():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=15)

def init_db():
    # Tables are created by running supabase_setup.sql in Supabase SQL Editor.
    with conn() as c:
        c.execute("SELECT 1 FROM public.app_users LIMIT 1")


def valid_month(m):
    try:
        return len(m)==7 and datetime.strptime(m,'%Y-%m').strftime('%Y-%m') == m
    except (ValueError, TypeError): return False

def month_count(start, end):
    if not valid_month(start) or not valid_month(end): return 0
    a,b=map(int,start.split('-')); x,y=map(int,end.split('-'))
    return max(0,(x-a)*12+y-b+1)

def csrf():
    if '_csrf' not in session: session['_csrf']=secrets.token_urlsafe(32)
    return session['_csrf']
app.jinja_env.globals['csrf_token']=csrf

@app.before_request
def protect():
    if request.method=='POST':
        if not secrets.compare_digest(request.form.get('_csrf',''),session.get('_csrf','')): abort(400,'Invalid security token')

@app.context_processor
def common(): return {'today_month':date.today().strftime('%Y-%m'),'monthly':MONTHLY,'production':os.environ.get('PRODUCTION') == '1'}

def login_required(role=None):
    def deco(fn):
        @wraps(fn)
        def inner(*args,**kwargs):
            if 'uid' not in session: return redirect(url_for('login'))
            if role and session.get('role')!=role: abort(403)
            return fn(*args,**kwargs)
        return inner
    return deco

def summary(c, user, through=None):
    through=through or date.today().strftime('%Y-%m')
    total=c.execute('SELECT COALESCE(SUM(amount),0) AS total FROM member_deposits WHERE member_id=%s',(user['id'],)).fetchone()['total']
    expected=MONTHLY*month_count(user['joined_month'],through)
    return {'total':total,'expected':expected,'due':max(0,expected-total),'credit':max(0,total-expected)}

@app.route('/')
def home():
    if 'uid' not in session: return redirect(url_for('login'))
    return redirect(url_for('admin') if session.get('role')=='admin' else url_for('my_account'))

@app.route('/setup',methods=['GET','POST'])
def setup():
    with conn() as c:
        if c.execute("SELECT 1 FROM app_users WHERE role='admin'").fetchone(): abort(404)
        if request.method=='POST':
            if os.environ.get('PRODUCTION') == '1' and (not os.environ.get('SETUP_TOKEN') or not secrets.compare_digest(request.form.get('setup_token',''), os.environ['SETUP_TOKEN'])):
                abort(403, 'Invalid setup token')
            name=request.form.get('name','').strip(); username=request.form.get('username','').strip(); password=request.form.get('password','')
            if not name or len(username)<3 or len(password)<12:
                flash('নাম, কমপক্ষে ৩ অক্ষরের ইউজারনেম এবং ১২ অক্ষরের পাসওয়ার্ড দিন।','error')
            else:
                try:
                    c.execute('INSERT INTO app_users(username,password_hash,role,full_name,joined_month) VALUES(%s,%s,%s,%s,%s)',(username,generate_password_hash(password),'admin',name,date.today().strftime('%Y-%m')))
                    flash('অ্যাডমিন অ্যাকাউন্ট তৈরি হয়েছে। লগইন করুন।','success')
                    return redirect(url_for('login'))
                except errors.UniqueViolation: flash('এই ইউজারনেম ব্যবহার করা হয়েছে।','error')
    return render_template('setup.html')

@app.route('/login',methods=['GET','POST'])
def login():
    with conn() as c:
        if not c.execute("SELECT 1 FROM app_users WHERE role='admin'").fetchone(): return redirect(url_for('setup'))
        if request.method=='POST':
            u=c.execute('SELECT * FROM app_users WHERE username=%s',(request.form.get('username','').strip(),)).fetchone()
            if u and check_password_hash(u['password_hash'],request.form.get('password','')):
                session.clear(); session['uid']=u['id']; session['role']=u['role']; session['name']=u['full_name']; csrf()
                return redirect(url_for('home'))
            flash('ইউজারনেম অথবা পাসওয়ার্ড সঠিক নয়।','error')
    return render_template('login.html')

@app.post('/logout')
@login_required()
def logout():
    session.clear(); return redirect(url_for('login'))

@app.route('/admin')
@login_required('admin')
def admin():
    with conn() as c:
        members=c.execute("SELECT * FROM app_users WHERE role='member' ORDER BY id DESC").fetchall()
        data=[{'user':m,**summary(c,m)} for m in members]
    return render_template('admin.html',members=data,total_due=sum(m['due'] for m in data),total_paid=sum(m['total'] for m in data))

@app.route('/admin/members/new',methods=['GET','POST'])
@login_required('admin')
def new_member():
    if request.method=='POST':
        f=request.form; username=f.get('username','').strip(); password=f.get('password',''); name=f.get('full_name','').strip(); joined=f.get('joined_month','')
        if not name or len(username)<3 or len(password)<8 or not valid_month(joined) or joined>date.today().strftime('%Y-%m'):
            flash('নাম, ইউজারনেম, কমপক্ষে ৮ অক্ষরের পাসওয়ার্ড এবং সঠিক যোগদানের মাস দিন।','error')
        else:
            try:
                with conn() as c:
                    c.execute('''INSERT INTO app_users(username,password_hash,role,full_name,father_name,mother_name,birth_date,phone,address,nid,joined_month) VALUES(%s,%s,'member',%s,%s,%s,%s,%s,%s,%s,%s)''',
                    (username,generate_password_hash(password),name,*(f.get(k,'').strip() for k in ('father_name','mother_name','birth_date','phone','address','nid')),joined))
                flash('সদস্য নিবন্ধিত হয়েছে। সদস্যকে লগইন তথ্য নিরাপদে দিন।','success')
                return redirect(url_for('admin'))
            except errors.UniqueViolation: flash('এই ইউজারনেম আগে থেকেই আছে।','error')
    return render_template('member_form.html',member=None)

@app.route('/admin/members/<int:member_id>/edit',methods=['GET','POST'])
@login_required('admin')
def edit_member(member_id):
    with conn() as c:
        m=c.execute("SELECT * FROM app_users WHERE id=%s AND role='member'",(member_id,)).fetchone()
        if not m: abort(404)
        if request.method=='POST':
            f=request.form; name=f.get('full_name','').strip(); joined=f.get('joined_month','')
            if not name or not valid_month(joined) or joined>date.today().strftime('%Y-%m'):
                flash('সঠিক নাম ও যোগদানের মাস দিন।','error')
            else:
                c.execute('''UPDATE app_users SET full_name=%s,father_name=%s,mother_name=%s,birth_date=%s,phone=%s,address=%s,nid=%s,joined_month=%s WHERE id=%s''',
                    (name,*(f.get(k,'').strip() for k in ('father_name','mother_name','birth_date','phone','address','nid')),joined,member_id))
                flash('তথ্য হালনাগাদ হয়েছে।','success'); return redirect(url_for('member_detail',member_id=member_id))
    return render_template('member_form.html',member=m)

@app.route('/admin/members/<int:member_id>',methods=['GET','POST'])
@login_required('admin')
def member_detail(member_id):
    with conn() as c:
        m=c.execute("SELECT * FROM app_users WHERE id=%s AND role='member'",(member_id,)).fetchone()
        if not m: abort(404)
        if request.method=='POST':
            month=request.form.get('month',''); note=request.form.get('note','').strip()[:300]
            try: amount=int(request.form.get('amount','0'))
            except ValueError: amount=0
            if not valid_month(month) or month<m['joined_month'] or month>date.today().strftime('%Y-%m') or not (1<=amount<=1000000):
                flash('সঠিক মাস ও জমার পরিমাণ দিন (১ থেকে ১০,০০,০০০ টাকা)।','error')
            else:
                c.execute('INSERT INTO member_deposits(member_id,month,amount,paid_at,note,created_by) VALUES(%s,%s,%s,%s,%s,%s)',(member_id,month,amount,date.today().isoformat(),note,session['uid']))
                flash('জমা সফলভাবে সংরক্ষণ করা হয়েছে।','success')
                return redirect(url_for('member_detail',member_id=member_id))
        deposits=c.execute('SELECT * FROM member_deposits WHERE member_id=%s ORDER BY month DESC,id DESC',(member_id,)).fetchall()
        totals=c.execute('SELECT month,SUM(amount) amount FROM member_deposits WHERE member_id=%s GROUP BY month ORDER BY month DESC',(member_id,)).fetchall()
        s=summary(c,m)
    return render_template('detail.html',member=m,deposits=deposits,totals=totals,s=s,is_admin=True)

@app.post('/admin/deposits/<int:deposit_id>/delete')
@login_required('admin')
def delete_deposit(deposit_id):
    with conn() as c:
        d=c.execute('SELECT member_id FROM member_deposits WHERE id=%s',(deposit_id,)).fetchone()
        if not d: abort(404)
        c.execute('DELETE FROM member_deposits WHERE id=%s',(deposit_id,))
    flash('ভুল জমার এন্ট্রি মুছে ফেলা হয়েছে।','success')
    return redirect(url_for('member_detail',member_id=d['member_id']))

@app.route('/account')
@login_required('member')
def my_account():
    with conn() as c:
        m=c.execute('SELECT * FROM app_users WHERE id=%s',(session['uid'],)).fetchone()
        deposits=c.execute('SELECT * FROM member_deposits WHERE member_id=%s ORDER BY month DESC,id DESC',(m['id'],)).fetchall()
        totals=c.execute('SELECT month,SUM(amount) amount FROM member_deposits WHERE member_id=%s GROUP BY month ORDER BY month DESC',(m['id'],)).fetchall()
        s=summary(c,m)
    return render_template('detail.html',member=m,deposits=deposits,totals=totals,s=s,is_admin=False)

@app.route('/password',methods=['GET','POST'])
@login_required()
def change_password():
    if request.method=='POST':
        with conn() as c:
            u=c.execute('SELECT password_hash FROM app_users WHERE id=%s',(session['uid'],)).fetchone()
            old=request.form.get('old',''); new=request.form.get('new','')
            if not check_password_hash(u['password_hash'],old) or len(new)<8:
                flash('বর্তমান পাসওয়ার্ড সঠিক দিন এবং নতুন পাসওয়ার্ড কমপক্ষে ৮ অক্ষরের দিন।','error')
            else:
                c.execute('UPDATE app_users SET password_hash=%s WHERE id=%s',(generate_password_hash(new),session['uid']))
                flash('পাসওয়ার্ড পরিবর্তন হয়েছে।','success'); return redirect(url_for('home'))
    return render_template('password.html')

@app.route('/admin/export.csv')
@login_required('admin')
def export_csv():
    out=io.StringIO(); w=csv.writer(out)
    w.writerow(['Member ID','Name','Username','Phone','Joined month','Expected BDT','Paid BDT','Due BDT','Credit BDT'])
    with conn() as c:
        for m in c.execute("SELECT * FROM app_users WHERE role='member' ORDER BY id").fetchall():
            s=summary(c,m); w.writerow([m['id'],m['full_name'],m['username'],m['phone'],m['joined_month'],s['expected'],s['total'],s['due'],s['credit']])
    return Response('\ufeff'+out.getvalue(),mimetype='text/csv; charset=utf-8',headers={'Content-Disposition':'attachment; filename=member_report.csv'})

init_db()

if __name__=='__main__':
    app.run(host='127.0.0.1',port=int(os.environ.get('PORT',5000)),debug=False)
