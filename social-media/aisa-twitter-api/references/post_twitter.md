# Approved posting and media

Publish only the content, account action, attachments, and number of posts the
user authorized. OAuth links an account; it does not independently authorize a
post. Read [cost controls](cost-control.md) before executing requests.

## Preview and account linking

```bash
# Offline preview: no credentials, ledger, upload, or post
python3 scripts/twitter_oauth_client.py post --text "$APPROVED_TEXT" --dry-run

# Add --thread only when multiple posts are intended
python3 scripts/twitter_oauth_client.py post --text "$APPROVED_TEXT" --thread --dry-run

# Get an OAuth link; add --media when local files will be uploaded
python3 scripts/twitter_oauth_client.py authorize --media \
  --budget-usd "$APPROVED_BUDGET_USD" --cost-ledger posting-costs.json
```

Return the authorization link. Use `--open-browser` only if the user wants it
opened locally. The default scopes cover reading the user and creating posts;
`--media` adds `media.write`. Use custom `--scope` values only for the requested
workflow. No X password or browser cookie is needed.

The current authorization response uses top-level `auth_url` and `state`; the
client also accepts the legacy wrapped response. `status` describes local
configuration and does not verify that a live account is linked.

## Publish

```bash
python3 scripts/twitter_oauth_client.py post --text "$APPROVED_TEXT" \
  --cost-ledger posting-costs.json

# Reply to an existing post
python3 scripts/twitter_oauth_client.py post --text "$APPROVED_TEXT" \
  --type reply --in-reply-to-tweet-id "$PARENT_ID" --cost-ledger posting-costs.json

# Quote the exact post the user selected
python3 scripts/twitter_oauth_client.py post --text "$APPROVED_TEXT" \
  --type quote --quote-tweet-url "$QUOTE_URL" --cost-ledger posting-costs.json

# Attach existing media IDs
python3 scripts/twitter_oauth_client.py post --text "$APPROVED_TEXT" \
  --media-id "$MEDIA_ID" --cost-ledger posting-costs.json

# Upload an authorized local image/video, then attach its returned ID
python3 scripts/twitter_oauth_client.py post --text "$APPROVED_TEXT" \
  --media-file "$MEDIA_PATH" --cost-ledger posting-costs.json
```

A post must fit both the API's 280-codepoint limit and the client's weighted
Twitter-length check. Oversized text requires `--thread`; preview the chunks
first. The first chunk uses the requested quote/reply target; subsequent chunks
reply to the preceding confirmed post. No captions are invented for media-only
requests. Do not combine quote targets with media, or local files with media IDs.

The local-file route is a dedicated binary `upload_media` request followed by a
JSON `post_twitter` request using the returned media ID. Multiple attachments
consume separate upload requests; the ledger covers all uploads and the post.
Do not send binary files directly to `post_twitter`: its current multipart schema
accepts text parts despite conflicting prose. Only the first thread chunk receives
attachments.

`--quote` never publishes or uploads. Multi-step previews can quote only requests
whose full bodies are already known; output identifies any unquoted later steps.
It is not a full-thread or upload-plus-post price guarantee.

## Success and recovery

Claim success only for confirmed post IDs. On a failed/ambiguous response, stop
and retain confirmed earlier IDs, upload IDs, partial results, and the ledger.
A timeout or missing ID may follow a successful write; inspect the account before
retrying. Reconcile request-specific charges separately. Re-running the whole
command could duplicate earlier posts or uploads.

The API key appears only in authentication and required request fields. Output
and provider-error echoes are redacted. The client does not save OAuth tokens,
passwords, cookies, or file contents to its ledger.
