# TODO(field-spec): Make display columns configurable per region
class MatchColumns:
    __slots__ = ()
    OCR_NAME = "OCR Name"
    OCR_ADDRESS = "OCR Address"
    MATCHED_NAME = "Matched Name"
    MATCHED_ADDRESS = "Matched Address"
    DATE = "Date"
    WARD = "Ward"
    MATCH_SCORE = "Match Score"
    VALID_MATCH = "Valid"
    PAGE_NUMBER = "Page Number"
    ROW_NUMBER = "Row Number"
    FILE_NAME = "Filename"

    def columns(self) -> list[str]:
        return [
            self.OCR_NAME,
            self.OCR_ADDRESS,
            self.MATCHED_NAME,
            self.MATCHED_ADDRESS,
            self.DATE,
            self.WARD,
            self.MATCH_SCORE,
            self.VALID_MATCH,
            self.PAGE_NUMBER,
            self.ROW_NUMBER,
            self.FILE_NAME,
        ]
