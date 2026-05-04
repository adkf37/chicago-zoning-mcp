# FEEDBACK — chicago-zoning-mcp

> Drop feedback here for the project's Squad Lead to pick up.
> The Lead reads this file at the start of each work cycle.

## Format

```
### 2025-05-02 — [Aaron]
Priority: [high]
Sope: [code improvement]

[Project is working well generally. Web deployment is successful and tied to a github action workfolw, so happens automatically. Don't touch the deployment setup.
But looking to improve the performance of the bot to answer any question thrown an it accurately. I'd like to expand the test suite to have a wider range of questions and then improve performance so it can answer 100 percent of the questions accurately. I want to include zoning code text and answering questions about specific addresses as part of the questions it needs to consistently answer correctly. Looking at the text we've downloaded it seems we may need to improve the code ingestion, not sure we've captured everything correctly. 
The other big thing to work on is front-end design of the website, which is very basic. Let's make it look a bit more professional. Use desgin of https://github.com/adkf37/Plan_for_Chicago_2030 for inspiration.


]
```

### 2025-05-03 — [Aaron]
Priority: [high]
Sope: [code improvement]

[Project is working well generally. Web deployment is successful and tied to a github action workfolw, so happens automatically. Don't touch the deployment setup.
Still looking to improve the performance of the bot to answer any question thrown an it accurately. 

The eval suite has some wrong answers in it. And the site is mapping to those wrong answers instead of reading the code. For example, q255 "What is the side yard setback requirement in an RS-3 single-family district?" has this answer: 
"RS-3 side setback is combined 8 ft, minimum 2 ft each side". Thats incorrect.

Code shows in section 17-2-0309:

RS3


Principal residential building: Combined total width of side setbacks must equal 20% of lot width with neither required setback less than 2 feet or 8% of lot width, whichever is greater

Principal nonresidential buildings (e.g., religious assembly and school buildings): 12 feet or 50% of building height, whichever is greater

Worried that we are doing something major wrong....



]
```

### 2025-05-03 — [Aaron]
Priority: [high]
Sope: [code improvement]

[Figured out the accuracy issue. The zoning_codes.csv file in the data folder has outdated information. Let's update that file using the data here: https://secondcityzoning.org/zones/

Then redo the answers in the eval file where relevant.
]


### 2025-05-04 — [Aaron]
Priority: [high]
Scope: [code improvement]

[i've manually changed the zoning_codes.csv data. Please update the  in the eval file where relevant.
]

Let's not add anymore test questions. 

And then i think we can move to closeout


## Feedback Log

