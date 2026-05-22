# social-publisher

A [Hermes agent](https://hermes-agent.nousresearch.com/) plugin for creating and publishing content to LinkedIn and Facebook, with AI image generation, image enhancement, and post scheduling.

## Features

- **Publish** to LinkedIn (personal profile + pages) and Facebook pages
- **AI image generation** via GPT Image
- **AI image enhancement** via GPT Image edits
- **Schedule posts** at a date and time of your choice
- **Web dashboard** to visualize and manage scheduled posts

## Plugin tools

| Tool | Description |
|---|---|
| `generate_image` | Generate an image from a text prompt (GPT Image) |
| `enhance_image` | Enhance or edit an existing image (GPT Image) |
| `publish_post` | Publish immediately to one or more targets |
| `schedule_post` | Schedule a post for a specific date and time |
| `list_scheduled_posts` | List all pending scheduled posts |
| `cancel_scheduled_post` | Cancel a scheduled post by ID |

Supported targets: `linkedin_profile`, `linkedin_page`, `facebook_page`

## Installation

### 1. Install dependencies

```bash
pip install openai requests pillow
```

### 2. Copy the plugin to your Hermes server

```bash
scp -r . user@your-server:~/.hermes/plugins/social-publisher/
```

### 3. Set environment variables on the server

```bash
# Required
export OPENAI_API_KEY="sk-..."
export LINKEDIN_ACCESS_TOKEN="AQX..."
export LINKEDIN_PERSON_URN="urn:li:person:YOUR_ID"

# Optional
export LINKEDIN_PAGE_URN="urn:li:organization:YOUR_ORG_ID"
export FACEBOOK_PAGE_ACCESS_TOKEN="EAA..."
export FACEBOOK_PAGE_ID="123456789"
```

#### Getting your credentials

| Credential | Where to get it |
|---|---|
| `OPENAI_API_KEY` | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| `LINKEDIN_ACCESS_TOKEN` | LinkedIn Developer App → OAuth 2.0 token with `w_member_social` + `w_organization_social` scopes |
| `LINKEDIN_PERSON_URN` | `GET https://api.linkedin.com/v2/me` → use the `id` field as `urn:li:person:{id}` |
| `LINKEDIN_PAGE_URN` | `urn:li:organization:` + your org's numeric ID (visible in the page admin URL) |
| `FACEBOOK_PAGE_ACCESS_TOKEN` | [Meta Graph API Explorer](https://developers.facebook.com/tools/explorer/) → generate a page token |
| `FACEBOOK_PAGE_ID` | Your page's About section or Graph API Explorer |

### 4. Enable the plugin

```bash
hermes plugins enable social-publisher
```

## Web dashboard

A web dashboard lets you visualize and cancel scheduled posts.

### Run with Docker Compose

```bash
docker compose up --build
```

- Dashboard: [http://localhost:52847](http://localhost:52847)
- API: [http://localhost:37421](http://localhost:37421)

### Connecting to the real Hermes DB

By default the dashboard uses an isolated Docker volume. To point it at the actual Hermes scheduler database, update the backend volume in `docker-compose.yml`:

```yaml
backend:
  volumes:
    - /path/to/.hermes/plugins/social-publisher/schedule.db:/data/schedule.db
```

## Notes

- Facebook personal profile posting is not supported — Meta's Graph API restricts this for third-party apps. Facebook Pages work fully.
- Scheduled posts are stored in a local SQLite database (`schedule.db`) and published by a background thread inside the Hermes process.
- Images are saved to `~/.hermes/plugins/social-publisher/images/` on the Hermes server.

## License

MIT
