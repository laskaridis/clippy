# Quick Search API and Model Draft

This document is a draft API and data-model specification for the quick-search feature described in `docs/plans/quick-search.md`.

## Scope

- Web UI and backend only.
- PostgreSQL-backed search implementation (Option 2).
- Result cap is global top 5 items across all groups.

## Draft API

### Endpoint

`GET /api/clips/quick-search/?q=<url-encoded-query>`

- Auth: required (`SessionAuthentication` / `CsrfExemptSessionAuthentication` + `IsAuthenticated`)
- Content type: `application/json`
- Ownership: all hits must be scoped to `request.user`

### Query Parameters

- `q` (required, string)
  - Must be URL-encoded by client.
  - Decoded value length: min 3, max 50.
  - Must not contain any whitespace.

### 200 Response Shape

```json
{
  "query": "python",
  "total": 5,
  "groups": {
    "clips": [
      {
        "type": "clip",
        "score": 0.97,
        "clip_id": "7f03e8d4-7b62-4772-8c72-3c77bfb8fb3f",
        "title": "Pathlib notes",
        "snippet": "Path objects are ...",
        "url": "https://docs.python.org/3/library/pathlib.html",
        "created_at": "2026-02-28T10:31:22Z",
        "target_url": "/clips/7f03e8d4-7b62-4772-8c72-3c77bfb8fb3f/"
      }
    ],
    "labels": [
      {
        "type": "label",
        "score": 0.88,
        "label_uuid": "7cd1b36d-3ab8-4c8f-9531-18cf7d9062af",
        "name": "python",
        "clip_count": 4,
        "target_url": "/clips?label=7cd1b36d-3ab8-4c8f-9531-18cf7d9062af"
      }
    ],
    "websites": [
      {
        "type": "website",
        "score": 0.81,
        "url": "https://docs.python.org/3/library/pathlib.html",
        "clip_count": 3,
        "target_url": "/clips?url=https%3A%2F%2Fdocs.python.org%2F3%2Flibrary%2Fpathlib.html"
      }
    ]
  }
}
```

### Error Cases

#### 401 Unauthorized

When request is unauthenticated.

Example:

```json
{
  "detail": "Authentication credentials were not provided."
}
```

#### 400 Bad Request: missing `q`

```json
{
  "q": ["This query parameter is required."]
}
```

#### 400 Bad Request: too short (`len < 3`)

```json
{
  "q": ["Ensure this field has at least 3 characters."]
}
```

#### 400 Bad Request: too long (`len > 50`)

```json
{
  "q": ["Ensure this field has no more than 50 characters."]
}
```

#### 400 Bad Request: whitespace present

```json
{
  "q": ["Whitespace is not allowed."]
}
```

#### 400 Bad Request: invalid encoding

```json
{
  "q": ["Invalid URL-encoded query value."]
}
```

## Draft Serializer Contracts

### `QuickSearchQuerySerializer`

- `q = serializers.CharField(required=True, min_length=3, max_length=50, trim_whitespace=False)`
- Custom `validate_q`:
  - decode URL-encoded value (raise validation error on decode failure)
  - reject any whitespace using regex `\s`

### `QuickSearchResponseSerializer`

- `query: str`
- `total: int`
- `groups: QuickSearchGroupsSerializer`

### `QuickSearchGroupsSerializer`

- `clips: list[QuickSearchClipHitSerializer]`
- `labels: list[QuickSearchLabelHitSerializer]`
- `websites: list[QuickSearchWebsiteHitSerializer]`

## Draft Data Model Changes

### `apps.clips.models.Label`

Add stable public identifier for URL filtering:

- `uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)`

Rationale:

- Supports `/clips?label=<uuid>` without exposing integer IDs.
- Keeps filter links stable and non-sequential.

### `apps.clips.models.Clip`

No new required columns for draft behavior.

Keep existing:

- `url` is used as exact website hit key.
- `normalized_text` is used for textual matching.

### PostgreSQL Search Support

Migration should include:

- enable `pg_trgm` extension
- GIN/trigram indexes for quick-search candidate fields, with ownership in mind

Draft index intent:

- `Clip(user_id, created_at)` (already present)
- `Clip(user_id, url)` (add for exact URL grouping/filter speed)
- trigram/FTS support for:
  - `Clip.normalized_text`
  - `Clip.title`
  - `Clip.url`
  - `Label.name`

## Draft Ranking Contract

- Build candidate sets from user-scoped clips, labels, and exact URLs.
- Score via PostgreSQL full-text + trigram similarity.
- Merge all candidates into one ranked list.
- Apply deterministic tie-breaks (recommended):
  1. higher score
  2. hit-type priority: `clip` > `label` > `website`
  3. recency (`created_at` desc) where applicable
  4. lexical fallback
- Keep only top 5 globally.
- Group selected top-5 by type in output.

## Web Filter Contract (for result clicks)

- Clip result: `/clips/<clip_uuid>/`
- Label result: `/clips?label=<label_uuid>`
- Website result: `/clips?url=<url-encoded-exact-url>`

## Validation Checklist

- Input validation at API boundary only (serializer).
- No cross-user data leakage in any candidate query.
- `total` never exceeds 5.
- Empty groups allowed; missing groups not allowed.
- Error payloads are user-safe and do not expose internals.
