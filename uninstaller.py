import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import winreg
import subprocess
import os
import shutil
import threading
from pathlib import Path

class UninstallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TraceWipe - Complete Uninstaller")
        self.root.geometry("1000x750")
        self.root.configure(bg="#f5f5f5")
        
        self.installed_apps = []
        self.selected_app = None
        
        # Color scheme
        self.colors = {
            'primary': '#2196F3',
            'danger': '#f44336',
            'success': '#4CAF50',
            'bg': '#f5f5f5',
            'card': '#ffffff',
            'text': '#333333',
            'text_light': '#666666',
            'border': '#e0e0e0'
        }
        
        self.create_widgets()
        self.load_installed_apps()
    
    def create_widgets(self):
        # Header Frame
        header_frame = tk.Frame(self.root, bg=self.colors['primary'], height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Title with icon
        title_container = tk.Frame(header_frame, bg=self.colors['primary'])
        title_container.pack(expand=True)
        
        title = tk.Label(title_container, text="TraceWipe", 
                        font=("Segoe UI", 24, "bold"),
                        bg=self.colors['primary'], fg="white")
        title.pack(side=tk.LEFT, padx=10)
        
        subtitle = tk.Label(title_container, text="Complete Application Removal", 
                           font=("Segoe UI", 10),
                           bg=self.colors['primary'], fg="#e3f2fd")
        subtitle.pack(side=tk.LEFT, padx=5)
        
        # Main content area
        content_frame = tk.Frame(self.root, bg=self.colors['bg'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # App list card
        list_card = tk.Frame(content_frame, bg=self.colors['card'], 
                            relief=tk.FLAT, bd=0)
        list_card.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Card header
        list_header = tk.Frame(list_card, bg=self.colors['card'])
        list_header.pack(fill=tk.X, padx=20, pady=(15, 10))
        
        tk.Label(list_header, text="Installed Applications", 
                font=("Segoe UI", 12, "bold"),
                bg=self.colors['card'], fg=self.colors['text']).pack(side=tk.LEFT)
        
        self.app_count_label = tk.Label(list_header, text="0 apps", 
                                        font=("Segoe UI", 9),
                                        bg=self.colors['card'], 
                                        fg=self.colors['text_light'])
        self.app_count_label.pack(side=tk.LEFT, padx=10)
        
        # Search box
        search_frame = tk.Frame(list_card, bg=self.colors['card'])
        search_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        tk.Label(search_frame, text="Search:", font=("Segoe UI", 9),
                bg=self.colors['card'], fg=self.colors['text_light']).pack(side=tk.LEFT, padx=(0, 5))
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_apps)
        search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                               font=("Segoe UI", 10), relief=tk.FLAT,
                               bg="#f9f9f9", fg=self.colors['text'])
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        
        # Treeview with custom style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview",
                       background=self.colors['card'],
                       foreground=self.colors['text'],
                       fieldbackground=self.colors['card'],
                       borderwidth=0,
                       font=("Segoe UI", 9))
        style.configure("Treeview.Heading",
                       background="#f0f0f0",
                       foreground=self.colors['text'],
                       borderwidth=0,
                       font=("Segoe UI", 10, "bold"))
        style.map('Treeview', background=[('selected', self.colors['primary'])])
        
        tree_frame = tk.Frame(list_card, bg=self.colors['card'])
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
        
        columns = ("Name", "Publisher", "Version")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=12)
        
        self.tree.heading("Name", text="Application Name")
        self.tree.heading("Publisher", text="Publisher")
        self.tree.heading("Version", text="Version")
        
        self.tree.column("Name", width=400)
        self.tree.column("Publisher", width=250)
        self.tree.column("Version", width=120)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Action buttons with modern styling
        btn_frame = tk.Frame(content_frame, bg=self.colors['bg'])
        btn_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Button style helper
        def create_button(parent, text, command, bg_color, icon=""):
            btn = tk.Button(parent, text=f"{icon} {text}".strip(), command=command,
                          bg=bg_color, fg="white", font=("Segoe UI", 10, "bold"),
                          relief=tk.FLAT, cursor="hand2", padx=25, pady=10,
                          activebackground=bg_color, activeforeground="white")
            btn.pack(side=tk.LEFT, padx=5)
            
            # Hover effect
            def on_enter(e):
                btn['background'] = self.adjust_color(bg_color, -20)
            def on_leave(e):
                btn['background'] = bg_color
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)
            return btn
        
        create_button(btn_frame, "Refresh List", self.load_installed_apps, 
                     self.colors['success'], "↻")
        create_button(btn_frame, "Uninstall Selected", self.uninstall_app, 
                     self.colors['danger'], "✕")
        create_button(btn_frame, "Scan for Leftovers", self.scan_leftovers, 
                     self.colors['primary'], "🔍")
        
        # Log card
        log_card = tk.Frame(content_frame, bg=self.colors['card'], 
                           relief=tk.FLAT, bd=0)
        log_card.pack(fill=tk.BOTH, expand=True)
        
        log_header = tk.Frame(log_card, bg=self.colors['card'])
        log_header.pack(fill=tk.X, padx=20, pady=(15, 10))
        
        tk.Label(log_header, text="Activity Log", 
                font=("Segoe UI", 12, "bold"),
                bg=self.colors['card'], fg=self.colors['text']).pack(side=tk.LEFT)
        
        log_content = tk.Frame(log_card, bg=self.colors['card'])
        log_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
        
        self.log_text = scrolledtext.ScrolledText(log_content, height=8, wrap=tk.WORD,
                                                  font=("Consolas", 9),
                                                  bg="#f9f9f9", fg=self.colors['text'],
                                                  relief=tk.FLAT, padx=10, pady=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def adjust_color(self, hex_color, amount):
        """Adjust color brightness for hover effects"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        rgb = tuple(max(0, min(255, c + amount)) for c in rgb)
        return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'
    
    def filter_apps(self, *args):
        """Filter apps based on search query"""
        query = self.search_var.get().lower()
        self.tree.delete(*self.tree.get_children())
        
        filtered_apps = [app for app in self.installed_apps 
                        if query in app["name"].lower() or 
                           query in app["publisher"].lower()]
        
        for app in filtered_apps:
            self.tree.insert("", tk.END, values=(app["name"], app["publisher"], app["version"]))
    
    def log(self, message):
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def load_installed_apps(self):
        self.log("Loading installed applications...")
        self.tree.delete(*self.tree.get_children())
        self.installed_apps = []
        
        def get_apps_from_registry(hive, key_path):
            apps = []
            try:
                key = winreg.OpenKey(hive, key_path)
                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        subkey = winreg.OpenKey(key, subkey_name)
                        
                        try:
                            name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                            publisher = ""
                            version = ""
                            uninstall_string = ""
                            
                            try:
                                publisher = winreg.QueryValueEx(subkey, "Publisher")[0]
                            except:
                                pass
                            
                            try:
                                version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                            except:
                                pass
                            
                            try:
                                uninstall_string = winreg.QueryValueEx(subkey, "UninstallString")[0]
                            except:
                                pass
                            
                            if name and uninstall_string:
                                apps.append({
                                    "name": name,
                                    "publisher": publisher,
                                    "version": version,
                                    "uninstall_string": uninstall_string
                                })
                        except:
                            pass
                        
                        winreg.CloseKey(subkey)
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(key)
            except:
                pass
            return apps
        
        # Get apps from both 32-bit and 64-bit registry
        uninstall_paths = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
        ]
        
        for path in uninstall_paths:
            self.installed_apps.extend(get_apps_from_registry(winreg.HKEY_LOCAL_MACHINE, path))
            self.installed_apps.extend(get_apps_from_registry(winreg.HKEY_CURRENT_USER, path))
        
        # Remove duplicates
        seen = set()
        unique_apps = []
        for app in self.installed_apps:
            if app["name"] not in seen:
                seen.add(app["name"])
                unique_apps.append(app)
        
        self.installed_apps = sorted(unique_apps, key=lambda x: x["name"].lower())
        
        # Populate tree
        for app in self.installed_apps:
            self.tree.insert("", tk.END, values=(app["name"], app["publisher"], app["version"]))
        
        self.log(f"Found {len(self.installed_apps)} installed applications.")
    
    def uninstall_app(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an application to uninstall.")
            return
        
        item = self.tree.item(selection[0])
        app_name = item["values"][0]
        
        # Find the app in our list
        app = next((a for a in self.installed_apps if a["name"] == app_name), None)
        if not app:
            messagebox.showerror("Error", "Application not found.")
            return
        
        confirm = messagebox.askyesno("Confirm Uninstall", 
                                      f"Are you sure you want to uninstall:\n{app_name}?")
        if not confirm:
            return
        
        self.selected_app = app_name
        self.log(f"Uninstalling: {app_name}")
        
        def uninstall_thread():
            try:
                uninstall_cmd = app["uninstall_string"]
                
                # Run uninstaller
                if "msiexec" in uninstall_cmd.lower():
                    subprocess.run(uninstall_cmd, shell=True)
                else:
                    subprocess.run(uninstall_cmd, shell=True)
                
                self.log(f"Uninstall command executed for {app_name}")
                self.log("Please complete the uninstaller wizard if it appeared.")
                
                messagebox.showinfo("Uninstall Started", 
                                  "Uninstaller has been launched. After completion, click 'Scan for Leftovers'.")
                
            except Exception as e:
                self.log(f"Error during uninstall: {str(e)}")
                messagebox.showerror("Error", f"Failed to uninstall: {str(e)}")
        
        thread = threading.Thread(target=uninstall_thread)
        thread.start()
    
    def scan_leftovers(self):
        if not self.selected_app:
            app_name = tk.simpledialog.askstring("App Name", 
                                                "Enter the name of the uninstalled application:")
            if not app_name:
                return
            self.selected_app = app_name
        
        self.log(f"Scanning for leftovers of: {self.selected_app}")
        
        def scan_thread():
            leftovers = []
            search_name = self.selected_app.lower()
            
            # Common locations to check
            locations = [
                os.path.expandvars(r"%APPDATA%"),
                os.path.expandvars(r"%LOCALAPPDATA%"),
                os.path.expandvars(r"%PROGRAMDATA%"),
                os.path.expandvars(r"%PROGRAMFILES%"),
                os.path.expandvars(r"%PROGRAMFILES(X86)%")
            ]
            
            for location in locations:
                if not os.path.exists(location):
                    continue
                
                try:
                    for item in os.listdir(location):
                        if search_name in item.lower():
                            full_path = os.path.join(location, item)
                            leftovers.append(full_path)
                except:
                    pass
            
            if leftovers:
                self.log(f"Found {len(leftovers)} potential leftover items:")
                for item in leftovers:
                    self.log(f"  - {item}")
                
                confirm = messagebox.askyesno("Leftovers Found", 
                                            f"Found {len(leftovers)} leftover items.\n\nDo you want to delete them?")
                if confirm:
                    self.clean_leftovers(leftovers)
            else:
                self.log("No leftovers found.")
                messagebox.showinfo("Clean", "No leftover files or folders found!")
        
        thread = threading.Thread(target=scan_thread)
        thread.start()
    
    def clean_leftovers(self, leftovers):
        self.log("Cleaning up leftovers...")
        cleaned = 0
        failed = 0
        
        for item in leftovers:
            try:
                if os.path.isfile(item):
                    os.remove(item)
                    self.log(f"Deleted file: {item}")
                    cleaned += 1
                elif os.path.isdir(item):
                    shutil.rmtree(item)
                    self.log(f"Deleted folder: {item}")
                    cleaned += 1
            except Exception as e:
                self.log(f"Failed to delete {item}: {str(e)}")
                failed += 1
        
        self.log(f"Cleanup complete. Deleted: {cleaned}, Failed: {failed}")
        messagebox.showinfo("Cleanup Complete", 
                          f"Successfully deleted {cleaned} items.\n{failed} items could not be deleted.")

if __name__ == "__main__":
    root = tk.Tk()
    app = UninstallerApp(root)
    root.mainloop()
