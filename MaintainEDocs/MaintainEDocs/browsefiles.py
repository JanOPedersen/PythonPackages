import webbrowser
import shutil
import tkinter as tk
import os
import glob
import sys
import pickle
sys.path.append(r'C:\Users\janop\OneDrive\Documents\e-Papers\e-library')
from MaintainEDocs.MaintainEDocs.elibraryutils import fetch_rows, EDocsDict

def open_pickle_file(currentType):
    '''
    This function opens a pickle file and populates the udc_table dictionary.
    '''
    global rows, udc_table
    # Fetch all rows from the UDC database
    rows = fetch_rows(currentType)

    with open(EDocsDict[currentType]["pickle_name"], 'rb') as f:
        udc_table = pickle.load(f)

def on_closing():
    root.destroy()

def update_listbox_on_select():
    '''
    This function is called when an item is selected in the listbox.
    listbox.curselection() returns a tuple with the index of the selected item.
    The [2], [4] and [5] are derived by the table structure of the database.
    The [2] is the filename, [4] is the path and [5] is the UDC code.
    (title, FileName, NormalizedFileName, Path, UDC, citationCount, publicationDate, paperId)
    '''
    global listbox, sub_rows, filename, path, udc_entry
    listbox_curselection = listbox.curselection()[0]

    if listbox_curselection in range(len(sub_rows)):
        filename = sub_rows[listbox_curselection][2]
        path = sub_rows[listbox_curselection][4]
        udc_txt = sub_rows[listbox_curselection][5]
        citationCount = sub_rows[listbox_curselection][6]
        publicationDate = sub_rows[listbox_curselection][7]
        udc_entry.delete(0, tk.END)
        udc_entry.insert(0, udc_txt)
        udc_name_label['text'] = udc_table[udc_txt]
        citationCount_label['text'] = citationCount
        publicationDate_label['text'] = publicationDate

def on_select(event):
    '''
    This function is called when an item is selected in the listbox.
    listbox.curselection() returns a tuple with the index of the selected item.
    The [2], [4] and [5] are derived by the table structure of the database.
    The [2] is the filename, [4] is the path and [5] is the UDC code.
    (title, FileName, NormalizedFileName, Path, UDC, citationCount, publicationDate, paperId)
    '''
    update_listbox_on_select()

def delete_files_in_folder(folder_path):
    files = glob.glob(os.path.join(folder_path, "*"))  # Get all files in the folder
    for file in files:
        try:
            os.remove(file)  # Remove the file
        except Exception as e:
            pass  # If there is an error, ignore it

def open_in_browser():
    '''
    The \\\\?\\\\ trick is to allow long path names in Windows. It ensures
    that the path is in unicode and not in the ANSI format.
    '''
    global path, filename
    temp = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
    delete_files_in_folder(temp)
    shutil.copy('\\\\?\\\\' + os.path.join(path, filename), temp)
    webbrowser.open_new(r'file://' + os.path.join(temp, filename))

def on_double_click(event):
    open_in_browser()  

def search():
    global listbox, filename_entry, rows, sub_rows
    sub_rows = [row for row in rows if filename_entry.get().lower() in row[3]]
    listbox.delete(0, tk.END)
    for row in sub_rows:
        listbox.insert(tk.END, row[2])

def populate_listbox_filename(entry_text):
    global listbox, rows, sub_rows
    sub_rows = [row for row in rows if entry_text.lower() in row[3]]
    listbox.delete(0, tk.END)
    for row in sub_rows:
        listbox.insert(tk.END, row[2])

def populate_listbox_udc(udc):
    global listbox, rows, sub_rows
    sub_rows = [row for row in rows if udc in row[5]]
    listbox.delete(0, tk.END)
    for row in sub_rows:
        listbox.insert(tk.END, row[2])

def filename_key_press(event):
    global filename_entry
    populate_listbox_filename(filename_entry.get() + event.char)

def filename_backspace_press(event):
    global filename_entry
    populate_listbox_filename(filename_entry.get()[0:-1])

