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
        self.root = tk.Tk()
        self.root.title("FAQBuddy Setup Wizard")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        self.root.configure(bg='#f0f0f0')
        
        # Initialize admin status
        self.is_admin = False
        
        # Center the window
        self.center_window()
        
        # Setup variables
        self.current_step = 0
        self.total_steps = 6
        self.env_vars = {}
        self.env_entries = {}  # Dictionary to store entry widgets
        self.progress_queue = queue.Queue()
        
        # Load existing .env if present
        self.load_existing_env()
        
        # Create UI
        self.create_widgets()
        self.show_step(0)
        
        # Start progress monitoring
        self.monitor_progress()
        
        # Role selection and admin authentication logic
        self.role_selection()
        
    def center_window(self):
        """Center the window on screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
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
                "DB_USER": os.getenv("DB_USER", "db_user"),
                "DB_PASSWORD": os.getenv("DB_PASSWORD", "pwd"),
                "DB_NAME": os.getenv("DB_NAME", "faqbuddy_db"),
                "DB_HOST": os.getenv("DB_HOST", "localhost"),
                "DB_PORT": os.getenv("DB_PORT", "5433"),
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
                "DB_USER": "db_user",
                "DB_PASSWORD": "pwd",
                "DB_NAME": "faqbuddy_db",
                "DB_HOST": "localhost",
                "DB_PORT": "5433",
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
        
        # Fixed bottom navigation (created separately)
        self.create_navigation()
        
        # Status bar (created separately)
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
            text="Step 1 of 6: Checking Python Version",
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
            text="🔄 Logout",
            command=self.return_to_role_selection,
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
        self.logout_btn.pack(side="left")
        
        # Back button
        self.back_btn = ModernButton(
            nav_frame,
            text="← Back",
            command=self.previous_step,
            width=10
        )
        self.back_btn.configure_secondary()
        self.back_btn.pack(side="left", padx=(10, 0))
        
        # Next button
        self.next_btn = ModernButton(
            nav_frame,
            text="Next →",
            command=self.next_step,
            width=10
        )
        self.next_btn.configure_primary()
        self.next_btn.pack(side="right")
        
        # Initially disable back button
        self.back_btn.configure(state="disabled")
        
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
        
    def show_step(self, step):
        """Show the specified step."""
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        # Clear environment entries to prevent stale references
        self.env_entries = {}
            
        self.current_step = step
        
        # Update progress based on role
        if self.is_admin:
            progress = ((step + 1) / self.total_steps) * 100
        else:
            # For users, skip admin-only steps
            user_steps = [0, 1, 3, 4, 5, 6]  # Python check, env setup, model download, vector db, deps, completion
            if step in user_steps:
                user_step_index = user_steps.index(step)
                progress = ((user_step_index + 1) / len(user_steps)) * 100
            else:
                progress = 0
        self.progress_bar['value'] = progress
        
        # Show appropriate step
        if step == 0:
            self.show_python_check()
        elif step == 1:
            self.show_env_setup()
        elif step == 2:
            if self.is_admin:
                self.show_db_test()
            else:
                self.show_step(3)  # Skip DB test for users
        elif step == 3:
            self.show_model_download()
        elif step == 4:
            self.show_vector_db_setup()
        elif step == 5:
            self.show_dependency_install()
        elif step == 6:
            self.show_completion()
            
        # Update navigation
        self.update_navigation()
        
    def show_python_check(self):
        """Show Python version check step."""
        self.progress_label.config(text="Step 1 of 6: Checking Python Version")
        
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
        self.progress_label.config(text="Step 2 of 6: Environment Configuration")
        
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
            
    def show_db_test(self):
        """Show database test step."""
        self.progress_label.config(text="Step 3 of 6: Testing Database Connection")
        
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
        
    def show_model_download(self):
        """Show model download step."""
        self.progress_label.config(text="Step 4 of 6: Downloading AI Models")
        
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
        self.progress_label.config(text="Step 5 of 6: Setting up Vector Database")
        
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
        self.progress_label.config(text="Step 6 of 6: Installing Dependencies")
        
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
        
    def save_env_vars(self):
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
                        "DB_USER": os.getenv("DB_USER", "db_user"),
                        "DB_PASSWORD": os.getenv("DB_PASSWORD", "pwd"),
                        "DB_NAME": os.getenv("DB_NAME", "faqbuddy_db"),
                        "DB_HOST": os.getenv("DB_HOST", "localhost"),
                        "DB_PORT": os.getenv("DB_PORT", "5433"),
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
                    "DB_USER": "db_user",
                    "DB_PASSWORD": "pwd",
                    "DB_NAME": "faqbuddy_db",
                    "DB_HOST": "localhost",
                    "DB_PORT": "5433",
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
            
            # Show success message only for admin or when actually saving
            if self.is_admin or self.env_entries:
                messagebox.showinfo("Success", "Environment variables saved successfully!")
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save environment variables: {e}")
            
    def launch_faqbuddy(self):
        """Launch FAQBuddy."""
        try:
            # Show confirmation dialog
            result = messagebox.askyesno("Launch FAQBuddy", "Do you want to launch FAQBuddy now? This will start both the backend and frontend servers.")
            if result:
                subprocess.Popen([sys.executable, "launch_servers.py"])
                self.root.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch FAQBuddy: {e}")
            
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
                self.save_env_vars()
            self.show_step(self.current_step + 1)
            
    def run(self):
        """Run the setup wizard."""
        self.root.mainloop()

    def role_selection(self):
        """Show a modal for role selection and handle admin authentication."""
        self.role_window = tk.Toplevel(self.root)
        self.role_window.title("Select Role")
        self.role_window.geometry("500x350")
        self.role_window.configure(bg=Colors.BACKGROUND)
        self.role_window.grab_set()
        self.role_window.resizable(False, False)
        self.role_window.transient(self.root)
        self.role_window.protocol("WM_DELETE_WINDOW", self.root.destroy)

        # Center the modal
        self.role_window.update_idletasks()
        width = self.role_window.winfo_width()
        height = self.role_window.winfo_height()
        x = (self.role_window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.role_window.winfo_screenheight() // 2) - (height // 2)
        self.role_window.geometry(f"{width}x{height}+{x}+{y}")

        # Main container
        main_frame = tk.Frame(self.role_window, bg=Colors.BACKGROUND)
        main_frame.pack(fill="both", expand=True, padx=40, pady=40)

        # Icon
        icon_label = tk.Label(
            main_frame, 
            text="🚀", 
            font=("Segoe UI", 48), 
            bg=Colors.BACKGROUND
        )
        icon_label.pack(pady=(0, 20))

        # Title
        title = tk.Label(
            main_frame, 
            text="Welcome to FAQBuddy Setup", 
            font=("Segoe UI", 20, "bold"), 
            fg=Colors.PRIMARY, 
            bg=Colors.BACKGROUND
        )
        title.pack(pady=(0, 10))

        subtitle = tk.Label(
            main_frame, 
            text="Please select your role to continue:", 
            font=("Segoe UI", 12), 
            fg=Colors.SECONDARY, 
            bg=Colors.BACKGROUND
        )
        subtitle.pack(pady=(0, 30))

        # Buttons container
        btn_frame = tk.Frame(main_frame, bg=Colors.BACKGROUND)
        btn_frame.pack(fill="x", pady=20)

        # Admin button with modern styling
        admin_btn = tk.Button(
            btn_frame, 
            text="👨‍💼 Admin", 
            width=20, 
            height=3, 
            bg=Colors.PRIMARY, 
            fg="white", 
            font=("SF Pro Display", 12, "bold"),
            activebackground=Colors.BUTTON_HOVER, 
            activeforeground="white", 
            relief="flat", 
            cursor="hand2",
            command=self.admin_login_modal, 
            padx=30, 
            pady=12,
            borderwidth=0
        )
        admin_btn.pack(pady=(0, 15), fill="x")

        # User button with modern styling
        user_btn = tk.Button(
            btn_frame, 
            text="👤 User", 
            width=20, 
            height=3, 
            bg=Colors.SECONDARY, 
            fg="white", 
            font=("SF Pro Display", 12, "bold"),
            activebackground="#6D6D70", 
            activeforeground="white", 
            relief="flat", 
            cursor="hand2",
            command=self.user_select, 
            padx=30, 
            pady=12,
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

    def admin_login_modal(self):
        """Prompt for admin password."""
        for widget in self.role_window.winfo_children():
            widget.destroy()
        
        # Main container
        main_frame = tk.Frame(self.role_window, bg=Colors.BACKGROUND)
        main_frame.pack(fill="both", expand=True, padx=40, pady=40)
        
        # Icon
        icon_label = tk.Label(
            main_frame, 
            text="🔐", 
            font=("Segoe UI", 48), 
            bg=Colors.BACKGROUND
        )
        icon_label.pack(pady=(0, 20))
        
        title = tk.Label(
            main_frame, 
            text="Admin Login", 
            font=("Segoe UI", 20, "bold"), 
            fg=Colors.PRIMARY, 
            bg=Colors.BACKGROUND
        )
        title.pack(pady=(0, 10))
        
        subtitle = tk.Label(
            main_frame, 
            text="Enter admin password to continue:", 
            font=("Segoe UI", 12), 
            fg=Colors.SECONDARY, 
            bg=Colors.BACKGROUND
        )
        subtitle.pack(pady=(0, 30))
        
        # Password entry frame
        entry_frame = tk.Frame(main_frame, bg=Colors.BACKGROUND)
        entry_frame.pack(fill="x", pady=(0, 20))
        
        self.admin_pw_var = tk.StringVar()
        pw_entry = tk.Entry(
            entry_frame, 
            textvariable=self.admin_pw_var, 
            show="*", 
            font=("Segoe UI", 14), 
            width=25, 
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
            main_frame, 
            text="", 
            font=("Segoe UI", 10), 
            fg=Colors.ERROR, 
            bg=Colors.BACKGROUND
        )
        self.admin_pw_error.pack(pady=(0, 30))
        
        # Buttons frame
        btn_frame = tk.Frame(main_frame, bg=Colors.BACKGROUND)
        btn_frame.pack(fill="x", pady=20)
        
        # Submit button
        submit_btn = tk.Button(
            btn_frame, 
            text="🔓 Login", 
            width=15, 
            height=2, 
            bg=Colors.PRIMARY, 
            fg="white", 
            font=("SF Pro Display", 12, "bold"),
            activebackground=Colors.BUTTON_HOVER, 
            activeforeground="white", 
            relief="flat", 
            cursor="hand2",
            command=self.check_admin_password, 
            padx=20, 
            pady=8,
            borderwidth=0
        )
        submit_btn.pack(side="left", padx=(0, 10), fill="x", expand=True)
        
        # Back button
        back_btn = tk.Button(
            btn_frame, 
            text="← Back", 
            width=15, 
            height=2, 
            bg=Colors.SECONDARY, 
            fg="white", 
            font=("SF Pro Display", 12, "bold"),
            activebackground="#6D6D70", 
            activeforeground="white", 
            relief="flat", 
            cursor="hand2",
            command=self.reset_role_modal, 
            padx=20, 
            pady=8,
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
        pw = self.admin_pw_var.get()
        if pw == 'faqbuddy-admin-panel-funtori-yessir-1970':
            self.is_admin = True
            self.role_window.destroy()
        else:
            self.admin_pw_error.config(text="Incorrect password. Please try again.")

    def user_select(self):
        self.is_admin = False
        self.role_window.destroy()

    def reset_role_modal(self):
        self.role_window.destroy()
        self.role_selection()

    def return_to_role_selection(self):
        """Return to the role selection modal from anywhere in the wizard."""
        self.role_selection()

    def show_tooltip(self, event, text):
        """Show a tooltip with help text."""
        tooltip = tk.Toplevel()
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
        
        label = tk.Label(tooltip, text=text, justify="left", background="#ffffe0", relief="solid", borderwidth=1, font=("Segoe UI", 9))
        label.pack()
        
        def hide_tooltip():
            tooltip.destroy()
        
        tooltip.bind("<Leave>", lambda e: hide_tooltip())
        tooltip.bind("<Button-1>", lambda e: hide_tooltip())
        
        # Auto-hide after 3 seconds
        tooltip.after(3000, hide_tooltip)

    def update_navigation(self):
        """Update navigation buttons."""
        if self.current_step == 0:
            self.back_btn.configure(state="disabled")
        else:
            self.back_btn.configure(state="normal")
            
        if self.current_step == self.total_steps:
            self.next_btn.configure(text="Finish", state="disabled")
        else:
            self.next_btn.configure(text="Next →", state="normal")
            
    def toggle_password_visibility(self, entry, button):
        """Toggle password field visibility."""
        if entry.cget('show') == '*':
            entry.configure(show='')
            button.configure(text="🙈 Hide")
        else:
            entry.configure(show='*')
            button.configure(text="👁 Show")
            
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
                self.save_env_vars()
                
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
                self.save_env_vars()
                
                result = subprocess.run([
                    sys.executable, "backend/src/rag/update_pinecone_from_neon.py"
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
                
                # Install Python dependencies
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", "backend/src/requirements.txt"
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

def main():
    """Main function."""
    try:
        wizard = SetupWizard()
        wizard.run()
    except Exception as e:
        messagebox.showerror("Setup Error", f"Failed to start setup wizard: {e}")

if __name__ == "__main__":
    main() 