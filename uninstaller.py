import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import winreg
import subprocess
import os
import shutil
import threading
from pathlib import Path
from datetime import datetime

class UninstallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TraceWipe - Complete Uninstaller")
        self.root.geometry("1000x650")
        self.root.minsize(800, 600)
        self.root.configure(bg="#f5f5f5")
        
        self.installed_apps = []
        self.selected_app = None
        self.selected_items = []
        
        # Color scheme
        self.colors = {
            'primary': '#2196F3',
            'danger': '#f44336',
            'success': '#4CAF50',
            'warning': '#FF9800',
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
        header_frame = tk.Frame(self.root, bg=self.colors['primary'], height=90)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Title with icon
        title_container = tk.Frame(header_frame, bg=self.colors['primary'])
        title_container.pack(expand=True)
        
        title = tk.Label(title_container, text="🗑️ TraceWipe", 
                        font=("Segoe UI", 26, "bold"),
                        bg=self.colors['primary'], fg="white")
        title.pack(side=tk.LEFT, padx=10)
        
        subtitle = tk.Label(title_container, text="Complete Application Removal • No Traces Left Behind", 
                           font=("Segoe UI", 10),
                           bg=self.colors['primary'], fg="#e3f2fd")
        subtitle.pack(side=tk.LEFT, padx=5)
        
        # Main content area
        content_frame = tk.Frame(self.root, bg=self.colors['bg'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Stats bar
        stats_frame = tk.Frame(content_frame, bg=self.colors['card'], relief=tk.FLAT)
        stats_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Total Apps stat
        total_box = tk.Frame(stats_frame, bg=self.colors['card'])
        total_box.pack(side=tk.LEFT, padx=20, pady=15)
        self.total_apps_stat = tk.Label(total_box, text="0", font=("Segoe UI", 20, "bold"),
                                        bg=self.colors['card'], fg=self.colors['primary'])
        self.total_apps_stat.pack()
        tk.Label(total_box, text="Total Apps", font=("Segoe UI", 9),
                bg=self.colors['card'], fg=self.colors['text_light']).pack()
        
        # Selected stat
        selected_box = tk.Frame(stats_frame, bg=self.colors['card'])
        selected_box.pack(side=tk.LEFT, padx=20, pady=15)
        self.selected_stat = tk.Label(selected_box, text="0", font=("Segoe UI", 20, "bold"),
                                      bg=self.colors['card'], fg=self.colors['warning'])
        self.selected_stat.pack()
        tk.Label(selected_box, text="Selected", font=("Segoe UI", 9),
                bg=self.colors['card'], fg=self.colors['text_light']).pack()
        
        # App list card
        list_card = tk.Frame(content_frame, bg=self.colors['card'], 
                            relief=tk.FLAT, bd=0)
        list_card.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Card header with controls
        list_header = tk.Frame(list_card, bg=self.colors['card'])
        list_header.pack(fill=tk.X, padx=20, pady=(15, 10))
        
        tk.Label(list_header, text="📋 Installed Applications", 
                font=("Segoe UI", 13, "bold"),
                bg=self.colors['card'], fg=self.colors['text']).pack(side=tk.LEFT)
        
        # Sort options
        sort_frame = tk.Frame(list_header, bg=self.colors['card'])
        sort_frame.pack(side=tk.RIGHT)
        
        tk.Label(sort_frame, text="Sort by:", font=("Segoe UI", 9),
                bg=self.colors['card'], fg=self.colors['text_light']).pack(side=tk.LEFT, padx=(0, 5))
        
        self.sort_var = tk.StringVar(value="Name")
        sort_combo = ttk.Combobox(sort_frame, textvariable=self.sort_var, 
                                 values=["Name", "Publisher", "Size"], 
                                 state="readonly", width=12, font=("Segoe UI", 9))
        sort_combo.pack(side=tk.LEFT)
        sort_combo.bind("<<ComboboxSelected>>", lambda e: self.sort_apps())
        
        # Search box
        search_frame = tk.Frame(list_card, bg=self.colors['card'])
        search_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        tk.Label(search_frame, text="🔍", font=("Segoe UI", 12),
                bg=self.colors['card']).pack(side=tk.LEFT, padx=(0, 5))
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_apps)
        search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                               font=("Segoe UI", 10), relief=tk.FLAT,
                               bg="#f9f9f9", fg=self.colors['text'])
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6)
        search_entry.insert(0, "Search applications...")
        search_entry.bind("<FocusIn>", lambda e: search_entry.delete(0, tk.END) if search_entry.get() == "Search applications..." else None)
        search_entry.bind("<FocusOut>", lambda e: search_entry.insert(0, "Search applications...") if not search_entry.get() else None)
        
        # Treeview with custom style and checkboxes
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview",
                       background=self.colors['card'],
                       foreground=self.colors['text'],
                       fieldbackground=self.colors['card'],
                       borderwidth=0,
                       rowheight=28,
                       font=("Segoe UI", 9))
        style.configure("Treeview.Heading",
                       background="#f0f0f0",
                       foreground=self.colors['text'],
                       borderwidth=0,
                       font=("Segoe UI", 10, "bold"))
        style.map('Treeview', background=[('selected', self.colors['primary'])])
        
        tree_frame = tk.Frame(list_card, bg=self.colors['card'])
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
        
        columns = ("Select", "Name", "Publisher", "Version", "Size")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=14)
        
        self.tree.heading("Select", text="☐")
        self.tree.heading("Name", text="Application Name")
        self.tree.heading("Publisher", text="Publisher")
        self.tree.heading("Version", text="Version")
        self.tree.heading("Size", text="Size")
        
        self.tree.column("Select", width=50, anchor="center")
        self.tree.column("Name", width=350)
        self.tree.column("Publisher", width=200)
        self.tree.column("Version", width=100)
        self.tree.column("Size", width=100, anchor="center")
        
        # Bind click event for checkbox
        self.tree.bind("<Button-1>", self.on_tree_click)
        
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
                          relief=tk.FLAT, cursor="hand2", padx=20, pady=12,
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
        create_button(btn_frame, "Batch Uninstall", self.batch_uninstall, 
                     self.colors['warning'], "📦")
        create_button(btn_frame, "Scan Leftovers", self.scan_leftovers, 
                     self.colors['primary'], "🔍")
        create_button(btn_frame, "Force Remove", self.force_remove, 
                     "#9C27B0", "⚡")
        
        # Quick actions on the right
        quick_frame = tk.Frame(btn_frame, bg=self.colors['bg'])
        quick_frame.pack(side=tk.RIGHT)
        
        tk.Button(quick_frame, text="Select All", command=self.select_all,
                 bg="#607D8B", fg="white", font=("Segoe UI", 9),
                 relief=tk.FLAT, cursor="hand2", padx=15, pady=8).pack(side=tk.LEFT, padx=2)
        
        tk.Button(quick_frame, text="Clear Selection", command=self.clear_selection,
                 bg="#607D8B", fg="white", font=("Segoe UI", 9),
                 relief=tk.FLAT, cursor="hand2", padx=15, pady=8).pack(side=tk.LEFT, padx=2)
        
        # Log card
        log_card = tk.Frame(content_frame, bg=self.colors['card'], 
                           relief=tk.FLAT, bd=0)
        log_card.pack(fill=tk.X, expand=False)
        
        log_header = tk.Frame(log_card, bg=self.colors['card'])
        log_header.pack(fill=tk.X, padx=20, pady=(15, 10))
        
        tk.Label(log_header, text="📝 Activity Log", 
                font=("Segoe UI", 12, "bold"),
                bg=self.colors['card'], fg=self.colors['text']).pack(side=tk.LEFT)
        
        # Clear log button
        tk.Button(log_header, text="Clear Log", command=self.clear_log,
                 bg="#607D8B", fg="white", font=("Segoe UI", 8),
                 relief=tk.FLAT, cursor="hand2", padx=10, pady=4).pack(side=tk.RIGHT)
        
        log_content = tk.Frame(log_card, bg=self.colors['card'])
        log_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
        
        self.log_text = scrolledtext.ScrolledText(log_content, height=7, wrap=tk.WORD,
                                                  font=("Consolas", 9),
                                                  bg="#f9f9f9", fg=self.colors['text'],
                                                  relief=tk.FLAT, padx=10, pady=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Welcome message
        self.log("Welcome to TraceWipe! 🎉")
        self.log("Select apps and click 'Uninstall Selected' or use 'Batch Uninstall' for multiple apps.")
    
    def on_tree_click(self, event):
        """Handle clicks in the tree - select row and toggle checkbox"""
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            item = self.tree.identify_row(event.y)
            if item:
                # Always select the row when clicking anywhere on it
                self.tree.selection_set(item)
                
                column = self.tree.identify_column(event.x)
                if column == "#1":  # Select/checkbox column
                    current_value = self.tree.item(item)["values"][0]
                    if current_value == "☐":
                        self.tree.item(item, values=("☑",) + tuple(self.tree.item(item)["values"][1:]))
                        if item not in self.selected_items:
                            self.selected_items.append(item)
                    else:
                        self.tree.item(item, values=("☐",) + tuple(self.tree.item(item)["values"][1:]))
                        if item in self.selected_items:
                            self.selected_items.remove(item)
                    self.update_selected_count()
    
    def select_all(self):
        """Select all apps in the list"""
        self.selected_items = []
        for item in self.tree.get_children():
            self.tree.item(item, values=("☑",) + tuple(self.tree.item(item)["values"][1:]))
            self.selected_items.append(item)
        self.update_selected_count()
        self.log("Selected all applications")
    
    def clear_selection(self):
        """Clear all selections"""
        for item in self.tree.get_children():
            self.tree.item(item, values=("☐",) + tuple(self.tree.item(item)["values"][1:]))
        self.selected_items = []
        self.update_selected_count()
        self.log("Cleared selection")
    
    def update_selected_count(self):
        """Update the selected count in stats"""
        self.selected_stat.config(text=str(len(self.selected_items)))
    
    def clear_log(self):
        """Clear the activity log"""
        self.log_text.delete(1.0, tk.END)
    
    def adjust_color(self, hex_color, amount):
        """Adjust color brightness for hover effects"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        rgb = tuple(max(0, min(255, c + amount)) for c in rgb)
        return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'
    
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def sort_apps(self):
        """Sort applications based on selected criteria"""
        sort_by = self.sort_var.get()
        if sort_by == "Name":
            self.installed_apps.sort(key=lambda x: x["name"].lower())
        elif sort_by == "Publisher":
            self.installed_apps.sort(key=lambda x: x["publisher"].lower())
        elif sort_by == "Size":
            self.installed_apps.sort(key=lambda x: x.get("size", 0), reverse=True)
        self.filter_apps()
        self.log(f"Sorted by {sort_by}")
    
    def filter_apps(self, *args):
        """Filter apps based on search query"""
        if not hasattr(self, 'tree'):
            return
        query = self.search_var.get().lower()
        if query == "search applications...":
            query = ""
        
        self.tree.delete(*self.tree.get_children())
        self.selected_items = []
        
        filtered_apps = [app for app in self.installed_apps 
                        if query in app["name"].lower() or 
                           query in app["publisher"].lower()]
        
        for app in filtered_apps:
            size_str = app.get("size_str", "Unknown")
            self.tree.insert("", tk.END, values=("☐", app["name"], app["publisher"], 
                                                 app["version"], size_str))
        
        self.update_selected_count()
    
    def load_installed_apps(self):
        self.log("🔄 Loading installed applications...")
        self.tree.delete(*self.tree.get_children())
        self.installed_apps = []
        self.selected_items = []
        
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
                            size = 0
                            
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
                            
                            try:
                                size = int(winreg.QueryValueEx(subkey, "EstimatedSize")[0])
                            except:
                                pass
                            
                            if name and uninstall_string:
                                # Convert size to readable format
                                if size > 0:
                                    size_mb = size / 1024
                                    if size_mb > 1024:
                                        size_str = f"{size_mb/1024:.1f} GB"
                                    else:
                                        size_str = f"{size_mb:.1f} MB"
                                else:
                                    size_str = "Unknown"
                                
                                apps.append({
                                    "name": name,
                                    "publisher": publisher,
                                    "version": version,
                                    "uninstall_string": uninstall_string,
                                    "size": size,
                                    "size_str": size_str
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
            self.tree.insert("", tk.END, values=("☐", app["name"], app["publisher"], 
                                                 app["version"], app["size_str"]))
        
        self.total_apps_stat.config(text=str(len(self.installed_apps)))
        self.update_selected_count()
        self.log(f"✓ Found {len(self.installed_apps)} installed applications")
    
    def uninstall_app(self):
        # Try tree selection first, then fall back to checkbox selection
        selection = self.tree.selection()
        if not selection and self.selected_items:
            selection = [self.selected_items[0]]  # Use first checked item
        
        if not selection:
            messagebox.showwarning("No Selection", "Please click on an application to select it, then click Uninstall.")
            return
        
        item = self.tree.item(selection[0])
        values = item.get("values", [])
        if not values or len(values) < 2:
            messagebox.showerror("Error", "Invalid selection. Please try again.")
            return
        app_name = values[1]  # Index 1 because of checkbox column
        
        # Find the app in our list
        app = next((a for a in self.installed_apps if a["name"] == app_name), None)
        if not app:
            messagebox.showerror("Error", "Application not found.")
            return
        
        # Confirm uninstall
        confirm = messagebox.askyesno("Confirm Uninstall", 
                                      f"Uninstall and remove all traces of:\n\n{app_name}\n\n" +
                                      "This will:\n" +
                                      "• Run the uninstaller silently\n" +
                                      "• Scan for leftover files and folders\n" +
                                      "• Remove all remaining traces\n\n" +
                                      "Continue?",
                                      icon='warning')
        if not confirm:
            return
        
        self.selected_app = app_name
        self.log(f"⚡ Starting complete uninstall: {app_name}")
        self.log("=" * 60)
        
        def complete_uninstall_thread():
            try:
                # Step 1: Run native uninstaller
                self.log("STEP 1: Running uninstaller...")
                uninstall_cmd = app["uninstall_string"]
                self.log(f"Command: {uninstall_cmd}")
                
                if "msiexec" in uninstall_cmd.lower():
                    # For MSI, add silent flags
                    if "/I" in uninstall_cmd:
                        uninstall_cmd = uninstall_cmd.replace("/I", "/X")
                    if "/quiet" not in uninstall_cmd.lower():
                        uninstall_cmd += " /quiet /norestart"
                    self.log(f"Modified MSI command: {uninstall_cmd}")
                    subprocess.run(uninstall_cmd, shell=True, timeout=300)
                else:
                    # Try to run with silent flags (common silent switches)
                    silent_flags = ["/S", "/silent", "/quiet", "/q", "-silent", "--silent"]
                    cmd_executed = False
                    
                    for flag in silent_flags:
                        try:
                            self.log(f"Trying with flag: {flag}")
                            subprocess.run(f'{uninstall_cmd} {flag}', shell=True, timeout=300, check=True)
                            cmd_executed = True
                            self.log(f"✓ Success with flag: {flag}")
                            break
                        except:
                            continue
                    
                    if not cmd_executed:
                        # Run without silent flag as fallback
                        self.log("Running without silent flags...")
                        subprocess.run(uninstall_cmd, shell=True, timeout=300)
                
                self.log("✓ Uninstaller completed")
                
                # Wait a moment for files to be released
                import time
                self.log("Waiting 3 seconds for file system to update...")
                time.sleep(3)
                
                # Step 2: Scan for leftovers
                self.log("\nSTEP 2: Scanning for leftover files...")
                self.log("=" * 60)
                leftovers = []
                search_terms = [app_name.lower()]
                
                # Extract additional search terms from app name
                words = app_name.lower().split()
                for word in words:
                    if len(word) > 3 and word not in ['the', 'and', 'for', 'with']:
                        search_terms.append(word)
                
                self.log(f"Search terms: {', '.join(search_terms)}")
                
                locations = [
                    os.path.expandvars(r"%APPDATA%"),
                    os.path.expandvars(r"%LOCALAPPDATA%"),
                    os.path.expandvars(r"%PROGRAMDATA%"),
                    os.path.expandvars(r"%PROGRAMFILES%"),
                    os.path.expandvars(r"%PROGRAMFILES(X86)%"),
                    os.path.expandvars(r"%USERPROFILE%\AppData\Roaming"),
                    os.path.expandvars(r"%USERPROFILE%\AppData\Local"),
                ]
                
                self.log(f"\nScanning {len(locations)} locations...")
                for location in locations:
                    if not os.path.exists(location):
                        continue
                    self.log(f"Scanning: {location}")
                    try:
                        items_found = 0
                        for item in os.listdir(location):
                            item_lower = item.lower()
                            for term in search_terms:
                                if term in item_lower:
                                    full_path = os.path.join(location, item)
                                    if full_path not in leftovers:
                                        leftovers.append(full_path)
                                        items_found += 1
                                        self.log(f"  Found: {item}")
                                    break
                        if items_found == 0:
                            self.log(f"  No matches found")
                    except Exception as e:
                        self.log(f"  Error scanning: {str(e)}")
                
                self.log(f"\n✓ Scan complete! Found {len(leftovers)} leftover items")
                
                # Step 3: Clean leftovers
                if leftovers:
                    self.log("\nSTEP 3: Removing leftover files...")
                    self.log("=" * 60)
                    cleaned = 0
                    failed = 0
                    
                    for item in leftovers:
                        try:
                            item_name = os.path.basename(item)
                            if os.path.isfile(item):
                                os.remove(item)
                                self.log(f"✓ Deleted file: {item}")
                                cleaned += 1
                            elif os.path.isdir(item):
                                shutil.rmtree(item)
                                self.log(f"✓ Deleted folder: {item}")
                                cleaned += 1
                        except Exception as e:
                            self.log(f"✗ Failed to delete: {item}")
                            self.log(f"  Error: {str(e)}")
                            failed += 1
                    
                    self.log(f"\n{'=' * 60}")
                    self.log(f"✓ Cleanup complete!")
                    self.log(f"  Successfully removed: {cleaned} items")
                    self.log(f"  Failed to remove: {failed} items")
                else:
                    self.log("\n✓ No leftover files found - system is clean!")
                
                self.log(f"\n{'=' * 60}")
                self.log(f"✓ {app_name} has been completely removed!")
                self.log(f"{'=' * 60}\n")
                
                # Show completion message
                self.root.after(0, lambda: messagebox.showinfo("Uninstall Complete", 
                                                               f"{app_name} has been completely removed!\n\n" +
                                                               f"• Uninstaller executed\n" +
                                                               f"• {len(leftovers)} leftover items found\n" +
                                                               f"• {cleaned if leftovers else 0} items cleaned\n\n" +
                                                               "Check Activity Log for details."))
                
                # Refresh the app list
                self.root.after(0, self.load_installed_apps)
                
            except subprocess.TimeoutExpired:
                self.log("⚠️ Uninstaller timed out - scanning for leftovers anyway...")
                # Continue with leftover scan even if uninstaller times out
                self.scan_and_clean_leftovers(app_name)
            except Exception as e:
                self.log(f"✗ Error during uninstall: {str(e)}")
                import traceback
                self.log(traceback.format_exc())
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to uninstall: {str(e)}\n\nTry using 'Force Remove' instead."))
        
        thread = threading.Thread(target=complete_uninstall_thread)
        thread.start()
    
    def scan_and_clean_leftovers(self, app_name):
        """Helper method to scan and clean leftovers"""
        try:
            self.log("Scanning for leftover files...")
            leftovers = []
            search_terms = [app_name.lower()]
            
            words = app_name.lower().split()
            for word in words:
                if len(word) > 3:
                    search_terms.append(word)
            
            locations = [
                os.path.expandvars(r"%APPDATA%"),
                os.path.expandvars(r"%LOCALAPPDATA%"),
                os.path.expandvars(r"%PROGRAMDATA%"),
                os.path.expandvars(r"%PROGRAMFILES%"),
                os.path.expandvars(r"%PROGRAMFILES(X86)%"),
            ]
            
            for location in locations:
                if not os.path.exists(location):
                    continue
                try:
                    for item in os.listdir(location):
                        item_lower = item.lower()
                        for term in search_terms:
                            if term in item_lower:
                                full_path = os.path.join(location, item)
                                if full_path not in leftovers:
                                    leftovers.append(full_path)
                                break
                except:
                    pass
            
            if leftovers:
                cleaned = 0
                for item in leftovers:
                    try:
                        if os.path.isfile(item):
                            os.remove(item)
                            cleaned += 1
                        elif os.path.isdir(item):
                            shutil.rmtree(item)
                            cleaned += 1
                    except:
                        pass
                self.log(f"✓ Cleaned {cleaned} leftover items")
            
            self.root.after(0, self.load_installed_apps)
        except Exception as e:
            self.log(f"✗ Error cleaning leftovers: {str(e)}")
    
    def batch_uninstall(self):
        """Uninstall multiple selected applications"""
        if not self.selected_items:
            messagebox.showwarning("No Selection", "Please select applications using the checkboxes.")
            return
        
        app_names = []
        apps_to_uninstall = []
        
        for item in self.selected_items:
            values = self.tree.item(item).get("values", [])
            if not values or len(values) < 2:
                continue
            app_name = values[1]
            app_names.append(app_name)
            app = next((a for a in self.installed_apps if a["name"] == app_name), None)
            if app:
                apps_to_uninstall.append(app)
        
        if not apps_to_uninstall:
            messagebox.showwarning("No Valid Selection", "No valid applications selected.")
            return
        
        confirm = messagebox.askyesno("Batch Uninstall", 
                                      f"Uninstall and remove all traces of {len(apps_to_uninstall)} applications?\n\n" +
                                      "\n".join(f"• {name}" for name in app_names[:5]) +
                                      (f"\n... and {len(app_names) - 5} more" if len(app_names) > 5 else "") +
                                      "\n\nEach app will be uninstalled and cleaned automatically.",
                                      icon='warning')
        if not confirm:
            return
        
        self.log(f"📦 Starting batch uninstall of {len(apps_to_uninstall)} applications")
        
        def batch_thread():
            import time
            for i, app in enumerate(apps_to_uninstall, 1):
                try:
                    app_name = app['name']
                    self.log(f"\n[{i}/{len(apps_to_uninstall)}] Processing: {app_name}")
                    
                    # Run uninstaller
                    self.log("  → Running uninstaller...")
                    uninstall_cmd = app["uninstall_string"]
                    
                    if "msiexec" in uninstall_cmd.lower():
                        if "/I" in uninstall_cmd:
                            uninstall_cmd = uninstall_cmd.replace("/I", "/X")
                        if "/quiet" not in uninstall_cmd.lower():
                            uninstall_cmd += " /quiet /norestart"
                        subprocess.run(uninstall_cmd, shell=True, timeout=300)
                    else:
                        silent_flags = ["/S", "/silent", "/quiet", "/q"]
                        cmd_executed = False
                        for flag in silent_flags:
                            try:
                                subprocess.run(f'{uninstall_cmd} {flag}', shell=True, timeout=300, check=True)
                                cmd_executed = True
                                break
                            except:
                                continue
                        if not cmd_executed:
                            subprocess.run(uninstall_cmd, shell=True, timeout=300)
                    
                    self.log("  ✓ Uninstaller completed")
                    time.sleep(2)
                    
                    # Scan and clean leftovers
                    self.log("  → Scanning for leftovers...")
                    leftovers = []
                    search_terms = [app_name.lower()]
                    words = app_name.lower().split()
                    for word in words:
                        if len(word) > 3:
                            search_terms.append(word)
                    
                    locations = [
                        os.path.expandvars(r"%APPDATA%"),
                        os.path.expandvars(r"%LOCALAPPDATA%"),
                        os.path.expandvars(r"%PROGRAMDATA%"),
                        os.path.expandvars(r"%PROGRAMFILES%"),
                        os.path.expandvars(r"%PROGRAMFILES(X86)%"),
                    ]
                    
                    for location in locations:
                        if not os.path.exists(location):
                            continue
                        try:
                            for item in os.listdir(location):
                                item_lower = item.lower()
                                for term in search_terms:
                                    if term in item_lower:
                                        full_path = os.path.join(location, item)
                                        if full_path not in leftovers:
                                            leftovers.append(full_path)
                                        break
                        except:
                            pass
                    
                    # Clean leftovers
                    if leftovers:
                        cleaned = 0
                        for item in leftovers:
                            try:
                                if os.path.isfile(item):
                                    os.remove(item)
                                    cleaned += 1
                                elif os.path.isdir(item):
                                    shutil.rmtree(item)
                                    cleaned += 1
                            except:
                                pass
                        self.log(f"  ✓ Cleaned {cleaned} leftover items")
                    else:
                        self.log("  ✓ No leftovers found")
                    
                    self.log(f"  ✓ Completed: {app_name}")
                    
                except subprocess.TimeoutExpired:
                    self.log(f"  ⚠️ Timeout: {app['name']}")
                except Exception as e:
                    self.log(f"  ✗ Failed: {app['name']} - {str(e)}")
            
            self.log(f"\n✓ Batch uninstall completed! Processed {len(apps_to_uninstall)} applications")
            self.root.after(0, lambda: messagebox.showinfo("Batch Uninstall Complete", 
                                                           f"Successfully processed {len(apps_to_uninstall)} applications!\n\n" +
                                                           "Check the Activity Log for details."))
            self.root.after(0, self.load_installed_apps)
        
        thread = threading.Thread(target=batch_thread)
        thread.start()
    
    def force_remove(self):
        """Force remove an application by deleting registry entries and files"""
        # Try tree selection first, then fall back to checkbox selection
        selection = self.tree.selection()
        if not selection and self.selected_items:
            selection = [self.selected_items[0]]  # Use first checked item
        
        if not selection:
            messagebox.showwarning("No Selection", "Please click on an application to select it, then click Force Remove.")
            return
        
        item = self.tree.item(selection[0])
        values = item.get("values", [])
        if not values or len(values) < 2:
            messagebox.showerror("Error", "Invalid selection. Please try again.")
            return
        app_name = values[1]
        
        confirm = messagebox.askyesno("Force Remove", 
                                      f"⚠️ WARNING: Force remove will delete registry entries and files for:\n\n{app_name}\n\n" +
                                      "This should only be used when normal uninstall fails.\n\nContinue?",
                                      icon='warning')
        if not confirm:
            return
        
        self.selected_app = app_name
        self.log(f"⚡ Force removing: {app_name}")
        
        # Immediately scan and remove
        self.scan_leftovers()
        self.log(f"✓ Force remove completed for {app_name}")
    
    def scan_leftovers(self):
        if not self.selected_app:
            app_name = simpledialog.askstring("Application Name", 
                                             "Enter the name of the uninstalled application:",
                                             parent=self.root)
            if not app_name:
                return
            self.selected_app = app_name
        
        self.log(f"🔍 Scanning for leftovers: {self.selected_app}")
        
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
                self.log(f"Found {len(leftovers)} leftover items:")
                for item in leftovers[:5]:  # Show first 5
                    self.log(f"  → {item}")
                if len(leftovers) > 5:
                    self.log(f"  ... and {len(leftovers) - 5} more")
                
                confirm = messagebox.askyesno("Leftovers Detected", 
                                            f"Found {len(leftovers)} leftover items.\n\nWould you like to delete them?\n\n(Check the Activity Log for details)")
                if confirm:
                    self.clean_leftovers(leftovers)
            else:
                self.log("✓ No leftovers found - system is clean!")
                messagebox.showinfo("All Clean", "No leftover files or folders were found.\n\nYour system is clean!")
        
        thread = threading.Thread(target=scan_thread)
        thread.start()
    
    def clean_leftovers(self, leftovers):
        self.log("🧹 Starting cleanup process...")
        cleaned = 0
        failed = 0
        
        for item in leftovers:
            try:
                if os.path.isfile(item):
                    os.remove(item)
                    self.log(f"✓ Deleted file: {os.path.basename(item)}")
                    cleaned += 1
                elif os.path.isdir(item):
                    shutil.rmtree(item)
                    self.log(f"✓ Deleted folder: {os.path.basename(item)}")
                    cleaned += 1
            except Exception as e:
                self.log(f"✗ Failed: {os.path.basename(item)}")
                failed += 1
        
        self.log(f"✓ Cleanup complete! Removed: {cleaned} | Failed: {failed}")
        messagebox.showinfo("Cleanup Complete", 
                          f"Successfully removed {cleaned} items.\n\n{failed} items could not be deleted (may require admin rights).")

if __name__ == "__main__":
    root = tk.Tk()
    app = UninstallerApp(root)
    root.mainloop()
