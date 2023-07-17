import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import webbrowser
import random
import socket
import os
import sys
import ctypes
import subprocess
import re


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_as_admin():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
        sys.exit()


def query_dns(domain, dns_server):
    cmd = f"nslookup {domain} {dns_server}"
    result = subprocess.check_output(cmd, shell=True).decode("utf-8")
    ip_addresses = []
    lines = result.splitlines()
    name_line_index = -1

    for i, line in enumerate(lines):
        if line.startswith("Name:"):
            name_line_index = i
            break

    if name_line_index >= 0:
        for i in range(name_line_index, len(lines)):
            line = lines[i]
            if line.startswith("Address:") or line.startswith("Addresses:"):
                parts = line.split(": ")
                if len(parts) >= 2:
                    # Ignore IPv6 addresses
                    if ":" not in parts[1]:
                        ip_addresses.append(parts[1])
    return {dns_server: ip_addresses}


def save_to_hosts_file(entry):
    domain = entry["domain"]
    ip_address = entry["ip_address"]
    commented = entry["commented"]

    with open('C:\\Windows\\System32\\drivers\\etc\\hosts', 'r') as file:
        lines = file.readlines()

    domain_exists = False
    with open('C:\\Windows\\System32\\drivers\\etc\\hosts', 'w') as file:
        for line in lines:
            stripped_line = line.strip()
            if stripped_line.startswith("#"):
                stripped_line = stripped_line[1:].strip()
            parts = re.split(r'\s+', stripped_line)  # Split by any whitespace characters
            if len(parts) >= 2 and parts[1] == domain:
                domain_exists = True
                if commented:
                    file.write(f"#{ip_address} {domain}\n")
                else:
                    file.write(f"{ip_address} {domain}\n")
            else:
                file.write(line)

        # If the domain doesn't exist in the hosts file, add a new line
        if not domain_exists:
            if commented:
                file.write(f"#{ip_address} {domain}\n")
            else:
                file.write(f"{ip_address} {domain}\n")


def get_hosts_file_entries():
    entries = []
    with open('C:\\Windows\\System32\\drivers\\etc\\hosts', 'r') as hosts_file:
        for line in hosts_file:
            stripped_line = line.strip()
            if stripped_line.startswith("#"):
                stripped_line = stripped_line[1:].strip()
            parts = re.split(r'\s+', stripped_line)  # Split by any whitespace characters
            if len(parts) >= 2 and (parts[0][0].isdigit() or parts[0][0] == ":"):
                ip_address = parts[0]
                domain = parts[1]
                commented = line.startswith('#')
                entry = {"domain": domain, "ip_address": ip_address, "commented": commented}
                entries.append(entry)
    return entries


def update_display():
    entries = get_hosts_file_entries()
    for widget in display_frame.winfo_children():
        widget.destroy()

    for entry in entries:
        domain = entry["domain"]
        ip_address = entry["ip_address"]
        commented = entry["commented"]

        row_frame = ttk.Frame(display_frame)
        row_frame.pack(fill=tk.X)

        remove_button = ttk.Button(row_frame, text="حذف", command=lambda e=entry: remove_entry(e))
        remove_button.pack(side=tk.LEFT, padx=5, pady=5)

        query_403_button = ttk.Button(row_frame, text="403", command=lambda d=domain: query_dns_and_update(d, "dns.403.ir"))
        query_403_button.pack(side=tk.LEFT, padx=5, pady=5)

        query_shecan_button = ttk.Button(row_frame, text="شکن", command=lambda d=domain: query_dns_and_update(d, "dns.shecan.ir"))
        query_shecan_button.pack(side=tk.LEFT, padx=5, pady=5)

        comment_button = ttk.Button(row_frame, text="فعال/غیرفعال", command=lambda e=entry: comment_entry(e))
        comment_button.pack(side=tk.LEFT, padx=5, pady=5)

        label = ttk.Label(row_frame, text=f"{domain}  {ip_address}")
        if commented:
            label.config(foreground="gray")
        label.pack(side=tk.LEFT)

    display_frame.pack(padx=10, pady=10, fill=tk.X)


