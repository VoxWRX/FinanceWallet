import customtkinter as ctk

class SavingsView(ctk.CTkFrame):
    def __init__(self, master, db, **kwargs):
        super().__init__(master, **kwargs)
        self.db = db
        
        self.grid_rowconfigure(0, weight=0) # Header
        self.grid_rowconfigure(1, weight=0) # Add form
        self.grid_rowconfigure(2, weight=1) # Goals list
        self.grid_columnconfigure(0, weight=1)
        
        # --- Header ---
        header = ctk.CTkLabel(self, text="Savings Goals", font=ctk.CTkFont(family="Noteworthy", size=24, weight="bold"))
        header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # --- Add Goal Form ---
        form_frame = ctk.CTkFrame(self)
        form_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        self.name_entry = ctk.CTkEntry(form_frame, placeholder_text="Goal Name", font=ctk.CTkFont(family="Noteworthy", size=14))
        self.name_entry.pack(side="left", padx=10, pady=10)
        
        self.target_entry = ctk.CTkEntry(form_frame, placeholder_text="Target Amount", font=ctk.CTkFont(family="Noteworthy", size=14))
        self.target_entry.pack(side="left", padx=10, pady=10)
        
        self.deadline_entry = ctk.CTkEntry(form_frame, placeholder_text="Deadline (YYYY-MM-DD)", font=ctk.CTkFont(family="Noteworthy", size=14))
        self.deadline_entry.pack(side="left", padx=10, pady=10)
        
        add_btn = ctk.CTkButton(form_frame, text="Add Goal", font=ctk.CTkFont(family="Noteworthy", size=14), command=self.add_goal)
        add_btn.pack(side="left", padx=10, pady=10)
        
        self.goal_error_lbl = ctk.CTkLabel(form_frame, text="", text_color="red", font=ctk.CTkFont(family="Noteworthy", size=12))
        self.goal_error_lbl.pack(side="left", padx=5)
        
        # --- Goals List ---
        self.goals_frame = ctk.CTkScrollableFrame(self)
        self.goals_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        
        self.load_goals()

    def add_goal(self):
        name = self.name_entry.get().strip()
        target = self.target_entry.get().strip()
        deadline = self.deadline_entry.get().strip()
        
        if not name or not target:
            self.goal_error_lbl.configure(text="Name & Target required!", text_color="red")
            return
            
        try:
            target_amt = float(target)
            print(f"Adding goal: {name}, {target_amt}")
            self.db.add_goal(name, target_amt, current_amount=0.0, deadline=deadline)
            
            self.name_entry.delete(0, 'end')
            self.target_entry.delete(0, 'end')
            self.deadline_entry.delete(0, 'end')
            self.goal_error_lbl.configure(text="Goal added!", text_color="green")
            self.load_goals()
        except ValueError:
            self.goal_error_lbl.configure(text="Target must be a number!", text_color="red")
        except Exception as e:
            print(f"Error adding goal: {e}")
            self.goal_error_lbl.configure(text="Error adding goal", text_color="red")

    def load_goals(self):
        for widget in self.goals_frame.winfo_children():
            widget.destroy()
            
        goals = self.db.get_goals()
        currency = self.db.get_setting("currency", "$")
        
        if not goals:
            lbl = ctk.CTkLabel(self.goals_frame, text="No savings goals yet. Create one above!", font=ctk.CTkFont(family="Noteworthy", size=14), text_color="gray")
            lbl.pack(pady=20)
            return
            
        for goal in goals:
            card = ctk.CTkFrame(self.goals_frame)
            card.pack(fill="x", pady=10, padx=10)
            
            # Header
            header_frame = ctk.CTkFrame(card, fg_color="transparent")
            header_frame.pack(fill="x", padx=10, pady=(10, 5))
            
            name_lbl = ctk.CTkLabel(header_frame, text=goal['name'], font=ctk.CTkFont(family="Noteworthy", size=18, weight="bold"))
            name_lbl.pack(side="left")
            
            deadline_str = f"Deadline: {goal['deadline']}" if goal['deadline'] else "No deadline"
            deadline_lbl = ctk.CTkLabel(header_frame, text=deadline_str, font=ctk.CTkFont(family="Noteworthy", size=12), text_color="gray")
            deadline_lbl.pack(side="right")
            
            # Progress Bar
            progress = goal['current_amount'] / goal['target_amount'] if goal['target_amount'] > 0 else 0
            if progress > 1: progress = 1
            
            bar = ctk.CTkProgressBar(card)
            bar.pack(fill="x", padx=10, pady=5)
            bar.set(progress)
            
            # Details & Actions
            details_frame = ctk.CTkFrame(card, fg_color="transparent")
            details_frame.pack(fill="x", padx=10, pady=(5, 10))
            
            status_text = f"{currency}{goal['current_amount']:.2f} / {currency}{goal['target_amount']:.2f} ({(progress*100):.1f}%)"
            status_lbl = ctk.CTkLabel(details_frame, text=status_text, font=ctk.CTkFont(family="Noteworthy", size=14))
            status_lbl.pack(side="left")
            
            del_btn = ctk.CTkButton(details_frame, text="Delete", width=60, fg_color="#d62728", hover_color="#ff7f7e", font=ctk.CTkFont(family="Noteworthy", size=12),
                                    command=lambda g_id=goal['id']: self.delete_goal(g_id))
            del_btn.pack(side="right", padx=5)
            
            add_funds_btn = ctk.CTkButton(details_frame, text="+ Add Funds", width=100, font=ctk.CTkFont(family="Noteworthy", size=12),
                                          command=lambda g_id=goal['id']: self.show_add_funds_modal(g_id))
            add_funds_btn.pack(side="right", padx=5)
            
            history_btn = ctk.CTkButton(details_frame, text="History", width=80, fg_color="gray", hover_color="gray30", font=ctk.CTkFont(family="Noteworthy", size=12),
                                        command=lambda g_id=goal['id'], n=goal['name']: self.show_history_modal(g_id, n))
            history_btn.pack(side="right", padx=5)
            
    def delete_goal(self, goal_id):
        self.db.delete_goal(goal_id)
        self.load_goals()

    def show_history_modal(self, goal_id, goal_name):
        modal = ctk.CTkToplevel(self)
        modal.title(f"History - {goal_name}")
        modal.geometry("400x300")
        modal.grab_set()
        
        lbl = ctk.CTkLabel(modal, text=f"Contribution History", font=ctk.CTkFont(family="Noteworthy", size=18, weight="bold"))
        lbl.pack(pady=10)
        
        scroll = ctk.CTkScrollableFrame(modal)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        history = self.db.get_goal_contributions(goal_id)
        currency = self.db.get_setting("currency", "$")
        
        if not history:
            ctk.CTkLabel(scroll, text="No funds added yet.", font=ctk.CTkFont(family="Noteworthy", size=12), text_color="gray").pack(pady=20)
        else:
            for item in history:
                f = ctk.CTkFrame(scroll)
                f.pack(fill="x", pady=2)
                d_lbl = ctk.CTkLabel(f, text=item['date'], font=ctk.CTkFont(family="Noteworthy", size=10), text_color="gray")
                d_lbl.pack(side="left", padx=5)
                desc_str = item['description'] or "No description"
                c_lbl = ctk.CTkLabel(f, text=desc_str, font=ctk.CTkFont(family="Noteworthy", size=12))
                c_lbl.pack(side="left", padx=5)
                a_lbl = ctk.CTkLabel(f, text=f"+{currency}{item['amount']:.2f}", font=ctk.CTkFont(family="Noteworthy", size=12, weight="bold"), text_color="green")
                a_lbl.pack(side="right", padx=5)
        
    def show_add_funds_modal(self, goal_id):
        modal = ctk.CTkToplevel(self)
        modal.title("Add Funds to Goal")
        modal.geometry("300x300")
        modal.grab_set()
        
        ctk.CTkLabel(modal, text="Amount to Add:", font=ctk.CTkFont(family="Noteworthy", size=14)).pack(pady=(20, 5))
        amt_entry = ctk.CTkEntry(modal, font=ctk.CTkFont(family="Noteworthy", size=14))
        amt_entry.pack(pady=5)
        
        ctk.CTkLabel(modal, text="Description (Optional):", font=ctk.CTkFont(family="Noteworthy", size=14)).pack(pady=(10, 5))
        desc_entry = ctk.CTkEntry(modal, font=ctk.CTkFont(family="Noteworthy", size=14))
        desc_entry.pack(pady=5)
        
        # We auto-capture date, but we can let them override it.
        # Let's keep it simple: just show what date will be used.
        from datetime import datetime
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ctk.CTkLabel(modal, text=f"Date: {now_str}", font=ctk.CTkFont(family="Noteworthy", size=12), text_color="gray").pack(pady=5)
        
        def save():
            try:
                amt = float(amt_entry.get())
                if amt <= 0: return
                desc = desc_entry.get()
                
                self.db.add_goal_contribution(goal_id, amt, now_str, desc)
                
                modal.destroy()
                self.load_goals()
            except ValueError:
                pass
                
        btn = ctk.CTkButton(modal, text="Save", font=ctk.CTkFont(family="Noteworthy", size=14), command=save)
        btn.pack(pady=20)
