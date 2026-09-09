import os
import csv
import json
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

CSV_PATH = "hr_contacts.csv"
RESUME_PATH = "resume2.pdf"
STATE_FILE = "state.json"

BATCH_SIZE = 2
DELAY_SECONDS = 2

SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
APP_PASSWORD = os.environ.get("APP_PASSWORD")

MESSAGE_TEMPLATE = '''Hi {hr_name},

I am reaching out to express my strong interest in Backend/Software Engineering opportunities at {company}. As a fourth-year B.Tech CSE student graduating in May 2027, I am actively seeking full-time roles as well as extended 6 to 12-month internships.

Most recently, I worked as a Backend Software Engineer Intern at VISA, where I was selected from over 440 applicants to engineer core, high-availability payment infrastructure handling 25,000+ Transactions Per Second (TPS). 

A quick summary of what I bring to the table:
🔹 Engineering at VISA: Architected fault-tolerant, event-driven payment pipelines and migrated legacy APIs to gRPC, successfully dropping latency by 60%.
🔹 Core Stack: Java (17/21), Spring Boot, Spring WebFlux, Microservices, and CQRS.
🔹 Distributed Systems: Built high-frequency trading engines and scalable e-commerce saga orchestrators using Kafka, Redis, and WebSockets.
🔹 Problem Solving: Deep foundation in DSA with 500+ LeetCode problems solved.

I have attached my resume for your reference. You can also explore my professional journey and projects here:
👉 LinkedIn: https://www.linkedin.com/in/keshav7029
👉 GitHub: https://github.com/Keshavgg

I would love the opportunity to bring my backend engineering skills to {company}. Are you available for a brief chat next week?

Best regards,

Keshav Jindal
+91 8368317466
keshav.jindal.7029@gmail.com'''

def get_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f).get("index", 200)
    return 200

def save_state(index):
    with open(STATE_FILE, "w") as f:
        json.dump({"index": index}, f)

def send_notification(server, subject, text):
    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = SENDER_EMAIL
        msg["Subject"] = subject
        msg.attach(MIMEText(text, "plain"))
        server.sendmail(SENDER_EMAIL, SENDER_EMAIL, msg.as_string())
    except Exception as e:
        print(f"Notification failed: {e}")

def main():
    if not SENDER_EMAIL or not APP_PASSWORD:
        print("Error: Missing SENDER_EMAIL or APP_PASSWORD env vars")
        return

    start_index = get_state()
    print(f"Starting from index: {start_index}")

    contacts = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            contacts.append(row)

    end_index = min(start_index + BATCH_SIZE, len(contacts))
    if start_index >= len(contacts):
        return

    resume_data = None
    if os.path.exists(RESUME_PATH):
        with open(RESUME_PATH, "rb") as f:
            resume_data = f.read()

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(SENDER_EMAIL, APP_PASSWORD)

    # 1. SEND START NOTIFICATION
    send_notification(server, 
                      f"🚀 HR Mailer: Batch Started (Index {start_index} to {end_index})", 
                      f"Hey Keshav,\n\nThe automation has woken up and is now sending a batch of {end_index - start_index} emails.\nStarting from index: {start_index}\nEnding at index: {end_index}\n\nYou will receive another email when this batch finishes.")

    success_count = 0
    for i in range(start_index, end_index):
        contact = contacts[i]
        hr_name = contact.get("name", "").split(" ")[0] or "Team"
        company = contact.get("company", "your company")
        target_email = contact.get("email", "").strip()

        if not target_email: continue

        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = target_email
        msg["Subject"] = f"Interest in Software Engineering/Internship Opportunities at {company}"
        msg.attach(MIMEText(MESSAGE_TEMPLATE.format(hr_name=hr_name, company=company), "plain"))

        if resume_data:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(resume_data)
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", "attachment; filename=resume2.pdf")
            msg.attach(part)

        try:
            server.sendmail(SENDER_EMAIL, target_email, msg.as_string())
            success_count += 1
            time.sleep(DELAY_SECONDS)
        except Exception as e:
            print(f"Failed to send to {target_email}: {e}")

    # 2. SEND END NOTIFICATION
    send_notification(server, 
                      f"✅ HR Mailer: Batch Completed (Index {end_index})", 
                      f"Hey Keshav,\n\nThe automation has successfully finished this batch!\nTotal emails sent this batch: {success_count}\n\nThe next batch will automatically start from Index {end_index} after 8 hours.\nDo not turn off your laptop/internet.")

    server.quit()
    save_state(end_index)

if __name__ == "__main__":
    main()