def populate_label_and_listbox(udc_label_txt):
    populate_listbox_udc(udc_label_txt)
    if udc_label_txt in udc_table:
        udc_name_label['text'] = udc_table[udc_label_txt]

def udc_key_press(event):
    global udc_entry, udc_name_label, udc_text
    if (len(udc_entry.get()) - 3) % 4 == 0:
        udc_entry.insert(tk.END, '.')
    udc_text = udc_entry.get() + event.char
    populate_label_and_listbox(udc_text)

def udc_backspace_press(event):
    global udc_entry, udc_name_label, udc_text
    if (len(udc_entry.get()) - 5) % 4 == 0:
        udc_entry.delete(len(udc_entry.get()) - 1, tk.END)
    udc_text = udc_entry.get()[0:-1]
    populate_label_and_listbox(udc_text)

def udc_select_all(event):
    global udc_entry, udc_name_label, udc_text
    udc_entry.delete(0, tk.END)
    udc_entry.insert(0, udc_text)
    if udc_text in udc_table:
        udc_name_label['text'] = udc_table[udc_text]

def only_numeric_input(P):
    return set(P).issubset(set(".0123456789"))

def handle_up(event):
    # Get the currently selected index 
    selected = listbox.curselection()
    if selected:  # If an item is selected
        new_index = max(0, selected[0] - 1)  # Move up but stay within bounds
        listbox.selection_clear(0, tk.END)  # Clear current selection
        listbox.selection_set(new_index)  # Set new selection
        listbox.activate(new_index)  # Activate the new selection
        update_listbox_on_select()
        
def handle_down(event):
    # Get the currently selected index
    selected = listbox.curselection()
    if selected:  # If an item is selected
        new_index = min(listbox.size() - 1, selected[0] + 1)  # Move down but stay within bounds
        listbox.selection_clear(0, tk.END)  # Clear current selection
        listbox.selection_set(new_index)  # Set new selection
        listbox.activate(new_index)  # Activate the new selection
        update_listbox_on_select()
        
def handle_enter(event):
    # Action to perform when Enter key is pressed
    open_in_browser()

root = tk.Tk()
root.title("Search e-library")
root.geometry("")
root.protocol("WM_DELETE_WINDOW", on_closing)

# Bind arrow keys to their respective handlers
root.bind("<Up>", handle_up)
root.bind("<Down>", handle_down)
root.bind("<Return>", handle_enter)

## FRAME 1
frame1 = tk.Frame(root)
frame1.pack(fill=tk.X)

listbox = tk.Listbox(frame1, selectmode=tk.SINGLE, width=150, height=30)
listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
listbox.bind('<<ListboxSelect>>', on_select)
listbox.bind('<Double-Button-1>', on_double_click)

scrollbar = tk.Scrollbar(frame1)
scrollbar.pack(side=tk.RIGHT, fill=tk.BOTH)

listbox.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=listbox.yview)

## FRAME 2
frame2 = tk.Frame(root)
frame2.pack(fill=tk.X)

filename_label = tk.Label(frame2, text='Enter document name:')
filename_label.pack(side=tk.LEFT)

filename_entry = tk.Entry(frame2)
filename_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
filename_entry.bind('<Key>', filename_key_press)
filename_entry.bind('<BackSpace>', filename_backspace_press)

## FRAME 3
frame3 = tk.Frame(root)
frame3.pack(fill=tk.X)

udc_label = tk.Label(frame3, text='Enter UDC code:')
udc_label.pack(side=tk.LEFT)

validate_command = root.register(only_numeric_input)
udc_entry = tk.Entry(frame3, validate="key", validatecommand=(validate_command, '%P'))
udc_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
udc_entry.bind('<Key>', udc_key_press)
udc_entry.bind('<BackSpace>', udc_backspace_press)
udc_entry.bind('<1>', udc_select_all)

udc_name_label = tk.Label(frame3, text='', width=50)
udc_name_label.pack(side=tk.LEFT)

citationCount_label = tk.Label(frame3, text='', width=20)
citationCount_label.pack(side=tk.LEFT)

publicationDate_label = tk.Label(frame3, text='', width=20)
publicationDate_label.pack(side=tk.LEFT)

udc_text = ''
