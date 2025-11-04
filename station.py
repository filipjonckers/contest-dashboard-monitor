from station_data import StationData


class Station:
    def __init__(self, callsign):
        self.callsign = callsign
        self.latest: StationData = StationData()

    def __str__(self) -> str:
        return f"{self.callsign}"

    def update_from_json_item(self, json_item: dict):
        self.latest.update_from_dict(json_item)

    def update_from_json_item2(self, json_item: dict):
        self.latest.score = json_item.get('score', 0)
        self.latest.qtotal = json_item.get('qtotal', 0)
        self.latest.ptotal = json_item.get('ptotal', 0)
        self.latest.mtotal = json_item.get('mtotal', 0)
        self.latest.mstotal = json_item.get('mstotal', 0)
        self.latest.mctotal = json_item.get('mctotal', 0)
        self.latest.mztotal = json_item.get('mztotal', 0)
        self.latest.mptotal = json_item.get('mptotal', 0)
        self.latest.version = json_item.get('version', '')
        self.latest.date = json_item.get('date', '')
        self.latest.soft = json_item.get('soft', '')
        self.latest.dxcc = json_item.get('dxcc', '')
        self.latest.waz = json_item.get('waz', 0)
        self.latest.itu = json_item.get('itu', 0)
        self.latest.wac = json_item.get('wac', '')
        self.latest.lat = json_item.get('lat', 0)
        self.latest.lon = json_item.get('lon', 0)
        self.latest.hrs = json_item.get('hrs', 0)
        self.latest.auth = json_item.get('auth', '')
        self.latest.elap = json_item.get('elap', 0)
        self.latest.clubname = json_item.get('clubname', '')
