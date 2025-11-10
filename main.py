import asyncio
import logging
import threading
from datetime import datetime
from tkinter import scrolledtext
from typing import Dict, List, Optional, Any

import aiohttp
import customtkinter as ctk

from category import Category
from contest import Contest
from find_font import find_font
from inpersonate import inpersonate_browser_headers
from log import setup_logging
from stations_list import StationsList


class Application:
    def __init__(self, root):
        self.zone = 14  # Default WAZ zone filter
        self.update_interval = 60  # seconds
        self.HEADER_TEXT = f" {'station':<10} {'score':>10} {'QSOs':>6}      160  80  40  20  15  10 | {'multi':>5}      160  80  40  20  15  10\n"
        self.entry_type = ctk.StringVar(value="OVERALL")
        self.contest_var = ctk.StringVar(value="")
        self.stations_var = ctk.StringVar(value="10")
        self.zone_var = ctk.StringVar(value="14")
        self.include_var = ctk.StringVar(value="")
        self.status_var = ctk.StringVar(value="Ready to start monitoring")

        self.include_callsigns: List[str] = []
        self.stations = StationsList()
        self.contests: List[Contest] = []
        self.categories: List[Category] = []
        self.current_monitor_task: Optional[asyncio.Task] = None
        self.is_monitoring = False

        self.root = root
        self.root.title("ON4FF Contest Scoreboard Monitor")
        self.root.geometry("1100x700")

        ctk.set_appearance_mode("Light")
        ctk.set_default_color_theme("blue")

        self.main_frame = None
        self.line1_frame = None
        self.line2_frame = None
        self.results_text = None
        self.start_button = None
        self.contest_dropdown = None
        self.entry_select = None
        self.setup_ui()

        self.thread = None
        self.loop = asyncio.new_event_loop()
        self.start_async_tasks()

    def setup_ui(self):
        self.main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=5, pady=3)

        self.line1_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.line1_frame.pack(fill="x", pady=3)

        frame1 = ctk.CTkFrame(self.line1_frame, fg_color="transparent")
        frame1.pack(side="left", fill="x")
        ctk.CTkLabel(frame1, text="Contest:").pack(side="left", padx=0)
        self.contest_dropdown = ctk.CTkComboBox(frame1, variable=self.contest_var,
                                                state="readonly", width=280, command=self.on_contest_selected)
        self.contest_dropdown.pack(side="left", padx=5)

        ctk.CTkLabel(frame1, text="Type:").pack(side="left", padx=(5, 0))
        self.entry_select = ctk.CTkComboBox(frame1, variable=self.entry_type, state="readonly", width=240)
        self.entry_select.pack(side="left", padx=5)

        ctk.CTkLabel(frame1, text="Stations:").pack(side="left", padx=(5, 0))
        stations_entry = ctk.CTkEntry(frame1, textvariable=self.stations_var, width=50, validate="key")
        stations_entry.pack(side="left", padx=5)
        stations_entry.configure(validatecommand=(self.root.register(Application.validate_number), '%P'))

        ctk.CTkLabel(frame1, text="Zone:").pack(side="left", padx=(5, 0))
        zone_entry = ctk.CTkEntry(frame1, textvariable=self.zone_var, width=30, validate="key")
        zone_entry.pack(side="left", padx=5)
        zone_entry.configure(validatecommand=(self.root.register(Application.validate_number), '%P'))

        self.start_button = ctk.CTkButton(self.line1_frame, text="START", command=self.toggle_monitoring,
                                          fg_color="#2E7D32", hover_color="#1B5E20")
        self.start_button.pack(side="right", padx=20, pady=0)

        self.line2_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.line2_frame.pack(fill="x", pady=(0, 3))

        ctk.CTkLabel(self.line2_frame, text="Include:").pack(side="left", padx=(5, 0))
        include_entry = ctk.CTkEntry(self.line2_frame, textvariable=self.include_var, width=500)
        include_entry.pack(side="left", padx=5)
        # include_entry must be in uppercase
        include_entry.bind("<KeyRelease>", lambda event: self.include_var.set(self.include_var.get().upper()))

        status_label = ctk.CTkLabel(
            self.line2_frame,
            textvariable=self.status_var,
            text_color="#4CAF50",
            bg_color="transparent"
        )
        status_label.pack(side="left", padx=5, pady=0)

        # Results frame with text widget
        results_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        results_frame.pack(fill="both", expand=True, pady=0)

        self.results_text = scrolledtext.ScrolledText(
            results_frame,
            width=80,
            height=20,
            font=(find_font(), 16),
            bg="#2b2b2b",
            fg="#ffffff",
            insertbackground="#ffffff",
            selectbackground="#4CAF50",
            relief="flat"
        )
        self.results_text.pack(fill="both", expand=True, padx=2, pady=0)
        # Configure text tags for coloring
        self.results_text.tag_configure("header", foreground="#4fc3f7")
        self.results_text.tag_configure("mark", foreground="#ffce00")
        self.results_text.tag_configure("N", background=self.results_text.cget("background"))
        self.results_text.tag_configure("T", background="#ff4f00")  # aerospace safe orange
        self.results_text.tag_configure("Y", background="#ffce00")
        self.results_text.tag_configure("O", background="#ff8d00")
        self.results_text.tag_configure("R", background="#c70000")
        self.results_text.tag_configure("G", background="#008000")

    @staticmethod
    def validate_number(value):
        if value.isdigit() or value == "":
            return True
        return False

    def on_contest_selected(self, event):
        selected_name = self.contest_var.get()
        logging.debug("Contest selected: %s", selected_name)
        contest = next((c for c in self.contests if f"{c.name} ({c.testid})" == selected_name), None)
        if contest:
            self.status_var.set(f"Selected: {contest.name} (ID: {contest.testid})")
            asyncio.run_coroutine_threadsafe(self.load_categories(contest.testid), self.loop)

    def get_selected_contest_id(self) -> Optional[int]:
        selected_name = self.contest_var.get()
        contest = next((c for c in self.contests if f"{c.name} ({c.testid})" == selected_name), None)
        return contest.testid if contest else None

    def get_selected_category_id(self) -> Optional[int]:
        selected_name = self.entry_type.get()
        category = next((c for c in self.categories if f"{c.categoryname} ({c.catid})" == selected_name), None)
        return category.catid if category else None

    def get_selected_category(self) -> Optional[Category]:
        selected_name = self.entry_type.get()
        category = next((c for c in self.categories if f"{c.categoryname} ({c.catid})" == selected_name), None)
        return category

    def enable_widgets(self, enable: bool):
        state = "normal" if enable else "disabled"
        for widgets in self.line1_frame.winfo_children():
            if widgets != self.start_button:
                for child in widgets.winfo_children():
                    child.configure(state=state)
        for widgets in self.line2_frame.winfo_children():
            # if widget type is label, skip
            if isinstance(widgets, ctk.CTkLabel):
                continue
            for child in widgets.winfo_children():
                child.configure(state=state)

    def toggle_monitoring(self):
        if not self.is_monitoring:
            self.start_monitoring()
        else:
            self.stop_monitoring()

    def start_monitoring(self):
        contest_id = self.get_selected_contest_id()
        if not contest_id:
            self.status_var.set("Error: Please select a contest first")
            return

        logging.debug("Starting monitoring contest ID %d top %s stations", contest_id, self.stations_var.get() or "10")
        self.is_monitoring = True
        self.start_button.configure(text="STOP", fg_color="#D32F2F", hover_color="#B71C1C")
        self.enable_widgets(False)
        self.status_var.set(f"Monitoring contest {contest_id}...")

        # Start async monitoring task
        self.stations.clear()
        asyncio.run_coroutine_threadsafe(self.monitor_contest(contest_id), self.loop)

    def stop_monitoring(self):
        logging.debug("Stopping monitoring")
        self.is_monitoring = False
        self.start_button.configure(text="START MONITORING", fg_color="#2E7D32", hover_color="#1B5E20")
        self.enable_widgets(True)
        self.status_var.set("Monitoring stopped")

        if self.current_monitor_task:
            self.current_monitor_task.cancel()

    async def fetch_json(self, url: str) -> Optional[Dict[str, Any]]:
        logging.debug("Fetching JSON data from URL: %s", url)
        try:
            connector = aiohttp.TCPConnector(ssl=False)
            headers = inpersonate_browser_headers()

            async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
                async with session.get(url, timeout=30) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            self.update_status(f"API Error: {str(e)}")
            return None

    async def load_contests(self):
        # alternative: fetch previous and current month: https://contest.run/api/contest/month/10
        data = await self.fetch_json("https://contest.run/api/contest/nearest")
        logging.debug("Received data for %d contests.", len(data) if data else 0)

        if data and isinstance(data, list):
            self.contests = [
                Contest(
                    testid=item.get('testid'),
                    name=item.get('name', 'Unknown'),
                    startdate=item.get('startdate', ''),
                    enddate=item.get('enddate', '')
                )
                for item in data
                if item.get('testid')
            ]

            if logging.getLogger().isEnabledFor(logging.DEBUG):
                for contest in self.contests:
                    logging.debug("Loaded contest: %s", contest)

            contest_names = [f"{c.name} ({c.testid})" for c in self.contests]
            self.root.after(0, lambda: self.contest_dropdown.configure(values=contest_names))

            if contest_names:
                self.root.after(0, lambda: self.contest_dropdown.set(contest_names[0]))
                first_contest_testid = self.contests[0].testid
                asyncio.run_coroutine_threadsafe(self.load_categories(first_contest_testid), self.loop)
                self.update_status(f"Loaded {len(contest_names)} contests")

    async def load_categories(self, contest_id: int):
        data = await self.fetch_json(f"https://contest.run/api/category/contest/{contest_id}")
        logging.debug("Received data for %d categories.", len(data) if data else 0)

        overall_category: Category = Category(
            catid=0,
            ct_oper="OVERALL",
            categoryname="OVERALL")

        if data and isinstance(data, list):
            self.categories = [overall_category] + [
                Category(
                    catid=item.get('catid'),
                    testid=item.get('testid'),
                    ctoper=item.get('ctoper', -1),
                    ctwac=item.get('ctwac', -1),
                    cttrans=item.get('cttrans', -1),
                    ctband=item.get('ctband', -1),
                    ctpwr=item.get('ctpwr', -1),
                    ctmode=item.get('ctmode', -1),
                    ctassis=item.get('ctassis', -1),
                    ctstatn=item.get('ctstatn', -1),
                    cttime=item.get('cttime', -1),
                    ctoverl=item.get('ctoverl', -1),
                    categoryname=item.get('categoryname', 'Unknown'),
                    wherescores=item.get('wherescores', ''),
                    ct_oper=item.get('ct-oper', ''),
                    ct_band=item.get('ct-band', ''),
                    ct_mode=item.get('ct-mode', ''),
                    ct_assis=item.get('ct-assis', ''),
                    ct_trans=item.get('ct-trans', ''),
                    ct_power=item.get('ct-power', ''),
                    ct_statn=item.get('ct-statn', ''),
                    ct_overl=item.get('ct-overl', ''),
                    ct_time=item.get('ct-time', ''),
                )
                for item in data
                if item.get('catid')
            ]
            for category in self.categories:
                logging.debug("Loaded category: %s", category)

            category_names = [f"{c.categoryname} ({c.catid})" for c in self.categories]
            self.root.after(0, lambda: self.entry_select.configure(values=category_names))

            if category_names:
                self.root.after(0, lambda: self.entry_select.set(category_names[0]))
                self.update_status(f"Loaded {len(category_names)} categories")

    async def monitor_contest(self, contest_id: int):
        """Monitor contest data periodically"""
        self.current_monitor_task = asyncio.current_task()

        url = f"https://contest.run/api/displayscore/{contest_id}"
        logging.debug("Starting monitoring for contest ID %d at URL: %s", contest_id, url)

        # self.include_var to list of callsigns
        self.include_callsigns = [cs.strip().upper() for cs in self.include_var.get().split(" ") if cs.strip()]
        logging.debug("Include callsigns: %s", self.include_callsigns)

        while self.is_monitoring:
            try:
                data = await self.fetch_json(url=url)
                logging.debug("Received data for %d entries.", len(data) if data else 0)
                if data:
                    self.process_contest_data(data)
                    self.update_status(f"Last updated: {datetime.now().strftime('%H:%M:%S')} ({len(data)})")

                await asyncio.sleep(self.update_interval)

            except asyncio.CancelledError:
                logging.error("async cancelled error")
                break

    def process_contest_data(self, data: Dict[str, Any]):
        category = self.get_selected_category()
        logging.debug("Processing: %s id=%d stations:%d", category.categoryname, category.catid, len(data))

        zone: int = int(self.zone_var.get() or "0")
        counter: int = 0

        for item in data:
            # check is sign is in include list
            if self.include_callsigns and item.get('sign', '').upper() in self.include_callsigns:
                self.stations.update_from_json_item(item, mark=True)
                continue

            # do we need to filter out this item?
            if not self.part_of_category(item, category, zone):
                continue
            # add to monitoring stations list
            self.stations.update_from_json_item(item)
            # do we have enough stations to monitor?
            counter += 1
            if counter >= int(self.stations_var.get() or "10"):
                break

        self.root.after(0, self.update_stations_display)

    @staticmethod
    def part_of_category(item: Dict[str, Any], category: Category, zone: int) -> bool:
        if not category or not item:
            return False

        try:
            if zone > 0 and zone != item.get('waz', 0):
                return False
            if 0 <= category.ctoper != item.get('ctoper', -1):
                return False
            if 0 <= category.ctpwr != item.get('ctpwr', -1):
                return False
            if 0 <= category.ctassis != item.get('ctassis', -1):
                return False
            if 0 <= category.cttrans != item.get('cttrans', -1):
                return False
            if 0 <= category.ctband != item.get('ctband', -1):
                return False
            if 0 <= category.ctmode != item.get('ctmode', -1):
                return False
            if 0 <= category.ctstatn != item.get('ctstatn', -1):
                return False
            if 0 <= category.cttime != item.get('cttime', -1):
                return False
            if 0 <= category.ctoverl != item.get('ctoverl', -1):
                return False
        except Exception as e:
            logging.error("Error checking category filters: %s", str(e))
            return False
        return True

    def update_stations_display(self):
        self.results_text.delete("1.0", "end")
        self.results_text.insert("1.0", self.HEADER_TEXT, "header")
        for station in self.stations.get_stations():
            station.add_to_scrolledtext(self.results_text)

    def update_status(self, message: str):
        self.root.after(0, lambda: self.status_var.set(message))

    def start_async_tasks(self):
        """Start the async event loop in a separate thread"""

        def run_loop():
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()

        self.thread = threading.Thread(target=run_loop, daemon=True)
        self.thread.start()

        # Start loading contests
        asyncio.run_coroutine_threadsafe(self.load_contests(), self.loop)

    def on_closing(self):
        """Cleanup when closing the application"""
        logging.debug("Closing application")
        self.is_monitoring = False
        if self.current_monitor_task:
            self.current_monitor_task.cancel()
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.root.destroy()


def main():
    setup_logging(logging.DEBUG)

    root = ctk.CTk()
    root.focus_force()
    app = Application(root)

    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    root.mainloop()


if __name__ == "__main__":
    main()
