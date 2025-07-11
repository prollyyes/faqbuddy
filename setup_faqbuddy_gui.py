#!/usr/bin/env python3
"""
FAQBuddy GUI Setup Wizard
A beautiful, modern setup wizard with secure environment variable handling.
"""

import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import json
import requests
from dotenv import load_dotenv
import queue

class Colors:
    """Color scheme for the application using Apple design language."""
    PRIMARY = "#007AFF"      # Apple Blue
    SECONDARY = "#8E8E93"    # Apple Gray
    SUCCESS = "#34C759"      # Apple Green
    WARNING = "#FF9500"      # Apple Orange
    ERROR = "#FF3B30"        # Apple Red
    BACKGROUND = "#F2F2F7"   # Apple Light Gray
    CARD_BG = "#FFFFFF"      # White
    TEXT = "#000000"         # Black
    BUTTON_HOVER = "#0056CC" # Darker Apple Blue for hover

class ModernButton(tk.Button):
    """Modern button with improved styling."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(
            relief="flat",
            borderwidth=0,
            cursor="hand2",
            font=("SF Pro Display", 10, "bold"),
            padx=20,
            pady=8
        )
        
    def configure_primary(self):
        """Configure as primary button."""
        self.configure(
            bg=Colors.PRIMARY,
            fg="white",
            activebackground=Colors.BUTTON_HOVER,
            activeforeground="white"
        )
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
    def configure_secondary(self):
        """Configure as secondary button."""
        self.configure(
            bg=Colors.SECONDARY,
            fg="white",
            activebackground="#6D6D70",
            activeforeground="white"
        )
        self.bind("<Enter>", self._on_enter_secondary)
        self.bind("<Leave>", self._on_leave_secondary)
        
    def _on_enter(self, event):
        """Handle mouse enter for primary button."""
        self.configure(bg=Colors.BUTTON_HOVER)
        
    def _on_leave(self, event):
        """Handle mouse leave for primary button."""
        self.configure(bg=Colors.PRIMARY)
        
    def _on_enter_secondary(self, event):
        """Handle mouse enter for secondary button."""
        self.configure(bg="#6D6D70")
        
    def _on_leave_secondary(self, event):
        """Handle mouse leave for secondary button."""
        self.configure(bg=Colors.SECONDARY)

class ModernEntry(tk.Entry):
    """Modern styled entry field."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(
            relief="flat",
            borderwidth=1,
            font=("SF Pro Display", 10),
            bg="white",
            fg=Colors.TEXT,
            insertbackground=Colors.PRIMARY
        )

