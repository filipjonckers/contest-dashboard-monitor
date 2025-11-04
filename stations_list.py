from station import Station


class StationsList:
    def __init__(self):
        self.stations_list = {}

    def get(self, callsign: str) -> Station | None:
        return self.stations_list.get(callsign)

    # update from a single JSON data object dict
    def update_from_json_item(self, json_item: dict):
        callsign = json_item.get('sign', 'ERROR')
        station = self.get(callsign)
        if not station:
            station = Station(callsign=callsign)
            self.stations_list[callsign] = station
        station.update_from_json_item(json_item)

    def get_stations(self) -> list[Station]:
        return list(self.stations_list.values())
