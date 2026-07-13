#!/bin/bash

# Define your variables
RTD_TOKEN=ea74e0cef65a935ade1e9fe77d8f9d001b85cbed
RTD_UPLOAD_API="http://devthedocs.org/api/v3/upload"
RTD_PROJECT="test-builds"
FILE_TO_UPLOAD="artifacts.zip"

# 1. Initiate the upload and capture the JSON response
echo "Initiating upload with Read the Docs..."
RESPONSE=$(curl -s -H "Authorization: token $RTD_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST \
  -d "{
    \"project\": \"$RTD_PROJECT\",
    \"version\": {
      \"commit\": \"abc123\",
      \"name\": \"1.0.0\",
      \"type\": \"branch\"
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
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
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
