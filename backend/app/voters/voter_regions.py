from abc import ABC, abstractmethod
from typing import Protocol


class VoterRecordSpec(Protocol):

    @abstractmethod
    def name_components(self) -> list[str]:
        pass

    @abstractmethod
    def address_components(self) -> list[str]:
        pass


class UndefinedVoterRecordSpec:

    def name_components(self) -> list[str]:
        return []

    def address_components(self) -> list[str]:
        return []


class DCVoterRecordSpec:
    def name_components(self) -> list[str]:
        return ["First_name", "Last_name"]

    def address_components(self) -> list[str]:
        return [
            "Street_Number",
            "Street_Name",
            "Street_Type",
            "Street_Dir_Suffix",
        ]


class VoterRecordProcessor:

    current_voter_region: VoterRecordSpec

    def __init__(self, voter_region_spec: VoterRecordSpec | None = None):
        self.current_voter_region = (
            voter_region_spec if voter_region_spec else UndefinedVoterRecordSpec()
        )

    def set_voter_region(self, voter_region: VoterRecordSpec):
        self.current_voter_region = voter_region

    def get_name_components(self) -> list[str]:
        return self.current_voter_region.name_components()

    def get_address_components(self) -> list[str]:
        return self.current_voter_region.address_components()
