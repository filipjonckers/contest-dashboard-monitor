import logging
from datetime import timedelta, datetime, timezone
from tkinter import scrolledtext, END
from typing import List, Optional, Dict, Any

from src.contest_scoreboard_monitor.station_data import StationData


class Station:
    def __init__(self, callsign):
        self.callsign: str = callsign
        self.delta: StationData = StationData({})
        self._data_history: List[StationData] = []
        self.mark: bool = False
        self._max_history: int = 10
        self.range: int = 10

    def update_from_json_item(self, json_item: Dict[str, Any]):
        try:
            new_data = StationData(json_item)
            if new_data and self.newest() and new_data.date == self.newest().date:
                return  # ignore duplicate data
            self._data_history.append(new_data)
            self.drop_old_data()
            self.update_delta()
        except Exception as e:
            logging.error("Error updating station from JSON item: %s", e)

    def newest(self) -> Optional[StationData]:
        if not self._data_history or len(self._data_history) < 1:
            return None
        return self._data_history[-1]

    def oldest(self) -> Optional[StationData]:
        if not self._data_history or len(self._data_history) < 1:
            return None
        return self._data_history[0]

    def data_history(self) -> List[StationData]:
        """Get all StationData instances as a list (oldest to newest)"""
        return self._data_history.copy()

    def drop_old_data(self) -> None:
        # Drop data older than max history time
        threshold = self.newest().date - timedelta(minutes=self._max_history)
        while self._data_history and self._data_history[0].date < threshold:
            self._data_history.pop(0)

    def update_delta(self) -> None:
        last: StationData = self.newest()
        first: StationData = self.oldest()
        # we need at least two data points to calculate a delta
        if not last or not first:
            return

        self.delta.qtotal = last.qtotal - first.qtotal
        self.delta.score = last.score - first.score
        self.delta.ptotal = last.ptotal - first.ptotal
        self.delta.mtotal = last.mtotal - first.mtotal

        self.delta.q10 = last.q10 - first.q10
        self.delta.q15 = last.q15 - first.q15
        self.delta.q20 = last.q20 - first.q20
        self.delta.q40 = last.q40 - first.q40
        self.delta.q80 = last.q80 - first.q80
        self.delta.q160 = last.q160 - first.q160

        self.delta.m10 = last.m10 - first.m10
        self.delta.m15 = last.m15 - first.m15
        self.delta.m20 = last.m20 - first.m20
        self.delta.m40 = last.m40 - first.m40
        self.delta.m80 = last.m80 - first.m80
        self.delta.m160 = last.m160 - first.m160

        # delta.date is difference between last.date and first.date
        # old version # self.delta.date = datetime.min + (last.date - first.date)
        if first.date > datetime.now(timezone.utc):
            self.delta.date = datetime.min  # strange but happens: future date, set delta to zero
        else:
            self.delta.date = datetime.min + (datetime.now(timezone.utc) - first.date)

        # calculate rate per hour
        elapsed_minutes = (last.date - first.date).total_seconds() / 60
        if elapsed_minutes > 0:
            self.delta.rate = int(self.delta.qtotal / elapsed_minutes * 60)

    def add_to_scrolledtext(self, text: scrolledtext.ScrolledText) -> None:
        current: StationData = self.newest()
        data: StationData = self.delta
        if not current or not data:
            return

        text.insert(END, f" {self.callsign:<10} ", "mark" if self.mark else "N", "")
        text.insert(END, f"{current.score:>10,} ")
        text.insert(END, f"{current.qtotal:>6,} ")
        text.insert(END, f"{data.qtotal:<+4d} " if data.qtotal > 0 else f"{'':4} ")
        text.insert(END, f"{data.rate:>4d}  " if data.rate > 0 else f"{'':4}  ")

        text.insert(END, f"{data.q160 if data.q160 > 0 else '0':>3}", "T" if data.q160 > 0 else "N", " ")
        text.insert(END, f"{data.q80 if data.q80 > 0 else '0':>3}", "T" if data.q80 > 0 else "N", " ")
        text.insert(END, f"{data.q40 if data.q40 > 0 else '0':>3}", "T" if data.q40 > 0 else "N", " ")
        text.insert(END, f"{data.q20 if data.q20 > 0 else '0':>3}", "T" if data.q20 > 0 else "N", " ")
        text.insert(END, f"{data.q15 if data.q15 > 0 else '0':>3}", "T" if data.q15 > 0 else "N", " ")
        text.insert(END, f"{data.q10 if data.q10 > 0 else '0':>3}", "T" if data.q10 > 0 else "N", " ")

        text.insert(END, f" | {current.mtotal:>5,} ")
        text.insert(END, f"{data.mtotal:<+4d} " if data.mtotal > 0 else f"{'':4} ")

        text.insert(END, f"{data.m160 if data.m160 > 0 else '0':>3}", "T" if data.m160 > 0 else "N", " ")
        text.insert(END, f"{data.m80 if data.m80 > 0 else '0':>3}", "T" if data.m80 > 0 else "N", " ")
        text.insert(END, f"{data.m40 if data.m40 > 0 else '0':>3}", "T" if data.m40 > 0 else "N", " ")
        text.insert(END, f"{data.m20 if data.m20 > 0 else '0':>3}", "T" if data.m20 > 0 else "N", " ")
        text.insert(END, f"{data.m15 if data.m15 > 0 else '0':>3}", "T" if data.m15 > 0 else "N", " ")
        text.insert(END, f"{data.m10 if data.m10 > 0 else '0':>3}", "T" if data.m10 > 0 else "N", " ")

        text.insert(END, f" {data.date.strftime('%H:%M:%S')}")
        text.insert(END, f" {current.date.strftime('%H:%M')} ")
        text.insert(END, f" ({len(self._data_history)})")
        text.insert(END, "\n")
