import sys
import os
import xmltodict
import pycountry


def main():
    mep_data = read_mep_data()
    for country_name in get_country_names():
        country_data = [mep for mep in mep_data if mep["country"]["#text"] == country_name]
        relevant_data = collect_data(country_data, country_name)
        remove_old_names(country_name, relevant_data)
        write_data(relevant_data, country_name)
    return 0


def get_email_address(contact_details: list) -> str:
    def as_list(obj):
        if isinstance(obj, list):
            return obj
        else:
            return [obj]

    if not contact_details:
        return "NO EMAIL ADDRESS FOUND"
    for method in as_list(contact_details):
        if method["@type"] == "EMA":
            return method["#text"]
    return "NO EMAIL ADDRESS FOUND"


def collect_data(mep_data, country: str) -> dict:
    relevant_data = dict()
    for mep in mep_data:
        assert mep["country"]["#text"] == country
        name = mep["fullName"]

        contact_details = mep.get("eContact")
        relevant_data[name] = {
            "email": get_email_address(contact_details),
            "eu_group": mep["politicalGroup"]["#text"],
            "national_group": mep["nationalPoliticalGroup"]["#text"]
        }
    return relevant_data


def write_data(relevant_data: dict, country: str):
    def fix_name_case(uppercase_name) -> str:
        components = uppercase_name.split("-")
        fixed_componenets = [c[0] + c[1:].lower() for c in components if c != "VAN" and c != "VON"]
        return "-".join(fixed_componenets)

    country_code = pycountry.countries.get(name=country).alpha_2
    output_folder = "contact_details"
    os.makedirs(output_folder, exist_ok=True)
    with open(f"{output_folder}/data_{country_code}.csv", mode="w", encoding="utf-8") as fd:
        fd.write("name,email,eu_group,national_group\n")
        for name, details in relevant_data.items():
            names = [fix_name_case(n) for n in name.split(' ')]
            fd.write(f"{' '.join(names)}#{details['email']}#{details['eu_group']}#{details['national_group']}\n")


def remove_old_names(country: str, relevant_data: dict):
    """
    MEPs may leave office, so make sure that any who are in the list of those elected
    but who are not current MEPs for the given country are not included in the results.
    """
    with open(f"meps_xml/full_list.xml", encoding="utf-8") as fd:
        all_meps = xmltodict.parse(fd.read(), encoding="utf-8")
        names = [n["fullName"] for n in all_meps["meps"]["mep"] if n["country"] == country]

    oldnames = [name for name in relevant_data if name not in names]
    for name in oldnames:
        del relevant_data[name]


def get_country_names() -> list:
    with open(f"meps_xml/full_list.xml", encoding="utf-8") as fd:
        data = xmltodict.parse(fd.read(), encoding="utf-8")
        countries = {mep["country"] for mep in data["meps"]["mep"]}
    return list(countries)


def read_mep_data():
    mep_data = list()
    xml_files = sorted(f for f in os.listdir("meps_xml") if f.startswith("mep_details"))
    for xml_file in xml_files:
        with open(f"meps_xml/{xml_file}", encoding="utf-8") as fd:
            xml_dict = xmltodict.parse(fd.read(), encoding="utf-8")
            if xml_dict["meps"]:
                mep_data.extend(*xml_dict["meps"].values())
    return mep_data


if __name__ == "__main__":
    sys.exit(main())
