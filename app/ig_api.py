import os
from typing import Dict, Any, List

# This file documents how you'd wire Instagram Graph API calls.
# We leave stub functions so you can fill in actual HTTP calls (requests) with your tokens.

FB_APP_ID = os.getenv("FB_APP_ID")
FB_APP_SECRET = os.getenv("FB_APP_SECRET")
FB_PAGE_ID = os.getenv("FB_PAGE_ID")
IG_BUSINESS_ID = os.getenv("IG_BUSINESS_ID")
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")

def docs() -> Dict[str, Any]:
    return {
        "note": "Followers bios are NOT available in Graph API. Use audience insights, commenters/likers on media, or consent-based CSV uploads.",
        "oauth_flow": [
            "Facebook Login -> user grants permissions to manage page/instagram_basic/etc.",
            "Exchange short-lived token for long-lived page token",
            "Use Page token to access Instagram Business Account (IG_BUSINESS_ID) endpoints"
        ],
        "example_endpoints": {
            "audience_insights": "GET https://graph.facebook.com/v21.0/{ig_id}/insights?metric=audience_city,audience_gender_age&access_token=...",
            "recent_media": "GET https://graph.facebook.com/v21.0/{ig_id}/media?fields=id,caption,comments.limit(50){text,username},like_count&access_token=...",
            "commenters": "Within media fields, use comments edge to list commenters; classify comment text."
        }
    }

# You can implement: get_audience_insights(), get_recent_media(), get_media_commenters() with 'requests'.
