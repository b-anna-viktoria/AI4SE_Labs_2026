# Task 1 Assignment

Choose 3 prompting frameworks (such as ROSES) from this https://frompting.com/frameworks or other website. Do not use ROSES nor zero-shot propting. Formulate prompts based on each chosen framework, that will later be used to solve problems in Task 2. Explain why you chose each of the prompts, what do you expect from it.

POINTS AWARDED FOR SUCCESSFUL COMPLETION: 1b

OUTPUT:
A data file or files containing the formulated prompts
A report on why each prompt framework was chosen and where was it found


---------------------------------------------------------------------------------------------------------------------------
SOLUTION:

#1 - RTF (Role-Task-Format)

I chose this framework from the given website, because it is a simpler framework with 3 steps, and I think that for this task some steps (like purpose or tone) are not important, because the solution is evaluated by a script, not by a human. I expect that it will work quite well, but maybe it won't be the best because of its simplicity. Note: I based my prompt on one of the examples on the website

Prompt:

You are a SQL specialist who translates natural‑language questions into precise, executable queries that provide the answer to these questions after execution. 
Your task is to read the questions written in plain English in the file restaurants_dataset.csv from the question column. Rewrite each question into an SQL statement that answers the given question after executed.You work with a standard relational database which is specified in the file restaurants-schema.csv. Identify the required tables, columns, joins, filters, aggregations, and ordering based solely on the information provided. 
The ouput is a file named "restaurants_dataset_predictions.csv" with 2 columns: question and predicted_sql, separated by a comma. The question column contains the natural-language question, the column predicted_sql contains the query that you wrote.
 Ensure the query is syntactically correct, uses explicit column aliases where appropriate, and avoids unnecessary complexity. Exclude any explanatory text and commentary. Also measure the time that is needed for this task and write the answer as text after you returned the csv file. 



#2 - ICIO (Instruction-Context-Input-Output)

I chose this framework from the given website because it also didn't contain things like tone and it is constructed for when humans will not read the result. I think it will perform quite okay.

Prompt:

Instruction: Translate each natural-language question into a precise, executable SQL query that correctly answers the question when executed against the specified relational database.

Context: The database structure is described in `restaurants-schema.csv`. Use this schema as the authoritative source for identifying available tables, columns, relationships, and data types. Do not assume the existence of tables or columns that are not supported by the provided schema. For some queries the correct result may be empty.

Input: Read all questions from the question column in `restaurants_dataset.csv`. For each question, determine the relevant tables, columns, joins, filtering conditions, aggregations, grouping, and ordering required to produce the answer.

Output: Create a CSV file named `restaurants_dataset_predictions_isio.csv` containing exactly two columns: question and predicted_sql, separated by commas. 
Example: 
question, predicted_sql
"What cities are the restaurants located in?", "SELECT DISTINCT CITY_NAME FROM RESTAURANT;"

- Preserve each original question exactly as it appears in the input file.
- Write the corresponding SQL query in the column predicted_sql.
- Ensure that each query is syntactically correct and executable against the specified schema.
- Use explicit column aliases where appropriate and avoid unnecessary complexity.
- Handle commas, quotation marks, and other special characters in CSV fields according to CSV escaping rules.
- Do not include explanatory text, comments, or additional columns in the CSV file.

After creating the CSV file, report the total elapsed time required to complete the task as plain text outside the file. Measure the actual elapsed time from the beginning of processing until the file has been written, rather than estimating it.
Return the completed CSV file and the elapsed time only.


#3 CO-STAR (Context-Objective-Style-Tone-Audience-Response)
I chose this framework from the given website, because it was mentioned during the lectures that it is great alternative to ROSES. It contains style, tone and audience though, which are not really needed for this task. 
I expect it to work quite well. 

Prompt:

Context: You are working with a standard relational database whose schema is provided in 'restaurants-schema.csv'. The file 'restaurants_dataset.csv' contains natural-language questions in its question column. Each question must be answered using SQL queries based solely on the supplied database schema.

Objective: Translate every natural-language question into a correct, executable SQL query that retrieves the requested information from the database. Identify the necessary tables, columns, joins, conditions, aggregations, grouping, and ordering for each query. Ensure that the query accurately reflects the meaning of the original question.

Style: Write clear, concise, efficient SQL. Use explicit column aliases where appropriate, avoid unnecessary subqueries or joins, and do not introduce assumptions unsupported by the provided schema.

Tone: Maintain a precise, technical, and unambiguous approach. Prioritize query correctness and faithful interpretation of the questions over stylistic complexity.

Audience: The output is intended for an automated evaluation workflow in which the generated SQL queries will be executed against the corresponding relational database.

Response: Create a CSV file named restaurants_dataset_predictions_costar.csv with exactly two columns, question and predicted_sql, separated by a comma.

Include one row for each question in the input file. Preserve the original question text exactly. Store the complete SQL query in the corresponding predicted_sql field.Ensure that the SQL statements are syntactically valid and compatible with the database schema.
Do not include explanations, comments, additional columns, or other text in the CSV file.

Measure the actual total elapsed time from the beginning of processing until the CSV file has been created successfully. After returning the file, report this duration as plain text outside the CSV file.

Return only the completed CSV file and the measured elapsed time.