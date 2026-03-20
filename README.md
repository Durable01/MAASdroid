## Introduction
AMAAS (Automated Mobile Accessibility Assessment System) is an innovative approach combining cognitive mapping with automated mobile application accessibility scoring. This project, implemented in Python, facilitates accessibility evaluations and is runnable within PyCharm.

## Steps:

1.  Utilize the automated testing tool, Fastbot, to procure logs containing actions for each step and corresponding XML files of the respective pages.
2.  Update folder addresses and their corresponding file addresses as necessary.
3.  Create a new **eval.xlsx** file in the location where you want to get the score table.
4.  Metrics and scores for each app will be stored in **eval.xlsx**.
5.  A single application cannot directly obtain a score. You need to have 4-5 application results in the eval.xlsx table in advance.
6.  Run the following command in the command line of the project folder:

```bash
python data_processing.py -f <folder_path> -e <eval_folder>

Options:
-f  --folder    Path to the folder containing Fastbot logs.
-e  --eval_folder    Path to the folder where evaluation results will be saved.

eg:python data_processing.py -f "E:\Fastbot_Android-main\fastbot-reddit" -e "E:\Fastbot_Android-main
```

## Contact Us:
For any further questions or specific requirements, please don't hesitate to reach out to us.
