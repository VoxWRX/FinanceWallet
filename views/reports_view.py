import customtkinter as ctk
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import collections

class ReportsView(ctk.CTkFrame):
    def __init__(self, master, db, **kwargs):
        super().__init__(master, **kwargs)
        self.db = db
        
        self.grid_rowconfigure(0, weight=0) # Header
        self.grid_rowconfigure(1, weight=0) # Controls
        self.grid_rowconfigure(2, weight=1) # Chart
        self.grid_columnconfigure(0, weight=1)
        
        # --- Header ---
        header = ctk.CTkLabel(self, text="Financial Reports", font=ctk.CTkFont(family="Noteworthy", size=24, weight="bold"))
        header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # --- Controls ---
        control_frame = ctk.CTkFrame(self, fg_color="transparent")
        control_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        ctk.CTkLabel(control_frame, text="Type:", font=ctk.CTkFont(family="Noteworthy", size=14)).pack(side="left", padx=5)
        self.report_type_var = ctk.StringVar(value="Annual")
        self.type_menu = ctk.CTkOptionMenu(control_frame, variable=self.report_type_var, values=["Annual", "Monthly"], font=ctk.CTkFont(family="Noteworthy", size=12), command=self.on_type_change)
        self.type_menu.pack(side="left", padx=5)
        
        ctk.CTkLabel(control_frame, text="Year:", font=ctk.CTkFont(family="Noteworthy", size=14)).pack(side="left", padx=5)
        current_year = str(datetime.today().year)
        self.year_var = ctk.StringVar(value=current_year)
        # Populate years from -2 to +1
        years = [str(int(current_year) + i) for i in range(-2, 2)]
        self.year_menu = ctk.CTkOptionMenu(control_frame, variable=self.year_var, values=years, font=ctk.CTkFont(family="Noteworthy", size=12))
        self.year_menu.pack(side="left", padx=5)
        
        self.month_lbl = ctk.CTkLabel(control_frame, text="Month:", font=ctk.CTkFont(family="Noteworthy", size=14))
        self.month_var = ctk.StringVar(value=str(datetime.today().month))
        months = [str(i) for i in range(1, 13)]
        self.month_menu = ctk.CTkOptionMenu(control_frame, variable=self.month_var, values=months, font=ctk.CTkFont(family="Noteworthy", size=12))
        
        # Hide month initially since default is Annual
        self.on_type_change("Annual")
        
        gen_btn = ctk.CTkButton(control_frame, text="Generate", font=ctk.CTkFont(family="Noteworthy", size=14), command=self.generate_report)
        gen_btn.pack(side="left", padx=20)
        
        export_btn = ctk.CTkButton(control_frame, text="Export Excel", width=90, fg_color="#28a745", hover_color="#34ce57", font=ctk.CTkFont(family="Noteworthy", size=14), command=self.export_report)
        export_btn.pack(side="right", padx=20)
        
        self.export_lbl = ctk.CTkLabel(control_frame, text="", font=ctk.CTkFont(family="Noteworthy", size=12))
        self.export_lbl.pack(side="right", padx=5)
        
        # --- Chart Frame ---
        self.chart_frame = ctk.CTkFrame(self)
        self.chart_frame.grid(row=2, column=0, padx=20, pady=20, sticky="nsew")
        self.canvas = None
        
        self.generate_report()
        
    def on_type_change(self, new_type):
        if new_type == "Monthly":
            self.month_lbl.pack(side="left", padx=5)
            self.month_menu.pack(side="left", padx=5)
        else:
            self.month_lbl.pack_forget()
            self.month_menu.pack_forget()
            
    def export_report(self):
        import pandas as pd
        import os
        
        r_type = self.report_type_var.get()
        target_year = self.year_var.get()
        target_month = self.month_var.get() if r_type == "Monthly" else None
        
        txs = self.db.get_transactions()
        cats = {c['id']: c for c in self.db.get_categories()}
        
        export_data = []
        for tx in txs:
            try:
                dt = datetime.strptime(tx['date'], "%Y-%m-%d")
            except ValueError:
                continue
                
            if str(dt.year) != target_year:
                continue
            if r_type == "Monthly" and str(dt.month) != target_month:
                continue
                
            cat = cats.get(tx['category_id'], {})
            export_data.append({
                'Date': tx['date'],
                'Name': tx['name'],
                'Amount': tx['amount'],
                'Type': cat.get('type', 'Unknown'),
                'Category': cat.get('name', 'Unknown'),
                'Tags': tx.get('tags', ''),
                'Description': tx.get('description', '')
            })
            
        if not export_data:
            self.export_lbl.configure(text="No data to export", text_color="red")
            return
            
        try:
            df = pd.DataFrame(export_data)
            exports_dir = os.path.expanduser("~/Desktop/Finance_Wallet_Exports")
            os.makedirs(exports_dir, exist_ok=True)
            
            filename = os.path.join(exports_dir, f"report_{r_type.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
            df.to_excel(filename, index=False)
            self.export_lbl.configure(text="Exported!", text_color="green")
        except Exception as e:
            self.export_lbl.configure(text="Export failed", text_color="red")
            print(f"Report export error: {e}")
            
    def generate_report(self):
        # Clear old chart
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
            
        r_type = self.report_type_var.get()
        target_year = self.year_var.get()
        target_month = self.month_var.get() if r_type == "Monthly" else None
        
        txs = self.db.get_transactions()
        cats = {c['id']: c for c in self.db.get_categories()}
        
        # Filter and aggregate
        income_data = collections.defaultdict(float)
        expense_data = collections.defaultdict(float)
        
        for tx in txs:
            try:
                dt = datetime.strptime(tx['date'], "%Y-%m-%d")
            except ValueError:
                continue
                
            if str(dt.year) != target_year:
                continue
                
            if r_type == "Monthly" and str(dt.month) != target_month:
                continue
                
            amt = tx['amount']
            cat = cats.get(tx['category_id'], {})
            is_income = (cat.get('type') == 'Income')
            
            if r_type == "Annual":
                key = dt.strftime("%b") # e.g. 'Jan', 'Feb'
                sort_val = dt.month
            else:
                key = str(dt.day)
                sort_val = dt.day
                
            if is_income:
                income_data[(sort_val, key)] += amt
            else:
                expense_data[(sort_val, key)] += amt
                
        # Prepare for plotting
        if r_type == "Annual":
            all_keys = [(m, datetime(2000, m, 1).strftime('%b')) for m in range(1, 13)]
        else:
            # Simple 1 to 31 depending on month
            import calendar
            days_in_month = calendar.monthrange(int(target_year), int(target_month))[1] if r_type == "Monthly" else 31
            all_keys = [(d, str(d)) for d in range(1, days_in_month + 1)]
            
        labels = [k[1] for k in all_keys]
        incomes = [income_data[k] for k in all_keys]
        expenses = [expense_data[k] for k in all_keys]
        
        # Plotting
        is_dark = ctk.get_appearance_mode() == "Dark"
        bg_col = "#2b2b2b" if is_dark else "#dbdbdb"
        text_col = "white" if is_dark else "black"
        
        fig, ax = plt.subplots(figsize=(8, 4), facecolor=bg_col)
        ax.set_facecolor(bg_col)
        
        x = range(len(labels))
        width = 0.35
        
        ax.bar([i - width/2 for i in x], incomes, width, label='Income', color='#28a745')
        ax.bar([i + width/2 for i in x], expenses, width, label='Expense', color='#d62728')
        
        ax.set_ylabel('Amount')
        ax.set_title(f"{r_type} Report - {target_year}" + (f"/{target_month}" if target_month else ""))
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45 if r_type == "Annual" else 90)
        ax.legend()
        
        # Style tweaks
        ax.tick_params(colors=text_col)
        ax.yaxis.label.set_color(text_col)
        ax.title.set_color(text_col)
        for spine in ax.spines.values():
            spine.set_edgecolor(text_col)
            
        fig.tight_layout()
        
        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
