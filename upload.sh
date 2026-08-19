#!/bin/bash

# Define your variables
RTD_TOKEN=${RTD_TOKEN:-"your_default_token_here"}
RTD_UPLOAD_API=${RTD_UPLOAD_API:-"http://devthedocs.org/api/v3/upload"}
RTD_PROJECT=${RTD_PROJECT:-"test-builds"}
RTD_OUTPUT_HTML=${RTD_OUTPUT_HTML:-"output/html"}
# Make it an absolute path.
RTD_OUTPUT_HTML="$(pwd)/$RTD_OUTPUT_HTML"
TMP_DIR=$(mktemp -d)
FILE_TO_UPLOAD="$TMP_DIR/artifacts.zip"
RTD_VERSION_COMMIT=${RTD_VERSION_COMMIT:-"abc123"}
RTD_VERSION_NAME=${RTD_VERSION_NAME:-"1.0.0"}
RTD_VERSION_TYPE=${RTD_VERSION_TYPE:-"branch"}

echo "Temporary directory created at $TMP_DIR"

# 0. Create zip
echo "Creating zip file of the HTML output..."
if [ -d "$RTD_OUTPUT_HTML" ]; then
    # Create a symlink so the zip command uses the name "html" instead of last part of the directory.
    ln -s "$RTD_OUTPUT_HTML" "$TMP_DIR/html"
    (cd "$TMP_DIR" && zip -r "$FILE_TO_UPLOAD" html)
    echo "Zip file created: $FILE_TO_UPLOAD"
  else
    echo "Error: Directory $RTD_OUTPUT_HTML does not exist."
    exit 1
fi

# 1. Initiate the upload and capture the JSON response
echo "Initiating upload with Read the Docs..."
RESPONSE=$(curl -s -H "Authorization: token $RTD_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST \
  -d "{
    \"project\": \"$RTD_PROJECT\",
    \"version\": {
      \"commit\": \"$RTD_VERSION_COMMIT\",
      \"name\": \"$RTD_VERSION_NAME\",
      \"type\": \"$RTD_VERSION_TYPE\"
    }
  }" \
  "$RTD_UPLOAD_API/initiate/")

# Print the response for debugging
echo "Response from Read the Docs API:"
echo "$RESPONSE"

# 2. Extract the target upload URL using jq
UPLOAD_URL=$(echo "$RESPONSE" | jq -r '.upload_url.url')
# UPLOAD_URL=http://127.0.0.1:9000/build-uploads

if [ -z "$UPLOAD_URL" ] || [ "$UPLOAD_URL" == "null" ]; then
    echo "Error: Failed to fetch upload URL. Response was:"
    echo "$RESPONSE"
    exit 1
fi

echo "Upload URL fetched successfully."

# 3. Build the curl arguments for the dynamic form parameters
# This maps the JSON fields object into multiple -F "key=value" arguments
eval_args=()
while IFS= read -r line; do
    eval_args+=("-F" "$line")
done < <(echo "$RESPONSE" | jq -r '.upload_url.fields | to_entries[] | "\(.key)=\(.value)"')

# 4. Execute the Upload and capture the HTTP status code
echo "Uploading file..."
# -o /dev/null hides the XML response body from S3, -w "%{http_code}" extracts just the status code
# -f turns 4xx/5xx into a non-zero exit, so --retry-all-errors retries them.
HTTP_STATUS=$(curl -sf --retry 5 --retry-all-errors --retry-delay 1 -o /dev/null -w "%{http_code}" -X POST \
  "${eval_args[@]}" \
  -F "file=@$FILE_TO_UPLOAD;type=application/zip" \
  "$UPLOAD_URL")

# 4. Determine success/failure and hit the final API
# Presigned POSTs typically return 200, 201, or 204 on success
if [ "$?" -eq 0 ] && [[ "$HTTP_STATUS" =~ ^2[0-9]{2}$ ]]; then
    STATUS="success"
    echo "Upload succeeded with HTTP $HTTP_STATUS."
else
    STATUS="failed"
    echo "Upload failed with HTTP $HTTP_STATUS."
fi

BUILD_ID=$(echo "$RESPONSE" | jq -r '.build.id')
echo "Reporting build status ($STATUS) back to Read the Docs..."
curl -H "Authorization: token $RTD_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST \
  -d "{\"build\": $BUILD_ID, \"status\": \"$STATUS\"}" \
  "$RTD_UPLOAD_API/complete/"
