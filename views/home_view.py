import customtkinter as ctk
from components.calendar_widget import CalendarWidget

class HomeView(ctk.CTkFrame):
    def __init__(self, master, db, **kwargs):
        super().__init__(master, **kwargs)
        self.db = db
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Container to hold either Calendar or Day View
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        
        self.show_calendar()

    def show_calendar(self):
        for widget in self.container.winfo_children():
            widget.destroy()
            
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_rowconfigure(1, weight=0)
            
        self.calendar = CalendarWidget(self.container, self.db, self.on_day_click)
        self.calendar.grid(row=0, column=0, sticky="nsew")

    def on_day_click(self, selected_date):
        # Switch to Day View
        for widget in self.container.winfo_children():
            widget.destroy()
            
        self.container.grid_rowconfigure(0, weight=0)
        self.container.grid_rowconfigure(1, weight=1)
            
        # Top bar with Back button
        top_bar = ctk.CTkFrame(self.container, fg_color="transparent", height=40)
        top_bar.grid(column=0, row=0, sticky="ew")
        top_bar.grid_columnconfigure(1, weight=1)
        
        back_btn = ctk.CTkButton(top_bar, text="< Back to Calendar", width=120, font=ctk.CTkFont(family="Noteworthy", size=14), command=self.show_calendar)
        back_btn.grid(row=0, column=0, padx=(10, 5), pady=15, sticky="w")
        
        date_str = selected_date.strftime("%B %d, %Y")
        lbl = ctk.CTkLabel(top_bar, text=f"Transactions for {date_str}", font=ctk.CTkFont(family="Noteworthy", size=20, weight="bold"))
        lbl.grid(row=0, column=1, padx=5, pady=15)
        
        add_btn = ctk.CTkButton(top_bar, text="+ Add Transaction", width=120, font=ctk.CTkFont(family="Noteworthy", size=14), command=lambda: self.show_add_transaction_modal(selected_date))
        add_btn.grid(row=0, column=2, padx=(5, 10), pady=15, sticky="e")
        
        # Transactions List
        self.tx_list_frame = ctk.CTkScrollableFrame(self.container)
        self.tx_list_frame.grid(column=0, row=1, sticky="nsew")

        self.load_transactions_for_day(selected_date)
        
    def load_transactions_for_day(self, date_obj):
        for widget in self.tx_list_frame.winfo_children():
            widget.destroy()
            
        date_str = date_obj.strftime("%Y-%m-%d")
        txs = self.db.get_transactions(start_date=date_str, end_date=date_str)
        
        if not txs:
            lbl = ctk.CTkLabel(self.tx_list_frame, text="No transactions for this day.", font=ctk.CTkFont(family="Noteworthy", size=14), text_color="gray")
            lbl.grid(row=0, column=0, padx=20, pady=20)
            return
            
        currency = self.db.get_setting("currency", "$")
            
        row = 1
        for tx in txs:
            frame = ctk.CTkFrame(self.tx_list_frame)
            frame.grid(row=row, column=0, sticky="ew", padx=5, pady=(5, 0))
            
            amount_lbl = ctk.CTkLabel(frame, text=f"{currency}{tx['amount']:.2f}", font=ctk.CTkFont(family="Noteworthy", size=16, weight="bold"))
            amount_lbl.grid(row=0, column=0, padx=10, pady=(10, 5))
            
            desc = tx['description'] or "No Description"
            tx_name = tx.get('name', 'Transaction')
            desc_lbl = ctk.CTkLabel(frame, text=f"{tx_name} - {desc}", font=ctk.CTkFont(family="Noteworthy", size=14))
            desc_lbl.grid(row=0, column=1, padx=10, pady=(5, 10))
            
            row += 1
            
            # Here we can add edit/delete buttons later


    def show_add_transaction_modal(self, date_obj):
        modal = ctk.CTkToplevel(self)
        modal.title(f"Add Transaction - {date_obj.strftime('%Y-%m-%d')}")
        modal.geometry("450x550")
        modal.grab_set() 
        # Name
        ctk.CTkLabel(modal, text="Name:", font=ctk.CTkFont(family="Noteworthy", size=14)).grid(row=0, column=0, sticky="w", pady=(20, 5))
        name_entry = ctk.CTkEntry(modal, width=250, font=ctk.CTkFont(family="Noteworthy", size=14))
        name_entry.grid(row=0, column=1, padx=10, pady=(5, 5), sticky="ew")

        # Type (Income / Expense)
        ctk.CTkLabel(modal, text="Type:", font=ctk.CTkFont(family="Noteworthy", size=14)).grid(row=1, column=0, sticky="w", pady=(10, 5))
        type_var = ctk.StringVar(value="Expense")
        
        # Category Dropdown
        ctk.CTkLabel(modal, text="Category:", font=ctk.CTkFont(family="Noteworthy", size=14)).grid(row=2, sticky="w", pady=(10, 5))
        cat_var = ctk.StringVar()
        cat_dropdown = ctk.CTkOptionMenu(modal, variable=cat_var, width=250, font=ctk.CTkFont(family="Noteworthy", size=14))
        cat_dropdown.grid(row=2, column=1, padx=10, pady=(10, 5), sticky="ew")
        
        categories_data = self.db.get_categories()
        
        def update_categories(*args):
            selected_type = type_var.get()
            options = [c['name'] for c in categories_data if c['type'] == selected_type]
            if not options:
                options = ["No Categories"]
            cat_dropdown.configure(values=options)
            cat_var.set(options[0])
            
        type_segmented = ctk.CTkSegmentedButton(modal, values=["Expense", "Income"], variable=type_var, font=ctk.CTkFont(family="Noteworthy", size=14), command=update_categories)
        type_segmented.grid(row=1, column=1, padx=10, pady=(5, 10), sticky="ew")
        
        # Initial population of categories
        update_categories()
        
        # Amount
        currency = self.db.get_setting("currency", "$")
        ctk.CTkLabel(modal, text=f"Amount ({currency}):", font=ctk.CTkFont(family="Noteworthy", size=14)).grid(row=3, column=0, sticky="w", pady=(10, 5))
        amount_entry = ctk.CTkEntry(modal, width=250, font=ctk.CTkFont(family="Noteworthy", size=14))
        amount_entry.grid(row=3, column=1, padx=10, pady=(5, 5), sticky="ew")
        
        # Notes
        ctk.CTkLabel(modal, text="Notes (Optional):", font=ctk.CTkFont(family="Noteworthy", size=14)).grid(row=4, column=0, sticky="w", pady=(10, 5))
        notes_entry = ctk.CTkEntry(modal, width=250, font=ctk.CTkFont(family="Noteworthy", size=14))
        notes_entry.grid(row=4, column=1, padx=10, pady=(5, 5), sticky="ew")
        
        # Tags
        ctk.CTkLabel(modal, text="Tags (comma separated):", font=ctk.CTkFont(family="Noteworthy", size=14)).grid(row=5, column=0, sticky="w", pady=(10, 5))
        tags_entry = ctk.CTkEntry(modal, width=250, placeholder_text="e.g. vacation, gift", font=ctk.CTkFont(family="Noteworthy", size=14))
        tags_entry.grid(row=5, column=1, padx=10, pady=(5, 5), sticky="ew")
        
        def save():
            try:
                amt = float(amount_entry.get())
                name = name_entry.get() or "Transaction"
                notes = notes_entry.get()
                tags_val = tags_entry.get()
                cat_name = cat_var.get()
                
                # Find category ID
                cat_id = None
                for c in categories_data:
                    if c['name'] == cat_name and c['type'] == type_var.get():
                        cat_id = c['id']
                        break
                        
                if not cat_id:
                    # Create default if none exists for this type
                    cat_id = self.db.add_category(cat_name if cat_name != "No Categories" else "General", type_var.get(), "#000000")
                
                self.db.add_transaction(name, amt, date_obj.strftime("%Y-%m-%d"), notes, category_id=cat_id, transaction_author="User", tags=tags_val)
                modal.destroy()
                self.load_transactions_for_day(date_obj)
            except ValueError:
                pass # Simple error handling for now
                
        save_btn = ctk.CTkButton(modal, text="Save Transaction", font=ctk.CTkFont(family="Noteworthy", size=14), command=save)
        save_btn.grid(row=6, column=0, columnspan=2, pady=(20, 5))
