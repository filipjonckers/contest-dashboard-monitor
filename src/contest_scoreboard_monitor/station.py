from datetime import timedelta
from tkinter import scrolledtext, END
from typing import List, Optional

from src.contest_scoreboard_monitor.station_data import StationData


class Station:
    def __init__(self, callsign):
        self.callsign: str = callsign
        self.delta: Optional[StationData] = None
        self.range_total: Optional[StationData] = None
        self._data_history: List[StationData] = []
        self._delta_history: List[StationData] = []
        self.mark: bool = False
        self._max_history: int = 10
        self.range: int = 10

    def __str__(self) -> str:
        current: StationData = self.current()
        return f"{self.callsign:<10} {current.score:>10,} - {current.qtotal:>6,} QSOs {current.ptotal:>7,} pts {current.mtotal:>5,} multi --> history: {len(self._data_history)}"

    def update_from_json_item(self, json_item: dict):
        new_data = StationData(json_item)
        if new_data and self.current() and new_data.date == self.current().date:
            # duplicate data, ignore
            return
        self._data_history.append(new_data)
        self.drop_old_data()
        self.update_delta()
        self.update_range_total()
        if self.callsign == "EF8R":
            print('==============================================')
            for data in self._data_history:
                print(f"{data}")
            print('----------------------------------------------')
            for data in self._delta_history:
                print(f"{data}")
            print('==============================================')


    def current(self) -> Optional[StationData]:
        if not self._data_history or len(self._data_history) < 1:
            return None
        return self._data_history[-1]

    def previous(self) -> Optional[StationData]:
        if not self._data_history or len(self._data_history) < 2:
            return None
        return self._data_history[-2]

    def oldest(self) -> Optional[StationData]:
        if not self._data_history or len(self._data_history) < 1:
            return None
        return self._data_history[0]

    def data_history(self) -> List[StationData]:
        """Get all StationData instances as a list (oldest to newest)"""
        return self._data_history.copy()

    def drop_old_data(self) -> None:
        # Drop data older than max history size
        while len(self._data_history) > self._max_history:
            self._data_history.pop(0)
        # Drop data older than max history time
        threshold = self.current().date - timedelta(minutes=self._max_history)
        while self._data_history and self._data_history[0].date < threshold:
            self._data_history.pop(0)

    def update_delta(self) -> None:
        current: StationData = self.current()
        previous: StationData = self.previous()
        # we need at least two data points to calculate a delta
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

    def update_range_total(self) -> None:
        # reset range_total
        self.range_total: StationData = StationData()

        start_index = max(0, len(self._delta_history) - self.range)
        # set start_index to the item in self._delta_history where date is within 10 minutes
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
        # calculate rate per hour
        if len(self._delta_history) > 0:
            if not self.oldest():
                return
            self.range_total.rate = int(self.range_total.qtotal / len(self._delta_history) * 60)

    def add_to_scrolledtext(self, text: scrolledtext.ScrolledText) -> None:
        current: StationData = self.current()
        data: StationData = self.range_total
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

        text.insert(END, f" ({len(self._data_history)})")
        text.insert(END,
                    f" ({'' if not self.oldest() else self.oldest().timestamp} - {current.timestamp} {'' if not self.oldest() else current.date - self.oldest().date})")
        text.insert(END, "\n")
