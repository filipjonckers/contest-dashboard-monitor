from dataclasses import dataclass


@dataclass
class Contest:
    testid: int
    name: str
    startdate: str
    enddate: str

    def __str__(self):
        return f"{self.name} (ID: {self.testid}, Start: {self.startdate}, End: {self.enddate})"
