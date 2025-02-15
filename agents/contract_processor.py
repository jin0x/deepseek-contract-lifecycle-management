from pathlib import Path
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from models import Contract, ProcessingResponse, Clause
from utils.pdf_parser import PDFParser
from utils.helpers import get_logger
import json

logger = get_logger(__name__)

class ContractProcessingAgent:
    def __init__(self, api_key: str):
        self.pdf_parser = PDFParser()

        # Document Parsing Agent
        self.parsing_agent = Agent(
            name="Document Parser",
            role="Document parsing specialist",
            model=OpenAIChat(id="gpt-4o", api_key=api_key),
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
            model=OpenAIChat(id="gpt-4o", api_key=api_key),
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
            model=OpenAIChat(id="gpt-4o", api_key=api_key),
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
            model=OpenAIChat(id="gpt-4o", api_key=api_key),
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
            model=OpenAIChat(id="gpt-4o", api_key=api_key),
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
            model=OpenAIChat(id="gpt-4o", api_key=api_key),
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
            model=OpenAIChat(id="gpt-4o", api_key=api_key),
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
           # 1. Extract and structure contract metadata
            logger.info("Step 1: Extracting contract metadata")
            metadata_prompt = f"""
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

            **Step 2: Extract & Structure Major Contract Sections**
            Identify and extract key contract clauses, ensuring they align with the `Clause` class structure.

            - **Clause Category (`clause_category`)** → Assign a general category based on the clause's legal function (e.g., Financial Terms, Termination, Confidentiality).
            - **Clause Name (`clause_name`)** → Extract the exact heading/title of the clause.
            - **Clause Text (`clause_text`)** → Extract the full clause content without truncation.
            - **Related Dates (`related_dates`)** → Leave blank unless a date is detected (NER will handle this).
            - **Amounts (`amounts`)** → Leave blank unless a monetary value is detected (NER will handle this).
            - **Metadata (`metadata`)**:
            - `"confidence_score"`: AI confidence level for extracted text.

            ⚠️ Flag any issues encountered during clause extraction:
            - `"warning": "Reference to Section 5—full text unavailable."` (Cross-referenced but missing details).
            - `"warning": "Clause may be incomplete—possible text truncation."` (Potential missing content).

            **Step 3: Handle Formatting, OCR Issues & Error Detection**
            Ensure document formatting remains clean and detect common errors.

            - **OCR Issues:** If text quality is poor, flag `"warning": "OCR issue detected—possible missing text."`
            - **Section Numbering Errors:** If clause numbers are inconsistent, flag `"warning": "Clause numbering mismatch detected."`
            - **Duplicate Clauses:** If similar clauses appear multiple times, flag `"warning": "Possible duplicate detected—review needed."`

            **Step 4: Validate Processing & Error Handling**
            Ensure structured contract output follows the `Contract` class format:

            ✅ **Successful Parsing:**
            - `"status": "success"`
            - `"document": {{ structured contract output }}`

            ❌ **Parsing Failure (If structure is inconsistent):**
            - `"status": "failed"`
            - `"error": "Contract could not be parsed due to format inconsistency."`

            **Final Execution Guidelines for AI**
            ✅ Extract all contract metadata and structure it properly.
            ✅ Ensure clauses align with predefined legal categories.
            ✅ Prepare placeholders for NER processing (dates, amounts).
            ✅ Detect and flag formatting errors, missing data, or inconsistencies.
            ✅ Ensure structured output follows `Contract` and `ProcessingResponse` models.

            Text: {text}
            """

            metadata_result = self.parsing_agent.run(metadata_prompt)
            logger.debug(f"Raw metadata result: {metadata_result}")
            logger.debug(f"Metadata type: {type(metadata_result)}")
            logger.info(f"Metadata extraction result: {metadata_result.content if hasattr(metadata_result, 'content') else metadata_result}")

            print(f"metadata_result type: {type(metadata_result)}")
            print(f"metadata_result dir: {dir(metadata_result)}")

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
            - "related_dates": [<list of all dates found>]  # All dates mentioned in the clause
            - "related_amounts": [<list of all monetary amounts>]  # All monetary values

            4. Metadata:
            - "metadata": {{
                "confidence_score": <float between 0 and 1>,
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
                            "confidence_score": 0.95,
                        }}
                    }}
                ]
            }}

            Important Guidelines:
            1. Preserve all original text formatting and numbering
            2. Extract all dates in YYYY-MM-DD format when possible
            3. Include all monetary amounts with currency symbols
            4. Maintain section hierarchy and relationships
            5. Flag any incomplete or ambiguous clauses

            Text: {text}
            """

            clauses_result = self.clause_agent.run(clause_prompt)
            logger.debug(f"Raw clauses result: {clauses_result}")
            logger.debug(f"Clauses type: {type(clauses_result)}")
            logger.info(f"Clause extraction result: {clauses_result.content if hasattr(clauses_result, 'content') else clauses_result}")

           # 3. Classify clauses
            logger.info("Step 3: Classifying clauses")

            classification_prompt = f"""
            You are an advanced AI contract clause classification specialist. Your task is to analyze and categorize contract clauses based on their legal purpose and function, ensuring standardization, consistency, and accuracy.

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
            - If the clause explicitly states its category (e.g., "Payment Terms"), confirm it aligns with the extracted text.
            - If multiple categories seem relevant, classify based on the **primary function** of the clause.

            ✅ **Uncertain Classification:**
            - If the AI **is unsure about a classification**, label it as `"Miscellaneous"` and **add a warning**.
            - Example: `"warning": "Clause classification uncertain—manual review needed."`
            - If a clause **contains multiple legal functions** (e.g., penalties + termination), return the **primary category** and **flag it for human review**.
            - Example: `"warning": "Overlapping clause categories detected—review recommended."`

            ### **Step 3: Ensure Legal Integrity & Formatting Consistency**
            ✅ **Preserve Clause Formatting**
            - Do **not alter or rephrase the clause text**—classification should be based on **legal function, not language style**.
            - Maintain **section numbering and paragraph structure** to preserve context.

            ✅ **Detect & Flag Misclassified Clauses**
            - If a clause appears **misclassified based on content**, return:
            - Example: `"warning": "Potential misclassification—manual verification recommended."`
            - If a clause **does not match any category**, assign `"Miscellaneous"` and provide an explanation.

            ### **Step 4: Validate Classification & Handle Errors**
            ✅ **If Classification is Successful, Return:**
            - `"status": "success"`
            - `"document": {{ structured clause classification output }}`

            ❌ **If Classification Fails (Unclear or Incomplete Clause), Return:**
            - `"status": "failed"`
            - `"error": "Clause classification failed due to ambiguous content."`

            ⚠️ **Additional Warnings for Edge Cases:**
            - `"warning": "Clause category inferred based on context—review recommended."`
            - `"warning": "Clause references external section—full classification may be incomplete."`

            Input Clauses: {clauses_result.content}
            """

            classified_clauses = self.classification_agent.run(classification_prompt)
            logger.info(f"Classification result: {classified_clauses.content if hasattr(classified_clauses, 'content') else classified_clauses}")


           # 4. Extract entities from each clause
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

            - **Governing Law & Jurisdiction**: Identify any legal jurisdiction references.
            - If multiple legal jurisdictions are detected, flag them for review.
            - Example: "warning": "Multiple jurisdictions detected—review required."

            Ensure extracted values match the contract's references and flag unclear cases with appropriate warnings. The output structure must align with the expected Clause class format.

            Input Clauses: {classified_clauses.content}
            """

            enriched_clauses = self.ner_agent.run(ner_prompt)
            logger.info(f"NER result: {enriched_clauses.content if hasattr(enriched_clauses, 'content') else enriched_clauses}")


            # 5. Generate alternative clauses (optional)
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
            - Ensure definitions of key terms are clear (e.g., jurisdiction, obligations, liabilities)

            ### **Step 3: Validate Legal Compliance & Precision**
            - Ensure compliance with standard legal best practices
            - Maintain contractual intent while improving structure
            - Confirm that revised clauses integrate seamlessly into the document
            - If a clause is already optimal, return it as-is with a justification

            ### **Step 4: Structured Output Format**
            For each clause, return:
            {{
                "clause_category": "Category",
                "original_clause_text": "Original text",
                "improved_clause_text": "Improved version",
                "modification_reason": "Explanation of changes or why no changes needed"
            }}

            Input Clauses: {enriched_clauses.content}
            """

            generated_clauses = self.generation_agent.run(generation_prompt)
            logger.debug(f"Raw generated result: {generated_clauses}")
            logger.debug(f"Generated type: {type(generated_clauses)}")
            logger.info(f"Generation result: {generated_clauses.content if hasattr(generated_clauses, 'content') else generated_clauses}")

            # 6. Create contract summary
            logger.info("Step 6: Creating contract summary")
            summary_prompt = f"""
            You are an advanced AI contract summarization specialist, trained to generate clear, structured summaries of legal agreements. Your goal is to provide a contract summary that captures key financial terms, risk factors, obligations, and termination conditions.

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

            ### **Step 4: Structured Output Format**
            Return as JSON:
            {{
                "contract_title": "Title",
                "contract_date": "Date",
                "parties_involved": [
                    {{
                        "party_name": "Name",
                        "role": "Role"
                    }}
                ],
                "summary": {{
                    "agreement_scope": "Description",
                    "financial_terms": {{
                        "total_value": "Amount",
                        "payment_schedule": "Schedule",
                        "penalties": "Terms"
                    }},
                    "termination_terms": {{
                        "notice_period": "Period",
                        "penalties": "Terms"
                    }},
                    "confidentiality_terms": "Description",
                    "risk_assessment": "Level and explanation"
                }}
            }}

            Contract Metadata: {metadata_result.content}
            Key Clauses: {generated_clauses.content}
            """

            summary_result = self.summary_agent.run(summary_prompt)
            logger.debug(f"Raw summary result: {summary_result}")
            logger.debug(f"Summary type: {type(summary_result)}")
            logger.info(f"Summary result: {summary_result.content if hasattr(summary_result, 'content') else summary_result}")

            # 7. Combine results
            logger.info("Step 7: Combining all results")
            try:
                # Get metadata from RunResponse
                metadata_content = metadata_result.content if hasattr(metadata_result, 'content') else metadata_result

                # Get clauses from RunResponse
                clauses_content = generated_clauses.content if hasattr(generated_clauses, 'content') else generated_clauses

                # Get summary from RunResponse
                summary_content = summary_result.content if hasattr(summary_result, 'content') else summary_result

                # Add debug logging
                logger.debug(f"Clauses content type: {type(clauses_content)}")
                logger.debug(f"Clauses content: {clauses_content}")

                contract_data = {
                    "pdf_name": pdf_path.name,
                    "contract_title": metadata_content.contract_title,
                    "contract_date": metadata_content.contract_date,
                    "parties_involved": metadata_content.parties_involved,
                    "clauses": metadata_content.clauses,
                    "summary": summary_content.summary,
                    "amounts": metadata_content.amounts
                }

                return ProcessingResponse(
                    status="success",
                    error=None,
                    document=Contract(**contract_data)
                )
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {e}")
                logger.error(f"Raw metadata content: {metadata_result.content if hasattr(metadata_result, 'content') else metadata_result}")
                logger.error(f"Raw clauses content: {generated_clauses.content if hasattr(generated_clauses, 'content') else generated_clauses}")
                raise

        except Exception as e:
            return ProcessingResponse(
                status="error",
                error=f"Contract processing failed: {str(e)}",
                document=None
            )