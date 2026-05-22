# AISA gateway endpoint catalog

> Auto-generated index of AISA gateway operations. Do not edit by hand.
> Operations: 95 | Paths: 74

Base URL: `https://api.aisa.one`

Replace `{param}` placeholders with real IDs from prior API responses.

## auth

| Method | inner_uri | apiName | table name |
|--------|-----------|---------|------------|
| GET | `/apis/v1/composio/auth/session/info` | Get current user session information | Auth Session Info |

## auth_configs

| Method | inner_uri | apiName | table name |
|--------|-----------|---------|------------|
| GET | `/apis/v1/composio/auth_configs` | List authentication configurations with optional filters | Auth Configs |
| POST | `/apis/v1/composio/auth_configs` | Create new authentication configuration | Auth Configs |
| DELETE | `/apis/v1/composio/auth_configs/{nanoid}` | Delete an authentication configuration | Auth Configs Nanoid |
| GET | `/apis/v1/composio/auth_configs/{nanoid}` | Get single authentication configuration by ID | Auth Configs Nanoid |
| PATCH | `/apis/v1/composio/auth_configs/{nanoid}` | Update an authentication configuration | Auth Configs Nanoid |
| PATCH | `/apis/v1/composio/auth_configs/{nanoid}/{status}` | Enable or disable an authentication configuration | Auth Configs Nanoid Status |

## connected_accounts

| Method | inner_uri | apiName | table name |
|--------|-----------|---------|------------|
| GET | `/apis/v1/composio/connected_accounts` | List connected accounts with optional filters | Connected Accounts |
| POST | `/apis/v1/composio/connected_accounts` | Create a new connected account | Connected Accounts |
| POST | `/apis/v1/composio/connected_accounts/link` | Create a new auth link session | Connected Accounts Link |
| PATCH | `/apis/v1/composio/connected_accounts/{nanoId}/status` | Enable or disable a connected account | Connected Accounts Nanoid Status |
| DELETE | `/apis/v1/composio/connected_accounts/{nanoid}` | Delete a connected account | Connected Accounts Nanoid |
| GET | `/apis/v1/composio/connected_accounts/{nanoid}` | Get connected account details by ID | Connected Accounts Nanoid |
| PATCH | `/apis/v1/composio/connected_accounts/{nanoid}` | Update a connected account | Connected Accounts Nanoid |
| POST | `/apis/v1/composio/connected_accounts/{nanoid}/refresh` | Refresh authentication for a connected account | Connected Accounts Nanoid Refresh |
| POST | `/apis/v1/composio/connected_accounts/{nanoid}/revoke` | Revoke a connected account at the provider | Connected Accounts Nanoid Revoke |

## consumer

| Method | inner_uri | apiName | table name |
|--------|-----------|---------|------------|
| GET | `/apis/v1/composio/consumer/connected_accounts/{nanoid}/permissions` | Get consumer tool permissions for a connected account | Consumer Connected Accounts Nanoid Permissions |
| PATCH | `/apis/v1/composio/consumer/connected_accounts/{nanoid}/permissions` | Upsert consumer tool permissions for a connected account | Consumer Connected Accounts Nanoid Permissions |
| PATCH | `/apis/v1/composio/consumer/connected_accounts/{nanoid}/permissions/tools/{tool_slug}` | Upsert one consumer tool permission for a connected account | Consumer Connected Accounts Nanoid Permissions Tools Tool Slug |
| POST | `/apis/v1/composio/consumer/permissions/resolve` | Resolve consumer tool-router permissions | Consumer Permissions Resolve |

## files

| Method | inner_uri | apiName | table name |
|--------|-----------|---------|------------|
| GET | `/apis/v1/composio/files/list` | List files with optional app and action filters | Files List |
| POST | `/apis/v1/composio/files/upload/request` | Create presigned URL for request file upload to S3 | Files Upload Request |

## logs

| Method | inner_uri | apiName | table name |
|--------|-----------|---------|------------|
| POST | `/apis/v1/composio/logs/tool_execution` | Search and retrieve tool execution logs | Logs Tool Execution |
| GET | `/apis/v1/composio/logs/tool_execution/{id}` | Get log details by ID | Logs Tool Execution Id |

## mcp

