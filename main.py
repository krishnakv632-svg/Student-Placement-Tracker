import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import hashlib
import secrets
import hmac
import csv
from datetime import datetime

current_admin = None

# =========================================================
# STUDENT PLACEMENT TRACKER - COMPLETE APPLICATION
# Existing database placement.db is preserved.
# =========================================================

conn = sqlite3.connect("placement.db")
cursor = conn.cursor()
cursor.execute("PRAGMA foreign_keys = ON")

cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    roll TEXT UNIQUE NOT NULL,
    branch TEXT NOT NULL,
    email TEXT NOT NULL,
    cgpa REAL NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    job_role TEXT NOT NULL,
    package REAL NOT NULL,
    eligibility_cgpa REAL NOT NULL,
    location TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS placements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL UNIQUE,
    company_id INTEGER,
    job_role TEXT,
    status TEXT NOT NULL CHECK(status IN ('Placed', 'Not Placed')),
    FOREIGN KEY(student_id) REFERENCES students(id),
    FOREIGN KEY(company_id) REFERENCES companies(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL
)
""")
conn.commit()

# ------------------------- WINDOW -------------------------

root = tk.Tk()
root.title("Student Placement Tracker")
root.geometry("1200x780")
root.minsize(980, 650)
root.configure(bg="#F1F5F9")

style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview", background="white", foreground="#172554",
                rowheight=29, fieldbackground="white", font=("Arial", 9))
style.configure("Treeview.Heading", background="#1E3A8A",
                foreground="white", font=("Arial", 9, "bold"))
style.configure("TCombobox", padding=5)

sidebar = tk.Frame(root, bg="#172554", width=235)
sidebar.pack_propagate(False)
main = tk.Frame(root, bg="#F1F5F9")
sidebar.pack_forget()
main.pack_forget()

# --------------------- COMMON FUNCTIONS -------------------

def clear_main():
    for widget in main.winfo_children():
        widget.destroy()

def page_title(title):
    tk.Label(main, text=title, font=("Arial", 22, "bold"),
             bg="#F1F5F9", fg="#172554").pack(anchor="w", padx=25, pady=18)

def create_button(parent, text, command, color="#2563EB"):
    return tk.Button(parent, text=text, command=command, bg=color, fg="white",
                     font=("Arial", 10, "bold"), relief="flat",
                     padx=14, pady=9, cursor="hand2",
                     activebackground="#1D4ED8", activeforeground="white")

def create_entry(parent, label):
    tk.Label(parent, text=label, font=("Arial", 10, "bold"),
             bg="#F1F5F9", fg="#172554").pack(anchor="w", padx=35, pady=(6, 2))
    entry = tk.Entry(parent, font=("Arial", 11), width=38)
    entry.pack(anchor="w", padx=35, ipady=4)
    return entry

def create_card(parent, title, value, color):
    card = tk.Frame(parent, bg="white", padx=12, pady=13,
                    highlightbackground="#E2E8F0", highlightthickness=1)
    card.pack(side="left", padx=7, pady=8, expand=True, fill="both")
    tk.Label(card, text=title, bg="white", fg="#64748B",
             font=("Arial", 9, "bold")).pack()
    tk.Label(card, text=str(value), bg="white", fg=color,
             font=("Arial", 19, "bold")).pack(pady=7)

def make_tree(parent, columns, widths=None, height=14):
    tree = ttk.Treeview(parent, columns=columns, show="headings", height=height)
    for i, col in enumerate(columns):
        tree.heading(col, text=col)
        tree.column(col, width=(widths[i] if widths else 130), anchor="center")
    return tree

def hash_password(password, salt):
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), 200000
    ).hex()

# ----------------------- AUTHENTICATION -------------------

def show_login():
    sidebar.pack_forget()
    main.pack_forget()
    for widget in root.winfo_children():
        if widget not in (sidebar, main):
            widget.destroy()

    frame = tk.Frame(root, bg="#F1F5F9")
    frame.pack(fill="both", expand=True)

    tk.Label(frame, text="STUDENT PLACEMENT TRACKER",
             font=("Arial", 23, "bold"), bg="#F1F5F9",
             fg="#172554").pack(pady=(75, 15))
    tk.Label(frame, text="ADMIN LOGIN", font=("Arial", 18, "bold"),
             bg="#F1F5F9", fg="#2563EB").pack(pady=12)

    tk.Label(frame, text="Username", bg="#F1F5F9",
             font=("Arial", 10, "bold")).pack()
    username = tk.Entry(frame, font=("Arial", 12), width=32)
    username.pack(pady=7, ipady=5)

    tk.Label(frame, text="Password", bg="#F1F5F9",
             font=("Arial", 10, "bold")).pack()
    password = tk.Entry(frame, font=("Arial", 12), width=32, show="*")
    password.pack(pady=7, ipady=5)

    cursor.execute("SELECT COUNT(*) FROM admins")
    first_admin = cursor.fetchone()[0] == 0

    def register():
        user, pwd = username.get().strip(), password.get()
        if not user or not pwd:
            messagebox.showwarning("Warning", "Enter username and password.")
            return
        if len(pwd) < 8:
            messagebox.showwarning("Weak Password",
                                   "Password must contain at least 8 characters.")
            return
        salt = secrets.token_hex(16)
        try:
            cursor.execute(
                "INSERT INTO admins(username,password_hash,salt) VALUES(?,?,?)",
                (user, hash_password(pwd, salt), salt)
            )
            conn.commit()
            messagebox.showinfo("Success", "Admin registered. Now login.")
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists.")

    def login():
        global current_admin
        user, pwd = username.get().strip(), password.get()
        if not user or not pwd:
            messagebox.showwarning("Warning", "Enter username and password.")
            return
        cursor.execute(
            "SELECT password_hash,salt FROM admins WHERE username=?", (user,)
        )
        result = cursor.fetchone()
        if result:
            stored_hash, salt = result
            if hmac.compare_digest(stored_hash, hash_password(pwd, salt)):
                current_admin = user
                frame.destroy()
                sidebar.pack(side="left", fill="y")
                main.pack(side="right", fill="both", expand=True)
                show_dashboard()
                return
        messagebox.showerror("Login Failed", "Invalid username or password.")

    create_button(frame, "LOGIN", login).pack(pady=14)
    if first_admin:
        create_button(frame, "REGISTER FIRST ADMIN", register, "#16A34A").pack()
        tk.Label(frame, text="Create your first administrator account.",
                 bg="#F1F5F9", fg="#64748B").pack(pady=10)
    else:
        tk.Label(frame, text="Enter your registered administrator credentials.",
                 bg="#F1F5F9", fg="#64748B").pack(pady=10)

def logout():
    global current_admin
    if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
        current_admin = None
        show_login()


def change_admin_password():
    clear_main()
    page_title("Change Admin Password")

    tk.Label(main, text=f"Logged in as: {current_admin or '-'}",
             bg="#F1F5F9", fg="#64748B",
             font=("Arial", 10, "bold")).pack(anchor="w", padx=35, pady=(0, 12))

    form = tk.Frame(main, bg="white", padx=25, pady=22,
                    highlightbackground="#E2E8F0", highlightthickness=1)
    form.pack(anchor="nw", padx=35, pady=10)

    def password_field(label):
        tk.Label(form, text=label, bg="white", fg="#172554",
                 font=("Arial", 10, "bold")).pack(anchor="w", pady=(8, 3))
        field = tk.Entry(form, show="*", font=("Arial", 11), width=36)
        field.pack(anchor="w", ipady=5)
        return field

    old_password = password_field("Current Password")
    new_password = password_field("New Password")
    confirm_password = password_field("Confirm New Password")

    def save_password():
        if not current_admin:
            messagebox.showerror("Session Error", "Please login again.")
            show_login()
            return

        old_pwd = old_password.get()
        new_pwd = new_password.get()
        confirm_pwd = confirm_password.get()

        if not old_pwd or not new_pwd or not confirm_pwd:
            messagebox.showwarning("Missing Details", "Please fill all password fields.")
            return
        if len(new_pwd) < 8:
            messagebox.showwarning("Weak Password", "New password must contain at least 8 characters.")
            return
        if new_pwd != confirm_pwd:
            messagebox.showerror("Password Mismatch", "New password and confirmation do not match.")
            return
        if old_pwd == new_pwd:
            messagebox.showwarning("Choose New Password", "New password must be different from current password.")
            return

        cursor.execute("SELECT id, password_hash, salt FROM admins WHERE username=?",
                       (current_admin,))
        record = cursor.fetchone()
        if not record or not hmac.compare_digest(record[1], hash_password(old_pwd, record[2])):
            messagebox.showerror("Incorrect Password", "Current password is incorrect.")
            return

        new_salt = secrets.token_hex(16)
        new_hash = hash_password(new_pwd, new_salt)
        cursor.execute("UPDATE admins SET password_hash=?, salt=? WHERE id=?",
                       (new_hash, new_salt, record[0]))
        conn.commit()
        old_password.delete(0, tk.END)
        new_password.delete(0, tk.END)
        confirm_password.delete(0, tk.END)
        messagebox.showinfo("Success", "Admin password changed successfully.")

    create_button(form, "UPDATE PASSWORD", save_password, "#16A34A").pack(anchor="w", pady=18)
    tk.Label(form, text="Password must be at least 8 characters.",
             bg="white", fg="#64748B").pack(anchor="w")

# ------------------------- DASHBOARD ----------------------

def show_dashboard():
    clear_main()
    page_title("Student Placement Dashboard")

    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM companies")
    total_companies = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM placements WHERE status='Placed'")
    placed = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM placements WHERE status='Not Placed'")
    not_placed = cursor.fetchone()[0]
    percentage = placed / total_students * 100 if total_students else 0

    cursor.execute("""SELECT COALESCE(MAX(c.package),0), COALESCE(AVG(c.package),0)
        FROM placements p JOIN companies c ON p.company_id=c.id
        WHERE p.status='Placed'""")
    highest, average = cursor.fetchone()

    cards_row1 = tk.Frame(main, bg="#F1F5F9")
    cards_row1.pack(fill="x", padx=10)
    create_card(cards_row1, "Total Students", total_students, "#2563EB")
    create_card(cards_row1, "Total Companies", total_companies, "#7C3AED")
    create_card(cards_row1, "Placed Students", placed, "#16A34A")

    cards_row2 = tk.Frame(main, bg="#F1F5F9")
    cards_row2.pack(fill="x", padx=10)
    create_card(cards_row2, "Not Placed", not_placed, "#DC2626")
    create_card(cards_row2, "Placement Rate", f"{percentage:.1f}%", "#0891B2")
    create_card(cards_row2, "Highest Package", f"{highest:.2f} LPA", "#D97706")

    info = tk.Frame(main, bg="white", padx=18, pady=14,
                    highlightbackground="#E2E8F0", highlightthickness=1)
    info.pack(fill="x", padx=20, pady=14)
    tk.Label(info, text="Placement Progress", bg="white", fg="#172554",
             font=("Arial", 13, "bold")).pack(anchor="w")
    progress = ttk.Progressbar(info, maximum=100, value=percentage, length=650)
    progress.pack(fill="x", pady=10)
    tk.Label(info, text=f"{placed} of {total_students} students placed  |  Average package: {average:.2f} LPA",
             bg="white", fg="#475569", font=("Arial", 10)).pack(anchor="w")

    recent = tk.Frame(main, bg="#F1F5F9")
    recent.pack(fill="both", expand=True, padx=20, pady=(0, 10))
    tk.Label(recent, text="Recent Placement Records", bg="#F1F5F9",
             fg="#172554", font=("Arial", 13, "bold")).pack(anchor="w", pady=(0, 7))
    tree = make_tree(recent, ("Student", "Roll Number", "Company", "Role", "Status"),
                     [170, 130, 170, 160, 110], height=5)
    tree.pack(fill="x")
    cursor.execute("""SELECT s.name,s.roll,COALESCE(c.company_name,'-'),
        COALESCE(p.job_role,'-'),COALESCE(p.status,'Not Updated')
        FROM students s LEFT JOIN placements p ON s.id=p.student_id
        LEFT JOIN companies c ON p.company_id=c.id
        ORDER BY p.id DESC, s.id DESC LIMIT 5""")
    for row in cursor.fetchall():
        tree.insert("", "end", values=row)

# ------------------------ ADD STUDENT ---------------------

def add_student():
    clear_main()
    page_title("Add New Student")
    name = create_entry(main, "Student Name")
    roll = create_entry(main, "Roll Number")
    branch = create_entry(main, "Branch")
    email = create_entry(main, "Email")
    cgpa = create_entry(main, "CGPA")

    def save():
        try:
            values = [name.get().strip(), roll.get().strip(),
                      branch.get().strip(), email.get().strip()]
            score = float(cgpa.get())
            if not all(values):
                messagebox.showwarning("Warning", "Please fill all fields.")
                return
            if not 0 <= score <= 10:
                messagebox.showwarning("Invalid CGPA",
                                       "CGPA must be between 0 and 10.")
                return
            cursor.execute("""INSERT INTO students
                (name,roll,branch,email,cgpa) VALUES(?,?,?,?,?)""",
                (*values, score))
            conn.commit()
            messagebox.showinfo("Success", "Student added successfully!")
            add_student()
        except ValueError:
            messagebox.showerror("Error", "Enter a valid CGPA.")
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Roll number already exists.")

    create_button(main, "Save Student", save).pack(anchor="w", padx=35, pady=18)

# ---------------- STUDENT VIEW / SEARCH / EDIT / DELETE ---

def view_students():
    clear_main()
    page_title("Student Management")
    search_var = tk.StringVar()
    tk.Label(main, text="Search by Name / Roll / Branch:",
             bg="#F1F5F9", font=("Arial", 10, "bold")).pack(anchor="w", padx=20)
    tk.Entry(main, textvariable=search_var, font=("Arial", 11),
             width=40).pack(anchor="w", padx=20, pady=7, ipady=4)

    columns = ("ID", "Name", "Roll", "Branch", "Email", "CGPA")
    tree = make_tree(main, columns, [55, 145, 110, 100, 190, 70])
    tree.pack(fill="both", expand=True, padx=20, pady=8)

    def load(*_):
        tree.delete(*tree.get_children())
        key = f"%{search_var.get().strip()}%"
        cursor.execute("""SELECT id,name,roll,branch,email,cgpa FROM students
            WHERE name LIKE ? OR roll LIKE ? OR branch LIKE ? ORDER BY id""",
            (key, key, key))
        for row in cursor.fetchall():
            tree.insert("", "end", values=row)

    def selected_row():
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Select Student", "Select a student first.")
            return None
        return tree.item(selection[0], "values")

    def edit():
        row = selected_row()
        if row is None:
            return
        dialog = tk.Toplevel(root)
        dialog.title("Edit Student")
        dialog.geometry("410x470")
        dialog.configure(bg="#F1F5F9")
        dialog.transient(root)
        dialog.grab_set()
        tk.Label(dialog, text="Edit Student Details",
                 font=("Arial", 16, "bold"), bg="#F1F5F9",
                 fg="#172554").pack(pady=14)
        entries = []
        for label, value in zip(
            ["Student Name", "Roll Number", "Branch", "Email", "CGPA"], row[1:]
        ):
            tk.Label(dialog, text=label, bg="#F1F5F9",
                     font=("Arial", 10, "bold")).pack(anchor="w", padx=28, pady=(5, 2))
            entry = tk.Entry(dialog, width=35, font=("Arial", 11))
            entry.pack(anchor="w", padx=28, ipady=4)
            entry.insert(0, str(value))
            entries.append(entry)

        def update():
            try:
                vals = [e.get().strip() for e in entries[:4]]
                score = float(entries[4].get())
                if not all(vals):
                    messagebox.showwarning("Warning", "Fill all fields.", parent=dialog)
                    return
                if not 0 <= score <= 10:
                    messagebox.showwarning("Invalid CGPA",
                                           "CGPA must be between 0 and 10.", parent=dialog)
                    return
                cursor.execute("""UPDATE students SET name=?,roll=?,branch=?,email=?,cgpa=?
                    WHERE id=?""", (*vals, score, row[0]))
                conn.commit()
                dialog.destroy()
                load()
                messagebox.showinfo("Success", "Student updated successfully!")
            except ValueError:
                messagebox.showerror("Invalid Input", "Enter a valid CGPA.", parent=dialog)
            except sqlite3.IntegrityError:
                messagebox.showerror("Duplicate Roll", "Roll number already exists.", parent=dialog)

        create_button(dialog, "Update Student", update, "#16A34A").pack(pady=18)

    def delete():
        row = selected_row()
        if row is None:
            return
        cursor.execute("SELECT COUNT(*) FROM placements WHERE student_id=?", (row[0],))
        if cursor.fetchone()[0]:
            messagebox.showwarning(
                "Cannot Delete",
                "This student has a placement record. Update/remove that record first."
            )
            return
        if messagebox.askyesno("Confirm Delete", f"Delete student {row[1]}?"):
            cursor.execute("DELETE FROM students WHERE id=?", (row[0],))
            conn.commit()
            load()
            messagebox.showinfo("Deleted", "Student deleted successfully!")

    buttons = tk.Frame(main, bg="#F1F5F9")
    buttons.pack(pady=8)
    create_button(buttons, "Edit Student", edit).pack(side="left", padx=7)
    create_button(buttons, "Delete Student", delete, "#DC2626").pack(side="left", padx=7)
    search_var.trace_add("write", load)
    load()

# ------------------------ ADD COMPANY ---------------------

def add_company():
    clear_main()
    page_title("Add New Company")
    company = create_entry(main, "Company Name")
    role = create_entry(main, "Job Role")
    package = create_entry(main, "Package (LPA)")
    eligibility = create_entry(main, "Eligibility CGPA")
    location = create_entry(main, "Location")

    def save():
        try:
            name = company.get().strip()
            job = role.get().strip()
            pkg = float(package.get())
            required = float(eligibility.get())
            place = location.get().strip()
            if not all([name, job, place]):
                messagebox.showwarning("Warning", "Please fill all fields.")
                return
            if pkg < 0:
                messagebox.showwarning("Invalid Package", "Package cannot be negative.")
                return
            if not 0 <= required <= 10:
                messagebox.showwarning("Invalid CGPA", "CGPA must be between 0 and 10.")
                return
            cursor.execute("""INSERT INTO companies
                (company_name,job_role,package,eligibility_cgpa,location)
                VALUES(?,?,?,?,?)""", (name, job, pkg, required, place))
            conn.commit()
            messagebox.showinfo("Success", "Company added successfully!")
            add_company()
        except ValueError:
            messagebox.showerror("Error", "Enter valid package and CGPA values.")

    create_button(main, "Save Company", save).pack(anchor="w", padx=35, pady=18)

# ---------------- COMPANY VIEW / SEARCH / EDIT / DELETE --

def view_companies():
    clear_main()
    page_title("Company Management")
    search_var = tk.StringVar()
    tk.Label(main, text="Search by Company / Job Role / Location:",
             bg="#F1F5F9", font=("Arial", 10, "bold")).pack(anchor="w", padx=20)
    tk.Entry(main, textvariable=search_var, font=("Arial", 11),
             width=42).pack(anchor="w", padx=20, pady=7, ipady=4)

    columns = ("ID", "Company", "Job Role", "Package", "Eligibility", "Location")
    tree = make_tree(main, columns, [55, 150, 145, 95, 100, 140])
    tree.pack(fill="both", expand=True, padx=20, pady=8)

    def load(*_):
        tree.delete(*tree.get_children())
        key = f"%{search_var.get().strip()}%"
        cursor.execute("""SELECT id,company_name,job_role,package,eligibility_cgpa,location
            FROM companies WHERE company_name LIKE ? OR job_role LIKE ? OR location LIKE ?
            ORDER BY id""", (key, key, key))
        for row in cursor.fetchall():
            tree.insert("", "end", values=row)

    def selected_row():
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Select Company", "Select a company first.")
            return None
        return tree.item(selection[0], "values")

    def edit():
        row = selected_row()
        if row is None:
            return
        dialog = tk.Toplevel(root)
        dialog.title("Edit Company")
        dialog.geometry("410x470")
        dialog.configure(bg="#F1F5F9")
        dialog.transient(root)
        dialog.grab_set()
        tk.Label(dialog, text="Edit Company Details",
                 font=("Arial", 16, "bold"), bg="#F1F5F9",
                 fg="#172554").pack(pady=14)
        entries = []
        labels = ["Company Name", "Job Role", "Package (LPA)",
                  "Eligibility CGPA", "Location"]
        for label, value in zip(labels, row[1:]):
            tk.Label(dialog, text=label, bg="#F1F5F9",
                     font=("Arial", 10, "bold")).pack(anchor="w", padx=28, pady=(5, 2))
            entry = tk.Entry(dialog, width=35, font=("Arial", 11))
            entry.pack(anchor="w", padx=28, ipady=4)
            entry.insert(0, str(value))
            entries.append(entry)

        def update():
            try:
                name, job, place = (entries[0].get().strip(),
                                    entries[1].get().strip(),
                                    entries[4].get().strip())
                pkg = float(entries[2].get())
                required = float(entries[3].get())
                if not all([name, job, place]):
                    messagebox.showwarning("Warning", "Fill all fields.", parent=dialog)
                    return
                if pkg < 0:
                    messagebox.showwarning("Invalid Package", "Package cannot be negative.", parent=dialog)
                    return
                if not 0 <= required <= 10:
                    messagebox.showwarning("Invalid CGPA", "CGPA must be between 0 and 10.", parent=dialog)
                    return
                cursor.execute("""UPDATE companies SET company_name=?,job_role=?,package=?,
                    eligibility_cgpa=?,location=? WHERE id=?""",
                    (name, job, pkg, required, place, row[0]))
                conn.commit()
                dialog.destroy()
                load()
                messagebox.showinfo("Success", "Company updated successfully!")
            except ValueError:
                messagebox.showerror("Invalid Input",
                                     "Enter valid package and CGPA values.", parent=dialog)

        create_button(dialog, "Update Company", update, "#16A34A").pack(pady=18)

    def delete():
        row = selected_row()
        if row is None:
            return
        cursor.execute("SELECT COUNT(*) FROM placements WHERE company_id=?", (row[0],))
        if cursor.fetchone()[0]:
            messagebox.showwarning(
                "Cannot Delete",
                "This company is linked to placement records. Update those records first."
            )
            return
        if messagebox.askyesno("Confirm Delete", f"Delete company {row[1]}?"):
            cursor.execute("DELETE FROM companies WHERE id=?", (row[0],))
            conn.commit()
            load()
            messagebox.showinfo("Deleted", "Company deleted successfully!")

    buttons = tk.Frame(main, bg="#F1F5F9")
    buttons.pack(pady=8)
    create_button(buttons, "Edit Company", edit).pack(side="left", padx=7)
    create_button(buttons, "Delete Company", delete, "#DC2626").pack(side="left", padx=7)
    search_var.trace_add("write", load)
    load()

def show_companies():
    clear_main()
    page_title("Company Management")
    create_button(main, "Add New Company", add_company).pack(anchor="w", padx=35, pady=12)
    create_button(main, "View / Search / Edit / Delete Companies",
                  view_companies).pack(anchor="w", padx=35, pady=12)

# --------------------- ELIGIBILITY CHECK ------------------

def check_eligibility():
    clear_main()
    page_title("Student Eligibility Checking")
    cursor.execute("SELECT id,company_name,eligibility_cgpa FROM companies")
    companies = cursor.fetchall()
    if not companies:
        tk.Label(main, text="Please add a company first.",
                 bg="#F1F5F9", font=("Arial", 13)).pack(pady=20)
        return

    company_map = {f"{c[1]} (Required CGPA: {c[2]})": c for c in companies}
    selected = tk.StringVar()
    tk.Label(main, text="Select Company:", bg="#F1F5F9",
             font=("Arial", 10, "bold")).pack(anchor="w", padx=30)
    ttk.Combobox(main, textvariable=selected, values=list(company_map),
                 state="readonly", width=42).pack(anchor="w", padx=30, pady=9)
    tree = make_tree(main, ("Name", "Roll", "CGPA", "Eligibility"), [180, 150, 100, 150])
    tree.pack(fill="both", expand=True, padx=25, pady=10)

    def check():
        if selected.get() not in company_map:
            messagebox.showwarning("Warning", "Please select a company.")
            return
        required = company_map[selected.get()][2]
        tree.delete(*tree.get_children())
        cursor.execute("SELECT name,roll,cgpa FROM students")
        for name, roll, cgpa in cursor.fetchall():
            tree.insert("", "end", values=(
                name, roll, cgpa, "Eligible" if cgpa >= required else "Not Eligible"
            ))

    create_button(main, "Check Eligibility", check).pack(pady=5)

# -------------------- PLACEMENT MANAGEMENT ----------------

def placement_management():
    clear_main()
    page_title("Placement Status Management")
    cursor.execute("SELECT id,name,roll FROM students ORDER BY name")
    students = cursor.fetchall()
    cursor.execute("SELECT id,company_name,job_role FROM companies ORDER BY company_name")
    companies = cursor.fetchall()

    if not students:
        tk.Label(main, text="Please add students first.",
                 bg="#F1F5F9", font=("Arial", 13)).pack(pady=20)
        return

    student_map = {f"{s[1]} - {s[2]}": s[0] for s in students}
    company_map = {f"{c[1]} - {c[2]}": c for c in companies}

    form = tk.Frame(main, bg="#F1F5F9")
    form.pack(anchor="w", padx=40, pady=10)

    tk.Label(form, text="Select Student:", bg="#F1F5F9",
             font=("Arial", 10, "bold")).pack(anchor="w")
    student_var = tk.StringVar()
    ttk.Combobox(form, textvariable=student_var, values=list(student_map),
                 state="readonly", width=42).pack(anchor="w", pady=7)

    tk.Label(form, text="Placement Status:", bg="#F1F5F9",
             font=("Arial", 10, "bold")).pack(anchor="w")
    status_var = tk.StringVar(value="Placed")
    ttk.Combobox(form, textvariable=status_var,
                 values=["Placed", "Not Placed"], state="readonly",
                 width=42).pack(anchor="w", pady=7)

    tk.Label(form, text="Select Company (Required for Placed):",
             bg="#F1F5F9", font=("Arial", 10, "bold")).pack(anchor="w")
    company_var = tk.StringVar()
    company_combo = ttk.Combobox(form, textvariable=company_var,
                                 values=list(company_map), state="readonly", width=42)
    company_combo.pack(anchor="w", pady=7)

    def update_company(*_):
        if status_var.get() == "Placed":
            company_combo.configure(state="readonly")
        else:
            company_var.set("")
            company_combo.configure(state="disabled")

    status_var.trace_add("write", update_company)
    update_company()

    def save():
        label, status = student_var.get(), status_var.get()
        if label not in student_map:
            messagebox.showwarning("Warning", "Select a student.")
            return
        student_id = student_map[label]
        company_id = None
        job_role = None
        if status == "Placed":
            if company_var.get() not in company_map:
                messagebox.showwarning("Warning", "Select a company.")
                return
            company = company_map[company_var.get()]
            company_id, job_role = company[0], company[2]
        try:
            cursor.execute("""UPDATE placements SET company_id=?,job_role=?,status=?
                WHERE student_id=?""", (company_id, job_role, status, student_id))
            if cursor.rowcount == 0:
                cursor.execute("""INSERT INTO placements
                    (student_id,company_id,job_role,status) VALUES(?,?,?,?)""",
                    (student_id, company_id, job_role, status))
            conn.commit()
            messagebox.showinfo("Success", f"Placement status saved as {status}!")
            placement_management()
        except sqlite3.Error as error:
            conn.rollback()
            messagebox.showerror("Database Error", str(error))

    create_button(form, "Save Placement Status", save, "#16A34A").pack(anchor="w", pady=18)

# -------------------- PLACEMENT RECORDS -------------------

def view_placement_records():
    clear_main()
    page_title("Student Placement Records")
    columns = ("Student Name", "Roll Number", "Company", "Job Role", "Status")
    tree = make_tree(main, columns, [170, 140, 170, 160, 120])
    tree.pack(fill="both", expand=True, padx=20, pady=10)
    cursor.execute("""
        SELECT s.name,s.roll,COALESCE(c.company_name,'-'),
               COALESCE(p.job_role,'-'),COALESCE(p.status,'Not Updated')
        FROM students s
        LEFT JOIN placements p ON s.id=p.student_id
        LEFT JOIN companies c ON p.company_id=c.id
        ORDER BY s.name
    """)
    for row in cursor.fetchall():
        tree.insert("", "end", values=row)

# ------------------------ CSV EXPORT ----------------------

def export_placement_report():
    cursor.execute("""
        SELECT s.name,s.roll,s.branch,s.email,s.cgpa,
               COALESCE(c.company_name,'-'),COALESCE(p.job_role,'-'),
               COALESCE(c.package,0),COALESCE(p.status,'Not Updated')
        FROM students s
        LEFT JOIN placements p ON s.id=p.student_id
        LEFT JOIN companies c ON p.company_id=c.id
        ORDER BY s.name
    """)
    rows = cursor.fetchall()
    if not rows:
        messagebox.showwarning("No Data", "No student records available.")
        return
    path = filedialog.asksaveasfilename(
        defaultextension=".csv", filetypes=[("CSV Files", "*.csv")],
        initialfile="Placement_Report.csv"
    )
    if not path:
        return
    try:
        with open(path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow([
                "Student Name", "Roll Number", "Branch", "Email", "CGPA",
                "Company", "Job Role", "Package (LPA)", "Placement Status"
            ])
            writer.writerows(rows)
        messagebox.showinfo("Success", "Placement report exported successfully!")
    except OSError as error:
        messagebox.showerror("Export Error", str(error))

# --------------------- PLACEMENT ANALYTICS ----------------

def placement_analytics():
    clear_main()
    page_title("Placement Analytics & Reports")
    cursor.execute("SELECT COUNT(*) FROM students")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM placements WHERE status='Placed'")
    placed = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM placements WHERE status='Not Placed'")
    not_placed = cursor.fetchone()[0]
    percentage = placed / total * 100 if total else 0

    cursor.execute("""SELECT MAX(c.package),AVG(c.package)
        FROM placements p JOIN companies c ON p.company_id=c.id
        WHERE p.status='Placed'""")
    highest, average = cursor.fetchone()
    highest = highest or 0
    average = average or 0

    cards = tk.Frame(main, bg="#F1F5F9")
    cards.pack(fill="x", padx=8)
    create_card(cards, "Total Students", total, "#2563EB")
    create_card(cards, "Placed", placed, "#16A34A")
    create_card(cards, "Not Placed", not_placed, "#DC2626")
    cards2 = tk.Frame(main, bg="#F1F5F9")
    cards2.pack(fill="x", padx=8)
    create_card(cards2, "Placement %", f"{percentage:.1f}%", "#7C3AED")
    create_card(cards2, "Highest Package", f"{highest:.2f} LPA", "#D97706")
    create_card(cards2, "Average Package", f"{average:.2f} LPA", "#0891B2")

    container = tk.Frame(main, bg="#F1F5F9")
    container.pack(fill="both", expand=True, padx=15, pady=5)
    canvas = tk.Canvas(container, bg="#F1F5F9", highlightthickness=0)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    content = tk.Frame(canvas, bg="#F1F5F9")
    window_id = canvas.create_window((0, 0), window=content, anchor="nw")
    content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda e: canvas.itemconfigure(window_id, width=e.width))
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    tk.Label(content, text="Overall Placement Progress",
             font=("Arial", 13, "bold"), bg="#F1F5F9",
             fg="#172554").pack(anchor="w", pady=8)
    progress = tk.Canvas(content, width=750, height=45, bg="white", highlightthickness=0)
    progress.pack(anchor="w", pady=5)
    progress.create_rectangle(10, 10, 740, 35, fill="#E2E8F0", outline="")
    if total and placed:
        progress.create_rectangle(10, 10, 10 + 730 * placed / total, 35,
                                  fill="#16A34A", outline="")
    tk.Label(content, text=f"{placed} out of {total} students placed ({percentage:.1f}%)",
             bg="#F1F5F9").pack(anchor="w", pady=4)

    tk.Label(content, text="Company-wise Placement Statistics",
             font=("Arial", 13, "bold"), bg="#F1F5F9",
             fg="#172554").pack(anchor="w", pady=(18, 7))
    company_tree = make_tree(content, ("Company", "Students Placed", "Package (LPA)"),
                             [220, 180, 160], height=6)
    company_tree.pack(fill="x", anchor="w")
    cursor.execute("""SELECT c.company_name,COUNT(p.student_id),c.package
        FROM companies c LEFT JOIN placements p
        ON c.id=p.company_id AND p.status='Placed'
        GROUP BY c.id ORDER BY COUNT(p.student_id) DESC""")
    for row in cursor.fetchall():
        company_tree.insert("", "end", values=row)

    tk.Label(content, text="Branch-wise Placement Statistics",
             font=("Arial", 13, "bold"), bg="#F1F5F9",
             fg="#172554").pack(anchor="w", pady=(18, 7))
    branch_tree = make_tree(content,
        ("Branch", "Total Students", "Placed Students", "Placement %"),
        [150, 150, 150, 140], height=7)
    branch_tree.pack(fill="x", anchor="w")
    cursor.execute("""SELECT s.branch,COUNT(s.id),
        SUM(CASE WHEN p.status='Placed' THEN 1 ELSE 0 END)
        FROM students s LEFT JOIN placements p ON s.id=p.student_id
        GROUP BY s.branch ORDER BY s.branch""")
    branch_rows = cursor.fetchall()
    for branch, count, branch_placed in branch_rows:
        rate = branch_placed / count * 100 if count else 0
        branch_tree.insert("", "end", values=(branch, count, branch_placed, f"{rate:.1f}%"))

    tk.Label(content, text="Branch-wise Placement Chart",
             font=("Arial", 13, "bold"), bg="#F1F5F9",
             fg="#172554").pack(anchor="w", pady=(18, 7))
    chart = tk.Canvas(content, width=750, height=260, bg="white", highlightthickness=0)
    chart.pack(anchor="w", pady=5)
    if branch_rows:
        max_count = max(row[1] for row in branch_rows) or 1
        bar_width = min(70, 500 // max(1, len(branch_rows)))
        for i, (branch, count, branch_placed) in enumerate(branch_rows):
            x = 60 + i * (bar_width + 35)
            bar_height = 175 * branch_placed / max_count
            y = 205 - bar_height
            chart.create_rectangle(x, y, x + bar_width, 205,
                                   fill="#2563EB", outline="")
            chart.create_text(x + bar_width / 2, y - 10, text=str(branch_placed))
            chart.create_text(x + bar_width / 2, 225, text=branch[:10])
    else:
        chart.create_text(375, 120, text="No branch data available", fill="#64748B")

    export_buttons = tk.Frame(content, bg="#F1F5F9")
    export_buttons.pack(anchor="w", pady=22)
    create_button(export_buttons, "Export Placement Report (CSV)",
                  export_placement_report, "#16A34A").pack(side="left", padx=(0, 10))
    create_button(export_buttons, "Export Placement Report (PDF)",
                  export_placement_report_pdf, "#1D4ED8").pack(side="left")

# ------------------------- SIDEBAR -------------------------

tk.Label(sidebar, text="PLACEMENT\nTRACKER", font=("Arial", 19, "bold"),
         bg="#172554", fg="white", pady=20).pack()

menu_items = [
    ("Dashboard", show_dashboard),
    ("Add Student", add_student),
    ("View / Manage Students", view_students),
    ("Companies", show_companies),
    ("Add Company", add_company),
    ("View / Manage Companies", view_companies),
    ("Check Eligibility", check_eligibility),
    ("Placement Management", placement_management),
    ("View Placement Records", view_placement_records),
    ("Placement Analytics", placement_analytics),
    ("Change Admin Password", change_admin_password),
    ("Logout", logout)
]

for label, function in menu_items:
    color = "#B91C1C" if label == "Logout" else "#1E3A8A"
    tk.Button(sidebar, text=label, command=function, bg=color, fg="white",
              activebackground="#3B82F6", activeforeground="white",
              font=("Arial", 9, "bold"), relief="flat", anchor="w",
              padx=11, pady=9, cursor="hand2").pack(fill="x", padx=8, pady=2)

# ----------------------- SAFE EXIT ------------------------

def close_application():
    try:
        conn.close()
    finally:
        root.destroy()

root.protocol("WM_DELETE_WINDOW", close_application)
show_login()
root.mainloop()