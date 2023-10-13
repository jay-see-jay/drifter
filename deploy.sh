#!/bin/zsh

env_yaml=".env.yaml"

# Check if env_yaml exists
if [ -f "$env_yaml" ]; then
    # If the file exists, truncate/empty it
    rm $env_yaml
fi

touch $env_yaml

# Read each line from .env
while IFS='=' read -r key value
do
  # Write the key value pair to .env.yaml
  echo "$key: '$value'" >> $env_yaml
done < .env

source .env

gcloud functions deploy watch_gmail_messages \
	--gen2 \
	--configuration=$CLOUD_SDK_CONFIG \
	--project=$GOOGLE_PROJECT_ID \
	--env-vars-file=.env.yaml \
	--runtime=python311 \
	--region=$CLOUD_REGION \
	--source=. \
	--entry-point=watch_gmail_messages \
	--trigger-topic=$GOOGLE_PUBSUB_TOPIC