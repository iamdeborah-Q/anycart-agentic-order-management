FROM public.ecr.aws/lambda/python:3.12

# Copy dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Copy LangGraph application
COPY graph.py ${LAMBDA_TASK_ROOT}/graph.py

# Lambda entry point
CMD ["graph.lambda_handler"]
