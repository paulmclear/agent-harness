import csv

from workflows.hubspot_company_data_population.repo import HubSpotCompanyRepository


def output_to_csv(repo: HubSpotCompanyRepository, output_path: str):
    """Output the normalised data from the repository to a CSV file."""

    normalised_data = repo.output_normalised_data()

    with open(output_path, "w", newline="", encoding="utf-8-sig") as csvfile:
        fieldnames = ["hubspot_id", "name", "sector", "sub_sector", "confidence", "rationale", "flags"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(normalised_data)


if __name__ == "__main__":
    repo = HubSpotCompanyRepository(db_path="hubspot_companies.db")
    output_to_csv(repo, "normalised_hubspot_companies.csv")
