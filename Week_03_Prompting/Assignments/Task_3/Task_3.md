# Task 3 Assignment

Propose another metric for assessing how well the problem was completed. Argue and defend why it is a good and applicable metric for the problem. Invention and originality is appreciated. Discuss if the metric complements or replaces the original metric(s) of the problem. Implement the metric calculation, and calculate the metric values for existing predictions from Task 2. Create a report comparing the metric values for different prompts.

POINTS AWARDED FOR SUCCESSFUL COMPLETION: 1b

OUTPUT:
A source code file or files containing the metric implementation
A report on how well in terms of the new metric the model completed the problems with different prompts

ALTERNATIVE OUTPUT:
If the metric is not possible to calculate, create a detailed guide on how to implement and calculate it.


------------------------------------------------------------------------------------------------------------------------
SOLUTION:

My new metric is the average number of JOIN operations per query. It measures how frequently the generated SQL queries combine data from multiple tables. The metric is calculated by counting the occurrences of the JOIN keyword in each predicted SQL query and computing the average across all queries. 
This metric is applicable because SQL queries often need to combine information from multiple tables to answer questions expressed in natural language. Although JOIN operations are frequently necessary, they can introduce additional computational work and increase query complexity. Therefore, the average number of JOIN operations provides a simple indicator of the structural complexity of the generated queries.
However, the metric has limitations. A larger number of JOIN operations does not necessarily indicate a worse query, since some questions inherently require information from several tables. Furthermore, the number of joins alone does not determine execution performance, which also depends on factors such as indexes, database size, query structure, and the database engine. Consequently, this metric should be interpreted as an indicator of query structure rather than a direct measurement of execution efficiency.

The proposed metric complements rather than replaces the original evaluation metrics. Accuracy measures whether the generated queries return the expected results, while generation time measures how long the prediction process takes. The average JOIN count adds information about the structure of the generated SQL queries.
Considering these metrics together provides a broader evaluation of the prompting frameworks. In particular, when accuracy is similar, the average JOIN count can help identify differences in query structure that accuracy alone does not reveal. However, it should not be interpreted as an independent measure of correctness or as definitive evidence of lower execution cost.

The metric scores for the frameworks:
RTF = 0.574
ICIO = 0.600
CO-STAR = 0.613

RTF produced the lowest average number of JOIN operations, ICIO produced middle score of 0.600, while CO-STAR had the highest value.
Compared with RTF, ICIO generated approximately 4.53% more JOIN operations per query, while CO-STAR generated approximately 6.79% more. The difference between CO-STAR and ICIO was smaller, at approximately 2.17%.

These results indicate that the prompting frameworks produced SQL queries with slightly different structural characteristics. RTF generated queries with the lowest average number of joins, whereas CO-STAR generated queries with the highest average number.

Because the accuracy values of the three frameworks were approximately equal, the results suggest that RTF achieved a slightly simpler query structure according to this particular metric. Nevertheless, the differences are relatively small, and the results alone do not establish that RTF generates faster or more efficient SQL queries.



The code for computing the metric:

import csv
import re
from pathlib import Path

def average_join_count(csv_path):
    join_counts = []

    with open(csv_path, encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            sql = row["predicted_sql"]

            count = len(re.findall(r"\bJOIN\b", sql, re.IGNORECASE))
            join_counts.append(count)

    return (
        sum(join_counts) / len(join_counts)
        if join_counts else 0.0
    )





