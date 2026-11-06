# বন্ধুর বন্ধন সমিতি লিমিটেড — Supabase সংস্করণ

এই Flask ওয়েব অ্যাপে অ্যাডমিন ও সদস্য লগইন, সদস্য বায়োডাটা, মাসিক নির্ধারিত ২,০০০ টাকা জমা, বকেয়া হিসাব এবং CSV রিপোর্ট রয়েছে।

অ্যাপের ডেটা Supabase PostgreSQL-এ রাখা হয়। একই ডেটাবেসে যুক্ত সব ডিভাইস একই তথ্য দেখতে পারবে।

## ১) Supabase ডেটাবেস তৈরি

১. Supabase Dashboard খুলুন: https://supabase.com/dashboard

২. আপনার প্রজেক্টের **SQL Editor → New query** খুলুন।

৩. `supabase_setup.sql` ফাইলের সম্পূর্ণ কোড পেস্ট করে **Run** করুন।

৪. এটি `app_users` এবং `member_deposits` নামে দুটি টেবিল তৈরি করবে।

আগের `members`, `deposits`, `expenses` টেবিল মুছে ফেলা হবে না।

## ২) Database connection string নিন

১. Supabase-এ **Project Settings → Database** খুলুন।

২. **Connection string** অংশ থেকে URI/connection string সংগ্রহ করুন। প্রয়োজনে Session pooler ব্যবহার করুন।

৩. সংযোগ স্ট্রিংয়ে আপনার ডেটাবেস পাসওয়ার্ড থাকবে। এটি কাউকে চ্যাটে পাঠাবেন না এবং GitHub-এ রাখবেন না।

৪. হোস্টিং সার্ভারের Environment Variables-এ `DATABASE_URL` হিসেবে সেট করুন।

উদাহরণ:

`postgresql://postgres:YOUR_DB_PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres?sslmode=require`

উপরেরটি শুধু নমুনা। আপনার Supabase Dashboard-এ প্রদর্শিত আসল URI ব্যবহার করবেন।

**গুরুত্বপূর্ণ:** এই Flask সংস্করণে Supabase publishable key ব্যবহার করা হয় না। সার্ভার থেকে PostgreSQL-এ সংযোগের জন্য `DATABASE_URL` প্রয়োজন।

## ৩) নিজের কম্পিউটারে পরীক্ষা

প্রথমে Python 3.10 বা তার পরের সংস্করণ ইনস্টল করুন।

প্রজেক্ট ফোল্ডারে Windows PowerShell খুলুন।

**ধাপ ১ — Virtual environment তৈরি করুন**

```powershell
py -m venv .venv
```

**ধাপ ২ — Virtual environment চালু করুন**

```powershell
.venv\Scripts\Activate.ps1
```

PowerShell-এ স্ক্রিপ্ট চালানোর অনুমতি না থাকলে এই কমান্ড ব্যবহার করতে পারেন:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

তারপর আবার Activate কমান্ড চালান।

**ধাপ ৩ — প্রয়োজনীয় প্যাকেজ ইনস্টল করুন**

```powershell
py -m pip install -r requirements.txt
```

**ধাপ ৪ — Supabase Database URL সেট করুন**

```powershell
$env:DATABASE_URL="আপনার Supabase connection string"
```

**ধাপ ৫ — Secret Key সেট করুন**

```powershell
$env:SECRET_KEY="একটি দীর্ঘ র‍্যান্ডম গোপন মান"
```

**ধাপ ৬ — Flask অ্যাপ চালু করুন**

```powershell
py app.py
```

তারপর ব্রাউজারে খুলুন:

`http://127.0.0.1:5000/setup`

প্রথম অ্যাডমিন অ্যাকাউন্ট তৈরি করুন।

অ্যাডমিন পাসওয়ার্ড কমপক্ষে ১২ অক্ষরের হতে হবে।

## ৪) অনলাইনে প্রকাশ

যে কোনো উপযুক্ত Python/Flask hosting-এ অ্যাপটি প্রকাশ করা যাবে।

Render ব্যবহার করলে:

- Runtime: Python 3
- Build Command:

```bash
pip install -r requirements.txt
```

- Start Command:

```bash
gunicorn wsgi:app
```

`gunicorn` ব্যবহার করার জন্য `requirements.txt` ফাইলে নিচের লাইনটি যোগ করতে হবে:

```txt
gunicorn>=23.0,<24
```

### Render Environment Variables

Render-এর Web Service → Environment অংশে নিচের ভেরিয়েবলগুলো সেট করুন:

| Variable | Value |
|---|---|
| `DATABASE_URL` | Supabase PostgreSQL connection string |
| `SECRET_KEY` | দীর্ঘ র‍্যান্ডম গোপন মান |
| `PRODUCTION` | `1` |
| `COOKIE_SECURE` | `1` |
| `SETUP_TOKEN` | আলাদা দীর্ঘ গোপন সেটআপ কোড |

প্রকাশের পর HTTPS চালু রাখুন।

প্রথম অ্যাডমিন তৈরি করার সময় `/setup` পেজে `SETUP_TOKEN` দিতে হবে।

অ্যাডমিন তৈরি হয়ে গেলে `/setup` আর ব্যবহারযোগ্য থাকবে না।

## ৫) নিরাপত্তা ও সীমাবদ্ধতা

- `DATABASE_URL` কখনো ব্রাউজারের JavaScript, HTML, GitHub বা চ্যাটে প্রকাশ করবেন না।
- Supabase `service_role` key এই অ্যাপে প্রয়োজন নেই।
- Database password এবং `SECRET_KEY` গোপন রাখুন।
- এই Flask সংস্করণে সার্ভার সরাসরি PostgreSQL-এ যুক্ত হয়।
- অ্যাপটি নিজে থেকে প্রকাশিত বা হোস্ট করা হয়নি; হোস্টিং সেটআপ সম্পন্ন করতে হবে।
- এই প্রাথমিক সংস্করণে লগইন রেট-লিমিট, পাসওয়ার্ড রিসেট, পূর্ণ নিরাপত্তা অডিট এবং ব্যাকআপ পুনরুদ্ধার ব্যবস্থা অন্তর্ভুক্ত নয়।
- বাস্তব জাতীয় পরিচয়পত্র বা সংবেদনশীল তথ্য যোগ করার আগে নিরাপত্তা পর্যালোচনা করুন।
- মাসিক জমার পরিমাণ কোডে `MONTHLY = 2000` হিসেবে নির্ধারিত।


- মাসিক জমার পরিমাণ কোডে `MONTHLY = 2000` হিসেবে নির্ধারিত।
