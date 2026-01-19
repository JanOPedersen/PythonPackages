import os
import sqlite3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkcalendar import DateEntry
from datetime import timedelta
from datetime import datetime
import io 
import zipfile 

DB_PATH = r"C:\Users\janop\OneDrive\Documents\Job\ansøgninger.sqlite"

BLOB_COLUMNS = ["Ansøgning", "CV", "Opslag", "Andet"]
TEXT_COLUMNS = [
    "Firma", "Addresse1", "Addresse2", "Stilling",
    "Noter", "Opslagsmedie"
]

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Ansøgninger - Database Manager")
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
       
        self.selected_id = None
        self.blob_data = {col: None for col in BLOB_COLUMNS}

        self.build_layout()
        self.load_table()

    # ---------------------------------------------------------
    # UI LAYOUT
    # ---------------------------------------------------------
    def build_layout(self):
        self.root.geometry("1500x700")

        # Left side: table
        table_frame = tk.Frame(self.root)
        table_frame.pack(side="left", fill="both", expand=True)

        # --- Scrollbars --- 
        vsb = ttk.Scrollbar(table_frame, orient="vertical") 
        hsb = ttk.Scrollbar(table_frame, orient="horizontal")

        self.tree = ttk.Treeview(
            table_frame,
            columns=("Id", "Firma", "Stilling", "Dato", "Opslagsmedie"),
            show="headings",
            yscrollcommand=vsb.set, 
            xscrollcommand=hsb.set
        )

        vsb.config(command=self.tree.yview) 
        hsb.config(command=self.tree.xview)

        # Layout 
        vsb.pack(side="right", fill="y") 
        hsb.pack(side="bottom", fill="x") 
        self.tree.pack(side="left", fill="both", expand=True)

        self.tree.bind("<Up>", self.on_arrow_key)
        self.tree.bind("<Down>", self.on_arrow_key)

        for col in ("Id", "Firma", "Stilling", "Dato", "Opslagsmedie"):
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_by_column(c, False))

        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)

        # Right side: detail panel
        detail_frame = tk.Frame(self.root, padx=10, pady=10)
        detail_frame.grid_columnconfigure(2, minsize=30)
        detail_frame.pack(side="right", fill="y")

        row = 0

        # ID (read-only)
        tk.Label(detail_frame, text="ID:").grid(row=row, column=0, sticky="w")
        self.id_var = tk.StringVar()
        tk.Entry(detail_frame, textvariable=self.id_var, state="readonly").grid(row=row, column=1)
        row += 1

        # Text fields
        self.text_vars = {}
        for col in TEXT_COLUMNS:
            tk.Label(detail_frame, text=f"{col}:").grid(row=row, column=0, sticky="w")
            var = tk.StringVar()
            self.text_vars[col] = var
            tk.Entry(detail_frame, textvariable=var, width=40).grid(row=row, column=1)
            row += 1

        # Dato (Date picker)
        tk.Label(detail_frame, text="Dato:").grid(row=row, column=0, sticky="w")
        self.date_dato = DateEntry(detail_frame, date_pattern="dd-mm-yyyy")
        self.date_dato.grid(row=row, column=1, sticky="w")
        row += 1

        # Opslagsdato (Date picker)
        tk.Label(detail_frame, text="Opslagsdato:").grid(row=row, column=0, sticky="w")
        self.date_opslagsdato = DateEntry(detail_frame, date_pattern="dd-mm-yyyy")
        self.date_opslagsdato.grid(row=row, column=1, sticky="w")
        row += 1

        self.enable_date_scroll(self.date_dato)
        self.enable_date_scroll(self.date_opslagsdato)

        # Jobsamtale checkbox
        self.jobsamtale_var = tk.IntVar()
        tk.Checkbutton(detail_frame, text="Jobsamtale", variable=self.jobsamtale_var).grid(row=row, column=1, sticky="w")
        row += 1

        # BLOB section
        tk.Label(detail_frame, text="Attachments:", font=("Arial", 12, "bold")).grid(row=row, column=0, pady=10)
        row += 1

        self.blob_labels = {}

        for col in BLOB_COLUMNS:
            tk.Label(detail_frame, text=f"{col}:").grid(row=row, column=0, sticky="w")

            # Inner frame to hold Upload + Extract tightly together
            btn_frame = tk.Frame(detail_frame)
            btn_frame.grid(row=row, column=1, sticky="w")

            upload_btn = tk.Button(btn_frame, text="Upload", command=lambda c=col: self.upload_blob(c))
            upload_btn.pack(side="left")

            extract_btn = tk.Button(btn_frame, text="Extract", command=lambda c=col: self.extract_blob(c))
            extract_btn.pack(side="left", padx=(5, 0))

            status_lbl = tk.Label(btn_frame, text=" ", width=2, anchor="w")
            status_lbl.pack(side="left", padx=(5, 0))
            self.blob_labels[col] = status_lbl

            row += 1

        # Buttons
        # Bottom button bar (aligned far left)
        button_bar = tk.Frame(detail_frame)
        button_bar.grid(row=row, column=0, columnspan=4, sticky="w", pady=20)

        tk.Button(button_bar, text="New", command=self.new_record).pack(side="left", padx=(0, 10))
        tk.Button(button_bar, text="Save", command=self.save_record).pack(side="left", padx=(0, 10))
        tk.Button(button_bar, text="Delete", command=self.delete_record).pack(side="left", padx=(0, 10))
        tk.Button(button_bar, text="Refresh", command=self.load_table).pack(side="left")

    # ---------------------------------------------------------
    # TABLE LOADING
    # ---------------------------------------------------------
    def _format_date(self, value):
        if not value:
            return ""
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d-%m-%Y %H:%M:%S"):
            try:
                parsed = datetime.strptime(value, fmt)
                return parsed.strftime("%d-%m-%Y")
            except ValueError:
                continue
        return value  # fallback if unknown format

    def load_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        self.cursor.execute("SELECT Id, Firma, Stilling, Dato, Opslagsmedie FROM Ansøgninger ORDER BY Id")

        for row in self.cursor.fetchall():
            Id, Firma, Stilling, Dato, Opslagsmedie = row

            # Convert date format if present
            if Dato:
                try:
                    # Parse YYYY-MM-DD
                    parsed = datetime.strptime(Dato, "%Y-%m-%d")
                    Dato_fmt = parsed.strftime("%d-%m-%Y")
                except ValueError:
                    # Fallback if DB contains other formats
                    Dato_fmt = Dato
            else:
                Dato_fmt = ""

            self.tree.insert("", "end", values=(Id, Firma, Stilling, Dato_fmt, Opslagsmedie))

    # ---------------------------------------------------------
    # ROW SELECTION
    # ---------------------------------------------------------
    def on_row_select(self, event):
        item = self.tree.selection()
        if not item:
            return
        row = self.tree.item(item)["values"]
        self.load_record(row[0])

    def _parse_db_date(self, value):
        if not value:
            return None
        # Try with time part first: '30-10-2012 00:00:00'
        for fmt in ("%d-%m-%Y %H:%M:%S", "%Y-%m-%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        return None

    # ---------------------------------------------------------
    # LOAD RECORD INTO FORM
    # ---------------------------------------------------------
    def clear_dateentry(self, widget):
        widget.set_date(datetime.today().date())  # required to avoid internal errors
        widget.entry.delete(0, "end")             # this makes it visually empty

    def load_record(self, record_id):
        self.selected_id = record_id
        self.cursor.execute("SELECT * FROM Ansøgninger WHERE Id=?", (record_id,))
        row = self.cursor.fetchone()

        if not row:
            return

        (
            Id, Firma, Addresse1, Addresse2, Stilling,
            Ansøgning, CV, Opslag, Andet,
            Jobsamtale, Dato, Opslagsdato, Noter, Opslagsmedie
        ) = row

        self.id_var.set(Id)
        self.text_vars["Firma"].set(Firma or "")
        self.text_vars["Addresse1"].set(Addresse1 or "")
        self.text_vars["Addresse2"].set(Addresse2 or "")
        self.text_vars["Stilling"].set(Stilling or "")

        # In load_record:
        parsed_dato = self._parse_db_date(Dato)
        if parsed_dato:
            self.date_dato.set_date(parsed_dato)
        else:
            self.date_dato.set_date(datetime.today().date())

        parsed_opslagsdato = self._parse_db_date(Opslagsdato)
        if parsed_opslagsdato:
            self.date_opslagsdato.set_date(parsed_opslagsdato)
        else:
            self.date_opslagsdato.delete(0, "end")

        self.text_vars["Noter"].set(Noter or "")
        self.text_vars["Opslagsmedie"].set(Opslagsmedie or "")

        self.jobsamtale_var.set(Jobsamtale or 0)

        # Load BLOBs
        blob_values = {
            "Ansøgning": Ansøgning,
            "CV": CV,
            "Opslag": Opslag,
            "Andet": Andet
        }

        for col, blob in blob_values.items():
            self.blob_data[col] = blob

        self.update_blob_markers()


    # ---------------------------------------------------------
    # NEW RECORD
    # ---------------------------------------------------------
    def new_record(self):
        self.selected_id = None
        self.id_var.set("")
        for col in TEXT_COLUMNS:
            self.text_vars[col].set("")
        self.jobsamtale_var.set(0)
        for col in BLOB_COLUMNS:
            self.blob_data[col] = None

        self.update_blob_markers()  # clear the A markers

        self.date_dato.set_date(datetime.today().date())
        self.date_opslagsdato.set_date(datetime.today().date())


    # ---------------------------------------------------------
    # UPLOAD BLOB
    # ---------------------------------------------------------
    def upload_blob(self, col):
        # Select multiple files
        paths = filedialog.askopenfilenames(
            title="Select files to ZIP",
            filetypes=[("All files", "*.*")]
        )
        if not paths:
            return

        # Create ZIP in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for path in paths:
                try:
                    zipf.write(path, arcname=os.path.basename(path))
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to add {path}:\n{e}")
                    return

        # Save ZIP bytes to BLOB
        self.blob_data[col] = zip_buffer.getvalue()

        # Update UI marker
        self.update_blob_markers()

    # ---------------------------------------------------------
    # EXTRACT BLOB
    # ---------------------------------------------------------
    def extract_blob(self, col):
        blob = self.blob_data[col]
        if not blob:
            messagebox.showerror("Error", "No file stored")
            return

        # Ask user for a folder to extract into
        folder = filedialog.askdirectory(title="Select folder to extract ZIP")
        if not folder:
            return

        try:
            # Load ZIP from memory
            zip_buffer = io.BytesIO(blob)
            with zipfile.ZipFile(zip_buffer, "r") as zipf:
                zipf.extractall(folder)

            messagebox.showinfo("Extracted", f"Files extracted to:\n{folder}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to extract ZIP:\n{e}")


    # ---------------------------------------------------------
    # SAVE RECORD (INSERT OR UPDATE)
    # ---------------------------------------------------------
    def save_record(self):
        data = {
            col: self.text_vars[col].get() for col in TEXT_COLUMNS
        }
        data["Jobsamtale"] = self.jobsamtale_var.get()

        for col in BLOB_COLUMNS:
            data[col] = self.blob_data[col]

        data["Dato"] = self.date_dato.get()
        data["Opslagsdato"] = self.date_opslagsdato.get()

        if self.selected_id is None:
            # INSERT
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?"] * len(data))
            sql = f"INSERT INTO Ansøgninger ({columns}) VALUES ({placeholders})"
            self.cursor.execute(sql, list(data.values()))
        else:
            # UPDATE
            assignments = ", ".join([f"{col}=?" for col in data.keys()])
            sql = f"UPDATE Ansøgninger SET {assignments} WHERE Id=?"
            self.cursor.execute(sql, list(data.values()) + [self.selected_id])

        self.conn.commit()
        self.load_table()
        messagebox.showinfo("Saved", "Record saved")

    # ---------------------------------------------------------
    # DELETE RECORD
    # ---------------------------------------------------------
    def delete_record(self):
        if not self.selected_id:
            return
        if not messagebox.askyesno("Confirm", "Delete this record"):
            return
        self.cursor.execute("DELETE FROM Ansøgninger WHERE Id=?", (self.selected_id,))
        self.conn.commit()
        self.load_table()
        self.new_record()

    # ---------------------------------------------------------
    # SORTING RECORDS
    # ---------------------------------------------------------
    def update_blob_markers(self):
        for col in BLOB_COLUMNS:
            blob = self.blob_data.get(col)
            self.blob_labels[col].config(text="A" if blob else "")

    def sort_by_column(self, col, reverse):
        data = []

        for child in self.tree.get_children(""):
            value = self.tree.set(child, col)

            # --- Special handling for Dato ---
            if col == "Dato":
                if not value:
                    # Empty date → lowest value → appears first
                    sort_value = datetime.min.date()
                else:
                    try:
                        sort_value = datetime.strptime(value, "%d-%m-%Y").date()
                    except Exception:
                        # Malformed date → treat as lowest
                        sort_value = datetime.min.date()

            # --- Numeric ID ---
            elif col == "Id":
                try:
                    sort_value = int(value)
                except ValueError:
                    sort_value = value

            # --- Default string sort ---
            else:
                sort_value = value.lower() if isinstance(value, str) else value

            data.append((sort_value, child))

        # Sort
        data.sort(reverse=reverse)

        # Reorder rows
        for index, (_, child) in enumerate(data):
            self.tree.move(child, "", index)

        # Toggle direction
        self.tree.heading(col, command=lambda: self.sort_by_column(col, not reverse))

        # After sorting, re-select the row by record ID 
        if self.selected_id is not None: 
            for item in self.tree.get_children(""): 
                values = self.tree.item(item)["values"] 
                if values and values[0] == self.selected_id: 
                    self.tree.selection_set(item) 
                    self.tree.focus(item)  
                    break
        
    # ---------------------------------------------------------
    # ENABLE DATE SCROLLING
    # ---------------------------------------------------------
    def enable_date_scroll(self, widget):
        def on_scroll(event):
            # Scroll up = +1 day, scroll down = -1 day
            delta = 1 if event.delta > 0 else -1
            current = widget.get_date()
            new_date = current + timedelta(days=delta)
            widget.set_date(new_date)

        widget.bind("<MouseWheel>", on_scroll)          # Windows
        widget.bind("<Button-4>", lambda e: on_scroll(type("Event", (), {"delta": 120})))   # Linux scroll up
        widget.bind("<Button-5>", lambda e: on_scroll(type("Event", (), {"delta": -120})))  # Linux scroll down

    # ---------------------------------------------------------
    # HANDLE KEYBOARD NAVIGATION
    # ---------------------------------------------------------
    def on_key_move(self, event):
        # After the key press, let Treeview update selection, then load the record
        self.root.after(10, self._load_selected_after_key)

    def _load_selected_after_key(self):
        item = self.tree.selection()
        if not item:
            return
        row = self.tree.item(item)["values"]
        record_id = row[0]
        self.load_record(record_id)

    def on_arrow_key(self, event):
        # Let Treeview process the keypress first
        self.root.after(1, self._update_after_arrow)

    def _update_after_arrow(self):
        item = self.tree.focus()  # <-- this is the row under the cursor
        if not item:
            return
        self.tree.selection_set(item)
        row = self.tree.item(item)["values"]
        if row:
            self.load_record(row[0])

def main():
    root = tk.Tk()
    app = App(root)
    root.mainloop()

if __name__ == "__main__":
    main()

 