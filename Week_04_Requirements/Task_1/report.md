The python code is in the file requirements_refinement.py. The file requirements.md contains the structured file that the agent network produced (requirements.json is the same, just in JSON format)


The solution uses multiple specialized AI agents connected through LangGraph. The workflow separates extraction, refinement, validation, conflict handling, and review into dedicated stages. 
The general workflow looks like this:

Load Documents
      ↓
Requirement Extraction Agent
      ↓
Requirement Merging Agent
      ↓
Deterministic Deduplication Node
      ↓
Conflict Resolution Agent
      ↓
Review Agent
      ↓
(Feedback Loop if necessary)
      ↓
Final Output Generation
      ↓
JSON + Markdown Report

Design choices:
The network was divided into specialized stages. This decomposition follows the principle of task specialization, where each agent focuses on one well-defined responsibility. Separating stages improves maintainability, makes the workflow easier to debug, and allows individual agents to focus on narrower tasks.


1. Requirement Extraction Agent
Model used: gpt-5-mini
This is the first AI agent in the workflow. Its responsibility is to: read the source documents, identify software requirements, create a structured representation of requirements, assign an initial priority and preserve traceability to the source document.
Its responsibility is extracting as many candidate requirements as possible.
This stage was separated from later refinement stages because extracting information and validating information are different tasks. Performing extraction independently reduces the chance of losing requirements during later processing and helps address the completeness requirement.
The gpt-5-mini model was selected because extraction requires good language understanding while still being computationally efficient.


2. Requirement Merging Agent
Model used: gpt-5-nano
After extraction, multiple requirements may describe the same functionality using different wording. The merging agent identifies semantic duplicates and produces a refined requirements set. It also combines all source references so traceability is preserved.
This stage directly addresses OS3 (duplicate requirements), OS4 (traceability), OS7 (consistent terminology).
The gpt-5-nano model was chosen because the task involves restructuring and merging already extracted information, which generally requires less reasoning capability than the initial extraction stage.


3. Deterministic Deduplication Node
This is a non-AI node implemented with traditional Python logic. Its responsibilities are to remove exact duplicates, merge source lists
and keep the highest priority if duplicates exist.
I included this deterministic step because using an LLM for exact duplicate detection would unnecessarily increase cost and complexity.
Exact duplicate detection does not require LLM reasoning and can be performed more reliably with traditional algorithms. 
It also satisfies the assignment requirement for a non-agentic node.


4. Conflict Resolution Agent
Model used: gpt-4.1-nano
This agent checks for problematic requirements, so it separates requirements into two categories: accepted requirements
and discarded requirements (blacklist). Every discarded requirement receives a justification explaining why it was rejected.
The separation of this stage ensures that rejected requirements are not silently removed. Instead, they are documented together with the reason of the rejection.

5. Review Agent
Model used: gpt-4o-mini
The review agent acts as a quality assurance component.
It verifies: consistency of terminology, completeness, proper traceability, duplicate detection quality.
The reviewer does not directly modify requirements. Instead, it produces feedback for the previous stages.
It acts like a real software review process where a reviewer provides comments.
This agent was intentionally separated from the extraction and refinement agents to provide independent feedback of the generated output.

Feedback Loop
After the extraction, merging, deduplication, and conflict resolution stages are completed, the refined requirements are passed to the Review Agent. If no significant issues are found, the reviewer approves the output and the workflow proceeds to the final document generation step. If problems are detected, the reviewer produces structured feedback describing what should be improved. The workflow routes this feedback back to the Requirement Merging Agent. The merging agent then performs another refinement pass while taking the review comments into account.

Output Generation
The final output is generated in two formats. The JSON file is machine-readable and suitable for further processing. The Markdown
is intended for human readers.

Traceability Design
Every requirement stores references to all source documents from which it was derived.
Traceability information is preserved throughout the entire workflow and included in the final report. This allows users to identify the origin of each requirement.




How Assignment Requirements Are Satisfied

ANS1 - At least 3 agentic nodes. Satisfied by Requirement Extraction Agent, Requirement Merging Agent, Conflict Resolution Agent
Review Agent. 

ANS2 - At least 1 deterministic node. Satisfied by Deterministic Deduplication Node.

ANS3 - At least 1 feedback loop. Satisfied by Review Agent → Merge Agent. The reviewer can trigger another refinement cycle if quality issues are detected.

ANS4 - At least 3 different LLM models. Satisfied by using gpt-5-mini, gpt-5-nano, gpt-4.1-nano, gpt-4o-mini.

ANS5 - LangGraph implementation. Satisfied through implementation using StateGraph and LangGraph conditional edges.

Output Specification Requirements
OS1 - Single structured document. Satisfied by generating requirements.md, which contains the complete requirements specification.

OS2 - Unique requirement identification. Satisfied by deterministic assignment of IDs like REQ-001, REQ-002 etc. 

OS3 - No duplicate requirements. Satisfied by Merge Agent and Deterministic Deduplication Node. The LLM handles semantic duplicates while Python removes exact duplicates.

OS4 - Requirement traceability. Each requirement stores source document references.

OS5 - Name and explanation. Each requirement contains a short descriptive title and a paragraph-length description. Required directly in extraction and refinement prompts.

OS6 - Requirement priority. Every requirement receives one level of priority: High, Medium or Low. The Markdown document also explains the meaning of each level.

OS7 - Consistency. Checked by: Conflict Resolution Agent and Review Agent. They verify terminology consistency and identify contradictions.

OS8 - Completeness. The extraction stage processes all supported documents.The reviewer checks whether extracted candidates were either
accepted or explicitly blacklisted.

OS9 - Blacklist. The Conflict Resolution Agent creates a separate blacklist section. For every discarded requirement the document includes the requirement itself, source references and the reason for rejection.


