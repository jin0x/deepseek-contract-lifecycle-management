class ContractPrompts:
    METADATA_PROMPT = """
    You are an advanced AI document parsing specialist. Your task is to accurately extract contract metadata, structure clauses for processing, and flag potential issues while preserving legal integrity.

    **Step 1: Extract & Structure Contract Metadata**  
    Extract and structure contract metadata according to the `Contract` class format.  

    - **Contract Title (`contract_title`)** → Extract the full contract title exactly as stated.  
    - **Contract Date (`contract_date`)** → Identify and extract the official start date of the agreement.  
    - **Parties Involved (`parties_involved`)**: Extract the name and role of each party in structured format:  
    - Example: `"party_name": "Company A", "role": "Service Provider"`  
    - Example: `"party_name": "Company B", "role": "Client"`  

    ⚠️ If any metadata fields are missing, incomplete, or ambiguous, flag them:  
    - Example: `"warning": "Contract date missing—manual review needed."`  

    Text: {text}
    """

    CLAUSE_EXTRACTION_PROMPT = """
    You are an advanced AI contract clause extraction specialist. Extract and structure clauses with:

    1. Clause Information:
    - "clause_category": Category or type of the clause
    - "clause_text": Complete text of the clause
    
    2. Related Information:
    - "related_dates": List of dates in YYYY-MM-DD format
    - "amounts": List of monetary amounts (numbers only, without currency symbols)
    
    3. Metadata:
    - confidence_score: Float between 0 and 1
    - extracted_by: Name of the extraction agent

    Text: {text}
    """

    CLASSIFICATION_PROMPT = """
    You are an advanced AI contract clause classification specialist. Classify each clause into standard categories:

    1. Categories:
    - Financial Terms (Payment, Fees, Penalties)
    - Confidentiality & NDA
    - Termination & Breach
    - Indemnification & Liability
    - Dispute Resolution
    - Rights & Restrictions
    - Miscellaneous

    Input Clauses: {clauses_content}
    """

    NER_PROMPT = """
    You are an advanced AI Named Entity Recognition (NER) specialist for legal contracts. Extract:

    1. Dates (YYYY-MM-DD format)
    2. Monetary amounts (without currency symbols)
    3. Party names and roles
    4. Legal jurisdictions

    Input Clauses: {clauses_content}
    """

    GENERATION_PROMPT = """
    You are an advanced AI legal contract assistant. For each clause:

    1. Analyze for clarity and legal robustness
    2. Suggest improvements while preserving meaning
    3. Flag ambiguous or risky language
    4. Provide alternative wording if needed

    Input Clauses: {clauses_content}
    """

    SUMMARY_PROMPT = """
    You are an advanced AI contract summarization specialist. Create a concise summary including:

    1. Contract type and purpose
    2. Key parties and roles
    3. Main financial terms
    4. Critical dates and deadlines
    5. Important obligations
    6. Risk assessment

    Contract Metadata: {metadata}
    Key Clauses: {clauses}
    """

    @staticmethod
    def format_metadata_prompt(text: str) -> str:
        return ContractPrompts.METADATA_PROMPT.format(text=text)

    @staticmethod
    def format_clause_prompt(text: str) -> str:
        return ContractPrompts.CLAUSE_EXTRACTION_PROMPT.format(text=text)

    @staticmethod
    def format_classification_prompt(clauses_content: str) -> str:
        return ContractPrompts.CLASSIFICATION_PROMPT.format(clauses_content=clauses_content)

    @staticmethod
    def format_ner_prompt(clauses_content: str) -> str:
        return ContractPrompts.NER_PROMPT.format(clauses_content=clauses_content)

    @staticmethod
    def format_generation_prompt(clauses_content: str) -> str:
        return ContractPrompts.GENERATION_PROMPT.format(clauses_content=clauses_content)

    @staticmethod
    def format_summary_prompt(metadata: str, clauses: str) -> str:
        return ContractPrompts.SUMMARY_PROMPT.format(metadata=metadata, clauses=clauses)

    # Add other format methods... 