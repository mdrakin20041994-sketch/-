# বন্ধুর বন্ধন সমিতি লিমিটেড — Supabase সংস্করণ

এই Flask ওয়েব অ্যাপে অ্যাডমিন ও সদস্য লগইন, সদস্য বায়োডাটা, মাসিক নির্ধারিত ২,০০০ টাকা জমা, বকেয়া হিসাব এবং CSV রিপোর্ট রয়েছে। অ্যাপের ডেটা Supabase PostgreSQL-এ রাখা হয়; একই ডেটাবেসে যুক্ত সব ডিভাইস একই তথ্য পাবে।

## ১) Supabase ডেটাবেস তৈরি

1. Supabase Dashboard খুলুন: https://supabase.com/dashboard
2. আপনার প্রজেক্টের **SQL Editor → New query** খুলুন।
3. এই ZIP-এর `supabase_setup.sql` ফাইলের সব কোড পেস্ট করে **Run** করুন।
4. এটি `app_users` এবং `member_deposits` নামে দুটি টেবিল তৈরি করবে। আগের `members`, `deposits`, `expenses` টেবিল মুছে ফেলবে না।

## ২) Database connection string নিন

1. Supabase-এ **Project Settings → Database** খুলুন।
2. **Connection string** অংশে URI/connection string দেখুন। প্রয়োজনে Session pooler ব্যবহার করুন।
3. এই সংযোগ স্ট্রিং-এ আপনার ডেটাবেস পাসওয়ার্ড থাকবে। এটি কাউকে চ্যাটে পাঠাবেন না এবং GitHub/সর্বজনীন জায়গায় রাখবেন না।
4. হোস্টিং সার্ভারের environment variable হিসেবে `DATABASE_URL` সেট করুন। উদাহরণ:
   `postgresql://postgres:YOUR_DB_PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres?sslmode=require`
   আপনার Dashboard-এ প্রদর্শিত আসল URI-টাই ব্যবহার করবেন; উপরেরটি শুধু নমুনা।

**গুরুত্বপূর্ণ:** এই Flask সংস্করণে Supabase publishable key ব্যবহার করা হয় না। সার্ভার থেকে PostgreSQL-এ সংযোগের জন্য `DATABASE_URL` প্রয়োজন। Database password/connection string গোপন রাখুন।

## ৩) নিজের কম্পিউটারে পরীক্ষা

Python 3.10+ ইনস্টল করুন। প্রজেক্ট ফোল্ডারে টার্মিনাল খুলে:

Windows PowerShell:
```powershell
py -m venv .venv
.venv\\Scripts\\Activate.ps1
py -m pip install -r requirements.txt
$env:DATABASE_URL="আপনার Supabase connection string"
$env:SECRET_KEY="একটি দীর্ঘ র‍্যান্ডম গোপন মান"
py app.py
```

তারপর ব্রাউজারে `http://127.0.0.1:5000/setup` খুলুন। প্রথম অ্যাডমিন অ্যাকাউন্ট তৈরি করুন। অ্যাডমিন পাসওয়ার্ড কমপক্ষে ১২ অক্ষরের হতে হবে।

## ৪) অনলাইনে প্রকাশ

যে কোনো Python/Flask hosting-এ অ্যাপটি প্রকাশ করা যাবে। হোস্টিংয়ের environment variables-এ অন্তত এগুলো সেট করুন:

- `DATABASE_URL` — Supabase-এর গোপন PostgreSQL connection string
- `SECRET_KEY` — দীর্ঘ, র‍্যান্ডম, গোপন মান
- `PRODUCTION=1`
- `COOKIE_SECURE=1`
- `SETUP_TOKEN` — প্রথম অ্যাডমিন তৈরির জন্য আলাদা দীর্ঘ গোপন token

প্রকাশের পর HTTPS চালু রাখুন। `/setup`-এ প্রথম অ্যাডমিন তৈরির সময় `SETUP_TOKEN` ফর্মে দিতে হবে। অ্যাডমিন তৈরি হয়ে গেলে `/setup` আর ব্যবহারযোগ্য থাকবে না।

## নিরাপত্তা ও সীমাবদ্ধতা

- `DATABASE_URL` কখনো ব্রাউজারের JavaScript, HTML, GitHub বা চ্যাটে দেবেন না। `service_role` key-ও প্রয়োজন নেই।
- এই সংস্করণে Flask সার্ভার সরাসরি PostgreSQL-এ যুক্ত হয়। তাই database connection string শুধু সার্ভারের environment variable-এ থাকবে।
- অ্যাপটি এখনো নিজে থেকে প্রকাশিত/হোস্ট করা হয়নি; শুধু Supabase-ready সোর্স কোড তৈরি হয়েছে।
- এই প্রাথমিক সংস্করণে লগইন রেট-লিমিট, পাসওয়ার্ড রিসেট, পূর্ণ নিরাপত্তা অডিট এবং ব্যাকআপ পুনরুদ্ধার ব্যবস্থা অন্তর্ভুক্ত নয়। বাস্তব জাতীয় পরিচয়পত্র বা সংবেদনশীল তথ্য যোগ করার আগে নিরাপত্তা পর্যালোচনা করুন।
- মাসিক জমার পরিমাণ কোডে `MONTHLY = 2000` হিসেবে নির্ধারিত।
