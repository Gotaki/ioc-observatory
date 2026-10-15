# Start from an official image that already has Python 3.12 installed.
# "slim" is a smaller version, so the image downloads and starts faster.
FROM python:3.12-slim

# Set the working folder inside the container. All later commands run from /app.
WORKDIR /app

# Copy ONLY the list of libraries first. Docker caches each step, so if
# requirements.txt hasn't changed, it skips the slow install on the next build
# even when collector.py has changed.
COPY requirements.txt .

# Install the libraries (requests, python-dotenv) into the image.
# --no-cache-dir keeps the image smaller by not storing the download cache.
RUN pip install --no-cache-dir -r requirements.txt

# Now copy in the script itself. This step changes often, so it comes last.
COPY collector.py .

# Run as the unprivileged user "nobody" instead of root. If the script were
# ever compromised, it would have far fewer permissions.
USER nobody

# The command that runs when the container starts. Note that no key is stored
# here: it is passed in at runtime (--env-file locally, a Secret in Kubernetes).
CMD ["python", "collector.py"]
