import customtkinter as ctk
import calendar
from datetime import datetime, date

class CalendarWidget(ctk.CTkFrame):
    def __init__(self, master, db, on_day_click, **kwargs):
        super().__init__(master, **kwargs)
        self.db = db
        self.on_day_click = on_day_click
        
        today = datetime.today()
        self.current_month = today.month
        self.current_year = today.year

        # --- Header ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(0, 10))
        
        self.prev_button = ctk.CTkButton(self.header_frame, text="<", width=40, command=self.prev_month)
        self.prev_button.pack(side="left", padx=10)
        
        self.month_label = ctk.CTkLabel(self.header_frame, text="", font=ctk.CTkFont(family="Noteworthy", size=20, weight="bold"))
        self.month_label.pack(side="left", expand=True)
        
        self.next_button = ctk.CTkButton(self.header_frame, text=">", width=40, command=self.next_month)
        self.next_button.pack(side="right", padx=10)

        # --- Grid ---
        self.grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.grid_frame.pack(fill="both", expand=True)
        
        for i in range(7):
            self.grid_frame.grid_columnconfigure(i, weight=1, uniform="col")
            
        # Days of week header
        days = ["SUNDAY", "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY"]
        for i, day in enumerate(days):
            lbl = ctk.CTkLabel(self.grid_frame, text=day, font=ctk.CTkFont(family="Noteworthy", size=10, weight="bold"), text_color="gray50")
            lbl.grid(row=0, column=i, pady=5)

        self.cells = []
        
        self.render_calendar()

    def prev_month(self):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.render_calendar()

    def next_month(self):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.render_calendar()

    def render_calendar(self):
        # Update header
        month_name = calendar.month_name[self.current_month].upper()
        self.month_label.configure(text=f"{month_name} {self.current_year}")
        
        # Clear old cells
        for cell in self.cells:
            cell.destroy()
        self.cells.clear()

        # Generate calendar data
        cal = calendar.Calendar(firstweekday=6) # Sunday is 6
        month_days = cal.monthdatescalendar(self.current_year, self.current_month)
        
        # Fetch transactions for the month
        start_date = f"{self.current_year}-{self.current_month:02d}-01"
        last_day = calendar.monthrange(self.current_year, self.current_month)[1]
        end_date = f"{self.current_year}-{self.current_month:02d}-{last_day}"
        
        transactions = self.db.get_transactions(start_date, end_date)
        tx_by_date = {}
        for tx in transactions:
            dt = tx['date'].split('T')[0] if 'T' in tx['date'] else tx['date']
            if dt not in tx_by_date:
                tx_by_date[dt] = []
            tx_by_date[dt].append(tx)

        # Render grid (Google Calendar style: thin borders, number top left)
        for row_idx, week in enumerate(month_days, start=1):
            self.grid_frame.grid_rowconfigure(row_idx, weight=1, uniform="row")
            for col_idx, day_date in enumerate(week):
                # Determine colors
                is_current_month = (day_date.month == self.current_month)
                bg_color = "white" if ctk.get_appearance_mode() == "Light" else "gray15"
                if not is_current_month:
                    bg_color = "gray95" if ctk.get_appearance_mode() == "Light" else "gray10"
                
                # Cell frame
                cell_frame = ctk.CTkFrame(self.grid_frame, fg_color=bg_color, corner_radius=0, border_width=1, border_color="gray80" if ctk.get_appearance_mode() == "Light" else "gray30")
                cell_frame.grid(row=row_idx, column=col_idx, sticky="nsew", padx=0, pady=0)
                self.cells.append(cell_frame)
                
                # Bind click event to the frame and all its children
                def on_click(event, d=day_date):
                    self.on_day_click(d)
                
                cell_frame.bind("<Button-1>", on_click)
                
                # Day Number (Top Left)
                day_lbl = ctk.CTkLabel(cell_frame, text=str(day_date.day), font=ctk.CTkFont(family="Noteworthy", size=11), text_color="black" if ctk.get_appearance_mode()=="Light" else "white")
                if not is_current_month:
                    day_lbl.configure(text_color="gray60")
                day_lbl.pack(anchor="nw", padx=5, pady=2)
                day_lbl.bind("<Button-1>", on_click)
                
                # Transactions
                date_str = day_date.strftime("%Y-%m-%d")
                day_txs = tx_by_date.get(date_str, [])
                
                currency = self.db.get_setting("currency", "$") if hasattr(self, 'db') else "$"
                
                for i, tx in enumerate(day_txs):
                    if i >= 3: # Limit to 3 items in cell
                        more_lbl = ctk.CTkLabel(cell_frame, text=f"+{len(day_txs) - 3} more", text_color="gray", font=ctk.CTkFont(family="Noteworthy", size=10))
                        more_lbl.pack(anchor="w", padx=5)
                        more_lbl.bind("<Button-1>", on_click)
                        break
                    
                    amount_str = f"{currency}{tx['amount']:.0f}"
                    tx_name = tx.get('name', 'Tx')
                    tx_lbl = ctk.CTkLabel(cell_frame, text=f"• {tx_name} ({amount_str})", anchor="w", font=ctk.CTkFont(family="Noteworthy", size=10))
                    tx_lbl.pack(fill="x", padx=5, pady=0)
                    tx_lbl.bind("<Button-1>", on_click)
