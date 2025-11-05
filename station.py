from typing import List, Optional

from station_data import StationData


class Station:
    def __init__(self, callsign):
        self.callsign = callsign
        self._data_history: List[StationData] = []
        self._max_history = 10

    def __str__(self) -> str:
        latest: StationData = self.latest()
        return f"{self.callsign:<10} {latest.score:,} pts {latest.qtotal:,} QSOs at {latest.ptotal} points ({latest.mtotal} multipliers) --> history: {len(self._data_history)}"

    def update_from_json_item(self, json_item: dict):
        new_data = StationData(json_item)
        self._data_history.append(new_data)

        while len(self._data_history) > self._max_history:
            self._data_history.pop(0)

    def latest(self) -> Optional[StationData]:
        if not self._data_history:
            return None
        return self._data_history[-1]

    def data_history(self) -> List[StationData]:
        """Get all StationData instances as a list (oldest to newest)"""
        return self._data_history.copy()
