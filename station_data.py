import json
from dataclasses import dataclass
from datetime import datetime


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

    def __init__(self):
        pass

    @property
    def datetime_obj(self) -> datetime:
        return datetime.strptime(self.date, "%Y-%m-%d %H:%M:%S")

    # Validation method (can be extended)
    def __post_init__(self):
        if self.score < 0:
            raise ValueError("Score cannot be negative")
        if not self.sign:
            raise ValueError("Sign cannot be empty")

    def __str__(self) -> str:
        return f"ContestData(sign={self.sign}, score={self.score:,}, date={self.date})"

    # Class method to create from JSON string
    @classmethod
    def from_json(cls, json_string: str) -> 'ContestData':
        data = json.loads(json_string)
        return cls(**data)

    @classmethod
    def update_from_dict(cls, update_dict: dict):
        for key, value in update_dict.items():
            if hasattr(cls, key):
                setattr(cls, key, value)
