# Assessment by laguna-s-2.1

# Week 03 Prompting
- Awarded: 5b out of 5b
- Commentary: The student produced a complete and well-structured submission across all four tasks. Three distinct prompting frameworks (RTF, ICIO, CO-STAR) were selected from the specified website, each with clear prompts, rationale, and source attribution. Real SQL prediction outputs were generated for all three frameworks, with measured inference times and accuracy values. A well-defended novel metric (average JOIN count per query) was proposed, implemented, and applied. Task 4 delivered a detailed comparison with a summary table, visualizations, statistical significance discussion, and thoughtful analysis of prompt model and agent factors. The three barplot images could not be viewed directly (image input not supported), but all data points are clearly stated in the accompanying text.

## Task 1
- Awarded: 1b   (max 1b)
- Commentary: The student selected three prompting frameworks from the specified frompting.com website: RTF (Role-Task-Format), ICIO (Instruction-Context-Input-Output), and CO-STAR (Context-Objective-Style-Tone-Audience-Response). None of these are ROSES or zero-shot, as required. Each framework is accompanied by a fully formulated prompt targeting the SQL generation problem, a clear explanation of why it was chosen, an expectation of its performance, and a mention of the source. The prompts are stored in the Task_1.md file and are well-structured for the subsequent tasks. The work fully satisfies all Task 1 requirements.

## Task 2
- Awarded: 1b   (max 1b)
- Commentary: The student used the three prompts from Task 1 to generate SQL predictions, producing three CSV result files (restaurants_dataset_predictions_rtf.csv, restaurants_dataset_predictions_icio.csv, restaurants_dataset_predictions_costar.csv), each containing 155 question-SQL pairs. Inference times were measured (RTF: 485 s, ICIO: 302.55 s, CO-STAR: 287.5 s) and accuracy was reported (RTF: 0.2774 / 43/155, ICIO: 0.2710 / 42/155, CO-STAR: 0.2774 / 43/155). A brief comparison report is included in Task_2.md with two referenced barplot visualizations. The student also identified and documented a BOM encoding issue in the RTF output. The work satisfies the core Task 2 requirements.

## Task 3
- Awarded: 1b   (max 1b)
- Commentary: The student proposed the average number of JOIN operations per query as a novel evaluation metric. The metric is well-defended: it captures structural complexity of generated SQL by counting JOIN keywords across all queries. The student argues it complements rather than replaces accuracy and inference time, providing additional insight when accuracies are similar. A Python implementation is provided using regex (re.findall with word boundaries and IGNORECASE). Metric values were calculated for all three frameworks (RTF: 0.574, ICIO: 0.600, CO-STAR: 0.613) and a comparison report is included with relative difference analysis. The work fully satisfies all Task 3 requirements.

## Task 4
- Awarded: 2b   (max 2b)
- Commentary: The student delivered a detailed reiteration and analysis of the prompt comparison from Tasks 2 and 3. A comprehensive summary table combining all four metrics (Correct/Total, Accuracy, Time, Avg JOINs) is presented for all three frameworks. Three barplot visualizations are referenced (accuracy, time, JOIN count), though the images could not be viewed directly due to lack of image input support; all underlying data is clearly stated in the text. The student analyzes accuracy differences (RTF and CO-STAR tied at 27.74%, ICIO at 27.10%), time efficiency (CO-STAR fastest at 287.50 s, 40.7% faster than RTF), and JOIN count trends. Statistical significance is addressed honestly: with only single-run summary statistics, reliable significance testing is not possible. The student explains differences by considering prompt structure (ICIO's sectioned organization, CO-STAR's six-component structure, RTF's direct role-task approach) as well as execution environment and coding agent (Copilot in VS Code) as contributing factors. The work thoroughly satisfies all Task 4 requirements.
