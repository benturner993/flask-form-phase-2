# Use a base image with Miniconda installed
FROM continuumio/miniconda3

# Set the working directory in the container
WORKDIR /app

# Copy the environment.yml file into the container at /app
COPY environment.yml .

# Install the Conda environment specified in environment.yml
RUN conda env create -f environment.yml

# Make RUN commands use the new environment
SHELL ["conda", "run", "-n", "myenv", "/bin/bash", "-c"]

# (Optional) Copy the rest of your application code
# COPY . .

# (Optional) Expose a port if your application uses one
# EXPOSE 8080

# (Optional) Define the default command to run your application
# CMD ["python", "your_script.py"]

# Activate the environment
# Note: Using the `RUN conda run` command for the default shell doesn't work well with CMD/ENTRYPOINT
# You might need to use an entrypoint script
# ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "myenv", "python", "your_script.py"]