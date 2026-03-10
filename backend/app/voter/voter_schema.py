from dataclasses import dataclass


@dataclass
class VoterRegistrationSchema:
	id: str
	locality_name_id: str
	locality_display_name: str
	name_fields: list[str]
	address_fields: list[str]
	additional_fields: list[str]


def get_demo_voter_schema() -> VoterRegistrationSchema:
	return VoterRegistrationSchema(
		id="demo_voter_reg_schema",
		locality_display_name="Washington D.C",
		locality_name_id="district_of_columbia",
		name_fields=[
			"First_Name",
			"Last_Name",
		],
		address_fields=[
			"Street_Number",
			"Street_Name",
			"Street_Type",
			"Street_Dir_Suffix",
		],
		additional_fields=["Ward"],
	)
