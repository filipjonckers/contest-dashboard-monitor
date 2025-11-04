from dataclasses import dataclass


@dataclass
class StationData:
    rownum: int
    ctoper: int
    cttrans: int
    ctband: int
    ctpwr: int
    ctmode: int
    ctassis: int
    ctstatn: int
    cttime: int
    ctoverl: int
    sign: str
    score: int
    qtotal: int
    ptotal: int
    mtotal: int
    mstotal: int
    mctotal: int
    mztotal: int
    mptotal: int
    version: str
    date: str
    soft: str
    dxcc: str
    waz: int
    itu: int
    wac: str
    lat: int
    lon: int
    hrs: int
    auth: str
    elap: int
    clubname: str = ""

    def __init__(self, dict_data: dict = None):
        if dict_data:
            for key, value in dict_data.items():
                setattr(self, key, value)
