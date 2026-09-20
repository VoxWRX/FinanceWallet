import customtkinter as ctk
import sys
import os

# Ensure backend module can be imported
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))
from backend.database import DatabaseManager
from backend.auth import AuthManager

class App(ctk.CTk):
    def __init__(self, db_path, current_username):
        super().__init__()

        self.title("Personal Finance Wallet")
        self.geometry("1000x700")
        
        self.current_username = current_username

        # Initialize the database connection for the specific user
        self.db = DatabaseManager(db_path)

        # Set up grid layout (1x2): Sidebar and Main Frame
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # --- Sidebar Navigation ---
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Finance Wallet", font=ctk.CTkFont(family="Noteworthy", size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.home_button = ctk.CTkButton(self.sidebar_frame, text="Home (Calendar)", font=ctk.CTkFont(family="Noteworthy", size=14), command=self.show_home_view)
        self.home_button.grid(row=1, column=0, padx=20, pady=10)

        self.dashboard_button = ctk.CTkButton(self.sidebar_frame, text="Dashboard", font=ctk.CTkFont(family="Noteworthy", size=14), command=self.show_dashboard_view)
        self.dashboard_button.grid(row=2, column=0, padx=20, pady=10)

        self.categories_tx_button = ctk.CTkButton(self.sidebar_frame, text="Transactions", font=ctk.CTkFont(family="Noteworthy", size=14), command=self.show_transactions_view)
        self.categories_tx_button.grid(row=3, column=0, padx=20, pady=10)

        self.savings_button = ctk.CTkButton(self.sidebar_frame, text="Savings", font=ctk.CTkFont(family="Noteworthy", size=14), command=self.show_savings_view)
        self.savings_button.grid(row=4, column=0, padx=20, pady=10)

        self.reports_button = ctk.CTkButton(self.sidebar_frame, text="Reports", font=ctk.CTkFont(family="Noteworthy", size=14), command=self.show_reports_view)
        self.reports_button.grid(row=5, column=0, padx=20, pady=10)

        self.settings_button = ctk.CTkButton(self.sidebar_frame, text="Settings", font=ctk.CTkFont(family="Noteworthy", size=14), command=self.show_settings_view)
        self.settings_button.grid(row=6, column=0, padx=20, pady=10)
        
        self.logout_button = ctk.CTkButton(self.sidebar_frame, text="Logout", fg_color="#d62728", hover_color="#ff7f7e", font=ctk.CTkFont(family="Noteworthy", size=14), command=self.logout)
        self.logout_button.grid(row=8, column=0, padx=20, pady=20)

        # --- Main Frame ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Start with Home View
        self.current_view = None
        
        # Ensure a default category exists for the quick-add feature
        cats = self.db.get_categories()
        if not cats:
            self.db.add_category("General", "Expense", "#808080")
            
        # Set Theme properly from user DB
        saved_theme = self.db.get_setting("theme", "Blue").lower()
        if saved_theme == "rose":
            import sys
            base_path = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
            ctk.set_default_color_theme(os.path.join(base_path, "themes", "rose_theme.json"))
        else:
            ctk.set_default_color_theme(saved_theme)
            
        self.show_home_view()
        self.after(2000, self.refresh_loop)

    def refresh_loop(self):
        try:
            if self.current_view:
                if hasattr(self.current_view, 'load_dashboard_data') and self.current_view.winfo_ismapped():
                    # Check if it needs refresh to avoid flicker? 
                    pass # actually rebuilding matplotlib flickers. We will only refresh Home or Management if needed
                elif hasattr(self.current_view, 'load_transactions') and hasattr(self.current_view, 'load_categories'):
                    # Management View
                    pass
        except Exception:
            pass
        self.after(5000, self.refresh_loop)

    def logout(self):
        self.destroy()
        python = sys.executable
        os.execv(python, ['python'] + sys.argv)

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)
        
    def _clear_main_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_home_view(self):
        self._clear_main_frame()
        from views.home_view import HomeView
        self.current_view = HomeView(self.main_frame, self.db)
        self.current_view.grid(row=0, column=0, sticky="nsew")

    def show_dashboard_view(self):
        self._clear_main_frame()
        from views.dashboard_view import DashboardView
        self.current_view = DashboardView(self.main_frame, self.db)
        self.current_view.grid(row=0, column=0, sticky="nsew")

    def show_transactions_view(self):
        self._clear_main_frame()
        from views.management_view import ManagementView
        self.current_view = ManagementView(self.main_frame, self.db)
        self.current_view.grid(row=0, column=0, sticky="nsew")

    def show_savings_view(self):
        self._clear_main_frame()
        from views.savings_view import SavingsView
        self.current_view = SavingsView(self.main_frame, self.db)
        self.current_view.grid(row=0, column=0, sticky="nsew")

    def show_reports_view(self):
        self._clear_main_frame()
        from views.reports_view import ReportsView
        self.current_view = ReportsView(self.main_frame, self.db)
        self.current_view.grid(row=0, column=0, sticky="nsew")

    def show_settings_view(self):
        self._clear_main_frame()
        label = ctk.CTkLabel(self.main_frame, text="User Settings", font=ctk.CTkFont(family="Noteworthy", size=24, weight="bold"))
        label.pack(pady=20, padx=20, anchor="w")
        
        # Appearance Mode
        appearance_frame = ctk.CTkFrame(self.main_frame)
        appearance_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(appearance_frame, text="Appearance Mode:", font=ctk.CTkFont(family="Noteworthy", size=16)).pack(side="left", padx=20, pady=20)
        
        appearance_mode_optionemenu = ctk.CTkOptionMenu(appearance_frame, values=["Light", "Dark", "System"],
                                                                       command=self.change_appearance_mode_event, font=ctk.CTkFont(family="Noteworthy", size=14))
        appearance_mode_optionemenu.pack(side="right", padx=20, pady=20)
        appearance_mode_optionemenu.set(ctk.get_appearance_mode())
        
        # Color Theme
        theme_frame = ctk.CTkFrame(self.main_frame)
        theme_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(theme_frame, text="Color Theme (Requires App Restart):", font=ctk.CTkFont(family="Noteworthy", size=16)).pack(side="left", padx=20, pady=20)
        
        self.theme_optionmenu = ctk.CTkOptionMenu(theme_frame, values=["Blue", "Rose", "Dark-Blue", "Green"],
                                                  command=self.change_theme_event, font=ctk.CTkFont(family="Noteworthy", size=14))
        self.theme_optionmenu.pack(side="right", padx=20, pady=20)
        
        # Determine current theme to display
        current_theme = self.db.get_setting("theme", "Blue")
        self.theme_optionmenu.set(current_theme.capitalize())
        
        # Currency
        currency_frame = ctk.CTkFrame(self.main_frame)
        currency_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(currency_frame, text="Preferred Currency:", font=ctk.CTkFont(family="Noteworthy", size=16)).pack(side="left", padx=20, pady=20)
        
        self.currency_optionmenu = ctk.CTkOptionMenu(currency_frame, values=["$", "€", "£", "¥", "₹", "MAD"],
                                                  command=self.change_currency_event, font=ctk.CTkFont(family="Noteworthy", size=14))
        self.currency_optionmenu.pack(side="right", padx=20, pady=20)
        self.currency_optionmenu.set(self.db.get_setting("currency", "$"))
        
        # Change Password
        pw_frame = ctk.CTkFrame(self.main_frame)
        pw_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(pw_frame, text="Change Password:", font=ctk.CTkFont(family="Noteworthy", size=16, weight="bold")).pack(anchor="w", padx=20, pady=(20, 10))
        
        inputs_frame = ctk.CTkFrame(pw_frame, fg_color="transparent")
        inputs_frame.pack(fill="x", padx=20, pady=10)
        
        old_pw = ctk.CTkEntry(inputs_frame, placeholder_text="Old Password", show="*", font=ctk.CTkFont(family="Noteworthy", size=14))
        old_pw.pack(side="left", padx=(0, 10))
        
        new_pw = ctk.CTkEntry(inputs_frame, placeholder_text="New Password", show="*", font=ctk.CTkFont(family="Noteworthy", size=14))
        new_pw.pack(side="left", padx=10)
        
        confirm_pw = ctk.CTkEntry(inputs_frame, placeholder_text="Confirm New", show="*", font=ctk.CTkFont(family="Noteworthy", size=14))
        confirm_pw.pack(side="left", padx=10)
        
        pw_lbl = ctk.CTkLabel(inputs_frame, text="", font=ctk.CTkFont(family="Noteworthy", size=12))
        pw_lbl.pack(side="left", padx=10)
        
        def do_change_pw():
            o = old_pw.get()
            n = new_pw.get()
            c = confirm_pw.get()
            if not o or not n or not c: return
            
            if n != c:
                pw_lbl.configure(text="Passwords do not match!", text_color="red")
                return
                
            auth = AuthManager()
            success, msg = auth.change_password(self.current_username, o, n)
            pw_lbl.configure(text=msg, text_color="green" if success else "red")
            if success:
                old_pw.delete(0, 'end')
                new_pw.delete(0, 'end')
                confirm_pw.delete(0, 'end')
                
        ctk.CTkButton(inputs_frame, text="Update", font=ctk.CTkFont(family="Noteworthy", size=14), command=do_change_pw).pack(side="right")

    def change_currency_event(self, new_currency: str):
        self.db.set_setting("currency", new_currency)
        print(f"Currency updated to {new_currency}")

    def change_theme_event(self, new_theme: str):
        # Save theme to database
        self.db.set_setting("theme", new_theme)
        
        print(f"Theme set to {new_theme}. Restarting app to apply changes...")
        # Restart the app
        python = sys.executable
        os.execv(python, ['python'] + sys.argv)


class AuthWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Finance Wallet - Login")
        self.geometry("400x500")
        self.auth = AuthManager()
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header
        ctk.CTkLabel(self, text="Welcome to Finance Wallet", font=ctk.CTkFont(family="Noteworthy", size=24, weight="bold")).pack(pady=(40, 20))
        
        # Tabs
        self.tabview = ctk.CTkTabview(self, width=300)
        self.tabview.pack(padx=20, pady=10, fill="both", expand=True)
        
        self.tab_login = self.tabview.add("Login")
        self.tab_signup = self.tabview.add("Signup")
        self.tab_users = self.tabview.add("Users")
        
        self.setup_login_tab()
        self.setup_signup_tab()
        self.setup_users_tab()
        
    def setup_login_tab(self):
        ctk.CTkLabel(self.tab_login, text="Username:", font=ctk.CTkFont(family="Noteworthy", size=14)).pack(pady=(20, 5))
        self.login_user_var = ctk.StringVar()
        self.login_user = ctk.CTkEntry(self.tab_login, width=200, textvariable=self.login_user_var, font=ctk.CTkFont(family="Noteworthy", size=14))
        self.login_user.pack(pady=5)
        
        ctk.CTkLabel(self.tab_login, text="Password:", font=ctk.CTkFont(family="Noteworthy", size=14)).pack(pady=(10, 5))
        self.login_pass = ctk.CTkEntry(self.tab_login, width=200, show="*", font=ctk.CTkFont(family="Noteworthy", size=14))
        self.login_pass.pack(pady=5)
        
        self.login_err = ctk.CTkLabel(self.tab_login, text="", text_color="red", font=ctk.CTkFont(family="Noteworthy", size=12))
        self.login_err.pack(pady=5)
        
        ctk.CTkButton(self.tab_login, text="Login", width=200, font=ctk.CTkFont(family="Noteworthy", size=14), command=self.do_login).pack(pady=20)
        
    def setup_signup_tab(self):
        ctk.CTkLabel(self.tab_signup, text="Username:", font=ctk.CTkFont(family="Noteworthy", size=14)).pack(pady=(20, 5))
        self.signup_user = ctk.CTkEntry(self.tab_signup, width=200, font=ctk.CTkFont(family="Noteworthy", size=14))
        self.signup_user.pack(pady=5)
        
        ctk.CTkLabel(self.tab_signup, text="Password:", font=ctk.CTkFont(family="Noteworthy", size=14)).pack(pady=(10, 5))
        self.signup_pass = ctk.CTkEntry(self.tab_signup, width=200, show="*", font=ctk.CTkFont(family="Noteworthy", size=14))
        self.signup_pass.pack(pady=5)
        
        self.signup_err = ctk.CTkLabel(self.tab_signup, text="", text_color="red", font=ctk.CTkFont(family="Noteworthy", size=12))
        self.signup_err.pack(pady=5)
        
        ctk.CTkButton(self.tab_signup, text="Create Account", width=200, font=ctk.CTkFont(family="Noteworthy", size=14), command=self.do_signup).pack(pady=20)

    def setup_users_tab(self):
        ctk.CTkLabel(self.tab_users, text="Registered Users", font=ctk.CTkFont(family="Noteworthy", size=16, weight="bold")).pack(pady=(10, 10))
        
        scroll = ctk.CTkScrollableFrame(self.tab_users, width=250, height=200)
        scroll.pack(pady=10)
        
        users = self.auth.get_all_users()
        if not users:
            ctk.CTkLabel(scroll, text="No users yet.", font=ctk.CTkFont(family="Noteworthy", size=14), text_color="gray").pack(pady=20)
        else:
            for u in users:
                btn = ctk.CTkButton(scroll, text=u, fg_color="transparent", hover_color="gray", text_color=("black", "white"), font=ctk.CTkFont(family="Noteworthy", size=14))
                btn.configure(command=lambda user=u: self.autofill_login(user))
                btn.pack(fill="x", pady=2)
                
    def autofill_login(self, username):
        self.login_user_var.set(username)
        self.after(50, lambda: self.tabview.set("Login"))
        self.after(100, lambda: self.login_pass.focus_set())

    def do_login(self):
        u = self.login_user.get()
        p = self.login_pass.get()
        success, res = self.auth.login(u, p)
        if success:
            self.launch_app(res, u)
        else:
            self.login_err.configure(text=res)
            
    def do_signup(self):
        u = self.signup_user.get()
        p = self.signup_pass.get()
        success, res = self.auth.signup(u, p)
        if success:
            self.launch_app(res, u)
        else:
            self.signup_err.configure(text=res)
            
    def launch_app(self, db_path, username):
        self.destroy()
        app = App(db_path, username)
        app.mainloop()

if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue") # Base theme for Auth Window
    
    auth_app = AuthWindow()
    auth_app.mainloop()
