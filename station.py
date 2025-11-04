from station_data import StationData


class Station:
    def __init__(self, callsign):
        self.callsign = callsign
        self.latest: StationData = StationData()

    def __str__(self) -> str:
        return f"{self.callsign}"

    def update_from_json_item(self, json_item: dict):
        self.latest.update_from_dict(json_item)
