import os
import json
import requests
import google.generativeai as genai

# 1. إعدادات موقعك (غيّر الرابط لرابط موقعك)
WP_API_URL = "https://gardensnursery.com/wp-json/wp/v2/posts?per_page=1"
HISTORY_FILE = "published_posts.txt"

# استدعاء المفاتيح السرية من إعدادات GitHub
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

def get_latest_post():
    response = requests.get(WP_API_URL, timeout=15)
    posts = response.json()
    if not posts:
        return None
    post = posts[0]
    return {
        "id": str(post["id"]),
        "title": post["title"]["rendered"],
        "url": post["link"],
        "excerpt": post["excerpt"]["rendered"][:1000]
    }

def is_already_sent(post_id):
    if not os.path.exists(HISTORY_FILE):
        return False
    with open(HISTORY_FILE, "r") as f:
        return post_id in f.read().splitlines()

def mark_as_sent(post_id):
    with open(HISTORY_FILE, "a") as f:
        f.write(post_id + "\n")

def generate_social_content(post):
    prompt = f"""
    أنت خبير تسويق إلكتروني وسيو (SEO). بناءً على المقال التالي، اكتب لي حزمة نشر جاهزة باللغة الإنجليزية (أو لغة المقال):
    العنوان: {post['title']}
    الرابط: {post['url']}
    المقتطف: {post['excerpt']}

    المطلوب تنسيق الرد بوضوح في 4 أقسام قصيرة جاهزة للنسخ واللصق:
    1. منشور فيسبوك (جذاب بدون رابط داخل النص + الرابط كتعليق أول).
    2. تغريدة X / Threads (مختصرة مع هاشتاغات والرابط).
    3. وصف Pinterest (غني بالكلمات المفتاحية).
    4. مسودة رد احترافي للمنتديات (Reddit/Quora) يقدم نصيحة حقيقية ويذكر الرابط كمصدر إضافي بدون سبام.
    """
    response = model.generate_content(prompt)
    return response.text

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    # تقسيم الرسالة إذا كانت طويلة لتناسب حدود تيليجرام
    for i in range(0, len(message), 4000):
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message[i:i+4000]
        }
        requests.post(url, json=payload)

def main():
    post = get_latest_post()
    if not post:
        print("لا توجد مقالات.")
        return

    if is_already_sent(post["id"]):
        print("تمت معالجة هذا المقال مسبقاً.")
        return

    content = generate_social_content(post)
    header = f"🚀 مقال جديد جاهز للنشر والباكلينك!\n📌 {post['title']}\n🔗 {post['url']}\n\n"
    send_to_telegram(header + content)
    mark_as_sent(post["id"])
    print("تم الإرسال بنجاح!")

if __name__ == "__main__":
    main()
