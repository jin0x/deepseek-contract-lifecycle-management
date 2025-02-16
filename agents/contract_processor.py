from pathlib import Path
from agno.agent import Agent
from agno.models.deepseek import DeepSeek
from models import Contract, ProcessingResponse, Clause
from typing import List
from utils.pdf_parser import PDFParser
from utils.helpers import get_logger, chunk_text
import json

logger = get_logger(__name__)

class ContractProcessingAgent:
    def __init__(self, api_key: str):
        self.pdf_parser = PDFParser()

        # Document Parsing Agent
        self.parsing_agent = Agent(
            name="Document Parser",
            role="Document parsing specialist",
            model=DeepSeek(id="deepseek-chat", base_url="https://api.aimlapi.com/v1", api_key=api_key),
            instructions=["Extract contract metadata and structure"],
            markdown=True,
            show_tool_calls=True,
            response_model=Contract,
            structured_outputs=True,
        )

        # Clause Extraction Agent
        self.clause_agent = Agent(
            name="Clause Extractor",
            role="Contract clause extraction specialist",
            model=DeepSeek(id="deepseek-chat", base_url="https://api.aimlapi.com/v1", api_key=api_key),
            instructions=["Identify and extract individual contract clauses"],
            markdown=True,
            show_tool_calls=True,
            response_model=Clause,
            structured_outputs=True,
        )

        # Clause Classification Agent
        self.classification_agent = Agent(
            name="Clause Classifier",
            role="Contract clause classification specialist",
            model=DeepSeek(id="deepseek-chat", base_url="https://api.aimlapi.com/v1", api_key=api_key),
            instructions=["Classify contract clauses into standard categories"],
            markdown=True,
            show_tool_calls=True,
            response_model=Clause,
            structured_outputs=True,
        )

        # NER Agent
        self.ner_agent = Agent(
            name="NER Processor",
            role="Named Entity Recognition specialist",
            model=DeepSeek(id="deepseek-chat", base_url="https://api.aimlapi.com/v1", api_key=api_key),
            instructions=["Extract dates, amounts, and named entities from clauses"],
            markdown=True,
            show_tool_calls=True,
            response_model=Clause,
            structured_outputs=True,
        )

        # Clause Generation Agent
        self.generation_agent = Agent(
            name="Clause Generator",
            role="Contract clause improvement specialist",
            model=DeepSeek(id="deepseek-chat", base_url="https://api.aimlapi.com/v1", api_key=api_key),
            instructions=["Generate improved versions of contract clauses"],
            markdown=True,
            show_tool_calls=True,
            response_model=Clause,
            structured_outputs=True
        )

        # Summarization Agent
        self.summary_agent = Agent(
            name="Contract Summarizer",
            role="Contract summarization specialist",
            model=DeepSeek(id="deepseek-chat", base_url="https://api.aimlapi.com/v1", api_key=api_key),
            instructions=["Create concise summaries of full contracts"],
            markdown=True,
            show_tool_calls=True,
            response_model=Contract,
            structured_outputs=True
        )

        # Agent Team
        self.agent_team = Agent(
            name="Contract Processing Team",
            role="Contract analysis coordination",
            model=DeepSeek(id="deepseek-chat", base_url="https://api.aimlapi.com/v1", api_key=api_key),
            team=[
                self.parsing_agent,
                self.clause_agent,
                self.classification_agent,
                self.ner_agent,
                self.generation_agent,
                self.summary_agent
            ],
            instructions=["Coordinate contract analysis workflow"],
            markdown=True,
            show_tool_calls=True,
            response_model=ProcessingResponse,
            structured_outputs=True
        )

    def process_chunks(self, chunks: List[dict], processor_func: callable, prompt_template: str) -> List[dict]:
        """Process text chunks through a specified agent function.

        Args:
            chunks (List[dict]): List of text chunks with metadata
            processor_func: The agent function to process each chunk
            prompt_template: The prompt template to use for processing

        Returns:
            List[dict]: List of processing results for each chunk
        """
        results = []
        for chunk in chunks:
            try:
                # Create chunk-specific prompt with correct variable names
                chunk_prompt = prompt_template.format(
                    sequence_num=chunk['sequence'] + 1,  # Changed from chunk_num
                    total_chunks=len(chunks),
                    text=chunk['text']
                )

                logger.info(f"Processing chunk {chunk['sequence'] + 1}/{len(chunks)}")
                result = processor_func(chunk_prompt)

                if hasattr(result, 'content'):
                    result_data = result.content
                else:
                    result_data = result

                results.append({
                    'result': result_data,
                    'chunk_metadata': chunk
                })

            except Exception as e:
                logger.error(f"Error processing chunk {chunk['sequence']}: {str(e)}")
                raise

        return results

    def combine_metadata_results(self, chunk_results: List[dict]) -> dict:
        """Combine metadata results from multiple chunks into a single coherent result.

        Args:
            chunk_results (List[dict]): Results from processing each chunk

        Returns:
            dict: Combined metadata
        """
        combined = {
            'contract_title': None,
            'contract_date': None,
            'parties_involved': set(),
            'clauses': [],
            'amounts': set()
        }

        for chunk_result in chunk_results:
            result = chunk_result['result']

            # Extract contract title from first chunk that has it
            if not combined['contract_title'] and hasattr(result, 'contract_title'):
                combined['contract_title'] = result.contract_title

            # Extract contract date from first chunk that has it
            if not combined['contract_date'] and hasattr(result, 'contract_date'):
                combined['contract_date'] = result.contract_date

            # Combine unique parties
            if hasattr(result, 'parties_involved'):
                for party in result.parties_involved:
                    combined['parties_involved'].add((party.party_name, party.role))

            # Combine clauses
            if hasattr(result, 'clauses'):
                combined['clauses'].extend(result.clauses)

            # Combine amounts
            if hasattr(result, 'amounts'):
                combined['amounts'].update(set(result.amounts))

        # Convert sets back to lists and create proper structure
        return {
            'contract_title': combined['contract_title'],
            'contract_date': combined['contract_date'],
            'parties_involved': [
                {'party_name': name, 'role': role}
                for name, role in combined['parties_involved']
            ],
            'clauses': combined['clauses'],
            'amounts': list(combined['amounts'])
        }

    def process_pdf(self, pdf_path: str | Path) -> ProcessingResponse:
        """Process a PDF file through the entire pipeline"""
        try:
            logger.info(f"Starting PDF processing for file: {pdf_path}")

            pdf_path = Path(pdf_path) if isinstance(pdf_path, str) else pdf_path
            logger.info(f"Using PDF path: {pdf_path.absolute()}")

            # Extract text from PDF
            logger.info("Extracting text from PDF")
            text = self.pdf_parser.parse_pdf(pdf_path)
            logger.debug(f"Extracted text length: {len(text)}")
            logger.debug(f"First 500 chars of text: {text[:500]}")

            # Process the extracted text
            logger.info("Processing extracted text through contract pipeline")
            return self.process_contract(text, pdf_path)

        except Exception as e:
            logger.error(f"PDF processing failed: {str(e)}", exc_info=True)
            return ProcessingResponse(
                status="error",
                error=f"PDF processing failed: {str(e)}",
                document=None
            )

    def process_contract(self, text: str, pdf_path: Path) -> ProcessingResponse:
        """
        Process a contract document through the entire pipeline of agents.

        Args:
            text (str): The raw text content of the contract
            pdf_path (Path): The path to the PDF file

        Returns:
            ProcessingResponse: Processing result with either the structured contract data or error
        """
        try:
            # Log initial text stats
            logger.info(f"""
                Contract Processing Stats:
                - Total text length: {len(text)} characters
                - Number of paragraphs: {len(text.split('\n\n'))}
            """)

            # 1. Extract and structure contract metadata
            logger.info("Step 1: Extracting contract metadata")
            chunks = chunk_text(text)
            logger.info(f"Created {len(chunks)} chunks for processing")

            metadata_prompt = """
            You are an advanced AI document parsing specialist. You are processing chunk {sequence_num} of {total_chunks}.

            **Step 1: Extract & Structure Contract Metadata**
            Extract and structure contract metadata according to the `Contract` class format.

            - **Contract Title (`contract_title`)** → Extract the full contract title exactly as stated.
            - **Contract Date (`contract_date`)** → Identify and extract the official start date of the agreement.
            - **Parties Involved (`parties_involved`)**: Extract the name and role of each party in structured format:
            - Example: `"party_name": "Company A", "role": "Service Provider"`
            - Example: `"party_name": "Company B", "role": "Client"`

            ⚠️ If any metadata fields are missing, incomplete, or ambiguous, flag them:
            - Example: `"warning": "Contract date missing—manual review needed."`

            **Step 2: Extract & Structure Major Contract Sections**
            Identify and extract key contract clauses, ensuring they align with the `Clause` class structure.

            - **Clause Category (`clause_category`)** → Assign a general category based on the clause's legal function
            - **Clause Name (`clause_name`)** → Extract the exact heading/title of the clause
            - **Clause Text (`clause_text`)** → Extract the full clause content
            - **Related Dates (`related_dates`)** → Leave blank unless a date is detected
            - **Amounts (`amounts`)** → Leave blank unless a monetary value is detected
            - **Metadata (`metadata`)**:
            - `"confidence_score"`: AI confidence level for extracted text

            ⚠️ Flag any issues encountered during clause extraction:
            - `"warning": "Reference to Section 5—full text unavailable."`
            - `"warning": "Clause may be incomplete—possible text truncation."`

            **Step 3: Handle Formatting, OCR Issues & Error Detection**
            Ensure document formatting remains clean and detect common errors.

            - **OCR Issues:** Flag `"warning": "OCR issue detected—possible missing text."`
            - **Section Numbering Errors:** Flag `"warning": "Clause numbering mismatch detected."`
            - **Duplicate Clauses:** Flag `"warning": "Possible duplicate detected—review needed."`

            **Step 4: Validate Processing & Error Handling**
            Ensure structured contract output follows the `Contract` class format:

            ✅ **Successful Parsing:**
            - `"status": "success"`
            - `"document": {{ structured contract output }}`

            ❌ **Parsing Failure:**
            - `"status": "failed"`
            - `"error": "Contract could not be parsed due to format inconsistency."`

            Text chunk to process: {text}
            """

            metadata_results = self.process_chunks(
                chunks,
                self.parsing_agent.run,
                metadata_prompt
            )

            combined_metadata = self.combine_metadata_results(metadata_results)
            logger.info("Metadata extraction complete")

            # 2. Extract clauses
            logger.info("Step 2: Extracting clauses")
            clause_prompt = f"""
            You are an advanced AI contract clause extraction specialist. Extract and structure clauses with:

            1. Sequential Numbering:
            - "clause": <number>  # Number each clause sequentially

            2. Section Information:
            - "section_name": <name>  # Extract section names/headers

            3. Detailed Extraction:
            - "clause_text": <full text>  # Complete clause text without truncation
            - "related_dates": [<list of all dates found>]  # All dates mentioned
            - "related_amounts": [<list of all monetary amounts>]  # All monetary values

            4. Metadata:
            - "metadata": {{
                "confidence_score": <float between 0 and 1>
            }}

            Output Format:
            {{
                "clauses": [
                    {{
                        "clause": 1,
                        "section_name": "NATURE OF RELATIONSHIP",
                        "clause_text": "Full text of the clause...",
                        "related_dates": ["2025-03-01", "2025-04-01"],
                        "related_amounts": ["$50,000", "$100,000"],
                        "metadata": {{
                            "confidence_score": 0.95
                        }}
                    }}
                ]
            }}

            Input Metadata: {combined_metadata}
            """

            clauses_result = self.clause_agent.run(clause_prompt)
            logger.debug(f"Clauses extraction complete")

            # 3. Classify clauses
            logger.info("Step 3: Classifying clauses")
            classification_prompt = f"""
            You are an advanced AI contract clause classification specialist. Your task is to analyze and categorize contract clauses based on their legal purpose and function.

            ### **Step 1: Analyze Clause Context & Determine Classification**
            Classify each clause into one of the following predefined legal categories based on its content and function:

            - **Financial Terms** → (Payment Obligations, Fees, Compensation, Penalties, Late Payments)
            - **Confidentiality & NDA** → (Data Protection, Trade Secrets, Non-Disclosure, Information Sharing)
            - **Termination & Breach** → (Exit Clauses, Termination Rights, Auto-Renewals, Breach Consequences)
            - **Indemnification & Liability** → (Risk Allocation, Damages, Legal Responsibilities)
            - **Dispute Resolution & Governing Law** → (Arbitration, Mediation, Legal Jurisdiction, Governing Law)
            - **Rights & Restrictions** → (Ownership, IP Rights, Exclusivity, Licensing, Non-Compete)
            - **Miscellaneous** → (Catch-All for Clauses That Do Not Fit Clearly into the Above Categories)

            ### **Step 2: Verify Classification Confidence & Handle Uncertainty**
            ✅ **Accurate Classification:**
            - If the clause explicitly states its category, confirm it aligns with the extracted text
            - If multiple categories seem relevant, classify based on the **primary function**

            ✅ **Uncertain Classification:**
            - If uncertain, label as `"Miscellaneous"` and **add a warning**
            - Example: `"warning": "Clause classification uncertain—manual review needed."`
            - If multiple legal functions detected, return **primary category** and **flag for review**
            - Example: `"warning": "Overlapping clause categories detected—review recommended."`

            Input Clauses: {clauses_result.content if hasattr(clauses_result, 'content') else clauses_result}
            """

            classified_clauses = self.classification_agent.run(classification_prompt)
            logger.info("Classification complete")

            # 4. Extract entities
            logger.info("Step 4: Extracting named entities")
            ner_prompt = f"""
            You are an advanced AI Named Entity Recognition (NER) specialist for legal contracts. Your role is to extract and structure key legal entities, ensuring precision and reliability.

            For each clause, extract and return the following:
            - **Dates (`related_dates`)**: Identify contract start dates, payment deadlines, renewal periods, and any other date references.
            - Convert relative dates (e.g., "payment due in 30 days") into explicit values where possible.
            - Example: "related_dates": ["2025-03-01"]
            - If a date reference is unclear or missing, flag it for review.
                - Example: "warning": "Contract date reference unclear—manual review needed."

            - **Monetary Amounts (`amounts`)**: Identify all financial values (e.g., "$50,000", "2% penalty fee").
            - Ensure extracted amounts retain their correct currency symbols.
            - Example: "amounts": ["$10,000"]
            - If an amount lacks clarity or context, flag it.
                - Example: "warning": "Potential misclassification—amount reference unclear."

            - **Contracting Parties (`parties_involved`)**: Identify all named parties and their roles.
            - Ensure role consistency with metadata.
            - Example:
                "parties_involved": [
                    {{
                        "party_name": "ABC Corp",
                        "role": "Service Provider"
                    }},
                    {{
                        "party_name": "XYZ Ltd",
                        "role": "Client"
                    }}
                ]
            - If a party's role is unclear, flag it.
                - Example: "warning": "Unclear entity reference—requires verification."

            Input Clauses: {classified_clauses.content if hasattr(classified_clauses, 'content') else classified_clauses}
            """

            enriched_clauses = self.ner_agent.run(ner_prompt)
            logger.info("NER processing complete")

            # 5. Generate alternative clauses
            logger.info("Step 5: Generating alternative clauses")
            generation_prompt = f"""
            You are an advanced AI legal contract assistant specializing in contract clause enhancement. Your task is to improve existing contract clauses by ensuring clarity, legal robustness, and compliance while preserving the intended meaning.

            ### **Step 1: Analyze Input Clause**
            - Understand the legal intent of the clause within the contract
            - Identify ambiguities, redundant phrasing, or vague legal language
            - Ensure that all financial, confidentiality, and liability clauses are well-defined
            - Flag any references to external sections (e.g., "as per Section 5") that lack details

            ### **Step 2: Improve Clause Wording**
            - Enhance clarity by making terms explicit and reducing ambiguity
            - Strengthen legal enforceability by ensuring legally binding phrasing
            - Simplify complex wording while maintaining legal accuracy
            - Ensure definitions of key terms are clear

            ### **Step 3: Structured Output Format**
            For each clause, return:
            {{
                "clause_category": "Category",
                "original_clause_text": "Original text",
                "improved_clause_text": "Improved version",
                "modification_reason": "Explanation of changes or why no changes needed"
            }}

            Input Clauses: {enriched_clauses.content if hasattr(enriched_clauses, 'content') else enriched_clauses}
            """

            generated_clauses = self.generation_agent.run(generation_prompt)
            logger.info("Clause generation complete")

            # 6. Create contract summary
            logger.info("Step 6: Creating contract summary")
            summary_prompt = f"""
            You are an advanced AI contract summarization specialist, trained to generate clear, structured summaries of legal agreements.

            ### **Step 1: Identify Core Contract Elements**
            Extract and summarize:
            - Contract title, effective date, and parties involved
            - Agreement scope and purpose
            - Core obligations for each party
            - Deliverables and service expectations

            ### **Step 2: Summarize Key Legal & Financial Terms**
            Financial Terms:
            - Payment obligations and pricing structures
            - Penalties and financial liabilities
            - Tax obligations or deductions

            Termination & Dispute Resolution:
            - Termination conditions and notice periods
            - Renewal terms and conditions
            - Dispute resolution mechanisms

            Confidentiality & IP Rights:
            - NDAs and confidentiality agreements
            - IP ownership terms
            - Business restrictions (exclusivity, non-compete)

            ### **Step 3: Risk Assessment**
            Liability & Indemnification:
            - Risk-bearing clauses
            - Liability caps
            - Party responsibilities

            Flag for Review:
            - Vague or one-sided terms
            - Risk assessment (low/medium/high)
            - Unclear obligations

            Contract Metadata: {combined_metadata}
            Processed Clauses: {generated_clauses.content if hasattr(generated_clauses, 'content') else generated_clauses}
            """

            summary_result = self.summary_agent.run(summary_prompt)
            logger.info("Summary generation complete")

            # 7. Combine results
            logger.info("Step 7: Combining all results")
            try:
                metadata_content = combined_metadata
                clauses_content = generated_clauses.content if hasattr(generated_clauses, 'content') else generated_clauses
                summary_content = summary_result.content if hasattr(summary_result, 'content') else summary_result

                contract_data = {
                    "pdf_name": pdf_path.name,
                    "contract_title": metadata_content["contract_title"],
                    "contract_date": metadata_content["contract_date"],
                    "parties_involved": metadata_content["parties_involved"],
                    "clauses": clauses_content.clauses if hasattr(clauses_content, 'clauses') else clauses_content,
                    "summary": summary_content.summary if hasattr(summary_content, 'summary') else summary_content,
                    "amounts": metadata_content["amounts"]
                }

                return ProcessingResponse(
                    status="success",
                    error=None,
                    document=Contract(**contract_data)
                )

            except Exception as e:
                logger.error(f"Error combining results: {e}", exc_info=True)
                raise

        except Exception as e:
            logger.error(f"Contract processing failed: {str(e)}", exc_info=True)
            return ProcessingResponse(
                status="error",
                error=f"Contract processing failed: {str(e)}",
                document=None
            )