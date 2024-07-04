import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import pandas as pd
import mysql.connector

mydb = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    port='3306',
    database='gauge'
)

mycursor = mydb.cursor()

class AddEntryDialog(simpledialog.Dialog):
    def __init__(self, parent):
        self.name_var = tk.StringVar()
        self.external_party_var = tk.StringVar()
        self.date_var = tk.StringVar()
        super().__init__(parent)

    def body(self, master):
        tk.Label(master, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        tk.Entry(master, textvariable=self.name_var).grid(row=0, column=1, pady=5)
        tk.Label(master, text="External Party:").grid(row=1, column=0, sticky=tk.W, pady=5)
        tk.Entry(master, textvariable=self.external_party_var).grid(row=1, column=1, pady=5)
        tk.Label(master, text="Date:").grid(row=2, column=0, sticky=tk.W, pady=5)
        tk.Entry(master, textvariable=self.date_var).grid(row=2, column=1, pady=5)
        return master

    def buttonbox(self):
        box = tk.Frame(self)
        tk.Button(box, text="Add", width=10, command=self.add).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(box, text="Cancel", width=10, command=self.cancel).pack(side=tk.LEFT, padx=5, pady=5)
        box.pack()

    def add(self):
        self.result = {
            'name': self.name_var.get(),
            'external_party': self.external_party_var.get(),
            'date': self.date_var.get()
        }
        self.ok()

    def apply(self):
        pass




def open_add_entry_dialog():
    dialog = AddEntryDialog(root)
    if dialog.result:
        tree.insert("", tk.END, values=(
            unchecked_char,  # Placeholder for checkbox
            dialog.result['name'],
            dialog.result['external_party'],
            "Yes",  # Default value for Verifications
            "No",   # Default value for Problems
            dialog.result['date']
        ))
        with open("entries.txt", "a") as f:
            f.write(f"{dialog.result['name']},{dialog.result['external_party']},Yes,No,{dialog.result['date']}\n")

def toggle_selection(event):
    item = tree.identify_row(event.y)
    if item:
        current_value = tree.item(item, 'values')[0]
        new_value = checked_char if current_value == unchecked_char else unchecked_char
        tree.item(item, values=(new_value,) + tree.item(item, 'values')[1:])
        update_selection()

def on_double_click(event):
    item = tree.identify('item', event.x, event.y)
    column = tree.identify('column', event.x, event.y)

    if item and column:
        column_id = int(column[1:]) - 1  # Convert column identifier to index
        if column_id in [1, 2, 5]:  # Name, External Party, or Date columns
            current_value = tree.item(item, 'values')[column_id]

            def edit_cell(event=None):
                new_value = entry.get()
                values = list(tree.item(item, 'values'))
                values[column_id] = new_value
                tree.item(item, values=values)
                entry.destroy()
                tree.focus_set()

            entry = tk.Entry(tree)
            entry.insert(0, current_value)
            entry.select_range(0, tk.END)
            entry.focus_set()
            entry.bind('<FocusOut>', edit_cell)
            entry.bind('<Return>', edit_cell)

            tree.column(column, width=entry.winfo_reqwidth())

            # Place the Entry widget on top of the cell
            x, y, width, height = tree.bbox(item, column)
            entry.place(x=x, y=y, width=width, height=height)

    return "break"  # Prevent default double-click behavior

def update_selection():
    for item in tree.get_children():
        current_value = tree.item(item, 'values')[0]
        if current_value == checked_char:
            tree.item(item, tags=('selected',))
        else:
            tree.item(item, tags=())

def delete_selected_entries(event):
    selected_items = [item for item in tree.get_children() if tree.item(item, 'values')[0] == checked_char]
    for item in selected_items:
        tree.delete(item)
    update_selection()

def select_all_entries(event):
    for item in tree.get_children():
        tree.item(item, values=(checked_char,) + tree.item(item, 'values')[1:])
    update_selection()

def open_selected_entries(event):
    selected_items = [item for item in tree.get_children() if tree.item(item, 'values')[0] == checked_char]
    if not selected_items:
        messagebox.showinfo("Open", "No entries selected")
        return

    for item in selected_items:
        entry_values = tree.item(item, 'values')
        entry_name = entry_values[1]
        open_details_window(entry_name)

def delete_selected_entries_in_details(tree):
    selected_items = tree.selection()
    for item in selected_items:
        tree.delete(item)

def select_all_entries_in_details(tree):
    for item in tree.get_children():
        tree.selection_add(item)

def open_details_window(entry_name):
    details_window = tk.Toplevel(root)
    details_window.title(entry_name)

    details_window.geometry("800x600")
    details_body_frame = tk.Frame(details_window, bg='white')
    details_body_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    details_headings = ['Select', 'Parameters', 'Actual Readings', 'Standard Readings', 'Acceptable Range', 'Error Percentage']
    details_tree = ttk.Treeview(details_body_frame, columns=details_headings, show="headings", selectmode="none")
    details_tree.pack(fill=tk.BOTH, expand=True)

    for heading in details_headings:
        details_tree.heading(heading, text=heading, anchor=tk.CENTER)
        if heading == 'Select':
            details_tree.column(heading, width=50, anchor=tk.CENTER)
        else:
            details_tree.column(heading, width=150, anchor=tk.CENTER)

    if entry_name in details_data and details_data[entry_name]:
        for data in details_data[entry_name]:
            details_tree.insert("", tk.END, values=data)

    def save_changes():
        any_out_of_range = False
        problems = []
        for item in details_tree.get_children():
            values = list(details_tree.item(item, 'values'))
            actual_reading = float(values[2])
            standard_reading = float(values[3])
            min_range, max_range = map(float, values[4].split('-'))

            error_percentage = ((actual_reading-standard_reading) / standard_reading) * 100
            values[5] = f"{error_percentage:.2f}%"
            details_tree.item(item, values=values)

            if not (min_range <= actual_reading <= max_range):
                any_out_of_range = True
                problems.append(values[1])


        for item in tree.get_children():
            if tree.item(item, 'values')[1] == entry_name:
                if any_out_of_range:
                    tree.item(item, values=(tree.item(item, 'values')[0], entry_name, tree.item(item, 'values')[2], "No", ", ".join(problems), tree.item(item, 'values')[5]))
                else:
                    tree.item(item, values=(tree.item(item, 'values')[0], entry_name, tree.item(item, 'values')[2], "Yes", "No", tree.item(item, 'values')[5]))

    create_button = tk.Button(details_window, text="Create New Entry", command=lambda: create_entry_dialog(details_tree, entry_name))
    create_button.pack(side=tk.LEFT, padx=5, pady=5)

    select_all_button = tk.Button(details_window, text="Select All", command=lambda: select_all_entries_in_details(details_tree))
    select_all_button.pack(side=tk.LEFT, padx=5, pady=5)

    delete_button = tk.Button(details_window, text="Delete", command=lambda: delete_selected_entries_in_details(details_tree))
    delete_button.pack(side=tk.LEFT, padx=5, pady=5)

    save_button = tk.Button(details_window, text="Save", command=save_changes)
    save_button.pack(side=tk.LEFT, padx=5, pady=5)


def create_entry_dialog(details_tree, entry_name):
    dialog = tk.Toplevel(root)
    dialog.title("Create New Entry")

    parameter_var = tk.StringVar()

    tk.Label(dialog, text="Parameter:").grid(row=0, column=0, sticky=tk.W, pady=5)
    parameter_menu = ttk.Combobox(dialog, textvariable=parameter_var, values=["Temperature", "Pressure", "Current"])
    parameter_menu.grid(row=0, column=1, pady=5)

    tk.Label(dialog, text="Actual Reading:").grid(row=1, column=0, sticky=tk.W, pady=5)
    actual_reading_entry = tk.Entry(dialog)
    actual_reading_entry.grid(row=1, column=1, pady=5)

    def add_entry():
        parameter = parameter_var.get()
        actual_reading = actual_reading_entry.get()
        if parameter and actual_reading:
            if parameter == "Temperature":
                standard_reading = 30
                acceptable_range = "28-35"
            elif parameter == "Pressure":
                standard_reading = 2
                acceptable_range = "1-4"
            elif parameter == "Current":
                standard_reading = 10
                acceptable_range = "5-15"

            error_percentage = ((float(actual_reading) - standard_reading) / standard_reading) * 100
            new_entry = (unchecked_char, parameter, actual_reading, standard_reading, acceptable_range, f"{error_percentage:.2f}%")
            details_tree.insert("", tk.END, values=new_entry)
            if entry_name not in details_data:
                details_data[entry_name] = []
            details_data[entry_name].append(new_entry)
            dialog.destroy()

    tk.Button(dialog, text="Add", command=add_entry).grid(row=2, column=0, columnspan=2, pady=10)


def create_action(event):
    open_add_entry_dialog()


def load_action(event):
    file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
    if file_path:
        try:
            df = pd.read_excel(file_path)
            global details_data
            details_data = {}
            tree.delete(*tree.get_children())

            for _, row in df.iterrows():
                name = row.get('Name', 'Empty')
                external_party = row.get('External Party', 'Empty')
                date = row.get('Date', 'Empty')
                parameter = row.get('Parameter', 'Empty')
                actual_reading = row.get('Actual Reading', 0)

                if name not in details_data:
                    tree.insert("", tk.END, values=(
                        unchecked_char, name, external_party, "Yes", "No", date
                    ))
                    details_data[name] = []

                if parameter == "Temperature":
                    standard_reading = 30
                    acceptable_range = "28-35"
                elif parameter == "Pressure":
                    standard_reading = 2
                    acceptable_range = "1-4"
                elif parameter == "Current":
                    standard_reading = 10
                    acceptable_range = "5-15"
                else:
                    standard_reading = 0
                    acceptable_range = "0-0"

                min_range, max_range = map(float, acceptable_range.split('-'))
                actual_reading_float = float(actual_reading)
                error_percentage = ((actual_reading_float - standard_reading) / standard_reading) * 100

                details_data[name].append((
                    unchecked_char, parameter, actual_reading, standard_reading, acceptable_range,
                    f"{error_percentage:.2f}%"
                ))

            for item in tree.get_children():
                entry_name = tree.item(item, 'values')[1]
                if entry_name in details_data:
                    any_out_of_range = False
                    problems = []

                    for detail in details_data[entry_name]:
                        actual_reading = float(detail[2])
                        min_range, max_range = map(float, detail[4].split('-'))

                        if not (min_range <= actual_reading <= max_range):
                            any_out_of_range = True
                            problems.append(detail[1])

                    if any_out_of_range:
                        tree.item(item, values=(tree.item(item, 'values')[0], entry_name, tree.item(item, 'values')[2], "No", ", ".join(problems), tree.item(item, 'values')[5]))
                    else:
                        tree.item(item, values=(tree.item(item, 'values')[0], entry_name, tree.item(item, 'values')[2], "Yes", "No", tree.item(item, 'values')[5]))

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {e}")


def save_as_action(event):
    file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx *.xls")])
    if file_path:
        try:
            data = []
            for item in tree.get_children():
                values = tree.item(item, 'values')
                data.append({
                    'Name': values[1],
                    'External Party': values[2],
                    'Verifications': values[3],
                    'Problems': values[4],
                    'Date': values[5]
                })
            df = pd.DataFrame(data)
            df.to_excel(file_path, index=False)
            messagebox.showinfo("Save", "File saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {e}")

def share_action(event):
    messagebox.showinfo("Shared", "shared")

def open_action(event):
    open_selected_entries(event)

def select_all_action(event):
    select_all_entries(event)

def delete_action(event):
    delete_selected_entries(event)

def search_action(*args):
    query = search_var.get().lower()
    for item in tree.get_children():
        values = tree.item(item, 'values')
        if query in values[1].lower() or query in values[2].lower() or query in values[5].lower():
            tree.item(item, tags=('found',))
        else:
            tree.item(item, tags=('hidden',))
    tree.tag_configure('found', foreground='black')
    tree.tag_configure('hidden', foreground='white')

def save_action(event):
    tk.messagebox.showinfo("Save clicked")

root = tk.Tk()
root.title("Gauge Inspection")
root.geometry("1200x600")

large_font = ('Verdana', 12)
checked_char = "\u2713"
unchecked_char = "\u2717"
details_data = {}

header_frame = tk.Frame(root)
header_frame.pack(fill=tk.X, padx=10, pady=10)

search_frame = tk.Frame(header_frame)
search_frame.pack(side=tk.LEFT, padx=10)

search_var = tk.StringVar()
search_var.trace("w", search_action)
search_entry = tk.Entry(search_frame, textvariable=search_var, width=40, font=large_font)
search_entry.pack(side=tk.TOP, pady=5)

left_panel_frame = tk.Frame(root, width=200, bg='light green')
left_panel_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

create_text = tk.Label(left_panel_frame, text="Create", fg='black', font=large_font, cursor="hand2", bg='light green')
create_text.pack(pady=5)
create_text.bind("<Button-1>", create_action)

load_text = tk.Label(left_panel_frame, text="Load", fg='black', font=large_font, cursor="hand2", bg='light green')
load_text.pack(pady=5)
load_text.bind("<Button-1>", load_action)

save_as_text = tk.Label(left_panel_frame, text="Save as", fg='black', font=large_font, cursor="hand2", bg='light green')
save_as_text.pack(pady=5)
save_as_text.bind("<Button-1>", save_as_action)

share_text = tk.Label(left_panel_frame, text="Share", fg='black', font=large_font, cursor="hand2", bg='light green')
share_text.pack(pady=5)
share_text.bind("<Button-1>", share_action)

save_text = tk.Label(left_panel_frame, text="Save", fg='black', font=large_font, cursor="hand2", bg='light green')
save_text.pack(pady=5)
save_text.bind("<Button-1>", save_action)

right_text_frame = tk.Frame(header_frame)
right_text_frame.pack(side=tk.RIGHT, padx=10)

open_text = tk.Label(right_text_frame, text="Open", fg='black', font=large_font, cursor="hand2")
open_text.pack(side=tk.LEFT, padx=5)
open_text.bind("<Button-1>", open_action)

select_all_text = tk.Label(right_text_frame, text="Select All", fg='black', font=large_font, cursor="hand2")
select_all_text.pack(side=tk.LEFT, padx=5)
select_all_text.bind("<Button-1>", select_all_action)

delete_text = tk.Label(right_text_frame, text="Delete", fg='black', font=large_font, cursor="hand2")
delete_text.pack(side=tk.LEFT, padx=5)
delete_text.bind("<Button-1>", delete_action)

body_frame = tk.Frame(root, bg='light green')
body_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

headings = ['Select', 'Name', 'External Party', 'Verifications', 'Problems', 'Date']

tree = ttk.Treeview(body_frame, columns=headings, show="headings", selectmode="none")
tree.pack(fill=tk.BOTH, expand=True)

for heading in headings:
    tree.heading(heading, text=heading, anchor=tk.CENTER)
    if heading == 'Select':
        tree.column(heading, width=50, anchor=tk.CENTER)
    else:
        tree.column(heading, width=200, anchor=tk.CENTER)



# Assume `mydb` is your database connection and `mycursor` is your cursor
query = """
    SELECT `name`, `external_party`, `date`, `parameters`, `actual_reading`
    FROM `gauge_entries`
    """
df = pd.read_sql(query, mydb)

# Assume `tree` is your Tkinter treeview widget
details_data = {}

for _, row in df.iterrows():
    name = row['name']
    external_party = row['external_party']
    date = row['date']
    parameter = row['parameters']
    actual_reading = row['actual_reading']

    if name not in details_data:
        tree.insert("", tk.END, values=(
            unchecked_char, name, external_party, "Yes", "No", date
        ))
        details_data[name] = []

    if parameter == "Temperature":
        standard_reading = 30
        acceptable_range = "28-35"
    elif parameter == "Pressure":
        standard_reading = 2
        acceptable_range = "1-4"
    elif parameter == "Current":
        standard_reading = 10
        acceptable_range = "5-15"
    else:
        standard_reading = 0
        acceptable_range = "0-0"

    min_range, max_range = map(float, acceptable_range.split('-'))
    actual_reading_float = float(actual_reading)
    error_percentage = ((actual_reading_float - standard_reading) / standard_reading) * 100

    details_data[name].append((
        unchecked_char, parameter, actual_reading, standard_reading, acceptable_range,
        f"{error_percentage:.2f}%"
    ))

for item in tree.get_children():
    entry_name = tree.item(item, 'values')[1]
    if entry_name in details_data:
        any_out_of_range = False
        problems = []

        for detail in details_data[entry_name]:
            actual_reading = float(detail[2])
            min_range, max_range = map(float, detail[4].split('-'))

            if not (min_range <= actual_reading <= max_range):
                any_out_of_range = True
                problems.append(detail[1])

        if any_out_of_range:
            tree.item(item, values=(
                tree.item(item, 'values')[0], entry_name, tree.item(item, 'values')[2], "No", ", ".join(problems),
                tree.item(item, 'values')[5]))
        else:
            tree.item(item, values=(
                tree.item(item, 'values')[0], entry_name, tree.item(item, 'values')[2], "Yes", "No",
                tree.item(item, 'values')[5]))



tree.bind("<ButtonRelease-1>", toggle_selection)
tree.bind("<Double-1>", on_double_click)

root.mainloop()
