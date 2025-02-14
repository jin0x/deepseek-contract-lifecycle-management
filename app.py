import os
from pathlib import Path
from dotenv import load_dotenv
from contract_processor import ContractProcessingAgent

# Load environment variables
load_dotenv()

def main():
    # Get API key from environment
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")

    # Initialize the processor
    processor = ContractProcessingAgent(api_key=api_key)

    # Define the path to the contract
    contract_path = Path("sample_contracts/AlliedEsportsEntertainmentInc_20190815_8-K_EX-10.19_11788293_EX-10.19_Content License Agreement.pdf")

    # Process the contract
    result = processor.process_contract(contract_path)

    # Handle the result
    if result.status == "success":
        print("\nContract Processing Results:")
        print(f"Title: {result.document.contract_title}")
        print(f"Date: {result.document.contract_date}")
        print("\nParties Involved:")
        for party in result.document.parties_involved:
            print(f"- {party.party_name} ({party.role})")
        print(f"\nNumber of Clauses: {len(result.document.clauses)}")
        print("\nSummary:")
        print(result.document.summary)
    else:
        print(f"Error processing contract: {result.error}")

if __name__ == "__main__":
    main()