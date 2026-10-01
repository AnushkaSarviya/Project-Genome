from models.user import User


class UserService:
    """Service handling user management."""

    def __init__(self):
        self.users = {}

    def create_user(self, user_id: int, name: str) -> User:
        user = User(user_id, name)
        self.users[user_id] = user
        return user

    def get_user(self, user_id: int) -> User:
        user = self.users.get(user_id)
        if user:
            user.get_display_name()
        return user
