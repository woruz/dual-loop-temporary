from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

# ── What is @dataclass? ───────────────────────────────────────────
# It's just a shortcut. Instead of writing __init__, __repr__ etc.
# manually, @dataclass generates them for you automatically.
# It turns your class into a simple "bag of fields".

@dataclass
class User:
    """
    Represents a person who has an account in our system.
    This is the central object — everything else revolves around it.
    """
    email: str                          # Required — no default

    id: UUID = field(default_factory=uuid4)
    # ↑ Auto-generates a unique ID if you don't pass one.
    #   uuid4() = random UUID. Like: "a3f8c1d2-..."
    #   default_factory means: call uuid4() fresh for each new User.

    hashed_password: str | None = None
    # ↑ None means this user signed up via GitHub only.
    #   They never set a password, so we store nothing.
    #   str means they registered with email+password (bcrypt hash).

    is_verified: bool = False
    # ↑ Did they confirm their email?
    #   For GitHub users this is True immediately (GitHub verified it).
    #   For email users it starts False until they click a verify link.

    created_at: datetime = field(default_factory=datetime.utcnow)
    # ↑ Automatically set to "right now" when the User is created.


@dataclass
class OAuthProfile:
    """
    A bridge between a User and their GitHub account.
    One User can have one OAuthProfile (for now).

    Why is this a separate object and not just fields on User?
    Because in the future you might add Google OAuth too.
    Each provider gets its own OAuthProfile row.
    """
    user_id: UUID           # Which User does this belong to?
    provider: str           # Always "github" in our case
    provider_user_id: str   # GitHub's own ID — e.g. "58291047"
                            # This is STABLE. @username can change.
                            # This number never changes on GitHub.

    username: str | None = None     # e.g. "deepak-raj" — the @handle
    avatar_url: str | None = None   # profile picture URL from GitHub

    id: UUID = field(default_factory=uuid4)  # Our own internal ID


@dataclass
class AuthToken:
    """
    What we send back to the user after a successful login.
    This is what the frontend stores and sends on every request.
    """
    access_token: str           # The actual JWT string
    token_type: str = "bearer"  # Always "bearer" — HTTP standard