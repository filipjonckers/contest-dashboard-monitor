import logging

from src.contest_scoreboard_monitor.station import Station


class StationsList:
    def __init__(self):
        self.stations_list = {}

    def get(self, callsign: str) -> Station | None:
        return self.stations_list.get(callsign)

    # update from a single JSON data object dict
    def update_from_json_item(self, json_item: dict, mark: bool = False):
        try:
            callsign = json_item.get('sign', 'ERROR')
            station: Station = self.get(callsign)
            if not station:
                station: Station = Station(callsign=callsign)
                self.stations_list[callsign] = station
            station.update_from_json_item(json_item)
            station.mark = mark
        except Exception as e:
            logging.error("Error updating station from JSON item: %s", e)

    def get_stations(self) -> list[Station]:
        return list(self.stations_list.values())

    def clear(self):
        self.stations_list = {}
