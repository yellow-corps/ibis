#!/bin/bash

echo "starting logger"
docker compose -f ../compose.yml logs -f --since "1h" | while read line; do
  if [[ "$line" =~ (error|ERROR|warn|WARN) ]]; then
    content=$(cat <<EOF
<t:$(date +%s):f>
\`\`\`
$line
\`\`\`
EOF
)
    content=$(echo "$content" | awk '{printf "%s\\n", $0}')
    msg="{\"content\": \"$content\"}"
    echo "sent to webhook: $msg"
    curl -H "Content-Type: application/json" -X POST -d "$msg" $ERROR_WEBHOOK_URL
  fi
done
echo "stopping logger"