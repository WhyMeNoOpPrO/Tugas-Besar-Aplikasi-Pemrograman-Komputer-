import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, date

DB_NAME = "dapur.db"

# ==============================
# DATABASE SETUP
# ==============================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS stok (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT UNIQUE,
            jumlah INTEGER,
            expired TEXT,
            keterangan TEXT
        )
    """)
    
    cur.execute("PRAGMA table_info(stok)")
    kolom = [c[1] for c in cur.fetchall()]

    if "keterangan" not in kolom:
        cur.execute("ALTER TABLE stok ADD COLUMN keterangan TEXT")

    conn.commit()
    conn.close()


# ==============================
# REFRESH TABLE
# ==============================
def refresh_table():
    for row in tree.get_children():
        tree.delete(row)

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT * FROM stok")
    data = cur.fetchall()
    conn.close()

    for row in data:
        tree.insert("", "end", values=row)


# ==============================
# INPUT WINDOW
# ==============================
def open_input_window(title, mode="add", data=None):
    win = tk.Toplevel(root)
    win.title(title)
    win.geometry("320x300")
    win.resizable(False, False)

    tk.Label(win, text="Nama Bahan").pack()
    entry_nama = tk.Entry(win)
    entry_nama.pack()

    tk.Label(win, text="Jumlah").pack()
    entry_jumlah = tk.Entry(win)
    entry_jumlah.pack()

    tk.Label(win, text="Expired (YYYY-MM-DD)").pack()
    entry_exp = tk.Entry(win)
    entry_exp.pack()

    tk.Label(win, text="Keterangan (kg, liter, botol, dll)").pack()
    entry_ket = tk.Entry(win)
    entry_ket.pack()

    if data:
        entry_nama.insert(0, data[1])
        entry_jumlah.insert(0, data[2])
        entry_exp.insert(0, data[3])
        entry_ket.insert(0, data[4])

    def submit():
        nama = entry_nama.get().strip()
        jumlah = entry_jumlah.get().strip()
        expired = entry_exp.get().strip()
        ket = entry_ket.get().strip()

        if not nama or not jumlah or not expired:
            messagebox.showerror("Error", "Semua input wajib diisi!")
            return

        try:
            jumlah = int(jumlah)
        except:
            messagebox.showerror("Error", "Jumlah harus angka!")
            return

        try:
            datetime.fromisoformat(expired)
        except:
            messagebox.showerror("Error", "Format tanggal salah!")
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        if mode == "add":
            try:
                cur.execute("""
                    INSERT INTO stok (nama, jumlah, expired, keterangan)
                    VALUES (?, ?, ?, ?)
                """, (nama, jumlah, expired, ket))
                messagebox.showinfo("Sukses", "Bahan ditambahkan!")
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Nama bahan sudah ada!")
        else:
            cur.execute("""
                UPDATE stok SET nama=?, jumlah=?, expired=?, keterangan=?
                WHERE id=?
            """, (nama, jumlah, expired, ket, data[0]))
            messagebox.showinfo("Sukses", "Bahan diupdate!")

        conn.commit()
        conn.close()
        refresh_table()
        win.destroy()

    tk.Button(win, text="Simpan", command=submit).pack(pady=10)


# ==============================
# MENU FUNGSI
# ==============================
def tambah_bahan():
    open_input_window("Tambah Bahan", "add")

def edit_bahan():
    selected = tree.selection()
    if not selected:
        messagebox.showerror("Error", "Pilih bahan dulu!")
        return

    data = tree.item(selected[0])["values"]
    open_input_window("Edit Bahan", "edit", data)

def hapus_bahan():
    selected = tree.selection()
    if not selected:
        messagebox.showerror("Error", "Pilih bahan dulu!")
        return

    data = tree.item(selected[0])["values"]
    nama = data[1]

    if messagebox.askyesno("Hapus", f"Hapus '{nama}'?"):
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("DELETE FROM stok WHERE id=?", (data[0],))
        conn.commit()
        conn.close()
        refresh_table()

def pakai_bahan():
    selected = tree.selection()
    if not selected:
        messagebox.showerror("Error", "Pilih bahan dulu!")
        return

    data = tree.item(selected[0])["values"]
    id_bahan, nama, stok, exp, ket = data

    win = tk.Toplevel(root)
    win.title("Pakai Bahan")
    win.geometry("250x180")

    tk.Label(win, text=f"Bahan: {nama} ({ket})").pack()
    tk.Label(win, text=f"Stok tersedia: {stok}").pack()

    tk.Label(win, text="Jumlah dipakai:").pack()
    entry = tk.Entry(win)
    entry.pack()

    def submit():
        try:
            jumlah = int(entry.get())
        except:
            messagebox.showerror("Error", "Harus angka!")
            return

        if jumlah <= 0:
            return

        if jumlah > stok:
            messagebox.showerror("Error", "Stok kurang!")
            return

        stok_baru = stok - jumlah

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        if stok_baru == 0:
            cur.execute("DELETE FROM stok WHERE id=?", (id_bahan,))
        else:
            cur.execute("UPDATE stok SET jumlah=? WHERE id=?", (stok_baru, id_bahan))

        conn.commit()
        conn.close()
        refresh_table()
        win.destroy()

    tk.Button(win, text="OK", command=submit).pack(pady=10)


def cek_kedaluwarsa():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT * FROM stok")
    data = cur.fetchall()
    conn.close()

    hari = date.today()
    hasil = [f"{r[1]} | Expired {r[3]}" for r in data if date.fromisoformat(r[3]) < hari]

    if hasil:
        messagebox.showwarning("Expired", "\n".join(hasil))
    else:
        messagebox.showinfo("Info", "Tidak ada yang expired.")


def cek_hampir_kedaluwarsa():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT * FROM stok")
    data = cur.fetchall()
    conn.close()

    hari = date.today()
    hasil = []

    for r in data:
        sisa = (date.fromisoformat(r[3]) - hari).days
        if 0 < sisa <= 7:
            hasil.append(f"{r[1]} | {sisa} hari lagi")

    if hasil:
        messagebox.showwarning("Hampir Expired", "\n".join(hasil))
    else:
        messagebox.showinfo("Info", "Tidak ada bahan hampir expired.")


# ==============================
# GUI UTAMA
# ==============================
root = tk.Tk()
root.title("Manajer Persediaan Dapur")
root.geometry("1000x450")
root.resizable(True, True)   # Bisa diperbesar

frame = tk.Frame(root)
frame.pack(pady=10)

tree = ttk.Treeview(frame, columns=("ID", "Nama", "Jumlah", "Expired", "Keterangan"),
                    show="headings", height=12)

tree.heading("ID", text="ID")
tree.heading("Nama", text="Nama")
tree.heading("Jumlah", text="Jumlah")
tree.heading("Expired", text="Expired")
tree.heading("Keterangan", text="Keterangan")
tree.pack()

btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

tk.Button(btn_frame, text="Tambah", width=12, command=tambah_bahan).grid(row=0, column=0, padx=5)
tk.Button(btn_frame, text="Edit", width=12, command=edit_bahan).grid(row=0, column=1, padx=5)
tk.Button(btn_frame, text="Hapus", width=12, command=hapus_bahan).grid(row=0, column=2, padx=5)
tk.Button(btn_frame, text="Pakai", width=12, command=pakai_bahan).grid(row=0, column=3, padx=5)

tk.Button(btn_frame, text="Cek Expired", width=12, command=cek_kedaluwarsa).grid(row=1, column=1, pady=10)
tk.Button(btn_frame, text="Cek 7 Hari", width=12, command=cek_hampir_kedaluwarsa).grid(row=1, column=2, pady=10)

init_db()
refresh_table()
root.mainloop()