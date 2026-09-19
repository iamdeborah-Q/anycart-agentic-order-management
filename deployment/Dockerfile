FROM public.ecr.aws/lambda/python:3.12

# Copy dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Copy LangGraph application package
COPY agent ${LAMBDA_TASK_ROOT}/agent

# Lambda entry point
CMD ["agent.graph.lambda_handler"]