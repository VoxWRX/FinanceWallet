import customtkinter as ctk
from datetime import datetime

class ManagementView(ctk.CTkFrame):
    def __init__(self, master, db, **kwargs):
        super().__init__(master, **kwargs)
        self.db = db
        
        self.grid_rowconfigure(0, weight=0) # Header
        self.grid_rowconfigure(1, weight=1) # Tabview
        self.grid_columnconfigure(0, weight=1)
        
        # --- Header ---
        header = ctk.CTkLabel(self, text="Management", font=ctk.CTkFont(family="Noteworthy", size=24, weight="bold"))
        header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # --- Tabs ---
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        self.tab_tx = self.tabview.add("Transactions")
        self.tab_cat = self.tabview.add("Categories")
        
        self.setup_transactions_tab()
        self.setup_categories_tab()
        
    def setup_transactions_tab(self):
        self.tab_tx.grid_rowconfigure(1, weight=1)
        self.tab_tx.grid_columnconfigure(0, weight=1)
        
        # Filters & Actions
        top_bar = ctk.CTkFrame(self.tab_tx, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        self.start_date_entry = ctk.CTkEntry(top_bar, placeholder_text="Start (YYYY-MM-DD)", width=130, font=ctk.CTkFont(family="Noteworthy", size=12))
        self.start_date_entry.pack(side="left", padx=5)
        
        self.end_date_entry = ctk.CTkEntry(top_bar, placeholder_text="End (YYYY-MM-DD)", width=130, font=ctk.CTkFont(family="Noteworthy", size=12))
        self.end_date_entry.pack(side="left", padx=5)
        
        self.type_var = ctk.StringVar(value="All")
        type_dropdown = ctk.CTkOptionMenu(top_bar, variable=self.type_var, values=["All", "Expense", "Income"], width=100, font=ctk.CTkFont(family="Noteworthy", size=12))
        type_dropdown.pack(side="left", padx=5)
        
        self.tag_filter_entry = ctk.CTkEntry(top_bar, placeholder_text="Tag (e.g. food)", width=100, font=ctk.CTkFont(family="Noteworthy", size=12))
        self.tag_filter_entry.pack(side="left", padx=5)
        
        filter_btn = ctk.CTkButton(top_bar, text="Filter", width=60, font=ctk.CTkFont(family="Noteworthy", size=12), command=self.load_transactions)
        filter_btn.pack(side="left", padx=5)
        
        refresh_btn = ctk.CTkButton(top_bar, text="Refresh", width=60, fg_color="#1f538d", hover_color="#14375e", font=ctk.CTkFont(family="Noteworthy", size=12), command=self.load_transactions)
        refresh_btn.pack(side="left", padx=5)
        
        export_btn = ctk.CTkButton(top_bar, text="Export Excel", width=90, fg_color="#28a745", hover_color="#34ce57", font=ctk.CTkFont(family="Noteworthy", size=12), command=self.export_excel)
        export_btn.pack(side="right", padx=5)
        
        self.export_lbl = ctk.CTkLabel(top_bar, text="", font=ctk.CTkFont(family="Noteworthy", size=12))
        self.export_lbl.pack(side="right", padx=5)
        
        # List
        self.tx_list_frame = ctk.CTkScrollableFrame(self.tab_tx)
        self.tx_list_frame.grid(row=1, column=0, sticky="nsew")
        
        self.load_transactions()
        
    def get_filtered_transactions(self):
        sd = self.start_date_entry.get().strip()
        ed = self.end_date_entry.get().strip()
        
        txs = self.db.get_transactions(start_date=sd if sd else None, end_date=ed if ed else None)
        cats = {c['id']: c for c in self.db.get_categories()}
        
        for tx in txs:
            cat = cats.get(tx.get('category_id'), {})
            tx['type'] = cat.get('type', 'Expense')
            tx['category_name'] = cat.get('name', 'Unknown')
        
        t_type = self.type_var.get()
        if t_type != "All":
            txs = [tx for tx in txs if tx.get('type') == t_type]
            
        tag_val = self.tag_filter_entry.get().strip().lower()
        if tag_val:
            txs = [tx for tx in txs if tx.get('tags') and tag_val in tx.get('tags').lower()]
            
        return txs

    def export_excel(self):
        import pandas as pd
        import os
        txs = self.get_filtered_transactions()
        if not txs:
            self.export_lbl.configure(text="No data to export", text_color="red")
            return
            
        try:
            df = pd.DataFrame(txs)
            # Reorder and filter columns
            cols = ['date', 'name', 'type', 'category_name', 'amount', 'tags', 'description', 'is_recurring']
            df = df[[c for c in cols if c in df.columns]]
            
            # Save to an 'exports' folder inside the project directory
            exports_dir = os.path.expanduser("~/Desktop/Finance_Wallet_Exports")
            os.makedirs(exports_dir, exist_ok=True)
            
            filename = os.path.join(exports_dir, f"finance_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
            
            df.to_excel(filename, index=False)
            self.export_lbl.configure(text=f"Exported to 'exports' folder!", text_color="green")
        except Exception as e:
            self.export_lbl.configure(text=f"Export failed", text_color="red")
            print(f"Export error: {e}")

    def load_transactions(self):
        for widget in self.tx_list_frame.winfo_children():
            widget.destroy()
            
        currency = self.db.get_setting("currency", "$")
        txs = self.get_filtered_transactions()
        for tx in txs:
            row = ctk.CTkFrame(self.tx_list_frame)
            row.pack(fill="x", pady=2, padx=2)
            
            # Simple row layout
            date_lbl = ctk.CTkLabel(row, text=tx['date'], width=100, font=ctk.CTkFont(family="Noteworthy", size=12))
            date_lbl.pack(side="left", padx=5)
            
            name_lbl = ctk.CTkLabel(row, text=tx['name'], width=150, anchor="w", font=ctk.CTkFont(family="Noteworthy", size=12))
            name_lbl.pack(side="left", padx=5)
            
            tags = tx.get('tags')
            if tags:
                tags_lbl = ctk.CTkLabel(row, text=f"[{tags}]", width=100, text_color="gray", font=ctk.CTkFont(family="Noteworthy", size=10))
                tags_lbl.pack(side="left", padx=5)
                
            amt_lbl = ctk.CTkLabel(row, text=f"{currency}{tx['amount']:.2f}", width=100, anchor="e", font=ctk.CTkFont(family="Noteworthy", size=12, weight="bold"))
            amt_lbl.pack(side="left", padx=5)
            
            # Actions
            del_btn = ctk.CTkButton(row, text="Delete", width=60, fg_color="#d62728", hover_color="#ff7f7e", font=ctk.CTkFont(family="Noteworthy", size=10),
                                    command=lambda t_id=tx['id']: self.delete_transaction(t_id))
            del_btn.pack(side="right", padx=5, pady=5)
            
    def delete_transaction(self, tx_id):
        self.db.delete_transaction(tx_id)
        self.load_transactions()

    def setup_categories_tab(self):
        self.tab_cat.grid_rowconfigure(1, weight=1)
        self.tab_cat.grid_columnconfigure(0, weight=1)
        
        # Add form
        add_frame = ctk.CTkFrame(self.tab_cat, fg_color="transparent")
        add_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        self.cat_name_entry = ctk.CTkEntry(add_frame, placeholder_text="New Category Name", font=ctk.CTkFont(family="Noteworthy", size=12))
        self.cat_name_entry.pack(side="left", padx=5)
        
        self.cat_budget_entry = ctk.CTkEntry(add_frame, placeholder_text="Budget Limit (0 = None)", width=150, font=ctk.CTkFont(family="Noteworthy", size=12))
        self.cat_budget_entry.pack(side="left", padx=5)
        
        self.cat_type_var = ctk.StringVar(value="Expense")
        cat_type_seg = ctk.CTkSegmentedButton(add_frame, values=["Expense", "Income"], variable=self.cat_type_var, font=ctk.CTkFont(family="Noteworthy", size=12))
        cat_type_seg.pack(side="left", padx=5)
        
        add_btn = ctk.CTkButton(add_frame, text="Add", width=60, font=ctk.CTkFont(family="Noteworthy", size=12), command=self.add_category)
        add_btn.pack(side="left", padx=5)
        
        self.cat_error_lbl = ctk.CTkLabel(add_frame, text="", text_color="red", font=ctk.CTkFont(family="Noteworthy", size=12))
        self.cat_error_lbl.pack(side="left", padx=5)
        
        # List
        self.cat_list_frame = ctk.CTkScrollableFrame(self.tab_cat)
        self.cat_list_frame.grid(row=1, column=0, sticky="nsew")
        
        self.load_categories()

    def add_category(self):
        name = self.cat_name_entry.get().strip()
        if not name:
            self.cat_error_lbl.configure(text="Name required!")
            return
            
        try:
            b = float(self.cat_budget_entry.get() or "0")
        except ValueError:
            self.cat_error_lbl.configure(text="Invalid budget!")
            return
            
        try:
            self.db.add_category(name, self.cat_type_var.get(), "#000000", budget_limit=b)
            self.cat_name_entry.delete(0, 'end')
            self.cat_budget_entry.delete(0, 'end')
            self.cat_error_lbl.configure(text="Added!", text_color="green")
            self.load_categories()
        except Exception as e:
            print(f"Error adding category: {e}")
            self.cat_error_lbl.configure(text="Error adding", text_color="red")
        
    def load_categories(self):
        for widget in self.cat_list_frame.winfo_children():
            widget.destroy()
            
        cats = self.db.get_categories()
        for cat in cats:
            row = ctk.CTkFrame(self.cat_list_frame)
            row.pack(fill="x", pady=2, padx=2)
            
            name_lbl = ctk.CTkLabel(row, text=cat['name'], width=150, anchor="w", font=ctk.CTkFont(family="Noteworthy", size=12))
            name_lbl.pack(side="left", padx=5)
            
            type_lbl = ctk.CTkLabel(row, text=cat['type'], width=80, font=ctk.CTkFont(family="Noteworthy", size=12))
            type_lbl.pack(side="left", padx=5)
            
            b_limit = cat.get('budget_limit', 0.0)
            b_text = f"Budget: {b_limit}" if b_limit else "No Budget"
            budget_lbl = ctk.CTkLabel(row, text=b_text, width=120, font=ctk.CTkFont(family="Noteworthy", size=12))
            budget_lbl.pack(side="left", padx=5)
            
            del_btn = ctk.CTkButton(row, text="Delete", width=60, fg_color="#d62728", hover_color="#ff7f7e", font=ctk.CTkFont(family="Noteworthy", size=10),
                                    command=lambda c_id=cat['id']: self.delete_category(c_id))
            del_btn.pack(side="right", padx=5, pady=5)
            
    def delete_category(self, cat_id):
        self.db.delete_category(cat_id)
        self.load_categories()
