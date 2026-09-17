import customtkinter as ctk
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime

matplotlib.use("TkAgg")

class DashboardView(ctk.CTkFrame):
    def __init__(self, master, db, **kwargs):
        super().__init__(master, **kwargs)
        self.db = db
        
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # --- Header ---
        header = ctk.CTkLabel(self, text="Dashboard & Analytics", font=ctk.CTkFont(family="Noteworthy", size=24, weight="bold"))
        header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # --- Content Container ---
        self.content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.content.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.content.grid_columnconfigure((0, 1, 2), weight=1)
        
        self.load_dashboard_data()

    def load_dashboard_data(self):
        # Clear existing
        for widget in self.content.winfo_children():
            widget.destroy()
            
        current_month = datetime.now().strftime("%Y-%m")
        start_date = f"{current_month}-01"
        end_date = f"{current_month}-31"
        
        # Fetch Data
        total_balance = self.db.get_total_balance()
        inc_exp = self.db.get_income_vs_expense(start_date, end_date)
        exp_by_cat = self.db.get_expenses_by_category(start_date, end_date)
        
        total_inc = inc_exp.get('Income', 0.0)
        total_exp = inc_exp.get('Expense', 0.0)
        
        # --- Summary Cards ---
        cards_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        cards_frame.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 20))
        cards_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        currency = self.db.get_setting("currency", "$")
        
        self.create_summary_card(cards_frame, "Total Balance", f"{currency}{total_balance:,.2f}", 0)
        self.create_summary_card(cards_frame, "Monthly Income", f"{currency}{total_inc:,.2f}", 1, color="#2ca02c")
        self.create_summary_card(cards_frame, "Monthly Expenses", f"{currency}{total_exp:,.2f}", 2, color="#d62728")
        
        # --- Charts ---
        chart_frame = ctk.CTkFrame(self.content)
        chart_frame.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=10)
        
        ctk.CTkLabel(chart_frame, text="Expenses by Category (This Month)", font=ctk.CTkFont(family="Noteworthy", size=18, weight="bold")).pack(pady=10)
        
        if not exp_by_cat:
            ctk.CTkLabel(chart_frame, text="No expenses recorded this month.", font=ctk.CTkFont(family="Noteworthy", size=14)).pack(pady=20)
        else:
            self.create_pie_chart(chart_frame, exp_by_cat)
            
        # --- Budget Alerts ---
        alerts_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        alerts_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(20, 10))
        
        alerts = []
        cats = {c['id']: c for c in self.db.get_categories()}
        for exp in exp_by_cat:
            # We need the category budget limit, but get_expenses_by_category doesn't return budget_limit.
            # We can find it from cats dict.
            # Wait, get_expenses_by_category returns name and color_hex. It doesn't return id.
            # I will just match by name.
            matched_cat = next((c for c in cats.values() if c['name'] == exp['name'] and c['type'] == 'Expense'), None)
            if matched_cat:
                limit = matched_cat.get('budget_limit')
                limit = float(limit) if limit is not None else 0.0
                if limit > 0 and exp['total'] > limit:
                    alerts.append(f"WARNING: '{exp['name']}' exceeded budget! ({currency}{exp['total']:.2f} / {currency}{limit:.2f})")
                    
        if alerts:
            ctk.CTkLabel(alerts_frame, text="Budget Alerts", font=ctk.CTkFont(family="Noteworthy", size=18, weight="bold"), text_color="#d62728").pack(pady=5)
            for alert in alerts:
                ctk.CTkLabel(alerts_frame, text=alert, font=ctk.CTkFont(family="Noteworthy", size=14), text_color="#d62728").pack(pady=2)

    def create_summary_card(self, parent, title, value, column, color=None):
        card = ctk.CTkFrame(parent)
        card.grid(row=0, column=column, padx=10, pady=10, sticky="ew")
        
        lbl_title = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(family="Noteworthy", size=14))
        lbl_title.pack(pady=(15, 5))
        
        val_color = color if color else ("black" if ctk.get_appearance_mode() == "Light" else "white")
        lbl_value = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(family="Noteworthy", size=24, weight="bold"), text_color=val_color)
        lbl_value.pack(pady=(0, 15))

    def create_pie_chart(self, parent, exp_by_cat):
        # Filter out categories with zero or negative total to avoid matplotlib crash
        valid_exp = [cat for cat in exp_by_cat if cat['total'] > 0]
        
        if not valid_exp:
            ctk.CTkLabel(parent, text="No positive expenses to chart.", font=ctk.CTkFont(family="Noteworthy", size=14)).pack(pady=20)
            return
            
        labels = [cat['name'] for cat in valid_exp]
        sizes = [cat['total'] for cat in valid_exp]
        
        # Dark mode styling for matplotlib
        bg_color = "#3D3133" if ctk.get_appearance_mode() == "Dark" else "#FCE8EC"
        text_color = "white" if ctk.get_appearance_mode() == "Dark" else "black"
        
        fig, ax = plt.subplots(figsize=(5, 4), facecolor=bg_color)
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, 
               textprops={'color': text_color, 'family': 'fantasy'}) # fantasy is closest to handwritten in default mpl
               
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        plt.close(fig) # Prevent memory leaks
