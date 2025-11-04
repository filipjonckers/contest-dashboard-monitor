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
        self.entry_type = ctk.StringVar(value="OVERALL")
        self.contest_var = ctk.StringVar(value="")
        self.stations_var = ctk.StringVar(value="10")
        self.status_var = ctk.StringVar(value="Ready to start monitoring")

        self.stations = StationsList()
        self.contests: List[Contest] = []
        self.categories: List[Category] = []
        self.current_monitor_task: Optional[asyncio.Task] = None
        self.is_monitoring = False

        self.root = root
        self.root.title("Contest Scoreboard Monitor")
        self.root.geometry("900x700")

        ctk.set_appearance_mode("Light")
        ctk.set_default_color_theme("blue")

        self.main_frame = None
        self.line1_frame = None
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
                                                state="readonly", width=240, command=self.on_contest_selected)
        self.contest_dropdown.pack(side="left", padx=5)

        ctk.CTkLabel(frame1, text="Type:").pack(side="left", padx=(5, 0))
        self.entry_select = ctk.CTkComboBox(frame1, variable=self.entry_type, state="readonly", width=200)
        self.entry_select.pack(side="left", padx=5)

        ctk.CTkLabel(frame1, text="Stations:").pack(side="left", padx=(5, 0))
        stations_entry = ctk.CTkEntry(frame1, textvariable=self.stations_var, width=30, validate="key")
        stations_entry.pack(side="left", padx=5)
        stations_entry.configure(validatecommand=(self.root.register(Application.validate_number), '%P'))

        self.start_button = ctk.CTkButton(self.line1_frame, text="START MONITORING", command=self.toggle_monitoring,
                                          fg_color="#2E7D32", hover_color="#1B5E20")
        self.start_button.pack(side="right", padx=20, pady=0)

        status_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        status_frame.pack(fill="x", pady=(0, 3))

        status_label = ctk.CTkLabel(
            status_frame,
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
        self.results_text.tag_configure("header", foreground="#4FC3F7", font=("Consolas", 12, "bold"))
        self.results_text.tag_configure("success", foreground="#4CAF50")
        self.results_text.tag_configure("warning", foreground="#FF9800")
        self.results_text.tag_configure("error", foreground="#f44336")
        self.results_text.tag_configure("highlight", foreground="#FFD54F")
        self.results_text.tag_configure("normal", foreground="#FFFFFF")

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

        try:
            stations_count = int(self.stations_var.get() or "10")
        except ValueError:
            stations_count = 10

        logging.debug("Starting monitoring contest ID %d top %d stations", contest_id, stations_count)
        self.is_monitoring = True
        self.start_button.configure(text="STOP MONITORING", fg_color="#D32F2F", hover_color="#B71C1C")
        self.enable_widgets(False)
        self.status_var.set(f"Monitoring contest {contest_id}...")

        # Start async monitoring task
        asyncio.run_coroutine_threadsafe(self.monitor_contest(contest_id, stations_count), self.loop)

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

        if data and isinstance(data, list):
            self.categories = [
                Category(
                    catid=item.get('catid'),
                    testid=item.get('testid'),
                    ctoper=item.get('ctoper', 0),
                    cttrans=item.get('cttrans', 0),
                    ctpwr=item.get('ctpwr', 0),
                    categoryname=item.get('categoryname', 'Unknown'),
                    wherescores=item.get('wherescores', ''),
                    ct_oper=item.get('ct_oper', ''),
                    ct_trans=item.get('ct_trans', ''),
                    ct_power=item.get('ct_power', '')
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

    async def monitor_contest(self, contest_id: int, stations_count: int):
        """Monitor contest data periodically"""
        self.current_monitor_task = asyncio.current_task()

        url = f"https://contest.run/api/mobilescore/{contest_id}"
        logging.debug("Starting monitoring for contest ID %d at URL: %s", contest_id, url)

        while self.is_monitoring:
            try:
                data = await self.fetch_json(url=url)
                logging.debug("Received data for %d entries.", len(data) if data else 0)
                if data:
                    self.process_contest_data(data, stations_count)
                    self.update_status(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

                # Wait 1 minute before next update
                await asyncio.sleep(60)

            except asyncio.CancelledError:
                logging.error("async cancelled error")
                break
            except Exception as e:
                logging.error("Error during monitoring: %s", str(e))
                self.update_status(f"Monitoring error: {str(e)}")
                await asyncio.sleep(60)

    def process_contest_data(self, data: Dict[str, Any], stations_count: int):
        category = self.get_selected_category()
        logging.debug("Processing contest data for category: %s id: %d", category.categoryname, category.catid)

        for item in data:
            # TODO: check if part of station monitoring list
            pass
            # filter by WAZ zone
            if item.get('waz', "") != self.zone:
                continue
            # add to monitoring stations list
            self.stations.update_from_json_item(item)

        self.root.after(0, self.update_stations_display)

    def update_stations_display(self):
        self.results_text.delete("1.0", "end")
        for station in self.stations.get_stations():
            self.results_text.insert("end", f"{station}\n")

    def update_status(self, message: str, level: str = "info"):
        def update():
            self.status_var.set(message)

        self.root.after(0, update)

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
    app = Application(root)

    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    root.mainloop()


if __name__ == "__main__":
    main()