def process_domain(event=None):
    global answer_frame

    domain = input_field.get()

    if not domain:
        messagebox.showerror("Error", "آدرس سایت را وارد نمایید")
        return

    try:
        dns_results = []
        dns_results.append(query_dns(domain, "dns.shecan.ir"))
        dns_results.append(query_dns(domain, "dns.403.ir"))

        # Destroy previous answer_frame, if any
        if answer_frame:
            answer_frame.destroy()

        answer_frame = ttk.Frame(pane_window)
        pane_window.add(answer_frame)

        ip_listbox = tk.Listbox(answer_frame, selectmode=tk.SINGLE)
        ip_listbox.pack(side=tk.LEFT, padx=5)

        scrollbar = ttk.Scrollbar(answer_frame, orient=tk.VERTICAL, command=ip_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        ip_listbox.config(yscrollcommand=scrollbar.set)

        dns_server_names = {"dns.shecan.ir": "Shecan", "dns.403.ir": "403"}

        for dns_result in dns_results:
            for dns_server, ip_addresses in dns_result.items():
                for ip_address in ip_addresses:
                    ip_listbox.insert(tk.END, f"{dns_server_names[dns_server]}: {ip_address}")

        def save_and_update_hosts():
            selected_index = ip_listbox.curselection()
            if len(selected_index) == 0:
                messagebox.showerror("Error", "لطفا یک گزینه را انتخاب نمایید")
                return

            selected_item = ip_listbox.get(selected_index[0])
            selected_ip = selected_item.split(": ")[1]
            entry = {"domain": domain, "ip_address": selected_ip, "commented": False}
            save_to_hosts_file(entry)
            update_display()
            messagebox.showinfo("Success", "!آدرس جدید ثبت شد")
            answer_frame.destroy()

        save_button = ttk.Button(answer_frame, text="Save", command=save_and_update_hosts)
        save_button.pack(side=tk.LEFT, padx=5)

    except subprocess.CalledProcessError:
        messagebox.showerror("Error", "!نتیجه ای دریافت نشد. ممکن است آدرس سایت اشتباه باشد")


def query_dns_and_update(domain, dns_server):
    try:
        dns_result = query_dns(domain, dns_server)
        for _, ip_addresses in dns_result.items():
            if ip_addresses:
                selected_ip = random.choice(ip_addresses)
                entries = get_hosts_file_entries()
                for entry in entries:
                    if entry["domain"] == domain:
                        entry["ip_address"] = selected_ip
                        save_to_hosts_file(entry)
                        break
                update_display()
                messagebox.showinfo("Success", "!آدرس جدید ثبت شد")
            else:
                messagebox.showwarning("Warning", "!آدرس آی پی برای سایت مورد نظر پیدا نشد")

    except subprocess.CalledProcessError:
        messagebox.showerror("Error", "!موفقیت آمیز نبود. ممکن است آدرس سایت اشتباه باشد")


def comment_entry(entry):
    entry["commented"] = not entry["commented"]
    save_to_hosts_file(entry)
    update_display()
    messagebox.showinfo("Success", "!غیر فعال شد")


def remove_entry(entry):
    domain = entry["domain"]
    with open('C:\\Windows\\System32\\drivers\\etc\\hosts', 'r') as file:
        lines = file.readlines()

    with open('C:\\Windows\\System32\\drivers\\etc\\hosts', 'w') as file:
        for line in lines:
            parts = line.strip().split()
            if len(parts) >= 2 and parts[1] != domain:
                file.write(line)

    update_display()
    messagebox.showinfo("Success", "!حذف شد")


run_as_admin()

window = tk.Tk()
window.title("Liana Anti Sanction - تحریم شکن لیانا - WEBINJA.IR")

top_frame = ttk.Frame(window)
top_frame.pack(padx=10, pady=10, fill=tk.X)


def open_webpage(event):
    webbrowser.open_new(r"http://www.arashnaderian.com")


def open_help_page(event):
    webbrowser.open_new(r"https://webinja.ir/liana-net_tools/liana-anti-sanction/")


link1 = tk.Label(top_frame, text="تهیه شده توسط آرش نادریان", fg="blue", cursor="hand2")
link1.pack(side=tk.LEFT, padx=5)
link1.bind("<Button-1>", open_webpage)

link2 = tk.Label(top_frame, text="راهنما", fg="blue", cursor="hand2")
link2.pack(side=tk.LEFT, padx=5)
link2.bind("<Button-1>", open_help_page)

input_field = ttk.Entry(top_frame)
input_field.pack(side=tk.LEFT, padx=5)
input_field.bind('<Return>', process_domain)

query_button = ttk.Button(top_frame, text="سایت جدید", command=process_domain)
query_button.pack(side=tk.LEFT, padx=5)

refresh_button = ttk.Button(top_frame, text="Refresh", command=update_display)
refresh_button.pack(side=tk.RIGHT, padx=5)

pane_window = ttk.Panedwindow(window, orient=tk.HORIZONTAL)
pane_window.pack(fill=tk.BOTH, expand=1)

left_frame = ttk.Frame(pane_window)
pane_window.add(left_frame)

display_frame = ttk.Frame(left_frame)
display_frame.pack(padx=10, pady=10, fill=tk.X)

answer_frame = None

update_display()

window.mainloop()
