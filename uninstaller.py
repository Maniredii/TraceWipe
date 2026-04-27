import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import winreg
import subprocess
import os
import shutil
import threading
import webbrowser
from pathlib import Path
from datetime import datetime

class UninstallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TraceWipe - Complete Uninstaller")
        self.root.geometry("1100x700")
        self.root.minsize(1000, 650)
        self.root.configure(bg="#f0f2f5")
        
        self.installed_apps = []
        self.selected_app = None
        self.selected_items = []
        
        # Modern Color scheme
        self.colors = {
            'primary': '#0a192f',
            'secondary': '#173d7a',
            'danger': '#f44336',
            'success': '#4CAF50',
            'warning': '#FF9800',
            'bg': '#f0f2f5',
            'card': '#ffffff',
            'text': '#1e293b',
            'text_light': '#64748b',
            'border': '#e2e8f0',
            'accent': '#3b82f6'
        }
        
        self.create_widgets()
        self.load_installed_apps()
        self.check_disclaimer()
        
    def _create_gradient(self, canvas, width, height, color1, color2):
        """Draw a horizontal gradient on a canvas."""
        # Simple approximation of a gradient by drawing rectangles
        r1, g1, b1 = canvas.winfo_rgb(color1)
        r2, g2, b2 = canvas.winfo_rgb(color2)
        
        r_ratio = (r2 - r1) / width
        g_ratio = (g2 - g1) / width
        b_ratio = (b2 - b1) / width
        
        for i in range(width):
            nr = int(r1 + (r_ratio * i))
            ng = int(g1 + (g_ratio * i))
            nb = int(b1 + (b_ratio * i))
            color = f"#{nr>>8:02x}{ng>>8:02x}{nb>>8:02x}"
            canvas.create_line(i, 0, i, height, fill=color)

    def create_widgets(self):
        # ── Menu Bar ──
        menubar = tk.Menu(self.root, bg='#1e293b', fg='white', activebackground=self.colors['accent'],
                          activeforeground='white', font=('Segoe UI', 10), relief=tk.FLAT)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0, bg='white', fg=self.colors['text'], font=('Segoe UI', 10))
        file_menu.add_command(label="↻  Refresh List", command=self.load_installed_apps)
        file_menu.add_separator()
        file_menu.add_command(label="✕  Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Action menu
        action_menu = tk.Menu(menubar, tearoff=0, bg='white', fg=self.colors['text'], font=('Segoe UI', 10))
        action_menu.add_command(label="🗑️  Uninstall Selected", command=self.uninstall_app)
        action_menu.add_command(label="📦  Batch Uninstall", command=self.batch_uninstall)
        action_menu.add_command(label="⚡  Force Remove", command=self.force_remove)
        action_menu.add_separator()
        action_menu.add_command(label="🔍  Scan Leftovers", command=self.scan_leftovers)
        action_menu.add_command(label="📁  Open File Location", command=self.open_selected_file_location)
        menubar.add_cascade(label="Action", menu=action_menu)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0, bg='white', fg=self.colors['text'], font=('Segoe UI', 10))
        view_menu.add_command(label="Select All", command=self.select_all)
        view_menu.add_command(label="Clear Selection", command=self.clear_selection)
        menubar.add_cascade(label="View", menu=view_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0, bg='white', fg=self.colors['text'], font=('Segoe UI', 10))
        help_menu.add_command(label="ℹ️  About TraceWipe", command=self.show_about_dialog)
        help_menu.add_command(label="📜  Privacy Policy & Disclaimer", command=self.show_privacy_policy)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)
        
        # Header Canvas for Gradient
        header_canvas = tk.Canvas(self.root, height=120, bg=self.colors['primary'], highlightthickness=0)
        header_canvas.pack(fill=tk.X)
        # Get correct width
        self.root.update_idletasks() 
        width = self.root.winfo_width() if self.root.winfo_width() > 1 else 1920
        # Draw gradient extra wide to cover window maximization
        self._create_gradient(header_canvas, max(width, 4000), 120, self.colors['primary'], self.colors['secondary'])
        
        # Remove empty header_content frame that was obscuring the canvas
        # Load Logo
        try:
            import base64
            from assets import LOGO_B64
            self.logo_img = tk.PhotoImage(data=LOGO_B64)
            # Center the 120x120 logo in the 120px tall header
            header_canvas.create_image(40, 60, image=self.logo_img, anchor=tk.W)
            text_x = 180
        except Exception as e:
            text_x = 40
            
        header_canvas.create_text(text_x, 45, text="TraceWipe", font=("Segoe UI", 28, "bold"), fill="white", anchor=tk.W)
        header_canvas.create_text(text_x, 85, text="Complete Application Removal • No Traces Left Behind", font=("Segoe UI", 11), fill="#cbd5e1", anchor=tk.W)
        
        # About Us button on top-right of header
        about_btn = tk.Button(self.root, text="ℹ  About Us", font=("Segoe UI", 10),
                              bg="#1e3a5f", fg="#e2e8f0", relief=tk.FLAT, bd=0,
                              activebackground="#2d4a6f", activeforeground="white",
                              cursor="hand2", padx=14, pady=4,
                              command=self.show_about_dialog)
        header_canvas.create_window(width - 30, 20, anchor=tk.NE, window=about_btn)
        
        # Main content area
        content_frame = tk.Frame(self.root, bg=self.colors['bg'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        # Stats and Actions Card (Horizontal)
        top_card = tk.Frame(content_frame, bg=self.colors['card'], relief=tk.FLAT, bd=0)
        top_card.pack(fill=tk.X, pady=(0, 20))
        
        # Stats area (Left)
        stats_area = tk.Frame(top_card, bg=self.colors['card'])
        stats_area.pack(side=tk.LEFT, padx=30, pady=20)
        
        total_box = tk.Frame(stats_area, bg=self.colors['card'])
        total_box.pack(side=tk.LEFT, padx=(0, 40))
        self.total_apps_stat = tk.Label(total_box, text="0", font=("Segoe UI", 28, "bold"), bg=self.colors['card'], fg=self.colors['accent'])
        self.total_apps_stat.pack()
        tk.Label(total_box, text="Total Applications", font=("Segoe UI", 10), bg=self.colors['card'], fg=self.colors['text_light']).pack()
        
        selected_box = tk.Frame(stats_area, bg=self.colors['card'])
        selected_box.pack(side=tk.LEFT)
        self.selected_stat = tk.Label(selected_box, text="0", font=("Segoe UI", 28, "bold"), bg=self.colors['card'], fg=self.colors['success'])
        self.selected_stat.pack()
        tk.Label(selected_box, text="Selected", font=("Segoe UI", 10), bg=self.colors['card'], fg=self.colors['text_light']).pack()
        
        # Divider
        tk.Frame(top_card, width=1, bg=self.colors['border']).pack(side=tk.LEFT, fill=tk.Y, pady=15, padx=20)
        
        # Actions area (Right)
        actions_area = tk.Frame(top_card, bg=self.colors['card'])
        actions_area.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=20, pady=15)
        
        def create_action_btn(parent, icon, title, subtitle, command, color):
            btn_frame = tk.Frame(parent, bg=self.colors['card'], cursor="hand2")
            btn_frame.pack(side=tk.LEFT, expand=True)
            
            icon_lbl = tk.Label(btn_frame, text=icon, font=("Segoe UI", 20), fg=color, bg=self.colors['card'])
            icon_lbl.pack()
            title_lbl = tk.Label(btn_frame, text=title, font=("Segoe UI", 11, "bold"), fg=self.colors['text'], bg=self.colors['card'])
            title_lbl.pack()
            sub_lbl = tk.Label(btn_frame, text=subtitle, font=("Segoe UI", 8), fg=self.colors['text_light'], bg=self.colors['card'])
            sub_lbl.pack()
            
            # Bind clicks
            for w in [btn_frame, icon_lbl, title_lbl, sub_lbl]:
                w.bind("<Button-1>", lambda e, c=command: c())
                w.bind("<Enter>", lambda e, bf=btn_frame: btn_frame.configure(bg="#f8fafc"))
                w.bind("<Leave>", lambda e, bf=btn_frame: btn_frame.configure(bg=self.colors['card']))
                
        create_action_btn(actions_area, "🗑️", "Uninstall", "Uninstall selected apps", self.uninstall_app, self.colors['accent'])
        create_action_btn(actions_area, "⚡", "Force Remove", "Remove stubborn apps", self.force_remove, self.colors['danger'])
        create_action_btn(actions_area, "🔍", "Deep Scan", "Find leftover traces", self.scan_leftovers, self.colors['primary'])
        create_action_btn(actions_area, "↻", "Refresh", "Refresh application list", self.load_installed_apps, self.colors['success'])
        
        # App list card
        list_card = tk.Frame(content_frame, bg=self.colors['card'], relief=tk.FLAT, bd=0)
        list_card.pack(fill=tk.BOTH, expand=True)
        
        # Card header with search and sort
        list_header = tk.Frame(list_card, bg=self.colors['card'])
        list_header.pack(fill=tk.X, padx=20, pady=(15, 10))
        
        tk.Label(list_header, text="📱 Installed Applications", font=("Segoe UI", 12, "bold"), bg=self.colors['card'], fg=self.colors['text']).pack(side=tk.LEFT)
        
        # Search box
        search_frame = tk.Frame(list_header, bg="#f1f5f9", relief=tk.FLAT, bd=1)
        search_frame.pack(side=tk.LEFT, padx=30, fill=tk.X, expand=True)
        tk.Label(search_frame, text="🔍", font=("Segoe UI", 10), bg="#f1f5f9", fg=self.colors['text_light']).pack(side=tk.LEFT, padx=10)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_apps)
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=("Segoe UI", 10), relief=tk.FLAT, bg="#f1f5f9", fg=self.colors['text'])
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8)
        search_entry.insert(0, "Search applications...")
        search_entry.bind("<FocusIn>", lambda e: search_entry.delete(0, tk.END) if search_entry.get() == "Search applications..." else None)
        search_entry.bind("<FocusOut>", lambda e: search_entry.insert(0, "Search applications...") if not search_entry.get() else None)
        
        # Sort options
        sort_frame = tk.Frame(list_header, bg=self.colors['card'])
        sort_frame.pack(side=tk.RIGHT)
        tk.Label(sort_frame, text="Sort by:", font=("Segoe UI", 9), bg=self.colors['card'], fg=self.colors['text_light']).pack(side=tk.LEFT, padx=(0, 5))
        self.sort_var = tk.StringVar(value="Name")
        sort_combo = ttk.Combobox(sort_frame, textvariable=self.sort_var, values=["Name", "Publisher", "Size"], state="readonly", width=12, font=("Segoe UI", 9))
        sort_combo.pack(side=tk.LEFT)
        sort_combo.bind("<<ComboboxSelected>>", lambda e: self.sort_apps())
        
        # Treeview
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", background=self.colors['card'], foreground=self.colors['text'], fieldbackground=self.colors['card'], borderwidth=0, rowheight=32, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", background="#f8fafc", foreground=self.colors['text_light'], borderwidth=0, font=("Segoe UI", 9, "bold"))
        style.map('Treeview', background=[('selected', '#e2e8f0')], foreground=[('selected', self.colors['text'])])
        
        tree_frame = tk.Frame(list_card, bg=self.colors['card'])
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
        
        columns = ("Select", "Name", "Publisher", "Version", "Size", "InstalledOn")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10)
        self.tree.heading("Select", text="☐")
        self.tree.heading("Name", text="Application Name")
        self.tree.heading("Publisher", text="Publisher")
        self.tree.heading("Version", text="Version")
        self.tree.heading("Size", text="Size")
        self.tree.heading("InstalledOn", text="Installed On")
        
        self.tree.column("Select", width=40, anchor="center")
        self.tree.column("Name", width=300)
        self.tree.column("Publisher", width=180)
        self.tree.column("Version", width=90)
        self.tree.column("Size", width=80, anchor="center")
        self.tree.column("InstalledOn", width=100, anchor="center")
        
        self.tree.bind("<Button-1>", self.on_tree_click)
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Log frame hidden by default, expandable if needed, or put at bottom
        self.log_frame = tk.Frame(self.root, bg=self.colors['card'])
        self.log_text = scrolledtext.ScrolledText(self.log_frame, height=5, font=("Consolas", 9))
        # Not packing log to match UI, we will popup log or print it
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
                    
    def on_tree_double_click(self, event):
        """Handle double-click on a row to open install location"""
        item = self.tree.identify_row(event.y)
        if item:
            app_name = self.tree.item(item)["values"][1]
            app = next((a for a in self.installed_apps if a["name"] == app_name), None)
            if app and app.get("install_location") and os.path.exists(app["install_location"]):
                os.startfile(app["install_location"])
                self.log(f"📁 Opened folder: {app['install_location']}")
            else:
                self.log(f"⚠️ Install location not available for {app_name}")
    
    def open_selected_file_location(self):
        """Open file location of the currently selected app (from menu bar)"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select an application first.")
            return
        item = selection[0]
        app_name = self.tree.item(item)["values"][1]
        app = next((a for a in self.installed_apps if a["name"] == app_name), None)
        if app and app.get("install_location") and os.path.exists(app["install_location"]):
            os.startfile(app["install_location"])
            self.log(f"📁 Opened folder: {app['install_location']}")
        else:
            messagebox.showinfo("Not Found", f"Install location is not available for '{app_name}'.")
    
    def check_disclaimer(self):
        """Check if user has accepted the disclaimer, if not show it."""
        config_dir = os.path.join(os.environ.get('APPDATA', ''), 'TraceWipe')
        config_file = os.path.join(config_dir, 'accepted.txt')
        
        if not os.path.exists(config_file):
            self.root.after(500, self.show_privacy_policy)
            
    def accept_disclaimer(self, window):
        config_dir = os.path.join(os.environ.get('APPDATA', ''), 'TraceWipe')
        try:
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
            with open(os.path.join(config_dir, 'accepted.txt'), 'w') as f:
                f.write('accepted=true')
        except:
            pass
        window.destroy()

    def show_privacy_policy(self):
        """Show Privacy Policy and Disclaimer dialog"""
        policy_win = tk.Toplevel(self.root)
        policy_win.title("Privacy Policy & Disclaimer")
        policy_win.geometry("650x600")
        policy_win.resizable(False, False)
        policy_win.configure(bg=self.colors['card'])
        policy_win.transient(self.root)
        policy_win.grab_set()
        
        # Center on parent
        policy_win.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 650) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 600) // 2
        policy_win.geometry(f"+{x}+{y}")
        
        header_frame = tk.Frame(policy_win, bg=self.colors['primary'], height=60)
        header_frame.pack(fill=tk.X)
        tk.Label(header_frame, text="Privacy Policy & Disclaimer", font=("Segoe UI", 16, "bold"),
                 bg=self.colors['primary'], fg="white").pack(pady=15)
                 
        content_frame = tk.Frame(policy_win, bg=self.colors['card'], padx=30, pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        text_area = scrolledtext.ScrolledText(content_frame, wrap=tk.WORD, width=60, height=20,
                                              font=("Segoe UI", 10), bg="#f8fafc", fg=self.colors['text'],
                                              relief=tk.FLAT, padx=15, pady=15)
        text_area.pack(fill=tk.BOTH, expand=True)
        
        policy_text = """TraceWipe - Complete Application Removal Engine\n\nDISCLAIMER - USE AT YOUR OWN RISK\n\nTraceWipe is a powerful system utility designed to remove applications and their residual files and registry entries from your system. Because this software interacts directly with the Windows Registry and file system, any mistakes or interruptions during the uninstallation process could potentially lead to system instability, application malfunctions, or other unintended consequences.\n\nThe developer(s) of TraceWipe provide this software "as is" and assume no responsibility for any system errors, data loss, or other problems that may arise from its use.\n\nBY USING TRACEWIPE, YOU ACKNOWLEDGE AND AGREE THAT YOU ARE USING IT ENTIRELY AT YOUR OWN RISK.\n\nAvailable Features:\n• Complete Uninstall: Runs the native uninstaller and cleans leftover traces.\n• Force Remove: Directly deletes an application's files and registry entries without running the native uninstaller. Useful for stubborn or broken applications.\n• Deep Scan for Leftovers: Scans for and removes leftover files, folders, and registry entries associated with uninstalled programs.\n• Batch Uninstall: Select multiple applications and uninstall them sequentially.\n• Safe Registry Cleaning: Targets specific application traces while protecting critical system registry keys.\n\nPrivacy Policy:\nTraceWipe respects your privacy. This application operates entirely locally on your machine. We do not collect, store, transmit, or share any personal data, application usage statistics, or system information. All application logs and activity are stored locally and cleared when the application is closed."""
        
        text_area.insert(tk.END, policy_text)
        text_area.config(state=tk.DISABLED)
        
        btn_frame = tk.Frame(policy_win, bg=self.colors['card'])
        btn_frame.pack(fill=tk.X, pady=(0, 20), padx=30)
        close_btn = tk.Button(btn_frame, text="I Understand & Agree", command=lambda: self.accept_disclaimer(policy_win),
                              bg=self.colors['accent'], fg="white", font=("Segoe UI", 10, "bold"),
                              relief=tk.FLAT, padx=30, pady=8, cursor="hand2")
        close_btn.pack()

    def show_about_dialog(self):
        """Show About dialog with developer info and clickable links"""
        about_win = tk.Toplevel(self.root)
        about_win.title("About TraceWipe")
        about_win.geometry("520x500")
        about_win.resizable(False, False)
        about_win.configure(bg="#0a192f")
        about_win.transient(self.root)
        about_win.grab_set()
        
        # Center on parent
        about_win.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 520) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 500) // 2
        about_win.geometry(f"+{x}+{y}")
        
        # Logo area
        try:
            logo_lbl = tk.Label(about_win, image=self.logo_img, bg="#0a192f")
            logo_lbl.pack(pady=(20, 3))
        except:
            pass
        
        tk.Label(about_win, text="TraceWipe", font=("Segoe UI", 24, "bold"),
                 bg="#0a192f", fg="white").pack(pady=(3, 0))
        tk.Label(about_win, text="Complete Application Removal Engine", font=("Segoe UI", 10),
                 bg="#0a192f", fg="#94a3b8").pack()
        tk.Label(about_win, text="Version 1.0.0", font=("Segoe UI", 9),
                 bg="#0a192f", fg="#64748b").pack(pady=(2, 12))
        
        # Divider
        tk.Frame(about_win, height=1, bg="#1e3a5f").pack(fill=tk.X, padx=60)
        
        # Developer info
        tk.Label(about_win, text="Developer", font=("Segoe UI", 9, "bold"),
                 bg="#0a192f", fg="#64748b").pack(pady=(12, 2))
        tk.Label(about_win, text="Manideep Reddy Eevuri", font=("Segoe UI", 14, "bold"),
                 bg="#0a192f", fg="white").pack()
        
        # Links frame
        links_frame = tk.Frame(about_win, bg="#0a192f")
        links_frame.pack(pady=(12, 0))
        
        # GitHub link
        gh_frame = tk.Frame(links_frame, bg="#0a192f", cursor="hand2")
        gh_frame.pack(pady=3)
        gh_icon = tk.Label(gh_frame, text="\U0001F517", font=("Segoe UI", 11), bg="#0a192f", fg="white")
        gh_icon.pack(side=tk.LEFT)
        gh_link = tk.Label(gh_frame, text="github.com/Maniredii", font=("Segoe UI", 11, "underline"),
                           bg="#0a192f", fg="#3b82f6", cursor="hand2")
        gh_link.pack(side=tk.LEFT, padx=5)
        for w in [gh_frame, gh_icon, gh_link]:
            w.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/Maniredii"))
            w.bind("<Enter>", lambda e: gh_link.configure(fg="#60a5fa"))
            w.bind("<Leave>", lambda e: gh_link.configure(fg="#3b82f6"))
        
        # LinkedIn link
        li_frame = tk.Frame(links_frame, bg="#0a192f", cursor="hand2")
        li_frame.pack(pady=3)
        li_icon = tk.Label(li_frame, text="\U0001F4BC", font=("Segoe UI", 11), bg="#0a192f", fg="white")
        li_icon.pack(side=tk.LEFT)
        li_link = tk.Label(li_frame, text="linkedin.com/in/manideep-reddy-eevuri", font=("Segoe UI", 11, "underline"),
                           bg="#0a192f", fg="#3b82f6", cursor="hand2")
        li_link.pack(side=tk.LEFT, padx=5)
        for w in [li_frame, li_icon, li_link]:
            w.bind("<Button-1>", lambda e: webbrowser.open("https://www.linkedin.com/in/manideep-reddy-eevuri-661659268/"))
            w.bind("<Enter>", lambda e: li_link.configure(fg="#60a5fa"))
            w.bind("<Leave>", lambda e: li_link.configure(fg="#3b82f6"))
        
        # Divider
        tk.Frame(about_win, height=1, bg="#1e3a5f").pack(fill=tk.X, padx=60, pady=(12, 8))
        
        # Contact message
        tk.Label(about_win, text="Want to reach me?",
                 font=("Segoe UI", 10, "bold"), bg="#0a192f", fg="#94a3b8").pack(pady=(0, 2))
        
        contact_msg = tk.Label(about_win,
                 text="LinkedIn is the fastest way to contact me \u2014 feel free to connect!",
                 font=("Segoe UI", 10), bg="#0a192f", fg="#60a5fa", cursor="hand2")
        contact_msg.pack()
        contact_msg.bind("<Button-1>", lambda e: webbrowser.open("https://www.linkedin.com/in/manideep-reddy-eevuri-661659268/"))
        contact_msg.bind("<Enter>", lambda e: contact_msg.configure(fg="#93c5fd", font=("Segoe UI", 10, "underline")))
        contact_msg.bind("<Leave>", lambda e: contact_msg.configure(fg="#60a5fa", font=("Segoe UI", 10)))
        
        # Divider
        tk.Frame(about_win, height=1, bg="#1e3a5f").pack(fill=tk.X, padx=60, pady=(10, 8))
        
        tk.Label(about_win, text="\u00a9 2026 TraceWipe. All rights reserved.",
                 font=("Segoe UI", 8), bg="#0a192f", fg="#475569").pack(pady=(0, 3))
        
        # Close button
        close_btn = tk.Button(about_win, text="Close", command=about_win.destroy,
                              bg="#3b82f6", fg="white", font=("Segoe UI", 10, "bold"),
                              relief=tk.FLAT, padx=30, pady=6, cursor="hand2")
        close_btn.pack(pady=(3, 15))
    
    def show_context_menu(self, event):
        """Show right-click context menu for the selected app"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            menu = tk.Menu(self.root, tearoff=0, font=('Segoe UI', 10))
            menu.add_command(label="✕  Uninstall", command=self.uninstall_app)
            menu.add_command(label="⚡  Force Remove", command=self.force_remove)
            
            app_name = self.tree.item(item)["values"][1]
            app = next((a for a in self.installed_apps if a["name"] == app_name), None)
            
            menu.add_separator()
            if app and app.get("install_location") and os.path.exists(app["install_location"]):
                menu.add_command(label="📁  Open File Location", 
                               command=lambda: os.startfile(app["install_location"]))
            else:
                menu.add_command(label="📁  Open File Location", state=tk.DISABLED)
            
            if app and app.get("registry_path"):
                menu.add_command(label="🔧  Open Registry Entry",
                               command=lambda: self.open_registry_key(app["registry_path"]))
            
            menu.add_separator()
            menu.add_command(label="📋  Copy App Info", 
                           command=lambda: self.copy_app_info(app))
            
            menu.post(event.x_root, event.y_root)
            
    def open_registry_key(self, path):
        try:
            # Set the LastKey so regedit opens to it
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Applets\Regedit", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "LastKey", 0, winreg.REG_SZ, path)
            winreg.CloseKey(key)
            subprocess.Popen(['regedit.exe'])
            self.log(f"🔧 Opened Registry Editor at: {path}")
        except Exception as e:
            self.log(f"⚠️ Failed to open Registry Editor: {e}")
            
    def copy_app_info(self, app):
        if app:
            info = f"Name: {app.get('name', '')}\nPublisher: {app.get('publisher', '')}\nVersion: {app.get('version', '')}\nUninstall String: {app.get('uninstall_string', '')}"
            if app.get('install_location'):
                info += f"\nInstall Location: {app['install_location']}"
            self.root.clipboard_clear()
            self.root.clipboard_append(info)
            self.log(f"📋 Copied info for {app['name']}")
    
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
                                                 app["version"], size_str,
                                                 app.get("install_date", "")))
        
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
                                uninstall_string = winreg.QueryValueEx(subkey, "QuietUninstallString")[0]
                            except:
                                try:
                                    uninstall_string = winreg.QueryValueEx(subkey, "UninstallString")[0]
                                except:
                                    pass
                            
                            try:
                                size = int(winreg.QueryValueEx(subkey, "EstimatedSize")[0])
                            except:
                                pass
                                
                            try:
                                install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                            except:
                                install_location = ""
                            
                            # Read install date
                            install_date_str = ""
                            try:
                                raw_date = winreg.QueryValueEx(subkey, "InstallDate")[0]
                                if raw_date and len(raw_date) == 8:
                                    install_date_str = f"{raw_date[0:4]}-{raw_date[4:6]}-{raw_date[6:8]}"
                                elif raw_date:
                                    install_date_str = str(raw_date)
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
                                    "install_location": install_location,
                                    "size": size,
                                    "size_str": size_str,
                                    "install_date": install_date_str,
                                    "registry_path": ("HKEY_LOCAL_MACHINE\\" if hive == winreg.HKEY_LOCAL_MACHINE else "HKEY_CURRENT_USER\\") + key_path + "\\" + subkey_name
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
                                                 app["version"], app["size_str"],
                                                 app.get("install_date", "")))
        
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
                    # For MSI, convert install flag to uninstall flag
                    if "/I" in uninstall_cmd or "/i" in uninstall_cmd:
                        uninstall_cmd = uninstall_cmd.replace("/I", "/X").replace("/i", "/X")
                    if "/quiet" not in uninstall_cmd.lower() and "/q" not in uninstall_cmd.lower():
                        uninstall_cmd += " /quiet /norestart"
                
                self.log(f"Executing: {uninstall_cmd}")
                
                # Execute the uninstaller and wait for it to finish
                process = subprocess.run(uninstall_cmd, shell=True, timeout=600)
                
                if process.returncode == 0:
                    self.log("✓ Uninstaller completed successfully")
                else:
                    self.log(f"⚠️ Uninstaller exited with code: {process.returncode} (Proceeding anyway)")
                
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
                    os.path.expandvars(r"%TEMP%"),
                    os.path.expandvars(r"%USERPROFILE%\Desktop"),
                    os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
                    os.path.expandvars(r"%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs")
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
                os.path.expandvars(r"%TEMP%"),
                os.path.expandvars(r"%USERPROFILE%\Desktop"),
                os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
                os.path.expandvars(r"%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs")
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
            
            # Now clean registry
            self.clean_registry_leftovers(app_name)
            
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
                        if "/I" in uninstall_cmd or "/i" in uninstall_cmd:
                            uninstall_cmd = uninstall_cmd.replace("/I", "/X").replace("/i", "/X")
                        if "/quiet" not in uninstall_cmd.lower() and "/q" not in uninstall_cmd.lower():
                            uninstall_cmd += " /quiet /norestart"
                            
                    self.log(f"  → Executing: {uninstall_cmd}")
                    process = subprocess.run(uninstall_cmd, shell=True, timeout=600)
                    
                    if process.returncode == 0:
                        self.log("  ✓ Uninstaller completed")
                    else:
                        self.log(f"  ⚠️ Uninstaller exited with code: {process.returncode}")
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
                        os.path.expandvars(r"%TEMP%"),
                        os.path.expandvars(r"%USERPROFILE%\Desktop"),
                        os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
                        os.path.expandvars(r"%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs")
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
                os.path.expandvars(r"%PROGRAMFILES(X86)%"),
                os.path.expandvars(r"%TEMP%"),
                os.path.expandvars(r"%USERPROFILE%\Desktop"),
                os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
                os.path.expandvars(r"%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs")
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

    def clean_registry_leftovers(self, app_name):
        self.log(f"🔍 Scanning registry for leftovers...")
        cleaned = 0
        hives = [
            (winreg.HKEY_CURRENT_USER, r"Software"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node")
        ]
        
        search_terms = [app_name.lower()]
        for word in app_name.lower().split():
            if len(word) > 4 and word not in ['the', 'and', 'for', 'with']:
                search_terms.append(word)

        # Safe deletion: Only delete if the subkey matches the search term closely
        for hive, path in hives:
            try:
                key = winreg.OpenKey(hive, path, 0, winreg.KEY_READ)
                subkeys_to_delete = []
                
                # Enumerate subkeys
                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        if any(term == subkey_name.lower() or term in subkey_name.lower() for term in search_terms):
                            # Very important safety check to prevent destroying system keys
                            if subkey_name.lower() not in ["microsoft", "windows", "policies", "classes", "clients", "intel", "amd", "nvidia", "google"]:
                                subkeys_to_delete.append(subkey_name)
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(key)
                
                # Delete found subkeys
                for subkey in subkeys_to_delete:
                    try:
                        self.delete_registry_key_recursive(hive, f"{path}\\{subkey}")
                        self.log(f"  ✓ Cleaned registry: {path}\\{subkey}")
                        cleaned += 1
                    except Exception as e:
                        pass
            except Exception as e:
                pass
                
        if cleaned > 0:
            self.log(f"✓ Removed {cleaned} leftover registry keys")
        else:
            self.log("✓ No registry leftovers found")

    def delete_registry_key_recursive(self, hive, key_path):
        """Recursively delete a registry key and all its subkeys"""
        try:
            key = winreg.OpenKey(hive, key_path, 0, winreg.KEY_ALL_ACCESS)
            # Delete all subkeys first
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, 0)
                    self.delete_registry_key_recursive(hive, f"{key_path}\\{subkey_name}")
                except OSError:
                    break
            winreg.CloseKey(key)
            winreg.DeleteKey(hive, key_path)
        except OSError:
            pass

if __name__ == "__main__":
    import ctypes
    import sys
    
    # Request admin rights if not already elevated
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        is_admin = False
        
    if not is_admin:
        try:
            # Re-launch with admin privileges
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
        except Exception:
            # User declined UAC or elevation failed — run without admin
            pass
        else:
            # Elevation succeeded — kill this non-admin instance immediately
            # os._exit bypasses all cleanup and cannot be caught by except
            os._exit(0)
            
    # Tell Windows to use our custom icon in the taskbar instead of the default Python feather
    try:
        myappid = 'maniredii.tracewipe.uninstaller.1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except:
        pass
        
    root = tk.Tk()
    
    # Set application window and taskbar icon using the absolute path to the .ico file
    try:
        import os, sys
        # Handle PyInstaller temp directory or normal script directory
        if getattr(sys, 'frozen', False):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
        icon_path = os.path.join(base_dir, 'logo.ico')
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
            
        # Also set iconphoto as a strong fallback (True makes it apply to all windows and taskbar)
        try:
            from assets import LOGO_B64
            icon_img = tk.PhotoImage(data=LOGO_B64)
            root.iconphoto(True, icon_img)
        except:
            pass
    except Exception as e:
        print("Failed to set icon:", e)
        
    app = UninstallerApp(root)
    root.mainloop()