| Method | inner_uri | apiName | table name |
|--------|-----------|---------|------------|
| GET | `/apis/v1/composio/mcp/app/{appKey}` | List MCP servers for a specific app | Mcp App Appkey |
| GET | `/apis/v1/composio/mcp/servers` | List MCP servers with optional filters and pagination | Mcp Servers |
| POST | `/apis/v1/composio/mcp/servers` | Create a new MCP server | Mcp Servers |
| POST | `/apis/v1/composio/mcp/servers/custom` | Create a new custom MCP server with multiple apps | Mcp Servers Custom |
| POST | `/apis/v1/composio/mcp/servers/generate` | Generate MCP URL with custom parameters | Mcp Servers Generate |
| GET | `/apis/v1/composio/mcp/servers/{serverId}/instances` | List all instances for an MCP server | Mcp Servers Serverid Instances |
| POST | `/apis/v1/composio/mcp/servers/{serverId}/instances` | Create a new MCP server instance | Mcp Servers Serverid Instances |
| DELETE | `/apis/v1/composio/mcp/servers/{serverId}/instances/{instanceId}` | Delete an MCP server instance and associated connected accounts | Mcp Servers Serverid Instances Instanceid |
| DELETE | `/apis/v1/composio/mcp/{id}` | Delete an MCP server | Mcp Id |
| GET | `/apis/v1/composio/mcp/{id}` | Get MCP server details by ID | Mcp Id |
| PATCH | `/apis/v1/composio/mcp/{id}` | Update MCP server configuration | Mcp Id |

## migration

| Method | inner_uri | apiName | table name |
|--------|-----------|---------|------------|
| GET | `/apis/v1/composio/migration/get-nanoid` | Get NanoId from UUID | Migration Get-nanoid |

## org

| Method | inner_uri | apiName | table name |
|--------|-----------|---------|------------|
| POST | `/apis/v1/composio/org/clanker/create_claim` | Create a clanker-claim slug | Org Clanker Create Claim |
| GET | `/apis/v1/composio/org/owner/project/list` | List all projects | Org Owner Project List |
| POST | `/apis/v1/composio/org/owner/project/new` | Create a new project | Org Owner Project New |
| DELETE | `/apis/v1/composio/org/owner/project/{nano_id}` | Delete a project | Org Owner Project Nano Id |
| GET | `/apis/v1/composio/org/owner/project/{nano_id}` | Get project details by ID With Org Api key | Org Owner Project Nano Id |
| POST | `/apis/v1/composio/org/owner/project/{nano_id}/regenerate_api_key` | Delete and generate new API key for project | Org Owner Project Nano Id Regenerate Api Key |
| GET | `/apis/v1/composio/org/project/config` | Get project configuration | Org Project Config |
| PATCH | `/apis/v1/composio/org/project/config` | Update project configuration | Org Project Config |
| POST | `/apis/v1/composio/org/usage/summary` | Org usage summary | Org Usage Summary |
| POST | `/apis/v1/composio/org/usage/{entity_type}` | Org usage breakdown | Org Usage Entity Type |

## project

| Method | inner_uri | apiName | table name |
|--------|-----------|---------|------------|
| POST | `/apis/v1/composio/project/usage/summary` | Project usage summary | Project Usage Summary |
| POST | `/apis/v1/composio/project/usage/{entity_type}` | Project usage breakdown | Project Usage Entity Type |

## tool_router

| Method | inner_uri | apiName | table name |
|--------|-----------|---------|------------|
| POST | `/apis/v1/composio/tool_router/session` | Create a new tool router session | Tool Router Session |
| GET | `/apis/v1/composio/tool_router/session/{session_id}` | Get a tool router session by ID (v3.1) | Tool Router Session Session Id |
| PATCH | `/apis/v1/composio/tool_router/session/{session_id}` | Patch a tool router session config (v3.1) | Tool Router Session Session Id |
| POST | `/apis/v1/composio/tool_router/session/{session_id}/attach` | Attach to an existing tool router session (v3.1) | Tool Router Session Session Id Attach |
| GET | `/apis/v1/composio/tool_router/session/{session_id}/config_history` | List a tool router session config history | Tool Router Session Session Id Config History |
| POST | `/apis/v1/composio/tool_router/session/{session_id}/execute` | Execute a tool within a tool router session | Tool Router Session Session Id Execute |
| POST | `/apis/v1/composio/tool_router/session/{session_id}/execute_meta` | Execute a meta tool within a tool router session | Tool Router Session Session Id Execute Meta |
| POST | `/apis/v1/composio/tool_router/session/{session_id}/link` | Create a link session for a toolkit in a tool router session | Tool Router Session Session Id Link |
| POST | `/apis/v1/composio/tool_router/session/{session_id}/mounts/{mount_id}/delete` | Delete a file from a session mount | Tool Router Session Session Id Mounts Mount Id Delete |
| POST | `/apis/v1/composio/tool_router/session/{session_id}/mounts/{mount_id}/download_url` | Create a presigned download URL for a mount file | Tool Router Session Session Id Mounts Mount Id Download Url |
| GET | `/apis/v1/composio/tool_router/session/{session_id}/mounts/{mount_id}/items` | List files in a session mount | Tool Router Session Session Id Mounts Mount Id Items |
| POST | `/apis/v1/composio/tool_router/session/{session_id}/mounts/{mount_id}/upload_url` | Create a presigned upload URL for a mount file | Tool Router Session Session Id Mounts Mount Id Upload Url |
| POST | `/apis/v1/composio/tool_router/session/{session_id}/proxy_execute` | Execute proxy request within a tool router session | Tool Router Session Session Id Proxy Execute |
| POST | `/apis/v1/composio/tool_router/session/{session_id}/search` | Search for tools using a query | Tool Router Session Session Id Search |
| GET | `/apis/v1/composio/tool_router/session/{session_id}/toolkits` | Get toolkits for a tool router session | Tool Router Session Session Id Toolkits |
| GET | `/apis/v1/composio/tool_router/session/{session_id}/tools` | List tools with schemas for a tool router session (v3.1) | Tool Router Session Session Id Tools |

