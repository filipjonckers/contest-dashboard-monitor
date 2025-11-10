import tkinter as tk
from tkinter import scrolledtext
from typing import List, Optional

from station_data import StationData


class Station:
    def __init__(self, callsign):
        self.callsign: str = callsign
        self.delta: Optional[StationData] = None
        self.range_total: Optional[StationData] = None
        self._data_history: List[StationData] = []
        self._delta_history: List[StationData] = []
        self._max_history: int = 10
        self.range: int = 10

    def __str__(self) -> str:
        current: StationData = self.current()
        return f"{self.callsign:<10} {current.score:>10,} - {current.qtotal:>6,} QSOs {current.ptotal:>7,} pts {current.mtotal:>5,} multi --> history: {len(self._data_history)}"

    def update_from_json_item(self, json_item: dict):
        new_data = StationData(json_item)
        self._data_history.append(new_data)

        while len(self._data_history) > self._max_history:
            self._data_history.pop(0)

        self.update_delta()
        self.update_range_total()

    def current(self) -> Optional[StationData]:
        if not self._data_history or len(self._data_history) < 1:
            return None
        return self._data_history[-1]

    def previous(self) -> Optional[StationData]:
        if not self._data_history or len(self._data_history) < 2:
            return None
        return self._data_history[-2]

    def data_history(self) -> List[StationData]:
        """Get all StationData instances as a list (oldest to newest)"""
        return self._data_history.copy()

    def update_delta(self) -> None:
        current: StationData = self.current()
        previous: StationData = self.previous()
        if not current or not previous:
            return

        # need new instance to put on stack
        self.delta: StationData = StationData()

        self.delta.qtotal = current.qtotal - previous.qtotal
        self.delta.score = current.score - previous.score
        self.delta.ptotal = current.ptotal - previous.ptotal
        self.delta.mtotal = current.mtotal - previous.mtotal

        self.delta.q10 = current.q10 - previous.q10
        self.delta.q15 = current.q15 - previous.q15
        self.delta.q20 = current.q20 - previous.q20
        self.delta.q40 = current.q40 - previous.q40
        self.delta.q80 = current.q80 - previous.q80
        self.delta.q160 = current.q160 - previous.q160

        self.delta.m10 = current.m10 - previous.m10
        self.delta.m15 = current.m15 - previous.m15
        self.delta.m20 = current.m20 - previous.m20
        self.delta.m40 = current.m40 - previous.m40
        self.delta.m80 = current.m80 - previous.m80
        self.delta.m160 = current.m160 - previous.m160

        self._delta_history.append(self.delta)

        while len(self._delta_history) > self._max_history:
            self._delta_history.pop(0)

        # if self.delta.score > 0:
            # go over every element in data_history for debug, also show number of element
            # print("---------------------------")
            # for nr, item in enumerate(self._data_history):
            #     print(f"DATA_HISTORY[{nr}]: {item}")
            # print("----")
            # for nr, item in enumerate(self._delta_history):
            #     print(f"DELTA_HISTORY[{nr}]: {item}")
            # print("----")
            # print(f"CURRENT :{current}")
            # print("----")
            # print(f"PREVIOUS:{previous}")
            # print("----")
            # print(f"DELTA:{self.delta}")
            # print("---------------------------")

    def update_range_total(self) -> None:
        # reset range_total
        self.range_total: StationData = StationData()

        start_index = max(0, len(self._delta_history) - self.range)
        end_index = len(self._delta_history)
        deltas_to_sum = self._delta_history[start_index:end_index]
        for delta in deltas_to_sum:
            self.range_total.qtotal += delta.qtotal
            self.range_total.score += delta.score
            self.range_total.ptotal += delta.ptotal
            self.range_total.mtotal += delta.mtotal

            self.range_total.q10 += delta.q10
            self.range_total.q15 += delta.q15
            self.range_total.q20 += delta.q20
            self.range_total.q40 += delta.q40
            self.range_total.q80 += delta.q80
            self.range_total.q160 += delta.q160

            self.range_total.m10 += delta.m10
            self.range_total.m15 += delta.m15
            self.range_total.m20 += delta.m20
            self.range_total.m40 += delta.m40
            self.range_total.m80 += delta.m80
            self.range_total.m160 += delta.m160

    def add_to_scrolledtext(self, text_widget: scrolledtext.ScrolledText) -> None:
        current: StationData = self.current()
        data: StationData = self.range_total
        if not current or not data:
            return

        text_widget.insert(tk.END, f"{self.callsign:<10} ", "N")
        text_widget.insert(tk.END, f"{current.score:>10,} ", "N")
        text_widget.insert(tk.END, f"{current.qtotal:>6,} ", "N")
        text_widget.insert(tk.END, f"{data.qtotal:<+4d} " if data.qtotal > 0 else f"{'':4} ", "N")

        text_widget.insert(tk.END, f"{data.q160 if data.q160 > 0 else '0':>3}", "X" if data.q160 > 0 else "N")
        text_widget.insert(tk.END, f" {data.q80 if data.q80 > 0 else '0':>3}", "X" if data.q80 > 0 else "N")
        text_widget.insert(tk.END, f" {data.q40 if data.q40 > 0 else '0':>3}", "X" if data.q40 > 0 else "N")
        text_widget.insert(tk.END, f" {data.q20 if data.q20 > 0 else '0':>3}", "X" if data.q20 > 0 else "N")
        text_widget.insert(tk.END, f" {data.q15 if data.q15 > 0 else '0':>3}", "X" if data.q15 > 0 else "N")
        text_widget.insert(tk.END, f" {data.q10 if data.q10 > 0 else '0':>3}", "X" if data.q10 > 0 else "N")

        text_widget.insert(tk.END, f" | {current.mtotal:>5,} ", "N")
        text_widget.insert(tk.END, f"{data.mtotal:<+4d} " if data.mtotal > 0 else f"{'':4} ", "N")

        text_widget.insert(tk.END, f" {data.m160 if data.m160 > 0 else '0':>3}", "X" if data.m160 > 0 else "N")
        text_widget.insert(tk.END, f" {data.m80 if data.m80 > 0 else '0':>3}", "X" if data.m80 > 0 else "N")
        text_widget.insert(tk.END, f" {data.m40 if data.m40 > 0 else '0':>3}", "X" if data.m40 > 0 else "N")
        text_widget.insert(tk.END, f" {data.m20 if data.m20 > 0 else '0':>3}", "X" if data.m20 > 0 else "N")
        text_widget.insert(tk.END, f" {data.m15 if data.m15 > 0 else '0':>3}", "X" if data.m15 > 0 else "N")
        text_widget.insert(tk.END, f" {data.m10 if data.m10 > 0 else '0':>3}", "X" if data.m10 > 0 else "N")

        text_widget.insert(tk.END, f" ({len(self._data_history)})")
        text_widget.insert(tk.END, "\n")

    def add_to_scrolledtext_old(self, text_widget: scrolledtext.ScrolledText) -> None:
        current: StationData = self.current()
        delta: StationData = self.delta
        if not current or not delta:
            return

        text_widget.insert(tk.END, f"{self.callsign:<10} ", "N")
        text_widget.insert(tk.END, f"{current.score:>10,} ", "N")
        text_widget.insert(tk.END, f"{current.qtotal:>6,} ", "N")
        text_widget.insert(tk.END, f"{delta.qtotal:<+3d}" if delta.qtotal > 0 else f"{'':3}", "N")

        text_widget.insert(tk.END, f"{delta.q160 if delta.q160 > 0 else '0':>3}", "X" if delta.q160 > 0 else "N")
        text_widget.insert(tk.END, f" {delta.q80 if delta.q80 > 0 else '0':>3}", "X" if delta.q80 > 0 else "N")
        text_widget.insert(tk.END, f" {delta.q40 if delta.q40 > 0 else '0':>3}", "X" if delta.q40 > 0 else "N")
        text_widget.insert(tk.END, f" {delta.q20 if delta.q20 > 0 else '0':>3}", "X" if delta.q20 > 0 else "N")
        text_widget.insert(tk.END, f" {delta.q15 if delta.q15 > 0 else '0':>3}", "X" if delta.q15 > 0 else "N")
        text_widget.insert(tk.END, f" {delta.q10 if delta.q10 > 0 else '0':>3}", "X" if delta.q10 > 0 else "N")

        text_widget.insert(tk.END, f" | {current.mtotal:>5,} ", "N")
        text_widget.insert(tk.END, f"{delta.mtotal:<+3d}" if delta.mtotal > 0 else f"{'':3}", "N")

        text_widget.insert(tk.END, f" {delta.m160 if delta.m160 > 0 else '0':>3}", "X" if delta.m160 > 0 else "N")
        text_widget.insert(tk.END, f" {delta.m80 if delta.m80 > 0 else '0':>3}", "X" if delta.m80 > 0 else "N")
        text_widget.insert(tk.END, f" {delta.m40 if delta.m40 > 0 else '0':>3}", "X" if delta.m40 > 0 else "N")
        text_widget.insert(tk.END, f" {delta.m20 if delta.m20 > 0 else '0':>3}", "X" if delta.m20 > 0 else "N")
        text_widget.insert(tk.END, f" {delta.m15 if delta.m15 > 0 else '0':>3}", "X" if delta.m15 > 0 else "N")
        text_widget.insert(tk.END, f" {delta.m10 if delta.m10 > 0 else '0':>3}", "X" if delta.m10 > 0 else "N")

        text_widget.insert(tk.END, f" ({len(self._data_history)})")
        text_widget.insert(tk.END, "\n")
