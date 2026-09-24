# Use the official lightweight Python image
FROM python:3.12-slim

# Step 1: Create a non-root user for security (HF requirement)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:${PATH}"

# Step 2: Set the working directory
WORKDIR /home/user/app

# Step 3: Copy requirements and install
# We do this before copying the whole app to leverage Docker's cache
COPY --chown=user requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir --upgrade -r requirements-dev.txt

# Step 4: Copy the rest of the application
# Using --chown=user ensures our non-root user owns the files
COPY --chown=user . .

# Step 5: Stop the Space build if the application test suite is broken
RUN pytest tests/

# Step 6: Inform HF which port to use
EXPOSE 7860

# Step 7: Start Streamlit
# We force the port to 7860 and the address to 0.0.0.0
CMD ["streamlit", "run", "app.py", "--server.port", "7860", "--server.address", "0.0.0.0"]