## toolkits

| Method | inner_uri | apiName | table name |
|--------|-----------|---------|------------|
| GET | `/apis/v1/composio/toolkits` | List available toolkits | Toolkits |
| GET | `/apis/v1/composio/toolkits/categories` | List toolkit categories | Toolkits Categories |
| GET | `/apis/v1/composio/toolkits/changelog` | Get toolkits changelog | Toolkits Changelog |
| POST | `/apis/v1/composio/toolkits/multi` | Fetch multiple toolkits | Toolkits Multi |
| GET | `/apis/v1/composio/toolkits/{slug}` | Get toolkit by slug | Toolkits Slug |

## tools

| Method | inner_uri | apiName | table name |
|--------|-----------|---------|------------|
| GET | `/apis/v1/composio/tools` | List available tools | Tools |
| GET | `/apis/v1/composio/tools/enum` | Get tool enum list | Tools Enum |
| POST | `/apis/v1/composio/tools/execute/proxy` | Execute proxy request | Tools Execute Proxy |
| POST | `/apis/v1/composio/tools/execute/{tool_slug}` | Execute tool | Tools Execute Tool Slug |
| POST | `/apis/v1/composio/tools/execute/{tool_slug}/input` | Generate tool inputs from natural language | Tools Execute Tool Slug Input |
| POST | `/apis/v1/composio/tools/scopes/required` | Get required scopes for tools | Tools Scopes Required |
| GET | `/apis/v1/composio/tools/{tool_slug}` | Get tool by slug | Tools Tool Slug |

## trigger_instances

| Method | inner_uri | apiName | table name |
|--------|-----------|---------|------------|
| GET | `/apis/v1/composio/trigger_instances/active` | List active triggers | Trigger Instances Active |
| DELETE | `/apis/v1/composio/trigger_instances/manage/{triggerId}` | Delete a trigger | Trigger Instances Manage Triggerid |
| PATCH | `/apis/v1/composio/trigger_instances/manage/{triggerId}` | Enable or disable a trigger | Trigger Instances Manage Triggerid |
| POST | `/apis/v1/composio/trigger_instances/{slug}/upsert` | Create or update a trigger | Trigger Instances Slug Upsert |

## triggers_types

| Method | inner_uri | apiName | table name |
|--------|-----------|---------|------------|
| GET | `/apis/v1/composio/triggers_types` | List trigger types | Triggers Types |
| GET | `/apis/v1/composio/triggers_types/list/enum` | List trigger type enums | Triggers Types List Enum |
| GET | `/apis/v1/composio/triggers_types/{slug}` | Get trigger type by slug | Triggers Types Slug |

## webhook_endpoints

| Method | inner_uri | apiName | table name |
|--------|-----------|---------|------------|
| GET | `/apis/v1/composio/webhook_endpoints` | List webhook endpoints | Webhook Endpoints |
| POST | `/apis/v1/composio/webhook_endpoints` | Create webhook endpoint | Webhook Endpoints |
| GET | `/apis/v1/composio/webhook_endpoints/{nano_id}` | Get webhook endpoint | Webhook Endpoints Nano Id |
| PATCH | `/apis/v1/composio/webhook_endpoints/{nano_id}` | Update webhook endpoint configuration | Webhook Endpoints Nano Id |
| DELETE | `/apis/v1/composio/webhook_endpoints/{nano_id}` | Delete webhook endpoint | Webhook Endpoints Nano Id |

## webhook_subscriptions

| Method | inner_uri | apiName | table name |
|--------|-----------|---------|------------|
| GET | `/apis/v1/composio/webhook_subscriptions` | List webhook subscriptions | Webhook Subscriptions |
| POST | `/apis/v1/composio/webhook_subscriptions` | Create webhook subscription | Webhook Subscriptions |
| GET | `/apis/v1/composio/webhook_subscriptions/event_types` | List available event types | Webhook Subscriptions Event Types |
| DELETE | `/apis/v1/composio/webhook_subscriptions/{id}` | Delete webhook subscription | Webhook Subscriptions Id |
| GET | `/apis/v1/composio/webhook_subscriptions/{id}` | Get webhook subscription | Webhook Subscriptions Id |
| PATCH | `/apis/v1/composio/webhook_subscriptions/{id}` | Update webhook subscription | Webhook Subscriptions Id |
| POST | `/apis/v1/composio/webhook_subscriptions/{id}/rotate_secret` | Rotate webhook secret | Webhook Subscriptions Id Rotate Secret |
