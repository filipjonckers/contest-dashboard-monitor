import asyncio
import logging
import threading
from datetime import datetime
from tkinter import scrolledtext
from typing import Dict, List, Optional, Any

import aiohttp
import customtkinter as ctk

from contest import Contest
from entry_type import ENTRY_TYPES
from log import setup_logging


class Application:
    def __init__(self, root):
        self.entry_type = ctk.StringVar(value="OVERALL")
        self.contest_var = ctk.StringVar(value="")
        self.stations_var = ctk.StringVar(value="10")
        self.status_var = ctk.StringVar(value="Ready to start monitoring")

        self.contests: List[Contest] = []
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
        self.contest_dropdown = ctk.CTkComboBox(frame1, variable=self.contest_var, state="readonly", width=240)
        self.contest_dropdown.pack(side="left", padx=5)
        self.contest_dropdown.bind('<<ComboboxSelected>>', self.on_contest_selected)

        ctk.CTkLabel(frame1, text="Type:").pack(side="left", padx=(5, 0))
        entry_select = ctk.CTkComboBox(frame1, values=ENTRY_TYPES, variable=self.entry_type,
                                       state="readonly", width=200)
        entry_select.pack(side="left", padx=5)

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
            font=("Consolas", 12),
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
        contest = next((c for c in self.contests if f"{c.name} ({c.testid})" == selected_name), None)
        if contest:
            self.status_var.set(f"Selected: {contest.name} (ID: {contest.testid})")

    def get_selected_contest_id(self) -> Optional[int]:
        selected_name = self.contest_var.get()
        contest = next((c for c in self.contests if f"{c.name} ({c.testid})" == selected_name), None)
        return contest.testid if contest else None

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

        self.is_monitoring = True
        self.start_button.configure(
            text="STOP MONITORING",
            fg_color="#D32F2F",
            hover_color="#B71C1C"
        )
        self.status_var.set(f"Monitoring contest {contest_id}...")

        # Start async monitoring task
        asyncio.run_coroutine_threadsafe(
            self.monitor_contest(contest_id, stations_count),
            self.loop
        )

    def stop_monitoring(self):
        self.is_monitoring = False
        self.start_button.configure(
            text="START MONITORING",
            fg_color="#2E7D32",
            hover_color="#1B5E20"
        )
        self.status_var.set("Monitoring stopped")

        if self.current_monitor_task:
            self.current_monitor_task.cancel()

    async def fetch_json(self, url: str) -> Optional[Dict[str, Any]]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            self.update_status(f"API Error: {str(e)}")
            return None

    async def load_contests(self):
        data = await self.fetch_json("https://contest.run/api/contest/nearest")
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
            for contest in self.contests:
                logging.debug("Loaded contest: %s", contest)

            contest_names = [f"{c.name} ({c.testid})" for c in self.contests]
            self.root.after(0, lambda: self.contest_dropdown.configure(values=contest_names))

            if contest_names:
                self.root.after(0, lambda: self.contest_dropdown.set(contest_names[0]))
                self.update_status(f"Loaded {len(contest_names)} contests")

    async def monitor_contest(self, contest_id: int, stations_count: int):
        """Monitor contest data periodically"""
        self.current_monitor_task = asyncio.current_task()

        while self.is_monitoring:
            try:
                data = await self.fetch_json(f"https://contest.run/api/mobilescore/{contest_id}")
                if data:
                    self.display_contest_data(data, stations_count)
                    self.update_status(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

                # Wait 1 minute before next update
                await asyncio.sleep(60)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.update_status(f"Monitoring error: {str(e)}")
                await asyncio.sleep(60)

    def display_contest_data(self, data: Dict[str, Any], stations_count: int):
        """Display contest data in the text widget with coloring"""

        def update_display():
            self.results_text.delete("1.0", "end")

            # Display basic contest info
            self.results_text.insert("end", "CONTEST RESULTS\n", "header")
            self.results_text.insert("end", f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n", "normal")

            # Display entry type and stations count
            self.results_text.insert("end", f"Entry Type: {self.entry_type.get()}\n", "normal")
            self.results_text.insert("end", f"Showing top {stations_count} stations\n\n", "normal")

            # Display stations/scores data
            if 'scores' in data and isinstance(data['scores'], list):
                scores = data['scores'][:stations_count]

                self.results_text.insert("end", f"Top {len(scores)} Stations:\n", "header")
                self.results_text.insert("end", "-" * 60 + "\n", "normal")

                for i, station in enumerate(scores, 1):
                    callsign = station.get('callsign', 'N/A')
                    score = station.get('score', 0)
                    multipliers = station.get('multipliers', 0)
                    qsos = station.get('qsos', 0)

                    # Use different colors based on rank
                    if i == 1:
                        tag = "success"
                    elif i <= 3:
                        tag = "highlight"
                    else:
                        tag = "normal"

                    self.results_text.insert("end", f"{i:2d}. {callsign:<12} ", tag)
                    self.results_text.insert("end", f"Score: {score:>10,} ", tag)
                    self.results_text.insert("end", f"Mult: {multipliers:>3} ", tag)
                    self.results_text.insert("end", f"QSOs: {qsos:>4}\n", tag)

            else:
                self.results_text.insert("end", "No score data available\n", "warning")

            # Add contest summary information if available
            if 'contest' in data and data['contest']:
                contest_info = data['contest']
                self.results_text.insert("end", f"\nContest: {contest_info.get('name', 'N/A')}\n", "header")
                self.results_text.insert("end", f"Start: {contest_info.get('startdate', 'N/A')} ", "normal")
                self.results_text.insert("end", f"End: {contest_info.get('enddate', 'N/A')}\n", "normal")

            self.results_text.see("1.0")  # Scroll to top

        # Schedule the display update on the main thread
        self.root.after(0, update_display)

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
        self.is_monitoring = False
        if self.current_monitor_task:
            self.current_monitor_task.cancel()
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.root.destroy()


def main():
    setup_logging()

    root = ctk.CTk()
    app = Application(root)

    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    root.mainloop()


if __name__ == "__main__":
    main()
