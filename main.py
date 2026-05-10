import requests
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime

# ================= SERVER =================

SERVER = "https://attendance-system-xdlp.onrender.com"

# ================= APP =================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.geometry("1100x700")
app.title("מערכת נוכחות מקצועית")

main_frame = ctk.CTkFrame(app)
main_frame.pack(fill="both", expand=True)

sidebar = ctk.CTkFrame(main_frame, width=200)
sidebar.pack(side="left", fill="y")

content = ctk.CTkFrame(main_frame)
content.pack(side="right", fill="both", expand=True)

# ================= עובדים =================

def load_employees():

    for w in content.winfo_children():
        w.destroy()

    ctk.CTkLabel(content, text="עובדים", font=("Arial", 28)).pack(pady=10)

    try:
        res = requests.get(SERVER + "/employees")
        rows = res.json()

        for r in rows:

            frame = ctk.CTkFrame(content)
            frame.pack(pady=5, fill="x")

            name = r[1]

            ctk.CTkLabel(frame, text=f"{name} | ₪{r[2]} ({r[3]})").pack(side="left", padx=10)

            ctk.CTkButton(frame, text="כניסה", command=lambda n=name: clock_in(n)).pack(side="left")
            ctk.CTkButton(frame, text="יציאה", command=lambda n=name: clock_out(n)).pack(side="left")

    except:
        messagebox.showerror("שגיאה", "אין חיבור לשרת")

# ================= הוספת עובד =================

def show_add_employee():

    for w in content.winfo_children():
        w.destroy()

    global name_entry, salary_entry, salary_type_var

    ctk.CTkLabel(content, text="הוספת עובד", font=("Arial", 28)).pack(pady=10)

    name_entry = ctk.CTkEntry(content, placeholder_text="שם")
    name_entry.pack(pady=5)

    salary_entry = ctk.CTkEntry(content, placeholder_text="שכר")
    salary_entry.pack(pady=5)

    salary_type_var = ctk.StringVar(value="שעתי")

    ctk.CTkOptionMenu(content, values=["שעתי", "יומי"], variable=salary_type_var).pack(pady=5)

    ctk.CTkButton(content, text="שמור", command=add_employee).pack(pady=10)

def add_employee():

    try:
        requests.post(SERVER + "/add_employee", json={
            "name": name_entry.get(),
            "salary": float(salary_entry.get()),
            "salary_type": salary_type_var.get()
        })

        messagebox.showinfo("בוצע", "עובד נוסף")

    except:
        messagebox.showerror("שגיאה", "אין חיבור לשרת")

# ================= נוכחות =================

def clock_in(name):
    try:
        requests.post(SERVER + "/clock_in", json={"name": name})
    except:
        messagebox.showerror("שגיאה", "אין חיבור לשרת")

def clock_out(name):
    try:
        requests.post(SERVER + "/clock_out", json={"name": name})
    except:
        messagebox.showerror("שגיאה", "אין חיבור לשרת")

# ================= דשבורד =================

def show_dashboard():

    for w in content.winfo_children():
        w.destroy()

    try:
        employees = requests.get(SERVER + "/employees").json()

        ctk.CTkLabel(content, text="דשבורד", font=("Arial", 28)).pack(pady=10)
        ctk.CTkLabel(content, text=f"סה״כ עובדים: {len(employees)}").pack(pady=10)

    except:
        messagebox.showerror("שגיאה", "אין חיבור לשרת")

# ================= SIDEBAR =================

ctk.CTkButton(sidebar, text="דשבורד", command=show_dashboard).pack(pady=10)
ctk.CTkButton(sidebar, text="עובדים", command=load_employees).pack(pady=10)
ctk.CTkButton(sidebar, text="הוספת עובד", command=show_add_employee).pack(pady=10)

# ================= START =================

load_employees()
app.mainloop()