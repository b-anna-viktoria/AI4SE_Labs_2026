# Assessment by human lecturer

# Week 03 Prompting
- Awarded: 4b out of 5b
- Commentary: Breakdown below

## Task 1
- Awarded: 1b
- Commentary: nice choices; in RTF you wrote a monolithic prompt - that can be okay, although when we use a prompting framework, we usually explicitly name sections an split them into paragraphs

## Task 2
- Awarded: 1b
- Commentary: nice comparison; plotting individual execution times in a violin plot might be interesting 

## Task 3
- Awarded: 1b
- Commentary: using JOIN count as a metric is an interesting idea; I appreciate you being honest about its drawbacks; under condition that we are comparing two relatively accurate prompts/models/settings, the one that gets the job done with less JOINs might be actually better (e.g. if one model hallucinates unnecessary JOINs), but it would also need to account for SUBSELECTs (in some cases, a join could be replaced with a SUBSELECT, which is potentially more resource-intensive than JOIN)

## Task 4
- Awarded: 1b
- Commentary: the summary is okay; but we are missing the statistical tests - yes, summary values are not enough to perform statistical tests, but you have access to all the values (or else how would you have calculated the summary values), so you can perform the statistical testing (test for data normality first, then test differences between data samles)