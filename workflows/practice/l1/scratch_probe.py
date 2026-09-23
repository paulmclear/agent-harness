from dotenv import load_dotenv
from typesafe_sdk import TypeSafeClient, Choice

load_dotenv()

client = TypeSafeClient()


def load_report() -> dict:
    with open('var/data/report_C-10482.md', 'r') as f:
        return {"report": f.read()}


def main():
    with client:
        response = client.system_one(
            state=load_report(),
            questions={
                "rating": Choice(
                    instructions="Which risk rating does the assessment recommend?",
                    criteria={"low": None, "medium": None, "high": None, "unclear": None}
                )
            }
        )
        
    print(response)


if __name__ == "__main__":
    main()