class ModernLabel(tk.Label):
    """Modern styled label."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(
            font=("SF Pro Display", 10),
            fg=Colors.TEXT,
            bg=Colors.BACKGROUND
        )

class SetupWizard:
    def __init__(self):
        """Initialize the setup wizard."""
        self.root = tk.Tk()
        self.root.title("FAQBuddy Setup Wizard")
        self.root.geometry("900x700")
        self.root.configure(bg=Colors.BACKGROUND)
        self.root.resizable(False, False)
        
        # Center the window
        self.center_window()
        
        # Initialize variables
        self.current_step = -1  # Start with login step
        self.total_steps = 8  # Changed from 7 to 8 to include environment setup step
        self.is_admin = False
        self.env_vars = {}
        self.env_entries = {}
        self.progress_queue = queue.Queue()
        
        # Environment detection variables
        self.python_env = None
        self.env_type = None  # 'venv', 'conda', or 'system'
        self.env_path = None
        
        # Load existing environment variables
        self.load_existing_env()
        
        # Create widgets
        self.create_widgets()
        
        # Start with login screen
        self.show_login_screen()
        
        # Start progress monitoring
        self.monitor_progress()
        
    def center_window(self):
        """Center the window on screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
    def detect_python_environment(self):
        """Detect the current Python environment."""
        try:
            # Check if we're in a virtual environment
            if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
                # We're in a virtual environment
                if hasattr(sys, 'real_prefix'):
                    # This is a virtualenv
                    self.env_type = 'venv'
                    self.env_path = sys.prefix
                else:
                    # This is a venv (Python 3.3+)
                    self.env_type = 'venv'
                    self.env_path = sys.prefix
                return True
            elif 'CONDA_DEFAULT_ENV' in os.environ:
                # We're in a conda environment
                self.env_type = 'conda'
                self.env_path = os.environ.get('CONDA_PREFIX', sys.prefix)
                return True
            else:
                # We're in the system Python
                self.env_type = 'system'
                self.env_path = sys.prefix
                return False
        except Exception as e:
            print(f"Error detecting Python environment: {e}")
            self.env_type = 'system'
            self.env_path = sys.prefix
            return False
    
    def get_python_executable(self):
        """Get the Python executable to use for installations."""
        if self.python_env:
            if self.env_type == 'venv':
                # For virtual environments, use the python executable in the env
                if os.name == 'nt':  # Windows
                    return os.path.join(self.env_path, 'Scripts', 'python.exe')
                else:  # Unix/Linux/macOS
                    return os.path.join(self.env_path, 'bin', 'python')
            elif self.env_type == 'conda':
                # For conda environments, use the conda python
                return os.path.join(self.env_path, 'bin', 'python')
        return sys.executable
        
    def load_existing_env(self):
        """Load existing environment variables from .env file."""
        env_file = Path(".env")
        if env_file.exists():
            load_dotenv()
            self.env_vars = {
                "DB_NEON_NAME": os.getenv("DB_NEON_NAME", "neondb"),
                "DB_NEON_USER": os.getenv("DB_NEON_USER", "neondb_owner"),
                "DB_NEON_PASSWORD": os.getenv("DB_NEON_PASSWORD", "npg_81IXpKWZQxEa"),
                "DB_NEON_HOST": os.getenv("DB_NEON_HOST", "ep-super-credit-a9zsuu7x-pooler.gwc.azure.neon.tech"),
                "DB_NEON_PORT": os.getenv("DB_NEON_PORT", "5432"),
                "PINECONE_API_KEY": os.getenv("PINECONE_API_KEY", "pcsk_6FLreq_PQ9dENviDRu7WwTHg5BF27PWBmFoVMPqJNzrJcNQSWywSns973idr5vqgTixqF2"),
                "EMAIL_FROM": os.getenv("EMAIL_FROM", "tutordimatematica.ing@gmail.com"),
                "EMAIL_PASS": os.getenv("EMAIL_PASS", "ohxrysinakqpryrb"),
                "EMAIL_USER": os.getenv("EMAIL_USER", "tutordimatematica.ing@gmail.com")
            }
        else:
            # Default values if no .env file exists
            self.env_vars = {
                "DB_NEON_NAME": "neondb",
                "DB_NEON_USER": "neondb_owner",
                "DB_NEON_PASSWORD": "npg_81IXpKWZQxEa",
                "DB_NEON_HOST": "ep-super-credit-a9zsuu7x-pooler.gwc.azure.neon.tech",
                "DB_NEON_PORT": "5432",
                "PINECONE_API_KEY": "pcsk_6FLreq_PQ9dENviDRu7WwTHg5BF27PWBmFoVMPqJNzrJcNQSWywSns973idr5vqgTixqF2",
                "EMAIL_FROM": "tutordimatematica.ing@gmail.com",
                "EMAIL_PASS": "ohxrysinakqpryrb",
                "EMAIL_USER": "tutordimatematica.ing@gmail.com"
            }
            
    def create_widgets(self):
        """Create the main UI widgets."""
        # Main container
        self.main_frame = tk.Frame(self.root, bg=Colors.BACKGROUND)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=(20, 0))
        
        # Header
        self.create_header()
        
        # Progress bar
        self.create_progress_bar()
        
        # Content area with scrollbar
        self.create_scrollable_content()
        
        # Navigation
        self.create_navigation()
        
        # Status bar
        self.create_status_bar()
        
    def create_header(self):
        """Create the header section."""
        header_frame = tk.Frame(self.main_frame, bg=Colors.BACKGROUND)
        header_frame.pack(fill="x", pady=(0, 20))
        
        # Title
        title_label = tk.Label(
            header_frame,
            text="🚀 FAQBuddy Setup Wizard",
            font=("Segoe UI", 24, "bold"),
            fg=Colors.PRIMARY,
            bg=Colors.BACKGROUND
        )
        title_label.pack()
        
        # Subtitle
        subtitle_label = tk.Label(
            header_frame,
            text="Configure your intelligent university assistant",
            font=("Segoe UI", 12),
            fg=Colors.SECONDARY,
            bg=Colors.BACKGROUND
        )
        subtitle_label.pack(pady=(5, 0))
        
    def create_progress_bar(self):
        """Create the progress bar."""
        progress_frame = tk.Frame(self.main_frame, bg=Colors.BACKGROUND)
        progress_frame.pack(fill="x", pady=(0, 20))
        
        # Progress label
        self.progress_label = tk.Label(
            progress_frame,
            text="Step 1 of 8: Checking Python Version",
            font=("Segoe UI", 10, "bold"),
            fg=Colors.TEXT,
            bg=Colors.BACKGROUND
        )
        self.progress_label.pack()
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            length=700,
            mode='determinate',
            style='Modern.Horizontal.TProgressbar'
        )
        self.progress_bar.pack(pady=(10, 0))
        
        # Configure progress bar style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            'Modern.Horizontal.TProgressbar',
            background=Colors.PRIMARY,
            troughcolor=Colors.BACKGROUND,
            borderwidth=0,
            lightcolor=Colors.PRIMARY,
            darkcolor=Colors.PRIMARY
        )
        
    def create_scrollable_content(self):
        """Create a scrollable content area."""
        # Create a frame for the scrollable content
        content_container = tk.Frame(self.main_frame, bg=Colors.BACKGROUND)
        content_container.pack(fill="both", expand=True, pady=(20, 10))
        
        # Create canvas and scrollbar
        self.canvas = tk.Canvas(content_container, bg=Colors.BACKGROUND, highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_container, orient="vertical", command=self.canvas.yview)
        
        # Configure canvas
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Create the content frame inside the canvas
        self.content_frame = tk.Frame(self.canvas, bg=Colors.BACKGROUND)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        
        # Configure scrolling
        self.content_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        
        # Bind mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        
    def on_canvas_configure(self, event):
        """Handle canvas resize."""
        # Update the width of the content frame to match the canvas
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)
        
    def on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
    def create_navigation(self):
        """Create fixed bottom navigation buttons."""
        # Create a fixed bottom navigation bar
        nav_frame = tk.Frame(self.root, bg=Colors.BACKGROUND, relief="flat", bd=1)
        nav_frame.pack(side="bottom", fill="x", padx=20, pady=(10, 20))
        
        # Logout button (left side)
        self.logout_btn = tk.Button(
            nav_frame,
            text="🔄 Restart",
            command=self.restart_setup,
            width=10,
            bg=Colors.WARNING,
            fg="white",
            font=("SF Pro Display", 9, "bold"),
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=6,
            activebackground="#E6850E",
            activeforeground="white"
        )
        
        # Back button
        self.back_btn = ModernButton(
            nav_frame,
            text="← Back",
            command=self.previous_step,
            width=10
        )
        self.back_btn.configure_secondary()
        
        # Next button
        self.next_btn = ModernButton(
            nav_frame,
            text="Next →",
            command=self.next_step,
            width=10
        )
        self.next_btn.configure_primary()
        
        # Initially hide all navigation buttons (will be shown after login)
        self.back_btn.pack_forget()
        self.next_btn.pack_forget()
        self.logout_btn.pack_forget()
        
    def create_status_bar(self):
        """Create the status bar fixed at bottom."""
        self.status_frame = tk.Frame(self.root, bg=Colors.CARD_BG, relief="flat", bd=1)
        self.status_frame.pack(side="bottom", fill="x", padx=20, pady=(0, 5))
        
        self.status_label = tk.Label(
            self.status_frame,
            text="Ready to start setup...",
            font=("SF Pro Display", 9),
            fg=Colors.SECONDARY,
            bg=Colors.CARD_BG,
            anchor="w"
        )
        self.status_label.pack(fill="x", padx=10, pady=10)
        
    def show_login_screen(self):
        """Show the login screen."""
        self.current_step = 0
        self.show_step(0)
        
    def show_step(self, step):
        """Show the specified step."""
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        # Clear environment entries to prevent stale references
        self.env_entries = {}
            
        self.current_step = step
        
        # Initialize progress variable
        progress = 0
        
        # Update progress based on role
        if step == 0:
            # Login screen - no progress bar
            self.progress_bar['value'] = 0
            self.progress_label.config(text="Login Required")
            self.show_login_interface()
        elif self.is_admin:
            progress = ((step) / self.total_steps) * 100
            self.progress_label.config(text=f"Step {step} of {self.total_steps}")
        else:
            # For users, skip admin-only steps
            user_steps = [1, 2, 3, 4, 5, 6, 7, 8]  # Python check, env setup, env detection, model download, vector db, deps, completion
            if step in user_steps:
                user_step_index = user_steps.index(step)
                progress = ((user_step_index + 1) / len(user_steps)) * 100
                self.progress_label.config(text=f"Step {user_step_index + 1} of {len(user_steps)}")
            else:
                progress = 0
        self.progress_bar['value'] = progress
        
        # Show appropriate step (skip step 0 as it's handled above)
        if step == 0:
            pass  # Already handled above
        elif step == 1:
            self.show_python_check()
        elif step == 2:
            self.show_env_setup()
        elif step == 3:
            if self.is_admin:
                self.show_db_test()
            else:
                self.show_step(4)  # Skip DB test for users
        elif step == 4:
            self.show_environment_setup()
        elif step == 5:
            self.show_model_download()
        elif step == 6:
            self.show_vector_db_setup()
        elif step == 7:
            self.show_dependency_install()
        elif step == 8:
            self.show_completion()
            
        # Update navigation
        self.update_navigation()
        
    def show_login_interface(self):
        """Show the integrated login interface."""
        # Hide progress bar for login screen
        self.progress_bar.pack_forget()
        self.progress_label.pack_forget()
        
        # Create main login container
        login_frame = tk.Frame(self.content_frame, bg=Colors.BACKGROUND)
        login_frame.pack(fill="both", expand=True, padx=50, pady=50)
        
        # Icon
        icon_label = tk.Label(
            login_frame, 
            text="🚀", 
            font=("Segoe UI", 64), 
            bg=Colors.BACKGROUND
        )
        icon_label.pack(pady=(0, 30))
        
        # Title
        title_label = tk.Label(
            login_frame, 
            text="Welcome to FAQBuddy Setup", 
            font=("Segoe UI", 24, "bold"), 
            fg=Colors.PRIMARY, 
            bg=Colors.BACKGROUND
        )
        title_label.pack(pady=(0, 10))
        
        subtitle_label = tk.Label(
            login_frame, 
            text="Choose your role to continue with the setup", 
            font=("Segoe UI", 14), 
            fg=Colors.SECONDARY, 
            bg=Colors.BACKGROUND
        )
        subtitle_label.pack(pady=(0, 40))
        
        # Role selection buttons
        btn_frame = tk.Frame(login_frame, bg=Colors.BACKGROUND)
        btn_frame.pack(fill="x", pady=20)
        
        # Admin button
        admin_btn = tk.Button(
            btn_frame, 
            text="👨‍💼 Admin Setup", 
            width=25, 
            height=3, 
            bg=Colors.PRIMARY, 
            fg="white", 
            font=("SF Pro Display", 14, "bold"),
            activebackground=Colors.BUTTON_HOVER, 
            activeforeground="white", 
            relief="flat", 
            cursor="hand2",
            command=self.show_admin_login, 
            padx=30, 
            pady=15,
            borderwidth=0
        )
        admin_btn.pack(pady=(0, 20), fill="x")
        
        # User button
        user_btn = tk.Button(
            btn_frame, 
            text="👤 User Setup", 
            width=25, 
            height=3, 
            bg=Colors.SECONDARY, 
            fg="white", 
            font=("SF Pro Display", 14, "bold"),
            activebackground="#6D6D70", 
            activeforeground="white", 
            relief="flat", 
            cursor="hand2",
            command=self.select_user_role, 
            padx=30, 
            pady=15,
            borderwidth=0
        )
        user_btn.pack(fill="x")
        
        # Add hover effects
        def on_admin_enter(e):
            admin_btn.configure(bg=Colors.BUTTON_HOVER)
        
        def on_admin_leave(e):
            admin_btn.configure(bg=Colors.PRIMARY)
            
        def on_user_enter(e):
            user_btn.configure(bg="#6D6D70")
            
        def on_user_leave(e):
            user_btn.configure(bg=Colors.SECONDARY)
            
        admin_btn.bind("<Enter>", on_admin_enter)
        admin_btn.bind("<Leave>", on_admin_leave)
        user_btn.bind("<Enter>", on_user_enter)
        user_btn.bind("<Leave>", on_user_leave)
        
    def show_admin_login(self):
        """Show admin login interface."""
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        # Create admin login container
        login_frame = tk.Frame(self.content_frame, bg=Colors.BACKGROUND)
        login_frame.pack(fill="both", expand=True, padx=50, pady=50)
        
        # Icon
        icon_label = tk.Label(
            login_frame, 
            text="🔐", 
            font=("Segoe UI", 64), 
            bg=Colors.BACKGROUND
        )
        icon_label.pack(pady=(0, 30))
        
        # Title
        title_label = tk.Label(
            login_frame, 
            text="Admin Login", 
            font=("Segoe UI", 24, "bold"), 
            fg=Colors.PRIMARY, 
            bg=Colors.BACKGROUND
        )
        title_label.pack(pady=(0, 10))
        
        subtitle_label = tk.Label(
            login_frame, 
            text="Enter admin password to access full setup options", 
            font=("Segoe UI", 14), 
            fg=Colors.SECONDARY, 
            bg=Colors.BACKGROUND
        )
        subtitle_label.pack(pady=(0, 40))
        
        # Password entry frame
        entry_frame = tk.Frame(login_frame, bg=Colors.BACKGROUND)
        entry_frame.pack(fill="x", pady=(0, 20))
        
        self.admin_pw_var = tk.StringVar()
        pw_entry = tk.Entry(
            entry_frame, 
            textvariable=self.admin_pw_var, 
            show="*", 
            font=("Segoe UI", 16), 
            width=30, 
            relief="flat", 
            bd=2,
            bg=Colors.CARD_BG,
            fg=Colors.TEXT,
            insertbackground=Colors.PRIMARY
        )
        pw_entry.pack(pady=(0, 10))
        pw_entry.focus_set()
        
        # Error label
        self.admin_pw_error = tk.Label(
            login_frame, 
            text="", 
            font=("Segoe UI", 12), 
            fg=Colors.ERROR, 
            bg=Colors.BACKGROUND
        )
        self.admin_pw_error.pack(pady=(0, 30))
        
        # Buttons frame
        btn_frame = tk.Frame(login_frame, bg=Colors.BACKGROUND)
        btn_frame.pack(fill="x", pady=20)
        
        # Submit button
        submit_btn = tk.Button(
            btn_frame, 
            text="🔓 Login", 
            width=20, 
            height=2, 
            bg=Colors.PRIMARY, 
            fg="white", 
            font=("SF Pro Display", 14, "bold"),
            activebackground=Colors.BUTTON_HOVER, 
            activeforeground="white", 
            relief="flat", 
            cursor="hand2",
            command=self.check_admin_password, 
            padx=25, 
            pady=10,
            borderwidth=0
        )
        submit_btn.pack(side="left", padx=(0, 10), fill="x", expand=True)
        
        # Back button
        back_btn = tk.Button(
            btn_frame, 
            text="← Back", 
            width=20, 
            height=2, 
            bg=Colors.SECONDARY, 
            fg="white", 
            font=("SF Pro Display", 14, "bold"),
            activebackground="#6D6D70", 
            activeforeground="white", 
            relief="flat", 
            cursor="hand2",
            command=self.show_login_interface, 
            padx=25, 
            pady=10,
            borderwidth=0
        )
        back_btn.pack(side="right", fill="x", expand=True)
        
        # Add hover effects
        def on_submit_enter(e):
            submit_btn.configure(bg=Colors.BUTTON_HOVER)
        
        def on_submit_leave(e):
            submit_btn.configure(bg=Colors.PRIMARY)
            
        def on_back_enter(e):
            back_btn.configure(bg="#6D6D70")
            
        def on_back_leave(e):
            back_btn.configure(bg=Colors.SECONDARY)
            
        submit_btn.bind("<Enter>", on_submit_enter)
        submit_btn.bind("<Leave>", on_submit_leave)
        back_btn.bind("<Enter>", on_back_enter)
        back_btn.bind("<Leave>", on_back_leave)
        
        # Bind Enter key to submit
        pw_entry.bind("<Return>", lambda e: self.check_admin_password())
        
    def check_admin_password(self):
        """Check admin password and proceed."""
        pw = self.admin_pw_var.get()
        if pw == 'faqbuddy-admin-panel-funtori-yessir-1970':
            self.is_admin = True
            self.admin_pw_error.config(text="✅ Login successful! Proceeding to setup...", fg=Colors.SUCCESS)
            self.root.after(1000, lambda: self.show_step(1))  # Proceed to step 1 after 1 second
        else:
            self.admin_pw_error.config(text="❌ Incorrect password. Please try again.", fg=Colors.ERROR)
            
    def select_user_role(self):
        """Select user role and proceed."""
        self.is_admin = False
        self.show_step(1)  # Proceed to step 1
        
    def update_navigation(self):
        """Update navigation buttons."""
        if self.current_step == 0:
            # Login screen - hide navigation
            self.back_btn.pack_forget()
            self.next_btn.pack_forget()
            self.logout_btn.pack_forget()
        else:
            # Show navigation for other steps
            self.back_btn.pack(side="left", padx=(10, 0))
            self.next_btn.pack(side="right")
            self.logout_btn.pack(side="left")
            
            if self.current_step == 1:
                self.back_btn.configure(state="disabled")
            else:
                self.back_btn.configure(state="normal")
                
            if self.current_step == self.total_steps:
                self.next_btn.configure(text="Finish", state="disabled")
            else:
                self.next_btn.configure(text="Next →", state="normal")
        
    def show_python_check(self):
        """Show Python version check step."""
        self.progress_label.config(text="Step 1 of 8: Checking Python Version")
        
        # Create card
        card = tk.Frame(self.content_frame, bg=Colors.CARD_BG, relief="flat", bd=1)
        card.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Content
        content_frame = tk.Frame(card, bg=Colors.CARD_BG)
        content_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Icon and title
        icon_label = tk.Label(
            content_frame,
            text="🐍",
            font=("Segoe UI", 48),
            bg=Colors.CARD_BG
        )
        icon_label.pack(pady=(0, 20))
        
        title_label = tk.Label(
            content_frame,
            text="Python Version Check",
            font=("Segoe UI", 18, "bold"),
            fg=Colors.TEXT,
            bg=Colors.CARD_BG
        )
        title_label.pack()
        
        desc_label = tk.Label(
            content_frame,
            text="Checking if your Python version is compatible with FAQBuddy",
            font=("Segoe UI", 11),
            fg=Colors.SECONDARY,
            bg=Colors.CARD_BG,
            wraplength=500
        )
        desc_label.pack(pady=(10, 30))
        
        # Check button with improved styling
        check_btn = tk.Button(
            content_frame,
            text="🔍 Check Python Version",
            command=self.check_python_version,
            width=25,
            height=2,
            bg=Colors.PRIMARY,
            fg="white",
            font=("SF Pro Display", 12, "bold"),
            relief="flat",
            cursor="hand2",
            activebackground=Colors.BUTTON_HOVER,
            activeforeground="white",
            padx=20,
            pady=8
        )
        check_btn.pack(pady=(0, 20))
        
        # Add tooltip
        self.create_tooltip(check_btn, "Click to verify your Python version meets the requirements (3.8+)")
        
        # Result label
        self.python_result_label = tk.Label(
            content_frame,
            text="",
            font=("Segoe UI", 10),
            bg=Colors.CARD_BG,
            wraplength=500
        )
        self.python_result_label.pack(pady=(20, 0))
        
    def show_env_setup(self):
        """Show environment setup step."""
        self.progress_label.config(text="Step 2 of 8: Environment Configuration")
        
        # Create card
        card = tk.Frame(self.content_frame, bg=Colors.CARD_BG, relief="flat", bd=1)
        card.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Content
        content_frame = tk.Frame(card, bg=Colors.CARD_BG)
        content_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Title
        title_label = tk.Label(
            content_frame,
            text="🔧 Environment Configuration",
            font=("Segoe UI", 18, "bold"),
            fg=Colors.TEXT,
            bg=Colors.CARD_BG
        )
        title_label.pack(pady=(0, 20))
        
        # Check if .env exists
        env_file = Path(".env")
        env_exists = env_file.exists()
        
        if env_exists and not self.is_admin:
            # For users, if .env exists, just show a message
            desc_label = tk.Label(
                content_frame,
                text="✅ Environment file already exists and is configured.",
                font=("Segoe UI", 11),
                fg=Colors.SUCCESS,
                bg=Colors.CARD_BG,
                wraplength=500
            )
            desc_label.pack(pady=(0, 30))
            
            info_label = tk.Label(
                content_frame,
                text="As a regular user, you cannot view or modify environment variables for security reasons.",
                font=("Segoe UI", 10),
                fg=Colors.SECONDARY,
                bg=Colors.CARD_BG,
                wraplength=500
            )
            info_label.pack(pady=(0, 30))
            
            # Skip button
            skip_btn = tk.Button(
                content_frame,
                text="Continue to Next Step",
                command=lambda: self.show_step(3),  # Skip to model download
                width=20,
                bg=Colors.PRIMARY,
                fg="white",
                font=("SF Pro Display", 11, "bold"),
                relief="flat",
                cursor="hand2",
                padx=20,
                pady=8,
                activebackground=Colors.BUTTON_HOVER,
                activeforeground="white"
            )
            skip_btn.pack()
            
        else:
            # Show form for admin or if .env doesn't exist
            if self.is_admin:
                desc_label = tk.Label(
                    content_frame,
                    text="Configure your database and API credentials. You can view and edit all values.",
                    font=("Segoe UI", 11),
                    fg=Colors.SECONDARY,
                    bg=Colors.CARD_BG,
                    wraplength=500
                )
            else:
                desc_label = tk.Label(
                    content_frame,
                    text="Configure your database and API credentials securely. Values will be masked for privacy.",
                    font=("Segoe UI", 11),
                    fg=Colors.SECONDARY,
                    bg=Colors.CARD_BG,
                    wraplength=500
                )
            desc_label.pack(pady=(0, 30))
            
            # Form frame
            form_frame = tk.Frame(content_frame, bg=Colors.CARD_BG)
            form_frame.pack(fill="x")
            
            # Database section
            db_label = tk.Label(
                form_frame,
                text="Database Configuration (Neon PostgreSQL)",
                font=("Segoe UI", 12, "bold"),
                fg=Colors.TEXT,
                bg=Colors.CARD_BG
            )
            db_label.pack(anchor="w", pady=(0, 10))
            
            # Database fields
            fields = [
                ("DB_NEON_NAME", "Database Name", "The name of your Neon PostgreSQL database"),
                ("DB_NEON_USER", "Username", "Your Neon database username"),
                ("DB_NEON_PASSWORD", "Password", "Your Neon database password"),
                ("DB_NEON_HOST", "Host", "Your Neon database host address"),
                ("DB_NEON_PORT", "Port", "Your Neon database port (usually 5432)")
            ]
            
            self.env_entries = {}
            
            for var_name, label_text, tooltip_text in fields:
                field_frame = tk.Frame(form_frame, bg=Colors.CARD_BG)
                field_frame.pack(fill="x", pady=5)
                
                # Label with tooltip
                label_frame = tk.Frame(field_frame, bg=Colors.CARD_BG)
                label_frame.pack(fill="x")
                
                label = ModernLabel(label_frame, text=f"{label_text}:")
                label.pack(side="left")
                
                # Tooltip icon
                tooltip_btn = tk.Label(
                    label_frame,
                    text="ℹ️",
                    font=("Segoe UI", 8),
                    fg=Colors.SECONDARY,
                    bg=Colors.CARD_BG,
                    cursor="hand2"
                )
                tooltip_btn.pack(side="right")
                tooltip_btn.bind("<Button-1>", lambda e, text=tooltip_text: self.show_tooltip(e, text))
                
                # Entry field
                if var_name == "DB_NEON_PASSWORD" or (not self.is_admin and var_name == "PINECONE_API_KEY"):
                    entry = ModernEntry(field_frame, width=50, show="*")
                else:
                    entry = ModernEntry(field_frame, width=50)
                entry.pack(fill="x", pady=(5, 0))
                
                # Show current value for admin
                if self.is_admin:
                    entry.insert(0, self.env_vars.get(var_name, ""))
                
                self.env_entries[var_name] = entry
                
                # Show/hide toggle for password fields (admin only)
                if var_name == "DB_NEON_PASSWORD" and self.is_admin:
                    show_btn = tk.Button(
                        field_frame,
                        text="👁 Show",
                        command=lambda e=entry, b=None: self.toggle_password_visibility(e, b),
                        width=8,
                        bg=Colors.SECONDARY,
                        fg="white",
                        font=("SF Pro Display", 8, "bold"),
                        relief="flat",
                        cursor="hand2",
                        padx=10,
                        pady=4,
                        activebackground="#6D6D70",
                        activeforeground="white"
                    )
                    show_btn.pack(anchor="w", pady=(5, 0))
                    # Update the command to include the button reference
                    show_btn.configure(command=lambda e=entry, b=show_btn: self.toggle_password_visibility(e, b))
            
            # Pinecone section
            pinecone_label = tk.Label(
                form_frame,
                text="Vector Database (Pinecone)",
                font=("Segoe UI", 12, "bold"),
                fg=Colors.TEXT,
                bg=Colors.CARD_BG
            )
            pinecone_label.pack(anchor="w", pady=(20, 10))
            
            pinecone_frame = tk.Frame(form_frame, bg=Colors.CARD_BG)
            pinecone_frame.pack(fill="x", pady=5)
            
            # Label with tooltip
            label_frame = tk.Frame(pinecone_frame, bg=Colors.CARD_BG)
            label_frame.pack(fill="x")
            
            pinecone_desc = ModernLabel(label_frame, text="Pinecone API Key:")
            pinecone_desc.pack(side="left")
            
            tooltip_btn = tk.Label(
                label_frame,
                text="ℹ️",
                font=("Segoe UI", 8),
                fg=Colors.SECONDARY,
                bg=Colors.CARD_BG,
                cursor="hand2"
            )
            tooltip_btn.pack(side="right")
            tooltip_btn.bind("<Button-1>", lambda e: self.show_tooltip(e, "Your Pinecone API key for vector database access"))
            
            # Entry field (always masked for security)
            pinecone_entry = ModernEntry(pinecone_frame, width=50, show="*")
            pinecone_entry.pack(fill="x", pady=(5, 0))
            
            if self.is_admin:
                pinecone_entry.insert(0, self.env_vars.get("PINECONE_API_KEY", ""))
            
            self.env_entries["PINECONE_API_KEY"] = pinecone_entry
            
            # Show/hide button (admin only)
            if self.is_admin:
                show_btn = tk.Button(
                    pinecone_frame,
                    text="👁 Show",
                    command=lambda e=pinecone_entry, b=None: self.toggle_password_visibility(e, b),
                    width=8,
                    bg=Colors.SECONDARY,
                    fg="white",
                    font=("SF Pro Display", 8, "bold"),
                    relief="flat",
                    cursor="hand2",
                    padx=10,
                    pady=4,
                    activebackground="#6D6D70",
                    activeforeground="white"
                )
                show_btn.pack(anchor="w", pady=(5, 0))
                show_btn.configure(command=lambda e=pinecone_entry, b=show_btn: self.toggle_password_visibility(e, b))
            
            # Save button
            save_btn = tk.Button(
                content_frame,
                text="Save Environment Configuration",
                command=self.save_env_vars,
                width=25,
                bg=Colors.SUCCESS,
                fg="white",
                font=("SF Pro Display", 11, "bold"),
                relief="flat",
                cursor="hand2",
                padx=20,
                pady=8,
                activebackground="#2FB344",
                activeforeground="white"
            )
            save_btn.pack(pady=(20, 0))
            
    def show_environment_setup(self):
        """Show Python environment setup step."""
        self.progress_label.config(text="Step 4 of 8: Python Environment Setup")
        
        # Create card
        card = tk.Frame(self.content_frame, bg=Colors.CARD_BG, relief="flat", bd=1)
        card.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Content
        content_frame = tk.Frame(card, bg=Colors.CARD_BG)
        content_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Icon and title
        icon_label = tk.Label(
            content_frame,
            text="🐍",
            font=("Segoe UI", 48),
            bg=Colors.CARD_BG
        )
        icon_label.pack(pady=(0, 20))
        
        title_label = tk.Label(
            content_frame,
            text="Python Environment Setup",
            font=("Segoe UI", 18, "bold"),
            fg=Colors.TEXT,
            bg=Colors.CARD_BG
        )
        title_label.pack()
        
        desc_label = tk.Label(
            content_frame,
            text="Detecting and setting up Python environment for FAQBuddy",
            font=("Segoe UI", 11),
            fg=Colors.SECONDARY,
            bg=Colors.CARD_BG,
            wraplength=500
        )
        desc_label.pack(pady=(10, 30))
        
        # Environment detection frame
        env_frame = tk.Frame(content_frame, bg=Colors.CARD_BG)
        env_frame.pack(fill="x", pady=(0, 20))
        
        # Detect current environment
        has_env = self.detect_python_environment()
        
        # Environment status
        status_frame = tk.Frame(env_frame, bg=Colors.CARD_BG)
        status_frame.pack(fill="x", pady=(0, 20))
        
        if has_env:
            status_icon = "✅"
            status_text = f"Active {self.env_type.upper()} environment detected"
            status_color = Colors.SUCCESS
            self.python_env = True
        else:
            status_icon = "⚠️"
            status_text = "No virtual environment detected - using system Python"
            status_color = Colors.WARNING
            self.python_env = False
        
        status_label = tk.Label(
            status_frame,
            text=f"{status_icon} {status_text}",
            font=("Segoe UI", 12, "bold"),
            fg=status_color,
            bg=Colors.CARD_BG
        )
        status_label.pack(anchor="w")
        
        # Environment path
        path_label = tk.Label(
            status_frame,
            text=f"Path: {self.env_path}",
            font=("Segoe UI", 10),
            fg=Colors.SECONDARY,
            bg=Colors.CARD_BG,
            anchor="w"
        )
        path_label.pack(anchor="w", pady=(5, 0))
        
        # Create environment section (only show if no environment detected)
        if not has_env:
            create_frame = tk.Frame(content_frame, bg=Colors.CARD_BG)
            create_frame.pack(fill="x", pady=(20, 0))
            
            create_title = tk.Label(
                create_frame,
                text="🔧 Create Virtual Environment",
                font=("Segoe UI", 14, "bold"),
                fg=Colors.TEXT,
                bg=Colors.CARD_BG,
                anchor="w"
            )
            create_title.pack(anchor="w", pady=(0, 15))
            
            create_desc = tk.Label(
                create_frame,
                text="It's recommended to create a virtual environment to avoid conflicts with system packages.",
                font=("Segoe UI", 10),
                fg=Colors.SECONDARY,
                bg=Colors.CARD_BG,
                wraplength=500,
                anchor="w"
            )
            create_desc.pack(anchor="w", pady=(0, 20))
            
            # Environment type selection
            env_type_frame = tk.Frame(create_frame, bg=Colors.CARD_BG)
            env_type_frame.pack(fill="x", pady=(0, 20))
            
            self.env_choice = tk.StringVar(value="venv")
            
            venv_radio = tk.Radiobutton(
                env_type_frame,
                text="Python venv (Recommended)",
                variable=self.env_choice,
                value="venv",
                font=("Segoe UI", 10),
                fg=Colors.TEXT,
                bg=Colors.CARD_BG,
                selectcolor=Colors.CARD_BG,
                activebackground=Colors.CARD_BG,
                activeforeground=Colors.TEXT
            )
            venv_radio.pack(anchor="w", pady=2)
            
            # Check if conda is available
            conda_available = subprocess.run(["conda", "--version"], capture_output=True, text=True).returncode == 0
            
            if conda_available:
                conda_radio = tk.Radiobutton(
                    env_type_frame,
                    text="Conda environment",
                    variable=self.env_choice,
                    value="conda",
                    font=("Segoe UI", 10),
                    fg=Colors.TEXT,
                    bg=Colors.CARD_BG,
                    selectcolor=Colors.CARD_BG,
                    activebackground=Colors.CARD_BG,
                    activeforeground=Colors.TEXT
                )
                conda_radio.pack(anchor="w", pady=2)
            
            # Environment name entry
            name_frame = tk.Frame(create_frame, bg=Colors.CARD_BG)
            name_frame.pack(fill="x", pady=(0, 20))
            
            name_label = tk.Label(
                name_frame,
                text="Environment Name:",
                font=("Segoe UI", 10, "bold"),
                fg=Colors.TEXT,
                bg=Colors.CARD_BG,
                anchor="w"
            )
            name_label.pack(anchor="w", pady=(0, 5))
            
            self.env_name_entry = ModernEntry(
                name_frame,
                width=30
            )
            self.env_name_entry.insert(0, "faqbuddy_env")
            self.env_name_entry.pack(anchor="w")
            
            # Create environment button
            create_btn = tk.Button(
                create_frame,
                text="🔧 Create Environment",
                command=self.create_environment,
                width=25,
                height=2,
                bg=Colors.PRIMARY,
                fg="white",
                font=("SF Pro Display", 12, "bold"),
                relief="flat",
                cursor="hand2",
                activebackground=Colors.BUTTON_HOVER,
                activeforeground="white",
                padx=20,
                pady=8
            )
            create_btn.pack(pady=(0, 20))
            
            # Progress frame
            self.env_progress_frame = tk.Frame(create_frame, bg=Colors.CARD_BG)
            self.env_progress_frame.pack(fill="x", pady=(20, 0))
            
            self.env_progress_bar = ttk.Progressbar(
                self.env_progress_frame,
                mode='indeterminate',
                style='Modern.Horizontal.TProgressbar'
            )
            self.env_progress_bar.pack(fill="x")
            
            # Result label
            self.env_result_label = tk.Label(
                create_frame,
                text="",
                font=("Segoe UI", 10),
                bg=Colors.CARD_BG,
                wraplength=500
            )
            self.env_result_label.pack(pady=(20, 0))
        
        # Skip button (if environment exists or user wants to skip)
        skip_btn = tk.Button(
            content_frame,
            text="⏭️ Continue with Current Environment",
            command=self.next_step,
            width=25,
            height=2,
            bg=Colors.SECONDARY,
            fg="white",
            font=("SF Pro Display", 12, "bold"),
            relief="flat",
            cursor="hand2",
            activebackground="#6D6D70",
            activeforeground="white",
            padx=20,
            pady=8
        )
        skip_btn.pack(pady=(20, 0))
        
    def create_environment(self):
        """Create a new virtual environment."""
        def create():
            try:
                self.env_progress_bar.start()
                self.update_status("Creating virtual environment...")
                
                env_name = self.env_name_entry.get().strip()
                if not env_name:
                    self.env_result_label.config(
                        text="❌ Please enter an environment name",
                        fg=Colors.ERROR
                    )
                    self.env_progress_bar.stop()
                    return
                
                env_choice = self.env_choice.get()
                
                if env_choice == "venv":
                    # Create Python venv
                    result = subprocess.run([
                        sys.executable, "-m", "venv", env_name
                    ], capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        self.env_type = 'venv'
                        self.env_path = os.path.abspath(env_name)
                        self.python_env = True
                        
                        self.env_result_label.config(
                            text=f"✅ Virtual environment '{env_name}' created successfully!",
                            fg=Colors.SUCCESS
                        )
                        self.update_status("Virtual environment created successfully")
                        
                        # Update the status display
                        for widget in self.content_frame.winfo_children():
                            if isinstance(widget, tk.Frame):
                                for child in widget.winfo_children():
                                    if isinstance(child, tk.Frame):
                                        for grandchild in child.winfo_children():
                                            if isinstance(grandchild, tk.Label) and "Active" in grandchild.cget("text"):
                                                grandchild.config(
                                                    text=f"✅ Active VENV environment created",
                                                    fg=Colors.SUCCESS
                                                )
                                            elif isinstance(grandchild, tk.Label) and "Path:" in grandchild.cget("text"):
                                                grandchild.config(text=f"Path: {self.env_path}")
                        
                    else:
                        self.env_result_label.config(
                            text=f"❌ Failed to create virtual environment: {result.stderr}",
                            fg=Colors.ERROR
                        )
                        self.update_status("Virtual environment creation failed")
                        
                elif env_choice == "conda":
                    # Check if conda is available
                    conda_check = subprocess.run(["conda", "--version"], capture_output=True, text=True)
                    if conda_check.returncode != 0:
                        self.env_result_label.config(
                            text="❌ Conda is not available. Please install conda or choose venv.",
                            fg=Colors.ERROR
                        )
                        self.env_progress_bar.stop()
                        self.update_status("Conda not available")
                        return
                    
                    # Create conda environment
                    result = subprocess.run([
                        "conda", "create", "-n", env_name, "python=3.11", "-y"
                    ], capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        self.env_type = 'conda'
                        self.env_path = env_name  # Conda env name
                        self.python_env = True
                        
                        self.env_result_label.config(
                            text=f"✅ Conda environment '{env_name}' created successfully!",
                            fg=Colors.SUCCESS
                        )
                        self.update_status("Conda environment created successfully")
                        
                    else:
                        self.env_result_label.config(
                            text=f"❌ Failed to create conda environment: {result.stderr}",
                            fg=Colors.ERROR
                        )
                        self.update_status("Conda environment creation failed")
                
                self.env_progress_bar.stop()
                
            except Exception as e:
                self.env_progress_bar.stop()
                self.env_result_label.config(
                    text=f"❌ Error creating environment: {e}",
                    fg=Colors.ERROR
                )
                self.update_status("Environment creation failed")
                
        threading.Thread(target=create, daemon=True).start()
        
    def show_model_download(self):
        """Show model download step."""
        self.progress_label.config(text="Step 5 of 8: Downloading AI Models")
        
        # Create card
        card = tk.Frame(self.content_frame, bg=Colors.CARD_BG, relief="flat", bd=1)
        card.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Content
        content_frame = tk.Frame(card, bg=Colors.CARD_BG)
        content_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Icon and title
        icon_label = tk.Label(
            content_frame,
            text="🤖",
            font=("Segoe UI", 48),
            bg=Colors.CARD_BG
        )
        icon_label.pack(pady=(0, 20))
        
        title_label = tk.Label(
            content_frame,
            text="AI Model Download",
            font=("Segoe UI", 18, "bold"),
            fg=Colors.TEXT,
            bg=Colors.CARD_BG
        )
        title_label.pack()
        
        desc_label = tk.Label(
            content_frame,
            text="Downloading required AI models for FAQBuddy",
            font=("Segoe UI", 11),
            fg=Colors.SECONDARY,
            bg=Colors.CARD_BG,
            wraplength=500
        )
        desc_label.pack(pady=(10, 30))
        
        # Model info with better styling
        model_info = tk.Frame(content_frame, bg=Colors.CARD_BG)
        model_info.pack(fill="x", pady=(0, 20))
        
        model_label = tk.Label(
            model_info,
            text="📦 Models to download:",
            font=("Segoe UI", 12, "bold"),
            fg=Colors.TEXT,
            bg=Colors.CARD_BG,
            anchor="w"
        )
        model_label.pack(anchor="w", pady=(0, 10))
        
        models_list = [
            "• Mistral 7B Instruct (4.1GB) - Main language model",
            "• Gemma 3 4B Italian (1.5GB) - Italian language model"
        ]
        
        for model in models_list:
            model_item = tk.Label(
                model_info,
                text=model,
                font=("Segoe UI", 10),
                fg=Colors.TEXT,
                bg=Colors.CARD_BG,
                anchor="w"
            )
            model_item.pack(anchor="w", pady=2)
        
        # Download button with improved styling
        download_btn = tk.Button(
            content_frame,
            text="⬇️ Download Models",
            command=self.download_models,
            width=25,
            height=2,
            bg=Colors.PRIMARY,
            fg="white",
            font=("SF Pro Display", 12, "bold"),
            relief="flat",
            cursor="hand2",
            activebackground=Colors.BUTTON_HOVER,
            activeforeground="white",
            padx=20,
            pady=8
        )
        download_btn.pack(pady=(0, 20))
        
        # Add tooltip
        self.create_tooltip(download_btn, "Download AI models (this may take several minutes)")
        
        # Progress frame
        self.download_progress_frame = tk.Frame(content_frame, bg=Colors.CARD_BG)
        self.download_progress_frame.pack(fill="x", pady=(20, 0))
        
        self.download_progress_bar = ttk.Progressbar(
            self.download_progress_frame,
            mode='indeterminate',
            style='Modern.Horizontal.TProgressbar'
        )
        self.download_progress_bar.pack(fill="x")
        
        # Result label
        self.download_result_label = tk.Label(
            content_frame,
            text="",
            font=("Segoe UI", 10),
            bg=Colors.CARD_BG,
            wraplength=500
        )
        self.download_result_label.pack(pady=(20, 0))
        
    def show_vector_db_setup(self):
        """Show vector database setup step."""
        self.progress_label.config(text="Step 6 of 8: Setting up Vector Database")
        
        # Create card
        card = tk.Frame(self.content_frame, bg=Colors.CARD_BG, relief="flat", bd=1)
        card.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Content
        content_frame = tk.Frame(card, bg=Colors.CARD_BG)
        content_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Icon and title
        icon_label = tk.Label(
            content_frame,
            text="🔍",
            font=("Segoe UI", 48),
            bg=Colors.CARD_BG
        )
        icon_label.pack(pady=(0, 20))
        
        title_label = tk.Label(
            content_frame,
            text="Vector Database Setup",
            font=("Segoe UI", 18, "bold"),
            fg=Colors.TEXT,
            bg=Colors.CARD_BG
        )
        title_label.pack()
        
        desc_label = tk.Label(
            content_frame,
            text="Setting up Pinecone vector database for semantic search",
            font=("Segoe UI", 11),
            fg=Colors.SECONDARY,
            bg=Colors.CARD_BG,
            wraplength=500
        )
        desc_label.pack(pady=(10, 30))
        
        # Options with better styling
        options_frame = tk.Frame(content_frame, bg=Colors.CARD_BG)
        options_frame.pack(fill="x", pady=(0, 20))
        
        self.update_vec_db_var = tk.BooleanVar(value=True)
        
        update_radio = tk.Radiobutton(
            options_frame,
            text="✅ Update vector database (recommended)",
            variable=self.update_vec_db_var,
            value=True,
            font=("Segoe UI", 11),
            fg=Colors.TEXT,
            bg=Colors.CARD_BG,
            selectcolor=Colors.CARD_BG,
            activebackground=Colors.CARD_BG
        )
        update_radio.pack(anchor="w", pady=5)
        
        skip_radio = tk.Radiobutton(
            options_frame,
            text="⏭️ Skip for now (can be done later)",
            variable=self.update_vec_db_var,
            value=False,
            font=("Segoe UI", 11),
            fg=Colors.TEXT,
            bg=Colors.CARD_BG,
            selectcolor=Colors.CARD_BG,
            activebackground=Colors.CARD_BG
        )
        skip_radio.pack(anchor="w", pady=5)
        
        # Setup button with improved styling
        setup_btn = tk.Button(
            content_frame,
            text="⚙️ Setup Vector Database",
            command=self.setup_vector_database,
            width=25,
            height=2,
            bg=Colors.PRIMARY,
            fg="white",
            font=("SF Pro Display", 12, "bold"),
            relief="flat",
            cursor="hand2",
            activebackground=Colors.BUTTON_HOVER,
            activeforeground="white",
            padx=20,
            pady=8
        )
        setup_btn.pack(pady=(0, 20))
        
        # Add tooltip
        self.create_tooltip(setup_btn, "Configure Pinecone vector database for semantic search")
        
        # Result label
        self.vector_result_label = tk.Label(
            content_frame,
            text="",
            font=("Segoe UI", 10),
            bg=Colors.CARD_BG,
            wraplength=500
        )
        self.vector_result_label.pack(pady=(20, 0))
        
    def show_dependency_install(self):
        """Show dependency installation step."""
        self.progress_label.config(text="Step 7 of 8: Installing Dependencies")
        
        # Create card
        card = tk.Frame(self.content_frame, bg=Colors.CARD_BG, relief="flat", bd=1)
        card.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Content
        content_frame = tk.Frame(card, bg=Colors.CARD_BG)
        content_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Icon and title
        icon_label = tk.Label(
            content_frame,
            text="📦",
            font=("Segoe UI", 48),
            bg=Colors.CARD_BG
        )
        icon_label.pack(pady=(0, 20))
        
        title_label = tk.Label(
            content_frame,
            text="Installing Dependencies",
            font=("Segoe UI", 18, "bold"),
            fg=Colors.TEXT,
            bg=Colors.CARD_BG
        )
        title_label.pack()
        
        desc_label = tk.Label(
            content_frame,
            text="Installing Python and Node.js dependencies",
            font=("Segoe UI", 11),
            fg=Colors.SECONDARY,
            bg=Colors.CARD_BG,
            wraplength=500
        )
        desc_label.pack(pady=(10, 30))
        
        # Dependencies info
        deps_info = tk.Frame(content_frame, bg=Colors.CARD_BG)
        deps_info.pack(fill="x", pady=(0, 20))
        
        deps_label = tk.Label(
            deps_info,
            text="📋 Dependencies to install:",
            font=("Segoe UI", 12, "bold"),
            fg=Colors.TEXT,
            bg=Colors.CARD_BG,
            anchor="w"
        )
        deps_label.pack(anchor="w", pady=(0, 10))
        
        deps_list = [
            "• Python packages (FastAPI, Pinecone, etc.)",
            "• Node.js packages (Next.js, React, etc.)"
        ]
        
        for dep in deps_list:
            dep_item = tk.Label(
                deps_info,
                text=dep,
                font=("Segoe UI", 10),
                fg=Colors.TEXT,
                bg=Colors.CARD_BG,
                anchor="w"
            )
            dep_item.pack(anchor="w", pady=2)
        
        # Environment info
        env_info_frame = tk.Frame(content_frame, bg=Colors.CARD_BG)
        env_info_frame.pack(fill="x", pady=(20, 0))
        
        env_info_label = tk.Label(
            env_info_frame,
            text="🐍 Python Environment:",
            font=("Segoe UI", 12, "bold"),
            fg=Colors.TEXT,
            bg=Colors.CARD_BG,
            anchor="w"
        )
        env_info_label.pack(anchor="w", pady=(0, 10))
        
        if self.python_env:
            if self.env_type == 'venv':
                env_name = os.path.basename(self.env_path)
                env_text = f"✅ Virtual Environment: {env_name}"
                env_color = Colors.SUCCESS
            elif self.env_type == 'conda':
                env_text = f"✅ Conda Environment: {self.env_path}"
                env_color = Colors.SUCCESS
            else:
                env_text = "⚠️ System Python (not recommended)"
                env_color = Colors.WARNING
        else:
            env_text = "⚠️ System Python (not recommended)"
            env_color = Colors.WARNING
        
        env_status_label = tk.Label(
            env_info_frame,
            text=env_text,
            font=("Segoe UI", 10),
            fg=env_color,
            bg=Colors.CARD_BG,
            anchor="w"
        )
        env_status_label.pack(anchor="w", pady=2)
        
        python_path_label = tk.Label(
            env_info_frame,
            text=f"Path: {self.get_python_executable()}",
            font=("Segoe UI", 9),
            fg=Colors.SECONDARY,
            bg=Colors.CARD_BG,
            anchor="w"
        )
        python_path_label.pack(anchor="w", pady=(5, 0))
        
        # Install button with improved styling
        install_btn = tk.Button(
            content_frame,
            text="🔧 Install Dependencies",
            command=self.install_dependencies,
            width=25,
            height=2,
            bg=Colors.PRIMARY,
            fg="white",
            font=("SF Pro Display", 12, "bold"),
            relief="flat",
            cursor="hand2",
            activebackground=Colors.BUTTON_HOVER,
            activeforeground="white",
            padx=20,
            pady=8
        )
        install_btn.pack(pady=(0, 20))
        
        # Add tooltip
        self.create_tooltip(install_btn, "Install all required Python and Node.js packages")
        
        # Progress frame
        self.install_progress_frame = tk.Frame(content_frame, bg=Colors.CARD_BG)
        self.install_progress_frame.pack(fill="x", pady=(20, 0))
        
        self.install_progress_bar = ttk.Progressbar(
            self.install_progress_frame,
            mode='indeterminate',
            style='Modern.Horizontal.TProgressbar'
        )
        self.install_progress_bar.pack(fill="x")
        
        # Result label
        self.install_result_label = tk.Label(
            content_frame,
            text="",
            font=("Segoe UI", 10),
            bg=Colors.CARD_BG,
            wraplength=500
        )
        self.install_result_label.pack(pady=(20, 0))
        
    def show_completion(self):
        """Show completion step."""
        self.progress_label.config(text="Setup Complete! 🎉")
        
        # Create card
        card = tk.Frame(self.content_frame, bg=Colors.CARD_BG, relief="flat", bd=1)
        card.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Content
        content_frame = tk.Frame(card, bg=Colors.CARD_BG)
        content_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Icon and title
        icon_label = tk.Label(
            content_frame,
            text="🎉",
            font=("Segoe UI", 48),
            bg=Colors.CARD_BG
        )
        icon_label.pack(pady=(0, 20))
        
        title_label = tk.Label(
            content_frame,
            text="Setup Complete!",
            font=("Segoe UI", 24, "bold"),
            fg=Colors.SUCCESS,
            bg=Colors.CARD_BG
        )
        title_label.pack()
        
        # Role-based completion message
        if self.is_admin:
            role_msg = "You have successfully configured FAQBuddy with admin privileges!"
        else:
            role_msg = "You have successfully configured FAQBuddy as a regular user!"
            
        desc_label = tk.Label(
            content_frame,
            text=role_msg,
            font=("Segoe UI", 12),
            fg=Colors.SECONDARY,
            bg=Colors.CARD_BG,
            wraplength=500
        )
        desc_label.pack(pady=(10, 30))
        
        # Instructions with better styling
        instructions_frame = tk.Frame(content_frame, bg=Colors.CARD_BG)
        instructions_frame.pack(fill="x", pady=(0, 30))
        
        instructions_title = tk.Label(
            instructions_frame,
            text="🚀 To launch FAQBuddy:",
            font=("Segoe UI", 14, "bold"),
            fg=Colors.TEXT,
            bg=Colors.CARD_BG
        )
        instructions_title.pack(anchor="w", pady=(0, 15))
        
        instructions = [
            "1. Run: python launch_servers.py",
            "2. Or start servers separately:",
            "   • Backend: cd backend && python -m uvicorn src.api.API:app --reload",
            "   • Frontend: cd frontend && npm run dev",
            "3. Access: http://localhost:3000"
        ]
        
        # Add environment-specific instructions
        if self.python_env and self.env_type == 'venv':
            env_name = os.path.basename(self.env_path)
            instructions = [
                f"1. Activate environment: source {env_name}/bin/activate (Linux/Mac) or {env_name}\\Scripts\\activate (Windows)",
                "2. Run: python launch_servers.py",
                "3. Or start servers separately:",
                "   • Backend: cd backend && python -m uvicorn src.api.API:app --reload",
                "   • Frontend: cd frontend && npm run dev",
                "4. Access: http://localhost:3000"
            ]
        elif self.python_env and self.env_type == 'conda':
            env_name = self.env_path
            instructions = [
                f"1. Activate environment: conda activate {env_name}",
                "2. Run: python launch_servers.py",
                "3. Or start servers separately:",
                "   • Backend: cd backend && python -m uvicorn src.api.API:app --reload",
                "   • Frontend: cd frontend && npm run dev",
                "4. Access: http://localhost:3000"
            ]
        else:
            instructions = [
                "1. Run: python launch_servers.py",
                "2. Or start servers separately:",
                "   • Backend: cd backend && python -m uvicorn src.api.API:app --reload",
                "   • Frontend: cd frontend && npm run dev",
                "3. Access: http://localhost:3000"
            ]
        
        # Add database setup instructions
        instructions.append("")
        instructions.append("📋 Note: RAG functionality uses a Neon database for structured queries.")
        instructions.append("   Ensure your .env file has the correct Neon database credentials.")
        
        for instruction in instructions:
            instruction_label = tk.Label(
                instructions_frame,
                text=instruction,
                font=("Segoe UI", 10),
                fg=Colors.TEXT,
                bg=Colors.CARD_BG,
                anchor="w"
            )
            instruction_label.pack(anchor="w", pady=2)
        
        # Button frame
        button_frame = tk.Frame(content_frame, bg=Colors.CARD_BG)
        button_frame.pack(pady=(20, 0))
        
        # Launch button with improved styling
        launch_btn = tk.Button(
            button_frame,
            text="🚀 Launch FAQBuddy",
            command=self.launch_faqbuddy,
            width=20,
            height=2,
            bg=Colors.SUCCESS,
            fg="white",
            font=("SF Pro Display", 12, "bold"),
            relief="flat",
            cursor="hand2",
            activebackground="#2FB344",
            activeforeground="white",
            padx=20,
            pady=8
        )
        launch_btn.pack(side="left", padx=(0, 10))
        
        # Add tooltip
        self.create_tooltip(launch_btn, "Launch both backend and frontend servers")
        
        # Finish button
        finish_btn = tk.Button(
            button_frame,
            text="✅ Finish Setup",
            command=self.root.destroy,
            width=15,
            height=2,
            bg=Colors.SECONDARY,
            fg="white",
            font=("SF Pro Display", 12, "bold"),
            relief="flat",
            cursor="hand2",
            activebackground="#6D6D70",
            activeforeground="white",
            padx=20,
            pady=8
        )
        finish_btn.pack(side="left")
        
        # Add tooltip
        self.create_tooltip(finish_btn, "Close the setup wizard")
        
    def create_tooltip(self, widget, text):
        """Create a tooltip for a widget."""
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = tk.Label(tooltip, text=text, justify="left", background="#ffffe0", relief="solid", borderwidth=1, font=("Segoe UI", 9))
            label.pack()
            
            def hide_tooltip():
                tooltip.destroy()
            
            tooltip.bind("<Leave>", lambda e: hide_tooltip())
            tooltip.bind("<Button-1>", lambda e: hide_tooltip())
            tooltip.after(3000, hide_tooltip)
            
            widget.tooltip = tooltip
            
        def hide_tooltip(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                delattr(widget, 'tooltip')
        
        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)
        
    def save_env_vars(self, show_message=True):
        """Save environment variables to .env file."""
        try:
            env_content = {}
            
            # If user is not admin and no entry widgets exist, preserve existing env vars
            if not self.is_admin and not self.env_entries:
                # Load existing .env file and preserve all variables
                env_file = Path(".env")
                if env_file.exists():
                    load_dotenv()
                    env_content = {
                        "DB_NEON_NAME": os.getenv("DB_NEON_NAME", "neondb"),
                        "DB_NEON_USER": os.getenv("DB_NEON_USER", "neondb_owner"),
                        "DB_NEON_PASSWORD": os.getenv("DB_NEON_PASSWORD", "npg_81IXpKWZQxEa"),
                        "DB_NEON_HOST": os.getenv("DB_NEON_HOST", "ep-super-credit-a9zsuu7x-pooler.gwc.azure.neon.tech"),
                        "DB_NEON_PORT": os.getenv("DB_NEON_PORT", "5432"),
                        "PINECONE_API_KEY": os.getenv("PINECONE_API_KEY", "pcsk_6FLreq_PQ9dENviDRu7WwTHg5BF27PWBmFoVMPqJNzrJcNQSWywSns973idr5vqgTixqF2"),
                        "EMAIL_FROM": os.getenv("EMAIL_FROM", "tutordimatematica.ing@gmail.com"),
                        "EMAIL_PASS": os.getenv("EMAIL_PASS", "ohxrysinakqpryrb"),
                        "EMAIL_USER": os.getenv("EMAIL_USER", "tutordimatematica.ing@gmail.com")
                    }
                else:
                    # If no .env file exists, use the loaded env_vars
                    env_content = self.env_vars.copy()
            else:
                # Admin mode or entry widgets exist - get values from entries
                for var_name, entry in self.env_entries.items():
                    try:
                        # Check if the widget still exists and is valid
                        if entry and entry.winfo_exists():
                            env_content[var_name] = entry.get()
                        else:
                            # If widget doesn't exist, use existing value or default
                            env_content[var_name] = self.env_vars.get(var_name, "")
                    except tk.TclError:
                        # Widget was destroyed, use existing value or default
                        env_content[var_name] = self.env_vars.get(var_name, "")
                
                # Add all other environment variables that weren't in the form
                all_vars = {
                    "DB_NEON_NAME": "neondb",
                    "DB_NEON_USER": "neondb_owner", 
                    "DB_NEON_PASSWORD": "npg_81IXpKWZQxEa",
                    "DB_NEON_HOST": "ep-super-credit-a9zsuu7x-pooler.gwc.azure.neon.tech",
                    "DB_NEON_PORT": "5432",
                    "PINECONE_API_KEY": "pcsk_6FLreq_PQ9dENviDRu7WwTHg5BF27PWBmFoVMPqJNzrJcNQSWywSns973idr5vqgTixqF2",
                    "EMAIL_FROM": "tutordimatematica.ing@gmail.com",
                    "EMAIL_PASS": "ohxrysinakqpryrb",
                    "EMAIL_USER": "tutordimatematica.ing@gmail.com"
                }
                
                # Update with any values from the form, otherwise use defaults
                for var_name, default_value in all_vars.items():
                    if var_name not in env_content:
                        env_content[var_name] = default_value
            
            # Write .env file
            with open(".env", 'w') as f:
                for key, value in env_content.items():
                    f.write(f"{key}={value}\n")
            
            # Update the stored env_vars
            self.env_vars.update(env_content)
            
            # Show success message only if requested and for admin or when actually saving
            if show_message and (self.is_admin or self.env_entries):
                messagebox.showinfo("Success", "Environment variables saved successfully!")
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save environment variables: {e}")
            
    def launch_faqbuddy(self):
        """Launch FAQBuddy."""
        try:
            # Get the correct Python executable
            python_executable = self.get_python_executable()
            
            subprocess.Popen([python_executable, "launch_servers.py"])
            messagebox.showinfo("FAQBuddy", "FAQBuddy is starting up!\n\nBackend: http://localhost:8000\nFrontend: http://localhost:3000")
        except Exception as e:
            messagebox.showerror("Launch Error", f"Failed to launch FAQBuddy: {e}")
            
    def update_status(self, message):
        """Update status bar message."""
        self.status_label.config(text=message)
        
    def monitor_progress(self):
        """Monitor progress queue."""
        try:
            while True:
                message = self.progress_queue.get_nowait()
                self.update_status(message)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.monitor_progress)
            
    def previous_step(self):
        """Go to previous step."""
        if self.current_step > 0:
            self.show_step(self.current_step - 1)
            
    def next_step(self):
        """Go to next step."""
        if self.current_step < self.total_steps:
            # Save environment variables if on env setup step and admin or entries exist
            if self.current_step == 1 and (self.is_admin or self.env_entries):
                self.save_env_vars(show_message=False)
            self.show_step(self.current_step + 1)
            
    def run(self):
        """Run the setup wizard."""
        self.root.mainloop()

    def check_python_version(self):
        """Check Python version compatibility."""
        def check():
            try:
                version = sys.version_info
                if version.major < 3 or (version.major == 3 and version.minor < 8):
                    self.python_result_label.config(
                        text=f"❌ Python {version.major}.{version.minor} is not compatible. Python 3.8+ required.",
                        fg=Colors.ERROR
                    )
                    self.update_status("Python version check failed")
                else:
                    self.python_result_label.config(
                        text=f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible!",
                        fg=Colors.SUCCESS
                    )
                    self.update_status("Python version check passed")
            except Exception as e:
                self.python_result_label.config(
                    text=f"❌ Error checking Python version: {e}",
                    fg=Colors.ERROR
                )
                self.update_status("Python version check failed")
                
        threading.Thread(target=check, daemon=True).start()
        
    def test_database_connection(self):
        """Test database connection."""
        def test():
            try:
                # Save current env vars
                self.save_env_vars(show_message=False)
                
                import psycopg2
                from dotenv import load_dotenv
                load_dotenv()
                
                conn = psycopg2.connect(
                    host=os.getenv("DB_NEON_HOST"),
                    port=os.getenv("DB_NEON_PORT", "5432"),
                    database=os.getenv("DB_NEON_NAME"),
                    user=os.getenv("DB_NEON_USER"),
                    password=os.getenv("DB_NEON_PASSWORD"),
                    sslmode="require"
                )
                
                cursor = conn.cursor()
                cursor.execute("SELECT version();")
                version = cursor.fetchone()
                cursor.close()
                conn.close()
                
                self.db_result_label.config(
                    text=f"✅ Database connection successful! PostgreSQL {version[0]}",
                    fg=Colors.SUCCESS
                )
                self.update_status("Database connection test passed")
                
            except Exception as e:
                self.db_result_label.config(
                    text=f"❌ Database connection failed: {e}",
                    fg=Colors.ERROR
                )
                self.update_status("Database connection test failed")
                
        threading.Thread(target=test, daemon=True).start()
        
    def download_models(self):
        """Download AI models."""
        def download():
            try:
                self.download_progress_bar.start()
                self.update_status("Downloading AI models...")
                
                models_dir = Path("backend/models")
                models_dir.mkdir(exist_ok=True)
                
                models = {
                    "mistral-7b-instruct-v0.2.Q4_K_M.gguf": {
                        "url": "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf",
                        "size": "4.1GB"
                    },
                    "gemma-3-4b-it-Q4_1.gguf": {
                        "url": "https://huggingface.co/unsloth/gemma-3-4b-it-GGUF/resolve/main/gemma-3-4b-it-Q4_1.gguf",
                        "size": "1.5GB"
                    }
                }
                
                for model_name, model_info in models.items():
                    model_path = models_dir / model_name
                    
                    if model_path.exists():
                        self.download_result_label.config(
                            text=f"✅ {model_name} already exists",
                            fg=Colors.SUCCESS
                        )
                        continue
                    
                    self.update_status(f"Downloading {model_name}...")
                    
                    response = requests.get(model_info["url"], stream=True)
                    response.raise_for_status()
                    
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    
                    with open(model_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                if total_size > 0:
                                    percent = (downloaded / total_size) * 100
                                    self.update_status(f"Downloading {model_name}: {percent:.1f}%")
                    
                    self.download_result_label.config(
                        text=f"✅ Downloaded {model_name} successfully",
                        fg=Colors.SUCCESS
                    )
                
                self.download_progress_bar.stop()
                self.update_status("AI models downloaded successfully")
                
            except Exception as e:
                self.download_progress_bar.stop()
                self.download_result_label.config(
                    text=f"❌ Failed to download models: {e}",
                    fg=Colors.ERROR
                )
                self.update_status("Model download failed")
                
        threading.Thread(target=download, daemon=True).start()
        
    def setup_vector_database(self):
        """Setup vector database."""
        def setup():
            try:
                if not self.update_vec_db_var.get():
                    self.vector_result_label.config(
                        text="⏭️ Skipping vector database update",
                        fg=Colors.WARNING
                    )
                    self.update_status("Vector database update skipped")
                    return
                
                self.update_status("Setting up vector database...")
                
                # Save env vars first
                self.save_env_vars(show_message=False)
                
                # Get the correct Python executable
                python_executable = self.get_python_executable()
                
                result = subprocess.run([
                    python_executable, "backend/src/rag/update_pinecone_from_neon.py"
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.vector_result_label.config(
                        text="✅ Vector database updated successfully",
                        fg=Colors.SUCCESS
                    )
                    self.update_status("Vector database setup completed")
                else:
                    self.vector_result_label.config(
                        text=f"❌ Vector database update failed: {result.stderr}",
                        fg=Colors.ERROR
                    )
                    self.update_status("Vector database setup failed")
                    
            except Exception as e:
                self.vector_result_label.config(
                    text=f"❌ Error setting up vector database: {e}",
                    fg=Colors.ERROR
                )
                self.update_status("Vector database setup failed")
                
        threading.Thread(target=setup, daemon=True).start()
        
    def install_dependencies(self):
        """Install dependencies."""
        def install():
            try:
                self.install_progress_bar.start()
                self.update_status("Installing Python dependencies...")
                
                # Get the correct Python executable
                python_executable = self.get_python_executable()
                
                # Install Python dependencies
                result = subprocess.run([
                    python_executable, "-m", "pip", "install", "-r", "requirements.txt"
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    self.install_result_label.config(
                        text=f"❌ Failed to install Python dependencies: {result.stderr}",
                        fg=Colors.ERROR
                    )
                    self.install_progress_bar.stop()
                    self.update_status("Dependency installation failed")
                    return
                
                self.update_status("Installing Node.js dependencies...")
                
                # Install Node.js dependencies
                frontend_dir = Path("frontend")
                if not frontend_dir.exists():
                    self.install_result_label.config(
                        text="❌ Frontend directory not found",
                        fg=Colors.ERROR
                    )
                    self.install_progress_bar.stop()
                    self.update_status("Dependency installation failed")
                    return
                
                result = subprocess.run(
                    ["npm", "install"], 
                    cwd=frontend_dir, 
                    capture_output=True, 
                    text=True
                )
                
                if result.returncode != 0:
                    self.install_result_label.config(
                        text=f"❌ Failed to install Node.js dependencies: {result.stderr}",
                        fg=Colors.ERROR
                    )
                    self.install_progress_bar.stop()
                    self.update_status("Dependency installation failed")
                    return
                
                self.install_progress_bar.stop()
                self.install_result_label.config(
                    text="✅ All dependencies installed successfully",
                    fg=Colors.SUCCESS
                )
                self.update_status("Dependencies installed successfully")
                
            except Exception as e:
                self.install_progress_bar.stop()
                self.install_result_label.config(
                    text=f"❌ Error installing dependencies: {e}",
                    fg=Colors.ERROR
                )
                self.update_status("Dependency installation failed")
                
        threading.Thread(target=install, daemon=True).start()

    def toggle_password_visibility(self, entry, button):
        """Toggle password field visibility."""
        if entry.cget('show') == '*':
            entry.configure(show='')
            button.configure(text="🙈 Hide")
        else:
            entry.configure(show='*')
            button.configure(text="👁 Show")

    def restart_setup(self):
        """Restart the setup wizard."""
        self.current_step = 0
        self.is_admin = False
        self.show_step(0)

    def show_db_test(self):
        """Show database test step."""
        self.progress_label.config(text="Step 3 of 8: Testing Database Connection")
        
        # Create card
        card = tk.Frame(self.content_frame, bg=Colors.CARD_BG, relief="flat", bd=1)
        card.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Content
        content_frame = tk.Frame(card, bg=Colors.CARD_BG)
        content_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Icon and title
        icon_label = tk.Label(
            content_frame,
            text="🗄️",
            font=("Segoe UI", 48),
            bg=Colors.CARD_BG
        )
        icon_label.pack(pady=(0, 20))
        
        title_label = tk.Label(
            content_frame,
            text="Database Connection Test",
            font=("Segoe UI", 18, "bold"),
            fg=Colors.TEXT,
            bg=Colors.CARD_BG
        )
        title_label.pack()
        
        desc_label = tk.Label(
            content_frame,
            text="Testing connection to your Neon PostgreSQL database",
            font=("Segoe UI", 11),
            fg=Colors.SECONDARY,
            bg=Colors.CARD_BG,
            wraplength=500
        )
        desc_label.pack(pady=(10, 30))
        
        # Test button
        test_btn = ModernButton(
            content_frame,
            text="Test Database Connection",
            command=self.test_database_connection,
            width=20
        )
        test_btn.configure_primary()
        test_btn.pack()
        
        # Result label
        self.db_result_label = tk.Label(
            content_frame,
            text="",
            font=("Segoe UI", 10),
            bg=Colors.CARD_BG,
            wraplength=500
        )
        self.db_result_label.pack(pady=(20, 0))

def main():
    """Main function."""
    try:
        wizard = SetupWizard()
        wizard.run()
    except Exception as e:
        messagebox.showerror("Setup Error", f"Failed to start setup wizard: {e}")

if __name__ == "__main__":
    main() 